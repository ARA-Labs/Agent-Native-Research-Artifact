#!/usr/bin/env python3
"""
Interactive reader: print structured summaries of MALT traces for a given task.
For each run, shows: model, node_count, and a structured breakdown of
  - assistant planning messages (text)
  - function_call (tool calls: name + key args)
  - tool results (content from user messages after tool calls)

Usage:
  python read_task_traces.py <task> [--run RUN_ID] [--max-runs N] [--max-nodes N]
  python read_task_traces.py triton_cumsum --max-runs 5 --max-nodes 60
  python read_task_traces.py fix_embedding --run 172246
"""

import json
import sys
import argparse
from pathlib import Path

SCRATCH = Path("/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/malt_analysis")


def print_run(run, max_nodes=80, show_tool_results=True, text_limit=600, result_limit=400):
    print(f"\n{'='*70}")
    print(f"RUN {run['run_id']} | model={run['model']} | nodes={run['node_count']} | score={run['score_cont']} | labels={run['labels']}")
    print(f"{'='*70}")

    msgs = run.get("messages", [])
    for i, msg in enumerate(msgs[:max_nodes]):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        fc = msg.get("function_call")

        if role == "assistant":
            if fc:
                name = fc.get("name", "?")
                args = fc.get("arguments", {})
                # Pretty-print key args
                if isinstance(args, dict):
                    args_str = json.dumps(args, ensure_ascii=False)
                    if len(args_str) > 300:
                        args_str = args_str[:300] + "..."
                else:
                    args_str = str(args)[:300]
                print(f"\n[{i}] TOOL_CALL: {name}({args_str})")
            elif content and content.strip():
                text = content.strip()
                if len(text) > text_limit:
                    text = text[:text_limit] + f"... [{len(content)} chars total]"
                print(f"\n[{i}] ASSISTANT: {text}")

        elif role == "user" and show_tool_results:
            if content and content.strip():
                text = content.strip()
                if len(text) > result_limit:
                    text = text[:result_limit] + f"... [{len(content)} chars total]"
                print(f"\n[{i}] RESULT: {text}")

        elif role == "tool" and show_tool_results:
            if content and content.strip():
                text = content.strip()
                if len(text) > result_limit:
                    text = text[:result_limit] + f"... [{len(content)} chars]"
                print(f"\n[{i}] TOOL_RESULT: {text}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", help="Task name (e.g. triton_cumsum)")
    parser.add_argument("--run", type=int, help="Specific run_id to show")
    parser.add_argument("--max-runs", type=int, default=5, help="Max runs to show")
    parser.add_argument("--max-nodes", type=int, default=80, help="Max messages per run")
    parser.add_argument("--no-results", action="store_true", help="Skip tool results")
    parser.add_argument("--sort", choices=["nodes_desc", "nodes_asc", "run_id"], default="nodes_desc")
    parser.add_argument("--model", help="Filter by model substring")
    parser.add_argument("--text-limit", type=int, default=600)
    parser.add_argument("--result-limit", type=int, default=400)
    args = parser.parse_args()

    trace_file = SCRATCH / f"{args.task}_traces.jsonl"
    if not trace_file.exists():
        print(f"ERROR: {trace_file} not found. Run download_traces.py first.")
        sys.exit(1)

    runs = [json.loads(line) for line in open(trace_file) if line.strip()]
    print(f"Loaded {len(runs)} runs for {args.task}")

    # Filter
    if args.run:
        runs = [r for r in runs if r["run_id"] == args.run]
    if args.model:
        runs = [r for r in runs if args.model.lower() in r["model"].lower()]

    # Sort
    if args.sort == "nodes_desc":
        runs.sort(key=lambda r: -r["node_count"])
    elif args.sort == "nodes_asc":
        runs.sort(key=lambda r: r["node_count"])

    print(f"Showing {min(args.max_runs, len(runs))} of {len(runs)} runs (sorted by {args.sort})")

    for run in runs[:args.max_runs]:
        print_run(
            run,
            max_nodes=args.max_nodes,
            show_tool_results=not args.no_results,
            text_limit=args.text_limit,
            result_limit=args.result_limit,
        )


if __name__ == "__main__":
    main()
