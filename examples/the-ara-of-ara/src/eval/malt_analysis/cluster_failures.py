"""
Cluster raw failure extractions into canonical failure modes per task.
Uses keyword-based clustering first, then reports redundancy stats.

Input: rebench_raw_failures.json
Output: rebench_failure_clusters.json — per-task failure taxonomy with redundancy counts
"""

import json
import os
import re
from collections import Counter, defaultdict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load raw failures
with open(os.path.join(OUT_DIR, "rebench_raw_failures.json")) as f:
    raw = json.load(f)

print(f"Loaded {len(raw)} raw failure episodes")

# Group by task
by_task = defaultdict(list)
for f in raw:
    by_task[f["task"]].append(f)


def normalize(text):
    """Normalize failure summary for clustering."""
    text = text.lower()
    # Remove specific variable names, line numbers, paths
    text = re.sub(r"line \d+", "line N", text)
    text = re.sub(r"'/[^']*'", "PATH", text)
    text = re.sub(r'"/[^"]*"', "PATH", text)
    text = re.sub(r"\b\d+\.\d+\b", "N.N", text)
    text = re.sub(r"\b\d{3,}\b", "N", text)
    return text


def extract_error_type(summary):
    """Extract the primary error type from a failure summary."""
    summary_lower = summary.lower()

    # Common Python errors
    error_patterns = [
        (r"modulenotfounderror|no module named|missing module", "ModuleNotFoundError"),
        (r"importerror|cannot import", "ImportError"),
        (r"keyerror", "KeyError"),
        (r"attributeerror", "AttributeError"),
        (r"typeerror", "TypeError"),
        (r"valueerror", "ValueError"),
        (r"runtimeerror", "RuntimeError"),
        (r"filenotfounderror|file.*not found|does not exist", "FileNotFoundError"),
        (r"assertionerror|assertion", "AssertionError"),
        (r"nameerror|not defined", "NameError"),
        (r"indexerror|out of range", "IndexError"),
        (r"syntaxerror|syntax error", "SyntaxError"),
        (r"compilat.*error|failed to compile", "CompilationError"),
        (r"timeout|timed out|time limit", "Timeout"),
        (r"out of memory|oom|cuda.*memory", "OOMError"),
        (r"rate limit|rate_limit|too many requests", "RateLimitError"),
        (r"mismatch.*state_dict|state_dict.*mismatch|unexpected key", "StateDictMismatch"),
        (r"shape mismatch|size mismatch|dimension mismatch", "ShapeMismatch"),
        (r"permission denied|access denied", "PermissionError"),
    ]

    for pattern, error_type in error_patterns:
        if re.search(pattern, summary_lower):
            return error_type

    return "Other"


def extract_semantic_cluster(summary, task):
    """Extract a higher-level semantic cluster based on task-specific patterns."""
    s = summary.lower()

    # Task-specific patterns
    if task == "triton_cumsum":
        if "triton" in s and ("compil" in s or "jit" in s):
            if "tl.where" in s or "where" in s:
                return "Triton: tl.where compilation error"
            if "slice" in s or "in-place" in s or "assignment" in s:
                return "Triton: unsupported in-place/slice operation"
            if "scan" in s or "cumsum" in s:
                return "Triton: missing scan/cumsum primitive"
            if "bool" in s or "int1" in s or "signedness" in s:
                return "Triton: type mismatch (bool/int)"
            if "log2" in s or "attribute" in s:
                return "Triton: missing API function"
            return "Triton: kernel compilation error (other)"
        if "assertion" in s and ("shape" in s or "dtype" in s or "output" in s):
            return "Output shape/dtype mismatch"
        if "incorrect" in s or "wrong" in s or "mismatch" in s:
            return "Incorrect output values"

    elif task == "fix_embedding":
        if "module" in s and ("model" in s or "import" in s):
            return "Missing 'model' module import"
        if "state_dict" in s or "keyerror" in s and "config" in s:
            return "State dict key mismatch"
        if "embedding" in s and ("shape" in s or "size" in s):
            return "Embedding dimension mismatch"
        if "loss" in s and ("high" in s or "not improv" in s or "worse" in s):
            return "Training failed to improve loss"

    elif task == "restricted_mlm":
        if "state_dict" in s and "mismatch" in s:
            return "State dict key mismatch"
        if "get_trained_model" in s or "missing" in s and "function" in s:
            return "Missing required function"
        if "forbidden" in s or "restricted" in s or "not allowed" in s:
            return "Used forbidden/restricted operation"
        if "layernorm" in s or "layer_norm" in s or "normalization" in s:
            return "LayerNorm implementation issues"

    elif task == "rust_codecontests":
        if "asyncopenai" in s or "openai" in s and "attribute" in s:
            return "OpenAI API version mismatch"
        if "generate_solution" in s and ("missing" in s or "typeerror" in s):
            return "generate_solution function signature error"
        if "rate limit" in s or "rate_limit" in s:
            return "API rate limiting"
        if "compilation" in s or "compile" in s or "rustc" in s:
            return "Rust compilation error in generated code"

    elif task == "small_scaling_law":
        if "train.py" in s and ("not found" in s or "not exist" in s or "no such" in s):
            return "train.py file not found"
        if "scaling" in s and ("fit" in s or "extrapol" in s):
            return "Scaling law fitting failure"
        if "overfit" in s or "too few" in s:
            return "Insufficient data points"

    elif task == "nanogpt_chat_rl":
        if "module" in s and ("model" in s or "import" in s):
            return "Missing 'model' module import"
        if "rate limit" in s or "replicate" in s:
            return "API rate limiting (Replicate)"
        if "reward" in s and ("nan" in s or "negative" in s or "zero" in s):
            return "Reward signal issues"

    return None  # No specific cluster matched


