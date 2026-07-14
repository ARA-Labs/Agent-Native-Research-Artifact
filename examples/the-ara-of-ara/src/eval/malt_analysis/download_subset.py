"""Download a small subset of MALT dataset and explore its structure."""

from datasets import load_dataset
import json
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load DAG format (smaller, has structure info)
print("Loading MALT-transcripts-public (DAG format), streaming mode...")
ds = load_dataset("metr-evals/malt-transcripts-public", "default", split="transcripts", streaming=True)

# Take first 50 runs to explore
samples = []
for i, row in enumerate(ds):
    if i >= 50:
        break
    samples.append(row)
    if i % 10 == 0:
        print(f"  loaded {i+1} runs...")

print(f"\nLoaded {len(samples)} runs total")

# Explore schema
print("\n=== SCHEMA ===")
print(f"Top-level keys: {list(samples[0].keys())}")
print(f"\nFirst run metadata:")
for k, v in samples[0].items():
    if k != "nodes":
        print(f"  {k}: {v}")

print(f"\n  nodes: list of {len(samples[0]['nodes'])} nodes")
if samples[0]["nodes"]:
    first_node = samples[0]["nodes"][0]
    print(f"  First node keys: {list(first_node.keys())}")
    print(f"  First node: {json.dumps(first_node, indent=2, default=str)[:1000]}")

# Summary stats
print("\n=== SUMMARY STATS ===")
task_ids = [s["task_id"] for s in samples]
models = [s["model"] for s in samples]
labels_all = [l for s in samples for l in (s.get("labels") or [])]
node_counts = [len(s["nodes"]) for s in samples]

print(f"Unique task_ids: {len(set(task_ids))}")
print(f"  Tasks: {sorted(set(task_ids))[:20]}")
print(f"Unique models: {set(models)}")
print(f"Labels distribution: ", end="")
from collections import Counter
print(dict(Counter(labels_all)))
print(f"Node counts: min={min(node_counts)}, max={max(node_counts)}, avg={sum(node_counts)/len(node_counts):.0f}")
print(f"Runs with CoT: {sum(1 for s in samples if s.get('has_chain_of_thought'))}")

# Save subset for offline analysis
out_path = os.path.join(OUT_DIR, "malt_subset_50.json")
print(f"\nSaving subset to {out_path}...")

# Convert to serializable format
serializable = []
for s in samples:
    entry = {k: v for k, v in s.items() if k != "nodes"}
    entry["node_count"] = len(s["nodes"])
    # Save first 5 nodes as sample, full nodes separately
    entry["sample_nodes"] = s["nodes"][:5] if s["nodes"] else []
    serializable.append(entry)

with open(out_path, "w") as f:
    json.dump(serializable, f, indent=2, default=str)

# Save full node data for a few interesting runs
print("\nSaving full traces for detailed analysis...")
detailed = []
for s in samples[:10]:  # First 10 runs with full nodes
    detailed.append({
        "run_id": s["run_id"],
        "task_id": s["task_id"],
        "model": s["model"],
        "labels": s.get("labels", []),
        "has_chain_of_thought": s.get("has_chain_of_thought"),
        "node_count": len(s["nodes"]),
        "nodes": s["nodes"]
    })

detail_path = os.path.join(OUT_DIR, "malt_detailed_10.json")
with open(detail_path, "w") as f:
    json.dump(detailed, f, indent=2, default=str)

print(f"Saved {len(detailed)} detailed traces to {detail_path}")
print(f"Total size: {os.path.getsize(detail_path) / 1024:.0f} KB")
print("\nDone!")
