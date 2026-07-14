"""Convert PaperBench rubric JSON into rubric/requirements.md for ARA artifacts.

Flattens the hierarchical rubric tree into a numbered list (R01, R02, ...)
grouped by finegrained_task_category, matching the format used by
adaptive-pruning, bam, and lbcs.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _flatten_leaves(node: dict, parent_req: str = "") -> list[dict]:
    """Recursively extract leaf requirements from rubric tree."""
    children = node.get("sub_tasks", [])
    if not children:
        # Leaf node
        return [{
            "id": node["id"],
            "requirements": node["requirements"],
            "weight": node.get("weight", 1),
            "task_category": node.get("task_category", ""),
            "finegrained_task_category": node.get("finegrained_task_category", ""),
            "parent_context": parent_req,
        }]
    leaves = []
    for child in children:
        leaves.extend(_flatten_leaves(child, parent_req=node["requirements"]))
    return leaves


def generate_requirements_md(paper_id: str, rubric_path: str, output_dir: str) -> str:
    """Generate rubric/requirements.md from rubric JSON."""
    with open(rubric_path) as f:
        rubric = json.load(f)

    leaves = _flatten_leaves(rubric)

    # Group by finegrained_task_category
    groups: dict[str, list] = {}
    for leaf in leaves:
        cat = leaf["finegrained_task_category"] or "Uncategorized"
        groups.setdefault(cat, []).append(leaf)

    # Build markdown
    lines = [
        f"# Rubric Requirements — {paper_id}",
        "**Source**: PaperBench expert-authored reproduction rubric",
        f"**Total leaf requirements**: {len(leaves)}",
        "",
    ]

    r_num = 1
    for category, reqs in groups.items():
        lines.append(f"## {category}")
        lines.append("")
        for req in reqs:
            short = req["requirements"][:60].rstrip()
            if len(req["requirements"]) > 60:
                short += "..."
            lines.append(f"### R{r_num:02d}: {short}")
            lines.append(f"- **Rubric ID**: {req['id']}")
            lines.append(f"- **Category**: {req['task_category']} / {category}")
            lines.append(f"- **Weight**: {req['weight']}")
            lines.append(f"- **Requirement**: {req['requirements']}")
            if req["parent_context"]:
                parent_short = req["parent_context"][:100]
                if len(req["parent_context"]) > 100:
                    parent_short += "..."
                lines.append(f"- **Parent context**: {parent_short}")
            lines.append("")
            r_num += 1

    # Write to output
    out_path = Path(output_dir) / "rubric" / "requirements.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"[rubric] Wrote {len(leaves)} requirements to {out_path}")
    return str(out_path)


def main():
    registry_path = ROOT / "code" / "eval" / "paper_registry.json"
    with open(registry_path) as f:
        registry = json.load(f)

    # Filter to PaperBench papers only
    papers = [p for p in registry["papers"] if p["benchmark"] == "paperbench"]

    # Optionally filter to specific papers
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        target_ids = set(sys.argv[1:])
        papers = [p for p in papers if p["paper_id"] in target_ids]

    for paper in papers:
        pid = paper["paper_id"]
        rubric_path = ROOT / paper["rubric_path"]
        artifact_dir = ROOT / paper["artifact_dir"]

        if not rubric_path.exists():
            print(f"[rubric] SKIP {pid}: rubric not found at {rubric_path}")
            continue

        # Check if already exists
        existing = artifact_dir / "rubric" / "requirements.md"
        if existing.exists():
            print(f"[rubric] SKIP {pid}: rubric/requirements.md already exists")
            continue

        generate_requirements_md(pid, str(rubric_path), str(artifact_dir))

    print("[rubric] Done.")


if __name__ == "__main__":
    main()
