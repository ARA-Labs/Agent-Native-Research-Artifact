"""rust_codecontests paper s0 sonnet-4-6 (job 7798926) full trajectory.

Plots ONLY full-165-problem scoring runs (no partial 10/15-problem dev tests).
Shows the strategic pivot at t=397min when the agent abandoned pure AI-gen
and started hand-coding Rust solutions to seed its few_shots cache.
Final canonical score: 68/165 (0.412) at t=445min — up from the 39/165
plateau that held from t=183-261min.

For comparison: rust ara s0 (sonnet-4-6) reached 85/165 with the H12
hand-coded SOLUTIONS dict approach handed to it via ARA materials. Paper
agent re-discovered the strategy independently 6.5h into the run.
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_DIR = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs/"
    "rust_codecontests_paper_seed0_job7798926"
)
JOB_ID = 7798926
ARA_BEST = 85          # rust ara s0 final (parent + resume + score-only)
PAPER_BASELINE = 19    # baseline_score.json (reference scaffold on this hardware)
PAPER_PRIOR = 0        # prior paper runs (7241187, 7398543) all 0/165

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

# Canonical: "Score: X | N successes / 165 problems"
SCORE_RE = re.compile(r"Score:\s*([0-9.]+)\s*\\?n?\s*\|\s*(\d+)\s*successes\s*/\s*165")


def collect_full_test_scores():
    events = []
    seen = set()
    trace = RUN_DIR / "trace.jsonl"
    for line in open(trace):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "user": continue
        t = d.get("wall_clock_s", 0) / 60.0
        for m in SCORE_RE.finditer(line):
            try:
                sv = float(m.group(1)); n = int(m.group(2))
            except ValueError: continue
            if not (0 <= n <= 165): continue
            k = (round(t, 1), n)
            if k in seen: continue
            seen.add(k); events.append((t, sv, n))
    events.sort()
    return events


def collect_costs():
    track, acc = [], 0.0
    trace = RUN_DIR / "trace.jsonl"
    for line in open(trace):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "assistant": continue
        u = d.get("usage", {}) or {}
        acc += (u.get("input_tokens", 0) * PRICE["in"]
                + u.get("cache_creation_input_tokens", 0) * PRICE["cache_w"]
                + u.get("cache_read_input_tokens", 0) * PRICE["cache_r"]
                + u.get("output_tokens", 0) * PRICE["out"]) / 1e6
        t = d.get("wall_clock_s")
        if t is not None:
            track.append((t / 60.0, acc))
    return track


def cost_at(track, t):
    if not track: return 0.0
    c = track[0][1]
    for ti, ci in track:
        if ti <= t: c = ci
        else: break
    return c


def detect_pivot(trace_path):
    """Find when the agent first started hand-coding Rust solutions."""
    pivot_t = None
    for line in open(trace_path):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "assistant": continue
        t = d.get("wall_clock_s", 0) / 60.0
        for c in d.get("content", []):
            if not isinstance(c, dict): continue
            r = c.get("repr", "")
            if "name='Bash'" in r:
                cm = re.search(r"'command':\s*'([^']{0,300})", r)
                if cm and re.search(r"cat\s*>\s*/tmp/sol_\d+", cm.group(1)):
                    if pivot_t is None or t < pivot_t:
                        pivot_t = t
                        return pivot_t
    return pivot_t


def main():
    events = collect_full_test_scores()
    track = collect_costs()
    pivot_t = detect_pivot(RUN_DIR / "trace.jsonl")
    final_cost = track[-1][1] if track else 0
    pivot_cost = cost_at(track, pivot_t) if pivot_t else 0

    # Anchor at baseline
    pts = [(0.0, PAPER_BASELINE / 165, PAPER_BASELINE, 0.0)]
    for t, sv, n in events:
        pts.append((t, sv, n, cost_at(track, t)))

    print(f"baseline (reference scaffold): {PAPER_BASELINE}/165 = {PAPER_BASELINE/165:.4f}")
    print(f"strategic pivot to hand-coding: t={pivot_t:.1f}min  cost=${pivot_cost:.2f}")
    print(f"\n{'t_min':>8}  {'score':>7}  {'n/165':>6}  {'cost$':>7}")
    for t, sv, n, c in pts:
        print(f"  {t:7.1f}  {sv:7.4f}  {n:>3}/165  {c:7.2f}")
    print(f"\nfinal best: {max(p[2] for p in pts)}/165")
    print(f"total trace cost: ${final_cost:.2f}")

    # Plot
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    ts = [p[0] for p in pts]
    ss = [p[1] for p in pts]
    cs = [p[3] for p in pts]
    color = "#1f77b4"

    # Baseline marker
    ax_t.scatter([0], [PAPER_BASELINE / 165], s=100, color=color, marker="s",
                 edgecolor="black", linewidth=0.7, zorder=5,
                 label=f"baseline ({PAPER_BASELINE}/165 = {PAPER_BASELINE/165:.3f})")
    ax_c.scatter([0], [PAPER_BASELINE / 165], s=100, color=color, marker="s",
                 edgecolor="black", linewidth=0.7, zorder=5)

    # Scoring runs (5 mid-run + final)
    for i, (t, sv, n, c) in enumerate(pts[1:]):
        is_final = (i == len(pts) - 2)
        marker = "*" if is_final else "o"
        size = 320 if is_final else 110
        label = (f"final scorer run ({n}/165 = {sv:.3f})" if is_final
                 else None if i > 0 else f"mid-run scorer (n={len(pts)-2})")
        ax_t.scatter([t], [sv], s=size, color=color, marker=marker,
                     edgecolor="black", linewidth=0.7, zorder=6, label=label)
        ax_c.scatter([c], [sv], s=size, color=color, marker=marker,
                     edgecolor="black", linewidth=0.7, zorder=6)

    # Best-so-far line
    best_curve = []
    cur = -1
    for t, sv, n, c in pts:
        cur = max(cur, sv)
        best_curve.append(cur)
    ax_t.plot(ts, best_curve, "-", color=color, lw=2, alpha=0.95)
    ax_c.plot(cs, best_curve, "-", color=color, lw=2, alpha=0.95)

    # Pivot marker
    if pivot_t:
        ax_t.axvline(pivot_t, color="orange", ls=":", lw=1.5, alpha=0.7,
                     label=f"hand-coding pivot (t={pivot_t:.0f}min)")
        ax_c.axvline(pivot_cost, color="orange", ls=":", lw=1.5, alpha=0.7,
                     label=f"hand-coding pivot (${pivot_cost:.0f})")

    # Comparison anchors
    for ax in (ax_t, ax_c):
        ax.axhline(ARA_BEST / 165, color="green", ls="--", lw=1, alpha=0.7,
                   label=f"ara s0 final ({ARA_BEST}/165 = {ARA_BEST/165:.3f})")
        ax.axhline(PAPER_PRIOR / 165, color="red", ls=":", lw=1, alpha=0.5,
                   label=f"prior paper runs (0/165)")
        ax.set_ylabel("score = n_successes / 165 (higher is better)")
        ax.grid(alpha=0.3)
        ax.set_ylim(-0.02, 0.55)

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Score vs cumulative cost")
    ax_t.legend(loc="upper left", fontsize=8, framealpha=0.92)
    ax_c.legend(loc="upper left", fontsize=8, framealpha=0.92)

    fig.suptitle(
        "rust_codecontests — sonnet-4-6, paper s0 (job 7798926)\n"
        f"6 full-test-set scoring runs over 8h. Plateau at 39/165 (~4h) until "
        f"agent re-discovered hand-coding strategy at t={pivot_t:.0f}min, "
        f"jumping to 68/165 by t=445min. Compare ara s0 final = 85/165 (with H12 in materials).",
        fontsize=10,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "rust_paper_46_s0_full_trajectory.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"\nsaved {out_path}")


if __name__ == "__main__":
    main()
