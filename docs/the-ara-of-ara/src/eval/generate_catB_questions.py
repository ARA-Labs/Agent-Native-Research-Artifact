"""Category B — Configuration & Detail Recovery question generator.

Generates 5 questions per PaperBench paper targeting information gaps.
Questions are derived from PaperBench rubric requirements rated 'partial'
or 'absent' in the info gap analysis, converted into targeted questions.

These questions are DESIGNED to test ARA's advantage over PDFs for
under-specified details (hyperparameters, configs, environment specs).
"""

import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SYSTEM_PROMPT = """\
You are a senior ML researcher preparing to reproduce a paper. You have access \
to the paper's PaperBench rubric — a detailed, expert-authored specification of \
every requirement needed for full reproduction.

Your task: Given a set of rubric requirements that the original paper FAILS to \
fully specify (rated "partial" or "absent" in our analysis), generate exactly 5 \
targeted questions that test whether a research artifact can recover this missing \
information.

## Question Design Principles

1. Each question targets a SPECIFIC gap identified in the info gap analysis.
2. Questions should be natural — something a researcher would genuinely ask.
3. The gold_answer comes from the rubric requirement, NOT from the paper.
4. These are HARDER than standard comprehension — by design, the PDF does NOT \
   fully answer them.

## Difficulty Distribution (per 5 questions)

- T2_scattered (2): Answer requires assembling from 2+ locations
- T3_implicit (3): Answer must be inferred or is not explicitly stated

No T1_explicit (by design these are NOT explicitly stated in the PDF).
No unanswerable controls (all 5 should have rubric-grounded answers).

## Grading Types

- exact_numeric: The gold answer is a specific number or config value
- checklist: The gold answer is a list of items; score by coverage
- semantic: The gold answer is a concept or explanation

## Output Format

Return a JSON array of exactly 5 objects:
- "id": sequential like "B01", "B02", ..., "B05"
- "category": one of [missing_hyperparameter, vague_description, \
missing_code_detail, missing_baseline_detail, missing_environment]
- "difficulty": one of [T2_scattered, T3_implicit]
- "question": targeted question about the specific gap
- "gold_answer": the complete answer derived from the rubric requirement \
(include the exact specification from the rubric)
- "grading_type": one of [exact_numeric, checklist, semantic]
- "rubric_requirement": the original rubric requirement text
- "info_gap_rating": "partial" or "absent"
- "gap_type": the gap category from the info gap analysis

Return ONLY the JSON array. No markdown fences, no preamble."""


def _select_requirements(info_gap_path: str, n: int = 10) -> list[dict]:
    """Select the most informative partial/absent requirements."""
    with open(info_gap_path) as f:
        data = json.load(f)

    candidates = []
    for item in data.get("detailed_results", []):
        if item["rating"] in ("partial", "absent"):
            candidates.append(item)

    # Sort by: absent first, then by weight (descending), then diversity
    candidates.sort(
        key=lambda x: (0 if x["rating"] == "absent" else 1, -x.get("weight", 1))
    )

    # Ensure diversity of gap types
    selected = []
    seen_types = set()
    # First pass: one per gap type
    for c in candidates:
        gap_types = c.get("gap_categories", [])
        primary_type = gap_types[0] if gap_types else "unknown"
        if primary_type not in seen_types and len(selected) < n:
            selected.append(c)
            seen_types.add(primary_type)
    # Second pass: fill remaining
    for c in candidates:
        if c not in selected and len(selected) < n:
            selected.append(c)

    return selected[:n]


def generate_catB_questions(
    paper_id: str,
    rubric_path: str,
    info_gap_path: str,
    output_dir: str = "code/eval/questions",
    model: str = "claude-sonnet-4-6",
) -> dict:
    """Generate 5 Category B questions from rubric gaps."""

    if not os.path.isfile(info_gap_path):
        print(f"[catB] ERROR: Info gap not found: {info_gap_path}")
        return {"questions": None, "output_path": None}

    # Select candidate requirements
    candidates = _select_requirements(info_gap_path, n=10)
    if len(candidates) < 5:
        print(f"[catB] WARN: Only {len(candidates)} partial/absent requirements "
              f"for {paper_id}")
        if len(candidates) == 0:
            return {"questions": None, "output_path": None}

    # Format candidates for the prompt
    req_block = []
    for i, c in enumerate(candidates):
        gap_types = c.get("gap_categories", [])
        req_block.append(
            f"### Requirement {i+1}\n"
            f"- **Rubric text**: {c.get('requirements', 'N/A')}\n"
            f"- **Rating**: {c['rating']}\n"
            f"- **Gap types**: {', '.join(gap_types)}\n"
            f"- **What PDF provides**: {c.get('evidence', 'N/A')}\n"
            f"- **What's missing**: {c.get('missing', 'N/A')}\n"
            f"- **Category**: {c.get('finegrained_task_category', 'N/A')}\n"
            f"- **Weight**: {c.get('weight', 1)}\n"
        )

    user_prompt = (
        f"Paper: {paper_id}\n\n"
        f"Below are {len(candidates)} rubric requirements that the paper's PDF "
        f"fails to fully specify. Select the 5 most important/diverse ones and "
        f"convert each into a targeted question.\n\n"
        + "\n".join(req_block)
        + "\n\nGenerate exactly 5 Category B questions targeting these gaps."
    )

    client = anthropic.Anthropic()

    print(f"[catB] Generating 5 detail-recovery questions for {paper_id}...")

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        questions_list = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[catB] ERROR: Failed to parse LLM response for {paper_id}: {e}")
        print(f"[catB] Raw output:\n{raw[:500]}")
        return {"questions": None, "output_path": None}

    # Tag with paper_id
    for i, q in enumerate(questions_list):
        q["id"] = f"{paper_id}_B{i+1:02d}"

    result = {
        "paper_id": paper_id,
        "category": "B",
        "eval_layer": "understanding",
        "n_questions": len(questions_list),
        "questions": questions_list,
    }

    out_path = Path(output_dir) / f"{paper_id}_catB.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[catB] Wrote {len(questions_list)} questions to {out_path}")

    return {"questions": result, "output_path": str(out_path)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python generate_catB_questions.py <paper_id> <rubric_path> <info_gap_path> [output_dir]")
        sys.exit(1)
    paper_id = sys.argv[1]
    rubric_path = sys.argv[2]
    info_gap_path = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else "code/eval/questions"
    generate_catB_questions(paper_id, rubric_path, info_gap_path, output_dir)
