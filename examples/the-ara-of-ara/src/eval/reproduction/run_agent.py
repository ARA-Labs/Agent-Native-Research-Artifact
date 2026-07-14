#!/usr/bin/env python3
"""
Reproduction Agent — Execution Engine

Runs a Claude coding agent that autonomously implements and executes ML
experiments. Evaluates results against PaperBench rubric requirements.

Two conditions:
  - ARA: agent reads only the structured ARA artifact
  - Baseline: agent reads the original paper PDF + GitHub repo

Two modes:
  - Per-subtask: one agent run per (paper, task, condition, seed)
  - Per-paper (mega-task): one agent run per (paper, condition, seed)

Usage:
    # Per-subtask commands
    python run_agent.py run <paper> <task_suffix> <condition> [--seed S]
    python run_agent.py run-batch [--workers N] [--paper P] [--difficulty D] [--seed S]
    python run_agent.py judge [--paper P]
    python run_agent.py analyze

    # Paper-level mega-task commands
    python run_agent.py run-paper <paper> <condition> [--seed S]
    python run_agent.py run-paper-batch [--workers N] [--paper P] [--seed S]
    python run_agent.py judge-paper [--paper P]
    python run_agent.py analyze-paper
"""

import argparse
import base64
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))
from run_reproduction import (
    generate_prompt, generate_judge_prompt,
    generate_paper_prompt, generate_paper_judge_prompt,
    load_tasks, load_rubric, collect_leaves,
    resolve_requirements, format_requirements,
    sort_tasks_by_difficulty,
    RESULTS_DIR, ARTIFACTS_DIR, PDFS_DIR, REPOS_DIR, BASE_DIR,
)

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

import anthropic
from openai import AzureOpenAI

# ── Configuration ────────────────────────────────────────────────────
AGENT_MODEL = "claude-sonnet-4-6"
JUDGE_MODEL = "claude-opus-4-6"
MAX_AGENT_TURNS = 200

# Per-paper token budgets — hardcoded based on task difficulty distribution,
# total requirements, and estimated complexity (env setup, training runs, etc.).
# Rationale: the old formula (5M + 50k*n_reqs) was too tight — the pilot on
# sequential-neural used 92% of 9.6M and couldn't finish hard tasks.
# These budgets give ~50-70% more headroom, weighted toward papers with more
# hard tasks or complex environments (Julia, MuJoCo, diffusion training).
PAPER_TOKEN_BUDGETS = {
    "stochastic-interpolants":              14_000_000,  #  84 reqs, 5E/3M/2H, diffusion + ODE solvers
    "sequential-neural-score-estimation":   15_000_000,  #  94 reqs, 4E/4M/2H, Julia/diffeqtorch env
    "mechanistic-understanding":            15_000_000,  #  94 reqs, 4E/2M/4H, 4 hard tasks
    "bbox":                                 16_000_000,  # 102 reqs, 3E/3M/4H, LLM API + adapter training
    "pinn":                                 16_000_000,  # 104 reqs, 3E/3M/4H, PDE optimization
    "rice":                                 16_000_000,  # 104 reqs, 2E/4M/4H, MuJoCo envs
    "bam":                                  17_000_000,  # 113 reqs, 3E/4M/3H, variational inference
    "adaptive-pruning":                     17_000_000,  # 121 reqs, 3E/4M/3H, pruning + fine-tuning
    "sample-specific-masks":                17_000_000,  # 123 reqs, 3E/4M/3H, mask learning
    "self-expansion":                       18_000_000,  # 129 reqs, 2E/3M/5H, 5 hard tasks + CL
    "test-time-model-adaptation":           18_000_000,  # 130 reqs, 3E/4M/3H, adaptation at test time
    "ftrl":                                 18_000_000,  # 133 reqs, 1E/5M/4H, RL fine-tuning, only 1 easy
    "self-composing-policies":              18_000_000,  # 133 reqs, 4E/2M/4H, MuJoCo + policy composition
    "fre":                                  18_000_000,  # 134 reqs, 2E/4M/4H, RL + representation learning
    "all-in-one":                           20_000_000,  # 143 reqs, 3E/2M/5H, 5 hard tasks, highest reqs
}
# Fallback for papers not in the dict (e.g. new papers added later)
TOKEN_BUDGET_FALLBACK_BASE = 8_000_000
TOKEN_BUDGET_FALLBACK_PER_REQ = 75_000
TOKEN_BUDGET_FALLBACK_CAP = 20_000_000

MAX_TOTAL_OUTPUT_TOKENS = 3_000_000
BASH_DEFAULT_TIMEOUT = 7200     # 2 hrs (visual reprogramming: 40-100 min/seed)
BASH_MAX_TIMEOUT = 28_800       # 8 hrs
MAX_TOOL_OUTPUT_CHARS = 30_000   # tool output cap (bash, search_files)
MAX_FILE_READ_BYTES = 500_000
TEMPERATURE = 1.0

# Context management (summarize-and-prune)
MAX_CONTEXT_TOKENS = 180_000    # compress when est. context exceeds this
CHARS_PER_TOKEN = 4             # rough token estimate
KEEP_RECENT_PAIRS = 15          # keep last N (assistant+user) turn pairs
# Summarization uses Azure OpenAI gpt-5-mini (reasoning model, better quality)
SUMMARY_MODEL = "gpt-5-mini"
MAX_SUMMARY_TOKENS = 8192       # max tokens for the compressed summary

SYSTEM_PROMPT = (
    "You are an expert ML engineer reproducing experimental results. "
    "Follow the instructions precisely. Use tools to read source material, "
    "write code, install packages, run experiments, and debug issues. "
    "When finished, write RESULT.md in the output directory and call the "
    "'done' tool with a brief summary.\n\n"
    "IMPORTANT GPU PROCESS MANAGEMENT:\n"
    "- NEVER run GPU scripts in the background (no '&', no 'nohup'). "
    "Always run GPU-intensive scripts in the foreground so they complete "
    "before you proceed.\n"
    "- If you need to run a long training job, run it directly and wait "
    "for it to finish. Set an appropriate timeout if needed.\n"
    "- Before starting a new GPU-intensive script, kill any previous GPU "
    "processes you started: `pkill -f 'python.*subtask' || true`\n"
    "- NEVER leave orphaned GPU processes running. If you move on from a "
    "script, make sure it has finished or kill it first."
)

# ── Tool Definitions ─────────────────────────────────────────────────
TOOLS = [
    {
        "name": "read_file",
        "description": (
            "Read a file from the filesystem. Handles text files and PDFs. "
            "For large files, use offset and limit to read a portion."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"},
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (0-indexed)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates parent directories if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Replace a specific string in a file. "
            "The old_string must appear exactly once in the file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path"},
                "old_string": {"type": "string", "description": "Text to find"},
                "new_string": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "bash",
        "description": (
            "Execute a bash command. Working directory is the output directory. "
            "Use for installing packages, running scripts, downloading data, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command to run"},
                "timeout": {
                    "type": "integer",
                    "description": f"Timeout in seconds (default {BASH_DEFAULT_TIMEOUT})",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_files",
        "description": "List files matching a glob pattern in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.py')"},
                "path": {"type": "string", "description": "Directory to search in"},
            },
            "required": ["pattern", "path"],
        },
    },
    {
        "name": "search_files",
        "description": "Search file contents with a regex pattern. Returns matching lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "path": {"type": "string", "description": "File or directory to search"},
                "file_pattern": {
                    "type": "string",
                    "description": "Glob filter for files (e.g. '*.py')",
                },
            },
            "required": ["pattern", "path"],
        },
    },
    {
        "name": "done",
        "description": (
            "Signal that you have completed the task. "
            "Call this after writing RESULT.md."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was accomplished",
                },
            },
            "required": ["summary"],
        },
        # Cache breakpoint: system prompt + all tool defs are static
        "cache_control": {"type": "ephemeral"},
    },
]


# ── Agent ─────────────────────────────────────────────────────────────

DOCKER_IMAGE = "ara-repro-agent"


