"""Identity, binding, registry and check-record rules for the stage-L1 Lara contracts.

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
import lara_identity as L  # noqa: E402

VECTORS = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))
BASE_VECTORS = json.loads((HERE.parent / "vectors.json").read_text(encoding="utf-8"))
ARG_A = VECTORS["files"]["argument_a"].encode("utf-8")


def rec(name):
    return copy.deepcopy(VECTORS["records"][name]["record"])


def raises(test, code, function, *args, **kwargs):
    with test.assertRaises(L.ContractError) as caught:
        function(*args, **kwargs)
    test.assertEqual(caught.exception.code, code)


class Identities(unittest.TestCase):
    def test_expected_ids_recompute(self):
        for name, case in VECTORS["records"].items():
            with self.subTest(name):
                record = case["record"]
                if record["schema"] in L.LARA_ID_FIELDS:
                    self.assertEqual(L.lara_record_id(record), case["expected_id"])
                    self.assertTrue(L.self_id_matches(record))
                    self.assertEqual(record[L.LARA_ID_FIELDS[record["schema"]]], case["expected_id"])
                else:
                    self.assertEqual(I.record_id(record["schema"], record), case["expected_id"])

    def test_domain_is_the_schema_value_and_self_id_is_excluded(self):
        descriptor = rec("setting_a")
        body = {key: value for key, value in descriptor.items() if key != "descriptor_id"}
        self.assertEqual(descriptor["descriptor_id"], I.domain_digest("ara.lara-setting-descriptor/v1", body))
        tampered = dict(descriptor, descriptor_id="sha256:" + "00" * 32)
        self.assertEqual(L.lara_record_id(tampered), descriptor["descriptor_id"])
        self.assertFalse(L.self_id_matches(tampered))
        relabeled = dict(body, schema="ara.lara-system-descriptor/v1")
        self.assertNotEqual(L.lara_record_id(relabeled), descriptor["descriptor_id"])
        raises(self, "invalid_domain", L.lara_record_id, {"schema": "ara.attachment/v1"})

    def test_every_lara_domain_is_new(self):
        self.assertFalse(set(L.LARA_ID_FIELDS) & set(I.RECORD_ID_FIELDS))
        self.assertTrue(all(schema.startswith("ara.lara-") for schema in L.LARA_ID_FIELDS))


class Bindings(unittest.TestCase):
    def setUp(self):
        self.binding = rec("binding_a")
        self.registry = rec("registry_r1")

    def test_base_bindings(self):
        L.check_binding(self.binding, ARG_A, self.registry)
        L.check_binding(rec("binding_c"), VECTORS["files"]["argument_c"].encode("utf-8"), self.registry)
        self.assertEqual(L.argument_artifact(ARG_A), ("ord_setting_demo", "sha256:" + self.binding["native"]["fingerprint"]))

    def test_argument_to_snapshot_hash_mismatch_rejects(self):
        other = BASE_VECTORS["snapshots"][2]["fingerprint"]
        stale = ARG_A.replace(self.binding["native"]["fingerprint"].encode(), other.encode())
        binding = L.with_id(dict(self.binding, argument=dict(self.binding["argument"], digest=I.bytes_digest(stale))))
        raises(self, "snapshot_mismatch", L.check_binding, binding, stale)
        declared = copy.deepcopy(self.binding)
        declared["argument"]["artifact"]["digest"] = "sha256:" + other
        raises(self, "snapshot_mismatch", L.check_binding, L.with_id(declared))
        # A mode-only snapshot change keeps the fingerprint the header names but changes the capture ID,
        # so the binding (and every review of it) changes identity too.
        moved = L.with_id(dict(self.binding, native=dict(self.binding["native"],
                                                         capture_id=BASE_VECTORS["snapshots"][1]["capture_id"])))
        L.check_binding(moved, ARG_A)
        self.assertNotEqual(moved["binding_id"], self.binding["binding_id"])

    def test_argument_bytes_must_match(self):
        raises(self, "identity_mismatch", L.check_binding, self.binding, ARG_A + b"\n")
        raises(self, "invalid_argument", L.argument_artifact, b"# only a comment\npolicy p\n")
        raises(self, "invalid_argument", L.argument_artifact, b"\xff")

    def test_elements_are_closed_and_sorted(self):
        orphan = copy.deepcopy(self.binding)
        orphan["claims"][0]["elements"].remove("e3")
        raises(self, "invalid_reference", L.check_binding, L.with_id(orphan))
        unbound = copy.deepcopy(self.binding)
        unbound["claims"][0]["elements"].append("z9")
        raises(self, "invalid_reference", L.check_binding, L.with_id(unbound))
        unsorted = copy.deepcopy(self.binding)
        unsorted["elements"].reverse()
        raises(self, "unsorted_or_duplicate", L.check_binding, L.with_id(unsorted))

    def test_registry_agreement(self):
        raises(self, "vocabulary_mismatch", L.check_binding, self.binding, None, rec("registry_r2"))
        unknown = copy.deepcopy(self.binding)
        unknown["claims"][0]["settings"] = [rec("setting_b")["descriptor_id"]]
        raises(self, "vocabulary_mismatch", L.check_binding, L.with_id(unknown), None, self.registry)

    def test_declared_audit_status_is_not_review(self):
        # The producer's 'reviewed' label is carried verbatim and validated as data only.
        self.assertEqual(self.binding["claims"][0]["formalization"]["declared_audit_status"], "reviewed")
        self.assertEqual(self.binding["producer"], self.binding["claims"][0]["formalization"]["author"])


class Settings(unittest.TestCase):
    def test_same_setting_replications_share_a_descriptor_id(self):
        first, second = VECTORS["replications"]
        self.assertNotEqual(first["value"], second["value"])
        self.assertNotEqual(first["contribution_id"], second["contribution_id"])
        self.assertEqual(L.lara_record_id(first["setting"]), L.lara_record_id(second["setting"]))
        self.assertEqual(first["setting"]["descriptor_id"], rec("setting_a")["descriptor_id"])

    def test_shared_dataset_name_does_not_make_a_shared_setting(self):
        a, b = rec("setting_a"), rec("setting_b")
        self.assertEqual(a["dataset"], b["dataset"])
        self.assertNotEqual(a["evaluator"]["config_digest"], b["evaluator"]["config_digest"])
        self.assertNotEqual(a["descriptor_id"], b["descriptor_id"])

    def test_every_bound_field_changes_the_id(self):
        base = rec("setting_a")
        changes = {
            "dataset.digest": "sha256:" + "01" * 32, "dataset.split.digest": "sha256:" + "02" * 32,
            "evaluator.revision": "fedcba9876543210fedcba9876543210fedcba98", "metric.polarity": "lower_is_better",
            "metric.definition_digest": "sha256:" + "03" * 32, "controls.0.value": "256",
            "replication.1.treatment": "fixed", "replication.1.value": "0",
        }
        seen = {base["descriptor_id"]}
        for path, value in changes.items():
            with self.subTest(path):
                changed = copy.deepcopy(base)
                node = changed
                keys = path.split(".")
                for key in keys[:-1]:
                    node = node[int(key)] if isinstance(node, list) else node[key]
                node[keys[-1]] = value
                identity = L.lara_record_id(changed)
                self.assertNotIn(identity, seen)
                seen.add(identity)

    def test_descriptor_order_rules(self):
        unsorted = copy.deepcopy(rec("setting_a"))
        unsorted["controls"].reverse()
        raises(self, "unsorted_or_duplicate", L.check_setting_descriptor, L.with_id(unsorted))


class Registries(unittest.TestCase):
    def setUp(self):
        self.r1, self.r2 = rec("registry_r1"), rec("registry_r2")

    def resettle(self, registry, **changes):
        changed = copy.deepcopy(registry)
        changed.update(changes)
        changed["settings"].sort(key=lambda entry: entry["descriptor"]["descriptor_id"])
        return L.with_id(changed)

    def test_base_and_extension(self):
        L.check_registry(self.r1)
        L.check_registry(self.r2)
        L.check_registry_extension(self.r1, self.r2)
        self.assertNotEqual(self.r1["registry_id"], self.r2["registry_id"])
        self.assertEqual(self.r2["previous"], self.r1["registry_id"])

    def test_one_meaning_per_symbol(self):
        b = rec("setting_b")
        same_pair = self.resettle(self.r1, settings=self.r1["settings"] + [
            {"measurand": "accuracy", "setting": "imagenet_val", "descriptor": b}])
        raises(self, "symbol_conflict", L.check_registry, same_pair)
        shared_setting = self.resettle(self.r1, settings=self.r1["settings"] + [
            {"measurand": "top5", "setting": "imagenet_val", "descriptor": b}])
        raises(self, "symbol_conflict", L.check_registry, shared_setting)
        lower = copy.deepcopy(b)
        lower["metric"]["polarity"] = "lower_is_better"
        two_metrics = self.resettle(self.r1, settings=self.r1["settings"] + [
            {"measurand": "accuracy", "setting": "imagenet_val_crop95", "descriptor": L.with_id(lower)}])
        raises(self, "symbol_conflict", L.check_registry, two_metrics)
        system_clash = copy.deepcopy(self.r1)
        system_clash["systems"][0]["symbol"] = "accuracy"
        raises(self, "symbol_conflict", L.check_registry, L.with_id(system_clash))

    def test_extension_keeps_every_symbol(self):
        rebound = copy.deepcopy(self.r2)
        for entry in rebound["settings"]:
            entry["setting"] = {"imagenet_val": "imagenet_val_crop95", "imagenet_val_crop95": "imagenet_val"}[entry["setting"]]
        raises(self, "symbol_rebound", L.check_registry_extension, self.r1, L.with_id(rebound))
        dropped = self.resettle(self.r2, systems=self.r2["systems"][:1])
        raises(self, "symbol_rebound", L.check_registry_extension, self.r1, dropped)
        skipped = self.resettle(self.r2, vocabulary={"name": "imagenet-cls", "revision": 3})
        raises(self, "invalid_extension", L.check_registry_extension, self.r1, skipped)
        orphan = self.resettle(self.r2, previous="sha256:" + "00" * 32)
        raises(self, "invalid_extension", L.check_registry_extension, self.r1, orphan)


class ArgumentChecks(unittest.TestCase):
    def test_base_checks(self):
        binding = rec("binding_a")
        for name in ("check_a", "check_rejected", "check_unavailable", "check_not_performed"):
            with self.subTest(name):
                L.check_argument_check(rec(name), binding=binding)
        L.check_argument_check(rec("check_map"), map_revision=rec("map_revision"))

    def test_accepted_check_can_report_gap_defeated_or_contested(self):
        for status in ("gap", "defeated", "contested"):
            check = rec("check_a")
            check["statuses"][0]["status"] = status
            L.check_argument_check(L.with_id(check))

    def test_out_file_is_read_only_after_exit_zero(self):
        check = rec("check_a")
        check["result"]["verdict_source"] = "out_file"
        raises(self, "stale_output", L.check_argument_check, L.with_id(check))
        rejected = rec("check_rejected")
        self.assertEqual(rejected["invocation"]["output"], "out_file")
        self.assertEqual(rejected["result"]["verdict_source"], "stdout")

    def test_exit_status_decides_the_outcome(self):
        unavailable = rec("check_unavailable")
        unavailable["result"] = {"exit_status": 1, "exit_checked_before_output_read": True, "verdict_source": "none",
                                 "verdict_digest": None, "stdout_digest": None, "stderr_digest": None}
        raises(self, "invalid_outcome", L.check_argument_check, L.with_id(unavailable))
        unavailable["result"]["exit_status"] = 137
        L.check_argument_check(L.with_id(unavailable))
        boundary = rec("check_rejected")
        boundary["result"]["exit_status"] = 2
        raises(self, "invalid_outcome", L.check_argument_check, L.with_id(boundary))
        boundary["rejection"]["boundary"] = True
        L.check_argument_check(L.with_id(boundary))

    def test_status_rows(self):
        both = rec("check_a")
        both["admission_blocked"] = [dict(both["statuses"][0], conditional_status="justified")]
        del both["admission_blocked"][0]["status"]
        raises(self, "invalid_status", L.check_argument_check, L.with_id(both))
        member = rec("check_a")
        member["statuses"][1]["member"] = "paper_a"
        raises(self, "invalid_status", L.check_argument_check, L.with_id(member))
        unsorted = rec("check_a")
        unsorted["statuses"].reverse()
        raises(self, "unsorted_or_duplicate", L.check_argument_check, L.with_id(unsorted))

    def test_check_inputs_bind_the_binding(self):
        other = rec("binding_c")
        raises(self, "identity_mismatch", L.check_argument_check, rec("check_a"), binding=other)

    def test_map_check_must_match_its_revision(self):
        revision = rec("map_revision")
        exploratory = rec("check_map")
        exploratory["scope"] = "exploratory_map"
        raises(self, "identity_mismatch", L.check_argument_check, L.with_id(exploratory), map_revision=revision)
        alias = rec("check_map")
        alias["statuses"][1]["member"] = "paper_z"
        raises(self, "invalid_status", L.check_argument_check, L.with_id(alias), map_revision=revision)

    def test_lara_status_is_not_ara_maturity(self):
        schema = json.loads((HERE / "lara-common.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$defs"]["claim_status"]["enum"], ["justified", "gap", "defeated", "contested"])
        check_fields = set(json.loads((HERE / "argument-check.schema.json").read_text(encoding="utf-8"))["properties"])
        for forbidden in ("maturity", "claim_status", "reproduction", "verification_kind", "supported"):
            self.assertNotIn(forbidden, check_fields)


class Attachments(unittest.TestCase):
    def setUp(self):
        self.check_doc = I.jcs(rec("check_a"))
        self.review_doc = I.jcs(rec("attestation_bob_a"))
        self.inventories = VECTORS["inventories"]

    def test_later_argument_check_leaves_the_contribution_unchanged(self):
        envelope = BASE_VECTORS["contribution"]["envelope"]
        attachment = rec("attachment_check")
        self.assertEqual(attachment["target"], envelope["contribution_id"])
        document = L.check_lara_attachment(attachment, self.check_doc, self.inventories["attachment_check"])
        self.assertEqual(document["target"]["argument"], {"kind": "enclosing_attachment"})
        I.check_contribution(envelope, BASE_VECTORS["payload"]["inventory"])
        self.assertEqual(I.contribution_id(envelope), BASE_VECTORS["contribution"]["expected_contribution_id"])
        L.check_lara_attachment(rec("attachment_review"), self.review_doc, self.inventories["attachment_review"])

    def test_document_rules(self):
        attachment = rec("attachment_review")
        inventory = self.inventories["attachment_review"]
        pretty = json.dumps(rec("attestation_bob_a"), indent=1).encode("utf-8")
        raises(self, "noncanonical_value", L.check_lara_attachment, attachment, pretty)
        raises(self, "identity_mismatch", L.check_lara_attachment, attachment, I.jcs(rec("attestation_bob_c")), inventory)
        raises(self, "identity_mismatch", L.check_lara_attachment, attachment, I.jcs(rec("attestation_bob_c")))
        wrong_kind = dict(attachment, kind="argument_check")
        wrong_kind["record_id"] = I.record_id("ara.attachment/v1", wrong_kind)
        raises(self, "invalid_body", L.check_lara_attachment, wrong_kind, self.review_doc)
        wrong_actor = dict(attachment, publisher="carol", request="carol:review-0001")
        wrong_actor["record_id"] = I.record_id("ara.attachment/v1", wrong_actor)
        raises(self, "actor_ownership", L.check_lara_attachment, wrong_actor, self.review_doc)


if __name__ == "__main__":
    unittest.main()
