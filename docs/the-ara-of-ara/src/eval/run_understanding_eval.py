"""Understanding Layer Evaluation — Sub-Agent Answering + Judging Pipeline.

Uses Claude Code sub-agents for autonomous artifact/paper exploration:
  Step 2: Agent answering (ARA sub-agent + PDF sub-agent)
  Step 3: Judging (Opus judge, absolute correctness vs gold answers)
  Step 4: Metrics & analysis

Usage:
  python run_understanding_eval.py answer   # Run agents (Step 2)
  python run_understanding_eval.py judge    # Run judge (Step 3)
  python run_understanding_eval.py analyze  # Compute metrics (Step 4)
  python run_understanding_eval.py all      # Run everything

Options:
  --papers p1 p2 ...   Only run on specified papers
  --force              Re-run even if results exist
"""

import json
import os
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_code_dir = str(Path(__file__).resolve().parent.parent)
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

from dotenv import load_dotenv

# ROOT = project root (parent of code/)
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / "code" / ".env")

REGISTRY_PATH = ROOT / "code" / "eval" / "paper_registry.json"
QUESTIONS_DIR = ROOT / "code" / "eval" / "questions"
RESULTS_DIR = ROOT / "code" / "eval" / "results" / "understanding"
PROMPTS_DIR = ROOT / "code" / "eval" / "prompts"

MAX_WORKERS = 5
JUDGE_MODEL = "claude-sonnet-4-6"

# Ensure output dirs
(RESULTS_DIR / "answers").mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "judging").mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "analysis").mkdir(parents=True, exist_ok=True)


def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def load_questions(paper_id: str) -> list[dict]:
    """Load all questions for a paper across categories."""
    questions = []
    for cat in ("catA", "catB", "catC"):
        path = QUESTIONS_DIR / f"{paper_id}_{cat}.json"
        if path.exists():
            data = json.loads(path.read_text())
            for q in data.get("questions", []):
                q["_category"] = cat.replace("cat", "")
                questions.append(q)
    return questions


def format_questions_block(questions: list[dict]) -> str:
    """Format questions for agent prompt."""
    lines = []
    for q in questions:
        lines.append(f"### Question {q['id']}")
        lines.append(f"{q['question']}")
        lines.append("")
    return "\n".join(lines)


# ── Sub-Agent Execution ──────────────────────────────────────────────


def _run_claude_subagent(prompt: str, workdir: str, timeout: int = 300) -> str:
    """Spawn a Claude Code sub-agent and return its output.

    Uses `claude -p` (print mode) which runs a single prompt non-interactively,
    with full tool access (Read, Grep, Glob) scoped to the working directory.
    """
    # Strip nesting-prevention env vars so sub-agent can launch
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )

    if result.returncode != 0:
        stderr = result.stderr[:500] if result.stderr else ""
        raise RuntimeError(f"Sub-agent failed (rc={result.returncode}): {stderr}")

    return result.stdout


def _normalize_answer_keys(d: dict) -> dict:
    """Normalize alternative wrapper keys ('responses', 'results') to 'answers'."""
    for key in ("responses", "results"):
        if key in d and "answers" not in d:
            d["answers"] = d.pop(key)
    return d


def _extract_individual_answers(raw: str) -> list[dict]:
    """Extract individual answer objects using progressively looser patterns."""
    import re
    answers = []
    seen_ids = set()

    # Pattern A: Full "id" + "answer" pairs with properly escaped strings
    for m in re.finditer(
        r'"id"\s*:\s*"([^"]+)"\s*,\s*"answer"\s*:\s*"((?:[^"\\]|\\.)*)"',
        raw, re.DOTALL,
    ):
        qid, answer = m.group(1), m.group(2)
        if qid not in seen_ids:
            answer = answer.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
            answers.append({"id": qid, "answer": answer})
            seen_ids.add(qid)

    if answers:
        return answers

    # Pattern B: Walk from "id":... to find the answer value manually
    obj_starts = list(re.finditer(r'"id"\s*:\s*"([^"]+)"\s*,\s*"answer"\s*:\s*"', raw))
    for m in obj_starts:
        qid = m.group(1)
        if qid in seen_ids:
            continue
        start_pos = m.end()
        i = start_pos
        while i < len(raw):
            if raw[i] == '\\':
                i += 2
            elif raw[i] == '"':
                answer_text = raw[start_pos:i]
                answer_text = answer_text.replace('\\"', '"').replace('\\n', '\n')
                answers.append({"id": qid, "answer": answer_text})
                seen_ids.add(qid)
                break
            else:
                i += 1

    return answers


