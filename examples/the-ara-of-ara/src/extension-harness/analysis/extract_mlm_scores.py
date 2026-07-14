"""Thoroughly extract ALL canonical scoring events for the 4 MLM agents.

Handles four output formats observed across paper/ARA × Sonnet 4.5/4.6 traces:
  (A) Inline JSON:    `{"score": X, "loss": Y, "compliant": ...}`
  (B) Short one-line: `Loss: X, Score: Y`            (agent's custom Python pipe)
  (C) Persisted file: `<persisted-output> ... saved to: <path>` — read the path
  (D) Subagent tmp:   `~/.claude/tmp/<sid>/<wd>/<uid>/tasks/*.output`

For each scoring event, records (arm, t_min, score, loss, source, run_dir).
Stitches paper parent + resume and ARA orig + resume into single timelines.

Output: code/extension-harness/analysis/mlm_scores_all.csv
"""
from __future__ import annotations

import csv
import datetime
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
CLAUDE_TMP = pathlib.Path("/n/home04/zechenzhang/.claude/tmp/claude-62233")
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

ARMS = [
    ("paper-4.5", "claude-sonnet-4-5", ROOT / "restricted_mlm_paper_seed1_job6858168",
     ROOT / "restricted_mlm_paper_seed1_resume_job7070627"),
    ("ARA-4.5",   "claude-sonnet-4-5", ROOT / "restricted_mlm_ara_seed1_job6786400", None),
    ("paper-4.6", "claude-sonnet-4-6", ROOT / "restricted_mlm_paper_seed0_job7079164", None),
    ("ARA-4.6",   "claude-sonnet-4-6", ROOT / "restricted_mlm_ara_seed0_job7079165",
     ROOT / "restricted_mlm_ara_seed0_resume_job8011216"),
]

# (A) JSON-shape scorer output
RE_JSON = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,300}'
    r'\\?"loss\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
)
# (B) Short Loss/Score one-liner
RE_SHORT = re.compile(r'Loss:\s*(-?\d+(?:\.\d+)?)\s*,\s*Score:\s*(-?\d+(?:\.\d+)?)')
# (C) Persisted-output pointer
RE_PERSISTED = re.compile(r"saved to:\s*([^\s'\"\\]+\.txt)")


def job_start_epoch(run_dir):
    if run_dir is None:
        return None
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


def parse_persisted(path_str):
    """Read a persisted tool-result file and return final canonical (score, loss) if present."""
    p = pathlib.Path(path_str)
    if not p.exists():
        return None
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        return None
    # Try short form first (final-line "Loss: X, Score: Y")
    last_short = None
    for m in RE_SHORT.finditer(txt):
        last_short = (float(m.group(2)), float(m.group(1)))   # (score, loss)
    if last_short:
        return last_short
    # Fall back to JSON form
    last_json = None
    for m in RE_JSON.finditer(txt):
        last_json = (float(m.group(1)), float(m.group(2)))
    return last_json


def cost_track(run_dir):
    """Per-message cumulative cost (rescaled to metadata total when present)."""
    track, acc = [], 0.0
    if run_dir is None or not (run_dir / "trace.jsonl").exists():
        return [], 0.0
    for line in open(run_dir / "trace.jsonl"):
        try: d = json.loads(line)
        except: continue
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
            mc = json.loads(meta.read_text()).get("agent", {}).get("total_cost_usd")
            if mc:
                scale = mc / acc
                track = [(t, c * scale) for (t, c) in track]
                final_cost = mc
        except Exception:
            pass
    return track, final_cost


def cost_at(track, t):
    if not track: return 0.0
    c = track[0][1]
    for ti, ci in track:
        if ti <= t: c = ci
        else: break
    return c


