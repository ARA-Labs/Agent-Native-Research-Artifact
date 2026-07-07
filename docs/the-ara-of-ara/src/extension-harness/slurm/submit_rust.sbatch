#!/bin/bash
#SBATCH --job-name=ext_rust
#SBATCH --output=slurm_logs/ext_rust_%j.out
#SBATCH --error=slurm_logs/ext_rust_%j.err
#SBATCH --time=8:00:00
#SBATCH --partition=sapphire
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
RUN_ROOT="$SCRATCH_ROOT/extension-runs"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
RUST_TOOLS="$SCRATCH_ROOT/tools"

# CLI overrides via env vars
TASK="${TASK:-rust_codecontests}"
ARM="${ARM:-paper}"
SEED="${SEED:-0}"
MAX_TURNS="${MAX_TURNS:-2000}"
MAX_BUDGET_USD="${MAX_BUDGET_USD:-50}"
MODEL="${MODEL:-claude-sonnet-4-6}"
SKIP_BASELINE="${SKIP_BASELINE:-0}"

mkdir -p "$REPO_DIR/slurm_logs" "$RUN_ROOT"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Run config: TASK=$TASK ARM=$ARM SEED=$SEED MAX_TURNS=$MAX_TURNS MAX_BUDGET_USD=$MAX_BUDGET_USD MODEL=$MODEL"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv at $VENV"
  uv venv "$VENV" --python 3.12.13
fi

# Python deps for rust task (idempotent).
"$VENV/bin/python" - <<'PYEOF'
import importlib, subprocess, sys
need = []
for pkg, mod in [("claude-agent-sdk", "claude_agent_sdk"),
                 ("openai", "openai"),
                 ("anthropic", "anthropic"),
                 ("backoff", "backoff"),
                 ("tqdm", "tqdm"),
                 ("setuptools", "setuptools"),
                 ("wheel", "wheel")]:
    try:
        importlib.import_module(mod)
    except ImportError:
        need.append(pkg)
if need:
    subprocess.check_call(["uv", "pip", "install", "--python", sys.executable, *need])
PYEOF

# Claude Agent SDK requires the `claude` CLI binary on PATH
if ! command -v claude >/dev/null 2>&1; then
  echo "[setup] installing claude CLI via npm (one-time)"
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm required to install claude CLI; load a node module first" >&2
    exit 1
  fi
  npm install -g @anthropic-ai/claude-code
fi

# Rust toolchain is pre-installed at $SCRATCH_ROOT/tools via rustup.
export CARGO_HOME="$RUST_TOOLS/cargo"
export RUSTUP_HOME="$RUST_TOOLS/rustup"
export PATH="$CARGO_HOME/bin:$PATH"
if ! command -v rustc >/dev/null 2>&1; then
  echo "ERROR: rustc not on PATH. Install via rustup to $RUST_TOOLS." >&2
  exit 1
fi
echo "[setup] rustc: $(rustc --version)"

# Pull API keys from repo .env.
if [ -f "$REPO_DIR/code/.env" ]; then
  set -a; source "$REPO_DIR/code/.env"; set +a
fi
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:?must be set}"
export OPENAI_API_KEY="${OPENAI_API_KEY:?must be set for rust task}"
echo "[setup] OPENAI_API_KEY prefix=${OPENAI_API_KEY:0:10}... len=${#OPENAI_API_KEY}"
# Verify org/tier of the key actually being used by the job.
"$VENV/bin/python" - <<'PYEOF' || echo "[setup] WARNING: key probe failed"
import os, openai
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=0)
try:
    raw = client.with_raw_response.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role":"user","content":"ping"}],
        max_tokens=1,
    )
    h = raw.headers
    print(f"[setup] org={h.get('openai-organization')} rpm={h.get('x-ratelimit-limit-requests')} tpm={h.get('x-ratelimit-limit-tokens')} remaining_req={h.get('x-ratelimit-remaining-requests')}")
except Exception as e:
    print(f"[setup] key probe ERROR: {type(e).__name__}: {str(e)[:200]}")
PYEOF
export PYTHONUNBUFFERED=1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
# Put venv on PATH so the agent's `bash score.sh` picks up our Python/deps.
export PATH="$VENV/bin:$PATH"

RUN_ID="${TASK}_${ARM}_seed${SEED}_job${SLURM_JOB_ID}"
SKIP_FLAG=""
if [ "$SKIP_BASELINE" = "1" ]; then SKIP_FLAG="--skip-baseline"; fi

"$VENV/bin/python" code/extension-harness/harness.py \
    --task "$TASK" \
    --arm "$ARM" \
    --seed "$SEED" \
    --max-turns "$MAX_TURNS" \
    --max-budget-usd "$MAX_BUDGET_USD" \
    --model "$MODEL" \
    --run-root "$RUN_ROOT" \
    --run-id "$RUN_ID" \
    $SKIP_FLAG

echo "[done] artifacts in $RUN_ROOT/$RUN_ID"
