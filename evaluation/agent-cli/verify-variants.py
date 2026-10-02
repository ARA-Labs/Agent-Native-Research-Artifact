#!/usr/bin/env python3
"""Verify candidate variant bytes/closure/access map without claiming semantic or binary proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def checked_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or any(part in (".", "..") for part in path.parts):
        raise ValueError(f"unsafe locked path: {relative}")
    resolved = (root / path).resolve(strict=True)
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"locked path escapes root: {relative}")
    return resolved


def verify_file(root: Path, row: dict) -> bytes:
    content = checked_path(root, row["path"]).read_bytes()
    if digest(content) != row["sha256"]:
        raise ValueError(f"digest mismatch: {row['path']}")
    if "bytes" in row and len(content) != row["bytes"]:
        raise ValueError(f"byte-count mismatch: {row['path']}")
    return content


def verify(evaluation: Path) -> dict:
    root = evaluation.parent.parent
    lock = load(evaluation / "variant-lock.json")
    source_lock = load(evaluation / "source-lock.json")
    inventory = load(evaluation / "operation-coverage.json")
    access = load(evaluation / "access-diff.json")
    collective = load(evaluation / "collective-contract.json")
    for row in (lock["source_lock"], lock["operation_inventory"], lock["access_diff"], lock["command_reference"]):
        verify_file(evaluation, row)
    inventory_bytes = (evaluation / "operation-coverage.json").read_bytes()
    if digest(inventory_bytes) != access["operation_inventory_sha256"]:
        raise ValueError("access diff inventory freeze does not match current inventory")
    rows = inventory["operations"]
    operation_ids = {row["operation_id"] for row in rows}
    if len(operation_ids) != len(rows) or lock["operation_inventory"]["operation_count"] != len(rows):
        raise ValueError("duplicate operation identity or wrong operation count")
    mappings = {row["operation_id"]: row for row in access["operation_mappings"]}
    if len(mappings) != len(access["operation_mappings"]) or set(mappings) != operation_ids:
        raise ValueError("access adapter inventory is not complete and one-to-one")
    for row in rows:
        mapped = mappings[row["operation_id"]]
        if mapped["source_clause"] != row["source_clause"] or mapped["access_policy"] != row["access_policy"]:
            raise ValueError(f"source/access boundary mismatch: {row['operation_id']}")
        if row["access_policy"] == "cli-required" and not mapped["adapter"]["commands"]:
            raise ValueError(f"required operation lacks adapter: {row['operation_id']}")
        if mapped.get("coverage_status") == "covered" and not mapped.get("proof_reference"):
            raise ValueError(f"unproved covered operation: {row['operation_id']}")
    source_files = {row["source_path"]: row for row in source_lock["files"]}
    for row in lock["files"]:
        content = verify_file(root, row)
        if row["path"].endswith("/SKILL.md"):
            if len(content.decode("utf-8").splitlines()) >= 500:
                raise ValueError(f"entrypoint exceeds contribution limit: {row['path']}")
            name = row["path"].split("/")[1]
            if not re.search(rf"(?m)^name: {re.escape(name)}$", content.decode("utf-8")):
                raise ValueError(f"install name mismatch: {row['path']}")
    for row in access["page_diffs"]:
        source = source_files[row["source_path"]]
        before = checked_path(root, source["archive_path"]).read_bytes()
        after = checked_path(root, row["variant_path"]).read_bytes()
        if digest(before) != source["sha256"] or digest(before) != row["source_sha256"] or digest(after) != row["variant_sha256"]:
            raise ValueError(f"source/variant page digest mismatch: {row['source_path']}")
        lines = before.decode("utf-8").splitlines(keepends=True)
        reconstructed: list[str] = []
        cursor = 0
        for hunk in row["hunks"]:
            start = hunk["source_lines"]["start"] - 1
            end = hunk["source_lines"]["end_exclusive"] - 1
            if start < cursor or end < start or end > len(lines):
                raise ValueError(f"invalid exact access hunk: {row['source_path']}")
            if "".join(lines[start:end]) != hunk["before"]:
                raise ValueError(f"access hunk does not quote source: {row['source_path']}")
            if not set(hunk["operation_ids"]).issubset(operation_ids):
                raise ValueError(f"access hunk refers to unknown inventory: {row['source_path']}")
            reconstructed.extend(lines[cursor:start])
            reconstructed.append(hunk["after"])
            cursor = end
        reconstructed.extend(lines[cursor:])
        if "".join(reconstructed).encode("utf-8") != after:
            raise ValueError(f"access diff does not reconstruct complete supplied page: {row['source_path']}")
    for movement in (row for row in access["clause_changes"] if row["change_kind"] == "movement"):
        source = source_files[movement["source_path"]]
        original = checked_path(root, source["archive_path"]).read_text(encoding="utf-8").splitlines(keepends=True)
        moved = "".join(original[movement["source_line_start"] - 1:movement["source_line_end"]])
        if digest(moved.encode()) != movement["unchanged_source_slice_sha256"]:
            raise ValueError("packaging movement source slice mismatch")
        for change in access["clause_changes"]:
            line = change.get("source_line_start")
            if change["change_kind"] == "access" and change["source_path"] == movement["source_path"] and line is not None and movement["source_line_start"] <= line <= movement["source_line_end"]:
                if moved.count(change["before"]) != 1:
                    raise ValueError("moved source access substitution is not unique")
                moved = moved.replace(change["before"], change["after"], 1)
        destination = checked_path(root, movement["destination_path"]).read_bytes()
        if digest(destination) != movement["destination_sha256"] or not destination.decode().endswith(moved):
            raise ValueError("moved schema/procedure content missing, reordered or changed outside the access diff")
    for delivery in lock["deliverables"]:
        skills = [skill.removesuffix("-cli") for skill in delivery["skills"]]
        required = {row["operation_id"] for row in rows if row["required"] and row["skill_pin"].split("/")[-1] in skills}
        if set(delivery["required_operation_ids"]) != required:
            raise ValueError(f"deliverable inventory incomplete: {delivery['deliverable']}")
        for row in delivery["variant_files"]:
            verify_file(root, row)
    if lock["collective_extension_included"]:
        raise ValueError("collective extension must not be included in interface-only variants")
    for row in collective["files"]:
        verify_file(root, row)
    common = root / "skills/collective-research-cli/references"
    for component in ("frontier", "intentions"):
        component_root = root / f"skills/collective-{component}-cli/references"
        for name in ("roles.md", "failure-policy.md"):
            if (common / name).read_bytes() != (component_root / name).read_bytes():
                raise ValueError(f"collective common condition diverges: {component}/{name}")
    return {
        "format": "ara.skill-variant-integrity/v1",
        "status": "pass",
        "variant_files": len(lock["files"]),
        "source_pages": len(access["page_diffs"]),
        "operation_count": len(rows),
        "collective_files": len(collective["files"]),
        "cli_pin_status": lock["cli_pin"]["status"],
        "semantic_review_status": access["review_status"],
        "runtime_proof_status": collective["observed_runtime_proof_status"],
        "scope": "byte/closure/inventory integrity only; not semantic review, upstream approval, binary proof or experiment results",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        result = verify(args.evaluation.resolve())
    except (OSError, KeyError, ValueError, TypeError) as error:
        print(json.dumps({"format": "ara.skill-variant-integrity/v1", "status": "fail", "error": str(error)}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