class ReproductionAgent:
    """Runs a coding agent for a single reproduction task."""

    def __init__(self, paper: str, task: dict, condition: str,
                 seed: int = 0, use_docker: bool = False):
        self.paper = paper
        self.task = task
        self.condition = condition
        self.task_id = task["task_id"]
        self.seed = seed

        # Output directory
        self.output_dir = RESULTS_DIR / f"{self.task_id}_{condition}_seed{seed}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Docker container mode
        self.use_docker = use_docker
        self._container_id: str | None = None

        # Workspace isolation — copy source material to a temp directory
        # so agents cannot modify the original repos or artifacts
        self._workspace_dir: str | None = None
        self._setup_workspace(paper, condition)

        # Access control — evidence/ blocked for ARA to prevent result leakage
        # Cross-condition keyword blocking prevents agents from reading the
        # other condition's results (e.g. baseline peeking at *ara* dirs).
        self._cross_condition_keyword = (
            "baseline" if condition == "ara" else "ara"
        )
        if condition == "ara":
            self.blocked_prefixes = [
                str(PDFS_DIR.resolve()),
                str(REPOS_DIR.resolve()),
                str(Path(self.workspace_artifact_dir, "evidence").resolve()),
            ]
        else:
            self.blocked_prefixes = [
                str(ARTIFACTS_DIR.resolve()),
                str(REPOS_DIR.resolve()),  # block original; use workspace copy
            ]

        # Per-paper token budget: use hardcoded value if available, else fallback
        n_reqs = task.get("n_requirements", 100)
        if paper in PAPER_TOKEN_BUDGETS:
            self.max_input_tokens = PAPER_TOKEN_BUDGETS[paper]
            print(f"[budget] {paper}/{condition}: {self.max_input_tokens:,} tokens "
                  f"(hardcoded, {n_reqs} reqs)")
        else:
            self.max_input_tokens = min(
                TOKEN_BUDGET_FALLBACK_BASE + TOKEN_BUDGET_FALLBACK_PER_REQ * n_reqs,
                TOKEN_BUDGET_FALLBACK_CAP,
            )
            print(f"[budget] {paper}/{condition}: {self.max_input_tokens:,} tokens "
                  f"(fallback: {n_reqs} reqs × {TOKEN_BUDGET_FALLBACK_PER_REQ:,} "
                  f"+ {TOKEN_BUDGET_FALLBACK_BASE:,} base)")

        # Budget tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_creation_tokens = 0
        self.total_cache_read_tokens = 0
        self.turn_count = 0
        self.tool_calls_log: list[dict] = []
        self._prune_count = 0

        # Process cleanup tracking — collect process group IDs from bash
        # commands so we can kill all children on agent exit
        self._spawned_pgids: set[int] = set()
        self.start_time: float | None = None
        self.end_time: float | None = None

        self.client = anthropic.Anthropic()

    def _setup_workspace(self, paper: str, condition: str):
        """Copy baseline repo to an isolated temp workspace.

        Baseline agents get a fresh repo copy so they can't modify the
        original. ARA artifacts are read-only (write access is restricted
        to output_dir), so no copy needed.
        """
        self._workspace_dir = None
        self.workspace_artifact_dir = str(ARTIFACTS_DIR / paper)

        if condition == "baseline":
            self._workspace_dir = tempfile.mkdtemp(
                prefix=f"ara_repro_{self.task_id}_{condition}_")
            src_repo = REPOS_DIR / paper
            if src_repo.exists():
                self.workspace_repo_dir = str(
                    Path(self._workspace_dir) / "repo")
                shutil.copytree(str(src_repo), self.workspace_repo_dir,
                                symlinks=True)
                print(f"[workspace] Copied repo → {self.workspace_repo_dir}")
            else:
                self.workspace_repo_dir = str(REPOS_DIR / paper)
                print(f"[workspace] WARNING: repo not found at {src_repo}")
        else:
            self.workspace_repo_dir = ""  # not used for ARA

    def _cleanup_workspace(self):
        """Remove the temporary workspace directory."""
        if self._workspace_dir and os.path.exists(self._workspace_dir):
            shutil.rmtree(self._workspace_dir, ignore_errors=True)
            print(f"[workspace] Cleaned up {self._workspace_dir}")

    def _cleanup_gpu_processes(self):
        """Kill any GPU processes spawned by this agent in the output dir.

        This catches orphaned processes from bash commands that:
        - Started background training jobs
        - Were killed mid-execution but left GPU children
        - Had their parent shell killed on timeout but children survived

        Uses nvidia-smi to find GPU processes, then checks if they belong
        to this agent run (cwd matches output_dir).
        """
        killed = 0
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return

            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                pid = int(line)

                # Check if this process's cwd is our output directory
                try:
                    proc_cwd = os.readlink(f"/proc/{pid}/cwd")
                    if proc_cwd == str(self.output_dir.resolve()):
                        os.kill(pid, signal.SIGTERM)
                        killed += 1
                        print(f"  [cleanup] Killed GPU process {pid} "
                              f"(cwd={proc_cwd})")
                except (FileNotFoundError, PermissionError, ProcessLookupError):
                    continue

            if killed:
                time.sleep(2)  # let SIGTERM take effect
                # SIGKILL any survivors
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    pid = int(line)
                    try:
                        proc_cwd = os.readlink(f"/proc/{pid}/cwd")
                        if proc_cwd == str(self.output_dir.resolve()):
                            os.kill(pid, signal.SIGKILL)
                    except (FileNotFoundError, PermissionError,
                            ProcessLookupError):
                        pass

        except Exception as e:
            print(f"  [cleanup] GPU cleanup error: {e}")

        if killed:
            print(f"  [cleanup] Killed {killed} orphaned GPU process(es)")

    # ── Access control ────────────────────────────────────────────

    def _check_read(self, path: str) -> tuple[bool, str]:
        try:
            abs_path = str(Path(path).resolve())
        except Exception:
            return False, f"Invalid path: {path}"
        # Prefix-based blocking (artifacts, repos, evidence)
        for blocked in self.blocked_prefixes:
            if abs_path.startswith(blocked):
                kind = (
                    "the original paper/repo"
                    if self.condition == "ara"
                    else "the ARA artifact"
                )
                return False, (
                    f"ACCESS DENIED: {path} belongs to {kind}, "
                    f"which is unavailable in the {self.condition} condition."
                )
        # Cross-condition keyword blocking — prevent agents from reading
        # the other condition's result directories.  We look for
        # "_{keyword}_" (with underscores) inside any path component under
        # the results dir, which matches result folder names like
        # "self-expansion_ara_seed0" without false-positiving on the
        # project root "ara-project".
        keyword = self._cross_condition_keyword
        if keyword:
            results_prefix = str(RESULTS_DIR.resolve())
            if abs_path.startswith(results_prefix):
                rel = abs_path[len(results_prefix):]
                if f"_{keyword}_" in rel.lower() or rel.lower().endswith(f"_{keyword}"):
                    return False, (
                        f"ACCESS DENIED: {path} belongs to the other "
                        f"experimental condition and cannot be read to "
                        f"avoid data leakage."
                    )
        return True, ""

    def _check_write(self, path: str) -> tuple[bool, str]:
        try:
            abs_path = str(Path(path).resolve())
        except Exception:
            return False, f"Invalid path: {path}"
        allowed = [str(self.output_dir.resolve()), "/tmp"]
        if self._workspace_dir:
            allowed.append(self._workspace_dir)
        for prefix in allowed:
            if abs_path.startswith(prefix):
                return True, ""
        return False, f"ACCESS DENIED: writes restricted to {self.output_dir} or /tmp"

    # ── Context management (PaperBench-style pruning) ────────────

    def _estimate_tokens(self, messages: list) -> int:
        """Rough token count from message content."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content) // CHARS_PER_TOKEN
            elif isinstance(content, list):
                for block in content:
                    if hasattr(block, "text"):
                        total += len(block.text) // CHARS_PER_TOKEN
                    elif hasattr(block, "input"):
                        total += len(json.dumps(block.input)) // CHARS_PER_TOKEN
                    elif isinstance(block, dict):
                        if block.get("type") == "document":
                            total += 50_000  # ~50K tokens for a paper PDF
                        elif "content" in block:
                            total += len(str(block["content"])) // CHARS_PER_TOKEN
                        elif "text" in block:
                            total += len(block["text"]) // CHARS_PER_TOKEN
        return total

    def _compress_context(self, messages: list) -> list:
        """Compress old conversation turns into a summary when context exceeds budget.

        Instead of silently dropping turns, uses a cheap model (Haiku) to
        summarize the dropped turns into structured memory. This preserves
        critical information: files created, implementation decisions, errors
        encountered, and subtask progress.

        Layout: [user(task), asst(1), user(tools), asst(2), user(tools), ...]
        Pairs are (assistant, user) starting at index 1.
        """
        est = self._estimate_tokens(messages)
        if est <= MAX_CONTEXT_TOKENS:
            return messages

        n_pairs = (len(messages) - 1) // 2
        keep_pairs = min(KEEP_RECENT_PAIRS, n_pairs)
        drop_pairs = n_pairs - keep_pairs

        if drop_pairs <= 0:
            return messages

        # Identify messages to drop (middle turns between task prompt and recent)
        keep_from = 1 + drop_pairs * 2
        dropped_messages = messages[1:keep_from]

        # Check if there's already a prior compressed summary to carry forward
        prior_summary = None
        if (dropped_messages and isinstance(dropped_messages[0].get("content"), str)
                and dropped_messages[0]["content"].startswith("[Compressed memory")):
            prior_summary = dropped_messages[0]["content"]
            dropped_messages = dropped_messages[1:]  # don't re-summarize the summary
            # Also skip the synthetic user message that follows
            if (dropped_messages and dropped_messages[0].get("role") == "user"
                    and "[Context compressed" in str(dropped_messages[0].get("content", ""))):
                dropped_messages = dropped_messages[1:]

        # Build a summary of the dropped turns
        summary = self._summarize_dropped_turns(dropped_messages,
                                                 prior_summary=prior_summary)

        pruned = [messages[0]]

        # Insert compressed summary as a synthetic pair
        pruned.append({
            "role": "assistant",
            "content": summary,
        })
        pruned.append({
            "role": "user",
            "content": (
                "[Context compressed. Your original task prompt is preserved above. "
                "The assistant message above summarizes all prior work. "
                "Re-read files if you need details beyond the summary. "
                "Continue working on remaining subtasks.]"
            ),
        })

        # Append remaining recent messages
        pruned.extend(messages[keep_from:])

        new_est = self._estimate_tokens(pruned)
        self._prune_count += 1
        print(f"  [context] Compressed {drop_pairs} turn pairs: "
              f"~{est:,} → ~{new_est:,} est. tokens")

        return pruned

    def _summarize_dropped_turns(self, dropped_messages: list,
                                  prior_summary: str | None = None) -> str:
        """Use a cheap model to summarize dropped conversation turns.

        Extracts key information: files created/modified, decisions made,
        errors encountered and resolved, subtask progress, and important
        implementation details.

        If prior_summary is provided (from a previous compression), it is
        included as context so the new summary accumulates all prior work.
        """
        # Serialize dropped messages into a compact text representation
        serialized = _serialize_messages(dropped_messages)
        turns_text = self._format_turns_for_summary(serialized)

        # Truncate if the turns text is too large for the summary model.
        # gpt-5-mini has a large context window; allow up to ~500k chars (~125k tokens).
        max_chars = 500_000
        if prior_summary:
            max_chars -= len(prior_summary)
        if len(turns_text) > max_chars:
            turns_text = turns_text[:max_chars] + "\n\n[... truncated ...]"

        prior_block = ""
        if prior_summary:
            prior_block = (
                "--- PRIOR COMPRESSED SUMMARY ---\n"
                "The following is a summary from an earlier compression pass. "
                "Incorporate its content into your new summary, merging and "
                "deduplicating as needed.\n\n"
                f"{prior_summary}\n\n"
                "--- NEW CONVERSATION TURNS (since prior summary) ---\n\n"
            )

        summary_prompt = (
            "You are a context compression assistant for an ML experiment "
            "reproduction agent. Below is a sequence of conversation turns "
            "between the agent and its tool execution environment.\n\n"
            "Produce a structured summary that preserves ALL information the "
            "agent needs to continue working. Organize by subtask.\n\n"
            "## Required sections\n\n"
            "### 1. Subtask Progress Table\n"
            "For EACH subtask (T01–T10), state: DONE / IN PROGRESS / NOT STARTED, "
            "plus a one-line summary of what was accomplished or attempted.\n\n"
            "### 2. Files Created/Modified\n"
            "List every file path the agent wrote or edited, with a one-line "
            "description of its contents. Group by subtask.\n\n"
            "### 3. Environment Setup\n"
            "All pip install, apt-get, conda, or other setup commands that were "
            "run. Include version pins if specified.\n\n"
            "### 4. Key Implementation Decisions\n"
            "Architecture choices, hyperparameters, loss functions, data "
            "preprocessing steps, interpolant formulas, or any convention "
            "that later subtasks must stay consistent with.\n\n"
            "### 5. Numerical Results Obtained\n"
            "Any metrics, scores, or measurements the agent computed. Include "
            "exact numbers — these are needed for RESULT.md.\n\n"
            "### 6. Errors Encountered and Resolutions\n"
            "What failed, the root cause, and how it was fixed. Include "
            "workarounds (e.g., fallback from Julia to scipy).\n\n"
            "### 7. Critical Code Details\n"
            "Variable names, class names, function signatures, config paths, "
            "or formulas that must remain consistent in subsequent work.\n\n"
            "Be thorough. Do NOT omit file paths, numerical results, or "
            "formulas. The agent will use this summary as its ONLY memory "
            "of all prior work.\n\n"
            f"{prior_block}"
            "--- CONVERSATION TURNS ---\n\n"
            f"{turns_text}"
        )

        try:
            # Use Azure OpenAI gpt-5-mini for higher-quality summarization
            azure_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
            azure_endpoint = os.environ.get("AZURE_ENDPOINT", "")

            if azure_key and azure_endpoint:
                summary = self._summarize_with_azure(
                    summary_prompt, azure_key, azure_endpoint,
                    len(dropped_messages))
            else:
                # Fallback to Anthropic Haiku if Azure credentials unavailable
                print("  [context] Azure OpenAI not configured, falling back to Haiku")
                summary = self._summarize_with_anthropic(
                    summary_prompt, len(dropped_messages))

            return f"[Compressed memory of prior {len(dropped_messages)//2} work turns]\n\n{summary}"
        except Exception as e:
            # Fallback to simple pruning if summarization fails
            print(f"  [context] Summary failed ({e}), using fallback")
            return (
                f"[Context management: {len(dropped_messages)//2} earlier turns "
                f"compressed (summary unavailable). Key work is reflected in "
                f"files already written to the output directory.]"
            )

    def _summarize_with_azure(self, prompt: str, api_key: str,
                               endpoint: str, n_dropped: int) -> str:
        """Summarize using Azure OpenAI gpt-5-mini (reasoning model)."""
        azure_client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-10-21",
            azure_endpoint=endpoint,
        )
        response = azure_client.chat.completions.create(
            model=SUMMARY_MODEL,
            # gpt-5-mini is a reasoning model: use max_completion_tokens, not max_tokens.
            # Do NOT pass temperature (unsupported for GPT-5 models).
            max_completion_tokens=MAX_SUMMARY_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.choices[0].message.content.strip()
        usage = response.usage
        # Track cost — map to approximate Anthropic-equivalent token counts
        in_tokens = usage.prompt_tokens
        out_tokens = usage.completion_tokens
        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens
        print(f"  [context] Summary generated (gpt-5-mini): {len(summary)} chars "
              f"({in_tokens:,} in + {out_tokens:,} out tokens)")
        return summary

    def _summarize_with_anthropic(self, prompt: str, n_dropped: int) -> str:
        """Fallback: summarize using Anthropic Haiku."""
        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=MAX_SUMMARY_TOKENS,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.content[0].text.strip()
        usage = response.usage
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        print(f"  [context] Summary generated (haiku): {len(summary)} chars "
              f"({usage.input_tokens:,} in + {usage.output_tokens:,} out tokens)")
        return summary

    @staticmethod
    def _format_turns_for_summary(serialized_messages: list) -> str:
        """Format serialized messages into readable text for the summary model."""
        parts = []
        for i, msg in enumerate(serialized_messages):
            role = msg.get("role", "?").upper()
            content = msg.get("content", "")

            if isinstance(content, str):
                # Truncate very long individual messages
                if len(content) > 10_000:
                    content = content[:5_000] + "\n[...truncated...]\n" + content[-2_000:]
                parts.append(f"--- {role} (turn {i//2 + 1}) ---\n{content}")
            elif isinstance(content, list):
                blocks = []
                for block in content:
                    if isinstance(block, dict):
                        btype = block.get("type", "")
                        if btype == "text":
                            text = block.get("text", "")
                            if len(text) > 10_000:
                                text = text[:5_000] + "\n[...truncated...]\n" + text[-2_000:]
                            blocks.append(text)
                        elif btype == "tool_use":
                            name = block.get("name", "?")
                            inp = json.dumps(block.get("input", {}))
                            if len(inp) > 3_000:
                                inp = inp[:1_500] + "...[truncated]..." + inp[-500:]
                            blocks.append(f"[Tool call: {name}({inp})]")
                        elif btype == "tool_result":
                            tool_content = str(block.get("content", ""))
                            if len(tool_content) > 5_000:
                                tool_content = tool_content[:2_500] + "\n[...truncated...]\n" + tool_content[-1_000:]
                            blocks.append(f"[Tool result: {tool_content}]")
                        elif btype == "document":
                            blocks.append("[Document: PDF attached]")
                    elif isinstance(block, str):
                        blocks.append(block)
                parts.append(f"--- {role} (turn {i//2 + 1}) ---\n" + "\n".join(blocks))

        return "\n\n".join(parts)

    # ── Tool executors ────────────────────────────────────────────

    def _exec_read_file(self, inp: dict) -> str:
        path = inp["path"]
        ok, msg = self._check_read(path)
        if not ok:
            return msg

        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        if p.is_dir():
            return f"Path is a directory: {path}. Use list_files instead."

        # PDF handling
        if p.suffix.lower() == ".pdf":
            return self._read_pdf(p)

        try:
            raw = p.read_bytes()
            if len(raw) > MAX_FILE_READ_BYTES:
                raw = raw[:MAX_FILE_READ_BYTES]
                truncated = True
            else:
                truncated = False
            content = raw.decode("utf-8", errors="replace")
        except Exception as e:
            return f"Error reading file: {e}"

        lines = content.split("\n")
        offset = inp.get("offset", 0)
        limit = inp.get("limit")
        if offset > 0:
            lines = lines[offset:]
        if limit:
            lines = lines[:limit]

        result = "\n".join(lines)
        if truncated:
            result += f"\n\n[TRUNCATED — file exceeds {MAX_FILE_READ_BYTES} bytes]"
        return result

    def _read_pdf(self, p: Path) -> str:
        """Extract text from a PDF file."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(p))
            parts = [f"--- Page {i+1} ---\n{page.get_text()}" for i, page in enumerate(doc)]
            text = "\n".join(parts)
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(p))
                parts = [f"--- Page {i+1} ---\n{page.extract_text() or ''}"
                         for i, page in enumerate(reader.pages)]
                text = "\n".join(parts)
            except ImportError:
                return "Cannot read PDF: install pymupdf or PyPDF2"
        return text[:MAX_TOOL_OUTPUT_CHARS]

    def _exec_write_file(self, inp: dict) -> str:
        path = inp["path"]
        ok, msg = self._check_write(path)
        if not ok:
            return msg
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(inp["content"])
        return f"Written {len(inp['content'])} chars to {path}"

    def _exec_edit_file(self, inp: dict) -> str:
        path = inp["path"]
        ok, msg = self._check_write(path)
        if not ok:
            return msg
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"

        content = p.read_text()
        old = inp["old_string"]
        count = content.count(old)
        if count == 0:
            return "old_string not found in file."
        if count > 1:
            return f"old_string found {count} times; provide a more specific match."

        p.write_text(content.replace(old, inp["new_string"], 1))
        return f"Edited {path}: replaced 1 occurrence"

    def _exec_bash(self, inp: dict) -> str:
        command = inp.get("command") or inp.get("cmd") or inp.get("script")
        if not command:
            return f"Error: no 'command' field in bash tool input. Got keys: {list(inp.keys())}"

        # Cross-condition access control for bash commands.
        # Block commands that reference the other condition's result directory
        # to prevent data leakage (e.g. cp, cat, ls on *_ara_* or *_baseline_*).
        keyword = self._cross_condition_keyword
        if keyword:
            results_dir_str = str(RESULTS_DIR.resolve())
            # Check if command references a cross-condition results path
            cross_pattern = f"_{keyword}_seed"
            if cross_pattern in command:
                return (
                    f"ACCESS DENIED: This bash command references the other "
                    f"experimental condition's results (contains '{cross_pattern}'). "
                    f"Cross-condition data access is blocked to prevent leakage."
                )

        timeout = min(inp.get("timeout", BASH_DEFAULT_TIMEOUT), BASH_MAX_TIMEOUT)

        if self.use_docker:
            return self._exec_bash_docker(command, timeout)
        return self._exec_bash_local(command, timeout)

    def _exec_bash_local(self, command: str, timeout: int) -> str:
        """Execute a bash command in a new process group.

        Uses start_new_session=True so that on timeout (or cleanup) we can
        kill the entire process tree via os.killpg(), preventing orphaned
        GPU processes from lingering after the agent moves on.
        """
        proc = None
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.output_dir),
                env={**os.environ, "CUDA_VISIBLE_DEVICES": "0"},
                start_new_session=True,  # create new process group
            )
            stdout, stderr = proc.communicate(timeout=timeout)

            # Build a CompletedProcess-like object for _format_bash_output
            result = subprocess.CompletedProcess(
                args=command,
                returncode=proc.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        except subprocess.TimeoutExpired:
            # Kill the entire process group (shell + all children)
            if proc:
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGTERM)
                    time.sleep(2)
                    os.killpg(pgid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                proc.wait()  # reap zombie
            return f"Command timed out after {timeout}s (process group killed)"
        except Exception as e:
            if proc:
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
            return f"Error: {e}"
        return self._format_bash_output(result)

    def _exec_bash_docker(self, command: str, timeout: int) -> str:
        """Execute bash inside a Docker container.

        Container setup (PaperBench-style):
          - Source material mounted read-only at /source
          - Output directory mounted read-write at /output
          - GPU passthrough if available (--gpus all)
          - Persistent container per agent run (created on first bash call)
        """
        if self._container_id is None:
            self._container_id = self._start_container()
            if self._container_id is None:
                return "ERROR: Failed to start Docker container"

        try:
            result = subprocess.run(
                ["docker", "exec", self._container_id, "bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s"
        except Exception as e:
            return f"Docker exec error: {e}"
        return self._format_bash_output(result)

    def _start_container(self) -> str | None:
        """Start a persistent Docker container for this agent run."""
        container_name = f"repro-{self.task_id}-{self.condition}"

        # Mount source material read-only
        mounts = [f"-v={self.output_dir}:/output"]
        if self.condition == "ara":
            src_dir = ARTIFACTS_DIR / self.paper
            mounts.append(f"-v={src_dir}:/source:ro")
        else:
            mounts.append(f"-v={PDFS_DIR}:/pdfs:ro")
            repo_dir = REPOS_DIR / self.paper
            if repo_dir.exists():
                mounts.append(f"-v={repo_dir}:/repo:ro")

        cmd = [
            "docker", "run", "-d", "--rm",
            f"--name={container_name}",
            "-w=/output",
            *mounts,
            DOCKER_IMAGE,
            "sleep", "infinity",  # keep alive
        ]

        # Try with GPU, fall back to CPU
        for gpu_flag in (["--gpus=all"], []):
            try:
                result = subprocess.run(
                    cmd[:3] + gpu_flag + cmd[3:],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    cid = result.stdout.strip()[:12]
                    print(f"  [docker] Started container {cid} "
                          f"({'GPU' if gpu_flag else 'CPU'})")
                    return cid
            except Exception:
                continue

        print("  [docker] Failed to start container")
        return None

    def _stop_container(self):
        """Stop the Docker container."""
        if self._container_id:
            subprocess.run(
                ["docker", "stop", self._container_id],
                capture_output=True, timeout=30,
            )
            self._container_id = None

    @staticmethod
    def _format_bash_output(result) -> str:
        parts = []
        if result.stdout:
            parts.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            parts.append(f"STDERR:\n{result.stderr}")
        if result.returncode != 0:
            parts.append(f"EXIT CODE: {result.returncode}")
        output = "\n".join(parts) or "(no output)"

        if len(output) > MAX_TOOL_OUTPUT_CHARS:
            half = MAX_TOOL_OUTPUT_CHARS // 2
            output = (
                output[:half]
                + f"\n\n[... TRUNCATED {len(output) - MAX_TOOL_OUTPUT_CHARS} chars ...]\n\n"
                + output[-half:]
            )
        return output

    def _exec_list_files(self, inp: dict) -> str:
        path = inp["path"]
        ok, msg = self._check_read(path)
        if not ok:
            return msg
        p = Path(path)
        if not p.exists():
            return f"Path not found: {path}"
        matches = sorted(str(m) for m in p.glob(inp["pattern"]))
        if not matches:
            return f"No files matching '{inp['pattern']}' in {path}"
        if len(matches) > 200:
            return "\n".join(matches[:200]) + f"\n\n[... {len(matches)-200} more]"
        return "\n".join(matches)

    def _exec_search_files(self, inp: dict) -> str:
        path = inp["path"]
        ok, msg = self._check_read(path)
        if not ok:
            return msg
        fp = inp.get("file_pattern", "*")
        cmd = (
            f"rg -n --glob '{fp}' '{inp['pattern']}' '{path}' 2>/dev/null || "
            f"grep -rn --include='{fp}' '{inp['pattern']}' '{path}' 2>/dev/null"
        )
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True,
                                    text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return "Search timed out"
        out = result.stdout.strip()
        if not out:
            return f"No matches for '{inp['pattern']}' in {path}"
        if len(out) > MAX_TOOL_OUTPUT_CHARS:
            out = out[:MAX_TOOL_OUTPUT_CHARS] + "\n[TRUNCATED]"
        return out

    def _execute_tool(self, name: str, inp: dict) -> str:
        dispatch = {
            "read_file": self._exec_read_file,
            "write_file": self._exec_write_file,
            "edit_file": self._exec_edit_file,
            "bash": self._exec_bash,
            "list_files": self._exec_list_files,
            "search_files": self._exec_search_files,
            "done": lambda i: "Task marked as complete.",
        }
        fn = dispatch.get(name)
        if fn is None:
            return f"Unknown tool: {name}"
        try:
            return fn(inp)
        except (KeyError, TypeError) as e:
            return (f"Tool '{name}' received malformed input: {e}. "
                    f"Input keys: {list(inp.keys())}. "
                    f"Please check the required parameters and try again.")

    # ── Main loop ─────────────────────────────────────────────────

    def run(self) -> dict:
        self.start_time = time.time()

        # Build the initial message with workspace-isolated paths
        prompt_text = generate_prompt(
            self.paper, self.task, self.condition, seed=self.seed)

        # Replace canonical paths with workspace-isolated paths
        if self.condition == "baseline":
            prompt_text = prompt_text.replace(
                str(REPOS_DIR / self.paper), self.workspace_repo_dir)
        else:
            prompt_text = prompt_text.replace(
                str(ARTIFACTS_DIR / self.paper), self.workspace_artifact_dir)

        if self.condition == "baseline":
            # Include the paper PDF natively for better comprehension
            first_msg = self._build_baseline_first_message(prompt_text)
        else:
            first_msg = self._build_cached_first_message(prompt_text)

        messages = [first_msg]

        tag = f"{self.task_id}_{self.condition}_seed{self.seed}"
        print(f"\n{'='*70}")
        print(f"[agent] START  {tag}  (difficulty={self.task['difficulty']})")
        print(f"{'='*70}")

        try:
            return self._run_loop(messages, tag)
        finally:
            self._cleanup_workspace()

    def _run_loop(self, messages: list, tag: str) -> dict:
        done = False

        for turn in range(MAX_AGENT_TURNS):
            self.turn_count = turn + 1

            # Budget check — hard stop
            # Count all input tokens (cached reads are cheap but still count
            # toward context usage)
            # Cache reads are 10% cost — don't count them at full price
            all_input = (self.total_input_tokens
                         + self.total_cache_creation_tokens
                         + int(self.total_cache_read_tokens * 0.1))
            if all_input > self.max_input_tokens:
                print(f"[agent] INPUT TOKEN BUDGET exceeded "
                      f"({all_input:,}/{self.max_input_tokens:,})")
                break
            if self.total_output_tokens > MAX_TOTAL_OUTPUT_TOKENS:
                print(f"[agent] OUTPUT TOKEN BUDGET exceeded ({self.total_output_tokens:,})")
                break

            # Budget / turn warnings → inject into system prompt
            extra_system = ""
            budget_pct = all_input / self.max_input_tokens
            if budget_pct > 0.80:
                extra_system = (
                    f"\n\nWARNING: You have used {budget_pct:.0%} of your token "
                    f"budget ({all_input:,}/{self.max_input_tokens:,}). "
                    "Start wrapping up: write RESULT.md and call 'done' soon."
                )
            if budget_pct > 0.92:
                extra_system = (
                    f"\n\nURGENT: Token budget nearly exhausted ({budget_pct:.0%}). "
                    "Write RESULT.md NOW and call 'done' immediately."
                )
            if turn >= MAX_AGENT_TURNS - 10:
                extra_system = (
                    "\n\nURGENT: You are approaching the turn limit. "
                    "Wrap up immediately: write RESULT.md and call 'done'."
                )

            # Compress old messages if context is too large
            messages = self._compress_context(messages)

            # API call with retry
            try:
                response = self._api_call(messages, extra_system)
            except Exception as e:
                print(f"[agent] API error turn {turn+1}: {e}")
                time.sleep(10)
                try:
                    response = self._api_call(messages, extra_system)
                except Exception as e2:
                    print(f"[agent] Retry failed: {e2}")
                    break

            usage = response.usage
            self.total_input_tokens += usage.input_tokens
            self.total_output_tokens += usage.output_tokens
            cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
            cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
            self.total_cache_creation_tokens += cache_create
            self.total_cache_read_tokens += cache_read
            if cache_read > 0:
                print(f"  [cache] read={cache_read:,}  uncached={usage.input_tokens:,}")

            # Append assistant response
            messages.append({"role": "assistant", "content": response.content})

            # Extract tool-use blocks
            tool_blocks = [b for b in response.content if b.type == "tool_use"]

            if not tool_blocks:
                if response.stop_reason == "end_turn":
                    print(f"[agent] Finished (end_turn) at turn {turn+1}")
                    done = True
                    break
                continue

            # Execute each tool
            tool_results = []
            for block in tool_blocks:
                short = _summarize_input(block.name, block.input)
                print(f"  [{turn+1:3d}] {block.name}({short})")

                if block.name == "done":
                    done = True

                result_text = self._execute_tool(block.name, block.input)

                self.tool_calls_log.append({
                    "turn": turn + 1,
                    "tool": block.name,
                    "input_summary": short,
                    "output_length": len(result_text),
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })

            messages.append({"role": "user", "content": tool_results})

            if done:
                print(f"[agent] Done signal at turn {turn+1}")
                break

        self.end_time = time.time()
        if self.use_docker:
            self._stop_container()
        # Kill any orphaned GPU processes spawned by this agent
        self._cleanup_gpu_processes()
        return self._save_results(messages, done)

    def _api_call(self, messages: list, extra_system: str = ""):
        system = [{"type": "text", "text": SYSTEM_PROMPT + extra_system}]
        return self.client.messages.create(
            model=AGENT_MODEL,
            max_tokens=16384,
            temperature=TEMPERATURE,
            system=system,
            messages=messages,
            tools=TOOLS,
        )

    def _build_baseline_first_message(self, prompt_text: str) -> dict:
        """Build baseline first message with native PDF inclusion."""
        pdf_path = PDFS_DIR / f"{self.paper}.pdf"
        if pdf_path.exists():
            pdf_b64 = base64.b64encode(pdf_path.read_bytes()).decode()
            return {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt_text,
                        # Cache breakpoint: PDF + task prompt are static
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
            }
        # Fallback: no PDF file, agent will read via tool
        return {"role": "user", "content": prompt_text}

    @staticmethod
    def _build_cached_first_message(prompt_text: str) -> dict:
        """Build ARA first message with cache breakpoint."""
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt_text,
                    # Cache breakpoint: task prompt is static across turns
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        }

    def _save_results(self, messages: list, completed: bool) -> dict:
        duration = round((self.end_time or time.time()) - self.start_time, 1)
        meta = {
            "task_id": self.task_id,
            "paper": self.paper,
            "condition": self.condition,
            "seed": self.seed,
            "difficulty": self.task["difficulty"],
            "model": AGENT_MODEL,
            "temperature": TEMPERATURE,
            "turns": self.turn_count,
            "completed": completed,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_creation_tokens": self.total_cache_creation_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "duration_seconds": duration,
            "tool_calls": self.tool_calls_log,
            "context_prunes": self._prune_count,
            "result_md_exists": (self.output_dir / "RESULT.md").exists(),
        }

        (self.output_dir / "_run_meta.json").write_text(
            json.dumps(meta, indent=2))

        # Save conversation (serialize ContentBlock objects)
        serializable = _serialize_messages(messages)
        (self.output_dir / "_conversation.json").write_text(
            json.dumps(serializable, indent=2, ensure_ascii=False))

        print(f"\n[agent] SUMMARY  {self.task_id}_{self.condition}_seed{self.seed}")
        print(f"  Turns:      {self.turn_count}")
        print(f"  Tokens:     {self.total_input_tokens:,} in + {self.total_output_tokens:,} out")
        if self.total_cache_read_tokens > 0:
            total_in = (self.total_input_tokens + self.total_cache_creation_tokens
                        + self.total_cache_read_tokens)
            pct = self.total_cache_read_tokens / total_in * 100
            print(f"  Cache:      {self.total_cache_read_tokens:,} read, "
                  f"{self.total_cache_creation_tokens:,} written "
                  f"({pct:.0f}% of input from cache)")
        print(f"  Duration:   {duration}s")
        print(f"  Completed:  {completed}")
        print(f"  RESULT.md:  {meta['result_md_exists']}")
        print(f"  Output dir: {self.output_dir}\n")

        return meta


class PaperReproductionAgent(ReproductionAgent):
    """Runs a coding agent for ALL subtasks of a paper (mega-task mode).

    Inherits all tools, budget, context management, access control, and
    workspace isolation from ReproductionAgent. Overrides only prompt
    generation and metadata.
    """

    def __init__(self, paper: str, condition: str, seed: int = 0,
                 use_docker: bool = False):
        # Load tasks to compute metadata
        self._paper_tasks = load_tasks(paper)
        self._sorted_tasks = sort_tasks_by_difficulty(self._paper_tasks)

        # Create a synthetic task dict so parent's __init__ works
        synthetic_task = {
            "task_id": paper,
            "difficulty": "mixed",
            "goal": f"Reproduce all {len(self._paper_tasks)} subtasks for {paper}",
            "rubric_requirement_ids": [],
            "n_requirements": sum(t["n_requirements"] for t in self._paper_tasks),
            "hypotheses_tested": [],
        }
        super().__init__(paper, synthetic_task, condition, seed=seed,
                         use_docker=use_docker)

    def run(self, resume_from: int | None = None) -> dict:
        self.start_time = time.time()

        # Build the initial message using paper-level prompt
        prompt_text = generate_paper_prompt(
            self.paper, self.condition, seed=self.seed)

        # Replace canonical paths with workspace-isolated paths
        if self.condition == "baseline":
            prompt_text = prompt_text.replace(
                str(REPOS_DIR / self.paper), self.workspace_repo_dir)
        else:
            prompt_text = prompt_text.replace(
                str(ARTIFACTS_DIR / self.paper), self.workspace_artifact_dir)

        # Checkpoint resume
        if resume_from is not None:
            prompt_text += self._build_checkpoint_context(resume_from)

        if self.condition == "baseline":
            first_msg = self._build_baseline_first_message(prompt_text)
        else:
            first_msg = self._build_cached_first_message(prompt_text)

        messages = [first_msg]

        tag = f"{self.paper}_{self.condition}_seed{self.seed}"
        resume_tag = f" (RESUME from T{resume_from})" if resume_from else ""
        print(f"\n{'='*70}")
        print(f"[agent] START PAPER  {tag}{resume_tag}  "
              f"({len(self._paper_tasks)} subtasks)")
        print(f"{'='*70}")

        try:
            return self._run_loop(messages, tag)
        finally:
            self._cleanup_gpu_processes()
            self._cleanup_workspace()

    def _build_checkpoint_context(self, resume_from: int) -> str:
        out_dir = str(self.output_dir)
        lines = [
            f"\n\n## CHECKPOINT — Resume from Subtask {resume_from}",
            f"\nSubtasks 1-{resume_from - 1} were completed in a previous run. "
            f"All code, models, and intermediate results are already in: `{out_dir}/`",
            f"\n**DO NOT re-run subtasks 1-{resume_from - 1}.** Instead:",
            f"1. List existing files (`ls {out_dir}/`) to see what is available",
            "2. Read existing code to understand the implementation",
            f"3. Start directly from **Subtask {resume_from}**, reusing all existing models/code",
            "\nKey existing assets:",
        ]
        models_dir = self.output_dir / "models"
        if models_dir.exists():
            for d in sorted(models_dir.iterdir()):
                if d.is_dir():
                    count = len(list(d.rglob("*.zip")))
                    lines.append(f"- `models/{d.name}/`: {count} model files")
        for f in sorted(self.output_dir.glob("*results*.json")):
            lines.append(f"- `{f.name}`: previous results")
        py_files = sorted(self.output_dir.glob("*.py"))
        if py_files:
            lines.append(f"- {len(py_files)} Python scripts: "
                         + ", ".join(f.name for f in py_files[:5])
                         + ("..." if len(py_files) > 5 else ""))
        return "\n".join(lines)

    def _save_results(self, messages: list, completed: bool) -> dict:
        duration = round((self.end_time or time.time()) - self.start_time, 1)

        difficulty_counts = {}
        total_reqs = 0
        for t in self._paper_tasks:
            d = t["difficulty"]
            difficulty_counts[d] = difficulty_counts.get(d, 0) + 1
            total_reqs += t["n_requirements"]

        meta = {
            "task_id": self.paper,
            "paper": self.paper,
            "condition": self.condition,
            "seed": self.seed,
            "mode": "paper",
            "n_subtasks": len(self._paper_tasks),
            "n_requirements": total_reqs,
            "subtask_difficulties": difficulty_counts,
            "model": AGENT_MODEL,
            "temperature": TEMPERATURE,
            "turns": self.turn_count,
            "completed": completed,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_creation_tokens": self.total_cache_creation_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "duration_seconds": duration,
            "tool_calls": self.tool_calls_log,
            "context_prunes": self._prune_count,
            "result_md_exists": (self.output_dir / "RESULT.md").exists(),
        }

        (self.output_dir / "_run_meta.json").write_text(
            json.dumps(meta, indent=2))

        serializable = _serialize_messages(messages)
        (self.output_dir / "_conversation.json").write_text(
            json.dumps(serializable, indent=2, ensure_ascii=False))

        print(f"\n[agent] SUMMARY  {self.paper}_{self.condition}_seed{self.seed}")
        print(f"  Mode:       paper ({len(self._paper_tasks)} subtasks)")
        print(f"  Turns:      {self.turn_count}")
        print(f"  Tokens:     {self.total_input_tokens:,} in + "
              f"{self.total_output_tokens:,} out")
        if self.total_cache_read_tokens > 0:
            total_in = (self.total_input_tokens
                        + self.total_cache_creation_tokens
                        + self.total_cache_read_tokens)
            pct = self.total_cache_read_tokens / total_in * 100
            print(f"  Cache:      {self.total_cache_read_tokens:,} read, "
                  f"{self.total_cache_creation_tokens:,} written "
                  f"({pct:.0f}% of input from cache)")
        print(f"  Duration:   {duration}s")
        print(f"  Completed:  {completed}")
        print(f"  RESULT.md:  {meta['result_md_exists']}")
        print(f"  Output dir: {self.output_dir}\n")

        return meta


# ── Helpers ───────────────────────────────────────────────────────────

def _summarize_input(tool_name: str, inp: dict) -> str:
    if tool_name == "read_file":
        return inp.get("path", "?")
    if tool_name == "write_file":
        return f"{inp.get('path','?')} ({len(inp.get('content',''))} chars)"
    if tool_name == "edit_file":
        return inp.get("path", "?")
    if tool_name == "bash":
        cmd = inp.get("command", "?")
        return (cmd[:80] + "...") if len(cmd) > 80 else cmd
    if tool_name == "list_files":
        return f"{inp.get('pattern','?')} in {inp.get('path','?')}"
    if tool_name == "search_files":
        return f"'{inp.get('pattern','?')}' in {inp.get('path','?')}"
    if tool_name == "done":
        return (inp.get("summary", "") or "")[:80]
    return str(inp)[:80]


def _serialize_messages(messages: list) -> list:
    """Convert messages with ContentBlock objects to JSON-serializable dicts."""
    out = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            out.append(msg)
        elif isinstance(content, list):
            serialized = []
            for block in content:
                if hasattr(block, "type"):
                    if block.type == "text":
                        serialized.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        serialized.append({
                            "type": "tool_use", "id": block.id,
                            "name": block.name, "input": block.input,
                        })
                    elif block.type == "thinking":
                        serialized.append({
                            "type": "thinking",
                            "thinking": getattr(block, "thinking", ""),
                        })
                    else:
                        serialized.append({"type": block.type})
                elif isinstance(block, dict):
                    # tool_result or document blocks — already dicts
                    if block.get("type") == "document":
                        # Don't save full PDF base64 in conversation log
                        serialized.append({"type": "document", "note": "[PDF omitted]"})
                    else:
                        serialized.append(block)
                else:
                    serialized.append(str(block))
            out.append({"role": msg["role"], "content": serialized})
        else:
            out.append(msg)
    return out


# ── Commands ──────────────────────────────────────────────────────────

def cmd_run(paper: str, task_suffix: str, condition: str,
            seed: int = 0, use_docker: bool = False):
    tasks = load_tasks(paper)
    task_id = f"{paper}_{task_suffix}"
    task = next((t for t in tasks if t["task_id"] == task_id), None)
    if not task:
        avail = [t["task_id"] for t in tasks]
        print(f"Task {task_id} not found. Available: {avail}")
        sys.exit(1)

    agent = ReproductionAgent(paper, task, condition, seed=seed,
                              use_docker=use_docker)
    return agent.run()


def cmd_run_batch(workers: int = 3, paper: str | None = None,
                  difficulty: str | None = None, seed: int = 0):
    manifest_path = RESULTS_DIR / "run_manifest_subtask.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    if paper:
        manifest = [m for m in manifest if m["paper"] == paper]
    if difficulty:
        manifest = [m for m in manifest if m["difficulty"] == difficulty]

    # Skip completed
    remaining = []
    for m in manifest:
        out_dir = RESULTS_DIR / f"{m['task_id']}_{m['condition']}_seed{seed}"
        meta_path = out_dir / "_run_meta.json"
        if meta_path.exists():
            data = json.loads(meta_path.read_text())
            if data.get("completed"):
                continue
        remaining.append(m)

    print(f"[batch] {len(remaining)} remaining of {len(manifest)} total")
    if not remaining:
        return

    def _run_one(entry):
        tasks = load_tasks(entry["paper"])
        task = next((t for t in tasks if t["task_id"] == entry["task_id"]), None)
        if not task:
            return entry["task_id"], False, "Task not found"
        try:
            agent = ReproductionAgent(
                entry["paper"], task, entry["condition"], seed=seed)
            result = agent.run()
            return entry["task_id"], True, result
        except Exception as e:
            traceback.print_exc()
            return entry["task_id"], False, str(e)

    ok_count = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_run_one, m): m for m in remaining}
        for future in as_completed(futures):
            tid, ok, result = future.result()
            if ok:
                ok_count += 1
                print(f"[batch] OK: {tid}")
            else:
                print(f"[batch] FAIL: {tid}: {result}")

    print(f"[batch] Done: {ok_count}/{len(remaining)}")


def cmd_judge(paper: str | None = None):
    """Judge per-subtask runs that produced RESULT.md."""
    to_judge = []
    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        meta_path = run_dir / "_run_meta.json"
        judge_path = run_dir / "_judge_result.json"
        if not meta_path.exists() or judge_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        # Skip paper-level runs — those are handled by judge-paper
        if meta.get("mode") == "paper":
            continue
        # Judge any run that produced a RESULT.md, even if agent was cut off
        if not meta.get("result_md_exists") and not meta.get("completed"):
            continue
        if paper and meta.get("paper") != paper:
            continue
        to_judge.append(meta)

    print(f"[judge] {len(to_judge)} runs to judge")
    client = anthropic.Anthropic()

    for meta in to_judge:
        task_id = meta["task_id"]
        paper_name = meta["paper"]
        condition = meta["condition"]
        seed = meta.get("seed", 0)
        tag = f"{task_id}_{condition}_seed{seed}"

        tasks = load_tasks(paper_name)
        task = next(t for t in tasks if t["task_id"] == task_id)
        judge_prompt = generate_judge_prompt(paper_name, task, condition,
                                             seed=seed)

        # Attach agent output files
        output_dir = RESULTS_DIR / f"{task_id}_{condition}_seed{seed}"
        agent_output = _read_agent_outputs(output_dir)
        full_prompt = (
            judge_prompt
            + "\n\n---\n\n## Agent Output Files\n\n"
            + agent_output
        )

        print(f"[judge] {tag} ...", end=" ", flush=True)

        try:
            response = client.messages.create(
                model=JUDGE_MODEL,
                max_tokens=8192,
                temperature=0,
                messages=[{"role": "user", "content": full_prompt}],
            )
            raw = response.content[0].text.strip()
            (output_dir / "_judge_raw.txt").write_text(raw)
            judge_result = _extract_json(raw)
            judge_result["token_usage"] = {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            }
            (output_dir / "_judge_result.json").write_text(
                json.dumps(judge_result, indent=2))

            sr = judge_result.get("summary", {}).get("success_rate", "?")
            print(f"success_rate={sr}")

        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()


def _extract_json(raw: str) -> dict:
    """Extract JSON from a model response that may contain markdown fences or preamble."""
    text = raw.strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first { ... last }
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("Could not extract JSON from response", raw, 0)


def _read_agent_outputs(output_dir: Path) -> str:
    """Collect agent output files for the judge to review."""
    parts = []

    # RESULT.md first
    result_md = output_dir / "RESULT.md"
    if result_md.exists():
        parts.append(f"### RESULT.md\n\n{result_md.read_text()[:20000]}")

    # Python files (including subdirectories)
    for py in sorted(output_dir.rglob("*.py"))[:15]:
        if py.stat().st_size < 30000 and not py.name.startswith("_"):
            rel = py.relative_to(output_dir)
            parts.append(f"### {rel}\n\n```python\n{py.read_text()}\n```")

    # Shell scripts
    for sh in sorted(output_dir.glob("*.sh"))[:5]:
        if sh.stat().st_size < 10000:
            parts.append(f"### {sh.name}\n\n```bash\n{sh.read_text()}\n```")

    # Logs (truncated)
    for log in sorted(output_dir.glob("*.log"))[:5]:
        content = log.read_text(errors="replace")
        if len(content) > 5000:
            content = content[:2500] + "\n...[TRUNCATED]...\n" + content[-2500:]
        parts.append(f"### {log.name}\n\n```\n{content}\n```")

    # Data files (including subdirectories)
    for ext in ("*.json", "*.csv", "*.txt"):
        for f in sorted(output_dir.rglob(ext))[:5]:
            if f.name.startswith("_"):
                continue
            if f.stat().st_size < 10000:
                rel = f.relative_to(output_dir)
                parts.append(f"### {rel}\n\n```\n{f.read_text(errors='replace')}\n```")

    return "\n\n---\n\n".join(parts) if parts else "(No output files found)"


def cmd_analyze():
    """Aggregate judged per-subtask results and compute metrics."""
    results = []
    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        judge_path = run_dir / "_judge_result.json"
        meta_path = run_dir / "_run_meta.json"
        if not judge_path.exists() or not meta_path.exists():
            continue

        meta = json.loads(meta_path.read_text())
        # Skip paper-level runs — those are handled by analyze-paper
        if meta.get("mode") == "paper":
            continue
        judge = json.loads(judge_path.read_text())
        summary = judge.get("summary", {})

        results.append({
            "task_id": meta["task_id"],
            "paper": meta["paper"],
            "condition": meta["condition"],
            "seed": meta.get("seed", 0),
            "difficulty": meta.get("difficulty", "unknown"),
            "turns": meta["turns"],
            "total_tokens": meta["total_tokens"],
            "total_input_tokens": meta["total_input_tokens"],
            "total_output_tokens": meta["total_output_tokens"],
            "duration_seconds": meta["duration_seconds"],
            "success_rate": summary.get("success_rate", 0),
            "weighted_score": summary.get("weighted_score", 0),
            "max_weighted_score": summary.get("max_weighted_score", 0),
            "yes_count": summary.get("yes_count", 0),
            "partial_count": summary.get("partial_count", 0),
            "no_count": summary.get("no_count", 0),
            "fabrication_detected": summary.get("fabrication_detected", False),
        })

    if not results:
        print("[analyze] No judged results found")
        return

    ara = [r for r in results if r["condition"] == "ara"]
    base = [r for r in results if r["condition"] == "baseline"]
    avg = lambda vs: sum(vs) / len(vs) if vs else 0

    ara_sr = avg([r["success_rate"] for r in ara])
    bas_sr = avg([r["success_rate"] for r in base])

    print("\n" + "=" * 70)
    print("REPRODUCTION EVALUATION RESULTS")
    print("=" * 70)
    print(f"Runs: {len(results)} ({len(ara)} ARA, {len(base)} baseline)\n")
    print(f"Overall success rate:")
    print(f"  ARA:      {ara_sr:.1%}")
    print(f"  Baseline: {bas_sr:.1%}")
    print(f"  Delta:    {ara_sr - bas_sr:+.1%}")

    # By difficulty
    print("\nBy difficulty:")
    for diff in ["easy", "medium", "hard"]:
        a_d = [r for r in ara if r["difficulty"] == diff]
        b_d = [r for r in base if r["difficulty"] == diff]
        if a_d or b_d:
            a = avg([r["success_rate"] for r in a_d])
            b = avg([r["success_rate"] for r in b_d])
            print(f"  {diff:8s}: ARA {a:.1%} | Baseline {b:.1%} | delta {a-b:+.1%}")

    # By paper
    print("\nBy paper:")
    papers = sorted(set(r["paper"] for r in results))
    for p in papers:
        a_p = [r for r in ara if r["paper"] == p]
        b_p = [r for r in base if r["paper"] == p]
        a = avg([r["success_rate"] for r in a_p])
        b = avg([r["success_rate"] for r in b_p])
        print(f"  {p:40s}: ARA {a:.1%} | Baseline {b:.1%} | delta {a-b:+.1%}")

    # Cost
    print("\nCost (per-run average):")
    print(f"  ARA:      {avg([r['total_tokens'] for r in ara]):,.0f} tokens, "
          f"{avg([r['turns'] for r in ara]):.1f} turns")
    print(f"  Baseline: {avg([r['total_tokens'] for r in base]):,.0f} tokens, "
          f"{avg([r['turns'] for r in base]):.1f} turns")

    # Statistical test (Wilcoxon signed-rank, paired by task)
    try:
        from scipy.stats import wilcoxon
        paired = []
        for task_id in sorted(set(r["task_id"] for r in results)):
            a_runs = [r for r in ara if r["task_id"] == task_id]
            b_runs = [r for r in base if r["task_id"] == task_id]
            if a_runs and b_runs:
                paired.append((avg([r["success_rate"] for r in a_runs]),
                               avg([r["success_rate"] for r in b_runs])))
        if len(paired) >= 5:
            diffs = [a - b for a, b in paired]
            stat, p = wilcoxon(diffs, alternative="two-sided")
            print(f"\nWilcoxon signed-rank (n={len(paired)} tasks): "
                  f"stat={stat:.1f}, p={p:.6f}")
    except ImportError:
        pass

    # Save
    analysis = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_runs": len(results),
        "overall": {
            "ara_success_rate": round(ara_sr, 4),
            "baseline_success_rate": round(bas_sr, 4),
            "delta": round(ara_sr - bas_sr, 4),
        },
        "all_results": results,
    }
    out_path = RESULTS_DIR / "reproduction_analysis.json"
    out_path.write_text(json.dumps(analysis, indent=2))
    print(f"\nSaved to: {out_path}")


