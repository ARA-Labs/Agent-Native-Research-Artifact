"""Live trajectory comparison: triton_cumsum, sonnet-4-5, paper s0 vs ara s2.

Mirrors the style of plots/triton_4.6_live.png:
  - left panel:  score over time (minutes) — attempts as dots, best-so-far as line
  - right panel: best score vs cumulative cost (USD)
  - dashed red reference line at 0.65 (user-specified per-hardware baseline)

Handles live / unfinished runs gracefully (no metadata.json yet). Without a
final total_cost_usd from metadata, costs are the raw token-based estimate
(no post-hoc rescaling).
"""
import json
import pathlib
import re

import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
RUNS = {
    "paper s0 (6754693)": RUN_ROOT / "triton_cumsum_paper_seed0_job6754693",
    "ara s2 (6848032)":   RUN_ROOT / "triton_cumsum_ara_seed2_job6848032",
}
COLORS = {"paper s0 (6754693)": "#1f77b4", "ara s2 (6848032)": "#ff7f0e"}
REFERENCE_SCORE = 0.65

# sonnet-4-5 public pricing (USD per MTok) — identical to 4-6
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}
SCORE_RE = re.compile(r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?)')


def parse_run(run_dir: pathlib.Path):
    scores, cost_track, cost_acc = [], [], 0.0
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return scores, cost_track
    for line in open(trace):
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

    meta_path = run_dir / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            final_cost = meta.get("agent", {}).get("total_cost_usd")
            if final_cost and cost_acc > 0:
                scale = final_cost / cost_acc
                cost_track = [(t, c * scale) for (t, c) in cost_track]
        except Exception:
            pass
    return scores, cost_track


def running_min(vals):
    out, best = [], float("inf")
    for v in vals:
        best = min(best, v)
        out.append(best)
    return out


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    ax_t, ax_c = axes

    print(f"{'run':30s} {'n':>5s} {'first':>8s} {'best':>8s} "
          f"{'final_min':>10s} {'cost_$':>8s}")
    for label, run_dir in RUNS.items():
        scores, costs = parse_run(run_dir)
        color = COLORS[label]
        ts = [s[0] / 60.0 for s in scores]
        sv = [s[1] for s in scores]
        cs, ci = [], 0
        for (t_s, _) in scores:
            while ci + 1 < len(costs) and costs[ci + 1][0] <= t_s:
                ci += 1
            cs.append(costs[ci][1] if costs else 0.0)
        best_curve = running_min(sv) if sv else []

        n = len(sv)
        ax_t.scatter(ts, sv, s=12, color=color, alpha=0.35,
                     label=f"{label} attempts (n={n})")
        if sv:
            ax_t.plot(ts, best_curve, "-", color=color, lw=2)
            ax_c.scatter(cs, sv, s=12, color=color, alpha=0.35)
            ax_c.plot(cs, best_curve, "-", color=color, lw=2,
                      label=f"{label} best-so-far")

        print(f"{label:30s} {n:>5d} "
              f"{sv[0] if sv else float('nan'):>8.4f} "
              f"{min(sv) if sv else float('nan'):>8.4f} "
              f"{ts[-1] if ts else 0:>10.2f} "
              f"{cs[-1] if cs else 0:>8.2f}")

    for ax in axes:
        ax.axhline(REFERENCE_SCORE, color="red", ls="--", lw=1,
                   label=f"reference ({REFERENCE_SCORE:.2f})")
        ax.axhline(0, color="grey", ls=":", lw=0.7)
        ax.set_ylabel("score = log(solution_ms / torch_ms) — lower is better")
        ax.grid(alpha=0.3)

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Best score vs cost")
    ax_t.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax_c.legend(loc="upper right", fontsize=8, framealpha=0.9)

    fig.suptitle(
        "triton_cumsum — sonnet-4-5, paper s0 vs ara s2 (live)",
        fontsize=11,
    )
    fig.tight_layout()

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots"
    )
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "triton_45_live_paper_s0_ara_s2.png"
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
