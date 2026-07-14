"""restricted_mlm sonnet-4-6 paper s0 vs ara s0: separate scorer vs train-val.

Mimics plot_fix_embed_46_paper_vs_ara.py — distinguishes:
  - training-internal val_loss readings (faded dots, agent's own train scripts)
  - canonical local_score.py JSON outputs (highlighted circles, real scoring runs)
  - harness final (star)
  - baseline anchor at score=1.85 (untouched ConvMLM starter)

MLM score = log(val_loss - 1.5), lower is better. Reference = 1.13 (loss 4.6).
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)

JOBS = {
    "paper s0 (7079164)": ("restricted_mlm_paper_seed0_job7079164", 7079164, "#1f77b4"),
    "ara s0 (7079165)":   ("restricted_mlm_ara_seed0_job7079165",   7079165, "#ff7f0e"),
}

BASELINE = 1.85       # untouched MLP / ConvMLM starter score (loss ~7.6)
REFERENCE = 1.13      # official reference solution (loss ~4.6)
HUMAN_BEST = 0.65     # approximate; RE-Bench MLM human ceiling

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

CANONICAL_RE = re.compile(
    r'\{[\\"]+score[\\"]+:\s*(-?[0-9.]+),\s*[\\"]+loss[\\"]+:\s*([0-9.]+),\s*[\\"]+compliant[\\"]+'
)
# Strict training-internal val_loss patterns (NOT step training loss)
TRAIN_VAL_RE = re.compile(
    r'(?:eval[_\s]?loss|val[_\s]?loss|validation[_\s]?loss)[\s:=]+([0-9]+\.[0-9]+)',
    re.IGNORECASE,
)


def sacct_field(job_id, field):
    return subprocess.run(
        ["sacct", "-j", str(job_id), f"--format={field}", "-n", "-X"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[0].strip()


def elapsed_min(job_id):
    e = sacct_field(job_id, "Elapsed")
    h, m, s = (int(x) for x in e.split(":"))
    return h * 60 + m + s / 60.0


def collect_scores(run_dir):
    """Return (training_events, scorer_events, final_event).
    - training_events: agent-script val/eval loss prints (biased low for partial-batch)
    - scorer_events: canonical local_score.py JSON (real scoring submissions)
    - final_event: harness final_score.json if present
    """
    trace = run_dir / "trace.jsonl"
    train_evts = []
    scorer_evts = []
    seen_t, seen_s = set(), set()
    if trace.exists():
        for line in open(trace):
            try: d = json.loads(line)
            except Exception: continue
            t = d.get("wall_clock_s", 0) / 60.0
            # Only look in user (tool_result) for canonical scorer
            if d.get("type") == "user":
                for m in CANONICAL_RE.finditer(line):
                    try:
                        sv = float(m.group(1))
                    except ValueError: continue
                    if not (-2 < sv < 5): continue
                    k = (round(t, 1), round(sv, 4))
                    if k in seen_s: continue
                    seen_s.add(k); scorer_evts.append((t, sv))
            # Training-internal val_loss can appear anywhere in trace
            for m in TRAIN_VAL_RE.finditer(line):
                try:
                    vl = float(m.group(1))
                except ValueError: continue
                if not (1.6 < vl < 50): continue
                sv = math.log(vl - 1.5)
                k = (round(t, 1), round(sv, 4))
                if k in seen_t: continue
                seen_t.add(k); train_evts.append((t, sv))
    train_evts.sort()
    scorer_evts.sort()

    final_evt = None
    fs = run_dir / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text())
            r = d.get("result", d)
            if r.get("score") is not None:
                final_evt = (None, r["score"])
        except Exception: pass
    return train_evts, scorer_evts, final_evt


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
    meta = run_dir / "metadata.json"
    if meta.exists() and acc > 0:
        try:
            final_cost = json.loads(meta.read_text())["agent"].get("total_cost_usd", 0)
            if final_cost:
                scale = final_cost / acc
                track = [(t, c * scale) for t, c in track]
        except Exception: pass
    return track


def cost_at(track, t):
    if not track: return 0.0
    c = track[0][1]
    for ti, ci in track:
        if ti <= t: c = ci
        else: break
    return c


def running_min(vs):
    out, b = [], float("inf")
    for v in vs:
        b = min(b, v); out.append(b)
    return out


def main():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    ax_t, ax_c = axes

    for label, (run_name, job_id, color) in JOBS.items():
        run_dir = RUN_ROOT / run_name
        train_evts, scorer_evts, final_evt = collect_scores(run_dir)
        track = collect_costs(run_dir)
        end_min = elapsed_min(job_id)

        # Best-so-far based on scorer events (anchored at baseline)
        anchor = (0.0, BASELINE)
        scorer_with_anchor = [anchor] + scorer_evts
        if final_evt is not None and final_evt[1] is not None:
            scorer_with_anchor.append((end_min, final_evt[1]))
        scorer_with_anchor.sort(key=lambda x: x[0])
        ts_b = [t for t, _ in scorer_with_anchor]
        ss_b = [s for _, s in scorer_with_anchor]
        cs_b = [cost_at(track, t) for t in ts_b]
        best = running_min(ss_b)

        # Training-internal val_loss (faded background dots)
        if train_evts:
            t_t = [t for t, _ in train_evts]
            t_s = [s for _, s in train_evts]
            t_c = [cost_at(track, t) for t in t_t]
            ax_t.scatter(t_t, t_s, s=10, color=color, alpha=0.20, marker=".",
                         label=f"{label} train-val (n={len(train_evts)})")
            ax_c.scatter(t_c, t_s, s=10, color=color, alpha=0.20, marker=".")

        # Canonical scorer (highlighted circles)
        if scorer_evts:
            e_t = [t for t, _ in scorer_evts]
            e_s = [s for _, s in scorer_evts]
            e_c = [cost_at(track, t) for t in e_t]
            ax_t.scatter(e_t, e_s, s=55, color=color, alpha=0.85, marker="o",
                         edgecolor="black", linewidth=0.5,
                         label=f"{label} scorer (n={len(scorer_evts)})")
            ax_c.scatter(e_c, e_s, s=55, color=color, alpha=0.85, marker="o",
                         edgecolor="black", linewidth=0.5)

        # Baseline marker
        ax_t.scatter([0], [BASELINE], s=80, color=color, marker="s",
                     edgecolor="black", linewidth=0.6, zorder=5)
        ax_c.scatter([0], [BASELINE], s=80, color=color, marker="s",
                     edgecolor="black", linewidth=0.6, zorder=5)

        # Final star
        if final_evt is not None and final_evt[1] is not None:
            ax_t.scatter([end_min], [final_evt[1]], s=280, color=color, marker="*",
                         edgecolor="black", linewidth=0.7, zorder=6,
                         label=f"{label} final ({final_evt[1]:.4f})")
            ax_c.scatter([cost_at(track, end_min)], [final_evt[1]], s=280, color=color, marker="*",
                         edgecolor="black", linewidth=0.7, zorder=6)

        # Best-so-far line
        ax_t.plot(ts_b, best, "-", color=color, lw=2, alpha=0.95)
        ax_c.plot(cs_b, best, "-", color=color, lw=2, alpha=0.95)

        print(f"{label:24s}  train_n={len(train_evts):3d}  scorer_n={len(scorer_evts):3d}  "
              f"best_scored={min((s for _, s in scorer_evts), default=float('nan')):.4f}  "
              f"final={final_evt[1] if final_evt else 'NA'}  "
              f"cost=${cost_at(track, end_min):.2f}")

    for ax in axes:
        ax.axhline(BASELINE, color="gray", ls="-.", lw=1, alpha=0.5,
                   label=f"baseline ({BASELINE:.2f})")
        ax.axhline(REFERENCE, color="red", ls="--", lw=1,
                   label=f"reference ({REFERENCE:.2f})")
        ax.axhline(HUMAN_BEST, color="green", ls=":", lw=1,
                   label=f"~human best ({HUMAN_BEST:.2f})")
        ax.set_ylabel("score = log(val_loss - 1.5) — lower is better")
        ax.grid(alpha=0.3)
        ax.set_ylim(0.4, 2.0)

    ax_t.set_xlabel("wall-clock minutes")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Score vs cost")
    ax_t.legend(loc="upper right", fontsize=7.5, framealpha=0.92)
    ax_c.legend(loc="upper right", fontsize=7.5, framealpha=0.92)

    fig.suptitle(
        "restricted_mlm — sonnet-4-6, paper s0 vs ara s0\n"
        "dots = training-internal val_loss (agent's own train scripts); circles = local_score.py official scorer; "
        "stars = harness final; squares = baseline anchor",
        fontsize=10,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "mlm_46_paper_s0_ara_s0.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