# ── Paper-level commands ──────────────────────────────────────────────

def cmd_run_paper(paper: str, condition: str, seed: int = 0,
                  use_docker: bool = False, resume_from: int | None = None):
    """Run all subtasks for one paper as a mega-task."""
    agent = PaperReproductionAgent(paper, condition, seed=seed,
                                   use_docker=use_docker)
    return agent.run(resume_from=resume_from)


def cmd_run_paper_batch(workers: int = 3, paper: str | None = None,
                        seed: int = 0):
    """Batch-run paper-level mega-tasks from the paper manifest."""
    manifest_path = RESULTS_DIR / "run_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    if paper:
        manifest = [m for m in manifest if m["paper"] == paper]

    # Skip completed
    remaining = []
    for m in manifest:
        out_dir = RESULTS_DIR / f"{m['paper']}_{m['condition']}_seed{seed}"
        meta_path = out_dir / "_run_meta.json"
        if meta_path.exists():
            data = json.loads(meta_path.read_text())
            if data.get("completed"):
                continue
        remaining.append(m)

    print(f"[paper-batch] {len(remaining)} remaining of {len(manifest)} total")
    if not remaining:
        return

    def _run_one(entry):
        try:
            agent = PaperReproductionAgent(
                entry["paper"], entry["condition"], seed=seed)
            result = agent.run()
            return entry["paper"], True, result
        except Exception as e:
            traceback.print_exc()
            return entry["paper"], False, str(e)

    ok_count = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_run_one, m): m for m in remaining}
        for future in as_completed(futures):
            p, ok, result = future.result()
            if ok:
                ok_count += 1
                print(f"[paper-batch] OK: {p}")
            else:
                print(f"[paper-batch] FAIL: {p}: {result}")

    print(f"[paper-batch] Done: {ok_count}/{len(remaining)}")


