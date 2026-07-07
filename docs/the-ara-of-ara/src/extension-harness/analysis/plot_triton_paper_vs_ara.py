"""triton_cumsum extension: paper vs ARA across Sonnet 4.5 and 4.6.

Polished publication figure with two side-by-side panels:
  - left:  score vs wall-clock minutes
  - right: score vs cumulative cost (USD, Sonnet list pricing)
Each panel overlays four trajectories: paper-4.5, ARA-4.5, paper-4.6, ARA-4.6.

Score = log(solution_time_ms); lower is better. Reference (~0.643) is the
per-hardware H100 baseline measured by the harness across all four runs;
the original RE-Bench reference of 0.47 was reported on different silicon.

Source runs:
  paper-4.5 = triton_cumsum_paper_seed8_job7982788   (best  0.628, n=1064)
  ARA-4.5   = triton_cumsum_ara_seed8_job7982791     (best  0.272, n=1105)
  paper-4.6 = triton_cumsum_paper_seed0_job6595591   (best -0.744, n=93)
  ARA-4.6   = triton_cumsum_ara_seed0_job6595593     (best -0.612, n=125)

Score and cost extraction reads only the canonical RE-Bench triton scorer
JSON ("score": X | "solution_time_ms": Y inside a tool-result message tagged
shape_dtype_match), so it cannot be polluted by the agent's own commentary,
training-script logs, or autotune output.

Saves PDF (vector, for LaTeX) + PNG (300 dpi, preview) to paper/shared/figures/extension/.
"""
from __future__ import annotations

import json
import pathlib
import re

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
RUNS = [
    # (label, run_dir, color, linestyle, marker, zorder)
    ("paper (Sonnet 4.5)", "triton_cumsum_paper_seed8_job7982788",
     "#56B4E9", "--", "o", 3),
    ("ARA (Sonnet 4.5)",   "triton_cumsum_ara_seed8_job7982791",
     "#E69F00", "--", "s", 3),
    ("paper (Sonnet 4.6)", "triton_cumsum_paper_seed0_job6595591",
     "#0072B2", "-",  "o", 4),
    ("ARA (Sonnet 4.6)",   "triton_cumsum_ara_seed0_job6595593",
     "#D55E00", "-",  "s", 4),
]

# Sonnet 4.5/4.6 list pricing per million tokens (Apr 2026)
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

# Reads the canonical RE-Bench triton scorer output:
#   {"score": X, "message": {"shape_dtype_match": true, ...,
#    "solution_time_ms": Y}}
# Anchored on solution_time_ms so the regex cannot match agent commentary that
# happens to mention the word "score". Also tolerates negative scores (post-4.6
# kernels routinely log ms) and scientific notation.
CANON_RE = re.compile(
    r'\\"score\\":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|NaN)'
    r'[^}]{0,500}'
    r'\\"solution_time_ms\\":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
)


def parse_run(run_dir: pathlib.Path):
    """Extract canonical score events and cumulative cost from a run.

    Returns:
        events: list of (t_min, score) for each canonical scoring attempt.
        cost_track: list of (t_min, usd) cumulative-cost samples, rescaled to
                    the SDK-reported metadata total when available.
    """
    events = []
    cost_track = []
    cost_acc = 0.0
    seen = set()  # dedupe by (rounded t, rounded score)

    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return events, cost_track

    for line in open(trace):
        try:
            d = json.loads(line)
        except Exception:
            continue
        t_s = d.get("wall_clock_s")

        if d.get("type") == "assistant":
            u = d.get("usage", {}) or {}
            cost_acc += (
                u.get("input_tokens", 0)                 * PRICE["in"]
                + u.get("cache_creation_input_tokens", 0) * PRICE["cache_w"]
                + u.get("cache_read_input_tokens", 0)     * PRICE["cache_r"]
                + u.get("output_tokens", 0)               * PRICE["out"]
            ) / 1e6
            if t_s is not None:
                cost_track.append((t_s / 60.0, cost_acc))
            continue

        if d.get("type") != "user" or "shape_dtype_match" not in line:
            continue
        t_min = (t_s or 0) / 60.0
        for m in CANON_RE.finditer(line):
            sv_raw = m.group(1)
            if sv_raw == "NaN":
                continue
            try:
                sv = float(sv_raw)
            except ValueError:
                continue
            key = (round(t_min, 2), round(sv, 4))
            if key in seen:
                continue
            seen.add(key)
            events.append((t_min, sv))

    events.sort()

    # Rescale per-message cost track to match the SDK's authoritative total
    # (metadata.json:agent.total_cost_usd is what the Anthropic billing portal
    # reports; per-message accumulation is approximate due to retry/cache nuances).
    meta_path = run_dir / "metadata.json"
    if meta_path.exists() and cost_acc > 0:
        try:
            meta = json.loads(meta_path.read_text())
            final_cost = meta.get("agent", {}).get("total_cost_usd")
            if final_cost:
                scale = final_cost / cost_acc
                cost_track = [(t, c * scale) for (t, c) in cost_track]
        except Exception:
            pass

    return events, cost_track


def cost_at(track, t_min):
    """Linear-interp cumulative cost at minute t_min from a (t, cost) track."""
    if not track:
        return 0.0
    c = track[0][1]
    for ti, ci in track:
        if ti <= t_min:
            c = ci
        else:
            break
    return c


def running_min(values):
    out, b = [], float("inf")
    for v in values:
        b = min(b, v)
        out.append(b)
    return out


