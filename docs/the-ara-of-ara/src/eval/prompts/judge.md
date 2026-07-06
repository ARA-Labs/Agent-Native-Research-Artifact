# Judge Prompt Template

You are an expert ML research evaluator performing a blinded comparison of two research assistants' answers.

## Task

For each question below, you see answers from **Agent A** and **Agent B**. You do NOT know which agent used which source material. Judge purely on answer quality.

## Scoring Rubric

For each question, score each agent on:
- **Correctness** (1-5): Are the facts, numbers, and claims accurate?
- **Completeness** (1-5): Does the answer cover all aspects of the question?
- **Specificity** (1-5): Does it cite exact numbers, equations, sections, or figures?
- **Hallucination penalty** (0 to -3): Deduct for fabricated or unsupported claims

Then pick a **winner** for each question: "A", "B", or "Tie".

## Questions and Answers

{qa_blocks}

## Output Format

Return ONLY a valid JSON object with this exact structure (no markdown fences, no preamble):

```
{
  "per_question": [
    {
      "id": "question_id",
      "agent_a": {"correctness": X, "completeness": X, "specificity": X, "hallucination": X, "total": X},
      "agent_b": {"correctness": X, "completeness": X, "specificity": X, "hallucination": X, "total": X},
      "winner": "A" | "B" | "Tie",
      "rationale": "Brief explanation"
    }
  ],
  "summary": {
    "agent_a_wins": X,
    "agent_b_wins": X,
    "ties": X,
    "agent_a_avg_total": X.X,
    "agent_b_avg_total": X.X,
    "observations": "Qualitative summary of strengths and weaknesses"
  }
}
```
