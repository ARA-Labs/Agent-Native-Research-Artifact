"""Thorough scoring-event extraction for all 5 RE-Bench extension tasks.

Same robustness pattern as extract_mlm_scores.py: catches inline JSON,
short one-liners, persisted-output files, and Claude tmp subagent task
outputs. Per-task score regex parameterised below.

Output: code/extension-harness/analysis/all_scores.csv with columns:
  task, arm, model, run, run_id, t_min, score, cost_usd, source, src_excerpt
"""
from __future__ import annotations

import csv
import datetime
import json
import math
import pathlib
import re
import subprocess

ROOT = pathlib.Path(
    "/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs"
)
CLAUDE_TMP = pathlib.Path("/n/home04/zechenzhang/.claude/tmp/claude-62233")
PRICE = {"in": 3.00, "cache_w": 3.75, "cache_r": 0.30, "out": 15.00}

# Task config: (task, arm, model, parent, resume, score_regexes [list of (pattern, score_group_index)])
# The score_group_index is the regex group containing the canonical score value.

TRITON_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|NaN)'
    r'[^}]{0,400}'
    r'\\?"solution_time_ms\\?":\s*(-?\d+(?:\.\d+)?)'
)
RUST_RE_TXT = re.compile(
    r"Score:\s*([0-9.]+)\s*\\?n?\s*\|\s*(\d+)\s*successes\s*/\s*165"
)
RUST_RE_JSON = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?)'
    r'[^}]{0,200}'
    r'\\?"n_problems\\?":\s*165'
    r'[^}]{0,200}'
    r'\\?"n_successes\\?":\s*(\d+)'
)
NANOGPT_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,400}'
    r'win_vs_gpt2-alpaca\\?":\s*(-?\d+(?:\.\d+)?)'
)
FIXEMBED_RE = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,400}'
    r'\\?"loss_validation\\?":\s*(-?\d+(?:\.\d+)?)'
)
MLM_RE_JSON = re.compile(
    r'\\?"score\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
    r'[^}]{0,300}'
    r'\\?"loss\\?":\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
)
MLM_RE_SHORT = re.compile(r'Loss:\s*(-?\d+(?:\.\d+)?)\s*,\s*Score:\s*(-?\d+(?:\.\d+)?)')

RE_PERSISTED = re.compile(r"saved to:\s*([^\s'\"\\]+\.txt)")

# (task, score_regexes_in_order_of_preference, score_keyword_filter)
TASK_REGEXES = {
    "triton_cumsum":   [(TRITON_RE, "shape_dtype_match")],
    "rust_codecontests": [(RUST_RE_TXT, None), (RUST_RE_JSON, "n_successes")],
    "nanogpt_chat_rl": [(NANOGPT_RE, "win_vs_gpt2-alpaca")],
    "fix_embedding":   [(FIXEMBED_RE, "loss_validation")],
    "restricted_mlm":  [(MLM_RE_JSON, "compliant"), (MLM_RE_SHORT, None)],
}

# Task → (arm-label, model, parent_dir, resume_dir or None)
RUNS = [
    # triton — Sonnet 4.5 + 4.6
    ("triton_cumsum", "paper-4.5", "claude-sonnet-4-5",
     ROOT / "triton_cumsum_paper_seed8_job7982788", None),
    ("triton_cumsum", "ARA-4.5",   "claude-sonnet-4-5",
     ROOT / "triton_cumsum_ara_seed8_job7982791", None),
    ("triton_cumsum", "paper-4.6", "claude-sonnet-4-6",
     ROOT / "triton_cumsum_paper_seed0_job6595591", None),
    ("triton_cumsum", "ARA-4.6",   "claude-sonnet-4-6",
     ROOT / "triton_cumsum_ara_seed0_job6595593", None),

    # rust — Sonnet 4.6 only (paper + ARA stitched)
    ("rust_codecontests", "paper-4.6", "claude-sonnet-4-6",
     ROOT / "rust_codecontests_paper_seed0_job7798926", None),
    ("rust_codecontests", "ARA-4.6", "claude-sonnet-4-6",
     ROOT / "rust_codecontests_ara_seed0_job7600566",
     ROOT / "rust_codecontests_ara_seed0_resume_job7720567"),

    # nanogpt — Sonnet 4.6 only
    ("nanogpt_chat_rl", "paper-4.6", "claude-sonnet-4-6",
     ROOT / "nanogpt_chat_rl_paper_seed0_job7517443",
     ROOT / "nanogpt_chat_rl_paper_seed0_resume_job7723617"),
    ("nanogpt_chat_rl", "ARA-4.6", "claude-sonnet-4-6",
     ROOT / "nanogpt_chat_rl_ara_seed0_job7077234", None),

    # fix_embedding — Sonnet 4.6 only
    ("fix_embedding", "paper-4.6", "claude-sonnet-4-6",
     ROOT / "fix_embedding_paper_seed0_job7591645",
     ROOT / "fix_embedding_paper_seed0_resume_job7729813"),
    ("fix_embedding", "ARA-4.6", "claude-sonnet-4-6",
     ROOT / "fix_embedding_ara_seed0_job7591646", None),

    # mlm — Sonnet 4.5 + 4.6
    ("restricted_mlm", "paper-4.5", "claude-sonnet-4-5",
     ROOT / "restricted_mlm_paper_seed1_job6858168",
     ROOT / "restricted_mlm_paper_seed1_resume_job7070627"),
    ("restricted_mlm", "ARA-4.5", "claude-sonnet-4-5",
     ROOT / "restricted_mlm_ara_seed1_job6786400", None),
    ("restricted_mlm", "paper-4.6", "claude-sonnet-4-6",
     ROOT / "restricted_mlm_paper_seed0_job7079164", None),
    ("restricted_mlm", "ARA-4.6", "claude-sonnet-4-6",
     ROOT / "restricted_mlm_ara_seed0_job7079165",
     ROOT / "restricted_mlm_ara_seed0_resume_job8011216"),
]