def _repair_truncated_json(text: str, agent_type: str = "unknown") -> dict | None:
    """Attempt to salvage answers from truncated JSON output."""
    # First try extracting individual answers from the text
    answers = _extract_individual_answers(text)
    if answers:
        return {"agent_type": agent_type, "answers": answers}

    # Try closing open brackets/braces
    text = text.rstrip().rstrip(',')
    for suffix in ['"}]}', '"}\n]}', ']\n}', ']}', '}']:
        try:
            parsed = json.loads(text + suffix)
            if isinstance(parsed, dict):
                parsed = _normalize_answer_keys(parsed)
                if "answers" in parsed:
                    return parsed
        except json.JSONDecodeError:
            continue

    return None


def _parse_agent_json(raw: str, agent_type: str) -> dict:
    """Extract JSON answer object from sub-agent output.

    Tries multiple extraction strategies in order of reliability:
    1. Direct JSON parse of full output
    2. Markdown JSON fences (prefers LAST fence — agents often emit intermediate JSON)
    3. Brace-matching for known wrapper patterns
    4. Individual answer block regex extraction
    5. Truncated JSON repair
    """
    import re

    # Strategy 1: Direct parse of full output
    try:
        parsed = json.loads(raw.strip())
        if isinstance(parsed, dict):
            parsed = _normalize_answer_keys(parsed)
            if "answers" in parsed:
                return parsed
    except json.JSONDecodeError:
        pass

    # Strategy 2: Markdown fences — take the LAST ```json block
    # (agents often emit intermediate JSON; the final block is the answer)
    json_fences = list(re.finditer(r"```(?:json)?\s*\n(.*?)\n\s*```", raw, re.DOTALL))
    for match in reversed(json_fences):
        candidate = match.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                parsed = _normalize_answer_keys(parsed)
                if "answers" in parsed:
                    return parsed
        except json.JSONDecodeError:
            # Try repairing truncated JSON inside the fence
            repaired = _repair_truncated_json(candidate, agent_type)
            if repaired and len(repaired.get("answers", [])) > 0:
                return repaired

    # Strategy 3: Brace-matching for known JSON wrapper patterns
    for marker in ['{"answers"', '{"agent_type"', '{"responses"', '{"results"']:
        idx = raw.find(marker)
        if idx == -1:
            continue
        candidate = raw[idx:]
        depth = 0
        for i, ch in enumerate(candidate):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(candidate[:i + 1])
                        parsed = _normalize_answer_keys(parsed)
                        if "answers" in parsed:
                            return parsed
                    except json.JSONDecodeError:
                        pass
                    break

    # Strategy 4: Individual answer block extraction via regex
    answers = _extract_individual_answers(raw)
    if answers:
        return {"agent_type": agent_type, "answers": answers}

    # Strategy 5: Truncated JSON repair — find start of JSON and try to salvage
    for marker in ['{"answers"', '{"agent_type"']:
        idx = raw.find(marker)
        if idx != -1:
            repaired = _repair_truncated_json(raw[idx:], agent_type)
            if repaired and len(repaired.get("answers", [])) > 0:
                return repaired

    return {"agent_type": agent_type, "answers": []}


# ── Step 2: Agent Answering ──────────────────────────────────────────


