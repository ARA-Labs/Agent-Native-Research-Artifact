"""Optimized agent eval v2: cached core ARA + evidence tool vs cached PDF.

Key optimization over v1:
  - ARA: all core files (logic/ + src/ + PAPER.md) pre-loaded in cached system prompt
         evidence files available via read_evidence tool (on-demand)
  - PDF: full text pre-loaded in cached system prompt
  - Both use Anthropic prompt caching — input tokens paid once, reused across questions
  - One question at a time, per-question token tracking

Usage:
  cd code && python -m eval.run_agent_eval_v2 [--paper andes] [--model claude-sonnet-4-6]

Multi-model sweep:
  for m in claude-sonnet-4-6 gpt-4o gemini-2.5-pro; do
    python -m eval.run_agent_eval_v2 --model $m --paper andes
  done
"""

import argparse
import json
import re
import time
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "eval" / "results"

# Set from CLI in main()
ANSWERER_MODEL = "claude-sonnet-4-6"
JUDGE_MODEL = "claude-opus-4-6"
ARTIFACTS_DIR = ROOT / "artifacts" / "andes"
PDF_PATH = ROOT / "pdfs" / "andes.pdf"


def parse_args():
    parser = argparse.ArgumentParser(description="Agent eval v2: ARA vs PDF (cached)")
    parser.add_argument("--paper", default="andes", help="Paper ID (default: andes)")
    parser.add_argument("--model", default="claude-sonnet-4-6",
                        help="Answerer model ID (default: claude-sonnet-4-6)")
    parser.add_argument("--judge-model", default="claude-opus-4-6",
                        help="Judge model ID (default: claude-opus-4-6)")
    return parser.parse_args()


# ── build contexts ─────────────────────────────────────────────────────

def build_ara_core() -> str:
    """Concatenate all core ARA files (logic + src + PAPER.md)."""
    parts = []
    skip_prefixes = ("evidence/", "trace/", "_")
    skip_names = {"questions.json", "exploration_tree.html"}
    content_exts = {".md", ".yaml", ".yml", ".py"}

    for fpath in sorted(ARTIFACTS_DIR.rglob("*")):
        if not fpath.is_file():
            continue
        rel = str(fpath.relative_to(ARTIFACTS_DIR))
        if any(rel.startswith(p) for p in skip_prefixes):
            continue
        if fpath.name in skip_names:
            continue
        if fpath.suffix not in content_exts:
            continue
        text = fpath.read_text(errors="replace")
        parts.append(f"=== {rel} ===\n{text}")

    # Also include evidence/README.md as the evidence index
    readme = ARTIFACTS_DIR / "evidence" / "README.md"
    if readme.exists():
        parts.append(f"=== evidence/README.md ===\n{readme.read_text()}")

    return "\n\n".join(parts)


def build_pdf_text() -> str:
    import sys
    sys.path.insert(0, str(ROOT))
    from utils.pdf_extract import extract_text
    return extract_text(str(PDF_PATH))


def load_questions(paper_id: str) -> list[dict]:
    """Load questions — try ab_eval result first, fall back to questions dir."""
    # Try finding any ab_eval result for this paper
    for f in sorted(OUTPUT_DIR.glob(f"ab_eval_{paper_id}*.json")):
        data = json.loads(f.read_text())
        if "questions" in data:
            return data["questions"]
    # Fall back to eval/questions directory
    for suffix in (f"{paper_id}_catA.json", f"{paper_id}.json"):
        q_path = ROOT / "eval" / "questions" / suffix
        if q_path.exists():
            data = json.loads(q_path.read_text())
            return data.get("questions", [])
    # Fall back to artifact dir
    q_path = ARTIFACTS_DIR / "questions.json"
    data = json.loads(q_path.read_text())
    qs = [q for q in data["questions"] if q["type"] == "understanding"]
    return qs


# ── evidence tool ──────────────────────────────────────────────────────

EVIDENCE_TOOL = {
    "name": "read_evidence",
    "description": "Read an evidence file (figure data or table data) from the ARA artifact. Use this to look up specific numerical results, data points from figures, or table contents. Path is relative to the artifact's evidence/ directory (e.g., 'figures/figure15_avg_qoe_vs_burst_intensity.md', 'tables/table1_models_hardware.md'). Check the evidence/README.md index in the system prompt to find the right file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path relative to evidence/ directory"
            }
        },
        "required": ["path"]
    }
}


def execute_evidence_tool(path: str) -> str:
    full = ARTIFACTS_DIR / "evidence" / path
    if not full.exists():
        return f"ERROR: File not found: evidence/{path}"
    return full.read_text(errors="replace")


