# Reproduction Task: {task_id}

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce an experimental result** from a machine learning paper using only the structured research artifact (ARA) provided below. You have NO access to the original paper PDF or its companion GitHub repository.

**Difficulty**: {difficulty}

## Objective

{task_goal}

## What You Must Produce

1. **Working code** that implements and/or executes the experiment described above
2. **Actual computed results** — you must run the code and report real outputs
3. **A summary report** at `{output_dir}/RESULT.md`

## Success Criteria

Your work will be evaluated by a blinded judge against these requirements. Each one will be scored **yes** (fully met), **partial** (partially addressed), or **no** (not met). Requirements with higher weight count more toward your score.

{rubric_requirements}

## Source Material — ARA Artifact

The paper's structured artifact is at: `{artifact_dir}`

**How to navigate it:**

| Path | What it contains |
|------|-----------------|
| `PAPER.md` | Overview and index — **read this first** |
| `logic/claims.md` | Paper's claims, hypotheses, falsification criteria |
| `logic/experiments.md` | Experimental setups, datasets, hyperparameters, evaluation protocols |
| `logic/concepts.md` | Key technical concepts and definitions |
| `logic/solution/` | Algorithm details, architecture specifications, mathematical formulations |
| `src/` | Implementation configs, environment setup, dependency lists, execution instructions |
| `evidence/` | Reported results, figure data, table data |

## Working Directory

Write ALL code, data, logs, and outputs to: `{output_dir}`

Create this directory if it does not exist.

## Experiment Process

Follow this workflow:

### Phase 1: Understand
- Read `PAPER.md` for an overview
- Read `logic/experiments.md` for the specific experimental setup relevant to your task
- Read `logic/solution/` for algorithm and architecture details
- Read `src/` for implementation specifics (hyperparameters, configs, dependencies)

### Phase 2: Plan
- Identify what code components are needed
- List dependencies to install
- Determine data requirements (downloads, preprocessing)
- Estimate whether the task is feasible on a single GPU

### Phase 3: Implement
- Write clean, runnable code in `{output_dir}/`
- Install any required packages via pip/conda
- Download any required datasets or pretrained models
- Configure hyperparameters exactly as specified in the artifact

### Phase 4: Execute
- Run your code end-to-end
- Capture all outputs, logs, and metrics
- If execution fails, debug and retry — document what went wrong

### Phase 5: Report
Write `{output_dir}/RESULT.md` with:
- **Setup**: What you installed, configured, and prepared
- **Implementation**: What code you wrote and key design decisions
- **Results**: The actual numerical outputs from your code (tables, metrics, plots)
- **Self-assessment**: For each success criterion, state whether you believe it is met and why
- **Issues**: Any problems encountered, debugging steps taken, or limitations

## Critical Rules

- **Do NOT fabricate results.** If code fails to run, report the failure. If a metric cannot be computed, say so. Inventing numbers is worse than reporting a failure.
- **Do NOT hardcode expected values.** Your results must come from actually running the experiment, not from copying numbers you found in the source material.
- **Hardware constraint**: Assume you have access to a single GPU (A100 80GB). If the task requires more, implement a reduced-scale version and document the difference.
- **Time constraint**: Target ≤ 8 GPU-hours. If full training is infeasible, run a shortened version (fewer epochs/steps/seeds) and document the reduction.
