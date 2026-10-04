"""Schema positives/negatives and the intention-schema v2 diff, using schema_check.

Run from the protocol repository root:
    python3 -m unittest discover -s evaluation/collaborative -p 'test_*.py' -v
"""

import copy
import hashlib
import json
from pathlib import Path
import unittest

import schema_check as S


HERE = Path(__file__).resolve().parent
V1_REQUEST = HERE.parent / "agent-cli" / "community-smoke-scenarios" / "request.schema.json"
V1_REQUEST_SHA256 = "e9b6d821a2730fb1ead342465be164ce5564397a932056edc6e9dcdf197a7756"
VECTORS = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))
SCHEMAS = sorted(HERE.glob("*.schema.json"))
RECORD_SCHEMAS = {
    "attachment_verification": "attachment.schema.json",
    "attachment_external_file_acknowledgment": "attachment.schema.json",
    "integration_import": "integration-receipt.schema.json",
    "integration_resolution": "integration-receipt.schema.json",
    "publication_request": "publication.schema.json",
    "publication_receipt": "publication.schema.json",
    "visibility": "visibility.schema.json",
    "role_policy": "roles.schema.json",
}


def check(instance, name):
    return S.validate(instance, HERE / name)


def at(path, value):
    def mutate(record):
        node = record
        keys = path.split(".")
        for key in keys[:-1]:
            node = node[int(key)] if isinstance(node, list) else node[key]
        node[keys[-1]] = value
    return mutate


def intention_v2(**changes):
    item = {"intention_id": "alice:work", "source_identity": "fork-alice", "artifact_revision": "sha256:fixture-revision",
            "native_refs": [{"source_identity": "fork-alice", "native_ref": "trace/exploration_tree.yaml:N12"}],
            "action": "Run the bounded fixture action", "question": "Does the fixture action hold?",
            "experiment_signature": "sha256:identical-configuration", "verification_of": None, "verification_rationale": None,
            "prediction": {"native_revision": "0" * 64, "selector": "O03", "input_signature": "sha256:" + "16" * 32},
            "state": "planned", "budget_reserved": 10, "result_refs": [], "result_contributions": []}
    item.update(changes)
    return {"request_id": "alice:request-1", "observed_sequence": 1, "observed_round": 1, "expected_revision": 0, "intention": item}


class SchemaFiles(unittest.TestCase):
    def test_every_schema_uses_supported_keywords_and_resolves(self):
        self.assertEqual(len(SCHEMAS), 10)
        for path in SCHEMAS:
            with self.subTest(path.name):
                schema = S.load(path)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(S.unsupported(schema), [])
                self.assertIsInstance(S.validate({}, path), list)

    def test_closed_objects(self):
        def walk(node, where):
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    self.assertIs(node.get("additionalProperties"), False, where)
                for key, value in node.items():
                    walk(value, where + "/" + key)
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, where + "/" + str(index))
        for path in SCHEMAS:
            walk(S.load(path), path.name)

    def test_archived_v1_request_schema_is_unchanged(self):
        digest = hashlib.sha256(V1_REQUEST.read_bytes()).hexdigest()
        self.assertEqual(digest, V1_REQUEST_SHA256)


