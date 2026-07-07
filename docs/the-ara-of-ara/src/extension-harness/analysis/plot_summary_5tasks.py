"""5-task composite trajectory summary for §7.4 body.

A single figure with 5 panels (one per RE-Bench extension task) showing the
best-so-far score envelope for each arm. No raw scoring scatter — that's in
the appendix per-task figures. Same color scheme as the per-task plots:

  paper Sonnet 4.5  → light blue dashed  (only triton + mlm have 4.5 data)
  ARA   Sonnet 4.5  → soft orange dashed
  paper Sonnet 4.6  → deep blue solid
  ARA   Sonnet 4.6  → vermillion solid

Each panel: shared 0-540min x-axis (8 h SLURM cap; rust ARA crosses into the
parent+resume window), per-task y-axis bounds, reference line, and a star
at the best-attempt position.

Output: paper/shared/figures/extension/summary_5tasks.{pdf,png}.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import subprocess

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
CLAUDE_TMP = pathlib.Path("/n/home04/zechenzhang/.claude/tmp/claude-62233")

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

C_PAPER_45 = "#56B4E9"
C_ARA_45   = "#E69F00"
C_PAPER_46 = "#0072B2"
C_ARA_46   = "#D55E00"


def job_start_epoch(run_dir):
    m = re.search(r"job(\d+)", run_dir.name)
    if not m:
        return None
    out = subprocess.run(
        ["sacct", "-j", m.group(1), "--format=Start", "-n", "-X"],
        capture_output=True, text=True,
    ).stdout.strip().split("\n")[0].strip()
    try:
        return datetime.datetime.fromisoformat(out).timestamp()
    except Exception:
        return None


def parse_run(run_dir, score_re):
    """Generic parser: trace.jsonl + Claude tmp subagent task outputs.
    Returns (events, cost_track, final_cost) where events is [(t_min, score)]
    and cost_track is [(t_min, cumulative_usd)]."""
    trace_events = []
    tmp_events = []
    cost_track = []
    cost_acc = 0.0
    seen = set()

    trace = run_dir / "trace.jsonl"
    if trace.exists():
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
            if d.get("type") != "user":
                continue
            t_min = (t_s or 0) / 60.0
            for m in score_re.finditer(line):
                try:
                    sv = float(m.group(1))
                except ValueError:
                    continue
                k = (round(t_min, 1), round(sv, 4))
                if k in seen:
                    continue
                seen.add(k)
                trace_events.append((t_min, sv))

    job_start_s = job_start_epoch(run_dir)
    trace_end_min = cost_track[-1][0] if cost_track else 0
    slug = run_dir.name.replace("_", "-").lower()
    if CLAUDE_TMP.exists() and job_start_s is not None and trace_end_min > 0:
        for tmp_dir in CLAUDE_TMP.iterdir():
            if not tmp_dir.is_dir():
                continue
            if slug not in tmp_dir.name.lower():
                continue
            for output_f in tmp_dir.glob("*/tasks/*.output"):
                try:
                    txt = output_f.read_text(errors="ignore")
                except Exception:
                    continue
                t_min = (output_f.stat().st_mtime - job_start_s) / 60.0
                if t_min < 0 or t_min > trace_end_min + 5:
                    continue
                for m in score_re.finditer(txt):
                    try:
                        sv = float(m.group(1))
                    except ValueError:
                        continue
                    tmp_events.append((t_min, sv))

    trace_scores = {round(s, 4) for _, s in trace_events}
    extra = []
    seen_tmp = set()
    for t, sv in sorted(tmp_events):
        if round(sv, 4) in trace_scores:
            continue
        k = (round(t, 0), round(sv, 4))
        if k in seen_tmp:
            continue
        seen_tmp.add(k)
        extra.append((t, sv))

    events = sorted(trace_events + extra)

    meta_path = run_dir / "metadata.json"
    final_cost = cost_acc
    if meta_path.exists() and cost_acc > 0:
        try:
            meta = json.loads(meta_path.read_text())
            mc = meta.get("agent", {}).get("total_cost_usd")
            if mc:
                scale = mc / cost_acc
                cost_track = [(t, c * scale) for (t, c) in cost_track]
                final_cost = mc
        except Exception:
            pass

    return events, cost_track, final_cost


def baseline_event(run_dir):
    fs = run_dir / "baseline_score.json"
    if not fs.exists():
        return None
    try:
        d = json.loads(fs.read_text()).get("result", {})
        if "score" in d and d["score"] is not None:
            return (0.0, d["score"])
    except Exception:
        return None
    return None


def harness_final(run_dir, t_min):
    fs = run_dir / "final_score.json"
    if not fs.exists():
        return None
    try:
        d = json.loads(fs.read_text()).get("result", {})
        if "score" in d and d["score"] is not None:
            return (t_min, d["score"])
    except Exception:
        return None
    return None


def stitch(parent_dir, resume_dir, score_re, baseline_dir=None):
    """Build best-so-far trajectory by stitching parent + resume.
    Returns list of (t_min, score) sorted by t_min."""
    pts = []
    bl = baseline_event(baseline_dir or parent_dir)
    if bl:
        pts.append(bl)
    p_evts, p_track, p_cost = parse_run(parent_dir, score_re)
    p_t_end = p_track[-1][0] if p_track else (p_evts[-1][0] if p_evts else 0)
    pts.extend(p_evts)
    pf = harness_final(parent_dir, p_t_end)
    if pf and not any(abs(p[1] - pf[1]) < 1e-4 and abs(p[0] - pf[0]) < 5 for p in pts):
        pts.append(pf)
    if resume_dir is not None:
        r_evts, r_track, _ = parse_run(resume_dir, score_re)
        pts.extend((p_t_end + t, s) for t, s in r_evts)
        rf = harness_final(resume_dir, p_t_end + (r_track[-1][0] if r_track else 0))
        if rf and not any(abs(p[1] - rf[1]) < 1e-4 and abs(p[0] - rf[0]) < 5 for p in pts):
            pts.append(rf)
    pts.sort(key=lambda x: x[0])
    return pts


def best_so_far(pts, lower_is_better):
    if not pts:
        return [], []
    ts = [p[0] for p in pts]
    sv = [p[1] for p in pts]
    op = min if lower_is_better else max
    out, b = [], None
    for v in sv:
        b = v if b is None else op(b, v)
        out.append(b)
    return ts, out


# ---------------------------------------------------------------------------
# Per-task data sources
# ---------------------------------------------------------------------------
TRITON_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|NaN)'
    r'[^}]{0,500}'
    r'\\?"solution_time_ms\\?":\s*(-?\d+(?:\.\d+)?)')
RUST_RE = re.compile(
    r"Score:\s*([0-9.]+)\s*\\?n?\s*\|\s*\d+\s*successes\s*/\s*165")
NANOGPT_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,500}'
    r'win_vs_gpt2-alpaca\\?":\s*(-?\d+(?:\.\d+)?)')
FIXEMBED_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,500}'
    r'\\?"loss_validation\\?":\s*(-?\d+(?:\.\d+)?)')
MLM_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,400}'
    r'\\?"loss\\?":\s*(-?\d+(?:\.\d+)?)'
    r'[^}]{0,200}'
    r'\\?"compliant\\?"')


# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "legend.frameon": False,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "lines.linewidth": 1.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def _draw_arm(ax, pts, color, ls, lower_is_better, marker_best="*"):
    if not pts:
        return
    ts, best = best_so_far(pts, lower_is_better)
    ax.plot(ts, best, ls, color=color, lw=1.5, zorder=4)
    sv = [p[1] for p in pts]
    op = min if lower_is_better else max
    i_best = sv.index(op(sv))
    ax.scatter([pts[i_best][0]], [pts[i_best][1]], s=55, color=color,
               marker=marker_best, edgecolor="black", linewidth=0.4, zorder=5)


def panel_triton(ax):
    paper_45 = stitch(RUN_ROOT / "triton_cumsum_paper_seed8_job7982788", None, TRITON_RE)
    ara_45   = stitch(RUN_ROOT / "triton_cumsum_ara_seed8_job7982791",   None, TRITON_RE)
    paper_46 = stitch(RUN_ROOT / "triton_cumsum_paper_seed0_job6595591", None, TRITON_RE)
    ara_46   = stitch(RUN_ROOT / "triton_cumsum_ara_seed0_job6595593",   None, TRITON_RE)
    _draw_arm(ax, paper_45, C_PAPER_45, "--", lower_is_better=True)
    _draw_arm(ax, ara_45,   C_ARA_45,   "--", lower_is_better=True)
    _draw_arm(ax, paper_46, C_PAPER_46, "-",  lower_is_better=True)
    _draw_arm(ax, ara_46,   C_ARA_46,   "-",  lower_is_better=True)
    ax.axhline(0.47, color="#888888", ls=":", lw=0.7)
    ax.text(10, 0.50, "ref. 0.47", fontsize=6, color="#888888")
    ax.set_ylim(-0.95, 0.85)
    ax.set_title(r"$\mathtt{triton\_cumsum}$ (\,$\downarrow$\,)")
    ax.set_ylabel(r"$\log(t_\mathrm{ms})$")


def panel_rust(ax):
    paper = stitch(RUN_ROOT / "rust_codecontests_paper_seed0_job7798926", None, RUST_RE)
    ara_parent = RUN_ROOT / "rust_codecontests_ara_seed0_job7600566"
    ara_resume = RUN_ROOT / "rust_codecontests_ara_seed0_resume_job7720567"
    ara = stitch(ara_parent, ara_resume, RUST_RE)
    # Add ara score-only confirmation (free re-eval after resume)
    so = harness_final(ara_parent / "score_only_job7760733", 540)
    if so:
        ara.append(so)
    ara.sort()
    _draw_arm(ax, paper, C_PAPER_46, "-",  lower_is_better=False)
    _draw_arm(ax, ara,   C_ARA_46,   "-",  lower_is_better=False)
    ax.axhline(0.13, color="#888888", ls=":", lw=0.7)
    ax.text(10, 0.16, "ref. 0.13", fontsize=6, color="#888888")
    ax.set_ylim(0.05, 0.60)
    ax.set_title(r"$\mathtt{rust\_codecontests}$ (\,$\uparrow$\,)")
    ax.set_ylabel(r"$n_\mathrm{solved}/165$")


def panel_nanogpt(ax):
    paper = stitch(RUN_ROOT / "nanogpt_chat_rl_paper_seed0_job7517443",
                    RUN_ROOT / "nanogpt_chat_rl_paper_seed0_resume_job7723617",
                    NANOGPT_RE)
    ara = stitch(RUN_ROOT / "nanogpt_chat_rl_ara_seed0_job7077234", None, NANOGPT_RE)
    _draw_arm(ax, paper, C_PAPER_46, "-",  lower_is_better=False)
    _draw_arm(ax, ara,   C_ARA_46,   "-",  lower_is_better=False)
    ax.axhline(0.85, color="#888888", ls=":", lw=0.7)
    ax.text(10, 0.87, "ref. 0.85", fontsize=6, color="#888888")
    ax.set_ylim(0.45, 1.02)
    ax.set_title(r"$\mathtt{nanogpt\_chat\_rl}$ (\,$\uparrow$\,)")
    ax.set_ylabel(r"win-rate")


def panel_fixembed(ax):
    paper = stitch(RUN_ROOT / "fix_embedding_paper_seed0_job7591645",
                    RUN_ROOT / "fix_embedding_paper_seed0_resume_job7729813",
                    FIXEMBED_RE)
    ara = stitch(RUN_ROOT / "fix_embedding_ara_seed0_job7591646", None, FIXEMBED_RE)
    _draw_arm(ax, paper, C_PAPER_46, "-",  lower_is_better=True)
    _draw_arm(ax, ara,   C_ARA_46,   "-",  lower_is_better=True)
    ax.axhline(0.26, color="#888888", ls=":", lw=0.7)
    ax.text(10, 0.275, "ref. 0.26", fontsize=6, color="#888888")
    ax.set_ylim(0.18, 0.40)
    ax.set_title(r"$\mathtt{fix\_embedding}$ (\,$\downarrow$\,)")
    ax.set_ylabel(r"$\log(\ell_\mathrm{val}{-}1.5)$")


def panel_mlm(ax):
    paper_45 = stitch(RUN_ROOT / "restricted_mlm_paper_seed1_job6858168",
                       RUN_ROOT / "restricted_mlm_paper_seed1_resume_job7070627",
                       MLM_RE)
    ara_45   = stitch(RUN_ROOT / "restricted_mlm_ara_seed1_job6786400", None, MLM_RE)
    paper_46 = stitch(RUN_ROOT / "restricted_mlm_paper_seed0_job7079164", None, MLM_RE)
    ara_46   = stitch(RUN_ROOT / "restricted_mlm_ara_seed0_job7079165",
                       RUN_ROOT / "restricted_mlm_ara_seed0_resume_job8011216",
                       MLM_RE)
    _draw_arm(ax, paper_45, C_PAPER_45, "--", lower_is_better=True)
    _draw_arm(ax, ara_45,   C_ARA_45,   "--", lower_is_better=True)
    _draw_arm(ax, paper_46, C_PAPER_46, "-",  lower_is_better=True)
    _draw_arm(ax, ara_46,   C_ARA_46,   "-",  lower_is_better=True)
    ax.axhline(1.13, color="#888888", ls=":", lw=0.7)
    ax.text(10, 1.18, "ref. 1.13", fontsize=6, color="#888888")
    ax.set_ylim(0.55, 1.95)
    ax.set_title(r"$\mathtt{restricted\_mlm}$ (\,$\downarrow$\,)")
    ax.set_ylabel(r"$\log(\ell_\mathrm{val}{-}1.5)$")


def main():
    fig = plt.figure(figsize=(7.0, 4.0))
    gs = fig.add_gridspec(2, 3, hspace=0.65, wspace=0.42)

    ax1 = fig.add_subplot(gs[0, 0]); panel_triton(ax1)
    ax2 = fig.add_subplot(gs[0, 1]); panel_rust(ax2)
    ax3 = fig.add_subplot(gs[0, 2]); panel_nanogpt(ax3)
    ax4 = fig.add_subplot(gs[1, 0]); panel_fixembed(ax4)
    ax5 = fig.add_subplot(gs[1, 1]); panel_mlm(ax5)
    ax_legend = fig.add_subplot(gs[1, 2]); ax_legend.axis("off")

    for ax in [ax1, ax2, ax3, ax4, ax5]:
        ax.set_xlim(0, 540)
        ax.set_xlabel("wall-clock min")
        ax.tick_params(labelsize=7)
        for label in ax.yaxis.get_ticklabels(): label.set_fontsize(7)

    # Custom legend in the empty 6th cell
    from matplotlib.lines import Line2D
    legend_handles = [
        Line2D([0], [0], color=C_PAPER_45, lw=1.5, ls="--", label="paper (Sonnet 4.5)"),
        Line2D([0], [0], color=C_ARA_45,   lw=1.5, ls="--", label="ARA (Sonnet 4.5)"),
        Line2D([0], [0], color=C_PAPER_46, lw=1.5, ls="-",  label="paper (Sonnet 4.6)"),
        Line2D([0], [0], color=C_ARA_46,   lw=1.5, ls="-",  label="ARA (Sonnet 4.6)"),
        Line2D([0], [0], marker="*", color="#888888", lw=0,
               markersize=8, markeredgecolor="black", markeredgewidth=0.4,
               label="best attempt"),
        Line2D([0], [0], color="#888888", lw=0.7, ls=":", label="task reference"),
    ]
    ax_legend.legend(handles=legend_handles, loc="center", frameon=False,
                     fontsize=7.5, handlelength=2.5, borderaxespad=0)
    ax_legend.text(0.5, 0.95, "Legend",
                   transform=ax_legend.transAxes, ha="center", va="top",
                   fontsize=8.5, fontweight="bold")

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/paper/shared/figures/extension"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "summary_5tasks.pdf"
    png_path = out_dir / "summary_5tasks.png"
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    print(f"saved {pdf_path}\nsaved {png_path}")


if __name__ == "__main__":
    main()