def cmd_judge_paper(paper: str | None = None):
    """Judge paper-level mega-task runs."""
    to_judge = []
    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        meta_path = run_dir / "_run_meta.json"
        judge_path = run_dir / "_judge_result.json"
        if not meta_path.exists() or judge_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        # Only judge paper-level runs
        if meta.get("mode") != "paper":
            continue
        # Judge any run that has output code, even if it didn't complete
        out_has_code = any(run_dir.glob("*.py"))
        if not meta.get("result_md_exists") and not meta.get("completed") and not out_has_code:
            continue
        if paper and meta.get("paper") != paper:
            continue
        to_judge.append(meta)

    print(f"[judge-paper] {len(to_judge)} runs to judge")
    client = anthropic.Anthropic()

    for meta in to_judge:
        paper_name = meta["paper"]
        condition = meta["condition"]
        seed = meta.get("seed", 0)
        tag = f"{paper_name}_{condition}_seed{seed}"

        judge_prompt = generate_paper_judge_prompt(
            paper_name, condition, seed=seed)

        # Attach agent output files
        output_dir = RESULTS_DIR / tag
        agent_output = _read_agent_outputs(output_dir)
        full_prompt = (
            judge_prompt
            + "\n\n---\n\n## Agent Output Files\n\n"
            + agent_output
        )

        print(f"[judge-paper] {tag} ...", end=" ", flush=True)

        try:
            response = client.messages.create(
                model=JUDGE_MODEL,
                max_tokens=16384,
                temperature=0,
                messages=[{"role": "user", "content": full_prompt}],
            )
            raw = response.content[0].text.strip()
            (output_dir / "_judge_raw.txt").write_text(raw)
            judge_result = _extract_json(raw)
            judge_result["token_usage"] = {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            }
            (output_dir / "_judge_result.json").write_text(
                json.dumps(judge_result, indent=2))

            sr = judge_result.get("summary", {}).get("success_rate", "?")
            print(f"success_rate={sr}")

        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()



