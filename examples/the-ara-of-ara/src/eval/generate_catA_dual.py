"""Category A question generation from dual sources (PDF + ARA).

Generates questions independently from both the PDF and ARA, then merges
and deduplicates to produce a balanced question set that doesn't favor
either format.

Protocol:
1. Generate 10 questions from PDF (gold answers from PDF)
2. Generate 10 questions from ARA (gold answers from ARA)
3. LLM-based deduplication: identify overlapping questions, keep the most
   precise version, produce ~10 unique questions
"""

import json
import base64
import sys
from pathlib import Path

from dotenv import load_dotenv

_code_dir = Path(__file__).resolve().parent.parent
load_dotenv(_code_dir / ".env")

import anthropic

QUESTION_GEN_SYSTEM = """\
You are a senior ML researcher generating understanding questions about a \
research paper. Generate exactly 10 questions that test whether an agent \
can extract technical knowledge from this material.

## Question categories (at least 1 from each):
1. **surface_results** — exact numerical outcomes
2. **method_detail** — algorithmic/architectural specifics
3. **hyperparameters** — training/inference configurations
4. **cross_section** — connecting info from different parts
5. **design_rationale** — implicit justifications
6. **failure_conditions** — where the method breaks

## Difficulty tiers (exact distribution):
- T1_explicit (2): answer stated verbatim in one location
- T2_scattered (4): requires assembling from 2+ locations
- T3_implicit (3): must be inferred
- unanswerable (1): plausible but not answerable from the material

## Output
Return ONLY a JSON array of 10 objects with:
- "id", "category", "difficulty", "question", "gold_answer", "grading_type"

grading_type: exact_numeric | semantic | checklist | abstention"""


MERGE_SYSTEM = """\
You are deduplicating two sets of questions about the same research paper. \
Questions were generated independently from two different representations \
of the same work.

For each pair of similar questions (asking about the same concept/fact), \
keep ONE version — prefer the question with the more precise, verifiable \
gold_answer. For unique questions (only in one set), keep them.

Output a MERGED JSON array of exactly 10 questions. Aim for diversity \
across categories and difficulties. Each question must have:
- "id": "{paper_id}_A{NN}" (renumbered 01-10)
- "category", "difficulty", "question", "gold_answer", "grading_type"
- "source": "pdf" | "ara" | "both" (which set it came from)

Return ONLY the JSON array."""


