"""Plot fix_embedding sonnet-4-6 paper vs ara: score trajectory over time + cost.

fix_embedding score = log(val_loss - 1.5), LOWER is better.
Reference: 0.26 (official 3-phase adapter solution).
Best human baseline: 0.16.
Baseline (raw permuted): 2.20.

paper 7591645 final score: 0.255  (matches official ~0.26)
ara   7591646 best score:  0.2363 (better than official; TIMEOUT'd before harness final)
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
TMP_ROOT = pathlib.Path("/n/home04/zechenzhang/.claude/tmp/claude-62233")

JOBS = {
    "paper s0 (7591645)": (
        "fix_embedding_paper_seed0_job7591645",
        "-n-netscratch-sompolinsky-lab-Everyone-zechenzhang-ara-project-extension-runs-fix-embedding-paper-seed0-job7591645-workdir",
        "047c7150-fb00-440d-9a95-bde839b8cb84",
        "#1f77b4",
    ),
    "ara s0 (7591646)": (
        "fix_embedding_ara_seed0_job7591646",
        "-n-netscratch-sompolinsky-lab-Everyone-zechenzhang-ara-project-extension-runs-fix-embedding-ara-seed0-job7591646-workdir",
        "1483427c-a84f-4e2d-af84-d41ae63ced78",
        "#ff7f0e",
    ),
}
# Resume runs to stitch onto the corresponding original (time + cost offset
# by the original's final). Each entry: original_label -> resume metadata.
RESUMES = {
    "paper s0 (7591645)": (
        "fix_embedding_paper_seed0_resume_job7729813",
        None,  # no separate task dir for the resume
        None,
        7729813,
    ),
}

REFERENCE = 0.26
HUMAN_BEST = 0.16
BASELINE = 2.20

# sonnet-4-6 pricing (same as 4-5)
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}


def get_job_start(job_id):
    out = subprocess.run(
        ["sacct", "-j", str(job_id), "--format=Start", "-n"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[0].strip()
    return datetime.datetime.fromisoformat(out).timestamp()


def collect_scores(run_dir, tasks_dir, job_id):
    """Return (training_events, explicit_events, baseline_event, final_event).
    - training_events: all val_loss readings (training-time internal eval, 200
      batches). Lower than scorer by ~0.02-0.04 due to batch sampling.
    - explicit_events: explicit "Score: X" lines or local_score.py JSON outputs
      (40-batch scorer, harness-equivalent).
    - baseline_event: the starting score (2.20 = corrupted gpt2-xl) at t=0.
    - final_event: harness final_score.json if available."""
    start = get_job_start(job_id)
    elapsed = subprocess.run(
        ["sacct", "-j", str(job_id), "--format=Elapsed", "-n"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[0].strip()
    h, m, s = (int(x) for x in elapsed.split(":"))
    end_min = h * 60 + m + s / 60.0
    end_ts = start + h * 3600 + m * 60 + s

    training_events = []
    explicit_events = []
    trace = run_dir / "trace.jsonl"

    if trace.exists():
        for l in open(trace):
            try:
                ev = json.loads(l)
                t = ev.get("wall_clock_s", 0) / 60.0
            except Exception:
                continue
            # Training-time val_loss readings (any context)
            for m in re.finditer(r'val[_\s]loss[":\s]+([0-9.]+)', l):
                try:
                    vl = float(m.group(1))
                    if 1.6 < vl < 15:
                        training_events.append((t, math.log(vl - 1.5)))
                        break
                except Exception:
                    pass
            # Explicit "Score: X" annotations from agent
            m = re.search(r"Score:\s*([0-9.]+)", l)
            if m:
                try:
                    explicit_events.append((t, float(m.group(1))))
                except Exception:
                    pass
            # JSON scorer outputs
            m = re.search(r'"score":\s*([0-9.]+),\s*"message":\s*\{[^}]*"loss_validation":', l)
            if m:
                try:
                    explicit_events.append((t, float(m.group(1))))
                except Exception:
                    pass

    # Baseline (corrupted gpt2-xl) at t=0
    baseline_event = (0.0, BASELINE)

    # Harness final_score.json
    final_event = None
    fs = run_dir / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text())
            r = d.get("result", d)
            if r.get("score") is not None:
                final_event = (end_min, r.get("score"))
        except Exception:
            pass

    # Dedupe each list
    def dedup(lst):
        seen, out = set(), []
        for t, sv in sorted(lst):
            k = (round(t, 1), round(sv, 4))
            if k in seen: continue
            seen.add(k); out.append((t, sv))
        return out
    return dedup(training_events), dedup(explicit_events), baseline_event, final_event


def collect_costs(run_dir):
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return [], 0.0
    cost_track, cost_acc = [], 0.0
    for line in open(trace):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant":
            continue
        u = d.get("usage", {}) or {}
        cost_acc += (
            u.get("input_tokens", 0) * PRICE["in"] / 1e6
            + u.get("cache_creation_input_tokens", 0) * PRICE["cache_w"] / 1e6
            + u.get("cache_read_input_tokens", 0) * PRICE["cache_r"] / 1e6
            + u.get("output_tokens", 0) * PRICE["out"] / 1e6
        )
        t = d.get("wall_clock_s")
        if t is not None:
            cost_track.append((t / 60.0, cost_acc))

    meta = run_dir / "metadata.json"
    if meta.exists():
        try:
            m = json.loads(meta.read_text())
            final_cost = m.get("agent", {}).get("total_cost_usd")
            if final_cost and cost_acc > 0:
                scale = final_cost / cost_acc
                cost_track = [(t, c * scale) for (t, c) in cost_track]
        except Exception:
            pass
    return cost_track


def running_min(vs):
    out, b = [], float("inf")
    for v in vs:
        b = min(b, v)
        out.append(b)
    return out


def collect_resume_scores(run_dir, job_id):
    """Resume runs: pull explicit score JSONs + harness final."""
    events = []
    trace = run_dir / "trace.jsonl"
    if trace.exists():
        for l in open(trace):
            m = re.search(r'"score":\s*([0-9.]+),\s*"message":\s*\{[^}]*"loss_validation":', l)
            if m:
                try:
                    ev = json.loads(l)
                    t = ev.get("wall_clock_s", 0) / 60.0
                    events.append((t, float(m.group(1))))
                except Exception:
                    pass
    fs = run_dir / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text())
            r = d.get("result", d)
            elapsed = subprocess.run(
                ["sacct", "-j", str(job_id), "--format=Elapsed", "-n"],
                capture_output=True, text=True
            ).stdout.strip().split("\n")[0].strip()
            h, m, s = (int(x) for x in elapsed.split(":"))
            off = h * 60 + m + s / 60.0
            if r.get("score") is not None:
                events.append((off, r["score"]))
        except Exception:
            pass
    events.sort()
    return events


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    ax_t, ax_c = axes

    def cost_at(costs_track, t):
        if not costs_track:
            return 0.0
        c = costs_track[0][1]
        for ti, ci in costs_track:
            if ti <= t:
                c = ci
            else:
                break
        return c

    for label, (run_name, frag, sess, color) in JOBS.items():
        run_dir = RUN_ROOT / run_name
        wd = next(TMP_ROOT.glob(f"*{frag}*"), None)
        tasks_dir = wd / sess / "tasks" if wd else None
        if tasks_dir is None or not tasks_dir.exists():
            print(f"{label}: no tasks dir"); continue

        job_id = run_name.split("job")[-1]
        train_ev, expl_ev, base_ev, final_ev = collect_scores(run_dir, tasks_dir, job_id)
        costs_track = collect_costs(run_dir)

        # Stitch resume explicit events
        resume_split_t = max((t for t, _ in (train_ev + expl_ev)), default=0)
        resume_split_c = cost_at(costs_track, resume_split_t)
        resume_expl = []
        resume_final = None
        resume_max_t = 0
        resume_cost = 0.0
        if label in RESUMES:
            r_run, _, _, r_jobid = RESUMES[label]
            r_dir = RUN_ROOT / r_run
            if r_dir.exists():
                r_events = collect_resume_scores(r_dir, r_jobid)
                if r_events:
                    resume_max_t = max(t for t, _ in r_events)
                    try:
                        resume_cost = json.loads((r_dir / "metadata.json").read_text())["agent"]["total_cost_usd"]
                    except Exception:
                        resume_cost = 0.0
                    # Treat last as final, rest as explicit attempts
                    resume_expl = r_events[:-1]
                    resume_final = r_events[-1]

        def shift(t):
            return t + resume_split_t

        def shift_cost(t):
            if resume_max_t <= 0:
                return resume_split_c
            return resume_split_c + (t / resume_max_t) * resume_cost

        # All explicit-scorer events (offset resume), in order
        all_expl = list(expl_ev) + [(shift(t), s) for t, s in resume_expl]
        if resume_final is not None:
            all_expl_with_final = all_expl + [(shift(resume_final[0]), resume_final[1])]
        elif final_ev is not None:
            all_expl_with_final = all_expl + [final_ev]
        else:
            all_expl_with_final = all_expl

        # Baseline anchor at t=0 -> for best-so-far line, treat as initial
        # (not plotted since y-limits are zoomed; mention in print)
        # Best-so-far based on harness-equivalent (explicit + final) signal
        if all_expl_with_final:
            ts_b = [t for t, _ in all_expl_with_final]
            ss_b = [s for _, s in all_expl_with_final]
            best = running_min(ss_b)
            cs_b = [cost_at(costs_track, t) if t <= resume_split_t else shift_cost(t - resume_split_t)
                    for t in ts_b]
        else:
            ts_b, ss_b, best, cs_b = [], [], [], []

        # Plot training-internal val_loss as faded background + best-so-far trace
        if train_ev:
            t_t = [t for t, _ in train_ev]
            t_s = [s for _, s in train_ev]
            t_c = [cost_at(costs_track, t) for t in t_t]
            ax_t.scatter(t_t, t_s, s=8, color=color, alpha=0.18, marker=".",
                         label=f"{label} train-val (n={len(t_t)})")
            ax_c.scatter(t_c, t_s, s=8, color=color, alpha=0.18, marker=".")
            # Faint best-so-far over training-internal val_loss
            t_best = running_min(t_s)
            ax_t.plot(t_t, t_best, "--", color=color, lw=1, alpha=0.35)
            ax_c.plot(t_c, t_best, "--", color=color, lw=1, alpha=0.35)

        # Plot explicit scorer attempts (harness-equivalent) as bigger markers
        if all_expl:
            e_t = [t for t, _ in all_expl]
            e_s = [s for _, s in all_expl]
            e_c = [cost_at(costs_track, t) if t <= resume_split_t else shift_cost(t - resume_split_t)
                   for t in e_t]
            ax_t.scatter(e_t, e_s, s=55, color=color, alpha=0.85, marker="o",
                         edgecolor="black", linewidth=0.6,
                         label=f"{label} scorer (n={len(e_t)})")
            ax_c.scatter(e_c, e_s, s=55, color=color, alpha=0.85, marker="o",
                         edgecolor="black", linewidth=0.6)

        # Plot harness final as star
        fin = (shift(resume_final[0]), resume_final[1]) if resume_final else final_ev
        if fin is not None:
            f_c = (shift_cost(resume_final[0]) if resume_final
                   else cost_at(costs_track, fin[0]))
            ax_t.scatter([fin[0]], [fin[1]], s=180, color=color, marker="*",
                         edgecolor="black", linewidth=0.8, zorder=5,
                         label=f"{label} final ({fin[1]:.4f})")
            ax_c.scatter([f_c], [fin[1]], s=180, color=color, marker="*",
                         edgecolor="black", linewidth=0.8, zorder=5)

        # Best-so-far line (harness-equivalent signal), anchored at baseline
        if best:
            ts_full = [0.0] + ts_b
            cs_full = [0.0] + cs_b
            best_full = running_min([BASELINE] + ss_b)
            ax_t.plot(ts_full, best_full, "-", color=color, lw=2, alpha=0.9)
            ax_c.plot(cs_full, best_full, "-", color=color, lw=2, alpha=0.9)
            # Baseline marker (both arms start here)
            ax_t.scatter([0], [BASELINE], s=80, color=color, marker="s",
                         edgecolor="black", linewidth=0.6, zorder=5)
            ax_c.scatter([0], [BASELINE], s=80, color=color, marker="s",
                         edgecolor="black", linewidth=0.6, zorder=5)

        if resume_expl or resume_final:
            ax_t.axvline(resume_split_t, color=color, ls=":", lw=1, alpha=0.5)
            ax_c.axvline(resume_split_c, color=color, ls=":", lw=1, alpha=0.5)

        n_expl = len(all_expl_with_final)
        best_v = min(ss_b) if ss_b else float("nan")
        first_v = ss_b[0] if ss_b else float("nan")
        last_t = ts_b[-1] if ts_b else 0
        last_c = cs_b[-1] if cs_b else 0
        print(f"{label:24s}  train_n={len(train_ev):3d}  scorer_n={n_expl:2d}  "
              f"first_scored={first_v:.4f}  best_scored={best_v:.4f}  "
              f"final_min={last_t:.1f}  cost_$={last_c:.2f}"
              f"{'  (+resume)' if resume_expl or resume_final else ''}")

    for ax in axes:
        ax.axhline(REFERENCE, color="red", ls="--", lw=1,
                   label=f"official ref ({REFERENCE:.2f})")
        ax.axhline(HUMAN_BEST, color="green", ls=":", lw=1,
                   label=f"best human ({HUMAN_BEST:.2f})")
        ax.axhline(BASELINE, color="gray", ls="-.", lw=1, alpha=0.5,
                   label=f"baseline ({BASELINE:.2f})")
        ax.set_ylabel("score = log(val_loss - 1.5) — lower is better")
        ax.grid(alpha=0.3, which="both")
        ax.set_yscale("function", functions=(lambda x: x**0.5, lambda x: x**2))
        ax.set_ylim(0.15, 2.35)
        ax.set_yticks([0.16, 0.20, 0.26, 0.30, 0.5, 1.0, 1.5, 2.0, 2.20])

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Best score vs cost")
    ax_t.legend(loc="upper right", fontsize=7, framealpha=0.9, ncol=1)
    ax_c.legend(loc="upper right", fontsize=7, framealpha=0.9, ncol=1)

    fig.suptitle(
        "fix_embedding — sonnet-4-6, paper s0 (orig+resume) vs ara s0\n"
        "dots = training-internal val_loss (200-batch, biased-low); circles = explicit scorer attempts (40-batch, harness-equivalent); "
        "stars = harness final; dotted = resume boundary; baseline 2.20 off-scale",
        fontsize=10,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "fix_embed_46_paper_vs_ara.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
