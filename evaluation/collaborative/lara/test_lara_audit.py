"""Review authority, audited coverage, supersession and map-scope rules (stage L1, plan 03).

Run from the protocol repository root:
    python3 -m unittest discover -s evaluation/collaborative -p 'test_*.py' -v
"""

import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
for _path in (str(HERE), str(HERE.parent)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import identity as I  # noqa: E402
import lara_audit as A  # noqa: E402
import lara_identity as L  # noqa: E402

VECTORS = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))


def rec(name):
    return copy.deepcopy(VECTORS["records"][name]["record"])


def raises(test, code, function, *args, **kwargs):
    with test.assertRaises(L.ContractError) as caught:
        function(*args, **kwargs)
    test.assertEqual(caught.exception.code, code)


def reissue(record, **changes):
    changed = copy.deepcopy(record)
    changed.update(changes)
    return L.with_id(changed)


class Attestations(unittest.TestCase):
    def setUp(self):
        self.policy = rec("role_policy")
        self.binding = rec("binding_a")

    def test_authorized_review_passes(self):
        A.check_attestation(rec("attestation_bob_a"), self.binding, self.policy)
        A.check_attestation(rec("attestation_bob_c"), rec("binding_c"), self.policy)
        I.check_role_policy(self.policy)

    def test_producer_cannot_self_attest(self):
        raises(self, "self_review", A.check_attestation, rec("attestation_alice_a"), self.binding, self.policy)
        # carol is an authorized reviewer but authored binding_c's formalization.
        own = reissue(rec("attestation_bob_c"), reviewer="carol")
        raises(self, "self_review", A.check_attestation, own, rec("binding_c"), self.policy)

    def test_unauthorized_review_rejected(self):
        raises(self, "unauthorized_reviewer", A.check_attestation, rec("attestation_dave_a"), self.binding, self.policy)
        other_policy = reissue(rec("attestation_bob_a"), role_policy="sha256:" + "00" * 32)
        raises(self, "unauthorized_reviewer", A.check_attestation, other_policy, self.binding, self.policy)

    def test_changed_covered_input_invalidates_the_attestation(self):
        approval = rec("attestation_bob_a")
        changes = {
            "argument": dict(self.binding["argument"], digest="sha256:" + "01" * 32),
            "policy": dict(self.binding["policy"], policy_digest="sha256:" + "02" * 32),
            "registry": rec("registry_r2")["registry_id"],
            "native": dict(self.binding["native"], capture_id="sha256:" + "03" * 32),
        }
        for field, value in changes.items():
            with self.subTest(field):
                changed = reissue(self.binding, **{field: value})
                raises(self, "stale_review", A.check_attestation, approval, changed, self.policy)
                states, ignored = A.claim_audit_states(changed, [approval], self.policy)
                self.assertEqual(states, {"c1": "unreviewed"})
                self.assertEqual(ignored, [(approval["attestation_id"], "stale_review")])

    def test_reviewed_selectors_must_match_the_binding(self):
        wrong = rec("attestation_bob_a")
        wrong["reviewed"][0]["selector"] = "C99"
        raises(self, "invalid_reference", A.check_attestation, L.with_id(wrong), self.binding, self.policy)

    def test_tampered_attestation_rejects(self):
        tampered = rec("attestation_bob_a")
        tampered["disposition"] = "rejected"
        raises(self, "identity_mismatch", A.check_attestation, tampered, self.binding, self.policy)


class AuditedCoverage(unittest.TestCase):
    def setUp(self):
        self.policy = rec("role_policy")
        self.binding = rec("binding_a")
        self.bob, self.alice, self.dave = rec("attestation_bob_a"), rec("attestation_alice_a"), rec("attestation_dave_a")
        self.dispute, self.resolve = rec("attestation_carol_dispute_a"), rec("attestation_carol_resolve_a")

    def states(self, *records, open_disputes=()):
        return A.claim_audit_states(self.binding, list(records), self.policy, open_disputes)

    def test_approval_counts(self):
        self.assertEqual(self.states(self.bob), ({"c1": "approved"}, []))
        self.assertIsNone(A.binding_audited(self.binding, [self.bob], self.policy))

    def test_self_review_and_unauthorized_review_supply_no_coverage(self):
        states, ignored = self.states(self.alice, self.dave)
        self.assertEqual(states, {"c1": "unreviewed"})
        self.assertEqual(sorted(code for _, code in ignored), ["self_review", "unauthorized_reviewer"])
        self.assertEqual(A.binding_audited(self.binding, [self.alice, self.dave], self.policy), "unreviewed_binding")

    def test_dispute_outranks_approval_until_withdrawn(self):
        self.assertEqual(self.states(self.bob, self.dispute)[0], {"c1": "disputed"})
        self.assertEqual(A.binding_audited(self.binding, [self.bob, self.dispute], self.policy), "disputed_binding")
        self.assertEqual(self.states(self.bob, self.dispute, self.resolve), ({"c1": "approved"}, []))
        rejected = reissue(self.dispute, disposition="rejected")
        self.assertEqual(self.states(self.bob, rejected)[0], {"c1": "rejected"})

    def test_open_dispute_attachment_suspends_an_approval(self):
        self.assertEqual(self.states(self.bob, open_disputes={self.bob["attestation_id"]})[0], {"c1": "disputed"})

    def test_supersession_by_another_reviewer_does_not_resolve_a_dispute(self):
        link = dict(self.resolve["linkage"], record=self.dispute["attestation_id"])
        foreign = reissue(self.resolve, reviewer="bob", linkage=link)
        states, ignored = self.states(self.bob, self.dispute, foreign)
        self.assertEqual(states, {"c1": "disputed"})
        self.assertIn((foreign["attestation_id"], "invalid_supersession"), ignored)


