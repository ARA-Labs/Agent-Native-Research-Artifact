"""rust_codecontests ara s0 (sonnet-4-6) full trajectory: parent + resume + score-only.

Stitches three jobs into a single trajectory:
  - Parent  7600566 — built SOLUTIONS library, official 78/165
  - Resume  7720567 — added 6 hand-coded solutions, in-trace 79/165 + estimate ~82-83
  - Score-only 7760733 — confirmed 85/165 official on resume's solution_final.py
                         (ran on the resume workdir; no agent cost)

Time axis: wall-clock minutes from parent job start.
Cost axis: cumulative USD across parent + resume (score-only is free of agent cost).
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)

PARENT = "rust_codecontests_ara_seed0_job7600566"
RESUME = "rust_codecontests_ara_seed0_resume_job7720567"
SCORE_ONLY = "rust_codecontests_ara_seed0_job7600566/score_only_job7760733"

PARENT_JOB = 7600566
RESUME_JOB = 7720567
SCORE_JOB = 7760733

REFERENCE = 0.127  # task baseline (gpt-3.5 + simple loop)
HUMAN_BEST = 0.51  # ~84/165 from RE-Bench human runs
PRIOR_MALT_BEST = 0.097  # 16/165 from MALT extraction history

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}


def sacct(job_id, field):
    return subprocess.run(
        ["sacct", "-j", str(job_id), f"--format={field}", "-n", "-X"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[0].strip()


def elapsed_min(job_id):
    e = sacct(job_id, "Elapsed")
    h, m, s = (int(x) for x in e.split(":"))
    return h * 60 + m + s / 60.0


def collect_trace_scores(run_dir):
    """Pull explicit Score: X | N successes lines from a run's trace.jsonl."""
    events = []
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return events
    rx = re.compile(r"Score:\s*([0-9.]+)\s*\\?n?\s*\|\s*(\d+)\s*successes")
    seen = set()
    for line in open(trace):
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("wall_clock_s", 0) / 60.0
        for m in rx.finditer(line):
            sv, n = float(m.group(1)), int(m.group(2))
            k = (round(t, 1), n)
            if k in seen:
                continue
            seen.add(k)
            events.append((t, sv, n))
    events.sort()
    return events


def collect_cost_track(run_dir):
    """Cumulative cost in USD over time from per-message usage in trace.jsonl,
    rescaled to metadata.json total_cost_usd if available."""
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return []
    track, acc = [], 0.0
    for line in open(trace):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant":
            continue
        u = d.get("usage", {}) or {}
        acc += (u.get("input_tokens", 0) * PRICE["in"]
                + u.get("cache_creation_input_tokens", 0) * PRICE["cache_w"]
                + u.get("cache_read_input_tokens", 0) * PRICE["cache_r"]
                + u.get("output_tokens", 0) * PRICE["out"]) / 1e6
        t = d.get("wall_clock_s")
        if t is not None:
            track.append((t / 60.0, acc))
    meta = run_dir / "metadata.json"
    if meta.exists() and acc > 0:
        try:
            final_cost = json.loads(meta.read_text())["agent"]["total_cost_usd"]
            if final_cost:
                scale = final_cost / acc
                track = [(t, c * scale) for t, c in track]
        except Exception:
            pass
    return track


def cost_at(track, t):
    if not track:
        return 0.0
    c = track[0][1]
    for ti, ci in track:
        if ti <= t:
            c = ci
        else:
            break
    return c


