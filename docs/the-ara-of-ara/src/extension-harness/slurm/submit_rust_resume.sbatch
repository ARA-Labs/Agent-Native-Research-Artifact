#!/bin/bash
#SBATCH --job-name=ext_rust_resume
#SBATCH --output=slurm_logs/ext_rust_%j.out
#SBATCH --error=slurm_logs/ext_rust_%j.err
#SBATCH --time=08:00:00
#SBATCH --partition=sapphire
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=200G

# Resume a rust_codecontests agent session from a prior run that ended
# prematurely (pushback ceiling hit, SDK crash, etc).
#
# Required env vars:
#   RESUME_FROM  — prior run_id (e.g. rust_codecontests_ara_seed0_job7600566)
#   SESSION_ID   — SDK session_id from prior trace.jsonl (first system init event)
# Optional:
#   ARM / SEED / MAX_TURNS / MAX_BUDGET_USD / MODEL

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
RUN_ROOT="$SCRATCH_ROOT/extension-runs"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
RUST_TOOLS="$SCRATCH_ROOT/tools"

TASK="${TASK:-rust_codecontests}"
ARM="${ARM:-ara}"
SEED="${SEED:-0}"
MAX_TURNS="${MAX_TURNS:-2000}"
MAX_BUDGET_USD="${MAX_BUDGET_USD:-25}"
MODEL="${MODEL:-claude-sonnet-4-6}"

if [ -z "${RESUME_FROM:-}" ] || [ -z "${SESSION_ID:-}" ]; then
  echo "ERROR: RESUME_FROM and SESSION_ID env vars required" >&2
  exit 2
fi

RESUME_WORKDIR="$RUN_ROOT/$RESUME_FROM/workdir"
if [ ! -f "$RESUME_WORKDIR/solution.py" ]; then
  echo "ERROR: $RESUME_WORKDIR/solution.py missing" >&2
  exit 2
fi

mkdir -p "$REPO_DIR/slurm_logs"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Partition: $SLURM_JOB_PARTITION"
echo "RESUME workdir:    $RESUME_WORKDIR"
echo "RESUME session_id: $SESSION_ID"
echo "Config: TASK=$TASK ARM=$ARM SEED=$SEED MAX_TURNS=$MAX_TURNS MAX_BUDGET_USD=$MAX_BUDGET_USD MODEL=$MODEL"

if [ ! -x "$VENV/bin/python" ]; then echo "ERROR: venv missing at $VENV" >&2; exit 1; fi
if ! command -v claude >/dev/null 2>&1; then echo "ERROR: claude CLI not on PATH" >&2; exit 1; fi

# Rust toolchain
export CARGO_HOME="$RUST_TOOLS/cargo"
export RUSTUP_HOME="$RUST_TOOLS/rustup"
export PATH="$CARGO_HOME/bin:$VENV/bin:$PATH"
if ! command -v rustc >/dev/null 2>&1; then
  echo "ERROR: rustc not on PATH" >&2; exit 1
fi
echo "rustc: $(rustc --version)"

if [ -f "$REPO_DIR/code/.env" ]; then
  set -a; source "$REPO_DIR/code/.env"; set +a
fi
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:?must be set}"
export OPENAI_API_KEY="${OPENAI_API_KEY:?must be set for rust task}"
export PYTHONUNBUFFERED=1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000

RUN_ID="${TASK}_${ARM}_seed${SEED}_resume_job${SLURM_JOB_ID}"

"$VENV/bin/python" code/extension-harness/harness.py \
    --task "$TASK" \
    --arm "$ARM" \
    --seed "$SEED" \
    --max-turns "$MAX_TURNS" \
    --max-budget-usd "$MAX_BUDGET_USD" \
    --model "$MODEL" \
    --run-root "$RUN_ROOT" \
    --run-id "$RUN_ID" \
    --resume-workdir "$RESUME_WORKDIR" \
    --resume-session-id "$SESSION_ID"

echo "[done] artifacts in $RUN_ROOT/$RUN_ID"