class Positives(unittest.TestCase):
    def test_vector_documents_validate(self):
        self.assertEqual(check(VECTORS["contribution"]["envelope"], "contribution.schema.json"), [])
        self.assertEqual(check(VECTORS["payload"]["inventory"], "payload-inventory.schema.json"), [])
        self.assertEqual(check(VECTORS["payload"]["mode_only_inventory"], "payload-inventory.schema.json"), [])
        self.assertEqual(check(VECTORS["attachment_inventory"]["inventory"], "payload-inventory.schema.json"), [])
        for name, schema in RECORD_SCHEMAS.items():
            with self.subTest(name):
                self.assertEqual(check(VECTORS["records"][name]["record"], schema), [])
        body = VECTORS["records"]["attachment_verification"]["record"]["body"]
        self.assertEqual(check(body, "verification.schema.json"), [])

    def test_workflow_state_events(self):
        cid = VECTORS["contribution"]["expected_contribution_id"]
        base = {"schema": "ara.workflow-state/v1", "community": "c", "publisher": "worker-a", "request": "worker-a:r",
                "sequence": 3, "evidence": None}
        good = [dict(base, contribution_id=None, track="publication", state="draft", previous=None),
                dict(base, contribution_id=cid, track="publication", state="published", previous="frozen"),
                dict(base, contribution_id=cid, track="integration", state="imported-with-conflicts", previous="pending")]
        bad = [dict(base, contribution_id=cid, track="publication", state="draft", previous=None),
               dict(base, contribution_id=None, track="integration", state="pending", previous=None),
               dict(base, contribution_id=cid, track="integration", state="published", previous=None),
               dict(base, contribution_id=cid, track="publication", state="frozen", previous="pending")]
        for event in good:
            self.assertEqual(check(event, "publication.schema.json"), [], event)
        for event in bad:
            self.assertNotEqual(check(event, "publication.schema.json"), [], event)

    def test_intention_v2_requests(self):
        name = "community-request-v2.schema.json"
        publish, _ = S.schema_at(HERE / name, "#/$defs/publish")
        refresh, _ = S.schema_at(HERE / name, "#/$defs/refresh-intention")
        base = (HERE / name).resolve()
        self.assertEqual(S.errors(intention_v2(), publish, base), [])
        target = {"contribution_id": VECTORS["contribution"]["expected_contribution_id"], "selectors": ["C01"]}
        self.assertEqual(S.errors(intention_v2(verification_of=target, verification_rationale="Reproduce C01",
                                               prediction=None), publish, base), [])
        completion = {"request_id": "alice:request-2", "observed_sequence": 2, "observed_round": 1,
                      "intention_id": "alice:work", "expected_revision": 2, "state": "completed", "result_refs": [],
                      "result_contributions": [VECTORS["contribution"]["expected_contribution_id"]]}
        self.assertEqual(S.errors(completion, refresh, base), [])
        for bad in (intention_v2(result_contributions=[target["contribution_id"]]),
                    intention_v2(prediction={"native_revision": "0" * 64, "selector": "O03"}),
                    intention_v2(verification_of={"contribution_id": "sha256:short", "selectors": ["C01"]})):
            self.assertNotEqual(S.errors(bad, publish, base), [])
        missing = intention_v2()
        del missing["intention"]["prediction"]
        self.assertNotEqual(S.errors(missing, publish, base), [])
        self.assertNotEqual(S.errors(dict(completion, result_contributions=["x"]), refresh, base), [])


