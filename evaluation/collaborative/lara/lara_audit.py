#!/usr/bin/env python3
"""Review authority, supersession and map-scope rules for the ARA-to-Lara contracts.

Standard library only. These functions decide which review attestations count
toward audited coverage and whether a map revision is a well-formed scope.
They never change ARA claim status and never treat a checker verdict, Lara's
own ``audit-status`` annotation, or a reproduction as review.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import lara_identity as L  # noqa: E402  (sibling module in this directory)

ContractError = L.ContractError
require = L.require



def has_role(role_policy: Mapping[str, Any], actor: str, role: str) -> bool:
    """True when ``actor`` holds ``role`` in the pinned ``ara.role-policy/v1``."""
    return any(item["actor_id"] == actor and role in item["roles"] for item in role_policy["actors"])


def check_attestation(attestation: Mapping[str, Any], binding: Mapping[str, Any],
                      role_policy: Mapping[str, Any]) -> None:
    """Raise unless ``attestation`` is an authorized, non-self review of exactly this binding.

    Codes: ``identity_mismatch``, ``stale_review`` (a covered input changed),
    ``invalid_reference``, ``self_review`` (checked before authority, so a
    producer's own approval is reported as self-review), ``unauthorized_reviewer``.
    """
    require(L.self_id_matches(attestation), "identity_mismatch", "attestation_id does not match")
    covered = attestation["covered"]
    require(attestation["native"] == binding["native"]
            and covered["argument_digest"] == binding["argument"]["digest"]
            and covered["binding_id"] == binding["binding_id"]
            and covered["policy"] == binding["policy"]
            and covered["registry"] == binding["registry"],
            "stale_review", "a covered input differs from the current binding")
    L.sorted_unique(attestation["reviewed"], lambda item: item["lara_claim"], "reviewed")
    claims = {claim["lara_id"]: claim for claim in binding["claims"]}
    for item in attestation["reviewed"]:
        claim = claims.get(item["lara_claim"])
        require(claim is not None and claim["source"]["selector"] == item["selector"], "invalid_reference",
                item["lara_claim"] + " is not a selected claim with that selector")
    linkage = attestation["linkage"]
    if linkage is not None:
        L.sorted_unique(linkage["affected_claims"], lambda item: item, "linkage.affected_claims")
        reviewed = {item["lara_claim"] for item in attestation["reviewed"]}
        require(set(linkage["affected_claims"]) <= reviewed, "invalid_reference",
                "affected claims must be reviewed claims")
        require(linkage["record"] != attestation["attestation_id"], "invalid_supersession", "self link")
    require(attestation["community"] == binding["community"] == role_policy["community"], "identity_mismatch",
            "community differs")
    authors = {claims[item["lara_claim"]]["formalization"]["author"] for item in attestation["reviewed"]}
    require(attestation["reviewer"] != binding["producer"] and attestation["reviewer"] not in authors,
            "self_review", "a producer or formalization author cannot review its own formalization")
    require(attestation["role_policy"] == role_policy["policy_id"]
            and has_role(role_policy, attestation["reviewer"], "authorized_reviewer"),
            "unauthorized_reviewer", attestation["reviewer"] + " is not an authorized reviewer under this policy")


def _attestation_key(record: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (record["community"], record["reviewer"], L.I.jcs(record["target"]), L.I.jcs(record["native"]),
            L.I.jcs(record["covered"]), tuple(item["lara_claim"] for item in record["reviewed"]))


def _check_key(record: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (record["community"], record["verifier"], L.I.jcs(record["target"]), record["scope"],
            L.I.jcs(record["checker"]), L.I.jcs(record["policy"]), L.I.jcs(record["inputs"]))


def check_supersession(prior: Mapping[str, Any], new: Mapping[str, Any]) -> None:
    """Supersession only within the same verifier, exact target, method/configuration and scope."""
    require(prior["schema"] == new["schema"], "invalid_supersession", "records of different kinds")
    if new["schema"] == "ara.lara-review-attestation/v1":
        link = new["linkage"]
        require(link is not None and link["relation"] == "supersedes" and link["record"] == prior["attestation_id"],
                "invalid_supersession", "the new attestation does not name the prior one")
        require(_attestation_key(prior) == _attestation_key(new), "invalid_supersession",
                "supersession needs the same reviewer, target, inputs and reviewed claims")
    elif new["schema"] == "ara.lara-argument-check/v1":
        require(new["supersedes"] == prior["check_id"], "invalid_supersession", "the new check does not name the prior one")
        require(_check_key(prior) == _check_key(new), "invalid_supersession",
                "supersession needs the same verifier, target, checker, policy, inputs and scope")
    else:
        raise ContractError("invalid_supersession", "records of this kind are never superseded")


def claim_audit_states(binding: Mapping[str, Any], attestations: Iterable[Mapping[str, Any]],
                       role_policy: Mapping[str, Any], open_disputes: Iterable[str] = ()
                       ) -> Tuple[Dict[str, str], List[Tuple[str, str]]]:
    """Per selected claim, its audit state, plus ``(attestation_id, code)`` for ignored records.

    Ignored records (unauthorized, self-review, stale, malformed) stay visible
    to the caller but supply no review. A valid supersession hides the earlier
    record; a current ``disputed`` or ``rejected`` attestation outranks any
    approval, and an approval named in ``open_disputes`` (open ``ara.dispute/v1``
    attachments) does not count.
    """
    valid: List[Mapping[str, Any]] = []
    ignored: List[Tuple[str, str]] = []
    for record in attestations:
        try:
            check_attestation(record, binding, role_policy)
        except ContractError as error:
            ignored.append((record["attestation_id"], error.code))
        else:
            valid.append(record)
    by_id = {record["attestation_id"]: record for record in valid}
    superseded = set()
    for record in valid:
        link = record["linkage"]
        if link is None or link["relation"] != "supersedes" or link["record"] not in by_id:
            continue
        try:
            check_supersession(by_id[link["record"]], record)
        except ContractError:
            ignored.append((record["attestation_id"], "invalid_supersession"))
        else:
            superseded.add(link["record"])
    disputed_approvals = set(open_disputes)
    current = [record for record in valid if record["attestation_id"] not in superseded]
    states: Dict[str, str] = {}
    for claim in binding["claims"]:
        covering = [record for record in current
                    if claim["lara_id"] in {item["lara_claim"] for item in record["reviewed"]}]
        dispositions = {record["disposition"] for record in covering
                        if record["disposition"] != "approved" or record["attestation_id"] not in disputed_approvals}
        if "rejected" in dispositions:
            states[claim["lara_id"]] = "rejected"
        elif "disputed" in dispositions or (covering and not dispositions):
            states[claim["lara_id"]] = "disputed"
        elif "approved" in dispositions:
            states[claim["lara_id"]] = "approved"
        else:
            states[claim["lara_id"]] = "unreviewed"
    return states, ignored


def binding_audited(binding: Mapping[str, Any], attestations: Iterable[Mapping[str, Any]],
                    role_policy: Mapping[str, Any], open_disputes: Iterable[str] = ()) -> Optional[str]:
    """``None`` when every selected claim is approved, else the exclusion reason."""
    states, _ = claim_audit_states(binding, attestations, role_policy, open_disputes)
    values = set(states.values())
    if values <= {"approved"}:
        return None
    return "disputed_binding" if values & {"disputed", "rejected"} else "unreviewed_binding"


def check_map_revision(map_revision: Mapping[str, Any], bindings: Mapping[str, Mapping[str, Any]],
                       attestations: Iterable[Mapping[str, Any]] = (),
                       role_policy: Optional[Mapping[str, Any]] = None,
                       open_disputes: Iterable[str] = ()) -> None:
    """Population partition, member agreement and, for audited scope, authorized review."""
    members, exclusions = map_revision["members"], map_revision["exclusions"]
    aliases = [member["alias"] for member in members]
    require(len(set(aliases)) == len(aliases), "unsorted_or_duplicate", "member aliases must be unique")
    population = map_revision["population"]["contributions"]
    L.sorted_unique(population, lambda item: item, "population.contributions")
    L.sorted_unique(exclusions, lambda item: item["contribution_id"], "exclusions")
    if map_revision["checker"] is not None:
        L.sorted_unique(map_revision["checker"]["backends"], lambda b: (b["name"], b["version"]), "backends")
        L.sorted_unique(map_revision["checker"]["theories"], lambda item: item, "theories")
    included = {member["contribution_id"] for member in members}
    excluded = {item["contribution_id"] for item in exclusions}
    require(not included & excluded, "invalid_population", "a contribution is both member and excluded")
    require(included | excluded == set(population), "invalid_population",
            "members and exclusions must partition the intended population")
    audited = map_revision["coverage"]["scope"] == "audited"
    attestations = list(attestations)
    for member in members:
        binding = bindings.get(member["binding_id"])
        require(binding is not None, "missing_object", member["alias"] + " names an unknown binding")
        L.check_binding(binding)
        require(binding["argument"]["digest"] == member["argument"]["digest"]
                and binding["native"]["source_key"] == member["source_key"]
                and binding["native"]["fingerprint"] == member["native_revision"],
                "identity_mismatch", member["alias"] + " member identity differs from its binding")
        require(binding["policy"] == map_revision["policy"], "incompatible_policy",
                member["alias"] + " was bound under another policy")
        require(binding["registry"] == map_revision["registry"], "vocabulary_mismatch",
                member["alias"] + " was bound under another registry")
        if audited:
            require(role_policy is not None, "unreviewed_binding", "audited scope needs the role policy")
            reason = binding_audited(binding, attestations, role_policy, open_disputes)
            require(reason is None, reason or "", member["alias"] + " lacks authorized, undisputed review")
    require(L.self_id_matches(map_revision), "identity_mismatch", "map_revision_id does not match")
