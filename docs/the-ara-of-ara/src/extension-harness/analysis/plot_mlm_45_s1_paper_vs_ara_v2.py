"""restricted_mlm sonnet-4-5 paper s1 (original+resume) vs ara s1: separate scorer vs train-val.

Mimics plot_fix_embed_46_paper_vs_ara.py — distinguishes:
  - training-internal val_loss (faded dots, agent's own train scripts)
  - canonical local_score.py JSON outputs (highlighted circles, real scoring)
  - harness final (star)
  - baseline anchor at score=1.85 (untouched ConvMLM starter)

Paper s1 stitched: orig 6858168 then resume 7070627 offset by orig's elapsed.
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)

PAPER_ORIG = ("paper s1 orig (6858168)", "restricted_mlm_paper_seed1_job6858168", 6858168)
PAPER_RESUME = ("paper s1 resume (7070627)", "restricted_mlm_paper_seed1_resume_job7070627", 7070627)
ARA = ("ara s1 (6786400)", "restricted_mlm_ara_seed1_job6786400", 6786400)

PAPER_COLOR = "#1f77b4"
ARA_COLOR = "#ff7f0e"

BASELINE = 1.85
REFERENCE = 1.13
HUMAN_BEST = 0.65

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

CANONICAL_RE = re.compile(
    r'\{[\\"]+score[\\"]+:\s*(-?[0-9.]+),\s*[\\"]+loss[\\"]+:\s*([0-9.]+),\s*[\\"]+compliant[\\"]+'
)
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
    trace = run_dir / "trace.jsonl"
    train_evts, scorer_evts = [], []
    seen_t, seen_s = set(), set()
    if trace.exists():
        for line in open(trace):
            try: d = json.loads(line)
            except Exception: continue
            t = d.get("wall_clock_s", 0) / 60.0
            if d.get("type") == "user":
                for m in CANONICAL_RE.finditer(line):
                    try: sv = float(m.group(1))
                    except ValueError: continue
                    if not (-2 < sv < 5): continue
                    k = (round(t, 1), round(sv, 4))
                    if k in seen_s: continue
                    seen_s.add(k); scorer_evts.append((t, sv))
            for m in TRAIN_VAL_RE.finditer(line):
                try: vl = float(m.group(1))
                except ValueError: continue
                if not (1.6 < vl < 50): continue
                sv = math.log(vl - 1.5)
                k = (round(t, 1), round(sv, 4))
                if k in seen_t: continue
                seen_t.add(k); train_evts.append((t, sv))
    train_evts.sort(); scorer_evts.sort()
    final_evt = None
    fs = run_dir / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text())
            r = d.get("result", d)
            if r.get("score") is not None:
                final_evt = r["score"]
        except Exception: pass
    return train_evts, scorer_evts, final_evt


def collect_costs(run_dir):
    trace = run_dir / "trace.jsonl"
    if not trace.exists(): return [], 0
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
    final_cost = acc
    meta = run_dir / "metadata.json"
    if meta.exists() and acc > 0:
        try:
            fc = json.loads(meta.read_text())["agent"].get("total_cost_usd", 0)
            if fc:
                scale = fc / acc
                track = [(t, c * scale) for t, c in track]
                final_cost = fc
        except Exception: pass
    return track, final_cost


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

    # --- PAPER s1 orig + resume (stitched) ---
    pp_label, pp_name, pp_job = PAPER_ORIG
    pr_label, pr_name, pr_job = PAPER_RESUME

    pp_dir = RUN_ROOT / pp_name
    pr_dir = RUN_ROOT / pr_name
    pp_train, pp_scorer, pp_final = collect_scores(pp_dir)
    pr_train, pr_scorer, pr_final = collect_scores(pr_dir)
    pp_track, pp_cost = collect_costs(pp_dir)
    pr_track, pr_cost = collect_costs(pr_dir)
    pp_elapsed = elapsed_min(pp_job)
    pr_elapsed = elapsed_min(pr_job)

    def shift_t(t): return t + pp_elapsed
    def shift_c(t): return pp_cost + cost_at(pr_track, t)

    paper_train = [(t, s, cost_at(pp_track, t)) for t, s in pp_train]
    paper_train += [(shift_t(t), s, shift_c(t)) for t, s in pr_train]
    paper_scorer = [(t, s, cost_at(pp_track, t)) for t, s in pp_scorer]
    paper_scorer += [(shift_t(t), s, shift_c(t)) for t, s in pr_scorer]
    paper_final_pt = None
    if pr_final is not None:
        paper_final_pt = (shift_t(pr_elapsed), pr_final, shift_c(pr_elapsed))

    # --- ARA s1 ---
    ara_label, ara_name, ara_job = ARA
    ara_dir = RUN_ROOT / ara_name
    ara_train, ara_scorer, ara_final = collect_scores(ara_dir)
    ara_track, ara_cost = collect_costs(ara_dir)
    ara_elapsed = elapsed_min(ara_job)

    ara_train = [(t, s, cost_at(ara_track, t)) for t, s in ara_train]
    ara_scorer = [(t, s, cost_at(ara_track, t)) for t, s in ara_scorer]
    ara_final_pt = (ara_elapsed, ara_final, cost_at(ara_track, ara_elapsed)) if ara_final is not None else None

    def plot_arm(train_pts, scorer_pts, final_pt, color, label):
        # Training-internal faded dots
        if train_pts:
            ax_t.scatter([p[0] for p in train_pts], [p[1] for p in train_pts],
                         s=10, color=color, alpha=0.20, marker=".",
                         label=f"{label} train-val (n={len(train_pts)})")
            ax_c.scatter([p[2] for p in train_pts], [p[1] for p in train_pts],
                         s=10, color=color, alpha=0.20, marker=".")
        # Canonical scorer circles
        if scorer_pts:
            ax_t.scatter([p[0] for p in scorer_pts], [p[1] for p in scorer_pts],
                         s=55, color=color, alpha=0.85, marker="o",
                         edgecolor="black", linewidth=0.5,
                         label=f"{label} scorer (n={len(scorer_pts)})")
            ax_c.scatter([p[2] for p in scorer_pts], [p[1] for p in scorer_pts],
                         s=55, color=color, alpha=0.85, marker="o",
                         edgecolor="black", linewidth=0.5)
        # Baseline anchor
        ax_t.scatter([0], [BASELINE], s=80, color=color, marker="s",
                     edgecolor="black", linewidth=0.6, zorder=5)
        ax_c.scatter([0], [BASELINE], s=80, color=color, marker="s",
                     edgecolor="black", linewidth=0.6, zorder=5)
        # Final star
        if final_pt is not None:
            ax_t.scatter([final_pt[0]], [final_pt[1]], s=280, color=color, marker="*",
                         edgecolor="black", linewidth=0.7, zorder=6,
                         label=f"{label} final ({final_pt[1]:.4f})")
            ax_c.scatter([final_pt[2]], [final_pt[1]], s=280, color=color, marker="*",
                         edgecolor="black", linewidth=0.7, zorder=6)
        # Best-so-far line through scorer + baseline + final
        anchor = [(0, BASELINE, 0)] + list(scorer_pts)
        if final_pt is not None: anchor.append(final_pt)
        anchor.sort(key=lambda x: x[0])
        if anchor:
            ts_b = [p[0] for p in anchor]
            ss_b = [p[1] for p in anchor]
            cs_b = [p[2] for p in anchor]
            best = running_min(ss_b)
            ax_t.plot(ts_b, best, "-", color=color, lw=2, alpha=0.95)
            ax_c.plot(cs_b, best, "-", color=color, lw=2, alpha=0.95)

    plot_arm(paper_train, paper_scorer, paper_final_pt, PAPER_COLOR, "paper s1 (orig+resume)")
    plot_arm(ara_train, ara_scorer, ara_final_pt, ARA_COLOR, "ara s1")

    # Resume boundary
    ax_t.axvline(pp_elapsed, color=PAPER_COLOR, ls=":", lw=1, alpha=0.5,
                 label=f"paper resume boundary ({pp_elapsed:.0f} min)")
    ax_c.axvline(pp_cost, color=PAPER_COLOR, ls=":", lw=1, alpha=0.5,
                 label=f"paper resume boundary (${pp_cost:.0f})")

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

    ax_t.set_xlabel("wall-clock minutes (orig + resume stitched)")
    ax_c.set_xlabel("cumulative cost (USD; orig + resume)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Score vs cost")
    ax_t.legend(loc="upper right", fontsize=7, framealpha=0.92)
    ax_c.legend(loc="upper right", fontsize=7, framealpha=0.92)

    print(f"paper s1 orig    n_train={len(pp_train):3d}  n_scorer={len(pp_scorer):3d}  cost=${pp_cost:.2f}")
    print(f"paper s1 resume  n_train={len(pr_train):3d}  n_scorer={len(pr_scorer):3d}  cost=${pr_cost:.2f}")
    print(f"paper combined   n_train={len(paper_train):3d}  n_scorer={len(paper_scorer):3d}")
    print(f"ara s1           n_train={len(ara_train):3d}  n_scorer={len(ara_scorer):3d}  cost=${ara_cost:.2f}")

    fig.suptitle(
        "restricted_mlm — sonnet-4-5, paper s1 (orig 6858168 + resume 7070627) vs ara s1 (6786400)\n"
        "dots = training-internal val_loss (agent's train scripts); circles = local_score.py official scorer; "
        "stars = harness final; squares = baseline anchor",
        fontsize=10,
    )
    fig.tight_layout()

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "mlm_45_paper_s1_extended_vs_ara_s1.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
