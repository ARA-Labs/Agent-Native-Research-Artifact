"""Plot score trajectory vs wall-clock and cumulative cost for finished
triton_cumsum extension-harness runs (paper s8, ara s0; both sonnet-4-6).

For each run:
  - scatter all score.sh attempts as faint dots
  - overlay best-so-far (running min) as solid line
  - overlay per-hardware baseline score from metadata.json as dashed line

Saves to code/extension-harness/plots/.
"""
import json
import pathlib
import re

import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
RUNS = {
    "paper s8 (6772400)": RUN_ROOT / "triton_cumsum_paper_seed8_job6772400",
    "ara s0 (6776923)":   RUN_ROOT / "triton_cumsum_ara_seed0_job6776923",
}
COLORS = {"paper s8 (6772400)": "#d95f02", "ara s0 (6776923)": "#1b9e77"}

# sonnet-4-6 public pricing (USD per MTok)
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}
SCORE_RE = re.compile(r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?)')


def parse_run(run_dir: pathlib.Path):
    scores, cost_track, cost_acc = [], [], 0.0
    for line in open(run_dir / "trace.jsonl"):
        d = json.loads(line)
        t = d.get("wall_clock_s")
        if d.get("type") == "assistant":
            u = d.get("usage", {})
            cost_acc += (
                u.get("input_tokens", 0)                 * PRICE["in"]      / 1e6
                + u.get("cache_creation_input_tokens", 0) * PRICE["cache_w"] / 1e6
                + u.get("cache_read_input_tokens", 0)     * PRICE["cache_r"] / 1e6
                + u.get("output_tokens", 0)               * PRICE["out"]     / 1e6
            )
            if t is not None:
                cost_track.append((t, cost_acc))
        elif d.get("type") == "user":
            raw = json.dumps(d)
            if "shape_dtype_match" in raw:
                m = SCORE_RE.search(raw)
                if m and t is not None:
                    scores.append((t, float(m.group(1))))

    meta = json.loads((run_dir / "metadata.json").read_text())
    final_cost = meta.get("agent", {}).get("total_cost_usd")
    baseline = meta.get("baseline_score", {}).get("result", {}).get("score")
    if final_cost and cost_acc > 0:
        scale = final_cost / cost_acc
        cost_track = [(t, c * scale) for (t, c) in cost_track]
    return scores, cost_track, baseline


def running_min(vals):
    out, best = [], float("inf")
    for v in vals:
        best = min(best, v)
        out.append(best)
    return out


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    ax_t, ax_c = axes

    print(f"{'run':30s} {'n':>5s} {'first':>8s} {'baseline':>10s} {'best':>8s} "
          f"{'final_h':>8s} {'cost_$':>8s}")
    baselines = []
    for label, run_dir in RUNS.items():
        scores, costs, baseline = parse_run(run_dir)
        color = COLORS[label]
        ts = [s[0] / 3600.0 for s in scores]
        sv = [s[1] for s in scores]
        # interpolate cumulative cost at each score timestamp
        cs, ci = [], 0
        for (t_s, _) in scores:
            while ci + 1 < len(costs) and costs[ci + 1][0] <= t_s:
                ci += 1
            cs.append(costs[ci][1] if costs else 0.0)
        best_curve = running_min(sv)

        ax_t.scatter(ts, sv, s=10, color=color, alpha=0.3)
        ax_t.plot(ts, best_curve, "-", color=color, lw=2, label=f"{label} best-so-far")
        ax_c.scatter(cs, sv, s=10, color=color, alpha=0.3)
        ax_c.plot(cs, best_curve, "-", color=color, lw=2, label=f"{label} best-so-far")
        if baseline is not None:
            baselines.append((label, baseline, color))

        print(f"{label:30s} {len(sv):>5d} {sv[0] if sv else float('nan'):>8.4f} "
              f"{baseline:>10.4f} {min(sv) if sv else float('nan'):>8.4f} "
              f"{ts[-1] if ts else 0:>8.2f} {cs[-1] if cs else 0:>8.2f}")

    # Per-hardware baseline reference (both runs baseline on H100 kempner, near identical).
    avg_baseline = sum(b for _, b, _ in baselines) / len(baselines)
    for ax in axes:
        ax.axhline(avg_baseline, color="red", ls="--", lw=1,
                   label=f"per-hardware reference ({avg_baseline:.3f})")
        ax.axhline(0, color="grey", ls=":", lw=0.7)
        ax.set_ylabel("score = log(solution_ms / torch_ms) — lower is better")
        ax.grid(alpha=0.3)

    ax_t.set_xlabel("wall-clock hours")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score vs wall-clock")
    ax_c.set_title("Score vs cumulative cost")
    ax_t.legend(loc="upper right", fontsize=8, framealpha=0.9)

    fig.suptitle(
        "triton_cumsum best-so-far trajectory (paper s8 vs ara s0; sonnet-4-6)",
        fontsize=11,
    )
    fig.tight_layout()

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots"
    )
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "triton_best_so_far_paper_s8_ara_s0.png"
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
