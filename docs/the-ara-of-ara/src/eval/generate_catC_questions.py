"""Category C — Failure & Exploration Knowledge question generator.

Generates 5 questions per RE-Bench/Speedrun task targeting failure knowledge
that only exists in ARA trace layers. Questions ask about dead ends, failed
configurations, and abandoned approaches.

The key design: questions are generated from the task description (fair — any
researcher would ask these), then validated against the ARA trace to ensure
answers exist. Gold answers are extracted from trace/exploration_tree.yaml.
"""

import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

QUESTION_GEN_PROMPT = """\
You are a researcher about to work on a programming/ML task. You want to learn \
from previous attempts before starting. Generate exactly 5 questions about what \
approaches have been tried and failed, what configurations don't work, and what \
pitfalls to avoid.

These are questions about NEGATIVE results — things that DIDN'T work. Frame \
them as practical researcher questions that would save time if answered.

## Question Categories (use at least 3 different ones):

1. **failed_configurations**: "What hyperparameter settings or configurations \
were tried but didn't improve the score?"
2. **abandoned_approaches**: "What algorithmic approaches were explored and \
abandoned, and why?"
3. **dead_end_analysis**: "What were the main failure modes encountered?"
4. **resource_waste**: "How much compute/time was spent on approaches that \
didn't work?"
5. **lessons_learned**: "What key lessons were learned from failed attempts \
that would help a new researcher?"

## Difficulty

All questions should be T3_implicit — they require knowledge from the \
exploration trace that is NOT in the task description.

Exception: 1 question can target information that might be partially \
inferrable from the task constraints.

## Output Format

Return a JSON array of exactly 5 objects:
- "id": sequential like "C01", "C02", ..., "C05"
- "category": one of [failed_configurations, abandoned_approaches, \
dead_end_analysis, resource_waste, lessons_learned]
- "difficulty": "T3_implicit"
- "question": the question text (practical researcher question)
- "grading_type": "semantic" or "checklist"

Return ONLY the JSON array. No markdown fences, no preamble."""


ANSWER_EXTRACTION_PROMPT = """\
You are extracting gold answers for failure-knowledge questions from an ARA \
exploration tree. The exploration tree records all research decisions, \
experiments, dead ends, and pivots that occurred during task completion.

For each question, find the relevant information in the exploration tree and \
construct a detailed gold answer. Reference specific node IDs (e.g., N05, N12) \
in your answers.

If a question cannot be answered from the exploration tree, mark it with \
"answerable": false.

## Output Format

Return a JSON array matching the input questions, each augmented with:
- "gold_answer": detailed answer citing specific tree nodes
- "trace_nodes": list of node IDs referenced (e.g., ["N05", "N12"])
- "answerable": true/false
- "expected_pdf_behavior": "abstention" (baseline cannot answer) or \
"partial" (baseline might guess)

Return ONLY the JSON array. No markdown fences, no preamble."""


def _read_task_description(baseline_dir: str) -> str:
    """Read the task README and key files."""
    base = Path(baseline_dir)
    parts = []

    # Read README
    readme = base / "README.md"
    if readme.is_file():
        parts.append(f"# Task README\n\n{readme.read_text()}")

    # Read manifest if exists
    manifest = base / "manifest.yaml"
    if manifest.is_file():
        parts.append(f"# Manifest\n\n{manifest.read_text()}")

    # Read main Python file if exists
    for py in sorted(base.glob("*.py")):
        if py.stat().st_size < 50000:  # Skip very large files
            parts.append(f"# {py.name}\n\n```python\n{py.read_text()}\n```")

    return "\n\n---\n\n".join(parts)


def _read_exploration_tree(artifact_dir: str) -> str:
    """Read the ARA exploration tree."""
    tree_path = Path(artifact_dir) / "trace" / "exploration_tree.yaml"
    if tree_path.is_file():
        return tree_path.read_text()
    return ""