def job_start_epoch(run_dir):
    if run_dir is None: return None
    m = re.search(r"job(\d+)", run_dir.name)
    if not m: return None
    out = subprocess.run(
        ["sacct", "-j", m.group(1), "--format=Start", "-n", "-X"],
        capture_output=True, text=True,
    ).stdout.strip().split("\n")[0].strip()
    try:
        return datetime.datetime.fromisoformat(out).timestamp()
    except Exception:
        return None


def cost_track(run_dir):
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


def parse_persisted(path_str, regexes):
    """Read a persisted tool-result file, return (score, source_label) of the LAST canonical hit."""
    p = pathlib.Path(path_str)
    if not p.exists(): return None
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        return None
    last = None
    for pat, kw_filter in regexes:
        for m in pat.finditer(txt):
            try: sv = float(m.group(1))
            except (ValueError, IndexError): continue
            last = sv
    return last


def collect_run_events(run_dir, task):
    """Collect ALL scoring events (any source) for one run_dir + task."""
    events = []
    if run_dir is None or not (run_dir / "trace.jsonl").exists():
        return events
    regexes = TASK_REGEXES[task]
    last_was_score_cmd = False
    last_score_cmd = ""
    for line in open(run_dir / "trace.jsonl"):
        try: d = json.loads(line)
        except: continue
        t_min = (d.get("wall_clock_s") or 0) / 60.0
        if d.get("type") == "assistant":
            last_was_score_cmd = False
            for block in d.get("content", []):
                r = block.get("repr", "")
                if "name='Bash'" in r:
                    cm = re.search(r"'command':\s*'([^']{0,200})", r)
                    if cm and any(kw in cm.group(1).lower()
                                  for kw in ["local_score", "score.sh", "score.py"]):
                        last_was_score_cmd = True
                        last_score_cmd = cm.group(1)[:80]
            continue
        if d.get("type") != "user":
            continue
        # (A) inline regex hits
        for pat, kw_filter in regexes:
            for m in pat.finditer(line):
                try: sv = float(m.group(1))
                except (ValueError, IndexError): continue
                events.append({"t_min": t_min, "score": sv, "source": "trace_inline"})
        # (B) persisted-output pointer
        if last_was_score_cmd:
            for m in RE_PERSISTED.finditer(line):
                p = m.group(1).rstrip("\\").rstrip("'\"")
                got = parse_persisted(p, regexes)
                if got is not None:
                    events.append({"t_min": t_min, "score": got, "source": "persisted"})
        last_was_score_cmd = False

    # (C) tmp subagent outputs
    js = job_start_epoch(run_dir)
    track, _ = cost_track(run_dir)
    trace_end_min = track[-1][0] if track else 0
    slug = run_dir.name.replace("_", "-").lower()
    if CLAUDE_TMP.exists() and js is not None and trace_end_min > 0:
        for tmp_dir in CLAUDE_TMP.iterdir():
            if not tmp_dir.is_dir() or slug not in tmp_dir.name.lower():
                continue
            for output_f in tmp_dir.glob("*/tasks/*.output"):
                try: txt = output_f.read_text(errors="ignore")
                except Exception: continue
                t_min = (output_f.stat().st_mtime - js) / 60.0
                if t_min < 0 or t_min > trace_end_min + 5: continue
                last = None
                for pat, kw_filter in regexes:
                    for m in pat.finditer(txt):
                        try: sv = float(m.group(1))
                        except (ValueError, IndexError): continue
                        last = sv
                if last is not None:
                    events.append({"t_min": t_min, "score": last, "source": "tmp_subagent"})
    return events