# ── ARA agent (cached core + evidence tool) ───────────────────────────

SHARED_INSTRUCTIONS = """You are a senior ML researcher answering a question about the paper "Andes: Defining and Enhancing Quality-of-Experience in LLM-Based Text Streaming Services".

The paper content is provided above. Answer the question thoroughly and precisely based ONLY on the provided content.

Guidelines:
- Include specific numbers, equations, and exact details where relevant
- When the question asks about mechanisms, explain HOW and WHY, not just WHAT
- For questions about configurations or parameters, be exhaustive — list everything relevant
- For questions about failure conditions or assumptions, look for implicit/indirect mentions too
- If the information is genuinely not available in the provided content, say so explicitly and explain what related information IS present
- Do NOT guess or hallucinate — only state what is supported by the content"""

ARA_EXTRA = """
The content above is a structured research artifact (ARA) with: problem statement, claims, concepts, algorithm, architecture, constraints, heuristics, code stubs, and configurations. If you need specific numerical results from figures or tables, use the read_evidence tool. The evidence/README.md index (included above) tells you which evidence files exist."""


def run_ara_question(client, system_blocks, question: str, qid: str) -> dict:
    """Answer one question using cached ARA core + evidence tool."""
    messages = [{"role": "user", "content": f"Question ({qid}):\n{question}"}]

    total_input = 0
    total_output = 0
    cache_creation = 0
    cache_read = 0
    turns = 0
    evidence_read = []
    t0 = time.time()

    while turns < 5:
        turns += 1
        response = client.messages.create(
            model=ANSWERER_MODEL,
            max_tokens=2048,
            temperature=0,
            system=system_blocks,
            tools=[EVIDENCE_TOOL],
            messages=messages,
        )

        u = response.usage
        total_input += u.input_tokens
        total_output += u.output_tokens
        cache_creation += getattr(u, "cache_creation_input_tokens", 0) or 0
        cache_read += getattr(u, "cache_read_input_tokens", 0) or 0

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "read_evidence":
                    path = block.input.get("path", "")
                    evidence_read.append(path)
                    result = execute_evidence_tool(path)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            answer = "".join(b.text for b in response.content if hasattr(b, "text"))
            break
    else:
        answer = "(hit turn limit)"

    return {
        "id": qid,
        "answer": answer,
        "token_usage": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "cache_creation": cache_creation,
            "cache_read": cache_read,
            "turns": turns,
            "evidence_read": evidence_read,
            "elapsed_s": round(time.time() - t0, 1),
        },
    }


# ── PDF agent (cached, single-shot) ───────────────────────────────────

PDF_EXTRA = """
The content above is the full text of the research paper."""


def run_pdf_question(client, system_blocks, question: str, qid: str) -> dict:
    t0 = time.time()
    response = client.messages.create(
        model=ANSWERER_MODEL,
        max_tokens=2048,
        temperature=0,
        system=system_blocks,
        messages=[{"role": "user", "content": f"Question ({qid}):\n{question}"}],
    )
    u = response.usage
    answer = "".join(b.text for b in response.content if hasattr(b, "text"))

    return {
        "id": qid,
        "answer": answer,
        "token_usage": {
            "input_tokens": u.input_tokens,
            "output_tokens": u.output_tokens,
            "total_tokens": u.input_tokens + u.output_tokens,
            "cache_creation": getattr(u, "cache_creation_input_tokens", 0) or 0,
            "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
            "turns": 1,
            "evidence_read": [],
            "elapsed_s": round(time.time() - t0, 1),
        },
    }


# ── judge ──────────────────────────────────────────────────────────────

JUDGE_SYSTEM = """You are an expert ML research evaluator judging answer quality for research questions.

For each question you receive two answers (A and B) from unknown systems.

Judge each on:
- **Correctness** (1-5)
- **Completeness** (1-5)
- **Specificity** (1-5)
- **Hallucination penalty** (0 to -3)

Output a JSON array:
[{"question_id": "...", "scores_A": {...}, "scores_B": {...}, "winner": "A"|"B"|"tie", "rationale": "..."}]

Output ONLY the JSON array."""