def generate_catC_questions(
    paper_id: str,
    artifact_dir: str,
    baseline_dir: str,
    output_dir: str = "code/eval/questions",
    model: str = "claude-sonnet-4-6",
) -> dict:
    """Generate 5 Category C questions from task description + trace validation."""

    # Step 1: Read task description
    task_desc = _read_task_description(baseline_dir)
    if not task_desc:
        print(f"[catC] ERROR: No task description found at {baseline_dir}")
        return {"questions": None, "output_path": None}

    # Step 2: Read exploration tree for answer extraction
    tree_text = _read_exploration_tree(artifact_dir)
    if not tree_text:
        print(f"[catC] WARN: No exploration tree at {artifact_dir}/trace/exploration_tree.yaml")

    client = anthropic.Anthropic()

    # Step 3: Generate questions from task description
    print(f"[catC] Generating 5 failure-knowledge questions for {paper_id}...")

    gen_response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=QUESTION_GEN_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Task: {paper_id}\n\n{task_desc}\n\n"
                       f"Generate exactly 5 failure-knowledge questions."
        }],
    )

    raw = gen_response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        questions_list = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[catC] ERROR: Failed to parse question generation for {paper_id}: {e}")
        return {"questions": None, "output_path": None}

    # Step 4: Extract gold answers from exploration tree
    if tree_text:
        print(f"[catC] Extracting gold answers from exploration tree...")

        questions_block = json.dumps(questions_list, indent=2)
        extract_response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=ANSWER_EXTRACTION_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"## Questions\n\n{questions_block}\n\n"
                    f"## Exploration Tree\n\n```yaml\n{tree_text}\n```\n\n"
                    f"Extract gold answers for each question from the "
                    f"exploration tree above."
                )
            }],
        )

        raw_answers = extract_response.content[0].text.strip()
        if raw_answers.startswith("```"):
            raw_answers = raw_answers.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            answered = json.loads(raw_answers)
            # Merge answers into questions
            for q, a in zip(questions_list, answered):
                q["gold_answer"] = a.get("gold_answer", "")
                q["trace_nodes"] = a.get("trace_nodes", [])
                q["answerable"] = a.get("answerable", True)
                q["expected_pdf_behavior"] = a.get("expected_pdf_behavior", "abstention")
        except (json.JSONDecodeError, Exception) as e:
            print(f"[catC] WARN: Answer extraction failed: {e}")
            for q in questions_list:
                q["gold_answer"] = "ANSWER EXTRACTION FAILED"
                q["trace_nodes"] = []
                q["answerable"] = True
                q["expected_pdf_behavior"] = "abstention"
    else:
        for q in questions_list:
            q["gold_answer"] = "NO EXPLORATION TREE AVAILABLE"
            q["trace_nodes"] = []
            q["answerable"] = False
            q["expected_pdf_behavior"] = "abstention"

    # Filter out unanswerable questions and replace if possible
    answerable = [q for q in questions_list if q.get("answerable", True)]
    if len(answerable) < len(questions_list):
        print(f"[catC] {len(questions_list) - len(answerable)} questions "
              f"not answerable from trace")

    # Tag with paper_id
    for i, q in enumerate(questions_list):
        q["id"] = f"{paper_id}_C{i+1:02d}"

    result = {
        "paper_id": paper_id,
        "category": "C",
        "eval_layer": "understanding",
        "n_questions": len(questions_list),
        "n_answerable": len(answerable),
        "questions": questions_list,
    }

    out_path = Path(output_dir) / f"{paper_id}_catC.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[catC] Wrote {len(questions_list)} questions to {out_path}")

    return {"questions": result, "output_path": str(out_path)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python generate_catC_questions.py <paper_id> <artifact_dir> <baseline_dir> [output_dir]")
        sys.exit(1)
    paper_id = sys.argv[1]
    artifact_dir = sys.argv[2]
    baseline_dir = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else "code/eval/questions"
    generate_catC_questions(paper_id, artifact_dir, baseline_dir, output_dir)
