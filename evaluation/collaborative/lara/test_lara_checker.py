"""Smoke test against a real Lara executable (skipped unless LARA_BIN is set).

    LARA_BIN=/path/to/lara python3 -m unittest discover -s evaluation/collaborative -p 'test_lara_checker.py' -v

The test copies Lara's own ``examples/S4`` (found next to LARA_BIN's source
tree, or at ``LARA_EXAMPLE``, the path to ``examples/S4/example.lara``), runs
``lara check``, and builds ``ara.lara-argument-check/v1`` records from the exit
status and output digests. It also reproduces the stale ``--out`` pitfall: a
rejected run leaves the previous accepted verdict file in place, and the record
must not read it.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
for _path in (str(HERE), str(HERE.parent)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import identity as I  # noqa: E402
import lara_identity as L  # noqa: E402
import schema_check as S  # noqa: E402

PIN = json.loads((HERE / "checker-pin.json").read_text(encoding="utf-8"))
VECTORS = json.loads((HERE / "vectors.json").read_text(encoding="utf-8"))
CONTRIBUTION = "sha256:" + "5a" * 32  # synthetic target; the smoke checks the record shape, not a publication


def find_example():
    explicit = os.environ.get("LARA_EXAMPLE")
    if explicit:
        return Path(explicit) if Path(explicit).is_file() else None
    binary = os.environ.get("LARA_BIN")
    if not binary:
        return None
    for parent in Path(binary).resolve().parents:
        candidate = parent / "examples" / "S4" / "example.lara"
        if candidate.is_file():
            return candidate
    return None


def read_sexp(text):
    """Parse one S-expression into nested lists of atom strings."""
    tokens, index = [], 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
        elif char in "()":
            tokens.append(char)
            index += 1
        elif char == '"':
            end = index + 1
            while text[end] != '"':
                end += 2 if text[end] == "\\" else 1
            tokens.append(text[index:end + 1])
            index = end + 1
        else:
            end = index
            while end < len(text) and not text[end].isspace() and text[end] not in "()":
                end += 1
            tokens.append(text[index:end])
            index = end
    stack = [[]]
    for token in tokens:
        if token == "(":
            stack.append([])
        elif token == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(token)
    return stack[0][0]


def show(node):
    return node if isinstance(node, str) else "(" + " ".join(show(item) for item in node) + ")"


def solo_rows(verdict, queries):
    """Return (class, statuses, admission_blocked, rejection class) of a solo Lara verdict."""
    tree = read_sexp(verdict)
    if tree[2] == "reject":
        return "reject", [], [], tree[3]
    sections = {item[0]: item[1:] for item in tree[3:]}
    conditional = iter(sections.get("conditional", []))
    statuses, blocked = [], []
    for claim, (_, atom, status) in zip(queries, sections["statuses"]):
        if status == "evidence-blocked":
            blocked.append({"member": None, "claim": claim, "proposition": show(atom), "conditional_status": next(conditional)[2]})
        else:
            statuses.append({"member": None, "claim": claim, "proposition": show(atom), "status": status})
    key = lambda row: (row["member"] or "", row["claim"])  # noqa: E731
    return "accept", sorted(statuses, key=key), sorted(blocked, key=key), None


def status_queries(source):
    return [line.split()[1] for line in source.splitlines() if line.startswith("status ")]


def check_record(binding, executable, run, output, rows=None, rejection=None, verdict_source="stdout"):
    outcome = {0: "accepted", 1: "rejected", 2: "rejected"}.get(run.returncode, "unavailable")
    verdict = I.bytes_digest(run.stdout) if verdict_source == "stdout" and run.stdout else None
    record = {
        "schema": "ara.lara-argument-check/v1", "community": binding["community"], "verifier": "runner",
        "target": {"kind": "contribution", "contribution_id": CONTRIBUTION, "argument": {"kind": "enclosing_attachment"}},
        "scope": "individual",
        "checker": {"build": dict(PIN["build"], executable_sha256=executable), "backends": [{"name": "ord", "version": 1}],
                    "theories": ["sha256:ord-setting-v1-theory-0"]},
        "policy": binding["policy"],
        "inputs": {"entry": {"kind": "argument", "digest": binding["argument"]["digest"]},
                   "binding_ids": [binding["binding_id"]], "registry": None},
        "invocation": {"command": "check", "entry": {"root": "lara", "path": "example.lara"}, "output": output},
        "result": {"exit_status": run.returncode, "exit_checked_before_output_read": True,
                   "verdict_source": verdict_source if verdict else "none", "verdict_digest": verdict,
                   "stdout_digest": I.bytes_digest(run.stdout) if run.stdout else None,
                   "stderr_digest": I.bytes_digest(run.stderr) if run.stderr else None},
        "outcome": outcome, "statuses": (rows or ([], []))[0], "admission_blocked": (rows or ([], []))[1],
        "rejection": rejection, "unavailable_reason": None, "supersedes": None,
    }
    return L.with_id(record)


@unittest.skipUnless(os.environ.get("LARA_BIN") and find_example(),
                     "set LARA_BIN (and LARA_EXAMPLE if the Lara source tree is not above it) to run the real checker")
class RealChecker(unittest.TestCase):
    def setUp(self):
        self.binary = os.environ["LARA_BIN"]
        self.executable = I.bytes_digest(Path(self.binary).read_bytes())
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name) / "S4"
        shutil.copytree(find_example().parent, self.work)
        self.source = (self.work / "example.lara").read_bytes()
        name, digest = L.argument_artifact(self.source)
        policy = I.bytes_digest((self.work / "ord-setting-v1.policy.lara").read_bytes())
        self.binding = L.with_id({
            "schema": "ara.lara-binding/v1", "community": "lara-smoke", "producer": "alice",
            "native": {"source_key": "fork-s4", "fingerprint": digest.split(":", 1)[1], "capture_id": "sha256:" + "5b" * 32},
            "argument": {"digest": I.bytes_digest(self.source), "artifact": {"name": name, "digest": digest}},
            "policy": {"lara_policy": "ord-setting-v1", "policy_digest": policy}, "registry": None,
            "claims": [{"lara_id": "c1", "source": {"source_key": "fork-s4", "native_revision": digest.split(":", 1)[1], "selector": "C01"},
                        "proposition": "better(sys_new, sys_base, accuracy, imagenet_val)", "settings": [], "systems": [],
                        "formalization": {"author": "alice", "rationale": "S4 golden example.", "assumptions": [],
                                          "declared_audit_status": "disputed"},
                        "elements": ["e1", "e2", "e3"]}],
            "elements": [{"ref": ref, "kind": "leaf", "sources": [{"source_key": "fork-s4", "native_revision": digest.split(":", 1)[1],
                                                                  "selector": "evidence/tables/accuracy.md", "evidence_digest": "sha256:" + "5c" * 32}]}
                         for ref in ("e1", "e2", "e3")]})

    def tearDown(self):
        self.temporary.cleanup()

    def run_lara(self, *extra):
        return subprocess.run([self.binary, "check", "example.lara", *extra], cwd=self.work, capture_output=True, timeout=120)

    def validate(self, record):
        self.assertEqual(S.validate(record, HERE / "argument-check.schema.json"), [])
        L.check_argument_check(record, binding=self.binding)

    def test_pinned_checker_accepts_s4_and_record_validates(self):
        L.check_binding(self.binding, self.source)
        self.assertEqual(self.binding["policy"]["policy_digest"], VECTORS["lara"]["policy_sha256"])
        if self.executable != PIN["build"]["executable_sha256"]:
            self.skipTest("LARA_BIN differs from checker-pin.json; a runner records such a check as unavailable")
        run = self.run_lara()
        self.assertEqual(run.returncode, 0, run.stderr)
        verdict_class, statuses, blocked, _ = solo_rows(run.stdout.decode("utf-8"), status_queries(self.source.decode("utf-8")))
        self.assertEqual(verdict_class, "accept")
        self.assertEqual([(row["claim"], row["status"]) for row in statuses], [("c1", "defeated"), ("c2", "justified")])
        self.validate(check_record(self.binding, self.executable, run, "stdout", (statuses, blocked)))

    def test_failed_run_leaves_stale_out_file_that_is_never_read(self):
        if self.executable != PIN["build"]["executable_sha256"]:
            self.skipTest("LARA_BIN differs from checker-pin.json")
        self.assertEqual(self.run_lara("--out", "verdict.sexp").returncode, 0)
        stale = (self.work / "verdict.sexp").read_bytes()
        (self.work / "example.lara").write_bytes(self.source.replace(b"0.74", b"0.70"))
        run = self.run_lara("--out", "verdict.sexp")
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual((self.work / "verdict.sexp").read_bytes(), stale)
        verdict_class, _, _, rejection = solo_rows(run.stdout.decode("utf-8"), [])
        self.assertEqual((verdict_class, rejection), ("reject", "R13"))
        changed = L.with_id(dict(self.binding, argument=dict(self.binding["argument"], digest=I.bytes_digest(
            (self.work / "example.lara").read_bytes()))))
        self.binding = changed
        record = check_record(changed, self.executable, run, "out_file",
                              rejection={"class": rejection, "boundary": False, "diagnostic_digest": I.bytes_digest(run.stderr)})
        self.validate(record)
        self.assertEqual(record["outcome"], "rejected")
        misread = dict(record, result=dict(record["result"], verdict_source="out_file", verdict_digest=I.bytes_digest(stale)))
        self.assertNotEqual(S.validate(L.with_id(misread), HERE / "argument-check.schema.json"), [])

    def test_snapshot_mismatch_rejects_the_argument_package(self):
        other = L.with_id(dict(self.binding, native=dict(self.binding["native"], fingerprint="4e" * 32)))
        with self.assertRaises(L.ContractError) as caught:
            L.check_binding(other, self.source)
        self.assertEqual(caught.exception.code, "snapshot_mismatch")


if __name__ == "__main__":
    unittest.main()
