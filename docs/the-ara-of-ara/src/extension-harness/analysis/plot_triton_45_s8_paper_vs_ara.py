"""triton_cumsum sonnet-4-5 seed 8 paper vs ara: score history vs time/cost.

Both runs submitted 2026-04-24 with the new harness fixes (16MB SDK buffer,
PreToolUse Bash hook rejecting `for i in {1..N>10}` mass-batch scoring loops,
200G mem / 26 cpu sbatch). Both ran the full 8h cleanly (TIMEOUT but agent
active throughout, no SDK crashes).

paper s8 7982788 best 0.6277 (1.873ms) — beats reference 0.6388 by ~1.7%
ara   s8 7982791 best 0.2717 (1.314ms) — 57% relative speedup over reference,
                                          biggest triton ara breakthrough we've seen
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)

JOBS = {
    "paper s8 (7982788)": ("triton_cumsum_paper_seed8_job7982788", 7982788, "#1f77b4"),
    "ara s8   (7982791)": ("triton_cumsum_ara_seed8_job7982791",   7982791, "#ff7f0e"),
}

REFERENCE = 0.6388  # task-defined reference score (~1.6ms)
HUMAN_BEST = 0.0    # not formally established for triton; agents have far exceeded ref

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

# Canonical: {"score": X, "message": {... "torch_time_ms": Y, "solution_time_ms": Z}}
CANONICAL_RE = re.compile(
    r'\\"score\\":\s*([0-9.]+|NaN)[^}]{0,400}solution_time_ms\\":\s*([0-9.]+)'
)


def sacct_field(job_id, field):
    return subprocess.run(
        ["sacct", "-j", str(job_id), f"--format={field}", "-n", "-X"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[0].strip()


def elapsed_min(job_id):
    e = sacct_field(job_id, "Elapsed")
    parts = e.split(":")
    h, m, s = (int(x) for x in parts)
    return h * 60 + m + s / 60.0


def collect_scores(run_dir):
    events = []; seen = set()
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return events
    for line in open(trace):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "user":
            continue
        t = d.get("wall_clock_s", 0) / 60.0
        for m in CANONICAL_RE.finditer(line):
            sv_str = m.group(1)
            if sv_str == "NaN": continue
            try:
                sv = float(sv_str); ms = float(m.group(2))
            except ValueError: continue
            if sv > 5: continue  # broken-model regression cap
            k = (round(t, 1), round(sv, 4))
            if k in seen: continue
            seen.add(k); events.append((t, sv, ms))
    events.sort()
    return events


def collect_costs(run_dir):
    trace = run_dir / "trace.jsonl"
    if not trace.exists(): return []
    track, acc = [], 0.0
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


def collect_hook_blocks(run_dir):
    """Times when the PreToolUse Bash hook rejected a mass-batch command."""
    blocks = []
    trace = run_dir / "trace.jsonl"
    if not trace.exists(): return blocks
    for line in open(trace):
        try: d = json.loads(line)
        except Exception: continue
        t = d.get("wall_clock_s", 0) / 60.0
        if "BLOCKED:" in line and "for ... 1.." in line:
            m = re.search(r"for \.\.\. 1\.\.(\d+)", line)
            if m:
                blocks.append((t, int(m.group(1))))
    seen = set(); uniq = []
    for t, n in blocks:
        k = (round(t, 1), n)
        if k in seen: continue
        seen.add(k); uniq.append((t, n))
    return uniq


def baseline_score(run_dir):
    bs = run_dir / "baseline_score.json"
    if bs.exists():
        try:
            d = json.loads(bs.read_text())
            return d.get("result", {}).get("score")
        except Exception: pass
    return None


def running_min(vs):
    out, b = [], float("inf")
    for v in vs:
        b = min(b, v); out.append(b)
    return out


def main():
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

    for label, (run_name, job_id, color) in JOBS.items():
        run_dir = RUN_ROOT / run_name
        events = collect_scores(run_dir)
        costs = collect_costs(run_dir)
        blocks = collect_hook_blocks(run_dir)
        baseline = baseline_score(run_dir)
        end_min = elapsed_min(job_id)

        # Anchor at baseline (t=0)
        anchor = (0.0, baseline if baseline else REFERENCE)
        all_pts = [anchor] + [(t, s) for t, s, _ in events]
        ts = [p[0] for p in all_pts]
        ss = [p[1] for p in all_pts]
        cs = [cost_at(costs, t) for t in ts]
        best = running_min(ss)

        # Show ALL scoring attempts (1000+ noise samples and all)
        if events:
            e_t = [t for t, _, _ in events]
            e_s = [s for _, s, _ in events]
            e_c = [cost_at(costs, t) for t in e_t]
            ax_t.scatter(e_t, e_s, s=8, color=color, alpha=0.12, marker=".",
                         label=f"{label} attempts (n={len(events)})")
            ax_c.scatter(e_c, e_s, s=8, color=color, alpha=0.12, marker=".")

        # Best-so-far line
        ax_t.plot(ts, best, "-", color=color, lw=2, alpha=0.95)
        ax_c.plot(cs, best, "-", color=color, lw=2, alpha=0.95)

        # Baseline anchor square
        ax_t.scatter([0], [anchor[1]], s=85, color=color, marker="s",
                     edgecolor="black", linewidth=0.5, zorder=5,
                     label=f"{label} baseline ({anchor[1]:.4f})")
        ax_c.scatter([0], [anchor[1]], s=85, color=color, marker="s",
                     edgecolor="black", linewidth=0.5, zorder=5)

        # Best-attempt star
        if events:
            best_attempt = min(events, key=lambda x: x[1])
            ax_t.scatter([best_attempt[0]], [best_attempt[1]], s=320, color=color,
                         marker="*", edgecolor="black", linewidth=0.7, zorder=6,
                         label=f"{label} best ({best_attempt[1]:.4f}, {best_attempt[2]:.3f}ms)")
            ax_c.scatter([cost_at(costs, best_attempt[0])], [best_attempt[1]], s=320,
                         color=color, marker="*", edgecolor="black", linewidth=0.7, zorder=6)

        # Hook blocks (X markers)
        for bt, bn in blocks:
            bc = cost_at(costs, bt)
            ax_t.scatter([bt], [anchor[1] + 0.3], s=80, color=color, marker="x",
                         linewidth=2, alpha=0.7)
            ax_c.scatter([bc], [anchor[1] + 0.3], s=80, color=color, marker="x",
                         linewidth=2, alpha=0.7)

        print(f"{label:24s}  baseline={anchor[1]:.4f}  n_attempts={len(events)}  "
              f"best={min((s for _, s, _ in events), default=float('nan')):.4f}  "
              f"hook_blocks={len(blocks)}  end_min={end_min:.1f}  "
              f"cost=${cost_at(costs, end_min):.2f}")

    for ax in (ax_t, ax_c):
        ax.axhline(REFERENCE, color="red", ls="--", lw=1,
                   label=f"reference ({REFERENCE:.4f})")
        ax.set_ylabel("score = log(time_ms) — lower is better")
        ax.grid(alpha=0.3)
        ax.set_ylim(0.20, 0.75)

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Score vs cost")
    ax_t.legend(loc="upper right", fontsize=7.5, framealpha=0.92)
    ax_c.legend(loc="upper right", fontsize=7.5, framealpha=0.92)

    fig.suptitle(
        "triton_cumsum — sonnet-4-5, paper s8 (7982788) vs ara s8 (7982791)\n"
        "square = baseline; dots = scoring attempts; line = best-so-far; star = best; × = bash mass-batch hook block.\n"
        "ara discovered a kernel-level breakthrough at ~1h (0.27, 57% speedup vs ref); paper found small autotune gains (0.63, ~1.7% better than ref).",
        fontsize=10,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "triton_45_s8_paper_vs_ara.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"\nsaved {out_path}")


if __name__ == "__main__":
    main()