class Negatives(unittest.TestCase):
    CASES = [
        ("contribution.schema.json", "contribution", "unknown-field", at("extra", 1)),
        ("contribution.schema.json", "contribution", "uppercase-digest", at("payload_digest", "sha256:" + "AB" * 32)),
        ("contribution.schema.json", "contribution", "prefixed-fingerprint", at("native.fingerprint", "sha256:" + "ab" * 32)),
        ("contribution.schema.json", "contribution", "duplicate-parents", at("lineage.parents", ["sha256:" + "51" * 32] * 2)),
        ("contribution.schema.json", "contribution", "prediction-without-receipt", at("execution.intention_receipt", None)),
        ("contribution.schema.json", "contribution", "copied-body", at("payload.outcome", {"selector": "N12", "field": "result", "text": "0.9"})),
        ("contribution.schema.json", "contribution", "bad-request", at("request", "req-0007")),
        ("contribution.schema.json", "contribution", "request-trailing-newline", at("request", "worker-a:req-0007\n")),
        ("contribution.schema.json", "contribution", "string-size-parent", at("lineage.parents", "sha256:" + "51" * 32)),
        ("payload-inventory.schema.json", "inventory", "traversal", at("entries.0.path", "../secret")),
        ("payload-inventory.schema.json", "inventory", "absolute", at("entries.0.path", "/etc/passwd")),
        ("payload-inventory.schema.json", "inventory", "git-dir", at("entries.0.path", "src/.git/config")),
        ("payload-inventory.schema.json", "inventory", "backslash", at("entries.0.path", "src\\x.py")),
        ("payload-inventory.schema.json", "inventory", "trailing-newline", at("entries.0.path", "x.py\n")),
        ("payload-inventory.schema.json", "inventory", "empty-component", at("entries.0.path", "a//b")),
        ("payload-inventory.schema.json", "inventory", "short-mode", at("entries.0.mode", "644")),
        ("payload-inventory.schema.json", "inventory", "unsafe-size", at("entries.0.size", 2 ** 53)),
        ("payload-inventory.schema.json", "inventory", "git-without-revision", at("external.0.retrieval.revision", None)),
        ("payload-inventory.schema.json", "inventory", "url-with-revision", at("external.0.retrieval.kind", "url")),
        ("payload-inventory.schema.json", "inventory", "unknown-root-kind", at("roots.0.kind", "scratch")),
        ("payload-inventory.schema.json", "inventory", "wrong-manifest", at("native.manifest", "manifest.json")),
        ("attachment.schema.json", "verification", "superseding-in-plain-verification", at("body.supersedes", "sha256:" + "00" * 32)),
        ("attachment.schema.json", "verification", "superseding-without-target", at("kind", "superseding_verdict")),
        ("attachment.schema.json", "verification", "reproduction-without-raw-output", at("body.execution.raw_outputs", [])),
        ("attachment.schema.json", "verification", "outcome-without-observation", at("body.observations", [])),
        ("attachment.schema.json", "verification", "unknown-outcome", at("body.outcome", "endorsed")),
        ("attachment.schema.json", "verification", "unknown-kind", at("body.verification_kind", "replication")),
        ("attachment.schema.json", "acknowledgment", "approval-disposition", at("body.disposition", "approved")),
        ("attachment.schema.json", "acknowledgment", "body-for-other-kind", at("kind", "correction")),
        ("integration-receipt.schema.json", "import", "integrated-with-unresolved", at("state", "integrated")),
        ("integration-receipt.schema.json", "import", "pending-receipt", at("state", "pending")),
        ("integration-receipt.schema.json", "resolution", "integrated-with-unresolved", at("unresolved_count", 2)),
        ("integration-receipt.schema.json", "resolution", "no-resolved-conflicts", at("resolved_conflicts", [])),
        ("roles.schema.json", "roles", "unknown-role", at("actors.0.roles", ["owner"])),
        ("roles.schema.json", "roles", "single-actor-factor", at("independence.shared_factors.0.actors", ["pm"])),
        ("visibility.schema.json", "visibility", "zero-sequence", at("contributions.0.sequence", 0)),
        ("publication.schema.json", "receipt", "missing-visibility", lambda record: record.pop("visibility_id")),
    ]
    SOURCES = {
        "contribution": lambda: VECTORS["contribution"]["envelope"],
        "inventory": lambda: VECTORS["payload"]["inventory"],
        "verification": lambda: VECTORS["records"]["attachment_verification"]["record"],
        "acknowledgment": lambda: VECTORS["records"]["attachment_external_file_acknowledgment"]["record"],
        "import": lambda: VECTORS["records"]["integration_import"]["record"],
        "resolution": lambda: VECTORS["records"]["integration_resolution"]["record"],
        "roles": lambda: VECTORS["records"]["role_policy"]["record"],
        "visibility": lambda: VECTORS["records"]["visibility"]["record"],
        "receipt": lambda: VECTORS["records"]["publication_receipt"]["record"],
    }

    def test_negative_cases_reject(self):
        for schema, source, name, mutate in self.CASES:
            with self.subTest(schema=schema, case=name):
                record = copy.deepcopy(self.SOURCES[source]())
                self.assertEqual(check(record, schema), [])
                mutate(record)
                self.assertNotEqual(check(record, schema), [])


class IntentionRevisionDiff(unittest.TestCase):
    def test_v2_changes_only_documented_definitions(self):
        v1 = S.load(V1_REQUEST)["$defs"]
        v2 = S.load(HERE / "community-request-v2.schema.json")["$defs"]
        self.assertEqual(sorted(set(v2) - set(v1)), ["contribution_ids", "prediction"])
        self.assertEqual(set(v1) - set(v2), set())
        changed = sorted(name for name in v1 if v1[name] != v2[name])
        self.assertEqual(changed, ["initialize", "intention", "refresh-intention"])
        self.assertEqual(v2["initialize"]["properties"]["config"]["$ref"],
                         "../agent-cli/community-smoke-scenarios/run-config.schema.json")
        added = set(v2["intention"]["properties"]) - set(v1["intention"]["properties"])
        self.assertEqual(added, {"prediction", "result_contributions"})
        added = set(v2["refresh-intention"]["properties"]) - set(v1["refresh-intention"]["properties"])
        self.assertEqual(added, {"prediction", "result_contributions"})
        self.assertEqual(len(v2["intention"]["properties"]["verification_of"]["oneOf"]), 3)
        self.assertEqual(v1["intention"]["properties"]["verification_of"]["oneOf"],
                         v2["intention"]["properties"]["verification_of"]["oneOf"][:2])


if __name__ == "__main__":
    unittest.main()
