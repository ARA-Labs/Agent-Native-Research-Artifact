# Reproduction Task: {task_id}

## Context

You are a **coding agent** participating in a controlled experiment. Your job is to **reproduce an experimental result** from a machine learning paper using the original paper PDF and its companion GitHub repository. You have NO access to any structured artifact (ARA).

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

## Source Material

- **Paper PDF**: `{pdf_path}` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `{repo_dir}` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiment you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts

## Working Directory

Write ALL code, data, logs, and outputs to: `{output_dir}`

Create this directory if it does not exist.

## Experiment Process

Follow this workflow:

### Phase 1: Understand
- Read the paper PDF for methodology and experimental details
- Explore the repo for reference code, configs, and READMEs
- Identify the specific experiment/table/figure you need to reproduce

### Phase 2: Plan
- Identify what code components are needed
- Decide whether to adapt existing repo code or write from scratch
- List dependencies to install
- Determine data requirements (downloads, preprocessing)

### Phase 3: Implement
- Write clean, runnable code in `{output_dir}/`
- You may copy and adapt code from the repository, but all runnable code must be in your output directory
- Install any required packages via pip/conda
- Download any required datasets or pretrained models
- Configure hyperparameters as specified in the paper

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
- **Do NOT hardcode expected values.** Your results must come from actually running the experiment, not from copying numbers you found in the paper or repository.
- **Hardware constraint**: Assume you have access to a single GPU (A100 80GB). If the task requires more, implement a reduced-scale version and document the difference.
- **Time constraint**: Target ≤ 8 GPU-hours. If full training is infeasible, run a shortened version (fewer epochs/steps/seeds) and document the reduction.
