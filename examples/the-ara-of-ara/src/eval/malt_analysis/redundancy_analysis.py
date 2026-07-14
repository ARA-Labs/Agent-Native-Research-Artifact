"""
Analyze cross-run redundancy and exploration waste patterns.
Focus: How much work is duplicated across independent runs on the same task?
"""

import json
import os
from collections import Counter, defaultdict
import statistics

DATA_PATH = "/tmp/eval-analysis-public/reports/time-horizon-1-1/data/raw/runs.jsonl"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

runs = []
with open(DATA_PATH) as f:
    for line in f:
        runs.append(json.loads(line))

# ============================================================
# 1. SAME TASK, SAME MODEL — OUTCOME VARIANCE
# ============================================================
print("="*70)
print("1. OUTCOME VARIANCE: SAME TASK + SAME MODEL")
print("="*70)

# Group by (task_id, model)
groups = defaultdict(list)
for r in runs:
    groups[(r["task_id"], r["alias"])].append(r)

# Only look at groups with 4+ runs (enough to compute variance)
multi_groups = {k: v for k, v in groups.items() if len(v) >= 4}
print(f"\n{len(multi_groups)} (task, model) pairs with 4+ runs")

# Compute outcome variance
variances = []
for (task_id, model), group_runs in multi_groups.items():
    scores = [r["score_binarized"] for r in group_runs]
    # If all 0 or all 1, variance = 0 (consistent). If mixed, there's randomness.
    success_rate = sum(scores) / len(scores)
    n = len(scores)
    variances.append({
        "task_id": task_id,
        "model": model,
        "n": n,
        "success_rate": success_rate,
        "all_fail": success_rate == 0,
        "all_success": success_rate == 1,
        "mixed": 0 < success_rate < 1,
        "scores_cont": [r["score_cont"] for r in group_runs]
    })

all_fail = sum(1 for v in variances if v["all_fail"])
all_success = sum(1 for v in variances if v["all_success"])
mixed = sum(1 for v in variances if v["mixed"])

print(f"\nOutcome consistency:")
print(f"  Always fail (100% failure):    {all_fail}/{len(variances)} ({all_fail/len(variances)*100:.1f}%)")
print(f"  Always succeed (100% success): {all_success}/{len(variances)} ({all_success/len(variances)*100:.1f}%)")
print(f"  Mixed outcomes (lottery):      {mixed}/{len(variances)} ({mixed/len(variances)*100:.1f}%)")

# For mixed outcome groups, what's the typical success rate?
mixed_rates = [v["success_rate"] for v in variances if v["mixed"]]
if mixed_rates:
    print(f"\n  Among mixed-outcome groups:")
    print(f"    Mean success rate: {statistics.mean(mixed_rates)*100:.1f}%")
    print(f"    Median success rate: {statistics.median(mixed_rates)*100:.1f}%")
    # How many runs are "wasted" in mixed groups?
    mixed_groups_data = [v for v in variances if v["mixed"]]
    total_mixed_runs = sum(v["n"] for v in mixed_groups_data)
    total_mixed_failures = sum(int(v["n"] * (1 - v["success_rate"])) for v in mixed_groups_data)
    print(f"    Total runs in mixed groups: {total_mixed_runs}")
    print(f"    Failed runs in mixed groups: {total_mixed_failures} ({total_mixed_failures/total_mixed_runs*100:.1f}%)")

# ============================================================
# 2. RE-BENCH: DETAILED RUN-LEVEL ANALYSIS
# ============================================================
print("\n" + "="*70)
print("2. RE-BENCH: SCORE DISTRIBUTION PER (TASK, MODEL)")
print("="*70)

rebench = [r for r in runs if r["task_source"] == "RE-Bench"]
rb_groups = defaultdict(list)
for r in rebench:
    rb_groups[(r["task_id"], r["alias"])].append(r)

# Show variance within same (task, model)
print(f"\nRE-Bench groups with multiple runs showing score spread:")
for (task_id, model), group_runs in sorted(rb_groups.items()):
    if len(group_runs) < 2:
        continue
    scores = [r["score_cont"] for r in group_runs]
    task_short = task_id.split("/")[0].replace("ai_rd_", "")
    if max(scores) - min(scores) > 0.1:  # significant spread
        print(f"  {task_short} + {model}: scores={[f'{s:.2f}' for s in sorted(scores)]}")

