"""
Extract structured failure modes from MALT RE-BENCH traces.

For each RE-BENCH task:
1. Stream all runs from metr-evals/malt-transcripts-public
2. Extract (hypothesis, action, failure_mode, lesson) from submit_review(is_bug=true) nodes
3. Cluster/dedup failure modes
4. Output per-task failure taxonomies

Output: rebench_failure_modes.json
"""

import json
import os
from collections import Counter, defaultdict
from datasets import load_dataset

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

REBENCH_TASK_PREFIXES = [
    "ai_rd_fix_embedding",
    "ai_rd_triton_cumsum",
    "ai_rd_optimize_llm_foundry",
    "ai_rd_small_scaling_law",
    "ai_rd_restricted_mlm",
    "ai_rd_nanogpt_chat_rl",
    "ai_rd_rust_codecontests",
]

SHORT_NAME = {
    "ai_rd_fix_embedding": "fix_embedding",
    "ai_rd_triton_cumsum": "triton_cumsum",
    "ai_rd_optimize_llm_foundry": "optimize_llm_foundry",
    "ai_rd_small_scaling_law": "small_scaling_law",
    "ai_rd_restricted_mlm": "restricted_mlm",
    "ai_rd_nanogpt_chat_rl": "nanogpt_chat_rl",
    "ai_rd_rust_codecontests_inference": "rust_codecontests",
}


def extract_failures_from_run(run):
    """Extract failure episodes from a single run's node trace.

    A failure episode is: agent plan (assistant text) → code attempt → submit_review(is_bug=true).
    We extract the plan as hypothesis and the review summary as failure_mode.
    """
    nodes = run.get("nodes", [])
    failures = []

    # Walk through nodes looking for submit_review(is_bug=true)
    for i, node in enumerate(nodes):
        nd = node.get("node_data", {})
        msg = nd.get("message", {})
        role = msg.get("role", "")
        func_call = msg.get("function_call", None)

        if role != "assistant" or not func_call:
            continue

        fc = func_call if isinstance(func_call, dict) else {}
        if fc.get("name") != "submit_review":
            continue

        # Parse submit_review arguments
        args_raw = fc.get("arguments", "")
        if isinstance(args_raw, str):
            try:
                args = json.loads(args_raw)
            except json.JSONDecodeError:
                continue
        elif isinstance(args_raw, dict):
            args = args_raw
        else:
            continue

        is_bug = args.get("is_bug", False)
        summary = args.get("summary", "")

        if not is_bug or not summary:
            continue

        # Look backward for the agent's plan/hypothesis (most recent assistant text before this review)
        hypothesis = ""
        for j in range(i - 1, max(i - 6, -1), -1):
            prev_nd = nodes[j].get("node_data", {})
            prev_msg = prev_nd.get("message", {})
            prev_content = prev_msg.get("content", "")
            prev_role = prev_msg.get("role", "")
            if prev_role == "assistant" and prev_content and len(prev_content) > 30:
                # Take first 2 sentences as hypothesis
                sentences = prev_content.replace("\n", " ").split(". ")
                hypothesis = ". ".join(sentences[:2]).strip()
                if not hypothesis.endswith("."):
                    hypothesis += "."
                break

        failures.append({
            "hypothesis": hypothesis[:500],
            "failure_summary": summary[:500],
            "node_index": i,
        })

    return failures


def main():
    print("Loading MALT transcripts (streaming)...")
    ds = load_dataset(
        "metr-evals/malt-transcripts-public", "default",
        split="transcripts", streaming=True
    )

    # Collect failures per task per model
    task_failures = defaultdict(list)  # task -> list of failure dicts
    task_run_counts = Counter()
    task_model_counts = defaultdict(Counter)
    total_scanned = 0

    for row in ds:
        total_scanned += 1
        if total_scanned % 2000 == 0:
            n_failures = sum(len(v) for v in task_failures.values())
            print(f"  scanned {total_scanned} runs, {n_failures} failures extracted...")

        task_id = row.get("task_id", "")

        # Check if RE-BENCH task
        matched_task = None
        for prefix in REBENCH_TASK_PREFIXES:
            if task_id.startswith(prefix):
                matched_task = task_id.split("/")[0]  # Remove /main suffix
                break
        if not matched_task:
            continue

        short = SHORT_NAME.get(matched_task, matched_task)
        model = row.get("model", "unknown")
        task_run_counts[short] += 1
        task_model_counts[short][model] += 1

        # Extract failures
        failures = extract_failures_from_run(row)
        for f in failures:
            f["task"] = short
            f["model"] = model
            f["run_id"] = row.get("run_id")
            task_failures[short].append(f)

    print(f"\nScanned {total_scanned} total runs")
    print(f"\n{'='*70}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*70}")

    total_failures = 0
    for task in sorted(task_failures.keys()):
        failures = task_failures[task]
        total_failures += len(failures)
        models = task_model_counts[task]
        print(f"\n{task}:")
        print(f"  Runs: {task_run_counts[task]}")
        print(f"  Failures extracted: {len(failures)}")
        print(f"  Failures/run: {len(failures)/task_run_counts[task]:.1f}")
        print(f"  Models: {dict(models)}")

        # Show top failure summaries (deduplicated by first 100 chars)
        summary_counts = Counter()
        for f in failures:
            key = f["failure_summary"][:100]
            summary_counts[key] += 1

        print(f"  Unique failure patterns (by first 100 chars): {len(summary_counts)}")
        print(f"  Top 5 recurring failures:")
        for pattern, count in summary_counts.most_common(5):
            print(f"    [{count}x] {pattern}...")

    print(f"\nTotal failures across all tasks: {total_failures}")

    # Save raw failures
    raw_path = os.path.join(OUT_DIR, "rebench_raw_failures.json")
    all_failures = []
    for task in sorted(task_failures.keys()):
        all_failures.extend(task_failures[task])

    with open(raw_path, "w") as f:
        json.dump(all_failures, f, indent=2)
    print(f"\nSaved raw failures: {raw_path} ({len(all_failures)} entries)")
    print(f"  File size: {os.path.getsize(raw_path) / 1024:.0f} KB")

    # Save summary stats
    stats_path = os.path.join(OUT_DIR, "rebench_failure_stats.json")
    stats = {
        "total_runs_scanned": total_scanned,
        "rebench_runs": dict(task_run_counts),
        "failures_per_task": {t: len(f) for t, f in task_failures.items()},
        "total_failures": total_failures,
        "models_per_task": {t: dict(c) for t, c in task_model_counts.items()},
    }
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Saved stats: {stats_path}")


if __name__ == "__main__":
    main()
