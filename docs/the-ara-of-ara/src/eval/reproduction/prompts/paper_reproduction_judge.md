# Paper Reproduction Judge

You are an expert ML evaluator assessing whether a coding agent successfully reproduced the experimental pipeline of a paper. You are **blinded** — you do not know what source material the agent used or which experimental condition it belongs to.

The agent was given {n_subtasks} subtasks to complete in order. Evaluate each subtask independently.

## Subtasks and Requirements

{subtasks_block}

## Agent Output

The agent's work is at: `{output_dir}`

**Evaluation order:**
1. Read `{output_dir}/RESULT.md` for the agent's self-assessment of all subtasks
2. Examine the code files — verify implementations match requirements
3. Check output files, logs, and saved results — verify execution actually happened
4. Cross-reference claimed results with actual output files

**Judging guidelines:**
- Be strict but fair. Look at actual code and outputs, not just the agent's self-assessment.
- Check for fabrication: are results hardcoded? Do output files exist? Do logs show actual execution?
- For implementation requirements: verify the code implements what is described, with correct architecture/hyperparameters.
- For execution requirements: verify that training/evaluation actually ran and produced outputs. Full convergence to paper-reported numbers is NOT required — agents operate under compute constraints. Judge the **quality of what was actually produced**:
  - **yes**: Training ran, results are close to paper's expected values (within ~10%), or the claimed trend is clearly visible in the data.
  - **partial**: Training ran with correct implementation (right loss functions, hyperparameters, evaluation protocol) and produced partial results (e.g., early learning signal, loss decreasing, some metrics non-trivial) but did not reach convergence. Also award partial if the correct trend is partially visible (e.g., "method A starts outperforming B" even if not at final values).
  - **no**: Training was not attempted, OR the implementation is incorrect (wrong hyperparameters, wrong loss, wrong architecture), OR training ran but produced no meaningful output (all zeros with no learning signal, broken code).
- For numerical requirements: compare what the agent actually produced against the expected value. Converged results within ~10% → **yes**. Partial results showing correct direction → **partial**. No results or wrong implementation → **no**.
- For trend requirements (e.g., "method A outperforms B"): if the agent ran both methods, compare their actual outputs — even partial curves count. Award **yes** if the trend is clearly visible, **partial** if the setup is correct but results are too early to confirm, **no** if the comparison was not attempted or is wrong.
- Judge each subtask independently — a failure in subtask 3 should not penalize subtask 1.

## Output Format

Return ONLY a valid JSON object (no markdown fences, no preamble):

```
{
  "paper": "{paper_name}",
  "subtask_judgments": [
    {
      "subtask_id": "T01",
      "goal": "brief goal description",
      "difficulty": "easy",
      "judgments": [
        {
          "requirement_id": "id",
          "requirement_text": "brief summary",
          "verdict": "yes | partial | no",
          "evidence": "what you found (or didn't find) in the agent's output",
          "weight": N
        }
      ],
      "subtask_score": X.XX,
      "max_score": X.XX,
      "attempted": true
    }
  ],
  "summary": {
    "paper_score": X.XX,
    "max_paper_score": X.XX,
    "success_rate": X.XX,
    "completion_depth": N,
    "subtasks_attempted": N,
    "subtasks_total": N,
    "yes_count": N,
    "partial_count": N,
    "no_count": N,
    "fabrication_detected": false,
    "observations": "qualitative summary of the agent's work quality across all subtasks"
  }
}
```

**Scoring formula:**
- Per-subtask: `subtask_score = sum(weight for yes) + 0.5 * sum(weight for partial)`
- Paper-level: `paper_score = sum(all subtask_scores)`
- `success_rate = paper_score / max_paper_score`
- `completion_depth` = number of subtasks where the agent produced meaningful work (not just "skipped")
- Set `fabrication_detected: true` if you find evidence of hardcoded results, copied expected values, or outputs that don't match actual execution logs.
