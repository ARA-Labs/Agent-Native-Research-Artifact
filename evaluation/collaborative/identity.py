#!/usr/bin/env python3
"""Reference identity functions for the collaborative-research contracts.

Standard library only. Every identity is SHA-256 over a schema-specific hash
domain, a NUL byte, and the RFC 8785 (JCS) encoding of a JSON value restricted
to objects, arrays, strings, booleans, null and integers. Floats are outside
the value domain and reject, so no number formatting rules are needed.

The functions here state the contract precisely; they are not a coordinator.
They do not read files, authenticate actors, or decide scientific questions.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

PAYLOAD_DOMAIN = "ara.payload/v1"
CONTRIBUTION_DOMAIN = "ara.contribution/v1"
CAPTURE_DOMAIN = "ara.capture/v1"

# Record schemas whose identity field is excluded from their own hash. The
# hash domain is the record's own ``schema`` value.
RECORD_ID_FIELDS: Dict[str, str] = {
    "ara.contribution/v1": "contribution_id",
    "ara.attachment/v1": "record_id",
    "ara.integration-receipt/v1": "record_id",
    "ara.publication-receipt/v1": "receipt_id",
    "ara.publication-rejection/v1": "receipt_id",
    "ara.visibility/v1": "visibility_id",
    "ara.role-policy/v1": "policy_id",
}
# Records hashed whole (no self-identity field).
WHOLE_RECORD_DOMAINS = ("ara.payload-inventory/v1", "ara.publication-request/v1")

MAX_SAFE_INTEGER = 2 ** 53 - 1
_SHORT_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\t": "\\t",
                  "\n": "\\n", "\f": "\\f", "\r": "\\r"}


class ContractError(ValueError):
    """A value violates the contract; ``code`` is a stable machine-readable reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code + ": " + message)
        self.code = code


# --------------------------------------------------------------------------
# Canonical encoding (RFC 8785 for the integer-only value domain)
# --------------------------------------------------------------------------

def _string(value: str) -> str:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ContractError("noncanonical_value", "string is not Unicode scalar values") from error
    parts = ['"']
    for char in value:
        if char in _SHORT_ESCAPES:
            parts.append(_SHORT_ESCAPES[char])
        elif ord(char) < 0x20:
            parts.append("\\u%04x" % ord(char))
        else:
            parts.append(char)
    parts.append('"')
    return "".join(parts)


def _utf16_key(key: str) -> bytes:
    return key.encode("utf-16-be", "surrogatepass")


def _encode(value: Any, out: List[str]) -> None:
    if value is None:
        out.append("null")
    elif value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif type(value) is int:
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise ContractError("noncanonical_value", "integer outside +/-(2^53-1)")
        out.append(str(value))
    elif isinstance(value, str):
        out.append(_string(value))
    elif isinstance(value, (list, tuple)):
        out.append("[")
        for index, item in enumerate(value):
            if index:
                out.append(",")
            _encode(item, out)
        out.append("]")
    elif isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ContractError("noncanonical_value", "object keys must be strings")
        out.append("{")
        for index, key in enumerate(sorted(value, key=_utf16_key)):
            if index:
                out.append(",")
            out.append(_string(key))
            out.append(":")
            _encode(value[key], out)
        out.append("}")
    else:
        raise ContractError("noncanonical_value", "unsupported JSON value type " + type(value).__name__)


def jcs(value: Any) -> bytes:
    """Return the RFC 8785 canonical UTF-8 bytes of ``value``; floats reject."""
    out: List[str] = []
    _encode(value, out)
    return "".join(out).encode("utf-8")


def _reject_constant(token: str) -> Any:
    raise ContractError("noncanonical_value", "non-finite number " + token)


def _reject_float(token: str) -> Any:
    raise ContractError("noncanonical_value", "floating-point number " + token)


