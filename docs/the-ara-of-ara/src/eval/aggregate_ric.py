#!/usr/bin/env python3
"""Aggregate RIC batch results from sub-agent evaluations into final Exp B output.

Usage:
  python eval/aggregate_ric.py \
    --results-dir eval/results \
    --rubric eval/rubrics/test-time-model-adaptation.json \
    --output eval/results/exp_b_test-time-model-adaptation.json
"""

import argparse
import json
import sys
from pathlib import Path


def load_batch_results(results_dir: Path, source: str) -> list:
    """Load and merge all batch results for a given source (pdf or ara)."""
    all_evals = []
    batch_num = 1
    while True:
        path = results_dir / f"ric_{source}_batch_{batch_num}.json"
        if not path.exists():
            break
        data = json.loads(path.read_text())
        all_evals.extend(data["evaluations"])
        batch_num += 1

    if not all_evals:
        print(f"WARNING: No batch results found for {source}")
    else:
        print(f"  {source.upper()}: {len(all_evals)} evaluations from {batch_num - 1} batches")

    return all_evals


def compute_ric(evals: list, rubric_leaves: list) -> dict:
    """Compute RIC metrics from evaluations."""
    # Build lookup by requirement ID
    eval_lookup = {e["id"]: e for e in evals}

    total = len(rubric_leaves)
    yes = 0
    partial = 0
    no = 0
    total_weight = 0
    yes_weight = 0
    partial_weight = 0

    by_category = {}
    by_fine = {}
    by_depth = {}

    results_with_meta = []

    for leaf in rubric_leaves:
        rid = leaf["id"]
        ev = eval_lookup.get(rid, {"found": "no", "evidence": "", "explanation": "not evaluated"})
        found = ev.get("found", "no")
        weight = leaf.get("weight", 1)
        cat = leaf.get("task_category", "Unknown")
        fine = leaf.get("finegrained_task_category", "Unknown")
        depth = str(leaf.get("depth", 0))

        total_weight += weight

        if found == "yes":
            yes += 1
            yes_weight += weight
        elif found == "partial":
            partial += 1
            partial_weight += weight
        else:
            no += 1

        # By category
        if cat not in by_category:
            by_category[cat] = {"total": 0, "yes": 0, "partial": 0, "no": 0}
        by_category[cat]["total"] += 1
        by_category[cat][found] = by_category[cat].get(found, 0) + 1

        # By finegrained category
        if fine not in by_fine:
            by_fine[fine] = {"total": 0, "yes": 0, "partial": 0, "no": 0}
        by_fine[fine]["total"] += 1
        by_fine[fine][found] = by_fine[fine].get(found, 0) + 1

        # By depth
        if depth not in by_depth:
            by_depth[depth] = {"total": 0, "yes": 0, "partial": 0, "no": 0}
        by_depth[depth]["total"] += 1
        by_depth[depth][found] = by_depth[depth].get(found, 0) + 1

        results_with_meta.append({
            **leaf,
            "found": found,
            "evidence": ev.get("evidence", ""),
            "explanation": ev.get("explanation", ""),
        })

    # Compute RIC scores for each grouping
    for group in [by_category, by_fine, by_depth]:
        for key in group:
            info = group[key]
            t = info["total"]
            info["ric"] = round((info["yes"] + 0.5 * info["partial"]) / t, 3) if t else 0
            info["strict_ric"] = round(info["yes"] / t, 3) if t else 0

    metrics = {
        "total_requirements": total,
        "yes": yes,
        "partial": partial,
        "no": no,
        "ric": round((yes + 0.5 * partial) / total, 3) if total else 0,
        "strict_ric": round(yes / total, 3) if total else 0,
        "weighted_ric": round(
            (yes_weight + 0.5 * partial_weight) / total_weight, 3
        ) if total_weight else 0,
        "by_category": by_category,
        "by_finegrained_category": by_fine,
        "by_depth": dict(sorted(by_depth.items())),
    }

    return metrics, results_with_meta


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
            "finegrained_task_category": node.get("finegrained_task_category", "Unknown"),
            "depth": depth,
        })
    else:
        for child in node["sub_tasks"]:
            leaves.extend(flatten_rubric(child, current_path, depth + 1))
    return leaves


