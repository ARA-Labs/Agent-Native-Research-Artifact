"""Identity, canonical-encoding and idempotency tests for the collaborative contracts.

Run from the protocol repository root:
    python3 -m unittest discover -s evaluation/collaborative -p 'test_*.py' -v
Set ARA_BIN to an ara binary (>= 0.1.24) to also cross-check a live capture.
"""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import identity as I


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
VECTORS = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))


def snapshot(name):
    entry = next(item for item in VECTORS["snapshots"] if item["name"] == name)
    return entry, entry["snapshot_json"].encode("utf-8")


def apply_changes(envelope, changes):
    result = copy.deepcopy(envelope)
    for path, value in changes.items():
        node = result
        keys = path.split(".")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return result


def rebuild(envelope, inventory):
    result = copy.deepcopy(envelope)
    result["payload_digest"] = I.payload_digest(inventory)
    result["native"]["fingerprint"] = inventory["native"]["fingerprint"]
    result["native"]["capture_id"] = inventory["native"]["capture_id"]
    result["contribution_id"] = I.contribution_id(result)
    return result


class CanonicalJson(unittest.TestCase):
    def test_vectors(self):
        for case in VECTORS["jcs"]:
            with self.subTest(case["name"]):
                self.assertEqual(I.jcs(case["input"]), case["expected"].encode("utf-8"))

    def test_rejects(self):
        for case in VECTORS["jcs_rejects"]:
            with self.subTest(case["name"]):
                with self.assertRaises(I.ContractError):
                    I.jcs(I.loads(case["json"].encode("utf-8")))

    def test_python_floats_and_bad_keys_reject(self):
        for value in (1.0, float("nan"), {1: "a"}, {"a": {1.5}}, b"bytes"):
            with self.subTest(repr(value)):
                with self.assertRaises(I.ContractError):
                    I.jcs(value)

    def test_keys_sort_by_utf16_code_units(self):
        # Code-point order would put U+FB33 before U+1F600; UTF-16 puts the surrogate pair first.
        self.assertEqual(I.jcs({"דּ": 1, "\U0001f600": 2}), '{"\U0001f600":2,"דּ":1}'.encode("utf-8"))

    def test_bool_is_not_integer(self):
        self.assertEqual(I.jcs([True, 1]), b"[true,1]")


class CaptureIdentity(unittest.TestCase):
    def test_real_manifests_are_reproduced_byte_for_byte(self):
        for entry in VECTORS["snapshots"]:
            with self.subTest(entry["name"]):
                raw = entry["snapshot_json"].encode("utf-8")
                manifest = I.loads(raw)
                self.assertEqual(I.jcs(manifest), raw)
                self.assertEqual(I.bytes_digest(raw), entry["snapshot_json_sha256"])
                self.assertEqual(I.capture_id(manifest), entry["capture_id"])
                self.assertEqual(manifest["capture_id"], entry["capture_id"])
                self.assertEqual(manifest["fingerprint"], entry["fingerprint"])

    def test_mode_only_change_keeps_fingerprint_and_changes_capture_id(self):
        (a, _), (b, _) = snapshot("snap-a"), snapshot("snap-b")
        self.assertEqual(a["fingerprint"], b["fingerprint"])
        self.assertNotEqual(a["capture_id"], b["capture_id"])

    def test_tampered_manifest_changes_capture_id(self):
        _, raw = snapshot("snap-a")
        manifest = I.loads(raw)
        manifest["files"][0]["mode"] = "0600"
        self.assertNotEqual(I.capture_id(manifest), manifest["capture_id"])

    @unittest.skipUnless(os.environ.get("ARA_BIN"), "set ARA_BIN to cross-check a live ara snapshot")
    def test_live_ara_snapshot_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "fixture"
            shutil.copytree(REPO / "examples" / "minimal-artifact", fixture)
            for path in fixture.rglob("*"):
                if path.is_file():
                    path.chmod(0o644)
            output = Path(temporary) / "snap"
            result = subprocess.run([os.environ["ARA_BIN"], "-C", str(fixture), "snapshot", "--output", str(output), "--json"],
                                    check=True, capture_output=True, text=True)
            raw = (output / "snapshot.json").read_bytes()
            manifest = I.loads(raw)
            self.assertEqual(I.jcs(manifest), raw)
            self.assertEqual(I.capture_id(manifest), json.loads(result.stdout)["capture_id"])
            self.assertEqual(raw, snapshot("snap-a")[1])


