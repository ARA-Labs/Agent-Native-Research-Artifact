"""4.6-only composite trajectory summary for §7.4 body.

Reads from all_scores.csv (produced by extract_all_scores.py) and plots
the five RE-Bench extension tasks on Sonnet 4.6 only. Layout is 2 rows
x 5 cols: top row is score-vs-time, bottom row is score-vs-cost, one
task per column. Y-axis is shared down each column (same task -> same
metric); only the top panel shows y-tick labels. All time panels share
0-500 min and all cost panels share 0-80 USD so readers can scan
across columns at a glance.

Sonnet 4.5 trajectories for triton and mlm are shown in the appendix
per-task figures, not here.

Output: paper/shared/figures/extension/summary_5tasks_46.{pdf,png}.
"""
from __future__ import annotations

import csv
import pathlib

import matplotlib.pyplot as plt
import numpy as np

CSV_PATH = pathlib.Path(__file__).parent / "all_scores.csv"
OUT_DIR = pathlib.Path(
    "/n/home04/zechenzhang/ara-project/paper/shared/figures/extension"
)

C_PAPER = "#0072B2"
C_ARA   = "#D55E00"

# All time panels share this x-axis; all cost panels share this one.
TIME_XLIM = 500
COST_XLIM = 80

# Per-task config: (task_key, short_title, lower_is_better, ylabel,
#                   ref_value, ylim, baseline_value)
# Direction arrow appended in the title (down for lower-is-better).
TASKS = [
    ("triton_cumsum",
     r"$\mathtt{triton\_cumsum}$" + r"  $\downarrow$", True,
     r"$\log(t_\mathrm{ms})$", 0.47, (-0.95, 1.10), None),
    ("rust_codecontests",
     r"$\mathtt{rust\_codecontests}$" + r"  $\uparrow$", False,
     r"$n_\mathrm{solved}/165$", 0.13, (0.05, 0.62), None),
    ("nanogpt_chat_rl",
     r"$\mathtt{nanogpt\_chat\_rl}$" + r"  $\uparrow$", False,
     r"win-rate", 0.85, (0.45, 1.02), None),
    ("fix_embedding",
     r"$\mathtt{fix\_embedding}$" + r"  $\downarrow$", True,
     r"$\log(\ell_\mathrm{val}{-}1.5)$", 0.26, (0.15, 2.40), None),
    # NOTE: the (task, special) handling below upgrades fix_embedding to
    # a piecewise y-axis (linear up to 0.45, compressed 0.45-2.4) so the
    # 2.20 baseline is visible as a starting point without crushing the
    # 0.20-0.40 tail where ARA and paper actually differ.
    ("restricted_mlm",
     r"$\mathtt{restricted\_mlm}$" + r"  $\downarrow$", True,
     r"$\log(\ell_\mathrm{val}{-}1.5)$", 1.13, (0.55, 2.05), None),
]

# Per-(task, arm) wall-clock cutoff (minutes): drop events past this. Used
# to align the body summary on a common 8-hour wall-clock window; appendix
# per-task figures retain the full parent+resume trajectories.
TIME_CUTOFF = {
    ("restricted_mlm", "ARA-4.6"): 480.0,
}

# Triton anchor only: the per-hardware baseline (0.644) is the same
# number every arm would get from running the unedited reference kernel,
# but neither 4.6 arm bothered scoring at t=0 -- so we synthesise the
# anchor to make the time-to-first-improvement visible.
# Fix_embedding has NO anchor: each agent's actual first scoring event
# (~2.196 for the unmodified corrupted model, around t=4 min) is shown
# directly, and the y-axis is widened to fit it.
BASELINE_AT_T0 = {
    "triton_cumsum": 0.644,
}


def load():
    rows = list(csv.DictReader(open(CSV_PATH)))
    out = {}
    for r in rows:
        if r["model"] != "claude-sonnet-4-6":
            continue
        key = (r["task"], r["arm"])
        t_min = float(r["t_min"])
        cutoff = TIME_CUTOFF.get(key)
        if cutoff is not None and t_min > cutoff:
            continue
        out.setdefault(key, []).append({
            "t_min": t_min,
            "score": float(r["score"]),
            "cost_usd": float(r["cost_usd"]),
        })
    for (task, arm), evs in out.items():
        if task in BASELINE_AT_T0 and not any(e["t_min"] == 0.0 for e in evs):
            evs.insert(0, {
                "t_min": 0.0,
                "score": BASELINE_AT_T0[task],
                "cost_usd": 0.0,
            })
    for k in out:
        out[k].sort(key=lambda x: x["t_min"])
    return out


