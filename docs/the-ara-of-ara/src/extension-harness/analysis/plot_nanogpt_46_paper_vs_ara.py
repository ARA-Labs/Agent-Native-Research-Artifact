"""nanogpt_chat_rl sonnet-4-6 paper-vs-ara trajectory.

Paper s0 lineage: original 7517443 (finished 0.609) + resume 7723617 (finished 0.7432).
Ara s0:           7077234 (finished 0.830, the only ara sonnet-4-6 run).

Score trajectory is sparse: nanogpt scoring is expensive (~$0.4/call, 3-7min wall),
so each agent only ran score.sh a handful of times. We extract:
  - explicit Score: 0.X mentions in agent text/tool-output (with dedupe by t,score)
  - the harness-recorded final score
  - implicit baseline 0.616 (un-tuned gpt2-xl on the same 60-token chat task)
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)

# Run info: (label, run_dir_name, job_id, color, is_resume_of_label)
PAPER_PARENT = ("paper s0 (7517443)", "nanogpt_chat_rl_paper_seed0_job7517443", 7517443, "#1f77b4")
PAPER_RESUME = ("paper resume (7723617)", "nanogpt_chat_rl_paper_seed0_resume_job7723617", 7723617, "#1f77b4")
ARA = ("ara s0 (7077234)", "nanogpt_chat_rl_ara_seed0_job7077234", 7077234, "#ff7f0e")

BASELINE = 0.616      # un-tuned gpt2-xl finetuned_model starting point (per agent text)
REFERENCE = 0.85      # official scaffold solution
HUMAN_BEST = 0.97     # RE-Bench human ceiling

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}


def sacct_field(job_id, field):
    return subprocess.run(
        ["sacct", "-j", str(job_id), f"--format={field}", "-n", "-X"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[0].strip()


def elapsed_min(job_id):
    e = sacct_field(job_id, "Elapsed")
    parts = e.split(":")
    if len(parts) == 3:
        h, m, s = (int(x) for x in parts)
    elif len(parts) == 4:  # day-hh:mm:ss
        d, h, m = int(parts[0].split("-")[0]), int(parts[0].split("-")[1]), int(parts[1])
        s = int(parts[2])
        return d * 1440 + h * 60 + m + s / 60
    return h * 60 + m + s / 60.0


def collect_scores(run_dir):
    """Extract every REAL score.py invocation that returned a score.
    Looks ONLY in user (tool_result) messages for either:
      (a) canonical JSON: {"score": X, "message": {"win_vs_gpt2-alpaca": ...}}
      (b) [score] overall win rate: X
    Both come directly from score.py output, never from agent text/plans.
    Returns list[(t_min, score)] of actual completed scoring submissions.
    """
    events = []
    seen = set()
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return events
    rxs = [
        re.compile(r'\\?"score\\?":\s*([0-9.]+)[^}]{0,400}win_vs_gpt2-alpaca'),
        re.compile(r'\[score\][\\\\\s]*overall win rate:\s*([0-9.]+)'),
    ]
    for line in open(trace):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "user":
            continue
        t = d.get("wall_clock_s", 0) / 60.0
        for rx in rxs:
            for m in rx.finditer(line):
                try:
                    sv = float(m.group(1))
                except ValueError:
                    continue
                if not (0.05 <= sv <= 1):
                    continue
                k = (round(t, 1), round(sv, 4))
                if k in seen:
                    continue
                seen.add(k)
                events.append((t, sv))
    events.sort()
    return events


def collect_costs(run_dir):
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
            final_cost = json.loads(meta.read_text())["agent"].get("total_cost_usd", 0)
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


def harness_final(run_dir, end_min):
    fs = run_dir / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text())
            r = d.get("result", d)
            return (end_min, r.get("score"))
        except Exception:
            pass
    return None


def running_max(vs):
    out, b = [], -float("inf")
    for v in vs:
        b = max(b, v)
        out.append(b)
    return out


def main():
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

    # ---- Ara (single run, no resume) ----
    ara_label, ara_name, ara_job, ara_color = ARA
    ara_dir = RUN_ROOT / ara_name
    ara_evts = collect_scores(ara_dir)
    ara_track = collect_costs(ara_dir)
    ara_elapsed = elapsed_min(ara_job)
    ara_final = harness_final(ara_dir, ara_elapsed)

    # ---- Paper parent + resume ----
    pp_label, pp_name, pp_job, pp_color = PAPER_PARENT
    pr_label, pr_name, pr_job, _ = PAPER_RESUME
    pp_dir = RUN_ROOT / pp_name
    pr_dir = RUN_ROOT / pr_name

    pp_evts = collect_scores(pp_dir)
    pp_track = collect_costs(pp_dir)
    pp_elapsed = elapsed_min(pp_job)
    pp_final = harness_final(pp_dir, pp_elapsed)
    pp_total_cost = (json.loads((pp_dir / "metadata.json").read_text())["agent"]["total_cost_usd"]
                     if (pp_dir / "metadata.json").exists() else 0)

    pr_evts = collect_scores(pr_dir)
    pr_track = collect_costs(pr_dir)
    pr_elapsed = elapsed_min(pr_job)
    pr_final = harness_final(pr_dir, pr_elapsed)

    def shift_t(t): return t + pp_elapsed
    def shift_c(t): return pp_total_cost + cost_at(pr_track, t)

    # Paper combined trajectory: baseline anchor + parent submissions + parent final + resume submissions + resume final
    paper_pts = [(0, BASELINE, 0)]
    paper_pts += [(t, s, cost_at(pp_track, t)) for t, s in pp_evts]
    if pp_final:
        paper_pts.append((pp_final[0], pp_final[1], pp_total_cost))
    paper_pts += [(shift_t(t), s, shift_c(t)) for t, s in pr_evts]
    if pr_final:
        paper_pts.append((shift_t(pr_final[0]), pr_final[1], shift_c(pr_final[0])))
    paper_pts.sort(key=lambda x: x[0])

    ara_pts = [(0, BASELINE, 0)]
    ara_pts += [(t, s, cost_at(ara_track, t)) for t, s in ara_evts]
    if ara_final:
        ara_total_cost = (json.loads((ara_dir / "metadata.json").read_text())["agent"]["total_cost_usd"]
                          if (ara_dir / "metadata.json").exists() else 0)
        ara_pts.append((ara_final[0], ara_final[1], ara_total_cost))
    ara_pts.sort(key=lambda x: x[0])

    # ---- print summary ----
    print(f"\n=== PAPER score submissions (parent + resume) ===  n={len(paper_pts)-1}")
    for t, s, c in paper_pts:
        kind = "baseline" if (t == 0) else ("FINAL" if (s in {pp_final[1] if pp_final else None, pr_final[1] if pr_final else None}) else "score.sh")
        print(f"  t={t:7.1f}min  score={s:.4f}  cost=${c:.2f}  [{kind}]")
    print(f"\n=== ARA score submissions ===  n={len(ara_pts)-1}")
    for t, s, c in ara_pts:
        kind = "baseline" if (t == 0) else ("FINAL" if (ara_final and s == ara_final[1] and t == ara_final[0]) else "score.sh")
        print(f"  t={t:7.1f}min  score={s:.4f}  cost=${c:.2f}  [{kind}]")

    # ---- plot ----
    def plot_arm(pts, color, label, ax_t_, ax_c_, final_t):
        ts = [p[0] for p in pts]
        ss = [p[1] for p in pts]
        cs = [p[2] for p in pts]
        best = running_max(ss)
        # Separate baseline (t=0), score.sh runs (intermediate), and harness FINAL (specific t)
        baseline_idx = [i for i, t in enumerate(ts) if t == 0]
        final_idx = [i for i, t in enumerate(ts) if t == final_t]
        attempt_idx = [i for i in range(len(ts)) if i not in baseline_idx and i not in final_idx]
        # Baseline square
        for i in baseline_idx:
            ax_t_.scatter([ts[i]], [ss[i]], s=85, color=color, marker="s",
                          edgecolor="black", linewidth=0.6, zorder=5)
            ax_c_.scatter([cs[i]], [ss[i]], s=85, color=color, marker="s",
                          edgecolor="black", linewidth=0.6, zorder=5)
        # Score.sh attempt circles
        ax_t_.scatter([ts[i] for i in attempt_idx], [ss[i] for i in attempt_idx],
                      s=80, color=color, marker="o", edgecolor="black", linewidth=0.6,
                      alpha=0.9, zorder=4,
                      label=f"{label} score.sh runs (n={len(attempt_idx)})")
        ax_c_.scatter([cs[i] for i in attempt_idx], [ss[i] for i in attempt_idx],
                      s=80, color=color, marker="o", edgecolor="black", linewidth=0.6,
                      alpha=0.9, zorder=4)
        # Final star
        for i in final_idx:
            ax_t_.scatter([ts[i]], [ss[i]], s=320, color=color, marker="*",
                          edgecolor="black", linewidth=0.7, zorder=6,
                          label=f"{label} harness FINAL ({ss[i]:.4f})")
            ax_c_.scatter([cs[i]], [ss[i]], s=320, color=color, marker="*",
                          edgecolor="black", linewidth=0.7, zorder=6)
        ax_t_.plot(ts, best, "-", color=color, lw=2, alpha=0.95)
        ax_c_.plot(cs, best, "-", color=color, lw=2, alpha=0.95)

    paper_final_t = shift_t(pr_final[0]) if pr_final else (pp_final[0] if pp_final else None)
    plot_arm(paper_pts, pp_color, "paper s0 (orig+resume)", ax_t, ax_c, paper_final_t)
    plot_arm(ara_pts, ara_color, ARA[0], ax_t, ax_c, ara_final[0] if ara_final else None)

    # Resume boundary on paper
    ax_t.axvline(pp_elapsed, color=pp_color, ls=":", lw=1, alpha=0.5,
                 label=f"paper resume boundary (t={pp_elapsed:.0f}min)")
    ax_c.axvline(pp_total_cost, color=pp_color, ls=":", lw=1, alpha=0.5,
                 label=f"paper resume boundary (cost=${pp_total_cost:.2f})")

    for ax in (ax_t, ax_c):
        ax.axhline(BASELINE, color="gray", ls="-.", lw=1, alpha=0.5,
                   label=f"baseline ({BASELINE:.3f})")
        ax.axhline(REFERENCE, color="red", ls="--", lw=1,
                   label=f"official ref ({REFERENCE:.2f})")
        ax.axhline(HUMAN_BEST, color="green", ls=":", lw=1,
                   label=f"human best ({HUMAN_BEST:.2f})")
        ax.set_ylabel("score (higher is better; mean win-rate vs gpt2-alpaca/xl)")
        ax.grid(alpha=0.3)
        ax.set_ylim(0.30, 1.02)

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Score vs cost")
    ax_t.legend(loc="lower right", fontsize=7.5, framealpha=0.92)
    ax_c.legend(loc="lower right", fontsize=7.5, framealpha=0.92)

    fig.suptitle(
        "nanogpt_chat_rl — sonnet-4-6, paper s0 (orig 7517443 + resume 7723617) vs ara s0 (7077234)\n"
        f"paper: orig 0.609 → resume final 0.7432 ({len(pp_evts)} + {len(pr_evts)} score events)  |  "
        f"ara: final 0.830 ({len(ara_evts)} score events)  |  square = baseline 0.616 (untuned gpt2-xl), "
        f"star = harness final, dotted = resume boundary",
        fontsize=10,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "nanogpt_46_paper_vs_ara.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"\nsaved {out_path}")


if __name__ == "__main__":
    main()
