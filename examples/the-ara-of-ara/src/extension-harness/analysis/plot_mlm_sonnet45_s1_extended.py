"""MLM paper s1 (original + resume) vs ara s1 (sonnet-4-5): score trajectory.

Extends plot_mlm_sonnet45_s1.py by stitching paper s1's resume run
(job 7070627) onto the tail of the original paper s1 run (6858168).
The resume continues from the original session's workdir, so for a
fair side-by-side view we append its wall-clock minutes and cumulative
cost to the end of the original.

MLM score = log(val_loss - 1.5), lower is better.
"""
import json
import pathlib
import re

import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
PAPER_ORIG = RUN_ROOT / "restricted_mlm_paper_seed1_job6858168"
PAPER_RESUME = RUN_ROOT / "restricted_mlm_paper_seed1_resume_job7070627"
ARA = RUN_ROOT / "restricted_mlm_ara_seed1_job6786400"

PAPER_COLOR = "#1f77b4"
ARA_COLOR = "#ff7f0e"
RESUME_MARKER_COLOR = "#555555"
REFERENCE_SCORE = 1.847

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}
SCORE_RE = re.compile(r'[\'"]score[\'"]:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)')


def parse_run(run_dir: pathlib.Path):
    scores, cost_track, cost_acc = [], [], 0.0
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return scores, cost_track, cost_acc
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
                if -2 < v < 3 and t is not None:
                    scores.append((t, v))
                    break

    # Rescale cost to final metadata cost if available
    meta_path = run_dir / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            final_cost = meta.get("agent", {}).get("total_cost_usd")
            if final_cost and cost_acc > 0:
                scale = final_cost / cost_acc
                cost_track = [(t, c * scale) for (t, c) in cost_track]
                cost_acc = final_cost
        except Exception:
            pass
    return scores, cost_track, cost_acc


def stitch(orig, resume):
    """Append resume's (t, cost) trajectory onto the end of orig.
    Returns (scores_merged, costs_merged, split_min, split_usd)."""
    o_scores, o_costs, o_final_cost = orig
    r_scores, r_costs, _ = resume

    # Time offset: take the max wall-clock-s seen in orig (from scores or costs)
    o_t_end = 0.0
    if o_scores: o_t_end = max(o_t_end, o_scores[-1][0])
    if o_costs:  o_t_end = max(o_t_end, o_costs[-1][0])

    merged_scores = list(o_scores) + [(t + o_t_end, v) for (t, v) in r_scores]
    merged_costs = list(o_costs) + [(t + o_t_end, c + o_final_cost) for (t, c) in r_costs]
    return merged_scores, merged_costs, o_t_end / 60.0, o_final_cost


def running_min(vals):
    out, best = [], float("inf")
    for v in vals:
        best = min(best, v)
        out.append(best)
    return out


def main():
    orig = parse_run(PAPER_ORIG)
    resume = parse_run(PAPER_RESUME)
    ara_scores, ara_costs, _ = parse_run(ARA)

    paper_scores, paper_costs, split_min, split_usd = stitch(orig, resume)

    print(f"paper s1 original : n={len(orig[0]):3d} first={orig[0][0][1] if orig[0] else float('nan'):.3f} "
          f"best={min(s[1] for s in orig[0]) if orig[0] else float('nan'):.3f} cost=${orig[2]:.2f}")
    print(f"paper s1 resume   : n={len(resume[0]):3d} first={resume[0][0][1] if resume[0] else float('nan'):.3f} "
          f"best={min(s[1] for s in resume[0]) if resume[0] else float('nan'):.3f} cost=${resume[2]:.2f}")
    print(f"paper s1 combined : n={len(paper_scores):3d} best={min(s[1] for s in paper_scores):.3f} "
          f"split at {split_min:.1f} min / ${split_usd:.2f}")
    print(f"ara   s1          : n={len(ara_scores):3d} best={min(s[1] for s in ara_scores):.3f}")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    ax_t, ax_c = axes

    # --- paper (stitched) ---
    p_ts = [s[0] / 60.0 for s in paper_scores]
    p_sv = [s[1] for s in paper_scores]
    p_cs, ci = [], 0
    for (t_s, _) in paper_scores:
        while ci + 1 < len(paper_costs) and paper_costs[ci + 1][0] <= t_s:
            ci += 1
        p_cs.append(paper_costs[ci][1] if paper_costs else 0.0)
    p_best = running_min(p_sv)

    ax_t.scatter(p_ts, p_sv, s=12, color=PAPER_COLOR, alpha=0.35,
                 label=f"paper s1 orig+resume attempts (n={len(p_sv)})")
    ax_t.plot(p_ts, p_best, "-", color=PAPER_COLOR, lw=2)
    ax_c.scatter(p_cs, p_sv, s=12, color=PAPER_COLOR, alpha=0.35)
    ax_c.plot(p_cs, p_best, "-", color=PAPER_COLOR, lw=2,
              label="paper s1 orig+resume best-so-far")

    # split marker showing where original ended / resume began
    ax_t.axvline(split_min, color=RESUME_MARKER_COLOR, ls=":", lw=1,
                 alpha=0.6, label=f"resume boundary ({split_min:.0f} min)")
    ax_c.axvline(split_usd, color=RESUME_MARKER_COLOR, ls=":", lw=1,
                 alpha=0.6, label=f"resume boundary (${split_usd:.0f})")

    # --- ara ---
    a_ts = [s[0] / 60.0 for s in ara_scores]
    a_sv = [s[1] for s in ara_scores]
    a_cs, ci = [], 0
    for (t_s, _) in ara_scores:
        while ci + 1 < len(ara_costs) and ara_costs[ci + 1][0] <= t_s:
            ci += 1
        a_cs.append(ara_costs[ci][1] if ara_costs else 0.0)
    a_best = running_min(a_sv)

    ax_t.scatter(a_ts, a_sv, s=12, color=ARA_COLOR, alpha=0.35,
                 label=f"ara s1 attempts (n={len(a_sv)})")
    ax_t.plot(a_ts, a_best, "-", color=ARA_COLOR, lw=2)
    ax_c.scatter(a_cs, a_sv, s=12, color=ARA_COLOR, alpha=0.35)
    ax_c.plot(a_cs, a_best, "-", color=ARA_COLOR, lw=2,
              label="ara s1 best-so-far")

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
        "restricted_mlm — sonnet-4-5, paper s1 (original+resume) vs ara s1",
        fontsize=11,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "mlm_45_paper_s1_extended_vs_ara_s1.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