def collect_run_events(run_dir, source_label_suffix=""):
    """Collect ALL scoring events from a single run dir.
    Returns list of dicts with keys: t_min, score, loss, source, src_excerpt."""
    events = []
    if run_dir is None or not (run_dir / "trace.jsonl").exists():
        return events

    # Track which assistant message preceded a tool result (to know if it was a score command)
    last_assistant_was_score_cmd = False
    last_score_cmd_text = ""

    for line in open(run_dir / "trace.jsonl"):
        try: d = json.loads(line)
        except: continue
        t_min = (d.get("wall_clock_s") or 0) / 60.0

        if d.get("type") == "assistant":
            last_assistant_was_score_cmd = False
            for block in d.get("content", []):
                r = block.get("repr", "")
                if "name='Bash'" in r:
                    cm = re.search(r"'command':\s*'([^']{0,300})", r)
                    if cm and any(kw in cm.group(1).lower()
                                  for kw in ["local_score", "score.sh"]):
                        last_assistant_was_score_cmd = True
                        last_score_cmd_text = cm.group(1)[:120]
            continue

        if d.get("type") != "user":
            continue

        # (A) Inline JSON in this tool result
        for m in RE_JSON.finditer(line):
            try:
                events.append({
                    "t_min": t_min, "score": float(m.group(1)),
                    "loss": float(m.group(2)),
                    "source": f"trace_json{source_label_suffix}",
                    "src_excerpt": last_score_cmd_text,
                })
            except ValueError:
                continue

        # (B) Short one-liner in this tool result
        for m in RE_SHORT.finditer(line):
            try:
                events.append({
                    "t_min": t_min, "score": float(m.group(2)),
                    "loss": float(m.group(1)),
                    "source": f"trace_short{source_label_suffix}",
                    "src_excerpt": last_score_cmd_text,
                })
            except ValueError:
                continue

        # (C) Persisted-output pointer; read the file
        if last_assistant_was_score_cmd:
            for m in RE_PERSISTED.finditer(line):
                p = m.group(1).rstrip("\\").rstrip("'\"")
                got = parse_persisted(p)
                if got:
                    sv, lv = got
                    events.append({
                        "t_min": t_min, "score": sv, "loss": lv,
                        "source": f"persisted{source_label_suffix}",
                        "src_excerpt": p.split("/")[-1],
                    })

        last_assistant_was_score_cmd = False

    # (D) Tmp subagent task outputs (mtime-based)
    job_start_s = job_start_epoch(run_dir)
    track, _ = cost_track(run_dir)
    trace_end_min = track[-1][0] if track else 0
    slug = run_dir.name.replace("_", "-").lower()
    if CLAUDE_TMP.exists() and job_start_s is not None and trace_end_min > 0:
        for tmp_dir in CLAUDE_TMP.iterdir():
            if not tmp_dir.is_dir() or slug not in tmp_dir.name.lower():
                continue
            for output_f in tmp_dir.glob("*/tasks/*.output"):
                try:
                    txt = output_f.read_text(errors="ignore")
                except Exception:
                    continue
                t_min = (output_f.stat().st_mtime - job_start_s) / 60.0
                if t_min < 0 or t_min > trace_end_min + 5:
                    continue
                # Try short then JSON
                got = None
                for m in RE_SHORT.finditer(txt):
                    got = (float(m.group(2)), float(m.group(1)))
                if got is None:
                    for m in RE_JSON.finditer(txt):
                        got = (float(m.group(1)), float(m.group(2)))
                if got:
                    sv, lv = got
                    events.append({
                        "t_min": t_min, "score": sv, "loss": lv,
                        "source": f"tmp_subagent{source_label_suffix}",
                        "src_excerpt": output_f.name[:12],
                    })

    return events