def _build_ara_prompt(paper_id: str, artifact_dir: str, questions: list[dict],
                      repo_dir: str | None = None) -> str:
    """Build prompt for ARA sub-agent."""
    template = (PROMPTS_DIR / "ara_agent.md").read_text()
    questions_block = format_questions_block(questions)

    repo_instructions = ""
    if repo_dir and Path(repo_dir).is_dir():
        repo_instructions = (
            "\n## GitHub Repository\n\n"
            f"The paper's source code is available at: `{repo_dir}`\n"
            "Use Grep and Read to search the repo for exact hyperparameters, "
            "implementation details, and config values that supplement the artifact.\n"
        )

    prompt = template.replace("{questions_block}", questions_block)
    prompt = prompt.replace("{n_questions}", str(len(questions)))
    prompt = prompt.replace("{repo_instructions}", repo_instructions)
    return prompt


def _build_pdf_prompt(paper_id: str, paper_path: str, questions: list[dict],
                      repo_dir: str | None = None) -> str:
    """Build prompt for PDF sub-agent."""
    template = (PROMPTS_DIR / "pdf_agent.md").read_text()
    questions_block = format_questions_block(questions)

    repo_instructions = ""
    if repo_dir and Path(repo_dir).is_dir():
        repo_instructions = (
            "\n## GitHub Repository\n\n"
            f"The paper's source code is available at: `{repo_dir}`\n"
            "Use Grep and Read to search the repo for exact hyperparameters, "
            "implementation details, and config values that supplement the paper.\n"
        )

    prompt = template.replace("{paper_path}", paper_path)
    prompt = prompt.replace("{questions_block}", questions_block)
    prompt = prompt.replace("{n_questions}", str(len(questions)))
    prompt = prompt.replace("{repo_instructions}", repo_instructions)
    return prompt


def run_ara_agent(paper_id: str, artifact_dir: str, questions: list[dict],
                  repo_dir: str | None = None) -> dict:
    """Run ARA sub-agent to answer questions by exploring the artifact."""
    prompt = _build_ara_prompt(paper_id, artifact_dir, questions, repo_dir)

    t0 = time.time()
    raw = _run_claude_subagent(prompt, workdir=artifact_dir, timeout=900)
    elapsed = time.time() - t0

    # Save raw output for debugging / re-parsing
    raw_path = RESULTS_DIR / "answers" / f"{paper_id}_ara_raw.txt"
    raw_path.write_text(raw)

    result = _parse_agent_json(raw, "ARA")
    result["paper_id"] = paper_id
    result["elapsed_s"] = round(elapsed, 1)
    result["method"] = "claude_code_subagent"

    # Validate answer count
    n_parsed = len(result.get("answers", []))
    n_expected = len(questions)
    if n_parsed < n_expected:
        print(f"[answer] WARNING: {paper_id} ARA parsed {n_parsed}/{n_expected} answers "
              f"(raw: {len(raw)} chars, saved to {raw_path.name})")

    return result


def run_pdf_agent(paper_id: str, paper_info: dict, questions: list[dict],
                  repo_dir: str | None = None) -> dict:
    """Run PDF sub-agent to answer questions from the paper."""
    # Determine paper path
    if paper_info["benchmark"] == "paperbench":
        paper_path = str(ROOT / paper_info["pdf_path"])
        # Use cached markdown if available
        from utils.pdf_extract import _pdf_hash
        cache_dir = ROOT / "code" / ".cache" / "pdf_md"
        content_hash = _pdf_hash(paper_path)
        cached_md = cache_dir / f"{content_hash}.md"
        if cached_md.exists():
            paper_path = str(cached_md)
    else:
        # RE-Bench/Speedrun: use task directory
        paper_path = str(ROOT / paper_info.get("baseline_dir", paper_info["artifact_dir"]))

    prompt = _build_pdf_prompt(paper_id, paper_path, questions, repo_dir)

    t0 = time.time()
    # Use project root as workdir so agent can access both paper and repo
    raw = _run_claude_subagent(prompt, workdir=str(ROOT), timeout=900)
    elapsed = time.time() - t0

    # Save raw output for debugging / re-parsing
    raw_path = RESULTS_DIR / "answers" / f"{paper_id}_baseline_raw.txt"
    raw_path.write_text(raw)

    result = _parse_agent_json(raw, "PDF")
    result["paper_id"] = paper_id
    result["elapsed_s"] = round(elapsed, 1)
    result["method"] = "claude_code_subagent"

    # Validate answer count
    n_parsed = len(result.get("answers", []))
    n_expected = len(questions)
    if n_parsed < n_expected:
        print(f"[answer] WARNING: {paper_id} baseline parsed {n_parsed}/{n_expected} answers "
              f"(raw: {len(raw)} chars, saved to {raw_path.name})")

    return result


