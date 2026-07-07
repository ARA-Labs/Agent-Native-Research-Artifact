#!/usr/bin/env python3
"""
Reproduction Layer Experiment Runner

Orchestrates reproduction tasks: resolves rubric requirements, fills prompt
templates, and produces ready-to-execute agent configurations.

Supports two modes:
  - Per-subtask mode: one agent run per (paper, task, condition)
  - Per-paper mode (mega-task): one agent run per (paper, condition)
    with all subtasks bundled in difficulty order (easy -> medium -> hard)

Usage:
    # List all tasks for a paper
    python run_reproduction.py list rice

    # Per-subtask prompts (backward compatible)
    python run_reproduction.py prompt rice T1 ara
    python run_reproduction.py prompt rice T1 baseline
    python run_reproduction.py prompt-all rice

    # Per-paper mega-task prompts
    python run_reproduction.py paper-prompt rice ara
    python run_reproduction.py paper-judge rice ara       # judge prompt
    python run_reproduction.py paper-prompt-all           # all 30 prompts

    # Manifest (30-run per-paper mode)
    python run_reproduction.py manifest

    # Validate rubric requirement IDs for all papers
    python run_reproduction.py validate
"""

import json
import re
import sys
import os
from pathlib import Path
from typing import Optional

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # code/
TASKS_DIR = BASE_DIR / "eval" / "reproduction" / "tasks"
PROMPTS_DIR = BASE_DIR / "eval" / "reproduction" / "prompts"
RESULTS_DIR = BASE_DIR / "eval" / "reproduction" / "results"
RUBRICS_DIR = BASE_DIR / "eval" / "rubrics"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
PDFS_DIR = BASE_DIR / "pdfs"
REPOS_DIR = BASE_DIR / "repos"


def load_rubric(paper: str) -> dict:
    """Load a PaperBench rubric JSON."""
    path = RUBRICS_DIR / f"{paper}.json"
    with open(path) as f:
        return json.load(f)


def collect_leaves(node: dict) -> dict[str, dict]:
    """Recursively collect all leaf nodes (sub_tasks == []) from a rubric tree."""
    if not node.get("sub_tasks"):
        return {node["id"]: node}
    leaves = {}
    for child in node["sub_tasks"]:
        leaves.update(collect_leaves(child))
    return leaves


def load_tasks(paper: str) -> list[dict]:
    """Load curated tasks for a paper."""
    path = TASKS_DIR / f"{paper}_tasks.json"
    with open(path) as f:
        return json.load(f)


def resolve_requirements(task: dict, leaves: dict[str, dict]) -> list[dict]:
    """Resolve rubric requirement IDs to full requirement objects."""
    resolved = []
    for rid in task["rubric_requirement_ids"]:
        if rid in leaves:
            leaf = leaves[rid]
            resolved.append({
                "id": rid,
                "requirement": leaf["requirements"],
                "weight": leaf["weight"],
                "category": leaf.get("task_category", ""),
                "fine_category": leaf.get("finegrained_task_category", ""),
            })
        else:
            resolved.append({
                "id": rid,
                "requirement": f"[UNRESOLVED: {rid}]",
                "weight": 1,
                "category": "Unknown",
                "fine_category": "Unknown",
            })
    return resolved


def mask_result_numbers(text: str) -> str:
    """Mask expected numerical results while preserving hyperparameters.

    Replaces result-oriented numbers (accuracy percentages, improvement
    deltas, approximate values) with [X] so agents cannot parrot expected
    outcomes. Preserves hyperparameters (lr, batch size, model sizes, step
    counts, etc.) since agents need those to implement correctly.
    """
    # ~N% or ~N.N% (approximate percentages — almost always results)
    text = re.sub(r'~\d+\.?\d*%', '[X]%', text)
    # "approximately N.N%" anywhere
    text = re.sub(r'approximately\s+\d+\.?\d*%', 'approximately [X]%', text,
                  flags=re.IGNORECASE)
    # "by N.N%" (improvement deltas)
    text = re.sub(r'\bby\s+\d+\.?\d*%', 'by [X]%', text, flags=re.IGNORECASE)
    # Percentages preceded by result-oriented words (with possible intervening text)
    text = re.sub(
        r'((?:accuracy|improvement|improves?|gain|achieves?|score|performance|'
        r'enhancement|reduces?|reduction|outperforms?)\s+(?:\S+\s+){0,5}?)'
        r'(\d+\.?\d*%)',
        lambda m: m.group(1) + '[X]%', text, flags=re.IGNORECASE,
    )
    # "verify that ... N.N%" — mask percentages in verification contexts
    text = re.sub(r'(verify\s+(?:\S+\s+){0,15}?)\d+\.?\d*%',
                  lambda m: m.group(1) + '[X]%', text, flags=re.IGNORECASE)
    # Standalone ~N.N (approximate values not followed by %)
    text = re.sub(r'~(\d+\.\d+)(?![%BbMmKk])', '~[X]', text)
    return text


