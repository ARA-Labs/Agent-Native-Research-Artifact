"""restricted_mlm sonnet-4-6 paper s0 vs ara s0 full trajectory (with resume).

Shows ALL real local_score.py canonical events for the 4-6 lineage:
  - paper s0 (7079164): single 8h run, monotone descent baseline 1.84 → 0.69
  - ara s0 ORIG (7079165): crashed at t=331min due to SDK 1MB buffer overflow
                           (best canonical 1.028, agent reached this at t=185)
  - ara s0 RESUME (8011216): inherited workdir + session_id from 7079165;
                              ran 6h53m cleanly with 16MB buffer fix; 17 canonical
                              scoring events; best 1.0120; harness final 1.0196
                              after 7+ failed architectural experiments.

ara s0 events are stitched: resume's wall-clock + cost offset by original's elapsed.
Resume boundary marked with a vertical dotted line.
"""
import datetime, json, math, pathlib, re, subprocess
import matplotlib.pyplot as plt

RUN_ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)

PAPER = ("paper s0 (7079164)", "restricted_mlm_paper_seed0_job7079164", 7079164, "#1f77b4")
ARA_ORIG = ("ara s0 ORIG (7079165)", "restricted_mlm_ara_seed0_job7079165", 7079165, "#ff7f0e")
ARA_RESUME = ("ara s0 RESUME (8011216)", "restricted_mlm_ara_seed0_resume_job8011216", 8011216, "#ff7f0e")

BASELINE = 1.85       # untouched starter (loss ~7.6)
REFERENCE = 1.13      # task reference solution (loss ~4.6)
HUMAN_BEST = 0.65     # ~best human-baseline approximation

PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

PATTERNS = [
    re.compile(r'[\\\\\"]+score[\\\\\"]+:\s*([\-0-9.]+)[^}]{0,200}[\\\\\"]+loss[\\\\\"]+:\s*([0-9.]+)[^}]{0,200}[\\\\\"]+compliant'),
    re.compile(r'\\?"score\\?":\s*([\-0-9.]+),\s*\\?"loss\\?":\s*([0-9.]+),\s*\\?"compliant\\?":'),
]


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
    events = []
    seen = set()
    trace = run_dir / "trace.jsonl"
    if not trace.exists(): return events
    for line in open(trace):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "user": continue
        t = d.get("wall_clock_s", 0) / 60.0
        for rx in PATTERNS:
            for m in rx.finditer(line):
                try:
                    sv = float(m.group(1)); ls = float(m.group(2))
                except ValueError: continue
                if sv > 100: continue  # repeated lines
                k = (round(t, 1), round(sv, 4))
                if k in seen: continue
                seen.add(k); events.append((t, sv, ls))
    events.sort()
    return events


def collect_costs(run_dir):
    trace = run_dir / "trace.jsonl"
    if not trace.exists(): return [], 0.0
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
    final = acc
    meta = run_dir / "metadata.json"
    if meta.exists() and acc > 0:
        try:
            fc = json.loads(meta.read_text())["agent"].get("total_cost_usd", 0)
            if fc:
                scale = fc / acc
                track = [(t, c * scale) for t, c in track]
                final = fc
        except Exception: pass
    return track, final


def cost_at(track, t):
    if not track: return 0.0
    c = track[0][1]
    for ti, ci in track:
        if ti <= t: c = ci
        else: break
    return c


def harness_final(run_dir):
    fs = run_dir / "final_score.json"
    if fs.exists():
        try:
            d = json.loads(fs.read_text())
            r = d.get("result", d)
            if r.get("score") is not None:
                return r["score"]
        except Exception: pass
    return None


def running_min(vs):
    out, b = [], float("inf")
    for v in vs:
        b = min(b, v); out.append(b)
    return out


