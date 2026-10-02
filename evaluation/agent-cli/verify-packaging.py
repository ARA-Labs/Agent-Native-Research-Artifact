#!/usr/bin/env python3
"""Audit immutable skill packaging; this does not run an agent or an experiment."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_path(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, f"unsafe path: {relative}")
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root.resolve()), f"path escapes root: {relative}")
    return resolved


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_content(root, revision, relative):
    return subprocess.check_output(["git", "show", f"{revision}:{relative}"], cwd=root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git-source", type=Path, help="Repository containing the fetched source commit; also verifies available question IDs")
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    repository = package.parent.parent
    lock = load_json(package / "source-lock.json")
    mapping = load_json(package / "task-skill-map.json")
    inventory = load_json(package / "operation-coverage.json")
    decisions = load_json(package / "protocol-decisions.json")
    smoke = load_json(package / "smoke-tasks.json")
    require(lock["format"] == "ara.skill-source-lock/v1", "unsupported source lock")
    require(mapping["format"] == "ara.task-skill-map/v1", "unsupported task map")
    require(inventory["format"] == "ara.skill-operations/v1", "unsupported operations")
    require(decisions["format"] == "ara.protocol-decisions/v1", "unsupported decisions")
    require(smoke["format"] == "ara.packaging-smoke-tasks/v1", "unsupported smoke fixture")

    files = {}
    archive_paths = set()
    for record in lock["files"]:
        source = record["source_path"]
        require(source not in files, f"duplicate locked source: {source}")
        path = safe_path(repository, record["archive_path"])
        require(not (repository / record["archive_path"]).is_symlink(), f"archive symlink: {path}")
        data = path.read_bytes()
        require(len(data) == record["bytes"], f"byte count mismatch: {source}")
        require(hashlib.sha256(data).hexdigest() == record["sha256"], f"SHA256 mismatch: {source}")
        files[source] = data
        archive_paths.add(path)
    pins = {pin["pin_id"]: pin for pin in lock["pins"]}
    require(len(pins) == len(lock["pins"]), "duplicate skill pin")
    for pin in pins.values():
        require(len(pin["full_revision"]) == 40, "source revision is not a full Git object ID")
        require(pin["entrypoint"] in pin["files"], f"entrypoint absent: {pin['pin_id']}")
        require(len(set(pin["files"])) == len(pin["files"]), "duplicate pin member")
        digest = hashlib.sha256()
        for source in sorted(pin["files"]):
            require(source in files, f"missing pin member: {source}")
            path_bytes = source.encode("utf-8")
            data = files[source]
            digest.update(len(path_bytes).to_bytes(8, "big"))
            digest.update(path_bytes)
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        require(digest.hexdigest() == pin["sha256"], f"pin tree digest mismatch: {pin['pin_id']}")
        require(pin["license"]["source_path"] in files, "license absent")
        root = safe_path(package, pin["archive_root"])
        present = {path.resolve() for path in root.rglob("*") if path.is_file()}
        require(present == archive_paths, f"unlocked or missing files in archive root: {root}")
        pending = [pin["entrypoint"]]
        reached = set()
        while pending:
            source = pending.pop()
            if source in reached:
                continue
            reached.add(source)
            for edge in lock["reference_closure"]:
                if edge["from"] == source:
                    require(edge["to"] in pin["files"], f"reference closure incomplete: {source} -> {edge['to']}")
                    pending.append(edge["to"])
    for edge in lock["reference_closure"]:
        require(edge["from"] in files and edge["to"] in files, f"unpackaged reference edge: {edge}")

    required_fields = {"operation_id", "skill_pin", "source_clause", "layer", "native_selector", "access", "access_policy", "required", "payload_contract", "history_contract", "provenance_contract", "role", "proposed_cli_operation", "proposed_batch_tag", "coverage_status", "proof_reference", "blocked_reason"}
    operation_ids = set()
    counts = {}
    for row in inventory["operations"]:
        require(required_fields <= row.keys(), f"incomplete operation row: {row.get('operation_id')}")
        identity = row["operation_id"]
        require(identity not in operation_ids, f"duplicate operation: {identity}")
        operation_ids.add(identity)
        require(row["skill_pin"] in pins, f"unlocked operation pin: {identity}")
        clause = row["source_clause"]
        require(clause["path"] in pins[row["skill_pin"]]["files"], f"operation source outside pin: {identity}")
        lines = files[clause["path"]].decode("utf-8").splitlines()
        start, end = clause["line_start"], clause["line_end"]
        require(1 <= start <= end <= len(lines), f"invalid source clause range: {identity}")
        require(clause["quoted_clause"] in lines[start - 1:end], f"source clause quote differs: {identity}")
        status = row["coverage_status"]
        require(status in {"proposed", "covered", "blocked"}, f"unknown coverage status: {identity}")
        if status == "covered":
            proof = row["proof_reference"]
            require(isinstance(proof, dict) and proof.get("observed_evidence"), f"unproved coverage claim: {identity}")
            cli_revision = proof.get("cli_revision")
            require(isinstance(cli_revision, str) and len(cli_revision) == 40 and all(character in "0123456789abcdef" for character in cli_revision), f"CLI proof lacks a full pinned revision: {identity}")
        if status == "blocked":
            require(row["blocked_reason"], f"blocked row without reason: {identity}")
        counts[row["skill_pin"]] = counts.get(row["skill_pin"], 0) + 1
    require(set(counts) == set(pins), "a required source skill has no operation inventory")

    decision_ids = {item["decision_id"] for item in decisions["decisions"]}
    require(decision_ids == {f"F{n}" for n in range(1, 8)}, "F1-F7 are not separately recorded")
    for item in decisions["decisions"]:
        if item["upstream_status"] == "pending-review":
            require(item["approved_revision"] is None and item["approval_evidence"] is None, f"fabricated pending approval: {item['decision_id']}")
    for row in inventory["operations"]:
        require(set(row.get("required_decisions", [])) <= decision_ids, f"unknown decision dependency: {row['operation_id']}")

    task_ids = set()
    for row in mapping["paper_questions"]:
        require(row["task_id"] not in task_ids, f"duplicate native question ID: {row['task_id']}")
        task_ids.add(row["task_id"])
        if row["mapping_status"] == "unresolved-historical-skill":
            require(row["skill_pin"] is None and row["entrypoint"] is None and row["loaded_references"] is None, f"invented historical mapping: {row['task_id']}")
            require(row["blocked_reason"], "unresolved historical mapping lacks reason")
    require(len(task_ids) == lock["historical_configuration"]["available_native_question_count"], "available question count differs")
    require(mapping["paper_reported_count"] == lock["historical_configuration"]["reported_published_question_count"], "reported paper count differs")

    declared_tasks = {row["task_id"]: row for row in mapping["live_tasks"]}
    require(set(declared_tasks) == {row["task_id"] for row in smoke["tasks"]}, "smoke task mapping differs")
    loaded_pages = {}
    for task in smoke["tasks"]:
        declared = declared_tasks[task["task_id"]]
        pin = pins[declared["skill_pin"]]
        require(declared["entrypoint"] == pin["entrypoint"], "smoke uses another entrypoint")
        require(set(declared["loaded_references"]) == set(pin["files"]) - {pin["entrypoint"]}, "smoke omits a pinned reference")
        require(task["not_a_reproduction"] is True, "live smoke misrepresented as reproduction")
        loaded_pages[task["task_id"]] = {source: files[source].decode("utf-8") for source in [declared["entrypoint"], *declared["loaded_references"]]}
    for relative, body in smoke["artifact_files"].items():
        safe_path(package, relative)
        require(isinstance(body, str), f"fixture body is not exact text: {relative}")

    remote_checked = False
    if args.git_source:
        root = args.git_source.resolve()
        revision = lock["remote_verification"]["fetched_revision"]
        for record in lock["files"]:
            require(git_content(root, revision, record["source_path"]) == files[record["source_path"]], f"archive differs from source commit: {record['source_path']}")
        for record in lock["historical_configuration"]["files"]:
            data = git_content(root, revision, record["source_path"])
            require(len(data) == record["bytes"] and hashlib.sha256(data).hexdigest() == record["sha256"], f"historical config digest differs: {record['source_path']}")
        source_rows = {}
        for relative in lock["historical_configuration"]["question_paths"]:
            data = json.loads(git_content(root, revision, relative))
            for index, question in enumerate(data.get("questions", [])):
                require(question["id"] not in source_rows, "duplicate question ID in verified source")
                source_rows[question["id"]] = (relative, f"/questions/{index}")
        require(set(source_rows) == task_ids, "task map does not enumerate the verified source question set")
        for row in mapping["paper_questions"]:
            require(source_rows[row["task_id"]] == (row["configuration_source"], row["question_pointer"]), f"task source pointer differs: {row['task_id']}")
        remote_checked = True
    print(json.dumps({"status": "packaging-verified", "archived_files": len(files), "skill_pins": len(pins), "operations": len(operation_ids), "operations_by_pin": counts, "available_native_questions": len(task_ids), "reported_published_questions": mapping["paper_reported_count"], "loaded_smoke_pages": {key: len(value) for key, value in loaded_pages.items()}, "source_commit_bytes_checked": remote_checked, "historical_skill_and_published_subset": "unresolved", "upstream_protocol_review": lock["upstream_review_status"], "agent_runtime_execution": "not-run", "cli_capability_proof": "not-run", "experiments": "deferred"}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"packaging verification failed: {error}", file=sys.stderr)
        sys.exit(1)