class PayloadAndContribution(unittest.TestCase):
    def setUp(self):
        self.inventory = copy.deepcopy(VECTORS["payload"]["inventory"])
        self.mode_only = copy.deepcopy(VECTORS["payload"]["mode_only_inventory"])
        self.envelope = copy.deepcopy(VECTORS["contribution"]["envelope"])

    def test_base_vectors(self):
        self.assertEqual(I.payload_digest(self.inventory), VECTORS["payload"]["expected_payload_digest"])
        self.assertEqual(I.payload_digest(self.mode_only), VECTORS["payload"]["expected_mode_only_payload_digest"])
        self.assertEqual(I.contribution_id(self.envelope), VECTORS["contribution"]["expected_contribution_id"])
        I.check_contribution(self.envelope, self.inventory)
        I.check_native_binding(self.inventory, snapshot("snap-a")[1])
        I.check_native_binding(self.mode_only, snapshot("snap-b")[1])

    def test_attribution_lineage_and_pointer_change_id_not_payload(self):
        base_id = self.envelope["contribution_id"]
        for case in VECTORS["contribution"]["variants"]:
            with self.subTest(case["name"]):
                if case["inventory"] == "mode_only":
                    changed = rebuild(self.envelope, self.mode_only)
                    self.assertNotEqual(changed["payload_digest"], self.envelope["payload_digest"])
                else:
                    changed = apply_changes(self.envelope, case["changes"])
                    changed["contribution_id"] = I.contribution_id(changed)
                    self.assertEqual(changed["payload_digest"], self.envelope["payload_digest"])
                self.assertNotEqual(changed["contribution_id"], base_id)
                self.assertEqual(changed["contribution_id"], case["expected_contribution_id"])
                self.assertEqual(changed["payload_digest"], case["expected_payload_digest"])

    def test_payload_bytes_or_mode_change_both_identities(self):
        for field, value in (("digest", "sha256:" + "00" * 32), ("mode", "0644"), ("size", 1)):
            with self.subTest(field):
                inventory = copy.deepcopy(self.inventory)
                entry = next(item for item in inventory["entries"] if item["path"] == "train.py")
                self.assertNotEqual(entry[field], value)
                entry[field] = value
                changed = rebuild(self.envelope, inventory)
                self.assertNotEqual(changed["payload_digest"], self.envelope["payload_digest"])
                self.assertNotEqual(changed["contribution_id"], self.envelope["contribution_id"])

    def test_mode_only_native_inventory_does_not_bind_other_manifest(self):
        with self.assertRaises(I.ContractError) as caught:
            I.check_native_binding(self.inventory, snapshot("snap-b")[1])
        self.assertEqual(caught.exception.code, "identity_mismatch")

    def test_contribution_id_field_is_excluded_and_tamper_rejects(self):
        tampered = copy.deepcopy(self.envelope)
        tampered["contribution_id"] = "sha256:" + "00" * 32
        self.assertEqual(I.contribution_id(tampered), self.envelope["contribution_id"])
        with self.assertRaises(I.ContractError):
            I.check_contribution(tampered)
        tampered = copy.deepcopy(self.envelope)
        tampered["source_key"] = "fork-z"
        with self.assertRaises(I.ContractError):
            I.check_contribution(tampered)

    def test_parents_must_be_sorted_unique_and_not_self(self):
        other = "sha256:" + "00" * 32
        for parents in ([self.envelope["lineage"]["parents"][0], other],
                        [other, other]):
            with self.subTest(parents=parents):
                changed = apply_changes(self.envelope, {"lineage.parents": parents})
                changed["contribution_id"] = I.contribution_id(changed)
                with self.assertRaises(I.ContractError) as caught:
                    I.check_contribution(changed)
                self.assertEqual(caught.exception.code, "unsorted_or_duplicate")

    def test_uses_must_be_sorted(self):
        uses = [{"source_key": "fork-b", "native_revision": "1" * 64, "selector": "N01"},
                {"source_key": "fork-a", "native_revision": "1" * 64, "selector": "N01"}]
        changed = apply_changes(self.envelope, {"lineage.uses": uses})
        changed["contribution_id"] = I.contribution_id(changed)
        with self.assertRaises(I.ContractError):
            I.check_contribution(changed)
        changed = apply_changes(self.envelope, {"lineage.uses": list(reversed(uses))})
        changed["contribution_id"] = I.contribution_id(changed)
        I.check_contribution(changed)

    def test_request_must_carry_publisher_prefix(self):
        changed = apply_changes(self.envelope, {"request": "worker-b:req-0007"})
        changed["contribution_id"] = I.contribution_id(changed)
        with self.assertRaises(I.ContractError) as caught:
            I.check_contribution(changed)
        self.assertEqual(caught.exception.code, "actor_ownership")

    def test_inventory_rules(self):
        cases = {
            "unsorted": lambda inv: inv["entries"].reverse(),
            "duplicate": lambda inv: inv["entries"].insert(1, copy.deepcopy(inv["entries"][0])),
            "undeclared-root": lambda inv: inv["roots"].pop(1),
            "missing-entry-point": lambda inv: inv["execution"].update(entry={"root": "code", "path": "absent.py"}),
            "second-snapshot-root": lambda inv: inv["roots"].__setitem__(0, {"name": "code", "kind": "ara-snapshot"}),
            "external-overlaps-entry": lambda inv: inv["external"][0].update(root="code", path="train.py"),
        }
        I.check_inventory(self.inventory)
        for name, mutate in cases.items():
            with self.subTest(name):
                inventory = copy.deepcopy(self.inventory)
                mutate(inventory)
                with self.assertRaises(I.ContractError):
                    I.check_inventory(inventory)

    def test_native_root_must_mirror_manifest(self):
        inventory = copy.deepcopy(self.inventory)
        native = [entry for entry in inventory["entries"] if entry["root"] == "native"]
        native[0]["mode"] = "0755"
        with self.assertRaises(I.ContractError) as caught:
            I.check_native_binding(inventory, snapshot("snap-a")[1])
        self.assertEqual(caught.exception.code, "inventory_mismatch")