class Supersession(unittest.TestCase):
    def test_attestation_supersession_needs_same_reviewer_target_inputs_and_scope(self):
        prior, new = rec("attestation_carol_dispute_a"), rec("attestation_carol_resolve_a")
        A.check_supersession(prior, new)
        target = dict(new["target"], argument={"kind": "initial_payload"})
        for changed in (reissue(new, reviewer="bob"), reissue(new, target=target),
                        reissue(new, covered=dict(new["covered"], registry=rec("registry_r2")["registry_id"])),
                        reissue(new, linkage=dict(new["linkage"], relation="disputes"))):
            raises(self, "invalid_supersession", A.check_supersession, prior, changed)

    def test_check_supersession_needs_same_verifier_target_method_and_scope(self):
        prior = rec("check_unavailable")
        rerun = reissue(rec("check_a"), supersedes=prior["check_id"])
        A.check_supersession(prior, rerun)
        checker = copy.deepcopy(rerun["checker"])
        checker["backends"].append({"name": "ra", "version": 1})
        target = {"kind": "contribution", "contribution_id": "sha256:" + "00" * 32, "argument": {"kind": "enclosing_attachment"}}
        for changed in (reissue(rerun, verifier="carol"), reissue(rerun, target=target), reissue(rerun, checker=checker),
                        reissue(rerun, policy=dict(rerun["policy"], lara_policy="ord-setting-v2")),
                        reissue(rerun, supersedes=None)):
            raises(self, "invalid_supersession", A.check_supersession, prior, changed)
        raises(self, "invalid_supersession", A.check_supersession, rec("attestation_bob_a"), rerun)
        raises(self, "invalid_supersession", A.check_supersession, rec("map_revision"), rec("map_revision"))


