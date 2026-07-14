#!/usr/bin/env python3
"""Understanding Layer QA — Per-Question Token Efficiency Experiment.

Each (question, condition) pair runs as an independent Claude Code subagent,
giving clean per-question token measurement from subagent metadata.

Two conditions:
  - ARA:      agent reads PAPER.md upfront + explores code/artifacts/{paper}/
  - Baseline: agent reads PDF (or polished paper) + explores code/repos/{paper}/

Usage:
  python run_understanding_token_eff.py                  # Run all papers
  python run_understanding_token_eff.py --papers p1 p2   # Run specific papers
  python run_understanding_token_eff.py --aggregate      # Only aggregate
  python run_understanding_token_eff.py --force           # Re-run existing
"""

import json
import os
import re
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent.parent
_code_dir = str(ROOT / "code")
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

from dotenv import load_dotenv
load_dotenv(ROOT / "code" / ".env")

REGISTRY_PATH = ROOT / "code" / "eval" / "paper_registry.json"
QUESTIONS_DIR = ROOT / "code" / "eval" / "questions"
RESULTS_DIR = ROOT / "code" / "eval" / "results"
ARTIFACTS_DIR = ROOT / "code" / "artifacts"
PDFS_DIR = ROOT / "code" / "pdfs"
REPOS_DIR = ROOT / "code" / "repos"
POLISHED_DIR = ROOT / "code" / "eval" / "extension" / "polished_papers"
SEND_SCRIPT = ROOT / "code" / "send.py"

MAX_CONCURRENT_PAIRS = 5   # 5 question-pairs → 10 simultaneous subagents
AGENT_TIMEOUT = 600        # 10 min per single-question agent
JUDGE_TIMEOUT = 600        # 10 min for judge (batches all Qs for a paper)
AGENT_MODEL = "claude-sonnet-4-6"
JUDGE_MODEL = "claude-sonnet-4-6"

# ── Helpers ─────────────────────────────────────────────────────────


def send_email(subject: str, body: str):
    """Send progress email via send.py."""
    try:
        subprocess.run(
            [sys.executable, str(SEND_SCRIPT),
             "--subject", subject, "--body", body],
            timeout=30, capture_output=True,
        )
    except Exception as e:
        print(f"[email] Failed: {e}")


def load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def load_questions_for_paper(paper_id: str, paper_info: dict) -> list[dict]:
    """Load questions according to paper-group rules (A+B or A+C)."""
    questions = []
    for cat_letter in paper_info.get("categories", ["A", "B"]):
        path = QUESTIONS_DIR / f"{paper_id}_cat{cat_letter}.json"
        if path.exists():
            data = json.loads(path.read_text())
            for q in data.get("questions", []):
                q["_category"] = cat_letter
                questions.append(q)
    return questions


def get_paper_md_content(paper_id: str) -> str:
    """Read PAPER.md content for an artifact."""
    paper_md = ARTIFACTS_DIR / paper_id / "PAPER.md"
    return paper_md.read_text() if paper_md.exists() else ""


def get_baseline_paper_path(paper_id: str, paper_info: dict) -> str:
    """Return the path the baseline agent should read."""
    benchmark = paper_info.get("benchmark", "paperbench")

    if benchmark == "rebench":
        task_name = paper_id.replace("rebench-", "")
        polished = POLISHED_DIR / f"{task_name}.md"
        if polished.exists():
            return str(polished)
        bd = paper_info.get("baseline_dir")
        if bd:
            return str(ROOT / bd)

    if benchmark == "speedrun":
        bd = paper_info.get("baseline_dir")
        if bd:
            return str(ROOT / bd)

    # PaperBench — prefer cached markdown over raw PDF
    pdf_path = paper_info.get("pdf_path")
    if pdf_path:
        full_pdf = ROOT / pdf_path
        try:
            from utils.pdf_extract import _pdf_hash
            cache_dir = ROOT / "code" / ".cache" / "pdf_md"
            h = _pdf_hash(str(full_pdf))
            cached_md = cache_dir / f"{h}.md"
            if cached_md.exists():
                return str(cached_md)
        except Exception:
            pass
        return str(full_pdf)
    return ""


