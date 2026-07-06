#!/usr/bin/env python3
"""Aggregate PDF Information Gap results across multiple papers.

Reads individual info_gap_*.json result files and produces a cross-paper summary
with aggregate statistics, systematic gap patterns, and per-category breakdowns.

Usage:
  python code/eval/aggregate_info_gap.py \
    --results-dir code/eval/results \
    --output code/eval/results/info_gap_aggregate.json
"""

import argparse
import json
import sys
from pathlib import Path


def load_results(results_dir: Path) -> list:
    """Load all info_gap_*.json result files."""
    papers = []
    for f in sorted(results_dir.glob("info_gap_*.json")):
        if "aggregate" in f.name:
            continue
        data = json.loads(f.read_text())
        papers.append(data)
        print(f"  Loaded: {f.name} ({data['n_requirements']} requirements)")
    return papers


def aggregate(papers: list) -> dict:
    """Compute cross-paper aggregate metrics."""
    # Per-paper summaries
    per_paper = []
    all_results = []
    total_reqs = 0

    for p in papers:
        s = p["metrics"]["summary"]
        name = Path(p["pdf_path"]).stem
        per_paper.append({
            "paper": name,
            "n_requirements": s["total_requirements"],
            "sufficient": s["sufficient"],
            "partial": s["partial"],
            "absent": s["absent"],
            "pct_sufficient": s["pct_sufficient"],
            "pct_partial": s["pct_partial"],
            "pct_absent": s["pct_absent"],
            "information_coverage": s["information_coverage"],
        })
        total_reqs += s["total_requirements"]
        all_results.extend(p["detailed_results"])

    # Aggregate across all papers
    total = len(all_results)
    sufficient = sum(1 for r in all_results if r["rating"] == "sufficient")
    partial = sum(1 for r in all_results if r["rating"] == "partial")
    absent = sum(1 for r in all_results if r["rating"] == "absent")

    # By task category (across all papers)
    by_cat = {}
    for r in all_results:
        cat = r.get("task_category", "Unknown")
        if cat not in by_cat:
            by_cat[cat] = {"total": 0, "sufficient": 0, "partial": 0, "absent": 0}
        by_cat[cat]["total"] += 1
        by_cat[cat][r["rating"]] += 1
    for cat in by_cat:
        t = by_cat[cat]["total"]
        by_cat[cat]["pct_sufficient"] = round(by_cat[cat]["sufficient"] / t, 3)
        by_cat[cat]["pct_partial"] = round(by_cat[cat]["partial"] / t, 3)
        by_cat[cat]["pct_absent"] = round(by_cat[cat]["absent"] / t, 3)

    # By fine-grained category
    by_fine = {}
    for r in all_results:
        fine = r.get("finegrained_task_category", "Unknown")
        if fine not in by_fine:
            by_fine[fine] = {"total": 0, "sufficient": 0, "partial": 0, "absent": 0}
        by_fine[fine]["total"] += 1
        by_fine[fine][r["rating"]] += 1
    for fine in by_fine:
        t = by_fine[fine]["total"]
        by_fine[fine]["pct_sufficient"] = round(by_fine[fine]["sufficient"] / t, 3)
        by_fine[fine]["pct_partial"] = round(by_fine[fine]["partial"] / t, 3)
        by_fine[fine]["pct_absent"] = round(by_fine[fine]["absent"] / t, 3)

    # Gap category distribution
    gap_counts = {}
    for r in all_results:
        if r["rating"] != "sufficient":
            for g in r.get("gap_categories", []):
                gap_counts[g] = gap_counts.get(g, 0) + 1
    gap_total = sum(gap_counts.values()) or 1
    gap_dist = {
        k: {"count": v, "pct_of_gaps": round(v / gap_total, 3)}
        for k, v in sorted(gap_counts.items(), key=lambda x: -x[1])
    }

    # Token/cost aggregation
    total_input = sum(p["token_usage"]["input_tokens"] for p in papers)
    total_output = sum(p["token_usage"]["output_tokens"] for p in papers)
    total_cache_created = sum(p["token_usage"]["cache_creation_input_tokens"] for p in papers)
    total_cache_read = sum(p["token_usage"]["cache_read_input_tokens"] for p in papers)
    total_wall = sum(p["token_usage"].get("total_wall_seconds", 0) for p in papers)

    # Confidence
    confidence = {}
    for r in all_results:
        c = r.get("confidence", "unknown")
        confidence[c] = confidence.get(c, 0) + 1

    # Median paper stats
    pct_sufs = sorted([p["pct_sufficient"] for p in per_paper])
    pct_pars = sorted([p["pct_partial"] for p in per_paper])
    pct_abss = sorted([p["pct_absent"] for p in per_paper])
    n = len(pct_sufs)
    median_idx = n // 2

    return {
        "experiment": "PDF Information Gap — Cross-Paper Aggregate",
        "n_papers": len(papers),
        "total_requirements": total,
        "aggregate_summary": {
            "sufficient": sufficient,
            "partial": partial,
            "absent": absent,
            "pct_sufficient": round(sufficient / total, 3),
            "pct_partial": round(partial / total, 3),
            "pct_absent": round(absent / total, 3),
            "information_coverage": round((sufficient + 0.5 * partial) / total, 3),
        },
        "median_paper": {
            "pct_sufficient": pct_sufs[median_idx],
            "pct_partial": pct_pars[median_idx],
            "pct_absent": pct_abss[median_idx],
        },
        "per_paper": per_paper,
        "by_task_category": by_cat,
        "by_finegrained_category": by_fine,
        "gap_distribution": gap_dist,
        "confidence_distribution": confidence,
        "cost": {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "cache_creation_tokens": total_cache_created,
            "cache_read_tokens": total_cache_read,
            "total_wall_seconds": total_wall,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Aggregate PDF Information Gap results")
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    print("Loading individual paper results...")
    papers = load_results(results_dir)

    if not papers:
        print("ERROR: No info_gap_*.json files found")
        sys.exit(1)

    print(f"\n{len(papers)} papers loaded, {sum(p['n_requirements'] for p in papers)} total requirements")

    agg = aggregate(papers)

    output_path = Path(args.output) if args.output else results_dir / "info_gap_aggregate.json"
    output_path.write_text(json.dumps(agg, indent=2) + "\n")

    # Print
    s = agg["aggregate_summary"]
    print(f"\n{'=' * 70}")
    print("CROSS-PAPER RESULTS: PDF Information Gap")
    print(f"{'=' * 70}")

    print(f"\n{'Paper':<45} {'n':>4} {'Suf%':>6} {'Par%':>6} {'Abs%':>6} {'Cov':>6}")
    print("─" * 75)
    for p in agg["per_paper"]:
        print(f"  {p['paper']:<43} {p['n_requirements']:>4}"
              f" {p['pct_sufficient']:>5.1%} {p['pct_partial']:>5.1%}"
              f" {p['pct_absent']:>5.1%} {p['information_coverage']:>5.1%}")
    print("─" * 75)
    print(f"  {'AGGREGATE':<43} {agg['total_requirements']:>4}"
          f" {s['pct_sufficient']:>5.1%} {s['pct_partial']:>5.1%}"
          f" {s['pct_absent']:>5.1%} {s['information_coverage']:>5.1%}")

    m = agg["median_paper"]
    print(f"\n  Median paper:  suf={m['pct_sufficient']:.1%}  "
          f"par={m['pct_partial']:.1%}  abs={m['pct_absent']:.1%}")

    print(f"\nBy task category:")
    for cat, info in sorted(agg["by_task_category"].items()):
        print(f"  {cat:30s} (n={info['total']:3d})  "
              f"suf={info['pct_sufficient']:.0%}  "
              f"par={info['pct_partial']:.0%}  "
              f"abs={info['pct_absent']:.0%}")

    n_gaps = s["partial"] + s["absent"]
    print(f"\nGap taxonomy (across {n_gaps} non-sufficient requirements):")
    for gap, info in agg["gap_distribution"].items():
        bar = "█" * int(info["pct_of_gaps"] * 40)
        print(f"  {gap:35s}  {info['count']:3d}  ({info['pct_of_gaps']:>5.1%})  {bar}")

    c = agg["cost"]
    print(f"\nTotal cost:")
    print(f"  Wall time: {c['total_wall_seconds']:.0f}s ({c['total_wall_seconds']/60:.1f}min)")
    print(f"  Tokens: {c['total_input_tokens']:,} in / {c['total_output_tokens']:,} out")
    print(f"  Cache: {c['cache_creation_tokens']:,} created / {c['cache_read_tokens']:,} read")

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