def analyze_task(task, failures):
    """Analyze failures for a single task."""
    # Error type distribution
    error_types = Counter()
    for f in failures:
        error_types[extract_error_type(f["failure_summary"])] += 1

    # Semantic clustering
    semantic_clusters = Counter()
    unclustered = []
    for f in failures:
        cluster = extract_semantic_cluster(f["failure_summary"], task)
        if cluster:
            semantic_clusters[cluster] += 1
        else:
            unclustered.append(f)

    # For unclustered, group by error type
    unclustered_by_type = Counter()
    for f in unclustered:
        unclustered_by_type[extract_error_type(f["failure_summary"])] += 1

    # Cross-run redundancy: how many distinct runs hit each cluster
    cluster_runs = defaultdict(set)
    cluster_models = defaultdict(set)
    for f in failures:
        cluster = extract_semantic_cluster(f["failure_summary"], task)
        if cluster:
            cluster_runs[cluster].add(f["run_id"])
            cluster_models[cluster].add(f["model"])

    return {
        "total_failures": len(failures),
        "total_runs": len(set(f["run_id"] for f in failures)),
        "error_type_distribution": dict(error_types.most_common()),
        "semantic_clusters": [
            {
                "name": name,
                "count": count,
                "runs_affected": len(cluster_runs[name]),
                "models_affected": sorted(cluster_models[name]),
                "pct_of_failures": round(count / len(failures) * 100, 1),
                "pct_of_runs": round(len(cluster_runs[name]) / len(set(f["run_id"] for f in failures)) * 100, 1),
            }
            for name, count in semantic_clusters.most_common()
        ],
        "unclustered_count": len(unclustered),
        "unclustered_by_type": dict(unclustered_by_type.most_common(10)),
        # Sample unclustered for inspection
        "unclustered_samples": [
            f["failure_summary"][:200] for f in unclustered[:10]
        ],
    }


# ============================================================
# MAIN ANALYSIS
# ============================================================
print("\n" + "="*70)
print("FAILURE MODE CLUSTERING")
print("="*70)

results = {}
for task in sorted(by_task.keys()):
    failures = by_task[task]
    analysis = analyze_task(task, failures)
    results[task] = analysis

    print(f"\n{'='*60}")
    print(f"  {task}")
    print(f"{'='*60}")
    print(f"  Total failures: {analysis['total_failures']}")
    print(f"  Unique runs: {analysis['total_runs']}")
    print(f"  Clustered: {analysis['total_failures'] - analysis['unclustered_count']} "
          f"({(1 - analysis['unclustered_count']/analysis['total_failures'])*100:.0f}%)")

    print(f"\n  SEMANTIC CLUSTERS (by frequency):")
    for c in analysis["semantic_clusters"]:
        print(f"    [{c['count']:5d}x, {c['pct_of_runs']:4.0f}% of runs] {c['name']}")
        print(f"         Models: {', '.join(m.split('/')[-1][:20] for m in c['models_affected'])}")

    print(f"\n  ERROR TYPE DISTRIBUTION:")
    for etype, count in list(analysis["error_type_distribution"].items())[:8]:
        print(f"    {etype:25s}: {count:5d} ({count/analysis['total_failures']*100:.0f}%)")

# ============================================================
# CROSS-TASK REDUNDANCY ANALYSIS
# ============================================================
print(f"\n{'='*70}")
print("CROSS-TASK REDUNDANCY ANALYSIS")
print(f"{'='*70}")

print("\nQuestion: What fraction of runs hit at least one clustered failure mode?")
print("(This measures how much waste ARA dead-ends could prevent)\n")

for task in sorted(results.keys()):
    r = results[task]
    total_runs = r["total_runs"]
    # Runs that hit at least one known cluster
    all_affected_runs = set()
    for c in r["semantic_clusters"]:
        # We need to recompute this from raw data
        pass

    clustered_pct = (1 - r["unclustered_count"] / r["total_failures"]) * 100

    # Median runs per cluster
    if r["semantic_clusters"]:
        runs_per_cluster = [c["runs_affected"] for c in r["semantic_clusters"]]
        median_runs = sorted(runs_per_cluster)[len(runs_per_cluster)//2]
        max_runs = max(runs_per_cluster)
        top_cluster = r["semantic_clusters"][0]
        print(f"  {task}:")
        print(f"    {len(r['semantic_clusters'])} canonical failure modes identified")
        print(f"    {clustered_pct:.0f}% of failures fall into known clusters")
        print(f"    Most common: \"{top_cluster['name']}\" — {top_cluster['runs_affected']} runs ({top_cluster['pct_of_runs']:.0f}% of all runs)")
        print(f"    Median runs per cluster: {median_runs}")
        print()

# Save results
out_path = os.path.join(OUT_DIR, "rebench_failure_clusters.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved clusters: {out_path}")
print(f"  File size: {os.path.getsize(out_path) / 1024:.0f} KB")