def main():
    parser = argparse.ArgumentParser(description="Aggregate RIC batch results")
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--rubric", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    rubric_path = Path(args.rubric)

    # Parse rubric
    with open(rubric_path) as f:
        rubric = json.load(f)
    leaves = flatten_rubric(rubric)
    print(f"Rubric: {len(leaves)} leaf requirements")

    # Load batch results
    print("\nLoading batch results...")
    pdf_evals = load_batch_results(results_dir, "pdf")
    ara_evals = load_batch_results(results_dir, "ara")

    # Compute metrics
    print("\nComputing metrics...")
    pdf_metrics, pdf_detailed = compute_ric(pdf_evals, leaves)
    ara_metrics, ara_detailed = compute_ric(ara_evals, leaves)

    # Comparison
    comparison = {
        "overall": {
            "pdf_ric": pdf_metrics["ric"],
            "ara_ric": ara_metrics["ric"],
            "delta": round(ara_metrics["ric"] - pdf_metrics["ric"], 3),
            "pdf_strict_ric": pdf_metrics["strict_ric"],
            "ara_strict_ric": ara_metrics["strict_ric"],
            "strict_delta": round(ara_metrics["strict_ric"] - pdf_metrics["strict_ric"], 3),
        },
        "by_category": {},
    }

    all_cats = set(pdf_metrics["by_category"]) | set(ara_metrics["by_category"])
    for cat in sorted(all_cats):
        pdf_cat = pdf_metrics["by_category"].get(cat, {})
        ara_cat = ara_metrics["by_category"].get(cat, {})
        comparison["by_category"][cat] = {
            "pdf_ric": pdf_cat.get("ric", 0),
            "ara_ric": ara_cat.get("ric", 0),
            "delta": round(ara_cat.get("ric", 0) - pdf_cat.get("ric", 0), 3),
            "pdf_strict": pdf_cat.get("strict_ric", 0),
            "ara_strict": ara_cat.get("strict_ric", 0),
        }

    # Per-requirement comparison
    per_req = []
    pdf_lookup = {r["id"]: r for r in pdf_detailed}
    ara_lookup = {r["id"]: r for r in ara_detailed}
    for leaf in leaves:
        rid = leaf["id"]
        pdf_r = pdf_lookup.get(rid, {})
        ara_r = ara_lookup.get(rid, {})
        per_req.append({
            "id": rid,
            "requirement": leaf["requirements"][:150],
            "category": leaf.get("task_category", ""),
            "fine_category": leaf.get("finegrained_task_category", ""),
            "weight": leaf.get("weight", 1),
            "pdf_found": pdf_r.get("found", "no"),
            "ara_found": ara_r.get("found", "no"),
            "pdf_evidence": (pdf_r.get("evidence", "") or "")[:200],
            "ara_evidence": (ara_r.get("evidence", "") or "")[:200],
        })

    # Summary stats
    ara_only = sum(1 for r in per_req if r["ara_found"] == "yes" and r["pdf_found"] == "no")
    pdf_only = sum(1 for r in per_req if r["pdf_found"] == "yes" and r["ara_found"] == "no")
    both_yes = sum(1 for r in per_req if r["pdf_found"] == "yes" and r["ara_found"] == "yes")
    neither = sum(1 for r in per_req if r["pdf_found"] == "no" and r["ara_found"] == "no")

    result = {
        "experiment": "Exp B: Reproducibility Information Completeness (RIC)",
        "paper": rubric.get("requirements", "Unknown"),
        "rubric_leaves": len(leaves),
        "pdf_metrics": pdf_metrics,
        "ara_metrics": ara_metrics,
        "comparison": comparison,
        "agreement": {
            "both_yes": both_yes,
            "ara_only": ara_only,
            "pdf_only": pdf_only,
            "neither": neither,
        },
        "per_requirement": per_req,
    }

    output_path = Path(args.output) if args.output else (
        results_dir / "exp_b_test-time-model-adaptation.json"
    )
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    # Print
    print(f"\n{'='*60}")
    print("RESULTS: Reproducibility Information Completeness (RIC)")
    print(f"{'='*60}")
    c = comparison["overall"]
    print(f"\n{'':>30}{'PDF':>10}{'ARA':>10}{'Δ':>10}")
    print(f"{'─'*60}")
    print(f"{'RIC (yes + 0.5×partial)':>30}{c['pdf_ric']:>10.1%}{c['ara_ric']:>10.1%}{c['delta']:>+10.1%}")
    print(f"{'Strict RIC (yes only)':>30}{c['pdf_strict_ric']:>10.1%}{c['ara_strict_ric']:>10.1%}{c['strict_delta']:>+10.1%}")

    print(f"\nBy PaperBench category:")
    for cat, info in sorted(comparison["by_category"].items()):
        n = pdf_metrics["by_category"].get(cat, {}).get("total", 0)
        print(f"  {cat:30s} (n={n:3d})  PDF={info['pdf_ric']:.1%}  ARA={info['ara_ric']:.1%}  Δ={info['delta']:+.1%}")

    print(f"\nAgreement analysis:")
    print(f"  Both found:       {both_yes:4d}")
    print(f"  ARA only:         {ara_only:4d}")
    print(f"  PDF only:         {pdf_only:4d}")
    print(f"  Neither found:    {neither:4d}")

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
