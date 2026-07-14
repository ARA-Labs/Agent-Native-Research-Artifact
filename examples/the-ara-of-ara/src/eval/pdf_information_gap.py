#!/usr/bin/env python3
"""PDF Information Gap Analysis using PaperBench Rubrics.

Evaluates how much reproduction-critical information is present in a paper PDF
by scoring each PaperBench rubric leaf requirement against the PDF content.

For each requirement, rates:
  - sufficient: PDF contains all actionable detail needed (exact values, URLs, equations)
  - partial: Topic is mentioned but specific details are missing or require inference
  - absent: Requirement is not addressed in the PDF at all

This is a motivation experiment: it quantifies the "Storytelling Tax" — the gap between
what a paper says and what you need to know to reproduce it.

Usage:
  python code/eval/pdf_information_gap.py \
    --pdf code/pdfs/test-time-model-adaptation.pdf \
    --rubric code/eval/rubrics/test-time-model-adaptation.json \
    --output code/eval/results/info_gap_test-time-model-adaptation.json
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
import anthropic

# Load .env from code/ directory
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# ── Rubric Parsing ────────────────────────────────────────────────────────

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


# ── Evaluation Prompts ────────────────────────────────────────────────────

SYSTEM = dedent("""\
You are a meticulous reproduction auditor. Your task: determine whether a
research paper PDF provides sufficient, actionable information for an AI agent
to fulfill each PaperBench reproduction requirement — without guessing,
inferring, or consulting external sources.

STRICT EVALUATION CRITERIA:

"sufficient" — the PDF explicitly provides ALL details needed to implement this
requirement. An engineer reading ONLY this PDF could implement it without
making any assumptions. This means:
  - Exact numerical values where applicable (learning rates, batch sizes,
    epochs, thresholds, dimensions, seeds)
  - Complete mathematical formulations (full equations, not verbal summaries)
  - Specific model identifiers, library names, or download URLs
  - Precise dataset specifications (name, split, preprocessing, augmentation)
  - Architecture details at implementation level (layer sizes, activation
    functions, normalization choices)
  - Expected numerical results for validation (exact numbers, not just plots)

"partial" — the PDF addresses this topic but at least one critical detail is
missing, vague, or would require the reader to guess. Examples:
  - "We use Adam optimizer" without specifying learning rate or betas
  - "Standard data augmentation" without listing which augmentations
  - Results shown in figures without exact numerical values in tables
  - A method is named and cited but implementation details are deferred
    to the cited paper
  - "We follow [citation]" for key experimental settings
  - Model mentioned but exact pretrained checkpoint/version not specified

"absent" — the requirement is not addressed at all in the PDF, or the
information is so vague it provides no actionable guidance.

BE STRICT. A casual mention is NOT a specification. If implementing this
requirement from the PDF alone would require ANY guesswork, inference, or
checking external sources, it is "partial" at best.

GAP CATEGORIES (assign all that apply for partial/absent):
  - missing_hyperparameter: A specific numerical value is not stated
  - vague_description: Method described verbally but not precisely enough
  - missing_url: Code repository, dataset URL, or pretrained weight link absent
  - figure_only: Results appear in figures without numerical tables
  - implicit_assumption: Assumed to be standard practice but not stated
  - missing_baseline_detail: Baseline method implementation details omitted
  - cross_reference_only: Critical detail exists only in a cited paper, not here
  - ambiguous_specification: Multiple valid interpretations are possible
  - missing_code_detail: Code-level specifics (data structures, APIs) omitted
  - incomplete_equation: Math partially described or stated informally

Respond ONLY with a JSON array. No markdown fences, no explanation.
""")


def build_eval_prompt(batch):
    """Build evaluation prompt for a batch of rubric requirements."""
    reqs = ""
    for i, leaf in enumerate(batch):
        reqs += f"\n[R{i}] (id: {leaf['id']}, category: {leaf['task_category']}, "
        reqs += f"fine: {leaf.get('finegrained_task_category', '')})\n"
        reqs += f"Requirement: {leaf['requirements']}\n"

    return dedent(f"""\