class RecordsAndIdempotency(unittest.TestCase):
    def test_record_vectors_and_checks(self):
        records = VECTORS["records"]
        for name, case in records.items():
            with self.subTest(name):
                record = case["record"]
                self.assertEqual(I.record_id(record["schema"], record), case["expected_id"])
                if record["schema"] in I.RECORD_ID_FIELDS:
                    self.assertTrue(I.self_id_matches(record))
        I.check_attachment(records["attachment_verification"]["record"], VECTORS["attachment_inventory"]["inventory"])
        I.check_attachment(records["attachment_external_file_acknowledgment"]["record"])
        I.check_integration_receipt(records["integration_import"]["record"])
        I.check_integration_receipt(records["integration_resolution"]["record"])
        I.check_role_policy(records["role_policy"]["record"])
        I.check_visibility(records["visibility"]["record"])
        receipt = records["publication_receipt"]["record"]
        self.assertEqual(receipt["request_digest"], records["publication_request"]["expected_id"])

    def test_domains_separate_identical_content(self):
        record = {"schema": "ara.attachment/v1", "x": 1}
        same = dict(record, schema="ara.integration-receipt/v1")
        self.assertNotEqual(I.record_id("ara.attachment/v1", record), I.record_id("ara.integration-receipt/v1", same))
        self.assertNotEqual(I.domain_digest("ara.payload/v1", {}), I.domain_digest("ara.contribution/v1", {}))
        with self.assertRaises(I.ContractError):
            I.record_id("ara.integration-receipt/v1", record)
        with self.assertRaises(I.ContractError):
            I.record_id("ara.unknown/v1", {"schema": "ara.unknown/v1"})

    def test_attachment_file_refs_stay_inside_inventory(self):
        attachment = copy.deepcopy(VECTORS["records"]["attachment_verification"]["record"])
        inventory = copy.deepcopy(VECTORS["attachment_inventory"]["inventory"])
        inventory["entries"].pop()
        attachment["payload_digest"] = I.payload_digest(inventory)
        attachment["record_id"] = I.record_id("ara.attachment/v1", attachment)
        with self.assertRaises(I.ContractError) as caught:
            I.check_attachment(attachment, inventory)
        self.assertEqual(caught.exception.code, "missing_object")

    def test_role_policy_requires_one_integration_pm(self):
        policy = copy.deepcopy(VECTORS["records"]["role_policy"]["record"])
        policy["actors"][3]["roles"] = ["continuity_writer", "integration_pm", "publisher"]
        policy["policy_id"] = I.record_id("ara.role-policy/v1", policy)
        with self.assertRaises(I.ContractError) as caught:
            I.check_role_policy(policy)
        self.assertEqual(caught.exception.code, "invalid_roles")

    def test_request_retry_and_conflict(self):
        envelope = VECTORS["contribution"]["envelope"]
        ledger = I.RequestLedger()
        self.assertEqual(ledger.bind_record(envelope), "accepted")
        self.assertEqual(ledger.bind_record(copy.deepcopy(envelope)), "replay")
        for changes in ({"payload_digest": "sha256:" + "00" * 32}, {"lineage.parents": []}, {"payload.follow_up": "N20"}):
            with self.subTest(changes=changes):
                changed = apply_changes(envelope, changes)
                changed["contribution_id"] = I.contribution_id(changed)
                with self.assertRaises(I.ContractError) as caught:
                    ledger.bind_record(changed)
                self.assertEqual(caught.exception.code, "request_conflict")
        # Contributions and attachments share one request namespace per (community, publisher).
        attachment = copy.deepcopy(VECTORS["records"]["attachment_verification"]["record"])
        attachment.update(publisher="worker-a", request=envelope["request"])
        with self.assertRaises(I.ContractError):
            ledger.bind_record(attachment)
        # The same request string in another community is a different binding.
        other = apply_changes(envelope, {"community": "run-2026-10-b"})
        other["contribution_id"] = I.contribution_id(other)
        self.assertEqual(ledger.bind_record(other), "accepted")
        with self.assertRaises(I.ContractError) as caught:
            ledger.bind("c", "worker-a", "worker-b:req", "sha256:" + "00" * 32)
        self.assertEqual(caught.exception.code, "actor_ownership")


if __name__ == "__main__":
    unittest.main()