class MapRevisions(unittest.TestCase):
    def setUp(self):
        self.policy = rec("role_policy")
        self.map = rec("map_revision")
        self.bindings = {b["binding_id"]: b for b in (rec("binding_a"), rec("binding_c"))}
        self.reviews = [rec("attestation_bob_a"), rec("attestation_bob_c")]

    def check(self, revision, reviews=None, **kwargs):
        A.check_map_revision(revision, self.bindings, self.reviews if reviews is None else reviews, self.policy, **kwargs)

    def test_audited_map_passes(self):
        self.check(self.map)
        L.check_argument_check(rec("check_map"), map_revision=self.map)

    def test_self_review_unreviewed_and_disputed_members_cannot_enter_audited_scope(self):
        self_only = [rec("attestation_bob_c"), rec("attestation_alice_a")]
        raises(self, "unreviewed_binding", self.check, self.map, self_only)
        disputed = self.reviews + [rec("attestation_carol_dispute_a")]
        raises(self, "disputed_binding", self.check, self.map, disputed)
        raises(self, "unreviewed_binding", self.check, self.map, [rec("attestation_bob_a")])

    def test_exploratory_scope_may_hold_unreviewed_members(self):
        exploratory = reissue(self.map, coverage={"scope": "exploratory", "policy": "Every member with an argument; not audited."})
        self.check(exploratory, [])
        self.assertNotEqual(exploratory["map_revision_id"], self.map["map_revision_id"])

    def test_excluded_disputed_member_stays_visible_without_coverage(self):
        paper_c = self.map["members"][1]
        reduced = reissue(self.map, members=self.map["members"][:1], exclusions=sorted(
            self.map["exclusions"] + [{"contribution_id": paper_c["contribution_id"], "reason": "disputed_binding",
                                       "detail": "carol's binding is disputed."}], key=lambda item: item["contribution_id"]))
        self.check(reduced, [rec("attestation_bob_a")])
        self.assertIn(paper_c["contribution_id"], reduced["population"]["contributions"])

    def test_population_is_partitioned(self):
        missing = reissue(self.map, exclusions=[])
        raises(self, "invalid_population", self.check, missing)
        both = reissue(self.map, exclusions=sorted(self.map["exclusions"] + [
            {"contribution_id": self.map["members"][0]["contribution_id"], "reason": "other", "detail": "x"}],
            key=lambda item: item["contribution_id"]))
        raises(self, "invalid_population", self.check, both)
        duplicate = reissue(self.map, members=[self.map["members"][0], dict(self.map["members"][1], alias="paper_a")])
        raises(self, "unsorted_or_duplicate", self.check, duplicate)

    def test_member_contract_must_match_the_map(self):
        raises(self, "vocabulary_mismatch", self.check, reissue(self.map, registry=rec("registry_r2")["registry_id"]))
        raises(self, "incompatible_policy", self.check,
               reissue(self.map, policy=dict(self.map["policy"], policy_digest="sha256:" + "05" * 32)))
        members = copy.deepcopy(self.map["members"])
        members[0]["argument"]["digest"] = "sha256:" + "06" * 32
        raises(self, "identity_mismatch", self.check, reissue(self.map, members=members))

    def test_vocabulary_extension_requires_recheck_or_exclusion(self):
        extended = reissue(self.map, registry=rec("registry_r2")["registry_id"])
        self.assertNotEqual(extended["map_revision_id"], self.map["map_revision_id"])
        raises(self, "vocabulary_mismatch", self.check, extended)
        # Rebinding binding_a under r2 invalidates bob's approval of the r1 version.
        rebound = reissue(rec("binding_a"), registry=rec("registry_r2")["registry_id"])
        states, ignored = A.claim_audit_states(rebound, self.reviews, self.policy)
        self.assertEqual(states, {"c1": "unreviewed"})
        self.assertEqual([code for _, code in ignored], ["stale_review", "stale_review"])

    def test_identity_changes_with_every_scope_input(self):
        base = self.map["map_revision_id"]
        population = dict(self.map["population"], sequence=13, contributions=sorted(
            self.map["population"]["contributions"] + ["sha256:" + "e5" * 32]))
        checker = copy.deepcopy(self.map["checker"])
        checker["build"]["provenance"] = "release"
        variants = {
            "roster": dict(members=list(reversed(self.map["members"]))),
            "population": dict(population=population),
            "visibility": dict(population=dict(self.map["population"], visibility_id="sha256:" + "07" * 32)),
            "policy": dict(policy=dict(self.map["policy"], policy_digest="sha256:" + "08" * 32)),
            "vocabulary": dict(registry=rec("registry_r2")["registry_id"]),
            "checker": dict(checker=checker),
            "coverage": dict(coverage=dict(self.map["coverage"], scope="exploratory")),
            "manifest": dict(manifest=dict(self.map["manifest"], digest="sha256:" + "09" * 32)),
        }
        seen = {base}
        for name, changes in variants.items():
            with self.subTest(name):
                identity = reissue(self.map, **changes)["map_revision_id"]
                self.assertNotIn(identity, seen)
                seen.add(identity)

    def test_identity_excludes_outputs_and_new_scope_keeps_old_verdict(self):
        schema = json.loads((HERE / "map-revision.schema.json").read_text(encoding="utf-8"))
        for output in ("outcome", "statuses", "verdict", "exit_status", "result"):
            self.assertNotIn(output, schema["properties"])
        contested = rec("check_map")
        self.assertEqual({row["status"] for row in contested["statuses"]}, {"contested"})
        smaller = reissue(self.map, members=self.map["members"][:1], exclusions=sorted(self.map["exclusions"] + [
            {"contribution_id": self.map["members"][1]["contribution_id"], "reason": "other", "detail": "Dropped from the roster."}],
            key=lambda item: item["contribution_id"]))
        self.assertNotEqual(smaller["map_revision_id"], self.map["map_revision_id"])
        # The contested verdict still binds its own revision and cannot be read as the smaller map's result.
        L.check_argument_check(contested, map_revision=self.map)
        raises(self, "identity_mismatch", L.check_argument_check, contested, map_revision=smaller)
        newer = reissue(contested, target={"kind": "map_revision", "map_revision_id": smaller["map_revision_id"]},
                        supersedes=contested["check_id"])
        raises(self, "invalid_supersession", A.check_supersession, contested, newer)


if __name__ == "__main__":
    unittest.main()