def step2_answer(skip_existing: bool = True, paper_filter: set | None = None):
    """Run ARA + baseline agents for all papers."""
    registry = load_registry()
    tasks = []

    for p in registry["papers"]:
        pid = p["paper_id"]
        if paper_filter and pid not in paper_filter:
            continue

        questions = load_questions(pid)
        if not questions:
            print(f"[answer] SKIP {pid} (no questions)")
            continue

        ara_out = RESULTS_DIR / "answers" / f"{pid}_ara.json"
        pdf_out = RESULTS_DIR / "answers" / f"{pid}_baseline.json"

        if skip_existing and ara_out.exists() and pdf_out.exists():
            print(f"[answer] SKIP {pid} (already answered)")
            continue

        tasks.append((pid, p, questions))

    print(f"[answer] Running sub-agents for {len(tasks)} papers...")

    def _run_pair(task_info):
        pid, paper_info, questions = task_info
        artifact_dir = str(ROOT / paper_info["artifact_dir"])
        repo_dir = None
        repo_path = ROOT / "code" / "repos" / pid
        if repo_path.is_dir():
            repo_dir = str(repo_path)

        results = {}
        try:
            ara_result = run_ara_agent(pid, artifact_dir, questions, repo_dir)
            (RESULTS_DIR / "answers" / f"{pid}_ara.json").write_text(
                json.dumps(ara_result, indent=2, ensure_ascii=False))
            results["ara"] = len(ara_result.get("answers", []))

            pdf_result = run_pdf_agent(pid, paper_info, questions, repo_dir)
            (RESULTS_DIR / "answers" / f"{pid}_baseline.json").write_text(
                json.dumps(pdf_result, indent=2, ensure_ascii=False))
            results["baseline"] = len(pdf_result.get("answers", []))

            return pid, True, results
        except Exception as e:
            print(f"[answer] ERROR {pid}: {e}")
            traceback.print_exc()
            return pid, False, {}

    success = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_run_pair, t): t for t in tasks}
        for future in as_completed(futures):
            pid, ok, results = future.result()
            if ok:
                success += 1
                print(f"[answer] OK: {pid} (ARA: {results.get('ara', 0)}, "
                      f"Baseline: {results.get('baseline', 0)})")
            else:
                print(f"[answer] FAIL: {pid}")

    print(f"[answer] Done: {success}/{len(tasks)} papers answered")


# ── Step 3: Absolute Correctness Scoring ─────────────────────────────


def _build_grading_prompt(questions: list[dict], answer_lookup: dict) -> str:
    """Build a grading prompt for the judge sub-agent."""
    template = (PROMPTS_DIR / "judge_agent.md").read_text()
    blocks = []
    for q in questions:
        qid = q["id"]
        gold = q.get("gold_answer", "N/A")
        ans = answer_lookup.get(qid, "No answer provided")
        blocks.append(
            f"### {qid}\n"
            f"**Question**: {q['question']}\n"
            f"**Gold Answer**: {gold}\n"
            f"**Agent Answer**: {ans}"
        )
    return template.replace("{grading_blocks}", "\n\n".join(blocks))