def main():
    parent_dir = RUN_ROOT / PARENT
    resume_dir = RUN_ROOT / RESUME
    score_dir = RUN_ROOT / SCORE_ONLY

    parent_evts = collect_trace_scores(parent_dir)
    parent_track = collect_cost_track(parent_dir)
    parent_elapsed = elapsed_min(PARENT_JOB)
    parent_final_cost = cost_at(parent_track, parent_elapsed) or (
        json.loads((parent_dir / "metadata.json").read_text())["agent"]["total_cost_usd"]
        if (parent_dir / "metadata.json").exists() else 0
    )

    # Parent's official final score
    parent_final = None
    fs = parent_dir / "final_score.json"
    if fs.exists():
        d = json.loads(fs.read_text())
        r = d.get("result", d)
        parent_final = (parent_elapsed, r["score"], r["n_successes"])

    resume_evts = collect_trace_scores(resume_dir)
    resume_track = collect_cost_track(resume_dir)
    resume_elapsed = elapsed_min(RESUME_JOB)

    # Score-only result: officially-confirmed final (no agent cost added)
    score_only_evt = None
    fs = score_dir / "final_score.json"
    if fs.exists():
        d = json.loads(fs.read_text())
        r = d.get("result", d)
        score_only_evt = (resume_elapsed, r["score"], r["n_successes"])

    # Stitch: shift resume timestamps & costs by parent's final
    def shift_t(t):
        return t + parent_elapsed

    def shift_c(t):
        return parent_final_cost + cost_at(resume_track, t)

    # Build unified per-source event lists with (t_min, score, n, cost_usd)
    parent_pts = [(t, s, n, cost_at(parent_track, t)) for t, s, n in parent_evts]
    resume_pts = [(shift_t(t), s, n, shift_c(t)) for t, s, n in resume_evts]
    parent_final_pt = ((parent_final[0], parent_final[1], parent_final[2], parent_final_cost)
                       if parent_final else None)
    score_only_pt = None
    if score_only_evt:
        # cost: parent + resume total (score-only itself adds no agent cost)
        resume_total_cost = (
            json.loads((resume_dir / "metadata.json").read_text())["agent"]["total_cost_usd"]
            if (resume_dir / "metadata.json").exists() else cost_at(resume_track, resume_elapsed)
        )
        total = parent_final_cost + resume_total_cost
        score_only_pt = (parent_elapsed + resume_elapsed, score_only_evt[1], score_only_evt[2], total)

    # ---- print summary ----
    print(f"{'src':<14} {'t_min':>8} {'score':>7} {'n/165':>7} {'cost$':>7}")
    for src, pts in [("parent.trace", parent_pts), ("resume.trace", resume_pts)]:
        for t, s, n, c in pts:
            print(f"{src:<14} {t:8.1f} {s:7.4f} {n:>4}/165 {c:7.2f}")
    if parent_final_pt:
        t, s, n, c = parent_final_pt
        print(f"{'parent.FINAL':<14} {t:8.1f} {s:7.4f} {n:>4}/165 {c:7.2f}")
    if score_only_pt:
        t, s, n, c = score_only_pt
        print(f"{'SCORE-ONLY':<14} {t:8.1f} {s:7.4f} {n:>4}/165 {c:7.2f}")

    # ---- combined best-so-far across all sources, in chronological order ----
    all_pts = list(parent_pts) + list(resume_pts)
    if parent_final_pt:
        all_pts.append(parent_final_pt)
    if score_only_pt:
        all_pts.append(score_only_pt)
    all_pts.sort(key=lambda x: x[0])
    best, b = [], -float("inf")
    for _, s, _, _ in all_pts:
        b = max(b, s)
        best.append(b)
    ts_all = [p[0] for p in all_pts]
    cs_all = [p[3] for p in all_pts]

    # ---- plot ----
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

    def scatter(ax, pts, color, marker, size, label, edge=False):
        if not pts:
            return
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        kw = dict(color=color, marker=marker, s=size, label=label, alpha=0.85, zorder=4)
        if edge:
            kw["edgecolor"] = "black"; kw["linewidth"] = 0.7
        ax.scatter(x, y, **kw)

    def scatter_c(ax, pts, color, marker, size, edge=False):
        if not pts:
            return
        x = [p[3] for p in pts]
        y = [p[1] for p in pts]
        kw = dict(color=color, marker=marker, s=size, alpha=0.85, zorder=4)
        if edge:
            kw["edgecolor"] = "black"; kw["linewidth"] = 0.7
        ax.scatter(x, y, **kw)

    # Parent trace
    scatter(ax_t, parent_pts, "#1f77b4", "o", 50,
            f"parent scorer (n={len(parent_pts)})", edge=True)
    scatter_c(ax_c, parent_pts, "#1f77b4", "o", 50, edge=True)
    # Parent final (official 78/165)
    if parent_final_pt:
        scatter(ax_t, [parent_final_pt], "#1f77b4", "*", 280,
                f"parent FINAL ({parent_final_pt[2]}/165)", edge=True)
        scatter_c(ax_c, [parent_final_pt], "#1f77b4", "*", 280, edge=True)
    # Resume trace
    scatter(ax_t, resume_pts, "#ff7f0e", "o", 70,
            f"resume scorer (n={len(resume_pts)})", edge=True)
    scatter_c(ax_c, resume_pts, "#ff7f0e", "o", 70, edge=True)
    # Score-only confirmation
    if score_only_pt:
        scatter(ax_t, [score_only_pt], "#d62728", "*", 380,
                f"OFFICIAL FINAL ({score_only_pt[2]}/165 from score-only)", edge=True)
        scatter_c(ax_c, [score_only_pt], "#d62728", "*", 380, edge=True)

    # Best-so-far line
    ax_t.plot(ts_all, best, "-", color="#2ca02c", lw=2, alpha=0.9, label="best-so-far")
    ax_c.plot(cs_all, best, "-", color="#2ca02c", lw=2, alpha=0.9, label="best-so-far")

    # Resume boundary
    ax_t.axvline(parent_elapsed, color="gray", ls=":", lw=1, alpha=0.6,
                 label=f"resume boundary (t={parent_elapsed:.0f}min)")
    ax_c.axvline(parent_final_cost, color="gray", ls=":", lw=1, alpha=0.6,
                 label=f"resume boundary (cost=${parent_final_cost:.2f})")

    for ax in (ax_t, ax_c):
        ax.axhline(REFERENCE, color="red", ls="--", lw=1,
                   label=f"task reference ({REFERENCE:.3f})")
        ax.axhline(PRIOR_MALT_BEST, color="orange", ls=":", lw=1,
                   label=f"prior MALT best ({PRIOR_MALT_BEST:.3f})")
        ax.axhline(HUMAN_BEST, color="green", ls="-.", lw=1, alpha=0.7,
                   label=f"~human best ({HUMAN_BEST:.2f}, ~84/165)")
        ax.set_ylabel("score = n_successes / 165 (higher is better)")
        ax.grid(alpha=0.3)

    ax_t.set_xlabel("wall-clock minutes (parent + resume)")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Score vs cumulative cost")
    ax_t.legend(loc="lower right", fontsize=7.5, framealpha=0.92)
    ax_c.legend(loc="lower right", fontsize=7.5, framealpha=0.92)

    fig.suptitle(
        "rust_codecontests — sonnet-4-6, ara s0 full trajectory\n"
        f"parent 7600566 → 78/165 (TIMEOUT pushback) → resume 7720567 added 6 solutions "
        f"→ score-only 7760733 confirmed 85/165 (+7 problems, +9% absolute)",
        fontsize=10,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "rust_ara_46_full_trajectory.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"\nsaved {out_path}")


if __name__ == "__main__":
    main()