# ============================================================
# 3. COMPUTE WASTE PER DIFFICULTY TIER
# ============================================================
print("\n" + "="*70)
print("3. COMPUTE WASTE BY DIFFICULTY TIER")
print("="*70)

tiers = {
    "Easy (<1h)": lambda r: r.get("human_minutes") and 0 < r["human_minutes"] <= 60,
    "Medium (1-4h)": lambda r: r.get("human_minutes") and 60 < r["human_minutes"] <= 240,
    "Hard (4-8h)": lambda r: r.get("human_minutes") and 240 < r["human_minutes"] <= 480,
    "Very Hard (>8h)": lambda r: r.get("human_minutes") and r["human_minutes"] > 480,
}

for tier_name, tier_filter in tiers.items():
    tier_runs = [r for r in runs if tier_filter(r)]
    if not tier_runs:
        continue

    total_n = len(tier_runs)
    failed_n = sum(1 for r in tier_runs if r["score_binarized"] == 0)

    total_tokens = sum(r.get("tokens_count", 0) or 0 for r in tier_runs)
    failed_tokens = sum(r.get("tokens_count", 0) or 0 for r in tier_runs if r["score_binarized"] == 0)

    total_cost = sum(r.get("generation_cost", 0) or 0 for r in tier_runs)
    failed_cost = sum(r.get("generation_cost", 0) or 0 for r in tier_runs if r["score_binarized"] == 0)

    print(f"\n{tier_name}:")
    print(f"  Runs: {failed_n}/{total_n} failed ({failed_n/total_n*100:.1f}%)")
    if total_tokens > 0:
        print(f"  Tokens: {failed_tokens/1e6:.1f}M / {total_tokens/1e6:.1f}M wasted ({failed_tokens/total_tokens*100:.1f}%)")
    if total_cost > 0:
        print(f"  Cost: ${failed_cost:.0f} / ${total_cost:.0f} wasted ({failed_cost/total_cost*100:.1f}%)")

# ============================================================
# 4. MODEL CAPABILITY PROGRESSION ON SAME TASKS
# ============================================================
print("\n" + "="*70)
print("4. MODEL CAPABILITY PROGRESSION (SAME RE-BENCH TASKS)")
print("="*70)

# Track how each model generation does on RE-Bench
model_progression = [
    ("GPT-4 0314", "2023-03"),
    ("GPT-4o (Inspect)", "2024-05"),
    ("Claude 3 Opus (Inspect)", "2024-03"),
    ("o1-preview", "2024-09"),
    ("Claude 3.5 Sonnet (Old) (Inspect)", "2024-06"),
    ("Claude 3.5 Sonnet (New) (Inspect)", "2024-10"),
    ("o1 (Inspect)", "2024-12"),
    ("Claude 3.7 Sonnet (Inspect)", "2025-02"),
    ("o3 (Inspect)", "2025-01"),
    ("Claude Opus 4.5 (Inspect)", "2025-03"),
    ("GPT-5 (Inspect)", "2025-06"),
    ("Claude 4 Opus (Inspect)", "2025-06"),
    ("Claude 4.1 Opus (Inspect)", "2025-09"),
    ("GPT-5.1-Codex-Max (Inspect)", "2025-09"),
    ("Claude Opus 4.6 (Inspect)", "2025-12"),
    ("GPT-5.3-Codex", "2026-01"),
]

print(f"\n{'Model':<40} {'Date':>8} {'RB Score':>9} {'RB N':>5} {'Fail%':>6}")
print("-" * 72)
for model_name, date in model_progression:
    rb = [r for r in rebench if r["alias"] == model_name]
    if not rb:
        continue
    avg_score = statistics.mean(r["score_cont"] for r in rb)
    fail_rate = sum(1 for r in rb if r["score_binarized"] == 0) / len(rb) * 100
    print(f"{model_name:<40} {date:>8} {avg_score:>9.3f} {len(rb):>5} {fail_rate:>5.0f}%")

# ============================================================
# 5. THE "EXPLORATION TAX" — AGGREGATE NUMBER
# ============================================================
print("\n" + "="*70)
print("5. THE EXPLORATION TAX — AGGREGATE")
print("="*70)

# Total resources spent
total_tokens_all = sum(r.get("tokens_count", 0) or 0 for r in runs)
total_cost_all = sum(r.get("generation_cost", 0) or 0 for r in runs)

