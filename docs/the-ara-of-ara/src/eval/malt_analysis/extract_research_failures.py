"""
Filter raw MALT failures to keep only research-level failures.
Infrastructure failures (import errors, file not found, API issues, etc.) are excluded.

For each remaining failure, output the agent's hypothesis + the failure summary,
grouped by task, for manual/LLM analysis.
"""

import json
import os
import re
from collections import Counter, defaultdict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(OUT_DIR, "rebench_raw_failures.json")) as f:
    raw = json.load(f)

print(f"Loaded {len(raw)} raw failure episodes")

# ============================================================
# Infrastructure failure patterns to EXCLUDE
# ============================================================
INFRA_PATTERNS = [
    # Import / module errors
    r"no module named",
    r"modulenotfounderror",
    r"importerror",
    r"cannot import",
    r"missing module",
    # File not found
    r"filenotfounderror",
    r"no such file",
    r"file.*does not exist",
    r"file.*not found",
    r"directory.*not found",
    r"path.*not found",
    # API / rate limiting
    r"rate limit",
    r"rate_limit",
    r"too many requests",
    r"api.*error",
    r"api.*timeout",
    r"asyncopenai",
    r"openai.*attribute",
    r"replicate.*api",
    # Permission / access
    r"permission denied",
    r"access denied",
    # State dict / model loading (environment setup issue)
    r"state_dict.*mismatch",
    r"unexpected key.*state_dict",
    r"missing key.*state_dict",
    r"state_dict.*unexpected",
    r"mismatch.*state_dict",
    r"load_state_dict",
    # Syntax / name errors (typos, wrong API)
    r"syntaxerror",
    r"syntax error",
    r"indentation",
    r"nameError.*not defined",
    r"is not defined",
    # Pure environment / setup
    r"pip install",
    r"command not found",
    r"executable.*not found",
    r"package.*not installed",
    r"missing.*dependency",
    # Generic connection / timeout
    r"connection.*refused",
    r"connection.*reset",
    r"connection.*timeout",
    r"timed out waiting",
    # Missing function signature (env setup)
    r"missing.*function.*get_trained",
    r"get_trained_model.*missing",
    r"function.*missing from",
    r"missing from the.*file",
    r"required function.*missing",
]

INFRA_RE = re.compile("|".join(INFRA_PATTERNS), re.IGNORECASE)


def is_infrastructure(failure):
    """Return True if this failure is infrastructure-level, not research-level."""
    summary = failure.get("failure_summary", "")
    hypothesis = failure.get("hypothesis", "")

    # Check summary against infra patterns
    if INFRA_RE.search(summary):
        return True

    # Also exclude if the hypothesis is empty (no research reasoning)
    if not hypothesis or len(hypothesis) < 20:
        return True

    return False


# Filter
by_task = defaultdict(list)
infra_count = 0
research_count = 0

for f in raw:
    if is_infrastructure(f):
        infra_count += 1
    else:
        research_count += 1
        by_task[f["task"]].append(f)

print(f"\nInfrastructure failures (excluded): {infra_count} ({infra_count/len(raw)*100:.0f}%)")
print(f"Research-level failures (kept):     {research_count} ({research_count/len(raw)*100:.0f}%)")

# ============================================================
# Per-task analysis of research failures
# ============================================================
for task in sorted(by_task.keys()):
    failures = by_task[task]
    models = Counter(f["model"] for f in failures)
    runs = len(set(f["run_id"] for f in failures))

    print(f"\n{'='*70}")
    print(f"  {task}: {len(failures)} research failures across {runs} runs")
    print(f"{'='*70}")
    print(f"  Models: {dict(models.most_common(5))}")

    # Deduplicate by (hypothesis[:100], failure_summary[:100])
    seen = Counter()
    unique_failures = []
    for f in failures:
        key = (f["hypothesis"][:100], f["failure_summary"][:100])
        seen[key] += 1
        if seen[key] == 1:
            unique_failures.append(f)

    print(f"  Unique (by hypothesis+summary prefix): {len(unique_failures)}")

    # Show top 20 unique research failures with full context
    print(f"\n  TOP RESEARCH FAILURES:")
    # Sort by frequency of the pattern
    for i, f in enumerate(unique_failures[:20]):
        key = (f["hypothesis"][:100], f["failure_summary"][:100])
        freq = seen[key]
        print(f"\n  [{i+1}] (occurs {freq}x across runs)")
        print(f"  HYPOTHESIS: {f['hypothesis'][:300]}")
        print(f"  FAILURE:    {f['failure_summary'][:300]}")
        print(f"  MODEL:      {f['model']}")

# ============================================================
# Save research failures for LLM processing
# ============================================================
out_path = os.path.join(OUT_DIR, "rebench_research_failures.json")
all_research = []
for task in sorted(by_task.keys()):
    all_research.extend(by_task[task])

with open(out_path, "w") as f:
    json.dump(all_research, f, indent=2)
print(f"\nSaved {len(all_research)} research failures to {out_path}")
print(f"  File size: {os.path.getsize(out_path) / 1024:.0f} KB")

# Also save per-task summaries for easier processing
for task in sorted(by_task.keys()):
    failures = by_task[task]
    # Deduplicate and sort by frequency
    seen = Counter()
    deduped = []
    for f in failures:
        key = (f["hypothesis"][:150], f["failure_summary"][:150])
        seen[key] += 1
        if seen[key] == 1:
            f_copy = dict(f)
            f_copy["_dedup_key"] = f["hypothesis"][:150] + " ||| " + f["failure_summary"][:150]
            deduped.append(f_copy)

    # Add frequency
    for d in deduped:
        key = (d["hypothesis"][:150], d["failure_summary"][:150])
        d["frequency"] = seen[key]
        d["models_affected"] = list(set(
            f2["model"] for f2 in failures
            if f2["hypothesis"][:150] == d["hypothesis"][:150]
            and f2["failure_summary"][:150] == d["failure_summary"][:150]
        ))

    # Sort by frequency
    deduped.sort(key=lambda x: -x["frequency"])

    task_path = os.path.join(OUT_DIR, f"research_failures_{task}.json")
    with open(task_path, "w") as f:
        json.dump(deduped, f, indent=2)
    print(f"  {task}: {len(deduped)} unique patterns -> {task_path}")