# ── Subagent Execution ──────────────────────────────────────────────


def _run_claude(prompt: str, workdir: str, timeout: int,
                model: str = AGENT_MODEL) -> dict:
    """Spawn ``claude -p`` and return {text, meta, raw}."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}

    t0 = time.time()
    proc = subprocess.run(
        ["claude", "-p", prompt,
         "--output-format", "json",
         "--model", model],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    wall = time.time() - t0

    if proc.returncode != 0:
        stderr = (proc.stderr or "")[:500]
        raise RuntimeError(f"rc={proc.returncode}: {stderr}")

    try:
        blob = json.loads(proc.stdout)
    except json.JSONDecodeError:
        blob = {"result": proc.stdout}

    usage = blob.get("usage", {})
    meta = {
        "wall_s": round(wall, 1),
        "cost_usd": blob.get("total_cost_usd", 0),
        "duration_ms": blob.get("duration_ms", 0),
        "duration_api_ms": blob.get("duration_api_ms", 0),
        "num_turns": blob.get("num_turns", 0),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0),
        "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
    }
    return {"text": blob.get("result", proc.stdout), "meta": meta, "raw": blob}


# ── Prompt Builders ─────────────────────────────────────────────────


def _ara_prompt(paper_id: str, paper_md: str,
                artifact_dir: str, q: dict) -> str:
    return f"""You are a senior ML researcher answering ONE question about a research paper using its structured ARA artifact.

## Paper Overview (PAPER.md — already loaded for you)

{paper_md}

## Instructions

The full artifact is at: `{artifact_dir}`
You have Read, Grep, and Glob tools. Use them to find the precise answer.

### Search strategy
1. **Grep first** — key terms from the question across the whole artifact.
2. **Navigate by layer**:
   - Numbers / results → `evidence/tables/`, `evidence/figures/`
   - Method details → `logic/solution/algorithm.md`, `logic/solution/architecture.md`
   - Hyperparams → `src/configs/training.md`, `src/configs/model.md`
   - Experimental setup → `logic/experiments.md`, `src/environment.md`
   - Design rationale → `logic/problem.md`, `logic/solution/heuristics.md`
   - Dead ends → `trace/exploration_tree.yaml`
   - Code → `src/execution/*.py`
3. Cross-validate evidence vs. claims, configs vs. experiments.
4. If initial search fails, broaden — synonyms, abbreviations, Grep across ALL files.

### Rules
- Answer ONLY from artifact content. Do NOT hallucinate.
- Cite exact numbers, equations, source file paths.
- If the question is genuinely unanswerable from the artifact, say "I cannot find this information in the artifacts." — but only after checking ≥3 locations.
- Do NOT access code/pdfs/ or code/repos/.

## Question

**{q['id']}**: {q['question']}

## Output — a single JSON object, nothing else

```json
{{"id": "{q['id']}", "answer": "your detailed answer"}}
```"""


def _baseline_prompt(paper_id: str, paper_path: str,
                     repo_dir: str | None, q: dict) -> str:
    repo_block = ""
    if repo_dir and Path(repo_dir).is_dir():
        repo_block = (
            f"\n## GitHub Repository\n\n"
            f"Source code at: `{repo_dir}`\n"
            f"Use Grep/Read to find hyperparameters, implementation details, configs.\n"
        )

    return f"""You are a senior ML researcher answering ONE question about a research paper.

## Instructions

Read the paper at: `{paper_path}`
You have Read, Grep, and Glob tools.

1. Read the paper to understand its full content.
2. Use Grep to search for specific numbers, terms, section references.
3. Answer based ONLY on what you find.
4. If you cannot find the answer, say "I cannot find this information in the paper."
5. Some questions are deliberately unanswerable — do NOT fabricate answers.
6. Do NOT access code/artifacts/.
{repo_block}
## Question

**{q['id']}**: {q['question']}

## Output — a single JSON object, nothing else

