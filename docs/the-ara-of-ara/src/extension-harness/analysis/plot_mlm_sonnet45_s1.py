"""MLM paper s1 vs ara s1 (sonnet-4.5): score trajectory over time + cost.

Companion to plot_triton_sonnet45_s0_s2.py. MLM score = log(val_loss - 1.5),
lower is better; per-hardware baseline ~1.847 (starter is a weak MLP).

Score extraction is trickier than triton: MLM tool_results often got
truncated by the CLI (150KB tqdm bar > 2KB preview window), so we can see
the score in roughly ~half of the agent's score.sh attempts — we plot only
the visible ones. cost is estimated from assistant-message usage tokens.
"""
import json
import pathlib
import re

import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
RUNS = {
    "paper s1 (6858168)": RUN_ROOT / "restricted_mlm_paper_seed1_job6858168",
    "ara s1 (6786400)":   RUN_ROOT / "restricted_mlm_ara_seed1_job6786400",
}
COLORS = {"paper s1 (6858168)": "#1f77b4", "ara s1 (6786400)": "#ff7f0e"}
REFERENCE_SCORE = 1.847  # per-hardware baseline from baseline_score.json

# sonnet-4-5 pricing, USD per MTok
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}
# MLM score.sh output contains `{"score": ..., "loss": ...}`; pick up both
# quote styles since Python repr and JSON flavors both show up in the raw
# ToolResultBlock dump.
SCORE_RE = re.compile(r'[\'"]score[\'"]:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)')


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
                u.get("input_tokens", 0) * PRICE["in"] / 1e6
                + u.get("cache_creation_input_tokens", 0) * PRICE["cache_w"] / 1e6
                + u.get("cache_read_input_tokens", 0) * PRICE["cache_r"] / 1e6
                + u.get("output_tokens", 0) * PRICE["out"] / 1e6
            )
            if t is not None:
                cost_track.append((t, cost_acc))
        elif d.get("type") == "user":
            c = str(d.get("content", ""))
            if "tool_use_id" not in c:
                continue
            for m in SCORE_RE.finditer(c):
                try:
                    v = float(m.group(1))
                except ValueError:
                    continue
                # MLM scores live in ~[-2, 3]; drop obvious noise from
                # bigram/index numbers the agent grepped.
                if -2 < v < 3 and t is not None:
                    scores.append((t, v))
                    break  # one score per tool_result (avoid double-count)

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
              f"{ts[-1] if ts else 0:>10.1f} "
              f"{cs[-1] if cs else 0:>8.2f}")

    for ax in axes:
        ax.axhline(REFERENCE_SCORE, color="red", ls="--", lw=1,
                   label=f"baseline ({REFERENCE_SCORE:.2f})")
        ax.axhline(0, color="grey", ls=":", lw=0.7)
        ax.set_ylabel("score = log(val_loss - 1.5) — lower is better")
        ax.grid(alpha=0.3)

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Best score vs cost")
    ax_t.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax_c.legend(loc="upper right", fontsize=8, framealpha=0.9)

    fig.suptitle(
        "restricted_mlm — sonnet-4-5, paper s1 vs ara s1 "
        "(visible scores only; see docstring)",
        fontsize=11,
    )
    fig.tight_layout()

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots"
    )
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "mlm_45_paper_s1_ara_s1.png"
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