# Difficulty multipliers: harder tasks are worth more in the final score.
# Rationale: easy tasks (setup, implementation) are necessary but less
# discriminative than hard tasks (full training + evaluation, ablations).
DIFFICULTY_MULTIPLIER = {"easy": 1.0, "medium": 2.0, "hard": 3.0}


def _compute_difficulty_weighted_score(judge: dict) -> dict:
    """Compute difficulty-weighted scores from judge results.

    Each subtask's score is multiplied by its difficulty weight before
    summing into the paper score. This rewards agents that succeed on
    harder tasks (training, evaluation, ablations) more than agents
    that only complete easy setup tasks.

    Returns dict with weighted_paper_score, max_weighted_paper_score,
    difficulty_weighted_rate, and per-difficulty breakdown.
    """
    per_difficulty = {}  # {difficulty: {"score": X, "max": Y}}
    weighted_total = 0.0
    weighted_max = 0.0

    for st in judge.get("subtask_judgments", []):
        diff = st.get("difficulty", "easy")
        mult = DIFFICULTY_MULTIPLIER.get(diff, 1.0)

        st_score = st.get("subtask_score", 0)
        st_max = st.get("max_score", 0)

        w_score = st_score * mult
        w_max = st_max * mult

        weighted_total += w_score
        weighted_max += w_max

        if diff not in per_difficulty:
            per_difficulty[diff] = {"score": 0, "max": 0, "n_subtasks": 0}
        per_difficulty[diff]["score"] += st_score
        per_difficulty[diff]["max"] += st_max
        per_difficulty[diff]["n_subtasks"] += 1

    rate = weighted_total / weighted_max if weighted_max > 0 else 0

    return {
        "weighted_paper_score": round(weighted_total, 2),
        "max_weighted_paper_score": round(weighted_max, 2),
        "difficulty_weighted_rate": round(rate, 4),
        "per_difficulty": {
            d: {
                "score": v["score"],
                "max": v["max"],
                "rate": round(v["score"] / v["max"], 4) if v["max"] > 0 else 0,
                "multiplier": DIFFICULTY_MULTIPLIER.get(d, 1.0),
                "n_subtasks": v["n_subtasks"],
            }
            for d, v in sorted(per_difficulty.items(),
                               key=lambda x: DIFFICULTY_MULTIPLIER.get(x[0], 1))
        },
    }