Evaluate whether the paper PDF above provides sufficient, actionable
information for an AI agent to fulfill each of these PaperBench reproduction
requirements. Remember: the question is NOT "does the paper mention this topic"
but "does the paper give you EVERYTHING you need to implement this requirement
without guessing?"

<requirements>
{reqs}
</requirements>

For EACH requirement R0, R1, ..., return a JSON object:
{{
  "id": "<the requirement id from the [RN] header>",
  "rating": "sufficient" | "partial" | "absent",
  "gap_categories": ["category1", ...],
  "evidence": "exact quote or paraphrase of what the PDF says (or 'not found')",
  "missing": "what specific detail is missing or vague (null if sufficient)",
  "confidence": "high" | "medium" | "low"
}}

Return a JSON array with exactly {len(batch)} objects, one per requirement.
Do NOT wrap in markdown code fences. Return ONLY the JSON array.""")


# ── API Evaluation ────────────────────────────────────────────────────────

def _safe_parse_json_array(text):
    """Try to parse a JSON array, handling extra trailing text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find the array boundaries
    start = text.find("[")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def evaluate_batch(client, pdf_b64, batch, model="claude-sonnet-4-6"):
    """Evaluate a batch of rubric requirements against the PDF."""
    prompt = build_eval_prompt(batch)

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_b64,
                    },
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }],
    )

    text = response.content[0].text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"```\w*\n?", "", text).strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    results = _safe_parse_json_array(text)
    if results is None:
        print(f"  WARNING: JSON parse failed, retrying with strict prompt...")
        response2 = client.messages.create(
            model=model,
            max_tokens=8192,
            system=SYSTEM + "\nCRITICAL: Return ONLY a valid JSON array. No markdown, no text.",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                        "cache_control": {"type": "ephemeral"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        text2 = response2.content[0].text.strip()
        if text2.startswith("```"):
            text2 = re.sub(r"```\w*\n?", "", text2).strip()
        if text2.endswith("```"):
            text2 = text2[:-3].strip()
        results = _safe_parse_json_array(text2)
        if results is None:
            print(f"  ERROR: JSON parse failed on retry too, marking batch as absent")
            results = []

    # Merge results back with rubric metadata
    merged = []
    for i, leaf in enumerate(batch):
        if i < len(results):
            r = results[i]
            r["rubric_id"] = leaf["id"]
            r["requirements"] = leaf["requirements"]
            r["task_category"] = leaf["task_category"]
            r["finegrained_task_category"] = leaf.get("finegrained_task_category", "")
            r["weight"] = leaf.get("weight", 1)
            r["depth"] = leaf.get("depth", 0)
            r["path"] = leaf.get("path", "")
            merged.append(r)
        else:
            merged.append({
                "rubric_id": leaf["id"],
                "requirements": leaf["requirements"],
                "task_category": leaf["task_category"],
                "finegrained_task_category": leaf.get("finegrained_task_category", ""),
                "weight": leaf.get("weight", 1),
                "depth": leaf.get("depth", 0),
                "path": leaf.get("path", ""),
                "rating": "absent",
                "gap_categories": ["evaluation_error"],
                "evidence": "not evaluated — batch result truncated",
                "missing": "evaluation failed",
                "confidence": "low",
            })

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
        "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
    }

    return merged, usage


def evaluate_batch_timed(client, pdf_b64, batch, model="claude-sonnet-4-6"):
    """Wrapper that adds wall-clock timing."""
    t0 = time.time()
    merged, usage = evaluate_batch(client, pdf_b64, batch, model=model)
    elapsed = time.time() - t0
    usage["wall_seconds"] = round(elapsed, 1)
    return merged, usage


# ── Metrics ───────────────────────────────────────────────────────────────

def compute_metrics(all_results):
    """Compute summary metrics from all evaluation results."""
    total = len(all_results)
    sufficient = sum(1 for r in all_results if r["rating"] == "sufficient")
    partial = sum(1 for r in all_results if r["rating"] == "partial")
    absent = sum(1 for r in all_results if r["rating"] == "absent")

    # Weighted
    total_w = sum(r.get("weight", 1) for r in all_results)
    suf_w = sum(r.get("weight", 1) for r in all_results if r["rating"] == "sufficient")
    par_w = sum(r.get("weight", 1) for r in all_results if r["rating"] == "partial")

    # By task category
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

    # By finegrained category
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

    # Confidence distribution
    confidence = {}
    for r in all_results:
        c = r.get("confidence", "unknown")
        confidence[c] = confidence.get(c, 0) + 1

    return {
        "summary": {
            "total_requirements": total,
            "sufficient": sufficient,
            "partial": partial,
            "absent": absent,
            "pct_sufficient": round(sufficient / total, 3),
            "pct_partial": round(partial / total, 3),
            "pct_absent": round(absent / total, 3),
            "information_coverage": round((sufficient + 0.5 * partial) / total, 3),
            "weighted_coverage": round((suf_w + 0.5 * par_w) / total_w, 3),
        },
        "by_task_category": by_cat,
        "by_finegrained_category": by_fine,
        "gap_distribution": gap_dist,
        "confidence_distribution": confidence,
    }


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PDF Information Gap Analysis using PaperBench rubrics"
    )
    parser.add_argument("--pdf", required=True, help="Path to paper PDF")
    parser.add_argument("--rubric", required=True, help="Path to PaperBench rubric.json")
    parser.add_argument("--output", default=None, help="Output JSON path")
    parser.add_argument("--model", default="claude-sonnet-4-6",
                        help="Model for evaluation (default: claude-sonnet-4-6)")
    parser.add_argument("--batch-size", type=int, default=12,
                        help="Requirements per API call (default: 12)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    rubric_path = Path(args.rubric)

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)
    if not rubric_path.exists():
        print(f"ERROR: Rubric not found: {rubric_path}")
        sys.exit(1)

    print(f"{'=' * 60}")
    print("PDF Information Gap Analysis (PaperBench Rubric)")
    print(f"{'=' * 60}")
    print(f"PDF:        {pdf_path}")
    print(f"Rubric:     {rubric_path}")
    print(f"Model:      {args.model}")
    print(f"Batch size: {args.batch_size}")

    # 1. Parse rubric
    with open(rubric_path) as f:
        rubric = json.load(f)
    leaves = flatten_rubric(rubric)
    print(f"\n{len(leaves)} leaf requirements to evaluate\n")

    # Category breakdown
    cats = {}
    for l in leaves:
        c = l["task_category"]
        cats[c] = cats.get(c, 0) + 1
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")

    # 2. Load PDF as base64
    pdf_bytes = pdf_path.read_bytes()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
    print(f"\nPDF size: {len(pdf_bytes) / 1024:.0f} KB")

    # 3. Evaluate in batches
    client = anthropic.Anthropic()
    all_results = []
    total_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "wall_seconds": 0,
    }
    batch_timings = []

    t_start = time.time()
    n_batches = (len(leaves) + args.batch_size - 1) // args.batch_size
    for i in range(0, len(leaves), args.batch_size):
        batch = leaves[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        print(f"\n[{batch_num}/{n_batches}] Evaluating {len(batch)} requirements...")

        results, usage = evaluate_batch_timed(client, pdf_b64, batch, model=args.model)
        all_results.extend(results)

        for k in total_usage:
            total_usage[k] += usage.get(k, 0)
        batch_timings.append({
            "batch": batch_num,
            "n_requirements": len(batch),
            "wall_seconds": usage["wall_seconds"],
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cache_read_input_tokens": usage["cache_read_input_tokens"],
        })

        # Progress
        suf = sum(1 for r in results if r["rating"] == "sufficient")
        par = sum(1 for r in results if r["rating"] == "partial")
        abs_ = sum(1 for r in results if r["rating"] == "absent")
        cached = usage.get("cache_read_input_tokens", 0)
        print(f"  → sufficient={suf}, partial={par}, absent={abs_}"
              f"  ({usage['wall_seconds']:.1f}s, cache_read={cached:,})")

    total_wall = round(time.time() - t_start, 1)
    total_usage["total_wall_seconds"] = total_wall

    # 4. Compute metrics
    metrics = compute_metrics(all_results)

    # 5. Build output
    output = {
        "experiment": "PDF Information Gap Analysis",
        "description": (
            "Strict evaluation of whether the paper PDF provides sufficient, "
            "actionable information for each PaperBench rubric leaf requirement. "
            "Measures the 'Storytelling Tax' — the gap between narrative prose "
            "and reproduction-grade specification."
        ),
        "paper": rubric.get("requirements", ""),
        "pdf_path": str(pdf_path),
        "rubric_path": str(rubric_path),
        "model": args.model,
        "n_requirements": len(leaves),
        "metrics": metrics,
        "token_usage": total_usage,
        "batch_timings": batch_timings,
        "detailed_results": all_results,
    }

    # Save
    output_path = Path(args.output) if args.output else (
        Path(__file__).parent / "results" / f"info_gap_{pdf_path.stem}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n")

    # ── Print Summary ─────────────────────────────────────────────────
    s = metrics["summary"]
    print(f"\n{'=' * 60}")
    print("RESULTS: PDF Information Gap")
    print(f"{'=' * 60}")
    print(f"\nTotal requirements: {s['total_requirements']}")
    print(f"  Sufficient:       {s['sufficient']:4d}  ({s['pct_sufficient']:.1%})")
    print(f"  Partial:          {s['partial']:4d}  ({s['pct_partial']:.1%})")
    print(f"  Absent:           {s['absent']:4d}  ({s['pct_absent']:.1%})")
    print(f"  Info coverage:    {s['information_coverage']:.1%}")
    print(f"  Weighted cov:     {s['weighted_coverage']:.1%}")

    print(f"\nBy task category:")
    for cat, info in sorted(metrics["by_task_category"].items()):
        print(f"  {cat:25s} (n={info['total']:3d})  "
              f"suf={info['pct_sufficient']:.0%}  "
              f"par={info['pct_partial']:.0%}  "
              f"abs={info['pct_absent']:.0%}")

    print(f"\nBy fine-grained category:")
    for fine, info in sorted(metrics["by_finegrained_category"].items()):
        print(f"  {fine:40s} (n={info['total']:3d})  "
              f"suf={info['pct_sufficient']:.0%}  "
              f"par={info['pct_partial']:.0%}  "
              f"abs={info['pct_absent']:.0%}")

    n_gaps = s["partial"] + s["absent"]
    print(f"\nGap distribution (across {n_gaps} non-sufficient requirements):")
    for gap, info in metrics["gap_distribution"].items():
        print(f"  {gap:35s}  {info['count']:3d}  ({info['pct_of_gaps']:.0%})")

    print(f"\nConfidence: {metrics['confidence_distribution']}")
    print(f"\nTiming & cost:")
    print(f"  Total wall time:   {total_wall:.0f}s ({total_wall/60:.1f}min)")
    print(f"  Avg per batch:     {total_wall/n_batches:.1f}s")
    print(f"  Token usage:       {total_usage['input_tokens']:,} in / "
          f"{total_usage['output_tokens']:,} out")
    print(f"  Cache:             {total_usage['cache_creation_input_tokens']:,} created, "
          f"{total_usage['cache_read_input_tokens']:,} read")
    effective_input = (total_usage['input_tokens']
                       - total_usage['cache_read_input_tokens']
                       + total_usage['cache_read_input_tokens'] * 0.1)
    est_cost = (effective_input / 1_000_000 * 3.0
                + total_usage['output_tokens'] / 1_000_000 * 15.0)
    print(f"  Est. cost (Sonnet): ~${est_cost:.2f}")
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
