#!/usr/bin/env python3
"""Exp A: Compare ARA artifact cognitive layer against PaperBench rubric.

Measures how well ARA's automated Ingestor recovers the same structured
understanding that took human authors weeks to build as PaperBench rubrics.

Metrics:
  1. Requirement coverage: fraction of rubric leaf nodes matched by ARA elements
  2. Granularity ratio: ARA nodes vs PaperBench leaf nodes
  3. Type coverage: breakdown by task_category (Code Dev / Execution / Result Analysis)
  4. Structural alignment: hierarchy overlap between rubric and ARA trees

Usage:
  python eval/rubric_compare.py \
    --rubric eval/rubrics/test-time-model-adaptation.json \
    --artifact artifacts/test-time-model-adaptation \
    --output eval/results/exp_a_test-time-model-adaptation.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from textwrap import dedent

import anthropic

# ── Rubric Parsing ──────────────────────────────────────────────────────────

def flatten_rubric(node, path="", depth=0):
    """Flatten PaperBench rubric tree into list of leaf nodes."""
    current_path = f"{path}/{node['id']}" if path else node["id"]
    leaves = []

    if not node.get("sub_tasks"):
        leaves.append({
            "id": node["id"],
            "path": current_path,
            "requirements": node["requirements"],
            "weight": node.get("weight", 1),
            "task_category": node.get("task_category", "Unknown"),
            "finegrained_category": node.get("finegrained_task_category", "Unknown"),
            "depth": depth,
        })
    else:
        for child in node["sub_tasks"]:
            leaves.extend(flatten_rubric(child, current_path, depth + 1))

    return leaves


def get_rubric_hierarchy(node, depth=0):
    """Extract the hierarchical structure (non-leaf internal nodes too)."""
    nodes = [{
        "id": node["id"],
        "requirements": node["requirements"],
        "depth": depth,
        "is_leaf": not bool(node.get("sub_tasks")),
        "n_children": len(node.get("sub_tasks", [])),
        "weight": node.get("weight", 1),
    }]
    for child in node.get("sub_tasks", []):
        nodes.extend(get_rubric_hierarchy(child, depth + 1))
    return nodes


# ── ARA Artifact Parsing ───────────────────────────────────────────────────

def extract_ara_elements(artifact_dir: Path) -> dict:
    """Extract all cognitive elements from an ARA artifact."""
    elements = {
        "claims": [],
        "experiments": [],
        "heuristics": [],
        "concepts": [],
        "architecture": [],
        "algorithm": [],
        "evidence_tables": [],
        "evidence_figures": [],
        "code_stubs": [],
    }

    # Claims
    claims_path = artifact_dir / "logic" / "claims.md"
    if claims_path.exists():
        elements["claims"] = _parse_numbered_sections(claims_path.read_text(), r"##\s+C\d+")

    # Experiments
    exp_path = artifact_dir / "logic" / "experiments.md"
    if exp_path.exists():
        elements["experiments"] = _parse_numbered_sections(exp_path.read_text(), r"##\s+E\d+")

    # Heuristics
    heur_path = artifact_dir / "logic" / "solution" / "heuristics.md"
    if heur_path.exists():
        elements["heuristics"] = _parse_numbered_sections(heur_path.read_text(), r"##\s+H\d+")

    # Concepts
    concepts_path = artifact_dir / "logic" / "concepts.md"
    if concepts_path.exists():
        elements["concepts"] = _parse_numbered_sections(concepts_path.read_text(), r"##\s+\d+\.")

    # Architecture
    arch_path = artifact_dir / "logic" / "solution" / "architecture.md"
    if arch_path.exists():
        elements["architecture"] = [{"id": "architecture", "text": arch_path.read_text()[:3000]}]

    # Algorithm
    algo_path = artifact_dir / "logic" / "solution" / "algorithm.md"
    if algo_path.exists():
        elements["algorithm"] = [{"id": "algorithm", "text": algo_path.read_text()[:3000]}]

    # Evidence tables
    tables_dir = artifact_dir / "evidence" / "tables"
    if tables_dir.exists():
        for f in sorted(tables_dir.glob("*.md")):
            elements["evidence_tables"].append({"id": f.stem, "text": f.read_text()[:1500]})

    # Evidence figures
    figs_dir = artifact_dir / "evidence" / "figures"
    if figs_dir.exists():
        for f in sorted(figs_dir.glob("*.md")):
            elements["evidence_figures"].append({"id": f.stem, "text": f.read_text()[:1500]})

    # Code stubs
    exec_dir = artifact_dir / "src" / "execution"
    if exec_dir.exists():
        for f in sorted(exec_dir.glob("*.py")):
            elements["code_stubs"].append({"id": f.stem, "text": f.read_text()[:2000]})

    return elements


def _parse_numbered_sections(text: str, pattern: str) -> list:
    """Parse markdown sections matching a pattern into individual elements."""
    sections = []
    matches = list(re.finditer(pattern, text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        # Extract ID from the header
        header_line = section_text.split("\n")[0]
        section_id = re.sub(r"^#+\s*", "", header_line).split(":")[0].strip()
        sections.append({
            "id": section_id,
            "text": section_text[:2000],  # cap for API
        })
    return sections


# ── Semantic Matching via LLM ──────────────────────────────────────────────

MATCH_SYSTEM = dedent("""\
    You are evaluating whether an AI-generated research artifact (ARA) covers
    the same knowledge as a human-authored paper reproduction rubric (PaperBench).

    For each rubric requirement, determine if the ARA artifact contains
    corresponding information that would help an agent fulfill that requirement.

    A match does NOT require identical wording — it means the ARA contains
    relevant knowledge (claim, experiment plan, heuristic, concept, architecture
    detail, code stub, or evidence) that addresses the same aspect of the paper.

    Respond in JSON format only.
