"""restricted_mlm extension: paper vs ARA across Sonnet 4.5 and 4.6.

Two side-by-side panels: score vs wall-clock minutes, score vs cumulative cost.
Four trajectories overlaid: paper-4.5, ARA-4.5, paper-4.6, ARA-4.6 (orig+resume).

Score = log(val_loss - 1.5); lower is better.
Reference (1.13) is the official Tao ConvMLM+bigrams solution.
RE-Bench human ceiling not formally established; the agent baseline (untrained
restricted MLP) lands around 1.84-1.85.

Canonical scorer pattern: '{"score": X, "loss": Y, "compliant": ...}'
anchored on the "compliant" key so the regex never matches training-internal
val_loss probes (which use plain "val_loss"). Read from trace.jsonl AND
~/.claude/tmp/<sid>/<workdir-slug>/<uuid>/tasks/*.output.

Source runs:
  paper-4.5 = restricted_mlm_paper_seed1_job6858168 + resume_job7070627
  ARA-4.5   = restricted_mlm_ara_seed1_job6786400 (single run)
  paper-4.6 = restricted_mlm_paper_seed0_job7079164 (single run, no final_score.json)
  ARA-4.6   = restricted_mlm_ara_seed0_job7079165 (orig, SDK crash at 5h32m)
              + restricted_mlm_ara_seed0_resume_job8011216 (resume after fix)
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

PAPER_45_PARENT = RUN_ROOT / "restricted_mlm_paper_seed1_job6858168"
PAPER_45_RESUME = RUN_ROOT / "restricted_mlm_paper_seed1_resume_job7070627"
ARA_45_DIR      = RUN_ROOT / "restricted_mlm_ara_seed1_job6786400"

PAPER_46_DIR    = RUN_ROOT / "restricted_mlm_paper_seed0_job7079164"
ARA_46_ORIG     = RUN_ROOT / "restricted_mlm_ara_seed0_job7079165"
ARA_46_RESUME   = RUN_ROOT / "restricted_mlm_ara_seed0_resume_job8011216"

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

# Canonical: '{"score": X, "loss": Y, "compliant": true/false, ...}'
SCORE_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,400}'
    r'\\?"loss\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,200}'
    r'\\?"compliant\\?"'
)

REFERENCE = 1.13   # Tao official ConvMLM+bigrams
BASELINE  = 1.84   # untrained restricted MLP


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


def baseline_event(run_dir: pathlib.Path):
    fs = run_dir / "baseline_score.json"
    if not fs.exists():
        return None
    try:
        d = json.loads(fs.read_text()).get("result", {})
        if "score" in d and d["score"] is not None:
            return (0.0, d["score"], 0.0)
    except Exception:
        return None
    return None


def harness_final(run_dir: pathlib.Path, t_min: float, cost: float):
    fs = run_dir / "final_score.json"
    if not fs.exists():
        return None
    try:
        d = json.loads(fs.read_text()).get("result", {})
        if "score" in d and d["score"] is not None:
            return (t_min, d["score"], cost)
    except Exception:
        return None
    return None


def stitch_parent_resume(parent_dir, resume_dir):
    """Build a single chronological trajectory: baseline + parent events + parent final + resume events + resume final."""
    p_evts, p_track, p_cost = parse_run(parent_dir)
    p_t_end = p_track[-1][0] if p_track else (p_evts[-1][0] if p_evts else 0)
    pts = []
    bl = baseline_event(parent_dir)
    if bl: pts.append(bl)
    pts.extend((t, s, cost_at(p_track, t)) for t, s in p_evts)
    pf = harness_final(parent_dir, p_t_end, p_cost)
    if pf and not any(abs(p[1] - pf[1]) < 1e-4 and abs(p[0] - pf[0]) < 5 for p in pts):
        pts.append(pf)
    if resume_dir is not None:
        r_evts, r_track, r_cost = parse_run(resume_dir)
        r_t_end = r_track[-1][0] if r_track else (r_evts[-1][0] if r_evts else 0)
        pts.extend((p_t_end + t, s, p_cost + cost_at(r_track, t)) for t, s in r_evts)
        rf = harness_final(resume_dir, p_t_end + r_t_end, p_cost + r_cost)
        if rf and not any(abs(p[1] - rf[1]) < 1e-4 and abs(p[0] - rf[0]) < 5 for p in pts):
            pts.append(rf)
    pts.sort(key=lambda x: x[0])
    return pts


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

    # ---- 4.5 paper (parent + resume) ----
    paper_45 = stitch_parent_resume(PAPER_45_PARENT, PAPER_45_RESUME)
    # ---- 4.5 ARA (single run) ----
    a45_evts, a45_track, a45_cost = parse_run(ARA_45_DIR)
    ara_45 = []
    bl = baseline_event(ARA_45_DIR)
    if bl: ara_45.append(bl)
    else:
        # No baseline_score.json; anchor at the assumed corrupted starting point
        ara_45.append((0.0, BASELINE, 0.0))
    ara_45.extend((t, s, cost_at(a45_track, t)) for t, s in a45_evts)
    a45_fin = harness_final(ARA_45_DIR, a45_track[-1][0] if a45_track else 0, a45_cost)
    if a45_fin: ara_45.append(a45_fin)
    ara_45.sort(key=lambda x: x[0])

    # ---- 4.6 paper (single run) ----
    p46_evts, p46_track, p46_cost = parse_run(PAPER_46_DIR)
    paper_46 = []
    bl = baseline_event(PAPER_46_DIR)
    if bl: paper_46.append(bl)
    paper_46.extend((t, s, cost_at(p46_track, t)) for t, s in p46_evts)
    p46_fin = harness_final(PAPER_46_DIR, p46_track[-1][0] if p46_track else 0, p46_cost)
    if p46_fin: paper_46.append(p46_fin)
    paper_46.sort(key=lambda x: x[0])

    # ---- 4.6 ARA (orig + resume) ----
    ara_46 = stitch_parent_resume(ARA_46_ORIG, ARA_46_RESUME)

    # Print summary
    for label, pts in [("paper-4.5", paper_45), ("ARA-4.5", ara_45),
                        ("paper-4.6", paper_46), ("ARA-4.6", ara_46)]:
        print(f"\n{label}:  n={len(pts)}")
        for t, s, c in pts:
            print(f"  t={t:6.1f}  {s:.4f}  cost=${c:.2f}")

    # ---- plot ----
    arms = [
        ("paper (Sonnet 4.5)", paper_45, "#56B4E9", "--", "o"),
        ("ARA (Sonnet 4.5)",   ara_45,   "#E69F00", "--", "s"),
        ("paper (Sonnet 4.6)", paper_46, "#0072B2", "-",  "o"),
        ("ARA (Sonnet 4.6)",   ara_46,   "#D55E00", "-",  "s"),
    ]
    for label, pts, color, ls, marker in arms:
        if not pts:
            continue
        ts = np.array([p[0] for p in pts])
        sv = np.array([p[1] for p in pts])
        cs = np.array([p[2] for p in pts])
        best = np.array(running_min(sv.tolist()))

        ax_t.scatter(ts, sv, s=22, color=color, alpha=0.65, marker=marker,
                     edgecolor="none", zorder=3)
        ax_c.scatter(cs, sv, s=22, color=color, alpha=0.65, marker=marker,
                     edgecolor="none", zorder=3)

        ax_t.plot(ts, best, ls, color=color, lw=1.7, zorder=4, label=label)
        ax_c.plot(cs, best, ls, color=color, lw=1.7, zorder=4)

        i_best = int(np.argmin(sv))
        ax_t.scatter([ts[i_best]], [sv[i_best]], s=95, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)
        ax_c.scatter([cs[i_best]], [sv[i_best]], s=95, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)

    for ax in (ax_t, ax_c):
        ax.axhline(REFERENCE, color="#888888", ls=":", lw=0.8, zorder=1)
        ax.set_ylabel(r"score $= \log(\ell_\mathrm{val}{-}1.5)$" "\n(lower is better)")
        ax.grid(alpha=0.18)
        ax.set_ylim(0.55, 1.95)

    ax_t.set_xlim(0, 540)
    ax_c.set_xlim(0, 90)
    ax_c.axvline(50, color="#555555", ls=":", lw=0.8, zorder=1)
    ax_c.text(50, 1.93, " \\$50 budget cap", fontsize=6.5, color="#555555",
              ha="left", va="top")

    for ax in (ax_t, ax_c):
        x0, x1 = ax.get_xlim()
        ax.text(x0 + 0.02 * (x1 - x0), REFERENCE + 0.02,
                "RE-Bench reference (1.13)",
                fontsize=6.5, color="#888888", ha="left", va="bottom")

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative API cost (USD)")
    ax_t.set_title("Score vs. time")
    ax_c.set_title("Score vs. cost")

    handles, labels = ax_t.get_legend_handles_labels()
    leg = fig.legend(handles, labels, loc="upper center",
                     bbox_to_anchor=(0.5, 1.005), ncol=4, handlelength=2.4,
                     columnspacing=1.2, borderaxespad=0.0)
    leg.set_zorder(10)

    fig.suptitle(
        "restricted_mlm: paper vs. ARA across Sonnet 4.5 and 4.6",
        fontsize=10.5, y=1.10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/paper/shared/figures/extension"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "mlm_paper_vs_ara.pdf"
    png_path = out_dir / "mlm_paper_vs_ara.png"
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    print(f"\nsaved {pdf_path}\nsaved {png_path}")


if __name__ == "__main__":
    main()