# ---------------------------------------------------------------------------
# Publication styling
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "legend.fontsize": 7.5,
    "legend.frameon": True,
    "legend.framealpha": 0.92,
    "legend.edgecolor": "#CCCCCC",
    "legend.borderpad": 0.4,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "grid.linestyle": "-",
    "lines.linewidth": 1.6,
    "lines.markersize": 4.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

REFERENCE_HW    = 0.643   # per-hardware H100 baseline (mean across runs)
REFERENCE_ORIG  = 0.47    # original RE-Bench reference (different HW)


def main():
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)

    # Print summary as we go (sanity check)
    print(f"{'run':24s} {'n':>5s} {'first':>8s} {'best':>8s} "
          f"{'t_max(min)':>11s} {'cost($)':>9s}")

    for label, run_name, color, ls, marker, zorder in RUNS:
        run_dir = RUN_ROOT / run_name
        events, costs = parse_run(run_dir)
        if not events:
            print(f"{label:24s}  no events found in {run_name}")
            continue

        ts = np.array([t for t, _ in events])
        sv = np.array([s for _, s in events])
        cs = np.array([cost_at(costs, t) for t in ts])
        best = np.array(running_min(sv.tolist()))

        # Raw scoring scatter (recede into background, alpha tuned to density;
        # floor at 0.12 so the 4.5 arms' ~1k-attempt noise bands stay visible).
        alpha = max(0.12, min(0.40, 50.0 / len(sv)))
        ax_t.scatter(ts, sv, s=7, color=color, alpha=alpha, marker=".",
                     edgecolor="none", zorder=zorder - 1, rasterized=True)
        ax_c.scatter(cs, sv, s=7, color=color, alpha=alpha, marker=".",
                     edgecolor="none", zorder=zorder - 1, rasterized=True)
        print(f"  scatter: {label} -> {len(sv)} dots @ alpha={alpha:.3f}")

        # Best-so-far envelope
        ax_t.plot(ts, best, ls, color=color, lw=1.7, zorder=zorder, label=label)
        ax_c.plot(cs, best, ls, color=color, lw=1.7, zorder=zorder)

        # Best-attempt star
        i_best = int(np.argmin(sv))
        ax_t.scatter([ts[i_best]], [sv[i_best]], s=85, color=color,
                     marker="*", edgecolor="black", linewidth=0.5,
                     zorder=zorder + 1)
        ax_c.scatter([cs[i_best]], [sv[i_best]], s=85, color=color,
                     marker="*", edgecolor="black", linewidth=0.5,
                     zorder=zorder + 1)

        print(f"{label:24s} {len(events):>5d} {sv[0]:>8.3f} {min(sv):>8.3f} "
              f"{ts[-1]:>11.1f} {cs[-1]:>9.2f}  best@(t={ts[i_best]:.0f}min, "
              f"cost=${cs[i_best]:.2f})")

    # Reference lines + axis bounds matched to harness caps (8 h, $50)
    for ax in (ax_t, ax_c):
        ax.axhline(REFERENCE_HW, color="#555555", ls=":", lw=1, zorder=1)
        ax.axhline(REFERENCE_ORIG, color="#888888", ls=":", lw=0.8, zorder=1)
        ax.set_ylabel(r"score $= \log(\mathrm{time}_\mathrm{ms})$" "\n(lower is better)")
        ax.grid(alpha=0.18)
        # Tight y-range: post-best regressions don't squash the trajectories
        ax.set_ylim(-0.95, 0.85)

    # x-bounds: hard 8 h SLURM cap on time; cost extends beyond the $50 SDK
    # cap to capture ARA-4.5's overshoot (SDK enforcement is approximate at
    # message boundaries; the cap is shown as a vertical reference).
    ax_t.set_xlim(0, 480)
    ax_c.set_xlim(0, 90)
    ax_c.axvline(50, color="#555555", ls=":", lw=0.8, zorder=1)
    ax_c.text(50, 0.80, " \\$50 budget cap", fontsize=6.5, color="#555555",
              ha="left", va="top")

    # Inline reference labels at the left edge of each panel
    for ax in (ax_t, ax_c):
        x0, x1 = ax.get_xlim()
        ax.text(x0 + 0.02 * (x1 - x0), REFERENCE_HW + 0.025,
                "per-hardware baseline (0.64)",
                fontsize=6.5, color="#555555", ha="left", va="bottom")
        ax.text(x0 + 0.02 * (x1 - x0), REFERENCE_ORIG + 0.025,
                "RE-Bench reference (0.47)",
                fontsize=6.5, color="#888888", ha="left", va="bottom")

    ax_t.set_xlabel("wall-clock minutes (8 h cap)")
    ax_c.set_xlabel("cumulative API cost (USD)")
    ax_t.set_title("Score vs. time")
    ax_c.set_title("Score vs. cost")

    # Single shared legend, anchored above panels (does not occlude data)
    handles, labels = ax_t.get_legend_handles_labels()
    leg = fig.legend(handles, labels, loc="upper center",
                     bbox_to_anchor=(0.5, 1.005), ncol=4, handlelength=2.4,
                     columnspacing=1.5, borderaxespad=0.0)
    leg.set_zorder(10)

    fig.suptitle(
        "triton_cumsum: paper vs. ARA across Sonnet 4.5 and 4.6",
        fontsize=10.5, y=1.10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/paper/shared/figures/extension"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "triton_paper_vs_ara.pdf"
    png_path = out_dir / "triton_paper_vs_ara.png"
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    print(f"\nsaved {pdf_path}\nsaved {png_path}")


if __name__ == "__main__":
    main()