def format_requirements(requirements: list[dict], mask: bool = False) -> str:
    """Format resolved requirements as a numbered checklist.

    If mask=True, result-oriented numbers are replaced with [X] so agents
    cannot simply parrot expected outcomes.
    """
    lines = []
    for i, req in enumerate(requirements, 1):
        req_text = req['requirement']
        if mask:
            req_text = mask_result_numbers(req_text)
        lines.append(f"{i}. **[{req['id'][:8]}]** (weight={req['weight']}) {req_text}")
    return "\n".join(lines)


def load_template(name: str) -> str:
    """Load a prompt template."""
    path = PROMPTS_DIR / f"{name}.md"
    with open(path) as f:
        return f.read()


def generate_prompt(paper: str, task: dict, condition: str,
                    seed: int = 0) -> str:
    """Generate a filled prompt for a (paper, task, condition) triple.

    Result-oriented numbers are masked so agents must compute results
    rather than parrot expected values from the source material.
    """
    rubric = load_rubric(paper)
    leaves = collect_leaves(rubric)
    requirements = resolve_requirements(task, leaves)
    req_text = format_requirements(requirements, mask=True)

    task_id = task["task_id"]
    masked_goal = mask_result_numbers(task["goal"])
    output_dir = str(RESULTS_DIR / f"{task_id}_{condition}_seed{seed}")

    if condition == "ara":
        template = load_template("ara_reproduction_agent")
        prompt = template.replace("{task_goal}", masked_goal)
        prompt = prompt.replace("{rubric_requirements}", req_text)
        prompt = prompt.replace("{artifact_dir}", str(ARTIFACTS_DIR / paper))
        prompt = prompt.replace("{output_dir}", output_dir)
        prompt = prompt.replace("{task_id}", task_id)
        prompt = prompt.replace("{difficulty}", task["difficulty"])
    elif condition == "baseline":
        template = load_template("baseline_reproduction_agent")
        prompt = template.replace("{task_goal}", masked_goal)
        prompt = prompt.replace("{rubric_requirements}", req_text)
        prompt = prompt.replace("{pdf_path}", str(PDFS_DIR / f"{paper}.pdf"))
        prompt = prompt.replace("{repo_dir}", str(REPOS_DIR / paper))
        prompt = prompt.replace("{output_dir}", output_dir)
        prompt = prompt.replace("{task_id}", task_id)
        prompt = prompt.replace("{difficulty}", task["difficulty"])
    else:
        raise ValueError(f"Unknown condition: {condition}")

    return prompt


def generate_judge_prompt(paper: str, task: dict, condition: str,
                          seed: int = 0) -> str:
    """Generate a filled judge prompt for evaluating an agent run."""
    rubric = load_rubric(paper)
    leaves = collect_leaves(rubric)
    requirements = resolve_requirements(task, leaves)
    req_text = format_requirements(requirements)

    task_id = task["task_id"]
    output_dir = str(RESULTS_DIR / f"{task_id}_{condition}_seed{seed}")

    template = load_template("reproduction_judge")
    prompt = template.replace("{task_goal}", task["goal"])
    prompt = prompt.replace("{rubric_requirements}", req_text)
    prompt = prompt.replace("{output_dir}", output_dir)
    prompt = prompt.replace("{task_id}", task_id)

    return prompt


DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def sort_tasks_by_difficulty(tasks: list[dict]) -> list[dict]:
    """Sort tasks by difficulty (easy -> medium -> hard), preserving order within each level."""
    return sorted(tasks, key=lambda t: (DIFFICULTY_ORDER.get(t["difficulty"], 99),
                                         t["task_id"]))


def format_source_material_block(paper: str, condition: str) -> str:
    """Generate the condition-specific source material section."""
    if condition == "ara":
        artifact_dir = str(ARTIFACTS_DIR / paper)
        return f"""You have access to the paper's **structured research artifact (ARA)**. You have NO access to the original paper PDF or its companion GitHub repository.

**ARA artifact location**: `{artifact_dir}`

**How to navigate it:**

| Path | What it contains |
|------|-----------------|
| `PAPER.md` | Overview and index — **read this first** |
| `logic/claims.md` | Paper's claims, hypotheses, falsification criteria |
| `logic/experiments.md` | Experimental setups, datasets, hyperparameters, evaluation protocols |
| `logic/concepts.md` | Key technical concepts and definitions |
| `logic/solution/` | Algorithm details, architecture specifications, mathematical formulations |
| `src/` | Implementation configs, environment setup, dependency lists, execution instructions |
| `evidence/` | Reported results, figure data, table data |"""
    elif condition == "baseline":
        pdf_path = str(PDFS_DIR / f"{paper}.pdf")
        repo_dir = str(REPOS_DIR / paper)
        return f"""You have access to the **original paper PDF** and its **companion GitHub repository**. You have NO access to any structured artifact (ARA).

- **Paper PDF**: `{pdf_path}` — Read this for methodology, experimental setup, and expected results
- **GitHub repository**: `{repo_dir}` — Explore this for reference implementations, configurations, data processing scripts, and pretrained model references

**Suggested reading order:**
1. Read the paper PDF to understand the method, experiments, and evaluation protocol
2. Explore the repository structure (`ls`, `README`, main scripts)
3. Identify relevant source files for the specific experiments you need to reproduce
4. Check for configuration files, hyperparameter settings, and data preparation scripts"""
    else:
        raise ValueError(f"Unknown condition: {condition}")


def format_subtasks_block(tasks: list[dict], leaves: dict[str, dict],
                          mask: bool = False) -> str:
    """Format all subtasks with their requirements into the prompt block."""
    sorted_tasks = sort_tasks_by_difficulty(tasks)
    blocks = []
    for i, task in enumerate(sorted_tasks, 1):
        requirements = resolve_requirements(task, leaves)
        req_text = format_requirements(requirements, mask=mask)
        goal = mask_result_numbers(task["goal"]) if mask else task["goal"]
        block = f"""### Subtask {i} of {len(sorted_tasks)}: {goal} [{task['difficulty']}]

**Success criteria:**

{req_text}"""
        blocks.append(block)
    return "\n\n".join(blocks)


def generate_paper_prompt(paper: str, condition: str,
                          seed: int = 0) -> str:
    """Generate a paper-level mega-task prompt with all subtasks bundled.

    Subtasks are sorted by difficulty (easy -> medium -> hard). Result-oriented
    numbers are masked so agents must compute results rather than parrot.
    """
    tasks = load_tasks(paper)
    rubric = load_rubric(paper)
    leaves = collect_leaves(rubric)

    sorted_tasks = sort_tasks_by_difficulty(tasks)
    output_dir = str(RESULTS_DIR / f"{paper}_{condition}_seed{seed}")

    template = load_template("paper_reproduction_agent")
    source_block = format_source_material_block(paper, condition)
    subtasks_block = format_subtasks_block(tasks, leaves, mask=True)

    prompt = template.replace("{paper_name}", paper)
    prompt = prompt.replace("{n_subtasks}", str(len(tasks)))
    prompt = prompt.replace("{output_dir}", output_dir)
    prompt = prompt.replace("{source_material_block}", source_block)
    prompt = prompt.replace("{subtasks_block}", subtasks_block)

    return prompt