def main():
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

    # ── paper s0 (single run) ────────────────────────────────────────────
    pp_label, pp_name, pp_job, pp_color = PAPER
    pp_dir = RUN_ROOT / pp_name
    pp_events = collect_scores(pp_dir)
    pp_track, pp_cost = collect_costs(pp_dir)
    pp_final = harness_final(pp_dir)
    pp_elapsed = elapsed_min(pp_job)

    paper_pts = [(0.0, BASELINE, 0.0)]
    for t, s, _ in pp_events:
        paper_pts.append((t, s, cost_at(pp_track, t)))
    if pp_final is not None:
        paper_pts.append((pp_elapsed, pp_final, pp_cost))
    paper_pts.sort(key=lambda x: x[0])

    # ── ara s0 ORIG + RESUME (stitched) ──────────────────────────────────
    ao_label, ao_name, ao_job, ao_color = ARA_ORIG
    ao_dir = RUN_ROOT / ao_name
    ao_events = collect_scores(ao_dir)
    ao_track, ao_cost = collect_costs(ao_dir)
    ao_elapsed = elapsed_min(ao_job)

    ar_label, ar_name, ar_job, _ = ARA_RESUME
    ar_dir = RUN_ROOT / ar_name
    ar_events = collect_scores(ar_dir)
    ar_track, ar_cost = collect_costs(ar_dir)
    ar_final = harness_final(ar_dir)
    ar_elapsed = elapsed_min(ar_job)

    def shift_t(t): return t + ao_elapsed
    def shift_c(t): return ao_cost + cost_at(ar_track, t)

    ara_pts = [(0.0, BASELINE, 0.0)]
    for t, s, _ in ao_events:
        ara_pts.append((t, s, cost_at(ao_track, t)))
    for t, s, _ in ar_events:
        ara_pts.append((shift_t(t), s, shift_c(t)))
    if ar_final is not None:
        ara_pts.append((shift_t(ar_elapsed), ar_final, shift_c(ar_elapsed)))
    ara_pts.sort(key=lambda x: x[0])

    # ── plotting ─────────────────────────────────────────────────────────
    def plot_arm(pts, color, label, final_scored_at):
        ts = [p[0] for p in pts]
        ss = [p[1] for p in pts]
        cs = [p[2] for p in pts]
        best = running_min(ss)
        # All scoring events as faded dots
        ax_t.scatter(ts[1:-1] if final_scored_at else ts[1:], ss[1:-1] if final_scored_at else ss[1:],
                     s=40, color=color, alpha=0.35, marker="o", edgecolor="black", linewidth=0.4,
                     label=f"{label} attempts (n={len(ts)-1-(1 if final_scored_at else 0)})")
        if final_scored_at is not None:
            ax_c.scatter(cs[1:-1], ss[1:-1], s=40, color=color, alpha=0.35, marker="o",
                         edgecolor="black", linewidth=0.4)
        else:
            ax_c.scatter(cs[1:], ss[1:], s=40, color=color, alpha=0.35, marker="o",
                         edgecolor="black", linewidth=0.4)
        # Baseline anchor
        ax_t.scatter([0], [BASELINE], s=85, color=color, marker="s",
                     edgecolor="black", linewidth=0.6, zorder=5)
        ax_c.scatter([0], [BASELINE], s=85, color=color, marker="s",
                     edgecolor="black", linewidth=0.6, zorder=5)
        # Final star
        if final_scored_at is not None:
            ax_t.scatter([ts[-1]], [ss[-1]], s=320, color=color, marker="*",
                         edgecolor="black", linewidth=0.7, zorder=6,
                         label=f"{label} final ({ss[-1]:.4f})")
            ax_c.scatter([cs[-1]], [ss[-1]], s=320, color=color, marker="*",
                         edgecolor="black", linewidth=0.7, zorder=6)
        # Best-so-far line
        ax_t.plot(ts, best, "-", color=color, lw=2, alpha=0.95)
        ax_c.plot(cs, best, "-", color=color, lw=2, alpha=0.95)

    plot_arm(paper_pts, pp_color, "paper s0", pp_final)
    plot_arm(ara_pts, ao_color, "ara s0 (orig+resume)", ar_final)

    # Resume boundary on ara
    ax_t.axvline(ao_elapsed, color=ao_color, ls=":", lw=1.5, alpha=0.6,
                 label=f"ara resume boundary ({ao_elapsed:.0f}min)")
    ax_c.axvline(ao_cost, color=ao_color, ls=":", lw=1.5, alpha=0.6,
                 label=f"ara resume boundary (${ao_cost:.0f})")

    # SDK crash marker on original ara
    ax_t.annotate("ara orig SDK crash\n(t=331min, 1MB buffer)",
                  xy=(ao_elapsed, BASELINE - 0.1), xytext=(ao_elapsed - 100, BASELINE - 0.5),
                  fontsize=7, color=ao_color, alpha=0.8,
                  arrowprops=dict(arrowstyle="->", color=ao_color, alpha=0.5, lw=0.8))

    for ax in (ax_t, ax_c):
        ax.axhline(BASELINE, color="gray", ls="-.", lw=1, alpha=0.5,
                   label=f"baseline ({BASELINE:.2f})")
        ax.axhline(REFERENCE, color="red", ls="--", lw=1,
                   label=f"reference ({REFERENCE:.2f})")
        ax.axhline(HUMAN_BEST, color="green", ls=":", lw=1,
                   label=f"~human best ({HUMAN_BEST:.2f})")
        ax.set_ylabel("score = log(val_loss - 1.5) — lower is better")
        ax.grid(alpha=0.3)
        ax.set_ylim(0.4, 2.5)

    ax_t.set_xlabel("wall-clock minutes (orig + resume stitched for ara)")
    ax_c.set_xlabel("cumulative cost (USD)")
    ax_t.set_title("Score over time")
    ax_c.set_title("Score vs cost")
    ax_t.legend(loc="upper right", fontsize=7, framealpha=0.92)
    ax_c.legend(loc="upper right", fontsize=7, framealpha=0.92)

    fig.suptitle(
        "restricted_mlm — sonnet-4-6, paper s0 (7079164) vs ara s0 lineage "
        "(orig 7079165 + resume 8011216)\n"
        f"paper monotone descent → 0.69 final  |  ara orig 1.028 best → SDK crash at 5h32m → resume 1.012 best, 1.020 final  "
        f"|  paper wins MLM 4-6",
        fontsize=10,
    )
    fig.tight_layout()

    # Print summary
    pp_best = min((s for _,s,_ in pp_events), default=float('nan'))
    ao_best = min((s for _,s,_ in ao_events), default=float('nan'))
    ar_best = min((s for _,s,_ in ar_events), default=float('nan'))
    print(f"\n=== PAPER s0 (7079164) ===")
    print(f"  baseline {BASELINE} -> {len(pp_events)} attempts, best {pp_best:.4f}, "
          f"final {pp_final if pp_final is None else f'{pp_final:.4f}'}, cost ${pp_cost:.2f}")
    print(f"\n=== ARA s0 ORIG (7079165) ===")
    print(f"  {len(ao_events)} attempts before SDK crash @ t={ao_elapsed:.0f}min, "
          f"best {ao_best:.4f}, cost ${ao_cost:.2f}")
    print(f"\n=== ARA s0 RESUME (8011216) ===")
    print(f"  {len(ar_events)} attempts in {ar_elapsed:.0f}min, "
          f"best {ar_best:.4f}, "
          f"final {ar_final if ar_final is None else f'{ar_final:.4f}'}, cost ${ar_cost:.2f}")

    out_path = pathlib.Path(
        "/n/home04/zechenzhang/ara-project/code/extension-harness/plots/"
        "mlm_46_paper_vs_ara_full.png"
    )
    fig.savefig(out_path, dpi=150)
    print(f"\nsaved {out_path}")


if __name__ == "__main__":
    main()
