#!/usr/bin/env python3
"""Reference identities and checks for the ARA-to-Lara contracts (stage L1, plan 03).

Standard library only. Reuses the canonical encoding and ``domain_digest`` of
``../identity.py``: every identity is SHA-256 over the record's own ``schema``
value as hash domain, a NUL byte, and the RFC 8785 encoding of the record
without its self-identity field.

The checks state the contract; they do not run Lara, read files, authenticate
actors or decide scientific questions. ``lara_audit.py`` holds the review,
supersession and map-scope rules.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

_PARENT = str(Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

import identity as I  # noqa: E402  (sibling contract module, located above)

ContractError = I.ContractError

# Lara record schemas and the self-identity field each excludes from its hash.
LARA_ID_FIELDS: Dict[str, str] = {
    "ara.lara-binding/v1": "binding_id",
    "ara.lara-review-attestation/v1": "attestation_id",
    "ara.lara-setting-descriptor/v1": "descriptor_id",
    "ara.lara-system-descriptor/v1": "system_id",
    "ara.lara-setting-registry/v1": "registry_id",
    "ara.lara-argument-check/v1": "check_id",
    "ara.lara-map-revision/v1": "map_revision_id",
}
# ara.attachment/v1 kinds whose body points to a Lara document, and that document's schema.
ATTACHMENT_DOCUMENTS: Dict[str, str] = {
    "review_attestation": "ara.lara-review-attestation/v1",
    "argument_check": "ara.lara-argument-check/v1",
}
_ARTIFACT_LINE = re.compile(r"^artifact[ \t]+([a-z][A-Za-z0-9_]*)[ \t]+at[ \t]+(\S+)[ \t]*$")


def require(condition: bool, code: str, message: str) -> None:
    """Raise ``ContractError(code)`` unless ``condition`` holds."""
    if not condition:
        raise ContractError(code, message)


def sorted_unique(items: List[Any], key: Callable[[Any], Any], what: str) -> None:
    """Require ``items`` strictly increasing by ``key`` (sorted, no duplicates)."""
    keys = [key(item) for item in items]
    require(all(left < right for left, right in zip(keys, keys[1:])),
            "unsorted_or_duplicate", what + " must be sorted and unique")


# --------------------------------------------------------------------------
# Identities
# --------------------------------------------------------------------------

def lara_record_id(record: Mapping[str, Any]) -> str:
    """Identity of a Lara record under its own ``schema`` domain, self-ID excluded."""
    schema = record.get("schema") if isinstance(record, Mapping) else None
    require(isinstance(schema, str) and schema in LARA_ID_FIELDS, "invalid_domain",
            "unknown Lara record schema " + repr(schema))
    field = LARA_ID_FIELDS[schema]
    return I.domain_digest(schema, {key: value for key, value in record.items() if key != field})


def self_id_matches(record: Mapping[str, Any]) -> bool:
    """True when the record's stored self-identity equals its recomputed identity."""
    return record.get(LARA_ID_FIELDS.get(record.get("schema"), ""), None) == lara_record_id(record)


def _check_self_id(record: Mapping[str, Any]) -> None:
    field = LARA_ID_FIELDS[record["schema"]]
    require(self_id_matches(record), "identity_mismatch", field + " does not match the record")


