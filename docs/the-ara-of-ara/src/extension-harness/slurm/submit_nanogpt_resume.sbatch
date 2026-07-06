#!/bin/bash
#SBATCH --job-name=ext_nanogpt_resume
#SBATCH --output=slurm_logs/ext_nanogpt_%j.out
#SBATCH --error=slurm_logs/ext_nanogpt_%j.err
#SBATCH --time=08:00:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=26
#SBATCH --gres=gpu:2
#SBATCH --mem=200G

# Resume a nanogpt_chat_rl agent session from a prior run that ended
# prematurely. Modeled on submit_mlm_resume.sbatch.
#
# Required env vars:
#   RESUME_FROM  — prior run_id (e.g. nanogpt_chat_rl_paper_seed0_job7517443)
#   SESSION_ID   — SDK session_id from prior trace.jsonl (first system init event)

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
RUN_ROOT="$SCRATCH_ROOT/extension-runs"
VENV="$SCRATCH_ROOT/venvs/extension-harness"

TASK="${TASK:-nanogpt_chat_rl}"
ARM="${ARM:-paper}"
SEED="${SEED:-0}"
MAX_TURNS="${MAX_TURNS:-2000}"
MAX_BUDGET_USD="${MAX_BUDGET_USD:-14}"
MODEL="${MODEL:-claude-sonnet-4-6}"

if [ -z "${RESUME_FROM:-}" ] || [ -z "${SESSION_ID:-}" ]; then
  echo "ERROR: RESUME_FROM and SESSION_ID env vars required" >&2
  exit 2
fi
RESUME_WORKDIR="$RUN_ROOT/$RESUME_FROM/workdir"
if [ ! -f "$RESUME_WORKDIR/solution/rl_finetune.py" ]; then
  echo "ERROR: $RESUME_WORKDIR/solution/rl_finetune.py missing" >&2
  exit 2
fi

mkdir -p "$REPO_DIR/slurm_logs"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "GPUs: $(nvidia-smi -L)"
echo "RESUME workdir:    $RESUME_WORKDIR"
echo "RESUME session_id: $SESSION_ID"
echo "Config: TASK=$TASK ARM=$ARM SEED=$SEED MAX_TURNS=$MAX_TURNS MAX_BUDGET_USD=$MAX_BUDGET_USD MODEL=$MODEL"

if [ ! -x "$VENV/bin/python" ]; then echo "ERROR: venv missing at $VENV" >&2; exit 1; fi
if ! command -v claude >/dev/null 2>&1; then echo "ERROR: claude CLI not on PATH" >&2; exit 1; fi

if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -f "$REPO_DIR/code/.env" ]; then
  set -a; source "$REPO_DIR/code/.env"; set +a
fi
if [ -z "${REPLICATE_API_TOKEN:-}" ] && [ -f "$REPO_DIR/code/.env" ]; then
  set -a; source "$REPO_DIR/code/.env"; set +a
fi
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:?must be set}"
export REPLICATE_API_TOKEN="${REPLICATE_API_TOKEN:?must be set for nanogpt task}"
export PYTHONUNBUFFERED=1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
export PATH="$VENV/bin:$PATH"

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