def generate_catA_dual(
    paper_id: str,
    pdf_path: str | None,
    artifact_dir: str,
    output_dir: str,
    baseline_dir: str | None = None,
    model: str = "claude-sonnet-4-6",
) -> dict:
    """Generate Cat A questions from both PDF/baseline and ARA, then merge.

    For PaperBench: pdf_path is the PDF file.
    For RE-Bench/Speedrun: baseline_dir is the task description directory.
    """
    client = anthropic.Anthropic()
    art = Path(artifact_dir)

    # ── Step 1: Generate from baseline (PDF or task description) ──
    if pdf_path and Path(pdf_path).exists():
        pdf_b64 = base64.standard_b64encode(Path(pdf_path).read_bytes()).decode("utf-8")
        baseline_content = [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
            {"type": "text", "text": f"Paper: {paper_id}\nGenerate exactly 10 understanding questions."},
        ]
    elif baseline_dir and Path(baseline_dir).exists():
        parts = []
        base = Path(baseline_dir)
        for f in ["README.md", "manifest.yaml"]:
            p = base / f
            if p.exists():
                parts.append(f"# {f}\n{p.read_text()}")
        for py in sorted(base.glob("*.py"))[:3]:
            if py.stat().st_size < 30000:
                parts.append(f"# {py.name}\n```python\n{py.read_text()}\n```")
        baseline_content = [
            {"type": "text", "text": f"Task: {paper_id}\n\n" + "\n\n---\n\n".join(parts) + "\n\nGenerate exactly 10 understanding questions."},
        ]
    else:
        return {"questions": None, "error": "No baseline source found"}

    print(f"[catA-dual] Generating PDF/baseline questions for {paper_id}...")
    with client.messages.stream(
        model=model, max_tokens=8192, temperature=0,
        system=QUESTION_GEN_SYSTEM,
        messages=[{"role": "user", "content": baseline_content}],
    ) as stream:
        resp1 = stream.get_final_message()
    raw1 = resp1.content[0].text.strip()
    if raw1.startswith("```"):
        raw1 = raw1.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        pdf_questions = json.loads(raw1)
    except json.JSONDecodeError:
        pdf_questions = []

    # ── Step 2: Generate from ARA ──
    ara_parts = []
    for subpath in [
        "PAPER.md",
        "logic/problem.md", "logic/claims.md", "logic/concepts.md",
        "logic/experiments.md", "logic/solution/architecture.md",
        "logic/solution/algorithm.md", "logic/solution/heuristics.md",
        "src/configs/training.md", "src/configs/model.md",
        "src/environment.md", "evidence/README.md",
    ]:
        p = art / subpath
        if p.exists() and p.stat().st_size < 30000:
            ara_parts.append(f"## {subpath}\n\n{p.read_text()}")
    # Evidence tables
    tables_dir = art / "evidence" / "tables"
    if tables_dir.is_dir():
        for tf in sorted(tables_dir.iterdir()):
            if tf.is_file() and tf.stat().st_size < 20000:
                ara_parts.append(f"## evidence/tables/{tf.name}\n\n{tf.read_text()}")
    # Configs
    configs_dir = art / "src" / "configs"
    if configs_dir.is_dir():
        for cf in sorted(configs_dir.iterdir()):
            if cf.is_file() and cf.name not in ("training.md", "model.md") and cf.stat().st_size < 20000:
                ara_parts.append(f"## src/configs/{cf.name}\n\n{cf.read_text()}")

    ara_text = "\n\n---\n\n".join(ara_parts)

    print(f"[catA-dual] Generating ARA questions for {paper_id}...")
    with client.messages.stream(
        model=model, max_tokens=8192, temperature=0,
        system=QUESTION_GEN_SYSTEM,
        messages=[{"role": "user", "content": f"Research artifact for: {paper_id}\n\n{ara_text}\n\nGenerate exactly 10 understanding questions based on this structured artifact."}],
    ) as stream:
        resp2 = stream.get_final_message()
    raw2 = resp2.content[0].text.strip()
    if raw2.startswith("```"):
        raw2 = raw2.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        ara_questions = json.loads(raw2)
    except json.JSONDecodeError:
        ara_questions = []

    # ── Step 3: Merge and deduplicate ──
    print(f"[catA-dual] Merging: {len(pdf_questions)} PDF + {len(ara_questions)} ARA questions...")

    merge_input = (
        f"Paper: {paper_id}\n\n"
        f"## Set 1 (from PDF/baseline):\n{json.dumps(pdf_questions, indent=2)}\n\n"
        f"## Set 2 (from ARA):\n{json.dumps(ara_questions, indent=2)}\n\n"
        f"Merge into exactly 10 unique questions. Use paper_id prefix: {paper_id}"
    )

    with client.messages.stream(
        model=model, max_tokens=8192, temperature=0,
        system=MERGE_SYSTEM,
        messages=[{"role": "user", "content": merge_input}],
    ) as stream:
        resp3 = stream.get_final_message()
    raw3 = resp3.content[0].text.strip()
    if raw3.startswith("```"):
        raw3 = raw3.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        merged = json.loads(raw3)
    except json.JSONDecodeError:
        # Fallback: interleave top 5 from each
        merged = pdf_questions[:5] + ara_questions[:5]
        for i, q in enumerate(merged):
            q["id"] = f"{paper_id}_A{i+1:02d}"
            q["source"] = "pdf" if i < 5 else "ara"

    # Tag IDs
    for i, q in enumerate(merged):
        q["id"] = f"{paper_id}_A{i+1:02d}"

    result = {
        "paper_id": paper_id,
        "category": "A",
        "eval_layer": "understanding",
        "generation_method": "dual_source_merged",
        "n_questions": len(merged),
        "n_from_pdf": sum(1 for q in merged if q.get("source") in ("pdf", "both")),
        "n_from_ara": sum(1 for q in merged if q.get("source") in ("ara", "both")),
        "questions": merged,
    }

    out_path = Path(output_dir) / f"{paper_id}_catA.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[catA-dual] Wrote {len(merged)} merged questions to {out_path}")

    return result
