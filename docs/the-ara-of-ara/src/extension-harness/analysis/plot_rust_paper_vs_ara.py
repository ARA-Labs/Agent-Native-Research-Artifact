"""rust_codecontests extension: paper vs ARA on Sonnet 4.6.

Two side-by-side panels: score vs wall-clock time, score vs cumulative cost.
Two trajectories overlaid: paper-4.6 and ARA-4.6.

Score = n_successes / 165 on the held-out test set; higher is better.
Reference (0.127 = 21/165) is the original RE-Bench scaffold result.

Canonical-score sources (CRITICAL — both arms launched scoring inside Claude
Task subagents, so the canonical scoring events live in TWO places):
  (a) trace.jsonl: "Score: X | N successes / 165 problems" lines
  (b) ~/.claude/tmp/<sid>/<workdir-slug>/<uuid>/tasks/*.output:
      same pattern, written by Task-tool subagents that ran the scorer.
We collect from both, dedupe by (n_succ, score), and prefer the trace
timestamp when an event appears in both.

Source runs:
  paper-4.6 = rust_codecontests_paper_seed0_job7798926
  ARA-4.6   = rust_codecontests_ara_seed0_job7600566 (parent)
              + rust_codecontests_ara_seed0_resume_job7720567 (resume)
              + score_only_job7760733 (post-resume canonical re-eval)

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
# Paths and prices
# ---------------------------------------------------------------------------
RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
CLAUDE_TMP = pathlib.Path("/n/home04/zechenzhang/.claude/tmp/claude-62233")

PAPER_DIR  = RUN_ROOT / "rust_codecontests_paper_seed0_job7798926"
ARA_PARENT = RUN_ROOT / "rust_codecontests_ara_seed0_job7600566"
ARA_RESUME = RUN_ROOT / "rust_codecontests_ara_seed0_resume_job7720567"
ARA_SCORE_ONLY = ARA_PARENT / "score_only_job7760733"

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

SCORE_RE = re.compile(
    r"Score:\s*([0-9.]+)\s*\\?n?\s*\|\s*(\d+)\s*successes\s*/\s*165"
)


# ---------------------------------------------------------------------------
# Helpers
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
    """Extract canonical full-test-set score events + per-message cumulative cost.

    Reads canonical events from BOTH:
      - trace.jsonl (the agent's own bash score.sh outputs)
      - Claude tmp subagent task-output files (Task-tool subagents' outputs)
    Deduplication: prefer trace events when present; pull tmp events for
    scores that never appear in trace.
    """
    trace_events = []   # (t_min, score, n_succ)
    tmp_events = []     # (t_min, score, n_succ)
    cost_track = []
    cost_acc = 0.0
    seen_trace = set()

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
                    sv = float(m.group(1)); n = int(m.group(2))
                except ValueError:
                    continue
                k = (round(t_min, 1), n)
                if k in seen_trace:
                    continue
                seen_trace.add(k)
                trace_events.append((t_min, sv, n))

    # Pull tmp subagent outputs (mtime-based timing).
    # CLAMP to within the run's actual wall-clock elapsed: tmp file mtimes can
    # lag the actual scoring event by hours (e.g., file written when later
    # agent re-reads the tmp dir), so anything past the trace's last event
    # is treated as a stale write and dropped.
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
                # Use file mtime offset from job start
                t_min = (output_f.stat().st_mtime - job_start_s) / 60.0
                if t_min < 0 or t_min > trace_end_min + 5:  # 5-min slack
                    continue
                for m in SCORE_RE.finditer(txt):
                    try:
                        sv = float(m.group(1)); n = int(m.group(2))
                    except ValueError:
                        continue
                    tmp_events.append((t_min, sv, n))

    # Merge: keep trace events as-is; pull tmp events whose (n_succ) is novel
    trace_n_set = {n for _, _, n in trace_events}
    extra = []
    seen_tmp = set()
    for t, sv, n in sorted(tmp_events):
        if n in trace_n_set:
            continue
        # Allow duplicate n only if separated in time (catch successive plateau hits)
        k = (round(t, 0), n)
        if k in seen_tmp:
            continue
        seen_tmp.add(k)
        extra.append((t, sv, n))

    events = sorted(trace_events + extra)

    # Rescale per-message cost track to the SDK-authoritative metadata total
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


def running_max(values):
    out, b = [], -float("inf")
    for v in values:
        b = max(b, v)
        out.append(b)
    return out


def stitched_ara_trajectory():
    """Stitch ARA parent + resume + score-only into one chronological trajectory."""
    p_evts, p_track, p_cost = parse_run(ARA_PARENT)
    r_evts, r_track, r_cost = parse_run(ARA_RESUME)

    # Anchor parent's wall-clock end (when SLURM TIMEOUT pushback fires)
    parent_t_end = p_track[-1][0] if p_track else (p_evts[-1][0] if p_evts else 0)

    # parent's harness post-agent canonical re-eval (78/165)
    p_final = None
    fs = ARA_PARENT / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text()).get("result", {})
            if "n_successes" in d:
                p_final = (parent_t_end, d["score"], d["n_successes"], p_cost)
        except Exception:
            pass

    # score-only's canonical re-eval (85/165) on the resume's solution_final.py
    so_evt = None
    fs = ARA_SCORE_ONLY / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text()).get("result", {})
            if "n_successes" in d:
                so_evt = (d["score"], d["n_successes"])
        except Exception:
            pass

    pts = []
    # parent's in-trace + tmp events
    for t, s, n in p_evts:
        pts.append((t, s, n, cost_at(p_track, t)))
    if p_final:
        pts.append(p_final)
    # resume events (shift by parent_t_end)
    for t, s, n in r_evts:
        pts.append((parent_t_end + t, s, n, p_cost + cost_at(r_track, t)))
    # score-only at end of resume (free cost)
    if so_evt:
        resume_t_end = r_track[-1][0] if r_track else (r_evts[-1][0] if r_evts else 0)
        s, n = so_evt
        pts.append((parent_t_end + resume_t_end, s, n, p_cost + r_cost))

    # Drop duplicate (t, n) entries
    seen = set(); out = []
    for ev in sorted(pts):
        k = (round(ev[0], 0), ev[2])
        if k in seen:
            continue
        seen.add(k); out.append(ev)
    return out


# ---------------------------------------------------------------------------
# Publication styling (mirrors triton plot)
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

REFERENCE = 21 / 165  # 0.127


def baseline_event(run_dir: pathlib.Path):
    """Return (t_min, score, n_succ, cost) for the harness's pre-agent baseline.
    Anchored at t=0, cost=$0 — the baseline is run by the harness before the
    agent session starts (so it doesn't consume agent budget)."""
    fs = run_dir / "baseline_score.json"
    if not fs.exists():
        return None
    try:
        d = json.loads(fs.read_text()).get("result", {})
        if "n_successes" not in d:
            return None
        return (0.0, d["score"], d["n_successes"], 0.0)
    except Exception:
        return None


def main():
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)

    # ---- paper arm ----
    p_evts, p_track, p_cost_total = parse_run(PAPER_DIR)
    paper_pts = []
    bl = baseline_event(PAPER_DIR)
    if bl:
        paper_pts.append(bl)
    paper_pts.extend((t, s, n, cost_at(p_track, t)) for t, s, n in p_evts)
    fs = PAPER_DIR / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text()).get("result", {})
            if "n_successes" in d:
                # Only add harness final if not already in trace events
                if not any(p[2] == d["n_successes"] and abs(p[0] - p_evts[-1][0]) < 5 for p in paper_pts):
                    t_end = p_track[-1][0] if p_track else (p_evts[-1][0] if p_evts else 0)
                    paper_pts.append((t_end, d["score"], d["n_successes"], p_cost_total))
        except Exception:
            pass
    paper_pts.sort(key=lambda x: x[0])

    # ---- ARA arm (stitched: parent baseline + parent + resume + score-only) ----
    ara_pts = []
    bl = baseline_event(ARA_PARENT)
    if bl:
        ara_pts.append(bl)
    ara_pts.extend(stitched_ara_trajectory())

    # Print summary
    print(f"\n{'arm':<10} {'n_canonical':>11s} canonical events:")
    print(f"{'paper':<10} {len(paper_pts):>11d}")
    for t, s, n, c in paper_pts:
        print(f"             t={t:6.1f}  {s:.4f}  ({n:>3}/165)  cost=${c:.2f}")
    print(f"{'ARA':<10} {len(ara_pts):>11d}")
    for t, s, n, c in ara_pts:
        print(f"             t={t:6.1f}  {s:.4f}  ({n:>3}/165)  cost=${c:.2f}")

    # ---- plot ----
    for label, pts, color, marker in [
        ("paper (Sonnet 4.6)", paper_pts, "#0072B2", "o"),
        ("ARA (Sonnet 4.6)",   ara_pts,   "#D55E00", "s"),
    ]:
        ts = np.array([p[0] for p in pts])
        sv = np.array([p[1] for p in pts])
        cs = np.array([p[3] for p in pts])
        best = np.array(running_max(sv.tolist()))

        # Raw scoring scatter
        ax_t.scatter(ts, sv, s=22, color=color, alpha=0.75, marker=marker,
                     edgecolor="none", zorder=3)
        ax_c.scatter(cs, sv, s=22, color=color, alpha=0.75, marker=marker,
                     edgecolor="none", zorder=3)

        # Best-so-far step line
        ax_t.plot(ts, best, "-", color=color, lw=1.7, zorder=4, label=label)
        ax_c.plot(cs, best, "-", color=color, lw=1.7, zorder=4)

        # Best-attempt star
        i_best = int(np.argmax(sv))
        ax_t.scatter([ts[i_best]], [sv[i_best]], s=110, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)
        ax_c.scatter([cs[i_best]], [sv[i_best]], s=110, color=color, marker="*",
                     edgecolor="black", linewidth=0.5, zorder=5)

    # Reference line + axis bounds
    for ax in (ax_t, ax_c):
        ax.axhline(REFERENCE, color="#888888", ls=":", lw=0.8, zorder=1)
        ax.set_ylabel("score = $n_\\mathrm{solved}/165$\n(higher is better)")
        ax.grid(alpha=0.18)
        ax.set_ylim(0.05, 0.60)

    ax_t.set_xlim(0, 540)   # parent + resume; rust ARA exceeds single-job 8 h
    ax_c.set_xlim(0, 90)
    ax_c.axvline(50, color="#555555", ls=":", lw=0.8, zorder=1)
    ax_c.text(50, 0.56, " \\$50 budget cap", fontsize=6.5, color="#555555",
              ha="left", va="top")

    for ax in (ax_t, ax_c):
        x0, x1 = ax.get_xlim()
        ax.text(x0 + 0.02 * (x1 - x0), REFERENCE + 0.01,
                "RE-Bench reference (0.13)",
                fontsize=6.5, color="#888888", ha="left", va="bottom")

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
        "rust_codecontests: paper vs. ARA on Sonnet 4.6",
        fontsize=10.5, y=1.10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    out_dir = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/paper/shared/figures/extension"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "rust_paper_vs_ara.pdf"
    png_path = out_dir / "rust_paper_vs_ara.png"
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    print(f"\nsaved {pdf_path}\nsaved {png_path}")


if __name__ == "__main__":
    main()
