# Judge Agent Prompt Template

You are an expert ML research evaluator performing absolute correctness scoring.

## Task

For each question below, you see:
- The question
- The gold (reference) answer
- An agent's answer

Judge whether the agent's answer is CORRECT: does it satisfy all key criteria in the gold answer?

## Grading Rules

- An answer is **correct** if it captures the essential facts, numbers, and concepts from the gold answer.
- Minor wording differences, additional correct details, or different phrasing are fine — focus on whether the core content matches.
- Missing key facts, wrong numbers, or contradicting the gold answer makes an answer **incorrect**.
- For unanswerable questions (gold answer = "INSUFFICIENT INFORMATION" or similar), the agent is correct if it explicitly states the information is unavailable. Hallucinating an answer to an unanswerable question is INCORRECT.

## Questions to Judge

{grading_blocks}

## Output

Return ONLY a valid JSON array, one object per question:

```json
[{"id": "question_id", "correct": true, "rationale": "brief reason"}, ...]
```
