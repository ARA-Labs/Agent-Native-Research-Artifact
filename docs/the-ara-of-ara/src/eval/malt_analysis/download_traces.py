#!/usr/bin/env python3
"""
Download full MALT traces for RE-BENCH tasks and save to scratch.
Streams directly to JSONL files (one run per line) to avoid OOM.

Usage: python download_traces.py [task_name ...]
  If no args, downloads all 6 tasks.
"""

import json
import sys
import os
from pathlib import Path
from datasets import load_dataset

SCRATCH = Path("/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/malt_analysis")
SCRATCH.mkdir(parents=True, exist_ok=True)

TASK_IDS = {
    "fix_embedding":     "ai_rd_fix_embedding",
    "triton_cumsum":     "ai_rd_triton_cumsum",
    "small_scaling_law": "ai_rd_small_scaling_law",
    "restricted_mlm":    "ai_rd_restricted_mlm",
    "nanogpt_chat_rl":   "ai_rd_nanogpt_chat_rl",
    "rust_codecontests": "ai_rd_rust_codecontests_inference",
}

TARGET_TASKS = sys.argv[1:] if len(sys.argv) > 1 else list(TASK_IDS.keys())

# Open one JSONL file per target task (write immediately, no buffering)
file_handles = {}
counts = {}
for task in TARGET_TASKS:
    p = SCRATCH / f"{task}_traces.jsonl"
    file_handles[task] = open(p, "w")
    counts[task] = 0

MSG_CONTENT_LIMIT = 2000  # chars per message content


def extract_run(row):
    nodes = row.get("nodes", [])
    messages = []
    for node in nodes:
        nd = node.get("node_data", {})
        msg = nd.get("message", {})
        role = msg.get("role", "")
        content = (msg.get("content") or "")[:MSG_CONTENT_LIMIT]
        fc = msg.get("function_call")

        entry = {"role": role}
        if content:
            entry["content"] = content
        if fc:
            fc = fc if isinstance(fc, dict) else {}
            args = fc.get("arguments", "")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = args[:500]
            elif isinstance(args, dict):
                # Truncate long string values
                args = {k: (v[:500] if isinstance(v, str) and len(v) > 500 else v)
                        for k, v in args.items()}
            entry["function_call"] = {"name": fc.get("name", ""), "arguments": args}
        messages.append(entry)

    return {
        "run_id": row.get("run_id"),
        "task_id": row.get("task_id"),
        "model": row.get("model"),
        "score_cont": row.get("score_cont"),
        "score_binarized": row.get("score_binarized"),
        "labels": row.get("labels", []),
        "has_chain_of_thought": row.get("has_chain_of_thought"),
        "node_count": len(nodes),
        "messages": messages,
    }


print("Streaming metr-evals/malt-transcripts-public ...")
sys.stdout.flush()

ds = load_dataset(
    "metr-evals/malt-transcripts-public", "default",
    split="transcripts", streaming=True
)

total_scanned = 0
for row in ds:
    total_scanned += 1
    if total_scanned % 2000 == 0:
        status = {t: counts[t] for t in TARGET_TASKS if counts[t] > 0}
        print(f"  scanned {total_scanned:,}  found: {status}")
        sys.stdout.flush()

    task_id = row.get("task_id", "")
    for short, prefix in TASK_IDS.items():
        if short not in TARGET_TASKS:
            continue
        if task_id.startswith(prefix):
            run = extract_run(row)
            file_handles[short].write(json.dumps(run, default=str) + "\n")
            file_handles[short].flush()
            counts[short] += 1
            break

# Close files
for fh in file_handles.values():
    fh.close()

print(f"\nScanned {total_scanned:,} total runs.")
for task in TARGET_TASKS:
    p = SCRATCH / f"{task}_traces.jsonl"
    if p.exists():
        size_mb = p.stat().st_size / 1e6
        print(f"  {task}: {counts[task]} runs -> {p} ({size_mb:.1f} MB)")

print("Done.")
os._exit(0)  # avoid datasets GIL crash on cleanup