def generate_paper_judge_prompt(paper: str, condition: str,
                                seed: int = 0) -> str:
    """Generate a paper-level judge prompt (unmasked) for evaluating a mega-task run."""
    tasks = load_tasks(paper)
    rubric = load_rubric(paper)
    leaves = collect_leaves(rubric)

    output_dir = str(RESULTS_DIR / f"{paper}_{condition}_seed{seed}")

    template = load_template("paper_reproduction_judge")
    subtasks_block = format_subtasks_block(tasks, leaves, mask=False)

    prompt = template.replace("{paper_name}", paper)
    prompt = prompt.replace("{n_subtasks}", str(len(tasks)))
    prompt = prompt.replace("{output_dir}", output_dir)
    prompt = prompt.replace("{subtasks_block}", subtasks_block)

    return prompt


def cmd_paper_prompt(paper: str, condition: str):
    """Generate and print a paper-level mega-task prompt."""
    prompt = generate_paper_prompt(paper, condition)
    print(prompt)


def cmd_paper_judge(paper: str, condition: str):
    """Generate and print a paper-level judge prompt."""
    prompt = generate_paper_judge_prompt(paper, condition)
    print(prompt)


def cmd_paper_prompt_all():
    """Generate all paper-level prompts (15 papers x 2 conditions) and save to files."""
    task_files = sorted(TASKS_DIR.glob("*_tasks.json"))
    out_dir = PROMPTS_DIR / "generated" / "paper_level"
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for tf in task_files:
        paper = tf.stem.replace("_tasks", "")
        for condition in ["ara", "baseline"]:
            prompt = generate_paper_prompt(paper, condition)
            fname = f"{paper}_{condition}.md"
            with open(out_dir / fname, "w") as f:
                f.write(prompt)
            print(f"  Written: {out_dir / fname}")
            count += 1

    print(f"\nGenerated {count} paper-level prompts in {out_dir}")


def cmd_list(paper: str):
    """List all tasks for a paper."""
    tasks = load_tasks(paper)
    rubric = load_rubric(paper)
    leaves = collect_leaves(rubric)

    print(f"\n{'='*70}")
    print(f"Paper: {paper}  |  {len(tasks)} tasks  |  {len(leaves)} rubric leaves")
    print(f"{'='*70}\n")

    for task in tasks:
        reqs = resolve_requirements(task, leaves)
        unresolved = sum(1 for r in reqs if r["requirement"].startswith("[UNRESOLVED"))
        total_weight = sum(r["weight"] for r in reqs if not r["requirement"].startswith("[UNRESOLVED"))

        print(f"  {task['task_id']}  [{task['difficulty']}]")
        print(f"    Goal: {task['goal'][:100]}...")
        print(f"    Requirements: {task['n_requirements']} ({unresolved} unresolved)")
        print(f"    Total weight: {total_weight}")
        print(f"    Hypotheses: {', '.join(task['hypotheses_tested'][:2])}")
        print()


def cmd_prompt(paper: str, task_suffix: str, condition: str):
    """Generate and print a prompt."""
    tasks = load_tasks(paper)
    task_id = f"{paper}_{task_suffix}"
    task = next((t for t in tasks if t["task_id"] == task_id), None)
    if not task:
        print(f"Task {task_id} not found. Available: {[t['task_id'] for t in tasks]}")
        sys.exit(1)

    prompt = generate_prompt(paper, task, condition)
    print(prompt)


def cmd_prompt_all(paper: str):
    """Generate all prompts for a paper and save to files."""
    tasks = load_tasks(paper)
    out_dir = PROMPTS_DIR / "generated" / paper
    out_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        for condition in ["ara", "baseline"]:
            prompt = generate_prompt(paper, task, condition)
            fname = f"{task['task_id']}_{condition}.md"
            with open(out_dir / fname, "w") as f:
                f.write(prompt)
            print(f"  Written: {out_dir / fname}")

    print(f"\nGenerated {len(tasks) * 2} prompts in {out_dir}")