""")


def build_match_prompt(rubric_batch: list, ara_summary: str) -> str:
    """Build prompt for matching a batch of rubric nodes against ARA elements."""
    rubric_block = ""
    for i, node in enumerate(rubric_batch):
        rubric_block += f"\n[R{i}] (category: {node['task_category']})\n{node['requirements']}\n"

    return dedent(f"""\
        Below is the ARA artifact's cognitive layer summary:

        <ara_elements>
        {ara_summary}
        </ara_elements>

        Below are rubric requirements to match:

        <rubric_requirements>
        {rubric_block}
        </rubric_requirements>

        For each requirement R0, R1, ..., determine:
        1. "matched": true/false — does the ARA contain relevant information?
        2. "match_type": which ARA element type matched (claim/experiment/heuristic/concept/architecture/algorithm/evidence/code_stub/none)
        3. "match_id": the specific ARA element ID that matched (or null)
        4. "match_quality": "exact" (same specific detail), "partial" (related but less specific), or "none"
        5. "explanation": brief reason (1 sentence)

        Return a JSON array with one object per requirement, keyed by R0, R1, etc.
        Example: {{"R0": {{"matched": true, "match_type": "experiment", "match_id": "E03", "match_quality": "exact", "explanation": "E03 describes the same ablation study"}}, "R1": ...}}

        Return ONLY the JSON object, no other text.
    """)


def summarize_ara_elements(elements: dict) -> str:
    """Create a concise summary of all ARA elements for matching."""
    parts = []

    for etype, items in elements.items():
        if not items:
            continue
        parts.append(f"\n### {etype.upper()} ({len(items)} items)")
        for item in items:
            # Truncate each item for the summary
            text = item["text"][:500].replace("\n", " ")
            parts.append(f"  [{item['id']}] {text}")

    return "\n".join(parts)


def run_llm_matching(rubric_leaves: list, ara_summary: str, model="claude-sonnet-4-6") -> list:
    """Match rubric leaves against ARA elements using LLM in batches."""
    client = anthropic.Anthropic()
    batch_size = 15  # ~15 requirements per API call
    all_results = []

    for i in range(0, len(rubric_leaves), batch_size):
        batch = rubric_leaves[i:i + batch_size]
        prompt = build_match_prompt(batch, ara_summary)

        print(f"  Matching batch {i // batch_size + 1}/{(len(rubric_leaves) + batch_size - 1) // batch_size} "
              f"({len(batch)} requirements)...")

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=MATCH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text.strip()
        # Extract JSON from response
        if response_text.startswith("```"):
            response_text = re.sub(r"```\w*\n?", "", response_text).strip()

        try:
            matches = json.loads(response_text)
        except json.JSONDecodeError:
            print(f"  WARNING: Failed to parse batch {i // batch_size + 1}, marking as unmatched")
            matches = {}

        for j, node in enumerate(batch):
            key = f"R{j}"
            match_info = matches.get(key, {})
            all_results.append({
                **node,
                "matched": match_info.get("matched", False),
                "match_type": match_info.get("match_type", "none"),
                "match_id": match_info.get("match_id"),
                "match_quality": match_info.get("match_quality", "none"),
                "explanation": match_info.get("explanation", ""),
            })

    return all_results


# ── Metrics Computation ────────────────────────────────────────────────────

def compute_metrics(matched_leaves: list, ara_elements: dict, rubric_hierarchy: list) -> dict:
    """Compute all Exp A metrics."""
    total = len(matched_leaves)
    matched = sum(1 for l in matched_leaves if l["matched"])
    exact = sum(1 for l in matched_leaves if l.get("match_quality") == "exact")
    partial = sum(1 for l in matched_leaves if l.get("match_quality") == "partial")

    # Weighted coverage (using rubric weights)
    total_weight = sum(l["weight"] for l in matched_leaves)
    matched_weight = sum(l["weight"] for l in matched_leaves if l["matched"])

    # Type coverage
    by_category = {}
    for l in matched_leaves:
        cat = l["task_category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "matched": 0, "exact": 0, "partial": 0}
        by_category[cat]["total"] += 1
        if l["matched"]:
            by_category[cat]["matched"] += 1
        if l.get("match_quality") == "exact":
            by_category[cat]["exact"] += 1
        elif l.get("match_quality") == "partial":
            by_category[cat]["partial"] += 1

    for cat in by_category:
        info = by_category[cat]
        info["coverage"] = round(info["matched"] / info["total"], 3) if info["total"] > 0 else 0

    # Granularity
    ara_node_count = sum(len(items) for items in ara_elements.values())

    # Depth distribution of matches
    depth_dist = {}
    for l in matched_leaves:
        d = l["depth"]
        if d not in depth_dist:
            depth_dist[d] = {"total": 0, "matched": 0}
        depth_dist[d]["total"] += 1
        if l["matched"]:
            depth_dist[d]["matched"] += 1

    return {
        "overall": {
            "total_rubric_leaves": total,
            "matched": matched,
            "exact_matches": exact,
            "partial_matches": partial,
            "unmatched": total - matched,
            "coverage": round(matched / total, 3) if total > 0 else 0,
            "exact_coverage": round(exact / total, 3) if total > 0 else 0,
            "weighted_coverage": round(matched_weight / total_weight, 3) if total_weight > 0 else 0,
        },
        "granularity": {
            "rubric_leaf_nodes": total,
            "rubric_total_nodes": len(rubric_hierarchy),
            "ara_total_elements": ara_node_count,
            "ara_element_breakdown": {k: len(v) for k, v in ara_elements.items()},
            "ratio": round(ara_node_count / total, 2) if total > 0 else 0,
        },
        "by_category": by_category,
        "by_depth": {str(k): v for k, v in sorted(depth_dist.items())},
    }


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Exp A: ARA vs PaperBench rubric comparison")
    parser.add_argument("--rubric", required=True, help="Path to PaperBench rubric.json")
    parser.add_argument("--artifact", required=True, help="Path to ARA artifact directory")
    parser.add_argument("--output", default=None, help="Output JSON path")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model for semantic matching")
    args = parser.parse_args()

    rubric_path = Path(args.rubric)
    artifact_dir = Path(args.artifact)

    if not rubric_path.exists():
        print(f"ERROR: Rubric not found: {rubric_path}")
        sys.exit(1)
    if not artifact_dir.exists():
        print(f"ERROR: Artifact not found: {artifact_dir}")
        sys.exit(1)

    print(f"{'=' * 60}")
    print("Exp A: Ingestor Validation Against PaperBench Rubric")
    print(f"{'=' * 60}")
    print(f"Rubric: {rubric_path}")
    print(f"Artifact: {artifact_dir}")

    # 1. Parse rubric
    print("\n[1/4] Parsing rubric...")
    with open(rubric_path) as f:
        rubric = json.load(f)
    leaves = flatten_rubric(rubric)
    hierarchy = get_rubric_hierarchy(rubric)
    print(f"  {len(leaves)} leaf nodes, {len(hierarchy)} total nodes")

    # 2. Extract ARA elements
    print("\n[2/4] Extracting ARA elements...")
    elements = extract_ara_elements(artifact_dir)
    for etype, items in elements.items():
        if items:
            print(f"  {etype}: {len(items)} items")

    # 3. Semantic matching
    print("\n[3/4] Running semantic matching...")
    ara_summary = summarize_ara_elements(elements)
    matched_leaves = run_llm_matching(leaves, ara_summary, model=args.model)

    # 4. Compute metrics
    print("\n[4/4] Computing metrics...")
    metrics = compute_metrics(matched_leaves, elements, hierarchy)

    # Build full result
    result = {
        "experiment": "Exp A: Ingestor Validation Against Rubrics",
        "paper": rubric.get("requirements", "Unknown"),
        "rubric_source": str(rubric_path),
        "artifact_source": str(artifact_dir),
        "model_used": args.model,
        "metrics": metrics,
        "detailed_matches": matched_leaves,
    }

    # Save
    output_path = Path(args.output) if args.output else (
        Path(__file__).parent / "results" / f"exp_a_{artifact_dir.name}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    # Print summary
    m = metrics["overall"]
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"Coverage:          {m['matched']}/{m['total_rubric_leaves']} = {m['coverage']:.1%}")
    print(f"  Exact matches:   {m['exact_matches']}")
    print(f"  Partial matches: {m['partial_matches']}")
    print(f"  Unmatched:       {m['unmatched']}")
    print(f"Weighted coverage: {m['weighted_coverage']:.1%}")
    print(f"\nBy category:")
    for cat, info in metrics["by_category"].items():
        print(f"  {cat}: {info['matched']}/{info['total']} = {info['coverage']:.1%}")
    g = metrics["granularity"]
    print(f"\nGranularity:")
    print(f"  Rubric leaves: {g['rubric_leaf_nodes']}")
    print(f"  ARA elements:  {g['ara_total_elements']}")
    print(f"  Ratio:         {g['ratio']}")
    for k, v in g["ara_element_breakdown"].items():
        if v:
            print(f"    {k}: {v}")
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
