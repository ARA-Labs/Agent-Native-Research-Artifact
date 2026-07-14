"""fix_embedding extension: paper vs ARA on Sonnet 4.6.

Two side-by-side panels: score vs wall-clock minutes, score vs cumulative cost.
Two trajectories overlaid: paper-4.6 (parent + resume stitched) and ARA-4.6.

Score = log(val_loss - 1.5); lower is better.
Reference (0.26) is the official 3-phase adapter solution.
Best human is 0.16 (RE-Bench leaderboard).
Baseline at 2.20 (untrained, permuted GPT-2-XL) is off-scale and shown
only as a t=0 anchor square outside the y-axis crop.

Canonical scorer outputs (per the standard pattern):
  (a) trace.jsonl: '{"score": X, "message": {"loss_train": Y,
        "loss_validation": Z, "elapsed_s": W}}'
  (b) ~/.claude/tmp/<sid>/<workdir-slug>/<uuid>/tasks/*.output: same
The regex is anchored on "loss_validation" so it never matches the
training-internal 200-batch val_loss probes (which use plain "val_loss"
without the loss_validation key).

Source runs:
  paper-4.6 = fix_embedding_paper_seed0_job7591645        (parent, final 0.255)
              + fix_embedding_paper_seed0_resume_job7729813 (resume, final 0.251)
  ARA-4.6   = fix_embedding_ara_seed0_job7591646           (final ~0.236, TIMEOUT before harness final)

Saves PDF + PNG to paper/shared/figures/extension/.
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

PAPER_PARENT = RUN_ROOT / "fix_embedding_paper_seed0_job7591645"
PAPER_RESUME = RUN_ROOT / "fix_embedding_paper_seed0_resume_job7729813"
ARA_DIR      = RUN_ROOT / "fix_embedding_ara_seed0_job7591646"

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

# Canonical scorer JSON: {"score": X, "message": {..., "loss_validation": Y}}
# Anchored on "loss_validation" to exclude training-internal val_loss probes.
SCORE_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,500}'
    r'\\?"loss_validation\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
)

REFERENCE  = 0.26   # official 3-phase adapter
HUMAN_BEST = 0.16
BASELINE   = 2.20   # log(val_loss - 1.5) at the untrained / permuted starting point


# ---------------------------------------------------------------------------
def job_start_epoch(run_dir: pathlib.Path) -> float | None:
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


def parse_run(run_dir: pathlib.Path):
    """Standard pattern: read canonical score events from trace + tmp subagent
    outputs, dedupe, return + per-message cumulative cost."""
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
            for m in SCORE_RE.finditer(line):
                try:
                    sv = float(m.group(1))
                except ValueError:
                    continue
                if not (0.05 <= sv <= 5.0):
                    continue
                k = (round(t_min, 1), round(sv, 4))
                if k in seen:
                    continue
                seen.add(k)
                trace_events.append((t_min, sv))

    # Tmp subagent outputs (mtime-clamped)
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
                for m in SCORE_RE.finditer(txt):
                    try:
                        sv = float(m.group(1))
                    except ValueError:
                        continue
                    if not (0.05 <= sv <= 5.0):
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


def cost_at(track, t_min):
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


def harness_final(run_dir: pathlib.Path, t_min: float, cost: float):
    fs = run_dir / "final_score.json"
    if not fs.exists():
        return None
    try:
        d = json.loads(fs.read_text()).get("result", {})
        if "score" in d:
            return (t_min, d["score"], cost)
    except Exception:
        return None
    return None


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


def main():
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)

    # ---- ARA arm (single run) ----
    a_evts, a_track, a_cost_total = parse_run(ARA_DIR)
    a_t_end = a_track[-1][0] if a_track else (a_evts[-1][0] if a_evts else 0)
    ara_pts = [(t, s, cost_at(a_track, t)) for t, s in a_evts]
    fin = harness_final(ARA_DIR, a_t_end, a_cost_total)
    if fin and not any(abs(p[1] - fin[1]) < 1e-4 and abs(p[0] - fin[0]) < 5 for p in ara_pts):
        ara_pts.append(fin)
    ara_pts.sort(key=lambda x: x[0])

    # ---- Paper arm (parent + resume stitched) ----
    pp_evts, pp_track, pp_cost_total = parse_run(PAPER_PARENT)
    pp_t_end = pp_track[-1][0] if pp_track else (pp_evts[-1][0] if pp_evts else 0)
    pr_evts, pr_track, pr_cost_total = parse_run(PAPER_RESUME)
    pr_t_end = pr_track[-1][0] if pr_track else (pr_evts[-1][0] if pr_evts else 0)

    paper_pts = [(t, s, cost_at(pp_track, t)) for t, s in pp_evts]
    pp_fin = harness_final(PAPER_PARENT, pp_t_end, pp_cost_total)
    if pp_fin and not any(abs(p[1] - pp_fin[1]) < 1e-4 and abs(p[0] - pp_fin[0]) < 5 for p in paper_pts):
        paper_pts.append(pp_fin)
    paper_pts.extend((pp_t_end + t, s, pp_cost_total + cost_at(pr_track, t)) for t, s in pr_evts)
    pr_fin = harness_final(PAPER_RESUME, pp_t_end + pr_t_end, pp_cost_total + pr_cost_total)
    if pr_fin and not any(abs(p[1] - pr_fin[1]) < 1e-4 and abs(p[0] - pr_fin[0]) < 5 for p in paper_pts):
        paper_pts.append(pr_fin)
    paper_pts.sort(key=lambda x: x[0])

    # Print summary
    print(f"\n{'arm':<10} {'n':>3s} canonical events:")
    for label, pts in [("paper", paper_pts), ("ARA", ara_pts)]:
        print(f"{label:<10} {len(pts):>3d}")
        for t, s, c in pts:
            print(f"             t={t:6.1f}  {s:.4f}  cost=${c:.2f}")

    # ---- plot ----
    for label, pts, color, marker in [
        ("paper (Sonnet 4.6)", paper_pts, "#0072B2", "o"),
        ("ARA (Sonnet 4.6)",   ara_pts,   "#D55E00", "s"),
    ]:
        ts = np.array([p[0] for p in pts])
        sv = np.array([p[1] for p in pts])
        cs = np.array([p[2] for p in pts])
        best = np.array(running_min(sv.tolist()))

        ax_t.scatter(ts, sv, s=28, color=color, alpha=0.75, marker=marker,
                     edgecolor="none", zorder=3)
        ax_c.scatter(cs, sv, s=28, color=color, alpha=0.75, marker=marker,
                     edgecolor="none", zorder=3)

        ax_t.plot(ts, best, "-", color=color, lw=1.7, zorder=4, label=label)
        ax_c.plot(cs, best, "-", color=color, lw=1.7, zorder=4)

        # Best-attempt star (lowest score)
        i_best = int(np.argmin(sv))
        ax_t.scatter([ts[i_best]], [sv[i_best]], s=110, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)
        ax_c.scatter([cs[i_best]], [sv[i_best]], s=110, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)

    # Reference lines
    for ax in (ax_t, ax_c):
        ax.axhline(REFERENCE, color="#888888", ls=":", lw=0.8, zorder=1)
        ax.axhline(HUMAN_BEST, color="#666666", ls=":", lw=0.8, zorder=1)
        ax.set_ylabel(r"score $= \log(\ell_\mathrm{val}{-}1.5)$" "\n(lower is better)")
        ax.grid(alpha=0.18)
        ax.set_ylim(0.13, 0.40)

    ax_t.set_xlim(0, 540)
    ax_c.set_xlim(0, 90)
    ax_c.axvline(50, color="#555555", ls=":", lw=0.8, zorder=1)
    ax_c.text(50, 0.39, " \\$50 budget cap", fontsize=6.5, color="#555555",
              ha="left", va="top")

    for ax in (ax_t, ax_c):
        x0, x1 = ax.get_xlim()
        ax.text(x0 + 0.02 * (x1 - x0), REFERENCE + 0.005,
                "RE-Bench reference (0.26)",
                fontsize=6.5, color="#888888", ha="left", va="bottom")
        ax.text(x0 + 0.02 * (x1 - x0), HUMAN_BEST + 0.005,
                "human best (0.16)",
                fontsize=6.5, color="#666666", ha="left", va="bottom")

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative API cost (USD)")
    ax_t.set_title("Score vs. time")
    ax_c.set_title("Score vs. cost")

    handles, labels = ax_t.get_legend_handles_labels()
    leg = fig.legend(handles, labels, loc="upper center",
                     bbox_to_anchor=(0.5, 1.005), ncol=2, handlelength=2.4,
                     columnspacing=1.5, borderaxespad=0.0)
    leg.set_zorder(10)

    fig.suptitle(
        "fix_embedding: paper vs. ARA on Sonnet 4.6",
        fontsize=10.5, y=1.10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/paper/shared/figures/extension"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "fix_embed_paper_vs_ara.pdf"
    png_path = out_dir / "fix_embed_paper_vs_ara.png"
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    print(f"\nsaved {pdf_path}\nsaved {png_path}")


if __name__ == "__main__":
    main()