def running_best(values, lower_is_better):
    op = min if lower_is_better else max
    out, b = [], None
    for v in values:
        b = v if b is None else op(b, v)
        out.append(b)
    return out


plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 7,
    "axes.titlesize": 7.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 6.5,
    "legend.fontsize": 7,
    "legend.frameon": False,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "lines.linewidth": 1.1,
    "lines.markersize": 3.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def apply_break_scale(ax, break_low=0.45, ymax=2.40, top_frac=0.20):
    """Piecewise-linear y-axis: full resolution below break_low, compressed
    above (the upper segment occupies only top_frac of the visual span).
    Used for fix_embedding so the 2.20 baseline is visible as a starting
    anchor without crushing the 0.20-0.40 tail where the two arms differ."""
    span_lo = break_low - 0.18  # data span of the lower (full-res) segment
    span_hi = ymax - break_low  # data span of the upper (compressed) segment
    # Map: lower segment occupies (1 - top_frac) of axis, upper occupies top_frac.
    # In transformed coords, place break_low at 0 and ymax at +1 / -1 limits.

    def forward(y):
        y = np.asarray(y, dtype=float)
        below = (y - break_low) / span_lo * (1 - top_frac)
        above = (y - break_low) / span_hi * top_frac
        return np.where(y <= break_low, below, above)

    def inverse(yt):
        yt = np.asarray(yt, dtype=float)
        below = break_low + yt / (1 - top_frac) * span_lo
        above = break_low + yt / top_frac * span_hi
        return np.where(yt <= 0, below, above)

    ax.set_yscale("function", functions=(forward, inverse))
    ax.set_ylim(0.18, ymax)
    ax.set_yticks([0.20, 0.30, 0.40, 1.0, 2.0])

    # Visible "//" break markers drawn on the y-axis at the boundary.
    # Two short diagonal segments, one just below the break and one just
    # above, drawn in axes-coordinates so they sit on the spine.
    y_break_axes = (1 - top_frac)  # axis-coord position of the break
    d_y = 0.015                     # half-height of each tick segment (axes units)
    d_x = 0.022                     # half-width of each tick (axes units)
    kw = dict(transform=ax.transAxes, color="black", clip_on=False,
              lw=0.7, zorder=10)
    # Lower tick of the //
    ax.plot([-d_x, +d_x], [y_break_axes - 2 * d_y, y_break_axes - 0 * d_y], **kw)
    # Upper tick of the //
    ax.plot([-d_x, +d_x], [y_break_axes - 0 * d_y, y_break_axes + 2 * d_y], **kw)
    # Mask the spine across the break with a small white rectangle to
    # avoid the spine running through the //.
    from matplotlib.patches import Rectangle
    mask = Rectangle((-d_x * 0.6, y_break_axes - d_y * 1.4),
                     d_x * 1.2, d_y * 2.8,
                     transform=ax.transAxes, facecolor="white",
                     edgecolor="none", clip_on=False, zorder=9)
    ax.add_patch(mask)


def draw_panel(ax, events, color, marker, lower_is_better, x_key):
    if not events:
        return
    xs = np.array([e[x_key] for e in events])
    sv = np.array([e["score"] for e in events])
    best = np.array(running_best(sv.tolist(), lower_is_better))

    ax.scatter(xs, sv, s=5, color=color, alpha=0.40, marker=marker,
               edgecolor="none", zorder=3)
    ax.plot(xs, best, "-", color=color, lw=1.1, zorder=4)
    op = np.argmin if lower_is_better else np.argmax
    i_best = int(op(sv))
    ax.scatter([xs[i_best]], [sv[i_best]], s=42, color=color, marker="*",
               edgecolor="black", linewidth=0.3, zorder=5)


