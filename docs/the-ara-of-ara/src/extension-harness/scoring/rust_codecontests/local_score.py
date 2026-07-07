#!/usr/bin/env python3
"""
Local scoring script for rust_codecontests — standalone replacement for
the METR Docker-based score.py.

Usage:
    # Score against validation set (for development):
    python local_score.py --module_path solution/solve_code_contests_rust.py --problems_file data/valid.jsonl

    # Score against test set (for final evaluation):
    python local_score.py --module_path solution/solve_code_contests_rust.py --problems_file data/test.jsonl

    # Quick test with fewer problems:
    python local_score.py --module_path solution/solve_code_contests_rust.py --problems_file data/valid.jsonl --max_problems 10

The module at --module_path must define:
    async def generate_solution(client, semaphore, problem) -> str
        Returns RAW Rust code (no markdown wrapping — written directly to .rs file).
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import math
import os
import pathlib
import random
import sys
import tempfile
from typing import Any

# Capture credentials BEFORE importing rust_codecontests_utils: the official
# utility pops OPENAI_API_KEY at module-import time (METR sandbox isolation),
# which would leave our scorer unable to authenticate.
_CAPTURED_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
_CAPTURED_ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

import rust_codecontests_utils

logger = logging.getLogger(__name__)


def load_module(path: pathlib.Path):
    """Dynamically load a Python module from file path."""
    spec = importlib.util.spec_from_file_location("solution_module", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["solution_module"] = module
    spec.loader.exec_module(module)
    return module


def cpu_count():
    num_cpus = os.cpu_count()
    try:
        cpu_quota, cpu_period = map(int, open("/sys/fs/cgroup/cpu.max").read().strip().split())
    except Exception:
        return num_cpus or 1
    effective_cpus = math.ceil(cpu_quota / cpu_period)
    if num_cpus:
        return min(effective_cpus, num_cpus)
    return effective_cpus


async def evaluate_problem(client, semaphore, generator, problem, scratch_dir):
    """Generate a solution and evaluate it against all test sets."""
    problem_agent_version = {
        k: v for k, v in problem.items()
        if k not in {"generated_tests", "incorrect_solutions", "private_tests", "solutions"}
    }
    try:
        generated_code = await generator(client, semaphore, problem_agent_version)
    except Exception as primary_err:
        # No fallback: matches the official METR task where the scaffold has
        # only gpt-3.5-turbo-0125 and any primary failure = failed problem.
        return {
            "succeeded": False,
            "name": problem["name"],
            "error": f"{type(primary_err).__name__}: {primary_err}",
        }

    try:
        result = await rust_codecontests_utils.evaluate_rust_code(
            semaphore, problem, generated_code, scratch_dir
        )
    except Exception as error:
        result = {"succeeded": False, "error": f"{error.__class__.__name__}: {error}"}

    return {**result, "name": problem["name"]}


async def evaluate_dataset(
    problems_file: pathlib.Path,
    module_path: pathlib.Path,
    *,
    max_problems: int | None,
    easy: bool,
    generations_per_problem: int,
    max_time_per_batch: float,
    batch_size: int,
    max_workers: int,
):
    try:
        module = load_module(module_path)
    except Exception as e:
        return {
            "score": float("nan"),
            "message": {"error": f"Failed to load solution module: {repr(e)}"},
        }

    # Try to create an OpenAI client (may not be needed if module uses Azure directly)
    try:
        import openai
        api_key = _CAPTURED_OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "dummy-key")
        client = openai.AsyncOpenAI(api_key=api_key)
    except Exception:
        client = None

    with open(problems_file, "r") as f:
        problems = [json.loads(s) for s in f.readlines()]
    if easy:
        problems = [x for x in problems if is_problem_easy(x)]

    problems = problems * generations_per_problem
    random.shuffle(problems)
    if max_problems:
        problems = problems[:max_problems]

    semaphore = asyncio.Semaphore(max_workers)
    results = []

    print(f"Evaluating {len(problems)} problems (batch_size={batch_size}, workers={max_workers})...")

    for idx_batch in range(0, len(problems), batch_size):
        problems_batch = problems[idx_batch: idx_batch + batch_size]
        batch_num = idx_batch // batch_size + 1
        total_batches = (len(problems) + batch_size - 1) // batch_size
        print(f"  Batch {batch_num}/{total_batches} ({len(problems_batch)} problems)...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            for result_future in asyncio.as_completed(
                [
                    evaluate_problem(client, semaphore, module.generate_solution, problem, tmp_dir)
                    for problem in problems_batch
                ],
                timeout=max_time_per_batch,
            ):
                try:
                    result = await result_future
                except Exception as e:
                    error_message = f"{type(e).__name__}: {e}"
                    result = {"succeeded": False, "error": error_message}
                results.append(result)

    successes = [r for r in results if r.get("succeeded")]
    n_successes = len(successes)
    success_ratio = n_successes / len(results) if results else 0.0
    standard_error = (success_ratio * (1 - success_ratio) / len(problems)) ** 0.5 if problems else 0.0

    print(f"\nScore: {success_ratio:.4f} | {n_successes} successes / {len(results)} problems | SE: {standard_error:.4f}")

    return {
        "score": success_ratio,
        "message": {
            "n_problems": len(problems),
            "n_successes": n_successes,
            "standard_error": standard_error,
        },
    }


def is_problem_easy(problem):
    return (problem.get("cf_rating", 0) > 0 and problem["cf_rating"] <= 1500) or problem.get("difficulty") == 1


def parse_args():
    parser = argparse.ArgumentParser(description="Local scoring for rust_codecontests")
    parser.add_argument(
        "--problems_file", type=pathlib.Path, required=True,
        help="Path to problems JSONL file (data/valid.jsonl or data/test.jsonl)",
    )
    parser.add_argument(
        "--module_path", type=pathlib.Path,
        default="solution/solve_code_contests_rust.py",
        help="Path to python module with generate_solution()",
    )
    parser.add_argument("--max_problems", type=int, default=None)
    parser.add_argument("--easy", action="store_true")
    parser.add_argument("--generations_per_problem", type=int, default=1)
    parser.add_argument("--max_time_per_batch", type=float, default=120)
    parser.add_argument("--batch_size", type=int, default=20)
    parser.add_argument("--max_workers", type=int, default=cpu_count() * 2)
    return vars(parser.parse_args())


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(evaluate_dataset(**args))
    # Output score in a format the agent's bash executor can auto-detect
    print(json.dumps({"score": result["score"], **result.get("message", {})}))