```json
{{"id": "{q['id']}", "answer": "your detailed answer"}}
```"""


# ── Answer Parsing ──────────────────────────────────────────────────


def _parse_answer(text: str) -> str:
    """Extract answer string from single-question agent output."""
    # Try markdown fence
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(1).strip())
            if isinstance(obj, dict) and "answer" in obj:
                return obj["answer"]
        except json.JSONDecodeError:
            pass

    # Direct JSON
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict) and "answer" in obj:
            return obj["answer"]
    except json.JSONDecodeError:
        pass

    # Regex for "answer": "..."
    m = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
    if m:
        a = m.group(1).replace('\\"', '"').replace('\\n', '\n')
        return a

    return text.strip()


# ── Per-Paper Pipeline ──────────────────────────────────────────────


def run_paper(paper_id: str, paper_info: dict) -> dict | None:
    """Run all question-pairs for one paper, judge, and save."""
    questions = load_questions_for_paper(paper_id, paper_info)
    if not questions:
        print(f"[paper] SKIP {paper_id}: no questions")
        return None

    n_q = len(questions)
    print(f"\n{'='*60}\n[paper] {paper_id}: {n_q} questions\n{'='*60}")

    paper_md = get_paper_md_content(paper_id)
    artifact_dir = str(ROOT / paper_info["artifact_dir"])
    baseline_path = get_baseline_paper_path(paper_id, paper_info)
    repo_dir = str(REPOS_DIR / paper_id) if (REPOS_DIR / paper_id).is_dir() else None

    # ── Run per-question agents ─────────────────────────────────────
    pq = {}  # qid → result dict

    def _pair(q):
        qid = q["id"]
        r = {"id": qid, "category": q.get("_category", "A"),
             "difficulty": q.get("difficulty", "unknown"),
             "source": q.get("source", "")}

        # ARA
        try:
            out = _run_claude(
                _ara_prompt(paper_id, paper_md, artifact_dir, q),
                workdir=artifact_dir, timeout=AGENT_TIMEOUT)
            r["ara_answer"] = _parse_answer(out["text"])
            r["ara_meta"] = out["meta"]
        except Exception as e:
            r["ara_answer"] = f"ERROR: {e}"
            r["ara_meta"] = {"error": str(e), "cost_usd": 0}
            print(f"  [err] ARA  {qid}: {e}")

        # Baseline
        try:
            out = _run_claude(
                _baseline_prompt(paper_id, baseline_path, repo_dir, q),
                workdir=str(ROOT), timeout=AGENT_TIMEOUT)
            r["baseline_answer"] = _parse_answer(out["text"])
            r["baseline_meta"] = out["meta"]
        except Exception as e:
            r["baseline_answer"] = f"ERROR: {e}"
            r["baseline_meta"] = {"error": str(e), "cost_usd": 0}
            print(f"  [err] BL   {qid}: {e}")

        return qid, r

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PAIRS * 2) as pool:
        futs = {pool.submit(_pair, q): q["id"] for q in questions}
        for f in as_completed(futs):
            qid, r = f.result()
            pq[qid] = r
            ac = r.get("ara_meta", {}).get("cost_usd", 0)
            bc = r.get("baseline_meta", {}).get("cost_usd", 0)
            print(f"  [done] {qid}  ARA ${ac:.4f}  BL ${bc:.4f}")

    # ── Judge ───────────────────────────────────────────────────────
    print(f"[judge] {paper_id} ({n_q} Qs)…")
    ara_map = {qid: r.get("ara_answer", "") for qid, r in pq.items()}
    bl_map = {qid: r.get("baseline_answer", "") for qid, r in pq.items()}

    blocks = []
    for q in questions:
        qid = q["id"]
        gold = q.get("gold_answer", "N/A")
        ara_gold = q.get("ara_gold_answer", gold)
        blocks.append(
            f"### {qid}\n"
            f"**Question**: {q['question']}\n\n"
            f"**Gold answer (baseline)**: {gold}\n"
            f"**Gold answer (ARA)**: {ara_gold}\n\n"
            f"**ARA answer**: {ara_map.get(qid, 'N/A')}\n\n"
            f"**Baseline answer**: {bl_map.get(qid, 'N/A')}"
        )

    judge_prompt = f"""You are an expert ML evaluator. For each question below judge BOTH the ARA and Baseline answers independently against their respective gold answers.