def main():
    data = load()
    n_tasks = len(TASKS)

    fig = plt.figure(figsize=(7.1, 2.95))
    gs = fig.add_gridspec(
        2, n_tasks,
        left=0.075, right=0.992, top=0.81, bottom=0.135,
        hspace=0.32, wspace=0.32,
    )

    for col, (task, title, lower, ylabel, ref, ylim, base_v) in enumerate(TASKS):
        ax_t = fig.add_subplot(gs[0, col])
        ax_c = fig.add_subplot(gs[1, col], sharey=ax_t)

        paper = data.get((task, "paper-4.6"), [])
        ara   = data.get((task, "ARA-4.6"),   [])

        draw_panel(ax_t, paper, C_PAPER, "o", lower, "t_min")
        draw_panel(ax_t, ara,   C_ARA,   "s", lower, "t_min")
        draw_panel(ax_c, paper, C_PAPER, "o", lower, "cost_usd")
        draw_panel(ax_c, ara,   C_ARA,   "s", lower, "cost_usd")

        for ax in (ax_t, ax_c):
            ax.axhline(ref, color="#888888", ls=":", lw=0.6, zorder=1)
            if base_v is not None:
                ax.axhline(base_v, color="#BBBBBB", ls=":", lw=0.6, zorder=1)
            ax.set_ylim(*ylim)
            ax.tick_params(labelsize=5.5, length=2, pad=1.2)

        # Special case: piecewise y-axis on fix_embedding so the 2.20
        # baseline anchor is visible without crushing the 0.20-0.40 tail.
        if task == "fix_embedding":
            for ax in (ax_t, ax_c):
                apply_break_scale(ax, break_low=0.45, ymax=2.40, top_frac=0.22)

        # Show y-tick labels on the bottom row too -- the cost panel x-axis
        # is different from the time panel, so a reader scanning across the
        # row (rather than down the column) needs the y-numbers locally.

        # Shared x-axes per row: time on top, cost on bottom.
        ax_t.set_xlim(0, TIME_XLIM)
        ax_c.set_xlim(0, COST_XLIM)
        ax_t.set_xticks([0, 250, 500])
        ax_c.set_xticks([0, 40, 80])

        # Y-label on the top panel only (shared sharey covers the bottom).
        ax_t.set_ylabel(ylabel, fontsize=6, labelpad=1.5)

        # X-labels: time on top, cost on bottom.
        ax_t.set_xlabel("wall-clock min", fontsize=6, labelpad=1.0)
        ax_c.set_xlabel("API cost (USD)", fontsize=6, labelpad=1.0)

        # Per-task title above the top panel (with up/down arrow).
        ax_t.set_title(title, fontsize=7, pad=3.0, fontweight="bold")

        # Tiny "ref" / "baseline" labels beside the dotted lines, on the
        # top panel only (cost panel is too crowded near the right edge).
        x_anchor = TIME_XLIM * 0.97
        ax_t.text(x_anchor, ref + 0.025 * (ylim[1] - ylim[0]),
                  f"ref {ref}", fontsize=4.5, color="#888888",
                  ha="right", va="bottom")
        if base_v is not None:
            ax_t.text(x_anchor, base_v + 0.025 * (ylim[1] - ylim[0]),
                      f"baseline {base_v}", fontsize=4.5, color="#999999",
                      ha="right", va="bottom")

    # Single global legend at the very top.
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color=C_PAPER, lw=1.2, marker="o", markersize=4,
               label="paper (Sonnet 4.6)"),
        Line2D([0], [0], color=C_ARA,   lw=1.2, marker="s", markersize=4,
               label="ARA (Sonnet 4.6)"),
        Line2D([0], [0], marker="*", color="#888888", lw=0, markersize=7,
               markeredgecolor="black", markeredgewidth=0.3,
               label="best attempt"),
        Line2D([0], [0], color="#888888", lw=0.7, ls=":", label="reference"),
    ]
    fig.legend(handles=handles, loc="upper center",
               bbox_to_anchor=(0.5, 1.01), ncol=4,
               handlelength=2.0, columnspacing=2.2, borderaxespad=0.0,
               frameon=False, fontsize=7)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = OUT_DIR / "summary_5tasks_46.pdf"
    png = OUT_DIR / "summary_5tasks_46.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    print(f"saved {pdf}\nsaved {png}")


if __name__ == "__main__":
    main()