def cmd_analyze_paper():
    """Aggregate paper-level judged results with per-paper breakdown."""
    results = []
    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        judge_path = run_dir / "_judge_result.json"
        meta_path = run_dir / "_run_meta.json"
        if not judge_path.exists() or not meta_path.exists():
            continue

        meta = json.loads(meta_path.read_text())
        # Only paper-level runs
        if meta.get("mode") != "paper":
            continue
        judge = json.loads(judge_path.read_text())
        summary = judge.get("summary", {})

        # Compute difficulty-weighted score
        dw = _compute_difficulty_weighted_score(judge)

        results.append({
            "paper": meta["paper"],
            "condition": meta["condition"],
            "seed": meta.get("seed", 0),
            "n_subtasks": meta.get("n_subtasks", 0),
            "n_requirements": meta.get("n_requirements", 0),
            "subtask_difficulties": meta.get("subtask_difficulties", {}),
            "turns": meta["turns"],
            "total_tokens": meta["total_tokens"],
            "total_input_tokens": meta["total_input_tokens"],
            "total_output_tokens": meta["total_output_tokens"],
            "duration_seconds": meta["duration_seconds"],
            # Flat (unweighted) scores — from judge summary
            "success_rate": summary.get("success_rate", 0),
            "paper_score": summary.get("paper_score", 0),
            "max_paper_score": summary.get("max_paper_score", 0),
            # Difficulty-weighted scores
            "difficulty_weighted_rate": dw["difficulty_weighted_rate"],
            "weighted_paper_score": dw["weighted_paper_score"],
            "max_weighted_paper_score": dw["max_weighted_paper_score"],
            "per_difficulty": dw["per_difficulty"],
            # Counts
            "yes_count": summary.get("yes_count", 0),
            "partial_count": summary.get("partial_count", 0),
            "no_count": summary.get("no_count", 0),
            "fabrication_detected": summary.get("fabrication_detected", False),
        })

    if not results:
        print("[analyze-paper] No judged paper-level results found")
        return

    ara = [r for r in results if r["condition"] == "ara"]
    base = [r for r in results if r["condition"] == "baseline"]
    avg = lambda vs: sum(vs) / len(vs) if vs else 0

    ara_sr = avg([r["success_rate"] for r in ara])
    bas_sr = avg([r["success_rate"] for r in base])
    ara_dw = avg([r["difficulty_weighted_rate"] for r in ara])
    bas_dw = avg([r["difficulty_weighted_rate"] for r in base])

    print("\n" + "=" * 70)
    print("PAPER-LEVEL REPRODUCTION EVALUATION RESULTS")
    print("=" * 70)
    print(f"Runs: {len(results)} ({len(ara)} ARA, {len(base)} baseline)\n")

    print(f"Difficulty-weighted score (primary metric, easy×1 / medium×2 / hard×3):")
    print(f"  ARA:      {ara_dw:.1%}")
    print(f"  Baseline: {bas_dw:.1%}")
    print(f"  Delta:    {ara_dw - bas_dw:+.1%}")
    print()
    print(f"Flat (unweighted) success rate:")
    print(f"  ARA:      {ara_sr:.1%}")
    print(f"  Baseline: {bas_sr:.1%}")
    print(f"  Delta:    {ara_sr - bas_sr:+.1%}")

    # Per-difficulty breakdown (aggregated across papers)
    print(f"\nPer-difficulty breakdown:")
    for diff in ["easy", "medium", "hard"]:
        mult = DIFFICULTY_MULTIPLIER[diff]
        a_scores = [r["per_difficulty"].get(diff, {}).get("score", 0) for r in ara]
        a_maxes = [r["per_difficulty"].get(diff, {}).get("max", 0) for r in ara]
        b_scores = [r["per_difficulty"].get(diff, {}).get("score", 0) for r in base]
        b_maxes = [r["per_difficulty"].get(diff, {}).get("max", 0) for r in base]
        a_rate = sum(a_scores) / sum(a_maxes) if sum(a_maxes) > 0 else 0
        b_rate = sum(b_scores) / sum(b_maxes) if sum(b_maxes) > 0 else 0
        print(f"  {diff:8s} (×{mult:.0f}): ARA {a_rate:.1%} | "
              f"Baseline {b_rate:.1%} | delta {a_rate - b_rate:+.1%}")

    # Per-paper breakdown
    print("\nPer-paper breakdown:")
    papers = sorted(set(r["paper"] for r in results))
    for p in papers:
        a_p = [r for r in ara if r["paper"] == p]
        b_p = [r for r in base if r["paper"] == p]
        a_flat = avg([r["success_rate"] for r in a_p])
        b_flat = avg([r["success_rate"] for r in b_p])
        a_dw = avg([r["difficulty_weighted_rate"] for r in a_p])
        b_dw = avg([r["difficulty_weighted_rate"] for r in b_p])
        n_sub = a_p[0]["n_subtasks"] if a_p else (b_p[0]["n_subtasks"] if b_p else 0)
        print(f"  {p:40s}: ARA {a_dw:.1%} | Baseline {b_dw:.1%} | "
              f"delta {a_dw-b_dw:+.1%} | flat {a_flat:.1%}/{b_flat:.1%} | "
              f"{n_sub} subtasks")

    # Completion depth: how many subtasks did each run complete?
    print("\nCompletion depth (yes+partial per run):")
    for r in results:
        completed = r["yes_count"] + r["partial_count"]
        total = r["yes_count"] + r["partial_count"] + r["no_count"]
        tag = f"{r['paper']}_{r['condition']}_seed{r['seed']}"
        print(f"  {tag:50s}: {completed}/{total} "
              f"({completed/total:.0%})" if total > 0 else
              f"  {tag:50s}: 0/0")

    # Cost
    print("\nCost (per-run average):")
    print(f"  ARA:      {avg([r['total_tokens'] for r in ara]):,.0f} tokens, "
          f"{avg([r['turns'] for r in ara]):.1f} turns, "
          f"{avg([r['duration_seconds'] for r in ara]):.0f}s")
    print(f"  Baseline: {avg([r['total_tokens'] for r in base]):,.0f} tokens, "
          f"{avg([r['turns'] for r in base]):.1f} turns, "
          f"{avg([r['duration_seconds'] for r in base]):.0f}s")

    # Statistical test (Wilcoxon signed-rank, paired by paper)
    try:
        from scipy.stats import wilcoxon
        paired = []
        for p in papers:
            a_runs = [r for r in ara if r["paper"] == p]
            b_runs = [r for r in base if r["paper"] == p]
            if a_runs and b_runs:
                paired.append((avg([r["success_rate"] for r in a_runs]),
                               avg([r["success_rate"] for r in b_runs])))
        if len(paired) >= 5:
            diffs = [a - b for a, b in paired]
            stat, pval = wilcoxon(diffs, alternative="two-sided")
            print(f"\nWilcoxon signed-rank (n={len(paired)} papers): "
                  f"stat={stat:.1f}, p={pval:.6f}")
    except ImportError:
        pass

    # Save
    analysis = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mode": "paper",
        "n_runs": len(results),
        "difficulty_multipliers": DIFFICULTY_MULTIPLIER,
        "overall": {
            "ara_success_rate": round(ara_sr, 4),
            "baseline_success_rate": round(bas_sr, 4),
            "delta_flat": round(ara_sr - bas_sr, 4),
            "ara_difficulty_weighted_rate": round(ara_dw, 4),
            "baseline_difficulty_weighted_rate": round(bas_dw, 4),
            "delta_weighted": round(ara_dw - bas_dw, 4),
        },
        "all_results": results,
    }
    out_path = RESULTS_DIR / "paper_reproduction_analysis.json"
    out_path.write_text(json.dumps(analysis, indent=2))
    print(f"\nSaved to: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="Run a single reproduction task")
    p_run.add_argument("paper")
    p_run.add_argument("task_suffix", help="e.g. T1")
    p_run.add_argument("condition", choices=["ara", "baseline"])
    p_run.add_argument("--seed", type=int, default=0)
    p_run.add_argument("--docker", action="store_true",
                       help="Run bash commands inside a Docker container")

    p_batch = sub.add_parser("run-batch", help="Run batch from subtask manifest")
    p_batch.add_argument("--workers", type=int, default=3)
    p_batch.add_argument("--paper")
    p_batch.add_argument("--difficulty")
    p_batch.add_argument("--seed", type=int, default=0)
    p_batch.add_argument("--docker", action="store_true")

    p_judge = sub.add_parser("judge", help="Judge completed runs")
    p_judge.add_argument("--paper")

    sub.add_parser("analyze", help="Aggregate and analyze per-subtask results")

    # Paper-level commands
    p_rp = sub.add_parser("run-paper",
                          help="Run all subtasks for one paper (mega-task)")
    p_rp.add_argument("paper")
    p_rp.add_argument("condition", choices=["ara", "baseline"])
    p_rp.add_argument("--seed", type=int, default=0)
    p_rp.add_argument("--docker", action="store_true")
    p_rp.add_argument("--resume-from", type=int, default=None, dest="resume_from",
                       help="Resume from subtask N (skip 1..N-1)")

    p_rpb = sub.add_parser("run-paper-batch",
                           help="Batch run paper-level mega-tasks")
    p_rpb.add_argument("--workers", type=int, default=3)
    p_rpb.add_argument("--paper")
    p_rpb.add_argument("--seed", type=int, default=0)

    p_jp = sub.add_parser("judge-paper",
                          help="Judge paper-level mega-task runs")
    p_jp.add_argument("--paper")

    sub.add_parser("analyze-paper",
                   help="Aggregate paper-level results")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args.paper, args.task_suffix, args.condition,
                seed=args.seed, use_docker=args.docker)
    elif args.command == "run-batch":
        cmd_run_batch(args.workers, args.paper, args.difficulty,
                      seed=args.seed)
    elif args.command == "judge":
        cmd_judge(args.paper)
    elif args.command == "analyze":
        cmd_analyze()
    elif args.command == "run-paper":
        cmd_run_paper(args.paper, args.condition, seed=args.seed,
                      use_docker=args.docker,
                      resume_from=getattr(args, 'resume_from', None))
    elif args.command == "run-paper-batch":
        cmd_run_paper_batch(args.workers, args.paper, seed=args.seed)
    elif args.command == "judge-paper":
        cmd_judge_paper(args.paper)
    elif args.command == "analyze-paper":
        cmd_analyze_paper()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