def _run_judge_subagent(prompt: str) -> list[dict]:
    """Run judge via claude -p sub-agent and parse grading results.

    The judge returns a JSON array: [{"id": ..., "correct": ..., "rationale": ...}]
    This differs from agent output ({"answers": [...]}) so we parse accordingly.
    """
    import re

    raw = _run_claude_subagent(prompt, workdir=str(ROOT), timeout=300)

    # Strip markdown fences
    cleaned = raw
    if "```json" in cleaned:
        match = re.search(r"```json\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
    elif "```" in cleaned:
        match = re.search(r"```\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()

    # Try direct parse as JSON array (expected judge format)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed
    except json.JSONDecodeError:
        pass

    # Try finding JSON array in raw output
    try:
        start = raw.index("[")
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == "[":
                depth += 1
            elif raw[i] == "]":
                depth -= 1
                if depth == 0:
                    result = json.loads(raw[start:i + 1])
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    break
    except (ValueError, json.JSONDecodeError):
        pass

    # Fallback: try _parse_agent_json in case judge used {"answers": [...]} format
    parsed = _parse_agent_json(raw, "judge")
    if parsed.get("answers"):
        return parsed["answers"]

    print(f"[judge] WARNING: Could not parse judge output ({len(raw)} chars)")
    return []


def step3_judge(skip_existing: bool = True, paper_filter: set | None = None):
    """Score each agent's answers independently against gold criteria."""
    registry = load_registry()
    tasks = []

    for p in registry["papers"]:
        pid = p["paper_id"]
        if paper_filter and pid not in paper_filter:
            continue

        ara_path = RESULTS_DIR / "answers" / f"{pid}_ara.json"
        pdf_path = RESULTS_DIR / "answers" / f"{pid}_baseline.json"
        judged_path = RESULTS_DIR / "judging" / f"{pid}_judged.json"

        if not ara_path.exists() or not pdf_path.exists():
            continue
        if skip_existing and judged_path.exists():
            print(f"[judge] SKIP {pid} (already judged)")
            continue

        questions = load_questions(pid)
        if not questions:
            continue

        ara_answers = json.loads(ara_path.read_text())
        pdf_answers = json.loads(pdf_path.read_text())
        tasks.append((pid, questions, ara_answers, pdf_answers))

    print(f"[judge] Scoring {len(tasks)} papers (sub-agent judge)...")

    def _judge_paper(task_info):
        pid, questions, ara_answers, pdf_answers = task_info

        ara_lookup = {a["id"]: a["answer"] for a in ara_answers.get("answers", [])}
        pdf_lookup = {a["id"]: a["answer"] for a in pdf_answers.get("answers", [])}

        ara_prompt = _build_grading_prompt(questions, ara_lookup)
        pdf_prompt = _build_grading_prompt(questions, pdf_lookup)

        ara_grades = _run_judge_subagent(ara_prompt)
        pdf_grades = _run_judge_subagent(pdf_prompt)

        ara_map = {g["id"]: g for g in ara_grades}
        pdf_map = {g["id"]: g for g in pdf_grades}

        per_question = []
        for q in questions:
            qid = q["id"]
            ara_g = ara_map.get(qid, {"correct": False, "rationale": "missing"})
            pdf_g = pdf_map.get(qid, {"correct": False, "rationale": "missing"})
            per_question.append({
                "id": qid,
                "ara_correct": ara_g.get("correct", False),
                "ara_rationale": ara_g.get("rationale", ""),
                "pdf_correct": pdf_g.get("correct", False),
                "pdf_rationale": pdf_g.get("rationale", ""),
            })

        result = {
            "paper_id": pid,
            "per_question": per_question,
            "method": "claude_code_subagent",
        }

        (RESULTS_DIR / "judging" / f"{pid}_judged.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False))

        ara_correct = sum(1 for pq in per_question if pq["ara_correct"])
        pdf_correct = sum(1 for pq in per_question if pq["pdf_correct"])
        return pid, True, (ara_correct, pdf_correct, len(per_question))

    success = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_judge_paper, t): t for t in tasks}
        for future in as_completed(futures):
            pid, ok, counts = future.result()
            if ok:
                success += 1
                ara_c, pdf_c, total = counts
                print(f"[judge] OK: {pid} — ARA {ara_c}/{total}, PDF {pdf_c}/{total}")
            else:
                print(f"[judge] FAIL: {pid}")

    print(f"[judge] Done: {success}/{len(tasks)} papers scored")


# ── Step 4: Analysis ─────────────────────────────────────────────────

def step4_analyze(paper_filter: set | None = None):
    """Compute absolute success rates and generate report."""
    from collections import defaultdict

    judged_files = sorted((RESULTS_DIR / "judging").glob("*_judged.json"))
    if paper_filter:
        judged_files = [f for f in judged_files
                        if f.stem.replace("_judged", "") in paper_filter]
    if not judged_files:
        print("[analyze] No judged files found")
        return

    registry = load_registry()

    all_questions = []
    for jf in judged_files:
        data = json.loads(jf.read_text())
        pid = data.get("paper_id", jf.stem.replace("_judged", ""))

        questions = load_questions(pid)
        paper_info = next((p for p in registry["papers"] if p["paper_id"] == pid), {})
        benchmark = paper_info.get("benchmark", "unknown")

        for qr in data.get("per_question", []):
            qid = qr.get("id", "")
            if "_A" in qid:
                cat = "A"
            elif "_B" in qid:
                cat = "B"
            elif "_C" in qid:
                cat = "C"
            else:
                cat = "A"

            q_meta = next((q for q in questions if q["id"] == qid), {})
            difficulty = q_meta.get("difficulty", "unknown")

            all_questions.append({
                "paper_id": pid,
                "question_id": qid,
                "category": cat,
                "difficulty": difficulty,
                "benchmark": benchmark,
                "ara_correct": bool(qr.get("ara_correct", False)),
                "pdf_correct": bool(qr.get("pdf_correct", False)),
            })

    if not all_questions:
        print("[analyze] No question results to analyze")
        return

    # Per-category absolute success rates
    category_stats = defaultdict(lambda: {"ara_correct": 0, "pdf_correct": 0, "n": 0})
    for q in all_questions:
        s = category_stats[q["category"]]
        s["n"] += 1
        if q["ara_correct"]:
            s["ara_correct"] += 1
        if q["pdf_correct"]:
            s["pdf_correct"] += 1

    category_summary = {}
    for cat in sorted(category_stats.keys()):
        s = category_stats[cat]
        category_summary[cat] = {
            "n": s["n"],
            "ara_correct": s["ara_correct"],
            "pdf_correct": s["pdf_correct"],
            "ara_success_rate": round(s["ara_correct"] / s["n"], 4) if s["n"] else 0,
            "pdf_success_rate": round(s["pdf_correct"] / s["n"], 4) if s["n"] else 0,
            "delta": round((s["ara_correct"] - s["pdf_correct"]) / s["n"], 4) if s["n"] else 0,
        }

    total_n = len(all_questions)
    total_ara = sum(q["ara_correct"] for q in all_questions)
    total_pdf = sum(q["pdf_correct"] for q in all_questions)
    overall = {
        "n": total_n,
        "ara_correct": total_ara,
        "pdf_correct": total_pdf,
        "ara_success_rate": round(total_ara / total_n, 4),
        "pdf_success_rate": round(total_pdf / total_n, 4),
        "delta": round((total_ara - total_pdf) / total_n, 4),
    }

    # Per-difficulty breakdown
    diff_stats = defaultdict(lambda: {"ara_correct": 0, "pdf_correct": 0, "n": 0})
    for q in all_questions:
        s = diff_stats[q["difficulty"]]
        s["n"] += 1
        if q["ara_correct"]:
            s["ara_correct"] += 1
        if q["pdf_correct"]:
            s["pdf_correct"] += 1

    difficulty_breakdown = {}
    for d in sorted(diff_stats.keys()):
        s = diff_stats[d]
        difficulty_breakdown[d] = {
            "n": s["n"],
            "ara_correct": s["ara_correct"],
            "pdf_correct": s["pdf_correct"],
            "ara_success_rate": round(s["ara_correct"] / s["n"], 4) if s["n"] else 0,
            "pdf_success_rate": round(s["pdf_correct"] / s["n"], 4) if s["n"] else 0,
        }

    # Per-paper breakdown
    paper_stats = defaultdict(lambda: {"ara_correct": 0, "pdf_correct": 0, "n": 0})
    for q in all_questions:
        s = paper_stats[q["paper_id"]]
        s["n"] += 1
        if q["ara_correct"]:
            s["ara_correct"] += 1
        if q["pdf_correct"]:
            s["pdf_correct"] += 1

    paper_breakdown = {}
    for pid in sorted(paper_stats.keys()):
        s = paper_stats[pid]
        paper_breakdown[pid] = {
            "n": s["n"],
            "ara_correct": s["ara_correct"],
            "pdf_correct": s["pdf_correct"],
            "ara_success_rate": round(s["ara_correct"] / s["n"], 4) if s["n"] else 0,
            "pdf_success_rate": round(s["pdf_correct"] / s["n"], 4) if s["n"] else 0,
        }

    # McNemar test
    stats_results = {}
    try:
        from scipy import stats as scipy_stats
        a = sum(1 for q in all_questions if q["ara_correct"] and q["pdf_correct"])
        b = sum(1 for q in all_questions if q["ara_correct"] and not q["pdf_correct"])
        c = sum(1 for q in all_questions if not q["ara_correct"] and q["pdf_correct"])
        d = sum(1 for q in all_questions if not q["ara_correct"] and not q["pdf_correct"])
        stats_results["contingency"] = {"both_correct": a, "ara_only": b, "pdf_only": c, "both_wrong": d}
        if b + c > 0:
            chi2 = (abs(b - c) - 1) ** 2 / (b + c)
            p_val = 1 - scipy_stats.chi2.cdf(chi2, df=1)
            stats_results["mcnemar_overall"] = {
                "chi2": round(chi2, 4), "p_value": round(p_val, 6),
                "ara_only": b, "pdf_only": c,
            }
    except ImportError:
        stats_results["error"] = "scipy not available"

    # Assemble report
    report = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "n_papers": len(judged_files),
            "n_questions_total": total_n,
            "method": "claude_code_subagent",
            "models": {"judge": JUDGE_MODEL},
            "scoring": "absolute_correctness",
        },
        "overall": overall,
        "by_category": category_summary,
        "by_difficulty": difficulty_breakdown,
        "by_paper": paper_breakdown,
        "statistical_tests": stats_results,
    }

    (RESULTS_DIR / "analysis" / "category_summary.json").write_text(
        json.dumps(category_summary, indent=2))
    (RESULTS_DIR / "analysis" / "difficulty_breakdown.json").write_text(
        json.dumps(difficulty_breakdown, indent=2))
    (RESULTS_DIR / "analysis" / "paper_breakdown.json").write_text(
        json.dumps(paper_breakdown, indent=2))
    (RESULTS_DIR / "analysis" / "statistical_tests.json").write_text(
        json.dumps(stats_results, indent=2))
    (RESULTS_DIR / "understanding_eval_report.json").write_text(
        json.dumps(report, indent=2))

    # Print summary
    print("\n" + "=" * 60)
    print("UNDERSTANDING EVALUATION RESULTS (Absolute Correctness)")
    print("=" * 60)
    print(f"Papers: {len(judged_files)}, Questions: {total_n}\n")
    print(f"Overall: ARA {total_ara}/{total_n} ({overall['ara_success_rate']:.1%}) | "
          f"PDF {total_pdf}/{total_n} ({overall['pdf_success_rate']:.1%}) | "
          f"delta {overall['delta']:+.1%}\n")

    for cat in sorted(category_summary.keys()):
        s = category_summary[cat]
        print(f"Category {cat} (n={s['n']}):")
        print(f"  ARA: {s['ara_correct']}/{s['n']} ({s['ara_success_rate']:.1%})")
        print(f"  PDF: {s['pdf_correct']}/{s['n']} ({s['pdf_success_rate']:.1%})")
        print(f"  delta: {s['delta']:+.1%}\n")

    if "mcnemar_overall" in stats_results:
        m = stats_results["mcnemar_overall"]
        print(f"McNemar (overall): chi2={m['chi2']:.2f}, p={m['p_value']:.6f}")
        print(f"  ARA-only correct: {m['ara_only']}, PDF-only correct: {m['pdf_only']}")

    print(f"\nReport saved to: {RESULTS_DIR / 'understanding_eval_report.json'}")