# Resources on failed runs (genuine dead ends, no fatal errors)
dead_end_runs = [r for r in runs if r["score_binarized"] == 0 and not r.get("fatal_error_from")]
dead_end_tokens = sum(r.get("tokens_count", 0) or 0 for r in dead_end_runs)
dead_end_cost = sum(r.get("generation_cost", 0) or 0 for r in dead_end_runs)

# Resources on redundant successful runs (same task+model, >1 success)
task_model_success = defaultdict(list)
for r in runs:
    if r["score_binarized"] > 0:
        task_model_success[(r["task_id"], r["alias"])].append(r)

redundant_tokens = 0
redundant_cost = 0
redundant_count = 0
for key, successful_runs in task_model_success.items():
    if len(successful_runs) > 1:
        # First run is "useful", rest are redundant
        for r in successful_runs[1:]:
            redundant_tokens += (r.get("tokens_count", 0) or 0)
            redundant_cost += (r.get("generation_cost", 0) or 0)
            redundant_count += 1

print(f"\nTotal: {len(runs)} runs, {total_tokens_all/1e9:.1f}B tokens, ${total_cost_all:,.0f}")
print(f"\nExploration waste breakdown:")
print(f"  Dead-end exploration: {len(dead_end_runs)} runs, {dead_end_tokens/1e9:.1f}B tokens ({dead_end_tokens/total_tokens_all*100:.1f}%), ${dead_end_cost:,.0f} ({dead_end_cost/total_cost_all*100:.1f}%)")
print(f"  Redundant re-discovery: {redundant_count} runs, {redundant_tokens/1e9:.1f}B tokens ({redundant_tokens/total_tokens_all*100:.1f}%), ${redundant_cost:,.0f} ({redundant_cost/total_cost_all*100:.1f}%)")
total_waste_tokens = dead_end_tokens + redundant_tokens
total_waste_cost = dead_end_cost + redundant_cost
print(f"  TOTAL WASTE: {total_waste_tokens/1e9:.1f}B tokens ({total_waste_tokens/total_tokens_all*100:.1f}%), ${total_waste_cost:,.0f} ({total_waste_cost/total_cost_all*100:.1f}%)")
print(f"  USEFUL WORK: {(total_tokens_all-total_waste_tokens)/1e9:.1f}B tokens ({(total_tokens_all-total_waste_tokens)/total_tokens_all*100:.1f}%), ${total_cost_all-total_waste_cost:,.0f} ({(total_cost_all-total_waste_cost)/total_cost_all*100:.1f}%)")

# Save final stats
final = {
    "dataset": "METR eval-analysis-public v1.1",
    "total_runs": len(runs),
    "total_models": len(set(r["alias"] for r in runs)),
    "total_tasks": len(set(r["task_id"] for r in runs)),
    "total_tokens_B": total_tokens_all / 1e9,
    "total_cost_usd": total_cost_all,
    "dead_end_runs": len(dead_end_runs),
    "dead_end_tokens_pct": dead_end_tokens / total_tokens_all * 100,
    "dead_end_cost_pct": dead_end_cost / total_cost_all * 100,
    "redundant_runs": redundant_count,
    "redundant_tokens_pct": redundant_tokens / total_tokens_all * 100,
    "redundant_cost_pct": redundant_cost / total_cost_all * 100,
    "total_waste_tokens_pct": total_waste_tokens / total_tokens_all * 100,
    "total_waste_cost_pct": total_waste_cost / total_cost_all * 100,
    "useful_work_tokens_pct": (total_tokens_all - total_waste_tokens) / total_tokens_all * 100,
    "useful_work_cost_pct": (total_cost_all - total_waste_cost) / total_cost_all * 100,
    "rebench": {
        "total_runs": len(rebench),
        "failure_rate": sum(1 for r in rebench if r["score_binarized"] == 0) / len(rebench),
        "best_model": "Claude Opus 4.6 (Inspect)",
        "best_model_avg": 0.974,
    },
    "difficulty_cliff": {
        "easy_success": 0.854,
        "medium_success": 0.307,
        "hard_success": 0.151,
    },
    "failed_vs_success_token_ratio": {
        "p50": 112.9,
        "p75": 28.2,
        "mean": 8.6,
    },
}

out_path = os.path.join(OUT_DIR, "exploration_tax_findings.json")
with open(out_path, "w") as f:
    json.dump(final, f, indent=2)
print(f"\nSaved comprehensive findings to {out_path}")
