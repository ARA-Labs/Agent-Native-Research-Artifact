"""Level 3 Execution Reproducibility: spawns Claude Code sub-agents to reproduce claims.

Primary path: invoke `claude` CLI as a subprocess (Agent-First Development).
Fallback: direct Anthropic API agentic loop (for environments without Claude CLI).

IMPORTANT — Sandboxing:
  The execution sub-agent is deliberately isolated from the ARA's evidence/ layer
  and logic/experiments.md (which contain the paper's ground-truth results).
  Only the code kernel (src/execution/*.py) and algorithm descriptions
  (logic/solution/algorithm.md) are copied into the agent's working directory.
  This prevents the agent from reading expected numbers and fabricating results.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import anthropic


DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TURNS = 15
MAX_TOKENS = 16_384
TOKEN_BUDGET = 300_000
EXEC_TIMEOUT = 60  # seconds per shell command

# Paths the execution agent is allowed to see (relative to ARA root).
# Everything else (evidence/, logic/experiments.md, PAPER.md, …) is hidden.
_ALLOWED_CODE_GLOBS = ["src/execution/*.py"]
_ALLOWED_DOCS = ["logic/solution/algorithm.md"]


# ── Work-dir preparation ────────────────────────────────────────────────────

def _prepare_work_dir(ara_dir: Path, claim_id: str) -> Path:
    """Create a sandboxed working directory with ONLY the code kernel.

    Copies:
      - src/execution/*.py  → work_dir/*.py  (importable code kernel)
      - logic/solution/algorithm.md → work_dir/algorithm.md (algorithm reference)

    Does NOT copy:
      - evidence/ (ground-truth results from the paper)
      - logic/experiments.md (expected experimental outcomes)
      - PAPER.md (full paper summary with numbers)
      - Any other ARA metadata
    """
    work_dir = Path(tempfile.mkdtemp(prefix=f"ara_l3_{claim_id}_"))

    # Copy code kernel
    src_exec = ara_dir / "src" / "execution"
    if src_exec.is_dir():
        for py_file in src_exec.glob("*.py"):
            shutil.copy2(py_file, work_dir / py_file.name)

    # Copy algorithm description (pseudocode for implementing baselines)
    algo_md = ara_dir / "logic" / "solution" / "algorithm.md"
    if algo_md.is_file():
        shutil.copy2(algo_md, work_dir / "algorithm.md")

    return work_dir


# ── Shared prompt builder ────────────────────────────────────────────────────

def _build_reproduction_prompt(
    work_dir: Path,
    test_case: dict,
) -> str:
    """Build the prompt for a reproduction sub-agent.

    NOTE: The prompt deliberately does NOT include any path to the ARA artifact.
    The agent can only see files in work_dir (code kernel + algorithm reference).
    This prevents it from reading evidence/ tables or experiments.md which
    contain the paper's ground-truth numbers.
    """
    return f"""You are a research reproduction agent. Your task is to reproduce a specific claim
from a research paper using the provided code kernel.

# Claim to Reproduce
**Claim ID**: {test_case['claim_id']}
**Claim**: {test_case.get('claim', '')}

# Experiment Plan
**Setup**: {test_case.get('setup', 'Create appropriate synthetic data.')}
**Procedure**: {test_case.get('procedure', 'Design a minimal test.')}
**Expected Results**: {test_case.get('expected_results', 'Not specified.')}
**Success Criteria**: {test_case.get('success_criteria', 'Directional agreement.')}
**Code Hints**: {test_case.get('code_hints', 'Read the code kernel to understand the API.')}

# File Locations
- Working directory: {work_dir}
- Code kernel `.py` files are in {work_dir} — you can import from them directly.
- `algorithm.md` in {work_dir} describes the algorithms (useful for implementing baselines).

# Instructions

1. Read the code kernel `.py` files in `{work_dir}` to understand the available functions.
2. Write a test script (`{work_dir}/test.py`) that:
   - Creates synthetic data matching the experiment setup
   - Imports and runs the core algorithm from the code kernel
   - Implements simple baselines for comparison
   - Prints numerical results and directional checks
3. Run: `python3 {work_dir}/test.py`
4. If there are errors, fix and re-run.

# Constraints
- Python standard library + numpy only. No pip installs.
- Keep simulations small-scale (run in < 60 seconds).
- Verify DIRECTIONAL properties only (rankings, orderings, trends).
  Absolute magnitudes WILL differ because you use synthetic data — this is expected.
- If the code kernel needs minor fixes to run standalone, fix them.
- You MUST work ONLY within the working directory. Do NOT attempt to read files
  outside of {work_dir}. The code kernel is already there — no need to look elsewhere.

# Output
When done, output EXACTLY one JSON object (no other text) with this structure:
```json
{{"reproduced": true, "results": {{"metric_name": value}}, "notes": "Brief explanation of what was observed."}}
```
Set `reproduced` to `true` if directional properties match the claim, `false` otherwise.
"""


# ── Primary path: Claude CLI sub-agent ───────────────────────────────────────

def _claude_cli_available() -> bool:
    """Check if the claude CLI is available."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _execute_via_subagent(
    ara_dir: Path,
    test_case: dict,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Spawn a Claude Code sub-agent to reproduce a test case.

    Uses the `claude` CLI in print mode with --output-format json.
    The sub-agent is sandboxed: it can only see files in work_dir
    (code kernel + algorithm.md). It has NO access to the ARA's
    evidence/ layer or any ground-truth results.
    """
    claim_id = test_case["claim_id"]

    # Create sandboxed working directory (code kernel only, no evidence)
    work_dir = _prepare_work_dir(ara_dir, claim_id)

    prompt = _build_reproduction_prompt(work_dir, test_case)

    print(f"  [L3] Spawning sub-agent for {claim_id}...")
    # Remove CLAUDECODE env var to allow nested Claude Code sessions
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--output-format", "json",
                "--model", model,
                "--max-turns", str(MAX_TURNS),
                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min overall timeout
            cwd=str(work_dir),
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "reproduced": False,
            "results": {},
            "notes": "Sub-agent timed out after 600s.",
            "turns": 0,
            "tokens": {"input": 0, "output": 0},
            "work_dir": str(work_dir),
        }

    # Parse the sub-agent output
    output_text = result.stdout.strip()
    tokens = {"input": 0, "output": 0}

    # Try to extract JSON from the output
    try:
        # The output-format json wraps everything in a JSON envelope
        envelope = json.loads(output_text)
        # Extract the actual text content from the envelope
        if isinstance(envelope, dict):
            # Claude CLI json output has "result" or "content" field
            text_content = envelope.get("result", envelope.get("content", output_text))
            if isinstance(text_content, list):
                text_content = " ".join(
                    block.get("text", "") for block in text_content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            tokens = {
                "input": envelope.get("input_tokens", 0),
                "output": envelope.get("output_tokens", 0),
            }
        else:
            text_content = output_text
    except json.JSONDecodeError:
        text_content = output_text

    # Extract the reproduction result JSON from the text
    parsed = _extract_json_result(str(text_content))

    return {
        "reproduced": parsed.get("reproduced", False),
        "results": parsed.get("results", {}),
        "notes": parsed.get("notes", text_content[:500] if text_content else "No output"),
        "turns": 0,  # not tracked in CLI mode
        "tokens": tokens,
        "work_dir": str(work_dir),
    }


def _extract_json_result(text: str) -> dict:
    """Extract a JSON object from agent output text."""
    import re

    # Try to find ```json ... ``` block
    match = re.search(r'```json\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find a bare JSON object
    for i, ch in enumerate(text):
        if ch == '{':
            depth = 0
            for j in range(i, len(text)):
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[i:j + 1])
                        except json.JSONDecodeError:
                            break

    return {"reproduced": False, "results": {}, "notes": f"Could not parse result from output"}


# ── Fallback path: direct Anthropic API agentic loop ─────────────────────────

FALLBACK_SYSTEM_TEMPLATE = r"""You are a research reproduction agent. Your task is to reproduce a specific claim from a research paper using the provided code kernel.

# Claim to Reproduce
{claim}

# Experiment Plan
**Setup**: {setup}

**Procedure**: {procedure}

**Expected Results**: {expected_results}

# Success Criteria
{success_criteria}

# Code Hints
{code_hints}

# Instructions

1. Read the code kernel `.py` files using `read_file` to understand the available functions.
2. Optionally read `algorithm.md` for algorithm pseudocode (useful for implementing baselines).
3. Write a test script (`test.py`) using `write_code` that:
   - Creates synthetic data matching the experiment setup description
   - Imports and runs the core algorithm from the code kernel
   - Implements simple baselines for comparison
   - Prints numerical results and directional checks
4. Run your script with `execute`: `python3 test.py`
   - The `execute` tool ALWAYS runs in your working directory. Do NOT use `cd` or absolute paths.
5. If there are errors, fix and re-run. But do NOT rewrite just to improve magnitudes.
6. Call `submit_results` with your findings. Include actual numbers in `results`.

# Constraints
- Python standard library + numpy only. No pip installs.
- Keep simulations small-scale (run in < 60 seconds).
- You do NOT need exact numbers — verify DIRECTIONAL properties only.
  (e.g., "algorithm A outperforms baseline B", "metric increases with parameter X")
- If the code kernel needs minor fixes to run standalone, fix them.
- You can ONLY read files in your working directory. Do NOT attempt to access
  any paths outside of it.

# CRITICAL: When to Submit
- Once your test runs and produces numerical results, check the DIRECTIONAL properties
  defined in the success criteria above.
- If the ordering/ranking/trend matches the claim, SUBMIT IMMEDIATELY with reproduced=true.
  Do NOT try to improve absolute magnitudes — they WILL differ from the paper because
  you use synthetic data. This is expected and acceptable.
- If you have run your test successfully, submit. Do NOT keep rewriting the simulation.
- If directional properties clearly contradict the claim, submit with reproduced=false.
- If you cannot get the code to run at all, submit with reproduced=false and explain why.
- You MUST submit within your turn budget. Always prefer submitting partial results
  over running out of budget with nothing submitted.
"""

FALLBACK_TOOLS = [
    {
        "name": "read_file",
        "description": (
            "Read a file from the working directory. "
            "Use to read code kernel .py files or algorithm.md."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Filename in the working directory (e.g., 'scheduler.py', 'algorithm.md')",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in the working directory.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "write_code",
        "description": "Write a file to the working directory for execution.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path in working directory (e.g., 'test.py')",
                },
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "execute",
        "description": f"Run a shell command in the working directory. Timeout: {EXEC_TIMEOUT}s.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "submit_results",
        "description": "Submit your reproduction results. Call this when you are done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reproduced": {
                    "type": "boolean",
                    "description": "Whether the directional claim was reproduced",
                },
                "results": {
                    "type": "object",
                    "description": "Key numerical results from your test",
                },
                "notes": {
                    "type": "string",
                    "description": "What you observed and how it relates to the claim",
                },
            },
            "required": ["reproduced", "results", "notes"],
        },
    },
]


class _FallbackToolExecutor:
    """Execute tools for the fallback API-based agentic loop.

    SANDBOXED: All file operations are restricted to work_dir.
    The agent has NO access to the ARA artifact's evidence/ layer,
    logic/experiments.md, or any ground-truth results.
    """

    def __init__(self, work_dir: Path):
        self.work_dir = work_dir.resolve()
        self.submitted_results = None

    def execute(self, tool_name: str, tool_input: dict) -> str:
        try:
            match tool_name:
                case "read_file":
                    return self._read_file(tool_input["path"])
                case "list_files":
                    return self._list_files()
                case "write_code":
                    return self._write_code(tool_input["path"], tool_input["content"])
                case "execute":
                    return self._execute(tool_input["command"])
                case "submit_results":
                    return self._submit_results(tool_input)
                case _:
                    return f"Error: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

    def _read_file(self, path: str) -> str:
        """Read a file — restricted to work_dir only."""
        path = path.strip().lstrip("/")
        if ".." in path:
            return "Error: Invalid path"
        target = (self.work_dir / path).resolve()
        # Enforce sandbox: must be inside work_dir
        if not str(target).startswith(str(self.work_dir)):
            return "Error: Access denied — can only read files in the working directory."
        if not target.is_file():
            return f"Error: File not found: {path}"
        content = target.read_text()
        if len(content) > 32_000:
            return content[:32_000] + f"\n... (truncated, {len(content)} total)"
        return content

    def _list_files(self) -> str:
        """List files in work_dir only."""
        lines = []
        for entry in sorted(self.work_dir.iterdir()):
            if entry.name.startswith("_"):
                continue
            if entry.is_dir():
                lines.append(f"  {entry.name}/")
            else:
                lines.append(f"  {entry.name} ({entry.stat().st_size} bytes)")
        return "\n".join(lines) if lines else "(empty)"

    def _write_code(self, path: str, content: str) -> str:
        path = path.strip().lstrip("/")
        if ".." in path:
            return "Error: Invalid path"
        target = (self.work_dir / path).resolve()
        if not str(target).startswith(str(self.work_dir)):
            return "Error: Access denied — can only write to the working directory."
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return f"OK: Wrote {len(content)} chars to {path}"

    def _execute(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.work_dir),
                capture_output=True,
                text=True,
                timeout=EXEC_TIMEOUT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            if len(output) > 16_000:
                output = output[:16_000] + "\n... (truncated)"
            return output if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {EXEC_TIMEOUT}s"

    def _submit_results(self, input_data: dict) -> str:
        self.submitted_results = {
            "reproduced": input_data.get("reproduced", False),
            "results": input_data.get("results", {}),
            "notes": input_data.get("notes", ""),
        }
        return "OK: Results submitted. You can stop now."


def _execute_via_api(
    ara_dir: Path,
    test_case: dict,
    model: str = DEFAULT_MODEL,
    max_turns: int = MAX_TURNS,
) -> dict:
    """Fallback: run a direct Anthropic API agentic loop.

    The agent is sandboxed to work_dir (code kernel only).
    No access to the ARA's evidence/ or ground-truth results.
    """
    claim_id = test_case["claim_id"]
    print(f"  [L3] API fallback for {claim_id}...")

    # Create sandboxed working directory (code kernel only, no evidence)
    work_dir = _prepare_work_dir(ara_dir, claim_id)

    system_prompt = FALLBACK_SYSTEM_TEMPLATE.format(
        claim=test_case.get("claim", ""),
        setup=test_case.get("setup", "Not specified — create synthetic data."),
        procedure=test_case.get("procedure", "Not specified — design a minimal test."),
        expected_results=test_case.get("expected_results", "Not specified."),
        success_criteria=test_case.get("success_criteria", "Directional agreement."),
        code_hints=test_case.get("code_hints", "Read the code kernel to understand the API."),
    )

    client = anthropic.Anthropic()
    executor = _FallbackToolExecutor(work_dir)

    messages = [{
        "role": "user",
        "content": (
            f"Reproduce claim {claim_id}. "
            f"Start by listing files, then read the code kernel."
        ),
    }]

    total_input = 0
    total_output = 0
    turn = 0

    for turn in range(1, max_turns + 1):
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=FALLBACK_TOOLS,
            messages=messages,
            temperature=0,
        )

        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"    [{claim_id}] {block.text.strip()[:100]}")
            elif block.type == "tool_use":
                if block.name == "execute":
                    print(f"    [{claim_id}] -> execute({block.input['command'][:80]})")
                elif block.name == "submit_results":
                    print(f"    [{claim_id}] -> submit_results(reproduced={block.input.get('reproduced')})")
                else:
                    args = json.dumps(block.input, ensure_ascii=False)
                    if len(args) > 80:
                        args = args[:80] + "..."
                    print(f"    [{claim_id}] -> {block.name}({args})")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = executor.execute(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if executor.submitted_results is not None:
            break

        if total_input + total_output > TOKEN_BUDGET:
            print(f"    [{claim_id}] Token budget exceeded. Stopping.")
            break

    result = executor.submitted_results or {
        "reproduced": False,
        "results": {},
        "notes": "Agent did not submit results (ran out of turns or budget).",
    }
    result["turns"] = turn
    result["tokens"] = {"input": total_input, "output": total_output}
    result["work_dir"] = str(work_dir)

    status = "REPRODUCED" if result["reproduced"] else "NOT REPRODUCED"
    print(f"  [L3] {claim_id}: {status} ({turn} turns, {total_input + total_output:,} tokens)")

    return result


# ── Public API ───────────────────────────────────────────────────────────────

def execute_test_case(
    ara_dir: Path,
    test_case: dict,
    model: str = DEFAULT_MODEL,
    max_turns: int = MAX_TURNS,
) -> dict:
    """Spawn an agent to reproduce a single test case.

    Primary: uses `claude` CLI sub-agent (Agent-First Development).
    Fallback: direct Anthropic API agentic loop.

    Args:
        ara_dir: Path to the ARA artifact.
        test_case: Test case dict with claim, setup, procedure, expected_results.
        model: LLM model for the agent.
        max_turns: Maximum agent turns (used in fallback mode).

    Returns:
        dict with: reproduced (bool), results (dict), notes (str),
        turns (int), tokens (dict), work_dir (str)
    """
    claim_id = test_case["claim_id"]
    print(f"  [L3] Executing {claim_id}: {test_case.get('experiment', 'unknown')[:60]}...")

    if _claude_cli_available():
        return _execute_via_subagent(ara_dir, test_case, model=model)
    else:
        print(f"  [L3] claude CLI not found, using API fallback")
        return _execute_via_api(ara_dir, test_case, model=model, max_turns=max_turns)