## Scoring
- 1.0 = correct (captures essential facts, numbers, concepts)
- 0.5 = partially correct (right idea, missing key details or numbers)
- 0.0 = incorrect (wrong facts, missing key info, or hallucinated answer to unanswerable question)

For unanswerable questions the agent is correct if it says the info is unavailable.
Use "Gold answer (ARA)" for judging ARA, "Gold answer (baseline)" for Baseline.

## Questions

{chr(10).join(blocks)}

## Output — ONLY a JSON array

```json
[{{"id":"qid","ara_score":1.0,"baseline_score":0.5,"ara_rationale":"...","baseline_rationale":"..."}}]
```"""

    judge_results = []
    try:
        jr = _run_claude(judge_prompt, workdir=str(ROOT),
                         timeout=JUDGE_TIMEOUT, model=JUDGE_MODEL)
        text = jr["text"]
        # Parse array
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        candidate = m.group(1).strip() if m else text.strip()
        try:
            judge_results = json.loads(candidate)
        except json.JSONDecodeError:
            start = text.index("[")
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "[":
                    depth += 1
                elif text[i] == "]":
                    depth -= 1
                    if depth == 0:
                        judge_results = json.loads(text[start:i + 1])
                        break
    except Exception as e:
        print(f"  [judge err] {paper_id}: {e}")

    jmap = {j["id"]: j for j in judge_results if isinstance(j, dict)}

    for qid, r in pq.items():
        j = jmap.get(qid, {})
        r["ara_score"] = j.get("ara_score", 0.0)
        r["baseline_score"] = j.get("baseline_score", 0.0)
        r["ara_rationale"] = j.get("ara_rationale", "")
        r["baseline_rationale"] = j.get("baseline_rationale", "")

    # ── Paper-level stats ───────────────────────────────────────────
    ara_acc = sum(r.get("ara_score", 0) for r in pq.values()) / n_q
    bl_acc = sum(r.get("baseline_score", 0) for r in pq.values()) / n_q
    ara_cost = sum(r.get("ara_meta", {}).get("cost_usd", 0) for r in pq.values())
    bl_cost = sum(r.get("baseline_meta", {}).get("cost_usd", 0) for r in pq.values())
    ara_tokens_in = sum(r.get("ara_meta", {}).get("input_tokens", 0) for r in pq.values())
    ara_tokens_out = sum(r.get("ara_meta", {}).get("output_tokens", 0) for r in pq.values())
    bl_tokens_in = sum(r.get("baseline_meta", {}).get("input_tokens", 0) for r in pq.values())
    bl_tokens_out = sum(r.get("baseline_meta", {}).get("output_tokens", 0) for r in pq.values())

    result = {
        "paper_id": paper_id,
        "benchmark": paper_info.get("benchmark", "unknown"),
        "n_questions": n_q,
        "model": AGENT_MODEL,
        "ara_accuracy": round(ara_acc, 4),
        "baseline_accuracy": round(bl_acc, 4),
        "delta": round(ara_acc - bl_acc, 4),
        "ara_total_cost_usd": round(ara_cost, 6),
        "baseline_total_cost_usd": round(bl_cost, 6),
        "ara_avg_cost_per_q": round(ara_cost / n_q, 6),
        "baseline_avg_cost_per_q": round(bl_cost / n_q, 6),
        "ara_total_input_tokens": ara_tokens_in,
        "ara_total_output_tokens": ara_tokens_out,
        "baseline_total_input_tokens": bl_tokens_in,
        "baseline_total_output_tokens": bl_tokens_out,
        "per_question": [pq[q["id"]] for q in questions if q["id"] in pq],
    }

    out = RESULTS_DIR / f"understanding_token_eff_{paper_id}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"[paper] {paper_id} DONE  "
          f"ARA {ara_acc:.0%} (${ara_cost:.3f})  "
          f"BL {bl_acc:.0%} (${bl_cost:.3f})  "
          f"delta {ara_acc - bl_acc:+.0%}")
    return result


# ── Aggregation ─────────────────────────────────────────────────────


def aggregate_results() -> dict | None:
    files = sorted(RESULTS_DIR.glob("understanding_token_eff_*.json"))
    files = [f for f in files if "aggregate" not in f.name]
    if not files:
        print("[agg] No result files")
        return None

    all_q: list[dict] = []
    papers: list[dict] = []

    for f in files:
        d = json.loads(f.read_text())
        pid = d["paper_id"]
        bm = d.get("benchmark", "unknown")
        papers.append({k: d[k] for k in (
            "paper_id", "benchmark", "n_questions",
            "ara_accuracy", "baseline_accuracy", "delta",
            "ara_total_cost_usd", "baseline_total_cost_usd",
            "ara_avg_cost_per_q", "baseline_avg_cost_per_q",
            "ara_total_input_tokens", "ara_total_output_tokens",
            "baseline_total_input_tokens", "baseline_total_output_tokens",
        ) if k in d})

        for q in d.get("per_question", []):
            all_q.append({
                "paper_id": pid, "benchmark": bm,
                "id": q["id"],
                "category": q.get("category", "A"),
                "difficulty": q.get("difficulty", "unknown"),
                "ara_score": q.get("ara_score", 0),
                "bl_score": q.get("baseline_score", 0),
                "ara_cost": q.get("ara_meta", {}).get("cost_usd", 0),
                "bl_cost": q.get("baseline_meta", {}).get("cost_usd", 0),
                "ara_in_tok": q.get("ara_meta", {}).get("input_tokens", 0),
                "ara_out_tok": q.get("ara_meta", {}).get("output_tokens", 0),
                "bl_in_tok": q.get("baseline_meta", {}).get("input_tokens", 0),
                "bl_out_tok": q.get("baseline_meta", {}).get("output_tokens", 0),
                "ara_turns": q.get("ara_meta", {}).get("num_turns", 0),
                "bl_turns": q.get("baseline_meta", {}).get("num_turns", 0),
            })

    def _agg(items):
        n = len(items)
        if n == 0:
            return {}
        aa = sum(i["ara_score"] for i in items) / n
        ba = sum(i["bl_score"] for i in items) / n
        ac = sum(i["ara_cost"] for i in items)
        bc = sum(i["bl_cost"] for i in items)
        return {
            "n": n,
            "ara_accuracy": round(aa, 4),
            "baseline_accuracy": round(ba, 4),
            "delta": round(aa - ba, 4),
            "ara_total_cost": round(ac, 4),
            "baseline_total_cost": round(bc, 4),
            "ara_avg_cost_per_q": round(ac / n, 6),
            "baseline_avg_cost_per_q": round(bc / n, 6),
            "cost_ratio": round(ac / bc, 3) if bc > 0 else None,
            "ara_avg_turns": round(sum(i["ara_turns"] for i in items) / n, 1),
            "bl_avg_turns": round(sum(i["bl_turns"] for i in items) / n, 1),
        }

    by_cat = {cat: _agg([q for q in all_q if q["category"] == cat])
              for cat in sorted({q["category"] for q in all_q})}
    by_diff = {d: _agg([q for q in all_q if q["difficulty"] == d])
               for d in sorted({q["difficulty"] for q in all_q})}
    by_grp = {g: _agg([q for q in all_q if q["benchmark"] == g])
              for g in sorted({q["benchmark"] for q in all_q})}

    overall = _agg(all_q)

    agg = {
        "n_papers": len(papers),
        "n_questions": len(all_q),
        "model": AGENT_MODEL,
        "overall": overall,
        "by_category": by_cat,
        "by_difficulty": by_diff,
        "by_paper_group": by_grp,
        "per_paper": papers,
    }

    out = RESULTS_DIR / "understanding_token_eff_aggregate.json"
    out.write_text(json.dumps(agg, indent=2, ensure_ascii=False))
    print(f"\n[agg] Saved → {out}")

    # ── Print table ─────────────────────────────────────────────────
    o = overall
    print(f"\n{'='*80}")
    print(f"TOKEN EFFICIENCY SUMMARY  ({o['n']} Qs, {len(papers)} papers, model={AGENT_MODEL})")
    print(f"{'='*80}")
    print(f"Overall  ARA {o['ara_accuracy']:.1%}  BL {o['baseline_accuracy']:.1%}  "
          f"Δ {o['delta']:+.1%}   "
          f"cost ARA ${o['ara_total_cost']:.2f}  BL ${o['baseline_total_cost']:.2f}  "
          f"ratio {o.get('cost_ratio', 'N/A')}")

    print(f"\nBy Category:")
    print(f"  {'Cat':<5} {'N':>4} {'ARA':>7} {'BL':>7} {'Δ':>7} "
          f"{'ARA$/Q':>9} {'BL$/Q':>9} {'ratio':>7}")
    for c, s in sorted(by_cat.items()):
        print(f"  {c:<5} {s['n']:>4} {s['ara_accuracy']:>6.1%} {s['baseline_accuracy']:>6.1%} "
              f"{s['delta']:>+6.1%} "
              f"{s['ara_avg_cost_per_q']:>9.5f} {s['baseline_avg_cost_per_q']:>9.5f} "
              f"{s.get('cost_ratio', 'N/A'):>7}")

    print(f"\nBy Difficulty:")
    print(f"  {'Tier':<16} {'N':>4} {'ARA':>7} {'BL':>7} {'Δ':>7}")
    for d, s in sorted(by_diff.items()):
        print(f"  {d:<16} {s['n']:>4} {s['ara_accuracy']:>6.1%} "
              f"{s['baseline_accuracy']:>6.1%} {s['delta']:>+6.1%}")

    print(f"\nBy Paper Group:")
    for g, s in sorted(by_grp.items()):
        print(f"  {g}: ARA {s['ara_accuracy']:.1%}  BL {s['baseline_accuracy']:.1%}  "
              f"Δ {s['delta']:+.1%}  n={s['n']}")

    return agg


# ── Main ────────────────────────────────────────────────────────────


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers", nargs="+")
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.aggregate:
        aggregate_results()
        return

    registry = load_registry()
    pf = set(args.papers) if args.papers else None

    todo = []
    for p in registry["papers"]:
        pid = p["paper_id"]
        if pf and pid not in pf:
            continue
        out = RESULTS_DIR / f"understanding_token_eff_{pid}.json"
        if out.exists() and not args.force:
            print(f"[skip] {pid}")
            continue
        todo.append(p)

    print(f"[main] {len(todo)} papers to run (model={AGENT_MODEL})")
    send_email(
        "Understanding Token Eff — START",
        f"Running {len(todo)} papers: "
        + ", ".join(p["paper_id"] for p in todo),
    )

    done, fail = 0, 0
    for i, p in enumerate(todo):
        pid = p["paper_id"]
        try:
            r = run_paper(pid, p)
            if r:
                done += 1
                if done % 5 == 0 or done == len(todo):
                    send_email(
                        f"Token Eff — {done}/{len(todo)} done",
                        f"Latest: {pid}\n"
                        f"  ARA  {r['ara_accuracy']:.1%} ${r['ara_total_cost_usd']:.3f}\n"
                        f"  BL   {r['baseline_accuracy']:.1%} ${r['baseline_total_cost_usd']:.3f}",
                    )
        except Exception as e:
            fail += 1
            print(f"[FATAL] {pid}: {e}")
            traceback.print_exc()
            send_email(f"Token Eff — ERROR {pid}", str(e)[:500])

    agg = aggregate_results()
    if agg:
        o = agg["overall"]
        send_email(
            "Understanding Token Eff — COMPLETE",
            f"{done} ok, {fail} fail\n\n"
            f"Overall: ARA {o['ara_accuracy']:.1%} vs BL {o['baseline_accuracy']:.1%} "
            f"(Δ {o['delta']:+.1%})\n"
            f"Cost: ARA ${o['ara_total_cost']:.2f}  BL ${o['baseline_total_cost']:.2f}  "
            f"ratio={o.get('cost_ratio')}",
        )


if __name__ == "__main__":
    # Unbuffer stdout for real-time logging when redirected
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    main()
