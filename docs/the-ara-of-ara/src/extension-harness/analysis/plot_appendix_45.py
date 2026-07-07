"""Sonnet 4.5 cross-model appendix figures for §H.5.

The body composite (summary_5tasks_46) shows only Sonnet 4.6. The 4.5
runs we have for triton_cumsum and restricted_mlm tell a complementary
cross-model story: on the weaker base, ARA helps; on the stronger base,
ARA's wider hint surface either neutralises or reverses the gain. This
script emits one single-task figure per task in the same visual style
as the body composite.

Output (single-column figures):
  paper/shared/figures/extension/triton_45_paper_vs_ara.{pdf,png}
  paper/shared/figures/extension/mlm_45_paper_vs_ara.{pdf,png}
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

# Per-task Sonnet 4.5 config: (task, title, lower_is_better, ylabel,
#   ref, ylim, time_xlim, cost_xlim, baseline_v, slug)
# Wall-clock and cost axes match the body composite (500 min, 80 USD)
# for direct cross-figure comparison; events past those cutoffs are
# dropped (the MLM paper-4.5 resume window past 500 min is a flat
# plateau at ~1.03 and contributes no new information).
TASKS = [
    ("triton_cumsum",
     r"$\mathtt{triton\_cumsum}$ (Sonnet 4.5)  $\downarrow$",
     True, r"$\log(t_\mathrm{ms})$",
     0.47, (-0.95, 1.10), 500, 80, None, "triton_45"),
    ("restricted_mlm",
     r"$\mathtt{restricted\_mlm}$ (Sonnet 4.5)  $\downarrow$",
     True, r"$\log(\ell_\mathrm{val}{-}1.5)$",
     1.13, (0.55, 2.05), 500, 80, 1.84, "mlm_45"),
]


# Synthetic t=0 baseline anchors for arms whose harness pre-agent
# baseline crashed (so no real baseline_json event exists in the CSV).
# Restricted_mlm ARA-4.5: pre-agent baseline failed with
# "PytorchStreamReader failed reading zip archive" because the starter
# checkpoint was corrupted in that run dir; the agent's first 3 score
# attempts also failed with model-architecture mismatches before it
# swapped to ConvMLMWithBiBigrams (which scores ~1.43 from precomputed
# bigram tables alone, no training). Anchoring at 1.84 matches the
# other three MLM arms' actual harness baselines and makes the
# starting-point comparison honest.
SYNTHETIC_T0 = {
    ("restricted_mlm", "ARA-4.5"): 1.84,
}


def load(task, model):
    rows = list(csv.DictReader(open(CSV_PATH)))
    out = {}
    for r in rows:
        if r["task"] != task or r["model"] != model:
            continue
        arm = r["arm"]
        out.setdefault(arm, []).append({
            "t_min": float(r["t_min"]),
            "score": float(r["score"]),
            "cost_usd": float(r["cost_usd"]),
        })
    for arm, evs in out.items():
        if (task, arm) in SYNTHETIC_T0 and not any(e["t_min"] == 0.0 for e in evs):
            evs.insert(0, {
                "t_min": 0.0,
                "score": SYNTHETIC_T0[(task, arm)],
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
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.labelsize": 8,
    "legend.fontsize": 7.5,
    "legend.frameon": False,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "lines.linewidth": 1.3,
    "lines.markersize": 3.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def draw_panel(ax, events, color, marker, lower_is_better, x_key, label):
    if not events:
        return
    xs = np.array([e[x_key] for e in events])
    sv = np.array([e["score"] for e in events])
    best = np.array(running_best(sv.tolist(), lower_is_better))

    ax.scatter(xs, sv, s=10, color=color, alpha=0.40, marker=marker,
               edgecolor="none", zorder=3)
    ax.plot(xs, best, "-", color=color, lw=1.3, zorder=4, label=label)
    op = np.argmin if lower_is_better else np.argmax
    i_best = int(op(sv))
    ax.scatter([xs[i_best]], [sv[i_best]], s=70, color=color, marker="*",
               edgecolor="black", linewidth=0.4, zorder=5)


def make_one(task, title, lower, ylabel, ref, ylim,
              t_xlim, c_xlim, base_v, slug):
    arms = load(task, "claude-sonnet-4-5")
    paper = arms.get("paper-4.5", [])
    ara   = arms.get("ARA-4.5",   [])

    fig, (ax_t, ax_c) = plt.subplots(
        1, 2, figsize=(7.0, 2.3),
        gridspec_kw={"wspace": 0.20},
        sharey=True,
    )

    draw_panel(ax_t, paper, C_PAPER, "o", lower, "t_min", "paper (Sonnet 4.5)")
    draw_panel(ax_t, ara,   C_ARA,   "s", lower, "t_min", "ARA (Sonnet 4.5)")
    draw_panel(ax_c, paper, C_PAPER, "o", lower, "cost_usd", None)
    draw_panel(ax_c, ara,   C_ARA,   "s", lower, "cost_usd", None)

    for ax in (ax_t, ax_c):
        ax.axhline(ref, color="#888888", ls=":", lw=0.7, zorder=1)
        if base_v is not None:
            ax.axhline(base_v, color="#BBBBBB", ls=":", lw=0.7, zorder=1)
        ax.set_ylim(*ylim)
        ax.tick_params(labelsize=7, length=2, pad=1.5)

    plt.setp(ax_c.get_yticklabels(), visible=False)
    ax_t.set_xlim(0, t_xlim)
    ax_c.set_xlim(0, c_xlim)
    ax_t.set_ylabel(ylabel, fontsize=7.5)
    ax_t.set_xlabel("wall-clock minutes", fontsize=7.5)
    ax_c.set_xlabel("cumulative API cost (USD)", fontsize=7.5)

    # Reference / baseline labels on the cost panel.
    ax_c.text(c_xlim * 0.97, ref + 0.025 * (ylim[1] - ylim[0]),
              f"RE-Bench ref. {ref}", fontsize=6, color="#888888",
              ha="right", va="bottom")
    if base_v is not None:
        ax_c.text(c_xlim * 0.97,
                  base_v + 0.025 * (ylim[1] - ylim[0]),
                  f"untrained baseline {base_v}", fontsize=6,
                  color="#999999", ha="right", va="bottom")

    fig.suptitle(title, fontsize=9.5, fontweight="bold", y=1.04)

    leg = ax_t.legend(loc="upper right", frameon=True, framealpha=0.92,
                      edgecolor="#CCCCCC", borderpad=0.4, fontsize=7)
    leg.set_zorder(10)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = OUT_DIR / f"{slug}_paper_vs_ara.pdf"
    png = OUT_DIR / f"{slug}_paper_vs_ara.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    print(f"saved {pdf}\nsaved {png}")
    plt.close(fig)


def main():
    for cfg in TASKS:
        make_one(*cfg)


if __name__ == "__main__":
    main()