def with_id(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``record`` with its self-identity field (re)computed."""
    result = dict(record)
    result[LARA_ID_FIELDS[record["schema"]]] = lara_record_id(record)
    return result


# --------------------------------------------------------------------------
# Argument files and bindings
# --------------------------------------------------------------------------

def argument_artifact(raw: bytes) -> Tuple[str, str]:
    """Return ``(name, digest)`` from a .lara file's ``artifact <name> at <digest>`` header."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError("invalid_argument", "argument is not UTF-8") from error
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _ARTIFACT_LINE.match(stripped)
        require(match is not None, "invalid_argument", "first declaration is not an artifact header")
        return match.group(1), match.group(2)
    raise ContractError("invalid_argument", "argument has no artifact header")


def check_binding(binding: Mapping[str, Any], argument_bytes: Optional[bytes] = None,
                  registry: Optional[Mapping[str, Any]] = None) -> None:
    """Ordering, element closure, snapshot agreement, optional argument bytes and registry."""
    claims, elements = binding["claims"], binding["elements"]
    sorted_unique(claims, lambda claim: claim["lara_id"], "claims")
    sorted_unique(elements, lambda element: element["ref"], "elements")
    refs = {element["ref"] for element in elements}
    used = set()
    for claim in claims:
        for name in ("elements", "settings", "systems"):
            sorted_unique(claim[name], lambda item: item, claim["lara_id"] + "." + name)
        missing = set(claim["elements"]) - refs
        require(not missing, "invalid_reference", "claim names unbound elements " + ", ".join(sorted(missing)))
        used.update(claim["elements"])
    require(used == refs, "invalid_reference", "every element must belong to a selected claim")
    for element in elements:
        sorted_unique(element["sources"], lambda src: (src["source_key"], src["native_revision"], src["selector"]),
                      element["ref"] + ".sources")
    require(binding["argument"]["artifact"]["digest"] == "sha256:" + binding["native"]["fingerprint"],
            "snapshot_mismatch", "argument header does not name the binding's native snapshot")
    if argument_bytes is not None:
        require(I.bytes_digest(argument_bytes) == binding["argument"]["digest"], "identity_mismatch",
                "argument bytes differ from argument.digest")
        name, digest = argument_artifact(argument_bytes)
        require(digest == "sha256:" + binding["native"]["fingerprint"], "snapshot_mismatch",
                "argument header names another snapshot; write a new argument against this one")
        require(name == binding["argument"]["artifact"]["name"], "identity_mismatch",
                "argument header name differs from the binding")
    if registry is not None:
        require(registry["registry_id"] == binding["registry"], "vocabulary_mismatch",
                "binding was written against another registry")
        settings = {entry["descriptor"]["descriptor_id"] for entry in registry["settings"]}
        systems = {entry["descriptor"]["system_id"] for entry in registry["systems"]}
        for claim in claims:
            require(set(claim["settings"]) <= settings and set(claim["systems"]) <= systems,
                    "vocabulary_mismatch", claim["lara_id"] + " names an unregistered descriptor")
    _check_self_id(binding)


# --------------------------------------------------------------------------
# Setting descriptors and the registry
# --------------------------------------------------------------------------

def check_setting_descriptor(descriptor: Mapping[str, Any]) -> None:
    """Sorted controls and replication variables; matching descriptor_id."""
    sorted_unique(descriptor["controls"], lambda item: item["name"], "controls")
    sorted_unique(descriptor["replication"], lambda item: item["variable"], "replication")
    _check_self_id(descriptor)


def _without_metric(descriptor: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in descriptor.items() if key not in ("metric", "descriptor_id")}


def check_registry(registry: Mapping[str, Any]) -> None:
    """Descriptor identities, ordering and one meaning per Lara symbol."""
    settings, systems = registry["settings"], registry["systems"]
    sorted_unique(settings, lambda entry: entry["descriptor"]["descriptor_id"], "settings")
    sorted_unique(systems, lambda entry: entry["descriptor"]["system_id"], "systems")
    pairs: Dict[Tuple[str, str], str] = {}
    metrics: Dict[str, Any] = {}
    contexts: Dict[str, Any] = {}
    for entry in settings:
        descriptor = entry["descriptor"]
        check_setting_descriptor(descriptor)
        pair = (entry["measurand"], entry["setting"])
        require(pair not in pairs, "symbol_conflict", "symbol pair %s/%s names two settings" % pair)
        pairs[pair] = descriptor["descriptor_id"]
        require(metrics.setdefault(entry["measurand"], descriptor["metric"]) == descriptor["metric"],
                "symbol_conflict", "measurand " + entry["measurand"] + " names two metrics")
        require(contexts.setdefault(entry["setting"], _without_metric(descriptor)) == _without_metric(descriptor),
                "symbol_conflict", "setting " + entry["setting"] + " names two experimental settings")
    system_symbols = [entry["symbol"] for entry in systems]
    require(len(set(system_symbols)) == len(system_symbols), "symbol_conflict", "a system symbol names two systems")
    require(not set(system_symbols) & (set(metrics) | set(contexts)), "symbol_conflict",
            "a system symbol is also a setting or measurand symbol")
    for entry in systems:
        _check_self_id(entry["descriptor"])
    _check_self_id(registry)


def _symbol_table(registry: Mapping[str, Any]) -> Dict[Tuple[str, ...], str]:
    table = {("setting", entry["measurand"], entry["setting"]): entry["descriptor"]["descriptor_id"]
             for entry in registry["settings"]}
    table.update({("system", entry["symbol"]): entry["descriptor"]["system_id"] for entry in registry["systems"]})
    return table


def check_registry_extension(old: Mapping[str, Any], new: Mapping[str, Any]) -> None:
    """A vocabulary extension: next revision of the same vocabulary keeping every old symbol."""
    check_registry(old)
    check_registry(new)
    require(new["previous"] == old["registry_id"], "invalid_extension", "previous must name the earlier registry")
    require(new["vocabulary"]["name"] == old["vocabulary"]["name"]
            and new["vocabulary"]["revision"] == old["vocabulary"]["revision"] + 1,
            "invalid_extension", "an extension is the next revision of the same vocabulary")
    before, after = _symbol_table(old), _symbol_table(new)
    for symbol, identity in before.items():
        require(after.get(symbol) == identity, "symbol_rebound",
                "symbol " + "/".join(symbol[1:]) + " changed meaning or was dropped")


# --------------------------------------------------------------------------
# Check records and attachments
# --------------------------------------------------------------------------

def _row_key(row: Mapping[str, Any]) -> Tuple[str, str]:
    return (row["member"] or "", row["claim"])


def check_argument_check(check: Mapping[str, Any], binding: Optional[Mapping[str, Any]] = None,
                         map_revision: Optional[Mapping[str, Any]] = None) -> None:
    """Exit-status discipline, status rows, and agreement with the binding or map revision."""
    statuses, blocked = check["statuses"], check["admission_blocked"]
    sorted_unique(statuses, _row_key, "statuses")
    sorted_unique(blocked, _row_key, "admission_blocked")
    require(not {_row_key(row) for row in statuses} & {_row_key(row) for row in blocked}, "invalid_status",
            "a claim is either reported or admission-blocked")
    on_map = check["target"]["kind"] == "map_revision"
    require(all((row["member"] is not None) == on_map for row in statuses + blocked), "invalid_status",
            "map rows name a member alias; individual rows do not")
    sorted_unique(check["inputs"]["binding_ids"], lambda item: item, "inputs.binding_ids")
    if check["checker"] is not None:
        sorted_unique(check["checker"]["backends"], lambda b: (b["name"], b["version"]), "backends")
        sorted_unique(check["checker"]["theories"], lambda item: item, "theories")
    result, invocation = check["result"], check["invocation"]
    if result is not None and invocation is not None and invocation["output"] == "stdout":
        require(result["verdict_source"] != "out_file", "stale_output", "no --out file was requested")
    if check["outcome"] == "unavailable" and result is not None:
        require(result["exit_status"] not in (0, 1, 2), "invalid_outcome",
                "a checker that exited 0, 1 or 2 ran: its outcome is accepted or rejected")
    if check["outcome"] == "rejected":
        require(check["rejection"]["boundary"] == (result["exit_status"] == 2), "invalid_outcome",
                "exit 2 is a boundary rejection and exit 1 is not")
    require(check["supersedes"] != check["check_id"], "invalid_supersession", "a check cannot supersede itself")
    if binding is not None:
        require(not on_map and check["inputs"]["binding_ids"] == [binding["binding_id"]]
                and check["inputs"]["entry"]["digest"] == binding["argument"]["digest"]
                and check["policy"] == binding["policy"] and check["inputs"]["registry"] == binding["registry"],
                "identity_mismatch", "check inputs differ from the binding")
    if map_revision is not None:
        members = map_revision["members"]
        aliases = {member["alias"] for member in members}
        expected_scope = {"audited": "audited_map", "exploratory": "exploratory_map"}[map_revision["coverage"]["scope"]]
        require(on_map and check["target"]["map_revision_id"] == map_revision["map_revision_id"]
                and check["scope"] == expected_scope
                and (check["checker"] is None or check["checker"] == map_revision["checker"])
                and check["policy"] == map_revision["policy"]
                and check["inputs"]["entry"]["digest"] == map_revision["manifest"]["digest"]
                and check["inputs"]["binding_ids"] == sorted({member["binding_id"] for member in members})
                and check["inputs"]["registry"] == map_revision["registry"],
                "identity_mismatch", "check inputs or scope differ from the map revision")
        require(all(row["member"] in aliases for row in statuses), "invalid_status", "row names an unknown alias")
    _check_self_id(check)


def check_lara_attachment(attachment: Mapping[str, Any], document_bytes: bytes,
                          inventory: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Check an attachment carrying a Lara document and return the decoded document."""
    I.check_attachment(attachment, inventory)
    expected = ATTACHMENT_DOCUMENTS.get(attachment["kind"])
    require(expected is not None and attachment["body"]["schema"] == expected, "invalid_body",
            "attachment kind and Lara document schema disagree")
    document = I.loads(document_bytes)
    require(I.jcs(document) == document_bytes, "noncanonical_value", "Lara documents are stored as JCS bytes")
    require(document.get("schema") == expected, "invalid_body", "document schema differs from body.schema")
    if inventory is not None:
        ref = attachment["body"]["document"]
        entry = next((item for item in inventory["entries"]
                      if (item["root"], item["path"]) == (ref["root"], ref["path"])), None)
        require(entry is not None and entry["digest"] == I.bytes_digest(document_bytes), "identity_mismatch",
                "document bytes differ from the inventory entry")
    require(document["community"] == attachment["community"], "identity_mismatch", "community differs")
    target = document["target"]
    require(target["kind"] == "contribution" and target["contribution_id"] == attachment["target"],
            "identity_mismatch", "document target differs from the attachment target")
    actor = document["reviewer"] if expected == ATTACHMENT_DOCUMENTS["review_attestation"] else document["verifier"]
    require(actor == attachment["publisher"], "actor_ownership", "the attachment publisher must be the document's actor")
    _check_self_id(document)
    return document
