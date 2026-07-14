"""MLM paper s0 vs ara s0 (sonnet-4-6): score trajectory over time + cost.

Differs from plot_mlm_sonnet45_s1.py in its data source: the 4-6 runs
have many truncated tool_result previews in trace.jsonl (TaskOutput
preview cut at ~2 KB), so reliable score numbers live in the task-output
files under
  /n/home04/zechenzhang/.claude/tmp/claude-*/<workdir>/<session>/tasks/*.output

We parse those directly, using file mtime as the completion timestamp.
Cost is still derived from trace.jsonl assistant-message usage, then
rescaled to the final metadata cost (if the run has metadata.json).

MLM score = log(val_loss - 1.5), lower is better. Baseline ≈ 1.847.
"""
import json
import pathlib
import re

import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
TMP_ROOT = pathlib.Path("/n/home04/zechenzhang/.claude/tmp/claude-62233")
REFERENCE_SCORE = 1.847

# sonnet-4-6 pricing (same rates as 4-5)
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}
RE_SCORE = re.compile(
    r'\{"score":\s*(-?\d+(?:\.\d+)?),\s*"loss":\s*(-?\d+(?:\.\d+)?),\s*"compliant":'
)

RUNS = {
    "paper s0 (7079164)": {
        "run_dir": RUN_ROOT / "restricted_mlm_paper_seed0_job7079164",
        "tmp_root": TMP_ROOT / (
            "-n-netscratch-sompolinsky-lab-Everyone-zechenzhang-"
            "ara-project-extension-runs-restricted-mlm-paper-seed0-"
            "job7079164-workdir"
        ),
        "color": "#1f77b4",
        "end_label": "TIMEOUT 8h",
    },
    "ara s0 (7079165)": {
        "run_dir": RUN_ROOT / "restricted_mlm_ara_seed0_job7079165",
        "tmp_root": TMP_ROOT / (
            "-n-netscratch-sompolinsky-lab-Everyone-zechenzhang-"
            "ara-project-extension-runs-restricted-mlm-ara-seed0-"
            "job7079165-workdir"
        ),
        "color": "#ff7f0e",
        "end_label": "JSON-buffer crash @ ~4h38m",
    },
}


def find_tasks_dir(tmp_root: pathlib.Path) -> pathlib.Path | None:
    if not tmp_root.exists():
        return None
    for sub in tmp_root.iterdir():
        if (sub / "tasks").is_dir():
            return sub / "tasks"
    return None


def scores_from_tasks(tasks_dir: pathlib.Path):
    """Return [(mtime_offset_s, score, loss), ...] one per task-output file,
    sorted by mtime. First match per file wins."""
    if tasks_dir is None:
        return []
    hits = []
    for f in tasks_dir.glob("*.output"):
        try:
            text = f.read_text(errors="ignore")
        except Exception:
            continue
        m = RE_SCORE.search(text)
        if not m:
            continue
        hits.append((f.stat().st_mtime, float(m.group(1)), float(m.group(2))))
    if not hits:
        return []
    hits.sort()
    t0 = hits[0][0]
    return [(mt - t0, s, loss) for (mt, s, loss) in hits]


def cost_track_from_trace(run_dir: pathlib.Path):
    """Return [(wall_s, cumulative_usd)] and final cost estimate."""
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return [], 0.0
    cost_track, cost_acc = [], 0.0
    for line in open(trace):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant":
            continue
        u = d.get("usage", {}) or {}
        cost_acc += (
            u.get("input_tokens", 0) * PRICE["in"] / 1e6
            + u.get("cache_creation_input_tokens", 0) * PRICE["cache_w"] / 1e6
            + u.get("cache_read_input_tokens", 0) * PRICE["cache_r"] / 1e6
            + u.get("output_tokens", 0) * PRICE["out"] / 1e6
        )
        t = d.get("wall_clock_s")
        if t is not None:
            cost_track.append((t, cost_acc))

    meta = run_dir / "metadata.json"
    if meta.exists():
        try:
            m = json.loads(meta.read_text())
            final_cost = m.get("agent", {}).get("total_cost_usd")
            if final_cost and cost_acc > 0:
                scale = final_cost / cost_acc
                cost_track = [(t, c * scale) for (t, c) in cost_track]
                cost_acc = final_cost
        except Exception:
            pass
    return cost_track, cost_acc


def pair_scores_with_cost(scores, cost_track):
    """For each (t, score), return the most recent cumulative cost at that t."""
    out = []
    ci = 0
    for (t_s, _s, _l) in scores:
        while ci + 1 < len(cost_track) and cost_track[ci + 1][0] <= t_s:
            ci += 1
        c = cost_track[ci][1] if cost_track else 0.0
        out.append(c)
    return out


def running_min(vals):
    out, best = [], float("inf")
    for v in vals:
        best = min(best, v)
        out.append(best)
    return out


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    ax_t, ax_c = axes

    print(f"{'run':28s} {'n':>4s} {'first':>8s} {'best':>8s} "
          f"{'final_min':>10s} {'cost_$':>8s}  end")
    for label, info in RUNS.items():
        tasks_dir = find_tasks_dir(info["tmp_root"])
        scores = scores_from_tasks(tasks_dir)
        cost_track, final_cost = cost_track_from_trace(info["run_dir"])
        pair_costs = pair_scores_with_cost(scores, cost_track)
        color = info["color"]

        ts = [s[0] / 60.0 for s in scores]
        sv = [s[1] for s in scores]
        best_curve = running_min(sv)

        n = len(sv)
        ax_t.scatter(ts, sv, s=16, color=color, alpha=0.40,
                     label=f"{label} attempts (n={n})")
        if sv:
            ax_t.plot(ts, best_curve, "-", color=color, lw=2)
            ax_c.scatter(pair_costs, sv, s=16, color=color, alpha=0.40)
            ax_c.plot(pair_costs, best_curve, "-", color=color, lw=2,
                      label=f"{label} best-so-far")

        print(f"{label:28s} {n:>4d} "
              f"{sv[0] if sv else float('nan'):>8.4f} "
              f"{min(sv) if sv else float('nan'):>8.4f} "
              f"{ts[-1] if ts else 0:>10.1f} "
              f"{pair_costs[-1] if pair_costs else 0:>8.2f}  "
              f"{info['end_label']}")

    for ax in axes:
        ax.axhline(REFERENCE_SCORE, color="red", ls="--", lw=1,
                   label=f"baseline ({REFERENCE_SCORE:.2f})")
        ax.axhline(0, color="grey", ls=":", lw=0.7)
        ax.set_ylabel("score = log(val_loss - 1.5) — lower is better")
        ax.grid(alpha=0.3)
        ax.set_ylim(0.4, 2.1)  # clip out outliers (e.g. 7.35 from a corrupted model state)

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Best score vs cost")
    ax_t.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax_c.legend(loc="upper right", fontsize=8, framealpha=0.9)

    fig.suptitle(
        "restricted_mlm — sonnet-4-6, paper s0 vs ara s0 "
        "(scores parsed from task-output files; cost from trace.jsonl)",
        fontsize=11,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "mlm_46_paper_s0_ara_s0.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
