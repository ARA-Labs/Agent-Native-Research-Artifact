"""
Download and explore MALT transcripts for RE-BENCH tasks.
Goal: Assess feasibility of extracting structured failure modes from real agent traces.
"""

import json
import os
from collections import Counter, defaultdict
from datasets import load_dataset

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# RE-BENCH task IDs (from the RE-Bench paper / our artifacts)
REBENCH_TASKS = [
    "fix_embedding", "triton_cumsum", "optimize_llm_foundry",
    "small_scaling_law", "restricted_mlm", "nanogpt_chat_rl", "rust_codecontests"
]

# ============================================================
# 1. LOAD MALT TRANSCRIPTS (streaming to avoid huge download)
# ============================================================
print("Loading MALT transcripts (streaming)...")
ds = load_dataset("metr-evals/malt-transcripts-public", "default", split="transcripts", streaming=True)

# Collect RE-BENCH runs
rebench_runs = []
total_scanned = 0

for row in ds:
    total_scanned += 1
    if total_scanned % 2000 == 0:
        print(f"  scanned {total_scanned} runs, found {len(rebench_runs)} RE-BENCH...")

    task_id = row.get("task_id", "")
    # RE-BENCH tasks might have various ID formats - check for substring match
    is_rebench = any(t in task_id.lower() for t in REBENCH_TASKS)
    if is_rebench:
        rebench_runs.append(row)

print(f"\nScanned {total_scanned} total runs")
print(f"Found {len(rebench_runs)} RE-BENCH runs")

if not rebench_runs:
    # Try to find what task IDs look like
    print("\nNo exact matches. Searching for similar task IDs...")
    ds2 = load_dataset("metr-evals/malt-transcripts-public", "default", split="transcripts", streaming=True)
    all_task_ids = set()
    for i, row in enumerate(ds2):
        all_task_ids.add(row.get("task_id", ""))
        if i >= 5000:
            break

    print(f"\nSample task IDs (first 5000 runs):")
    for tid in sorted(all_task_ids):
        print(f"  {tid}")

    # Also check labels
    print("\nSearching by labels...")
    ds3 = load_dataset("metr-evals/malt-transcripts-public", "default", split="transcripts", streaming=True)
    label_counts = Counter()
    for i, row in enumerate(ds3):
        for label in (row.get("labels") or []):
            label_counts[label] += 1
        if i >= 5000:
            break
    print(f"\nLabel distribution (first 5000):")
    for label, count in label_counts.most_common(30):
        print(f"  {label}: {count}")

    exit(0)

# ============================================================
# 2. BASIC STATS
# ============================================================
print("\n" + "="*70)
print("2. RE-BENCH TRACE STATISTICS")
print("="*70)

# Group by task
by_task = defaultdict(list)
for r in rebench_runs:
    by_task[r["task_id"]].append(r)

for task_id in sorted(by_task.keys()):
    runs = by_task[task_id]
    models = set(r.get("model", "?") for r in runs)
    node_counts = [len(r.get("nodes", [])) for r in runs]
    scores = [r.get("score_cont", None) for r in runs if r.get("score_cont") is not None]
    labels = [l for r in runs for l in (r.get("labels") or [])]

    print(f"\n{task_id}:")
    print(f"  Runs: {len(runs)}")
    print(f"  Models: {models}")
    print(f"  Nodes per run: min={min(node_counts)}, max={max(node_counts)}, avg={sum(node_counts)/len(node_counts):.0f}")
    if scores:
        print(f"  Scores: min={min(scores):.3f}, max={max(scores):.3f}, avg={sum(scores)/len(scores):.3f}")
    print(f"  Labels: {dict(Counter(labels))}")

# ============================================================
# 3. EXPLORE NODE STRUCTURE OF FAILED RUNS
# ============================================================
print("\n" + "="*70)
print("3. FAILED RUN NODE STRUCTURE")
print("="*70)

# Pick a few failed runs to inspect
for task_id in sorted(by_task.keys())[:3]:  # First 3 tasks
    runs = by_task[task_id]
    # Find failed runs (score_cont close to 0 or negative)
    failed = [r for r in runs if (r.get("score_cont") or 0) <= 0.1]
    if not failed:
        failed = sorted(runs, key=lambda r: r.get("score_cont", 0))[:2]

    print(f"\n--- {task_id} (failed runs: {len(failed)}) ---")

    for r in failed[:1]:  # Just one per task
        nodes = r.get("nodes", [])
        print(f"  Run: {r.get('run_id', '?')}, model={r.get('model', '?')}, score={r.get('score_cont', '?')}")
        print(f"  Total nodes: {len(nodes)}")

        if nodes:
            # Show first node structure
            first = nodes[0]
            print(f"  Node keys: {list(first.keys())}")

            # Show a few nodes to understand the content
            for i, node in enumerate(nodes[:3]):
                content = str(node.get("content", ""))[:500]
                print(f"\n  Node {i} (role={node.get('role', '?')}, type={node.get('type', '?')}):")
                print(f"    {content[:300]}...")

# ============================================================
# 4. SAVE FULL RE-BENCH TRACES FOR DETAILED ANALYSIS
# ============================================================
print("\n" + "="*70)
print("4. SAVING RE-BENCH TRACES")
print("="*70)

# Save metadata (without full node content, to keep file small)
meta_path = os.path.join(OUT_DIR, "rebench_traces_meta.json")
meta = []
for r in rebench_runs:
    meta.append({
        "run_id": r.get("run_id"),
        "task_id": r.get("task_id"),
        "model": r.get("model"),
        "score_cont": r.get("score_cont"),
        "score_binarized": r.get("score_binarized"),
        "labels": r.get("labels"),
        "has_chain_of_thought": r.get("has_chain_of_thought"),
        "node_count": len(r.get("nodes", [])),
    })
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"Saved metadata: {meta_path} ({len(meta)} runs)")

# Save a few full traces for detailed inspection
detail_path = os.path.join(OUT_DIR, "rebench_traces_sample.json")
# Pick 2 failed + 1 successful per task (if available)
sample_traces = []
for task_id in sorted(by_task.keys()):
    runs = by_task[task_id]
    failed = sorted([r for r in runs if (r.get("score_cont") or 0) <= 0.3],
                     key=lambda r: r.get("score_cont", 0))
    success = sorted([r for r in runs if (r.get("score_cont") or 0) > 0.5],
                      key=lambda r: -r.get("score_cont", 0))

    selected = failed[:2] + success[:1]
    for r in selected:
        # Truncate node content to keep file manageable
        truncated_nodes = []
        for node in r.get("nodes", [])[:50]:  # First 50 nodes
            truncated = {k: v for k, v in node.items()}
            if "content" in truncated and isinstance(truncated["content"], str):
                truncated["content"] = truncated["content"][:2000]
            truncated_nodes.append(truncated)

        sample_traces.append({
            "run_id": r.get("run_id"),
            "task_id": r.get("task_id"),
            "model": r.get("model"),
            "score_cont": r.get("score_cont"),
            "score_binarized": r.get("score_binarized"),
            "labels": r.get("labels"),
            "total_nodes": len(r.get("nodes", [])),
            "nodes_sample": truncated_nodes,
        })

with open(detail_path, "w") as f:
    json.dump(sample_traces, f, indent=2, default=str)
print(f"Saved sample traces: {detail_path} ({len(sample_traces)} runs, truncated)")
print(f"  File size: {os.path.getsize(detail_path) / 1024:.0f} KB")

print("\nDone!")