def run_judge(questions, ara_results, pdf_results):
    client = anthropic.Anthropic()
    ara_map = {r["id"]: r["answer"] for r in ara_results}
    pdf_map = {r["id"]: r["answer"] for r in pdf_results}

    assignments = {}
    blocks = []
    for q in questions:
        qid = q["id"]
        a_ara, a_pdf = ara_map.get(qid, ""), pdf_map.get(qid, "")
        if random.random() < 0.5:
            a, b = a_ara, a_pdf
            assignments[qid] = {"A": "ARA", "B": "PDF"}
        else:
            a, b = a_pdf, a_ara
            assignments[qid] = {"A": "PDF", "B": "ARA"}
        blocks.append(f"## Question {qid}\n{q['question']}\n\n### Answer A\n{a}\n\n### Answer B\n{b}")

    t0 = time.time()
    response = client.messages.create(
        model=JUDGE_MODEL, max_tokens=8192, temperature=0,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": "\n\n---\n\n".join(blocks)}],
    )
    elapsed = time.time() - t0
    u = response.usage
    raw = "".join(b.text for b in response.content if b.type == "text").strip()
    try:
        judgments = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
        judgments = json.loads(m.group(1).strip()) if m else json.loads(raw[raw.index("["):raw.rindex("]")+1])

    return {
        "judgments": judgments, "assignments": assignments,
        "token_usage": {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                        "total_tokens": u.input_tokens + u.output_tokens, "elapsed_s": round(elapsed, 1)},
    }


# ── main ───────────────────────────────────────────────────────────────

