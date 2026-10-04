"""Schema positives and negatives for the stage-L1 Lara contracts, using ../schema_check.py.

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

import schema_check as S  # noqa: E402

VECTORS = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))
RECORDS = VECTORS["records"]
SCHEMAS = sorted(HERE.glob("*.schema.json"))
SCHEMA_OF = {
    "ara.lara-binding/v1": "lara-binding.schema.json",
    "ara.lara-review-attestation/v1": "review-attestation.schema.json",
    "ara.lara-setting-descriptor/v1": "setting-descriptor.schema.json",
    "ara.lara-setting-registry/v1": "setting-registry.schema.json",
    "ara.lara-argument-check/v1": "argument-check.schema.json",
    "ara.lara-map-revision/v1": "map-revision.schema.json",
    "ara.attachment/v1": "../attachment.schema.json",
    "ara.role-policy/v1": "../roles.schema.json",
}


def check(instance):
    schema = instance["schema"]
    if schema == "ara.lara-system-descriptor/v1":
        node, base = S.schema_at(HERE / "setting-descriptor.schema.json", "#/$defs/system_descriptor")
        return S.errors(instance, node, base)
    return S.validate(instance, HERE / SCHEMA_OF[schema])


def at(path, value):
    def mutate(record):
        node = record
        keys = path.split(".")
        for key in keys[:-1]:
            node = node[int(key)] if isinstance(node, list) else node[key]
        node[keys[-1]] = value
    return mutate


class SchemaFiles(unittest.TestCase):
    def test_every_schema_uses_supported_keywords_and_resolves(self):
        self.assertEqual([path.name for path in SCHEMAS], [
            "argument-check.schema.json", "lara-binding.schema.json", "lara-common.schema.json",
            "map-revision.schema.json", "review-attestation.schema.json", "setting-descriptor.schema.json",
            "setting-registry.schema.json"])
        for path in SCHEMAS:
            with self.subTest(path.name):
                schema = S.load(path)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertTrue(schema["$id"].startswith("ara.lara-"))
                self.assertEqual(S.unsupported(schema), [])
                self.assertIsInstance(S.validate({}, path), list)

    def test_closed_objects(self):
        def walk(node, where):
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    self.assertIs(node.get("additionalProperties"), False, where)
                for key, value in node.items():
                    if key not in ("if", "then", "else"):
                        walk(value, where + "/" + key)
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, where + "/" + str(index))
        for path in SCHEMAS:
            walk(S.load(path), path.name)

    def test_attachment_documents_match_the_deferred_body_pattern(self):
        # ../attachment.schema.json fixed only the pointer shape; these are the frozen document schemas.
        node, base = S.schema_at(HERE.parent / "attachment.schema.json", "#/$defs/deferred_body")
        for schema in ("ara.lara-review-attestation/v1", "ara.lara-argument-check/v1"):
            body = {"schema": schema, "document": {"root": "lara", "path": "doc.json"}}
            self.assertEqual(S.errors(body, node, base), [])


class Positives(unittest.TestCase):
    def test_vector_records_validate(self):
        for name, case in RECORDS.items():
            with self.subTest(name):
                self.assertEqual(check(case["record"]), [])
        for name, inventory in VECTORS["inventories"].items():
            with self.subTest(name):
                self.assertEqual(S.validate(inventory, HERE.parent / "payload-inventory.schema.json"), [])
        for replication in VECTORS["replications"]:
            self.assertEqual(check(replication["setting"]), [])

    def test_checker_pin_file_validates(self):
        pin = json.loads((HERE / "checker-pin.json").read_text(encoding="utf-8"))
        node, base = S.schema_at(HERE / "lara-common.schema.json", "#/$defs/checker_pin_file")
        self.assertEqual(S.errors(pin, node, base), [])
        self.assertEqual(pin["build"]["source_commit"], "a31299feafb484404b62bc3b4fd313d987cdda44")
        self.assertEqual(pin["build"]["provenance"], "local-build")
        self.assertEqual(pin["registration_status"], "provisional-local-build")
        for bad in (at("build.provenance", "nightly"), at("build.source_commit", "a31299f"),
                    at("build.executable_sha256", "dfbc59")):
            changed = copy.deepcopy(pin)
            bad(changed)
            self.assertNotEqual(S.errors(changed, node, base), [])


def _result(**changes):
    result = copy.deepcopy(RECORDS["check_a"]["record"]["result"])
    result.update(changes)
    return result


class Negatives(unittest.TestCase):
    CASES = [
        ("binding_a", "unknown-field", at("extra", 1)),
        ("binding_a", "leaf-without-evidence", at("elements.3.sources.0.evidence_digest", None)),
        ("binding_a", "audit-status-approved", at("claims.0.formalization.declared_audit_status", "approved")),
        ("binding_a", "unnamed-attack", at("elements.0.ref", "attack x1")),
        ("binding_a", "prefixed-fingerprint", at("native.fingerprint", "sha256:" + "ab" * 32)),
        ("binding_a", "no-selected-claim", at("claims", [])),
        ("binding_c", "attack-to-unknown-kind", at("elements.2.kind", "edge")),
        ("attestation_bob_a", "unknown-disposition", at("disposition", "endorsed")),
        ("attestation_bob_a", "enclosing-location", at("target.argument", {"kind": "enclosing_attachment"})),
        ("attestation_bob_a", "no-reviewed-claim", at("reviewed", [])),
        ("attestation_bob_a", "missing-registry", lambda record: record["covered"].pop("registry")),
        ("attestation_carol_dispute_a", "approving-dispute", at("disposition", "approved")),
        ("attestation_carol_dispute_a", "no-affected-claims", at("linkage.affected_claims", [])),
        ("setting_a", "free-seed-with-value", at("replication.1.value", "0")),
        ("setting_a", "fixed-without-value", at("replication.0.value", None)),
        ("setting_a", "unknown-polarity", at("metric.polarity", "higher")),
        ("setting_a", "outcome-in-descriptor", at("outcome", "0.74")),
        ("setting_a", "unknown-treatment", at("replication.1.treatment", "ignored")),
        ("system_new", "system-with-setting", at("dataset", {})),
        ("registry_r1", "revision-1-with-previous", at("previous", "sha256:" + "00" * 32)),
        ("registry_r2", "revision-2-without-previous", at("previous", None)),
        ("registry_r1", "uppercase-symbol", at("settings.0.setting", "ImageNet_val")),
        ("check_a", "accepted-with-exit-1", at("result.exit_status", 1)),
        ("check_a", "accepted-with-rejection", at("rejection", {"class": "R13", "boundary": False, "diagnostic_digest": None})),
        ("check_a", "exit-not-checked-first", at("result.exit_checked_before_output_read", False)),
        ("check_a", "accepted-without-verdict", at("result", _result(verdict_source="none", verdict_digest=None))),
        ("check_a", "evidence-blocked-status", at("statuses.0.status", "evidence-blocked")),
        ("check_a", "unknown-outcome", at("outcome", "passed")),
        ("check_a", "individual-two-bindings", at("inputs.binding_ids", ["sha256:" + "01" * 32, "sha256:" + "02" * 32])),
        ("check_a", "individual-map-scope", at("scope", "audited_map")),
        ("check_a", "individual-manifest-entry", at("inputs.entry.kind", "map_manifest")),
        ("check_rejected", "rejected-reads-stale-out-file", at("result.verdict_source", "out_file")),
        ("check_rejected", "rejected-with-statuses", at("statuses", copy.deepcopy(RECORDS["check_a"]["record"]["statuses"]))),
        ("check_rejected", "rejected-without-rejection", at("rejection", None)),
        ("check_rejected", "rejected-exit-0", at("result.exit_status", 0)),
        ("check_unavailable", "unavailable-without-reason", at("unavailable_reason", None)),
        ("check_unavailable", "unavailable-with-verdict", at("result", _result(exit_status=None))),
        ("check_not_performed", "not-performed-with-result", at("result", _result())),
        ("check_not_performed", "not-performed-with-checker", at("checker", copy.deepcopy(RECORDS["check_a"]["record"]["checker"]))),
        ("check_map", "map-individual-scope", at("scope", "individual")),
        ("check_map", "map-admission-blocked", at("admission_blocked", [
            {"member": "paper_a", "claim": "c1", "proposition": "p", "conditional_status": "justified"}])),
        ("check_map", "out-file-with-exit-1", at("result.exit_status", 1)),
        ("map_revision", "unknown-exclusion-reason", at("exclusions.0.reason", "pending")),
        ("map_revision", "complete-scope", at("coverage.scope", "complete")),
        ("map_revision", "member-without-binding", lambda record: record["members"][0].pop("binding_id")),
        ("map_revision", "verdict-in-revision", at("outcome", "accepted")),
        ("map_revision", "empty-population", at("population.contributions", [])),
        ("attachment_review", "lara-body-wrong-prefix", at("body.schema", "ara.review/v1")),
    ]

    def test_negative_cases_reject(self):
        for source, name, mutate in self.CASES:
            with self.subTest(case=name):
                record = copy.deepcopy(RECORDS[source]["record"])
                self.assertEqual(check(record), [])
                mutate(record)
                self.assertNotEqual(check(record), [])


if __name__ == "__main__":
    unittest.main()
