"""Two separate MLM trajectory plots: one for Sonnet 4.5, one for Sonnet 4.6.

Reads exhaustive scoring events from mlm_scores_all.csv (extracted by
extract_mlm_scores.py) which catches all four output formats:
  - inline JSON, short Loss/Score one-liners, persisted-output files,
    and Claude tmp subagent task outputs.

For each model version, produces a 2-panel figure (score vs time, score vs
cost) with paper and ARA arms overlaid. Saves to:
  paper/shared/figures/extension/mlm_45_paper_vs_ara.{pdf,png}
  paper/shared/figures/extension/mlm_46_paper_vs_ara.{pdf,png}
"""
from __future__ import annotations

import csv
import pathlib

import matplotlib.pyplot as plt
import numpy as np

CSV_PATH = pathlib.Path(__file__).parent / "mlm_scores_all.csv"
OUT_DIR = pathlib.Path(
    "/n/home04/zechenzhang/ara-project/paper/shared/figures/extension"
)

REFERENCE = 1.13
BASELINE  = 1.84

C_PAPER = "#0072B2"
C_ARA   = "#D55E00"


def load():
    rows = list(csv.DictReader(open(CSV_PATH)))
    out = {}
    for r in rows:
        arm = r["arm"]
        out.setdefault(arm, []).append({
            "t_min": float(r["t_min"]),
            "score": float(r["score"]),
            "loss": float(r["loss"]),
            "cost_usd": float(r["cost_usd"]),
            "source": r["source"],
        })
    for arm in out:
        out[arm].sort(key=lambda x: x["t_min"])
    return out


def dedup_events(events):
    """Per-arm: same (round(t,0), round(score,3)) reported through multiple
    sources is a single underlying event. Drop NaN/inf scores (these reflect
    failed scoring runs whose canonical scorer returned NaN, e.g. when the
    model didn't load or the val loss exploded into Inf)."""
    import math
    seen = set(); out = []
    for ev in events:
        sv = ev["score"]
        if not math.isfinite(sv):
            continue
        k = (round(ev["t_min"], 0), round(sv, 3))
        if k in seen: continue
        seen.add(k); out.append(ev)
    return out


def running_min(values):
    out, b = [], float("inf")
    for v in values:
        b = min(b, v); out.append(b)
    return out


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
    "lines.linewidth": 1.6,
    "lines.markersize": 4.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def make_plot(paper_events, ara_events, model_label, slug, time_xlim, cost_xlim):
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)

    for label, events, color, marker in [
        (f"paper ({model_label})", paper_events, C_PAPER, "o"),
        (f"ARA ({model_label})",   ara_events,   C_ARA,   "s"),
    ]:
        if not events:
            continue
        ts = np.array([e["t_min"] for e in events])
        sv = np.array([e["score"] for e in events])
        cs = np.array([e["cost_usd"] for e in events])
        best = np.array(running_min(sv.tolist()))

        # Raw scoring scatter (all events, including transient regressions)
        ax_t.scatter(ts, sv, s=22, color=color, alpha=0.55, marker=marker,
                     edgecolor="none", zorder=3)
        ax_c.scatter(cs, sv, s=22, color=color, alpha=0.55, marker=marker,
                     edgecolor="none", zorder=3)

        # Best-so-far envelope
        ax_t.plot(ts, best, "-", color=color, lw=1.7, zorder=4, label=label)
        ax_c.plot(cs, best, "-", color=color, lw=1.7, zorder=4)

        # Best-attempt star
        i_best = int(np.argmin(sv))
        ax_t.scatter([ts[i_best]], [sv[i_best]], s=110, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)
        ax_c.scatter([cs[i_best]], [sv[i_best]], s=110, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)

    for ax in (ax_t, ax_c):
        ax.axhline(REFERENCE, color="#888888", ls=":", lw=0.8, zorder=1)
        ax.axhline(BASELINE,  color="#BBBBBB", ls=":", lw=0.8, zorder=1)
        ax.set_ylabel(r"score $= \log(\ell_\mathrm{val}{-}1.5)$" "\n(lower is better)")
        ax.grid(alpha=0.18)
        ax.set_ylim(0.55, 2.05)

    ax_t.set_xlim(0, time_xlim)
    ax_c.set_xlim(0, cost_xlim)
    ax_c.axvline(50, color="#555555", ls=":", lw=0.8, zorder=1)
    ax_c.text(50, 2.03, " \\$50 budget cap", fontsize=6.5, color="#555555",
              ha="left", va="top")

    for ax in (ax_t, ax_c):
        x0, x1 = ax.get_xlim()
        ax.text(x0 + 0.02 * (x1 - x0), REFERENCE + 0.03,
                "RE-Bench reference (1.13)", fontsize=6.5, color="#888888",
                ha="left", va="bottom")
        ax.text(x0 + 0.02 * (x1 - x0), BASELINE + 0.03,
                "untrained-MLP baseline (1.84)", fontsize=6.5, color="#999999",
                ha="left", va="bottom")

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative API cost (USD)")
    ax_t.set_title("Score vs. time")
    ax_c.set_title("Score vs. cost")

    handles, labels = ax_t.get_legend_handles_labels()
    leg = fig.legend(handles, labels, loc="upper center",
                     bbox_to_anchor=(0.5, 1.005), ncol=2, handlelength=2.4,
                     columnspacing=1.5, borderaxespad=0.0)
    leg.set_zorder(10)

    fig.suptitle(f"restricted_mlm: paper vs. ARA on {model_label}",
                 fontsize=10.5, y=1.10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / f"mlm_{slug}_paper_vs_ara.pdf"
    png_path = OUT_DIR / f"mlm_{slug}_paper_vs_ara.png"
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    print(f"saved {pdf_path}\nsaved {png_path}")


def main():
    data = load()
    paper_45 = dedup_events(data.get("paper-4.5", []))
    ara_45   = dedup_events(data.get("ARA-4.5", []))
    paper_46 = dedup_events(data.get("paper-4.6", []))
    ara_46   = dedup_events(data.get("ARA-4.6", []))

    print(f"\nDeduped event counts:")
    print(f"  paper-4.5: {len(paper_45)}  (best={min(e['score'] for e in paper_45):.4f})")
    print(f"  ARA-4.5:   {len(ara_45)}  (best={min(e['score'] for e in ara_45):.4f})")
    print(f"  paper-4.6: {len(paper_46)}  (best={min(e['score'] for e in paper_46):.4f})")
    print(f"  ARA-4.6:   {len(ara_46)}  (best={min(e['score'] for e in ara_46):.4f})")

    # Sonnet 4.5 plot — both arms span ~770 min (parent + resume for paper, single for ARA)
    print("\n--- Sonnet 4.5 plot ---")
    make_plot(paper_45, ara_45, "Sonnet 4.5", "45",
              time_xlim=800, cost_xlim=70)

    # Sonnet 4.6 plot — paper single 8h, ARA orig+resume ~12h
    print("\n--- Sonnet 4.6 plot ---")
    make_plot(paper_46, ara_46, "Sonnet 4.6", "46",
              time_xlim=750, cost_xlim=80)


if __name__ == "__main__":
    main()