def cmd_validate():
    """Validate all rubric requirement IDs across all papers."""
    task_files = sorted(TASKS_DIR.glob("*_tasks.json"))
    total_tasks = 0
    total_reqs = 0
    total_unresolved = 0

    for tf in task_files:
        paper = tf.stem.replace("_tasks", "")
        tasks = load_tasks(paper)
        rubric = load_rubric(paper)
        leaves = collect_leaves(rubric)

        paper_unresolved = 0
        for task in tasks:
            reqs = resolve_requirements(task, leaves)
            unresolved = [r for r in reqs if r["requirement"].startswith("[UNRESOLVED")]
            paper_unresolved += len(unresolved)
            total_reqs += len(reqs)

        status = "OK" if paper_unresolved == 0 else f"WARN: {paper_unresolved} unresolved"
        print(f"  {paper:40s}  {len(tasks)} tasks  {sum(t['n_requirements'] for t in tasks):4d} reqs  {status}")
        total_tasks += len(tasks)
        total_unresolved += paper_unresolved

    print(f"\nTotal: {total_tasks} tasks, {total_reqs} requirements, {total_unresolved} unresolved")


def cmd_manifest():
    """Generate a paper-level run manifest (paper × condition = 30 runs)."""
    task_files = sorted(TASKS_DIR.glob("*_tasks.json"))
    manifest = []

    for tf in task_files:
        paper = tf.stem.replace("_tasks", "")
        tasks = load_tasks(paper)
        difficulty_counts = {}
        total_reqs = 0
        for task in tasks:
            d = task["difficulty"]
            difficulty_counts[d] = difficulty_counts.get(d, 0) + 1
            total_reqs += task["n_requirements"]

        for condition in ["ara", "baseline"]:
            manifest.append({
                "paper": paper,
                "condition": condition,
                "n_subtasks": len(tasks),
                "n_requirements": total_reqs,
                "subtask_difficulties": difficulty_counts,
            })

    out_path = RESULTS_DIR / "run_manifest.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated manifest with {len(manifest)} runs -> {out_path}")

    # Summary
    by_condition = {}
    for m in manifest:
        by_condition[m["condition"]] = by_condition.get(m["condition"], 0) + 1
    print(f"  By condition: {by_condition}")
    total_reqs = sum(m["n_requirements"] for m in manifest)
    print(f"  Total requirement evaluations: {total_reqs}")


def cmd_manifest_subtask():
    """Generate the legacy per-subtask manifest (paper × task × condition = 300 runs)."""
    task_files = sorted(TASKS_DIR.glob("*_tasks.json"))
    manifest = []

    for tf in task_files:
        paper = tf.stem.replace("_tasks", "")
        tasks = load_tasks(paper)
        for task in tasks:
            for condition in ["ara", "baseline"]:
                manifest.append({
                    "paper": paper,
                    "task_id": task["task_id"],
                    "condition": condition,
                    "difficulty": task["difficulty"],
                    "n_requirements": task["n_requirements"],
                })

    out_path = RESULTS_DIR / "run_manifest_subtask.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated subtask manifest with {len(manifest)} runs -> {out_path}")

    by_condition = {}
    by_difficulty = {}
    for m in manifest:
        by_condition[m["condition"]] = by_condition.get(m["condition"], 0) + 1
        by_difficulty[m["difficulty"]] = by_difficulty.get(m["difficulty"], 0) + 1
    print(f"  By condition: {by_condition}")
    print(f"  By difficulty: {by_difficulty}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list" and len(sys.argv) >= 3:
        cmd_list(sys.argv[2])
    # Per-subtask commands (backward compatible)
    elif cmd == "prompt" and len(sys.argv) >= 5:
        cmd_prompt(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "prompt-all" and len(sys.argv) >= 3:
        cmd_prompt_all(sys.argv[2])
    # Per-paper mega-task commands
    elif cmd == "paper-prompt" and len(sys.argv) >= 4:
        cmd_paper_prompt(sys.argv[2], sys.argv[3])
    elif cmd == "paper-judge" and len(sys.argv) >= 4:
        cmd_paper_judge(sys.argv[2], sys.argv[3])
    elif cmd == "paper-prompt-all":
        cmd_paper_prompt_all()
    # Manifests
    elif cmd == "manifest":
        cmd_manifest()
    elif cmd == "manifest-subtask":
        cmd_manifest_subtask()
    elif cmd == "validate":
        cmd_validate()
    else:
        print(__doc__)
        sys.exit(1)
