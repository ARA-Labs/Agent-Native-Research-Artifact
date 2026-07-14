# Full Paper Reproduction: {paper_name}

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce the full experimental pipeline** of a machine learning paper by completing the subtasks below IN ORDER. Each subtask builds on your previous work — you should naturally reuse code, environments, models, and data from earlier subtasks.

## Objective

Complete all {n_subtasks} subtasks below, progressing from setup and implementation through training, evaluation, and analysis. Your work is cumulative: later subtasks assume earlier ones are complete.

## What You Must Produce

1. **Working code** for all subtasks in `{output_dir}/`
2. **Actual computed results** from running your code
3. **A cumulative report** at `{output_dir}/RESULT.md` — append results after each subtask

## Source Material

{source_material_block}

## Working Directory

Write ALL code, data, logs, and outputs to: `{output_dir}/`

Create this directory if it does not exist.

## Subtasks

Work through these in order. Each subtask's success criteria will be independently judged.

{subtasks_block}

## Workflow

1. **Work through subtasks in order** — each builds on previous work
2. **After each subtask**, append your results to `{output_dir}/RESULT.md` under a heading like `## Subtask N: {goal}`
3. **Reuse prior work** — if Subtask 1 sets up the environment, Subtask 3 should use that same environment
4. **If a subtask fails**, document the failure in RESULT.md and move on to the next subtask
5. **Keep running code** — do not tear down environments, models, or data between subtasks

## Report Format

Your `RESULT.md` should have this structure:

```
# Paper Reproduction: {paper_name}

## Subtask 1 of {n_subtasks}: {goal}
### Setup
What you installed, configured, prepared
### Implementation
Key code and design decisions
### Results
Actual numerical outputs
### Self-Assessment
For each requirement: met / partially met / not met, with justification
### Issues
Problems encountered, if any

## Subtask 2 of {n_subtasks}: {goal}
...
(repeat for each subtask attempted)
```

## Critical Rules

- **Do NOT fabricate results.** If code fails to run, report the failure. If a metric cannot be computed, say so. Inventing numbers is worse than reporting a failure.
- **Do NOT hardcode expected values.** Your results must come from actually running the experiment, not from copying numbers you found in the source material.
- **Hardware constraint**: Assume you have access to a single GPU (A100 80GB). If a subtask requires more, implement a reduced-scale version and document the difference.
- **Time constraint**: Target <= 8 GPU-hours per subtask. If full training is infeasible, run a shortened version and document the reduction.
- **Training strategy**: Full convergence is NOT required. Run **proof-of-concept** training: 1 seed, ~10k-50k steps per method, just enough to verify the training loop runs end-to-end and produces non-trivial output. The goal is to demonstrate correct implementation (loss decreases, metrics are tracked, checkpoints save) — NOT to reproduce the paper's final numbers. Spend at most 10-15 minutes per training run. Do NOT iterate on training to achieve convergence — move on to the next subtask instead. **Breadth over depth**: covering all subtasks with working code matters more than converging on one.
- **Cumulative work**: Reuse code, models, and data from earlier subtasks. Do not redo setup work unnecessarily.