def step_validate():
    """Validate that all answer files have the expected number of answers."""
    registry = load_registry()
    issues = []

    for p in registry["papers"]:
        pid = p["paper_id"]
        questions = load_questions(pid)
        if not questions:
            continue
        n_expected = len(questions)

        for agent_type, suffix in [("ARA", "ara"), ("PDF", "baseline")]:
            path = RESULTS_DIR / "answers" / f"{pid}_{suffix}.json"
            if not path.exists():
                issues.append((pid, agent_type, 0, n_expected, "MISSING"))
                continue
            data = json.loads(path.read_text())
            n_parsed = len(data.get("answers", []))
            if n_parsed < n_expected:
                issues.append((pid, agent_type, n_parsed, n_expected, "INCOMPLETE"))

    if issues:
        print(f"\n{'=' * 60}")
        print(f"VALIDATION FAILURES ({len(issues)} issues)")
        print(f"{'=' * 60}")
        for pid, atype, got, expected, status in issues:
            print(f"  {status}: {pid} {atype} — {got}/{expected} answers")
        print()
    else:
        print("\n[validate] All answer files complete.\n")

    return issues


def step_reparse():
    """Re-parse all raw output files with the current (improved) parser."""
    raw_files = sorted((RESULTS_DIR / "answers").glob("*_raw.txt"))
    if not raw_files:
        print("[reparse] No raw output files found. Run 'answer --force' to generate them.")
        return

    reparsed = 0
    for rf in raw_files:
        name = rf.stem  # e.g., "bam_ara_raw" or "bam_baseline_raw"
        if name.endswith("_ara_raw"):
            agent_type = "ARA"
            pid = name[:-8]
            out_name = f"{pid}_ara.json"
        elif name.endswith("_baseline_raw"):
            agent_type = "PDF"
            pid = name[:-13]
            out_name = f"{pid}_baseline.json"
        else:
            continue

        raw = rf.read_text()
        result = _parse_agent_json(raw, agent_type)

        out_path = RESULTS_DIR / "answers" / out_name
        if out_path.exists():
            existing = json.loads(out_path.read_text())
            old_count = len(existing.get("answers", []))
            new_count = len(result.get("answers", []))
            if new_count > old_count:
                result["paper_id"] = existing.get("paper_id", pid)
                result["elapsed_s"] = existing.get("elapsed_s", 0)
                result["method"] = existing.get("method", "claude_code_subagent")
                result["reparsed"] = True
                out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
                reparsed += 1
                print(f"[reparse] IMPROVED {out_name}: {old_count} → {new_count} answers")
            else:
                print(f"[reparse] OK {out_name}: {old_count} → {new_count} (no improvement)")
        else:
            result["paper_id"] = pid
            result["method"] = "claude_code_subagent"
            result["reparsed"] = True
            out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            reparsed += 1
            print(f"[reparse] NEW {out_name}: {len(result.get('answers', []))} answers")

    print(f"\n[reparse] Done: {reparsed}/{len(raw_files)} files updated")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Understanding eval pipeline")
    parser.add_argument("command",
                        choices=["answer", "judge", "analyze", "all",
                                 "validate", "reparse"])
    parser.add_argument("--papers", nargs="+", default=None,
                        help="Only run on specified paper IDs")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if results exist")
    return parser.parse_args()


def main():
    args = parse_args()
    paper_filter = set(args.papers) if args.papers else None
    skip_existing = not args.force

    if args.command == "validate":
        step_validate()
        return
    if args.command == "reparse":
        step_reparse()
        return

    if args.command in ("answer", "all"):
        step2_answer(skip_existing=skip_existing, paper_filter=paper_filter)
    if args.command in ("judge", "all"):
        step3_judge(skip_existing=skip_existing, paper_filter=paper_filter)
    if args.command in ("analyze", "all"):
        step4_analyze(paper_filter=paper_filter)


if __name__ == "__main__":
    main()