def main():
    rows = []
    for task, arm, model, parent, resume in RUNS:
        # baseline
        bl = parent / "baseline_score.json"
        if bl.exists():
            try:
                d = json.loads(bl.read_text()).get("result", {})
                if d and d.get("score") is not None:
                    rows.append({
                        "task": task, "arm": arm, "model": model,
                        "run": "parent", "run_id": parent.name,
                        "t_min": 0.0, "score": d["score"], "cost_usd": 0.0,
                        "source": "baseline_json", "src_excerpt": "harness pre-agent",
                    })
            except Exception: pass

        # parent run
        ptrack, pcost = cost_track(parent)
        pt_end = ptrack[-1][0] if ptrack else 0
        for ev in collect_run_events(parent, task):
            ev.update({
                "task": task, "arm": arm, "model": model,
                "run": "parent", "run_id": parent.name,
                "cost_usd": cost_at(ptrack, ev["t_min"]),
                "src_excerpt": "",
            })
            rows.append(ev)
        # parent harness final
        fs = parent / "final_score.json"
        if fs.exists():
            try:
                fr = json.loads(fs.read_text()).get("result", {})
                if fr and fr.get("score") is not None:
                    rows.append({
                        "task": task, "arm": arm, "model": model,
                        "run": "parent", "run_id": parent.name,
                        "t_min": pt_end, "score": fr["score"], "cost_usd": pcost,
                        "source": "final_json", "src_excerpt": "harness post-agent",
                    })
            except Exception: pass

        # resume (shifted)
        if resume is not None:
            rtrack, rcost = cost_track(resume)
            rt_end = rtrack[-1][0] if rtrack else 0
            for ev in collect_run_events(resume, task):
                ev["t_min"] = pt_end + ev["t_min"]
                ev["cost_usd"] = pcost + cost_at(rtrack, ev["t_min"] - pt_end)
                ev.update({
                    "task": task, "arm": arm, "model": model,
                    "run": "resume", "run_id": resume.name,
                    "src_excerpt": "",
                    "source": ev["source"] + "(resume)",
                })
                rows.append(ev)
            fs = resume / "final_score.json"
            if fs.exists():
                try:
                    fr = json.loads(fs.read_text()).get("result", {})
                    if fr and fr.get("score") is not None:
                        rows.append({
                            "task": task, "arm": arm, "model": model,
                            "run": "resume", "run_id": resume.name,
                            "t_min": pt_end + rt_end,
                            "score": fr["score"],
                            "cost_usd": pcost + rcost,
                            "source": "final_json(resume)",
                            "src_excerpt": "harness post-agent",
                        })
                except Exception: pass
        # rust score-only re-eval (special case)
        if task == "rust_codecontests" and arm == "ARA-4.6":
            so = parent / "score_only_job7760733" / "final_score.json"
            if so.exists():
                try:
                    fr = json.loads(so.read_text()).get("result", {})
                    if fr and fr.get("score") is not None:
                        rt_end = cost_track(resume)[0][-1][0] if resume and cost_track(resume)[0] else 0
                        rows.append({
                            "task": task, "arm": arm, "model": model,
                            "run": "score_only", "run_id": "score_only_job7760733",
                            "t_min": pt_end + rt_end,
                            "score": fr["score"],
                            "cost_usd": pcost + (rcost if resume else 0),
                            "source": "score_only_json",
                            "src_excerpt": "post-resume canonical re-eval",
                        })
                except Exception: pass

    # Filter NaN, dedup
    print(f"\nbefore filter/dedup: {len(rows)}")
    seen = set(); out = []
    for r in sorted(rows, key=lambda x: (x["task"], x["arm"], x["t_min"])):
        sv = r["score"]
        try: sv = float(sv)
        except (TypeError, ValueError): continue
        if not math.isfinite(sv): continue
        k = (r["task"], r["arm"], round(r["t_min"], 0), round(sv, 4))
        if k in seen: continue
        seen.add(k); r["score"] = sv; out.append(r)
    print(f"after  filter/dedup: {len(out)}")

    out_csv = pathlib.Path(__file__).parent / "all_scores.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "task", "arm", "model", "run", "run_id", "t_min", "score",
            "cost_usd", "source", "src_excerpt",
        ])
        w.writeheader()
        for r in out: w.writerow(r)
    print(f"saved {out_csv}")

    # Per-task per-arm summary
    from collections import Counter
    print(f"\n=== per-task per-arm event counts ===")
    for task in ["triton_cumsum", "rust_codecontests", "nanogpt_chat_rl",
                  "fix_embedding", "restricted_mlm"]:
        for arm in ["paper-4.5", "ARA-4.5", "paper-4.6", "ARA-4.6"]:
            arm_rows = [r for r in out if r["task"] == task and r["arm"] == arm]
            if not arm_rows: continue
            best_op = (max if task in ("rust_codecontests", "nanogpt_chat_rl") else min)
            best = best_op(r["score"] for r in arm_rows)
            print(f"  {task:22s}  {arm:10s}  n={len(arm_rows):4d}  best={best:.4f}")


if __name__ == "__main__":
    main()