def main():
    global ANSWERER_MODEL, JUDGE_MODEL, ARTIFACTS_DIR, PDF_PATH

    args = parse_args()
    ANSWERER_MODEL = args.model
    JUDGE_MODEL = args.judge_model
    ARTIFACTS_DIR = ROOT / "artifacts" / args.paper
    PDF_PATH = ROOT / "pdfs" / f"{args.paper}.pdf"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    questions = load_questions(args.paper)

    print(f"Paper: {args.paper}")
    print(f"Answerer model: {ANSWERER_MODEL}")
    print(f"Judge model:    {JUDGE_MODEL}")

    # Build contexts
    ara_core = build_ara_core()
    pdf_text = build_pdf_text()
    print(f"ARA core: {len(ara_core):,} chars | PDF text: {len(pdf_text):,} chars")

    # Build cached system prompt blocks (shared instructions, format-specific extra)
    ara_system = [
        {"type": "text", "text": f"# ARA Artifact Content\n\n{ara_core}", "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": SHARED_INSTRUCTIONS + ARA_EXTRA},
    ]
    pdf_system = [
        {"type": "text", "text": f"# Paper Content\n\n{pdf_text}", "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": SHARED_INSTRUCTIONS + PDF_EXTRA},
    ]

    client = anthropic.Anthropic()

    # ── Phase 1: Answer questions sequentially (to measure caching)
    print(f"\n{'='*80}")
    print("PHASE 1: Per-question answering (with prompt caching)")
    print(f"{'='*80}")

    ara_results = []
    pdf_results = []

    for i, q in enumerate(questions):
        qid = q["id"]
        tier = q.get("tier", "?")
        cat = q.get("category", "?")

        # Run ARA and PDF in parallel for this question
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_ara = pool.submit(run_ara_question, client, ara_system, q["question"], qid)
            f_pdf = pool.submit(run_pdf_question, client, pdf_system, q["question"], qid)
            r_ara = f_ara.result()
            r_pdf = f_pdf.result()

        ara_results.append(r_ara)
        pdf_results.append(r_pdf)

        au = r_ara["token_usage"]
        pu = r_pdf["token_usage"]
        ara_cache = f"create={au['cache_creation']}, read={au['cache_read']}" if au['cache_creation'] or au['cache_read'] else "no cache"
        pdf_cache = f"create={pu['cache_creation']}, read={pu['cache_read']}" if pu['cache_creation'] or pu['cache_read'] else "no cache"

        print(f"\n{qid} ({cat}, T{tier})")
        print(f"  ARA: {au['total_tokens']:>6} tok | {au['turns']} turns | {len(au['evidence_read'])} evidence | {au['elapsed_s']}s | {ara_cache}")
        if au['evidence_read']:
            print(f"       evidence: {au['evidence_read']}")
        print(f"  PDF: {pu['total_tokens']:>6} tok | {pu['turns']} turn  | {pu['elapsed_s']}s | {pdf_cache}")

    # ── Phase 2: Judge
    print(f"\n{'='*80}")
    print("PHASE 2: Opus 4.6 judge (blinded)")
    print(f"{'='*80}")
    judge = run_judge(questions, ara_results, pdf_results)
    print(f"Judge: {judge['token_usage']['total_tokens']:,} tok, {judge['token_usage']['elapsed_s']}s")

    # ── Phase 3: Results
    qids = list(judge["assignments"].keys())
    judgments = judge["judgments"]

    def score(s):
        return s.get("correctness", 0) + s.get("completeness", 0) + s.get("specificity", 0) + s.get("hallucination_penalty", 0)

    q_map = {q["id"]: q for q in questions}
    ara_tok_map = {r["id"]: r["token_usage"] for r in ara_results}
    pdf_tok_map = {r["id"]: r["token_usage"] for r in pdf_results}

    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"\n{'Q':<15} {'Win':<5} {'ARA':>4} {'PDF':>4} {'T':<5} {'ARA tok':>8} {'PDF tok':>8} {'ARA $':>8} {'PDF $':>8} {'Ev':>3}")
    print("─" * 80)

    ara_wins = pdf_wins = ties = 0
    ara_total_s = pdf_total_s = 0
    ara_total_tok = pdf_total_tok = 0
    ara_total_cache_read = pdf_total_cache_read = 0
    detailed = []

    for idx, j in enumerate(judgments):
        qid = qids[idx]
        assign = judge["assignments"][qid]
        sa = j.get("scores_A", {}); sb = j.get("scores_B", {})
        ara_sc = sa if assign["A"] == "ARA" else sb
        pdf_sc = sa if assign["A"] == "PDF" else sb
        ara_s, pdf_s = score(ara_sc), score(pdf_sc)

        w = j.get("winner", "tie")
        actual = assign[w] if w in ("A", "B") else "tie"
        if actual == "ARA": ara_wins += 1
        elif actual == "PDF": pdf_wins += 1
        else: ties += 1

        ara_total_s += ara_s; pdf_total_s += pdf_s
        at = ara_tok_map[qid]; pt = pdf_tok_map[qid]
        ara_total_tok += at["total_tokens"]; pdf_total_tok += pt["total_tokens"]
        ara_total_cache_read += at["cache_read"]; pdf_total_cache_read += pt["cache_read"]

        # Effective cost = input - cache_read (cache reads are 10x cheaper)
        ara_eff = at["input_tokens"] - at["cache_read"] * 0.9
        pdf_eff = pt["input_tokens"] - pt["cache_read"] * 0.9

        tier = q_map[qid]["tier"]
        n_ev = len(at["evidence_read"])
        print(f"{qid:<15} {actual:<5} {ara_s:>4} {pdf_s:>4} T{tier:<4} {at['total_tokens']:>8} {pt['total_tokens']:>8} {ara_eff:>8.0f} {pdf_eff:>8.0f} {n_ev:>3}")

        detailed.append({
            "question_id": qid, "category": q_map[qid]["category"], "tier": tier,
            "winner": actual, "ara_score": ara_s, "pdf_score": pdf_s,
            "ara_tokens": at, "pdf_tokens": pt,
            "ara_detail": ara_sc, "pdf_detail": pdf_sc,
            "rationale": j.get("rationale", ""),
        })

    print(f"\n{'─'*80}")
    print(f"ARA wins: {ara_wins}  |  PDF wins: {pdf_wins}  |  Ties: {ties}")
    print(f"ARA avg score: {ara_total_s/10:.1f}  |  PDF avg score: {pdf_total_s/10:.1f}")
    print(f"ARA total tokens: {ara_total_tok:,}  |  PDF total tokens: {pdf_total_tok:,}")
    print(f"ARA cache reads: {ara_total_cache_read:,}  |  PDF cache reads: {pdf_total_cache_read:,}")

    # Save — include model in filename for multi-model sweeps
    model_slug = ANSWERER_MODEL.replace("/", "_").replace(":", "_")
    output = {
        "config": {"paper": args.paper, "answerer": ANSWERER_MODEL, "judge": JUDGE_MODEL, "version": "v2_cached"},
        "context_sizes": {"ara_core_chars": len(ara_core), "pdf_chars": len(pdf_text)},
        "ara_results": [{"id": r["id"], "answer": r["answer"], "token_usage": r["token_usage"]} for r in ara_results],
        "pdf_results": [{"id": r["id"], "answer": r["answer"], "token_usage": r["token_usage"]} for r in pdf_results],
        "judge": judge,
        "detailed_results": detailed,
        "summary": {
            "ara_wins": ara_wins, "pdf_wins": pdf_wins, "ties": ties,
            "ara_avg_score": round(ara_total_s / 10, 2),
            "pdf_avg_score": round(pdf_total_s / 10, 2),
            "ara_total_tokens": ara_total_tok,
            "pdf_total_tokens": pdf_total_tok,
            "ara_total_cache_read": ara_total_cache_read,
            "pdf_total_cache_read": pdf_total_cache_read,
        },
    }
    out_path = OUTPUT_DIR / f"agent_eval_v2_{args.paper}_{model_slug}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