def _unique_object(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("noncanonical_value", "duplicate JSON key " + key)
        result[key] = value
    return result


def loads(raw: bytes) -> Any:
    """Decode JSON bytes, rejecting duplicate keys, floats and non-finite numbers."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError("noncanonical_value", "input is not UTF-8") from error
    try:
        return json.loads(text, object_pairs_hook=_unique_object,
                          parse_float=_reject_float, parse_constant=_reject_constant)
    except json.JSONDecodeError as error:
        raise ContractError("invalid_json", str(error)) from error


# --------------------------------------------------------------------------
# Identities
# --------------------------------------------------------------------------

def domain_digest(domain: str, value: Any) -> str:
    """``sha256:`` hex of SHA-256(domain || NUL || JCS(value))."""
    if "\0" in domain:
        raise ContractError("invalid_domain", "hash domain contains NUL")
    hasher = hashlib.sha256(domain.encode("utf-8") + b"\0")
    hasher.update(jcs(value))
    return "sha256:" + hasher.hexdigest()


def bytes_digest(raw: bytes) -> str:
    """``sha256:`` hex of raw file bytes (inventory entries, manifests)."""
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _without(record: Mapping[str, Any], field: str) -> Dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ContractError("invalid_record", "record must be an object")
    return {key: value for key, value in record.items() if key != field}


def payload_digest(inventory: Mapping[str, Any]) -> str:
    """Payload digest: SHA-256("ara.payload/v1\\0" || JCS(inventory))."""
    return domain_digest(PAYLOAD_DOMAIN, inventory)


def contribution_id(envelope: Mapping[str, Any]) -> str:
    """Contribution ID over the envelope without its ``contribution_id`` field."""
    return domain_digest(CONTRIBUTION_DOMAIN, _without(envelope, "contribution_id"))


def capture_id(manifest: Mapping[str, Any]) -> str:
    """ara-cli ``ara.snapshot/v1`` capture ID over the manifest without ``capture_id``."""
    return domain_digest(CAPTURE_DOMAIN, _without(manifest, "capture_id"))


def record_id(domain: str, record: Mapping[str, Any]) -> str:
    """Identity of a record under its schema-specific domain.

    ``domain`` must equal ``record["schema"]``. Records with a self-identity
    field (see ``RECORD_ID_FIELDS``) exclude it; whole-record domains hash the
    complete value. Distinct domains keep identical bytes of different record
    kinds from sharing an identity.
    """
    if not isinstance(record, Mapping) or record.get("schema") != domain:
        raise ContractError("invalid_domain", "record schema does not match domain " + domain)
    if domain in RECORD_ID_FIELDS:
        return domain_digest(domain, _without(record, RECORD_ID_FIELDS[domain]))
    if domain in WHOLE_RECORD_DOMAINS:
        return domain_digest(domain, record)
    raise ContractError("invalid_domain", "unknown record domain " + domain)


def self_id_matches(record: Mapping[str, Any]) -> bool:
    """True when a record's stored self-identity equals its recomputed identity."""
    domain = record.get("schema") if isinstance(record, Mapping) else None
    field = RECORD_ID_FIELDS.get(domain) if isinstance(domain, str) else None
    if field is None:
        raise ContractError("invalid_domain", "record has no self-identity field")
    return record.get(field) == record_id(domain, record)


# --------------------------------------------------------------------------
# Semantic checks that JSON Schema cannot express
# --------------------------------------------------------------------------

def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise ContractError(code, message)


def _sorted_unique(items: List[Any], key: Any, what: str) -> None:
    keys = [key(item) for item in items]
    _require(all(left < right for left, right in zip(keys, keys[1:])),
             "unsorted_or_duplicate", what + " must be sorted and unique")


def check_inventory(inventory: Mapping[str, Any]) -> None:
    """Check ordering, root declarations and pointer targets of a payload inventory."""
    roots = inventory["roots"]
    _sorted_unique(roots, lambda root: root["name"], "roots")
    kinds = {root["name"]: root["kind"] for root in roots}
    entries, external = inventory["entries"], inventory["external"]
    path_key = lambda item: (item["root"], item["path"])  # noqa: E731
    _sorted_unique(entries, path_key, "entries")
    _sorted_unique(external, path_key, "external objects")
    located = [path_key(item) for item in entries] + [path_key(item) for item in external]
    _require(len(set(located)) == len(located), "duplicate_path", "entry and external paths overlap")
    for root, _ in located:
        _require(root in kinds, "undeclared_root", "undeclared root " + root)
    snapshot_roots = [name for name, kind in kinds.items() if kind == "ara-snapshot"]
    native = inventory["native"]
    if native is None:
        _require(not snapshot_roots, "ambiguous_root", "ara-snapshot root without native block")
    else:
        _require(snapshot_roots == [native["root"]], "ambiguous_root",
                 "exactly one ara-snapshot root must equal native.root")
        _require(native["root"] not in {item["root"] for item in external}, "ambiguous_root",
                 "the native root holds no external objects")
    for name in ("entry", "config"):
        target = inventory["execution"][name]
        if target is not None:
            _require(path_key(target) in set(located), "missing_object",
                     "execution." + name + " names no inventory object")


def native_entries(manifest_bytes: bytes, root: str, manifest_mode: str) -> List[Dict[str, Any]]:
    """Inventory entries for an ``ara snapshot`` package: snapshot.json plus ara/<path>."""
    manifest = loads(manifest_bytes)
    entries = [{"root": root, "path": "snapshot.json", "digest": bytes_digest(manifest_bytes),
                "size": len(manifest_bytes), "mode": manifest_mode}]
    for item in manifest["files"]:
        entries.append({"root": root, "path": "ara/" + item["path"], "digest": item["digest"],
                        "size": item["size"], "mode": item["mode"]})
    return sorted(entries, key=lambda entry: entry["path"])


def check_native_binding(inventory: Mapping[str, Any], manifest_bytes: bytes) -> None:
    """Verify that the inventory's native root mirrors the snapshot manifest exactly."""
    native = inventory["native"]
    _require(native is not None, "missing_object", "inventory has no native snapshot")
    manifest = loads(manifest_bytes)
    _require(jcs(manifest) == manifest_bytes, "identity_mismatch", "snapshot.json is not canonical")
    _require(manifest.get("format") == "ara.snapshot/v1", "identity_mismatch", "not ara.snapshot/v1")
    _require(capture_id(manifest) == manifest["capture_id"] == native["capture_id"],
             "identity_mismatch", "capture_id differs from the manifest")
    _require(manifest["fingerprint"] == native["fingerprint"], "identity_mismatch",
             "fingerprint differs from the manifest")
    held = [entry for entry in inventory["entries"] if entry["root"] == native["root"]]
    mode = next((entry["mode"] for entry in held if entry["path"] == "snapshot.json"), "0644")
    _require(held == native_entries(manifest_bytes, native["root"], mode), "inventory_mismatch",
             "native root entries differ from the snapshot manifest")


def check_contribution(envelope: Mapping[str, Any], inventory: Optional[Mapping[str, Any]] = None) -> None:
    """Check cross-field envelope rules and, given the inventory, the payload binding."""
    _require(envelope["request"].split(":", 1)[0] == envelope["publisher"], "actor_ownership",
             "request must carry the publisher prefix")
    lineage = envelope["lineage"]
    _sorted_unique(lineage["parents"], lambda item: item, "lineage.parents")
    _sorted_unique(lineage["uses"], lambda item: (item["source_key"], item["native_revision"],
                                                  item["selector"]), "lineage.uses")
    _require(envelope["contribution_id"] not in lineage["parents"], "invalid_lineage",
             "a contribution cannot be its own parent")
    _require(contribution_id(envelope) == envelope["contribution_id"], "identity_mismatch",
             "contribution_id does not match the envelope")
    if inventory is not None:
        check_inventory(inventory)
        _require(payload_digest(inventory) == envelope["payload_digest"], "identity_mismatch",
                 "payload_digest does not match the inventory")
        native = inventory["native"]
        _require(native is not None and native["capture_id"] == envelope["native"]["capture_id"]
                 and native["fingerprint"] == envelope["native"]["fingerprint"]
                 and envelope["native"]["snapshot"] == {"root": native["root"], "path": "snapshot.json"},
                 "identity_mismatch", "envelope native pointer differs from the inventory")


def check_attachment(attachment: Mapping[str, Any], inventory: Optional[Mapping[str, Any]] = None) -> None:
    """Request ownership, verification target agreement, file refs and record_id."""
    _require(attachment["request"].split(":", 1)[0] == attachment["publisher"], "actor_ownership",
             "request must carry the publisher prefix")
    body = attachment["body"]
    refs: List[Mapping[str, Any]] = []
    if attachment["kind"] in ("verification", "superseding_verdict"):
        _require(body["target"]["contribution_id"] == attachment["target"], "identity_mismatch",
                 "verification target differs from the attachment target")
        _sorted_unique(body["target"]["selectors"], lambda item: item, "target.selectors")
        refs += list(body["execution"]["raw_outputs"])
        refs += [ref for ref in [body["method"]["config"]] if ref is not None]
        refs += [item["evidence"] for item in body["observations"] if item["evidence"] is not None]
    elif attachment["kind"] in ("review_attestation", "argument_check"):
        refs.append(body["document"])
    if inventory is not None:
        check_inventory(inventory)
        _require(payload_digest(inventory) == attachment["payload_digest"], "identity_mismatch",
                 "payload_digest does not match the attachment inventory")
        located = {(item["root"], item["path"]) for item in inventory["entries"] + inventory["external"]}
        for ref in refs:
            _require((ref["root"], ref["path"]) in located, "missing_object",
                     "attachment body names a file outside its inventory")
    _require(record_id("ara.attachment/v1", attachment) == attachment["record_id"], "identity_mismatch",
             "record_id does not match the attachment")


def check_role_policy(policy: Mapping[str, Any]) -> None:
    """Exactly one integration PM, one continuity writer per source key, sorted actors and roles."""
    actors = policy["actors"]
    _sorted_unique(actors, lambda actor: actor["actor_id"], "actors")
    for actor in actors:
        _sorted_unique(actor["roles"], lambda role: role, "roles of " + actor["actor_id"])
        if {"publisher", "continuity_writer"} & set(actor["roles"]):
            _require(actor["source_key"] is not None, "invalid_roles",
                     actor["actor_id"] + " needs a source_key")
    managers = [actor["actor_id"] for actor in actors if "integration_pm" in actor["roles"]]
    _require(managers == [policy["integration_pm"]], "invalid_roles", "exactly one integration PM required")
    writers = [actor["source_key"] for actor in actors if "continuity_writer" in actor["roles"]]
    _require(len(set(writers)) == len(writers), "invalid_roles", "one continuity writer per source key")
    known = {actor["actor_id"] for actor in actors}
    for factor in policy["independence"]["shared_factors"]:
        _sorted_unique(factor["actors"], lambda actor: actor, "shared factor actors")
        _require(set(factor["actors"]) <= known, "invalid_roles", "shared factor names an unknown actor")
    _require(record_id("ara.role-policy/v1", policy) == policy["policy_id"], "identity_mismatch",
             "policy_id does not match the policy")


def check_visibility(snapshot: Mapping[str, Any]) -> None:
    """Records sorted by sequence, sequences unique across lists and not beyond the snapshot."""
    for name in ("contributions", "attachments"):
        _sorted_unique(snapshot[name], lambda item: item["sequence"], name)
    sequences = [item["sequence"] for item in snapshot["contributions"] + snapshot["attachments"]]
    _require(len(set(sequences)) == len(sequences), "unsorted_or_duplicate", "sequences must be unique")
    _require(all(sequence <= snapshot["sequence"] for sequence in sequences), "invalid_sequence",
             "a listed record is newer than the snapshot")
    _require(record_id("ara.visibility/v1", snapshot) == snapshot["visibility_id"], "identity_mismatch",
             "visibility_id does not match the snapshot")


def check_integration_receipt(receipt: Mapping[str, Any]) -> None:
    """Sorted mappings, external references and acknowledgments; matching record_id."""
    _require(receipt["request"].split(":", 1)[0] == receipt["integration_pm"], "actor_ownership",
             "request must carry the integration PM prefix")
    _sorted_unique(receipt["acknowledgments"], lambda item: item, "acknowledgments")
    if receipt["kind"] == "import":
        _sorted_unique(receipt["identity_mapping"], lambda item: (
            item["source_key"], item["original"], item["layer"], item["path"], item["target"]), "identity_mapping")
        _sorted_unique(receipt["external_references"], lambda item: (
            item["contribution_id"], item["source_key"], item["native_revision"], item["path"]),
            "external_references")
    else:
        _sorted_unique(receipt["review_decisions"], lambda item: item, "review_decisions")
    _require(record_id("ara.integration-receipt/v1", receipt) == receipt["record_id"], "identity_mismatch",
             "record_id does not match the receipt")


class RequestLedger:
    """Request idempotency: one (community, publisher, request) binds one record identity.

    Contributions and attachments share the namespace. ``bind`` returns
    ``"accepted"`` the first time and ``"replay"`` for an exact retry; any other
    record under an accepted request raises ``request_conflict``.
    """

    def __init__(self) -> None:
        self._bound: Dict[Tuple[str, str, str], str] = {}

    def bind(self, community: str, publisher: str, request: str, identity: str) -> str:
        _require(request.split(":", 1)[0] == publisher, "actor_ownership",
                 "request must carry the publisher prefix")
        key = (community, publisher, request)
        previous = self._bound.get(key)
        if previous is None:
            self._bound[key] = identity
            return "accepted"
        _require(previous == identity, "request_conflict",
                 "request " + request + " is already bound to " + previous)
        return "replay"

    def bind_record(self, record: Mapping[str, Any]) -> str:
        """Bind a contribution envelope or attachment by its recomputed identity."""
        publisher = record.get("integration_pm", record.get("publisher"))
        return self.bind(record["community"], publisher, record["request"],
                         record_id(record["schema"], record))
