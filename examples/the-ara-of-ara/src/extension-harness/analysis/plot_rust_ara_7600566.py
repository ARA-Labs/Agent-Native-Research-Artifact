"""Plot rust ara 7600566 (sonnet-4-6) score trajectory vs time and cost.

Context: this is the first rust run to meaningfully beat reference 0.13.
Final score 0.473 came from implementing H12 (hand-coded Rust solution
library) from the ARA exploration tree.
"""
import datetime, json, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/"
    "extension-runs/rust_codecontests_ara_seed0_job7600566"
)
TMP_WD = pathlib.Path(
    "/n/home04/zechenzhang/.claude/tmp/claude-62233/"
    "-n-netscratch-sompolinsky-lab-Everyone-zechenzhang-ara-project-"
    "extension-runs-rust-codecontests-ara-seed0-job7600566-workdir"
)

# Job start time
start = datetime.datetime.fromisoformat(
    subprocess.run(["sacct", "-j", "7600566", "--format=Start", "-n"],
                   capture_output=True, text=True).stdout.strip().split("\n")[0].strip()
).timestamp()


def collect_scores():
    """Return [(offset_min, score, n_successes)] from all known sources."""
    events = []
    # 1. Harness baseline (pre-agent) from slurm log
    log = pathlib.Path(f"/n/home04/zechenzhang/ara-project/slurm_logs/ext_rust_7600566.out")
    if log.exists():
        text = log.read_text()
        m = re.search(r"baseline ok=True result=\{'score':\s*([\d.]+),"
                      r"\s*'n_problems':\s*(\d+),\s*'n_successes':\s*(\d+)", text)
        if m:
            # baseline runs right after job start, assume ~25min
            events.append((25.0, float(m.group(1)), int(m.group(3)), "baseline"))

    # 2. Trace.jsonl "Score: X | N successes"
    trace = RUN / "trace.jsonl"
    rx = re.compile(r"Score:\s*([\d.]+)\s*\|\s*(\d+)\s*successes")
    for l in open(trace):
        m = rx.search(l)
        if m:
            try:
                ev = json.loads(l)
                t = ev.get("wall_clock_s", 0) / 60.0
            except Exception:
                t = 0
            events.append((t + 25.0, float(m.group(1)), int(m.group(2)), "trace"))  # +25 for baseline offset

    # 3. Task-output files (full-test scores) — use mtime offset from job start
    tasks_dir = next(TMP_WD.glob("*/tasks"), None)
    if tasks_dir:
        rx_json = re.compile(r'"score":\s*([\d.]+),\s*"n_problems":\s*165,\s*"n_successes":\s*(\d+)')
        seen = set()
        for f in sorted(tasks_dir.glob("*.output"), key=lambda x: x.stat().st_mtime):
            try:
                text = f.read_text(errors="ignore")
            except Exception:
                continue
            for m in rx_json.finditer(text):
                key = (f.name, m.group(1), m.group(2))
                if key in seen:
                    continue
                seen.add(key)
                off = (f.stat().st_mtime - start) / 60.0
                events.append((off, float(m.group(1)), int(m.group(2)), "task"))

    # 4. Harness final score
    fs = RUN / "final_score.json"
    if fs.exists():
        d = json.loads(fs.read_text())
        r = d.get("result", d)
        elapsed = subprocess.run(
            ["sacct", "-j", "7600566", "--format=Elapsed", "-n"],
            capture_output=True, text=True
        ).stdout.strip().split("\n")[0].strip()
        # Elapsed like "05:42:53"
        h, m, s = (int(x) for x in elapsed.split(":"))
        off = h * 60 + m + s / 60.0
        events.append((off, r.get("score"), r.get("n_successes"), "final"))

    events.sort()
    return events


def main():
    events = collect_scores()
    print(f"{'t(min)':>10s}  {'score':>7s}  {'n_succ':>6s}  source")
    for t, s, n, src in events:
        print(f"  {t:8.1f}  {s:7.4f}  {n:>6d}  {src}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # --- time axis ---
    ts = [e[0] for e in events]
    ss = [e[1] for e in events]
    srcs = [e[3] for e in events]

    # running max (rust: higher is better)
    best = []
    b = -float("inf")
    for s in ss:
        b = max(b, s)
        best.append(b)

    colors = {"baseline": "#888888", "trace": "#1f77b4",
              "task": "#2ca02c", "final": "#d62728"}
    for src in set(srcs):
        xs = [t for t, s in zip(ts, ss) if srcs[ts.index(t)] == src]
        ys = [s for t, s in zip(ts, ss) if srcs[ts.index(t)] == src]
        ax1.scatter(xs, ys, s=60, color=colors[src], label=src, zorder=3)
    ax1.plot(ts, best, "-", color="#ff7f0e", lw=2, label="best-so-far", zorder=2)
    ax1.axhline(0.127, color="red", ls="--", lw=1, label="reference 0.127")
    ax1.axhline(0.097, color="orange", ls=":", lw=1, label="prior MALT best 0.097")
    ax1.set_xlabel("wall-clock minutes")
    ax1.set_ylabel("score = n_successes / 165")
    ax1.set_title("rust ara 7600566: score over time")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=9)

    # --- cost axis (approx from metadata) ---
    meta = json.loads((RUN / "metadata.json").read_text())
    final_cost = meta["agent"]["total_cost_usd"]
    # linear approx: cost scales with time
    max_t = max(ts) if ts else 1
    costs = [t / max_t * final_cost for t in ts]

    for src in set(srcs):
        xs = [c for c, src_ in zip(costs, srcs) if src_ == src]
        ys = [s for s, src_ in zip(ss, srcs) if src_ == src]
        ax2.scatter(xs, ys, s=60, color=colors[src], label=src, zorder=3)
    best2 = best
    ax2.plot(costs, best2, "-", color="#ff7f0e", lw=2, label="best-so-far", zorder=2)
    ax2.axhline(0.127, color="red", ls="--", lw=1)
    ax2.axhline(0.097, color="orange", ls=":", lw=1)
    ax2.set_xlabel(f"cumulative cost (USD; total ${final_cost:.2f})")
    ax2.set_ylabel("score")
    ax2.set_title("rust ara 7600566: score vs cost (approx)")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=9)

    fig.suptitle(
        f"rust_codecontests ara s0 sonnet-4-6 "
        f"(final 0.473 = 78/165, 3.6× reference 0.13)",
        fontsize=11,
    )
    fig.tight_layout()

    out = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "rust_ara_7600566.png"
    )
    fig.savefig(out, dpi=150)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