def main():
    rows = []
    for arm, model, parent, resume in ARMS:
        print(f"\n=== {arm} ({model}) ===")

        # Baseline (canonical pre-agent score from baseline_score.json)
        bl_path = parent / "baseline_score.json"
        if bl_path.exists():
            try:
                bl = json.loads(bl_path.read_text()).get("result", {})
                if bl and bl.get("score") is not None:
                    msg = bl.get("message") or {}
                    rows.append({
                        "arm": arm, "model": model,
                        "run": "parent", "run_id": parent.name,
                        "t_min": 0.0, "score": bl["score"],
                        "loss": (msg.get("loss") if isinstance(msg, dict) else bl.get("loss")) or 0,
                        "cost_usd": 0.0,
                        "source": "baseline_json",
                        "src_excerpt": "harness pre-agent baseline",
                    })
            except Exception as e:
                print(f"  baseline parse error: {e}")

        # Parent run events
        parent_track, parent_total_cost = cost_track(parent)
        parent_t_end = parent_track[-1][0] if parent_track else 0
        for ev in collect_run_events(parent):
            ev["arm"] = arm
            ev["model"] = model
            ev["run"] = "parent"
            ev["run_id"] = parent.name
            ev["cost_usd"] = cost_at(parent_track, ev["t_min"])
            rows.append(ev)

        # Parent harness final
        fs = parent / "final_score.json"
        if fs.exists():
            try:
                fr = json.loads(fs.read_text()).get("result", {})
                if fr and fr.get("score") is not None:
                    rows.append({
                        "arm": arm, "model": model,
                        "run": "parent", "run_id": parent.name,
                        "t_min": parent_t_end, "score": fr["score"],
                        "loss": fr.get("loss") or (fr.get("message", {}) or {}).get("loss") or 0,
                        "cost_usd": parent_total_cost,
                        "source": "final_json",
                        "src_excerpt": "harness post-agent final",
                    })
            except Exception:
                pass

        # Resume run events (if any), shifted by parent_t_end
        if resume is not None:
            print(f"  + resume: {resume.name}")
            resume_track, resume_total_cost = cost_track(resume)
            resume_t_end = resume_track[-1][0] if resume_track else 0
            for ev in collect_run_events(resume, source_label_suffix="(resume)"):
                ev["arm"] = arm
                ev["model"] = model
                ev["run"] = "resume"
                ev["run_id"] = resume.name
                ev["t_min"] = parent_t_end + ev["t_min"]
                ev["cost_usd"] = parent_total_cost + cost_at(resume_track, ev["t_min"] - parent_t_end)
                rows.append(ev)
            fs = resume / "final_score.json"
            if fs.exists():
                try:
                    fr = json.loads(fs.read_text()).get("result", {})
                    if fr and fr.get("score") is not None:
                        rows.append({
                            "arm": arm, "model": model,
                            "run": "resume", "run_id": resume.name,
                            "t_min": parent_t_end + resume_t_end,
                            "score": fr["score"],
                            "loss": fr.get("loss") or (fr.get("message", {}) or {}).get("loss") or 0,
                            "cost_usd": parent_total_cost + resume_total_cost,
                            "source": "final_json(resume)",
                            "src_excerpt": "harness post-agent final",
                        })
                except Exception:
                    pass

    # Per-arm dedup: (round(t,1), round(score,4), source) — tolerate small repeats
    print(f"\nbefore dedup: {len(rows)} rows")
    seen = set(); deduped = []
    for r in sorted(rows, key=lambda x: (x["arm"], x["t_min"])):
        k = (r["arm"], round(r["t_min"], 1), round(r["score"], 4))
        if k in seen: continue
        seen.add(k); deduped.append(r)
    print(f"after dedup:  {len(deduped)} rows")

    # Write CSV
    out_csv = pathlib.Path(__file__).parent / "mlm_scores_all.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "arm", "model", "run", "run_id", "t_min", "score", "loss",
            "cost_usd", "source", "src_excerpt",
        ])
        w.writeheader()
        for r in deduped:
            w.writerow(r)
    print(f"\nsaved {out_csv}")

    # Per-arm summary
    print(f"\n=== per-arm event counts ===")
    for arm in ["paper-4.5", "ARA-4.5", "paper-4.6", "ARA-4.6"]:
        arm_rows = [r for r in deduped if r["arm"] == arm]
        print(f"\n{arm}:  n={len(arm_rows)}")
        for r in arm_rows:
            print(f"  t={r['t_min']:7.1f}  score={r['score']:7.4f}  loss={r['loss']:8.3f}"
                  f"  cost=${r['cost_usd']:6.2f}  [{r['source']}]")


if __name__ == "__main__":
    main()
