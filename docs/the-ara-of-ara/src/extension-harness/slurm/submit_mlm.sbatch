#!/bin/bash
#SBATCH --job-name=ext_mlm
#SBATCH --output=slurm_logs/ext_mlm_%j.out
#SBATCH --error=slurm_logs/ext_mlm_%j.err
#SBATCH --time=08:00:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=26
#SBATCH --gres=gpu:2
#SBATCH --mem=200G

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
RUN_ROOT="$SCRATCH_ROOT/extension-runs"
VENV="$SCRATCH_ROOT/venvs/extension-harness"

TASK="${TASK:-restricted_mlm}"
ARM="${ARM:-paper}"
SEED="${SEED:-0}"
MAX_TURNS="${MAX_TURNS:-2000}"
MAX_BUDGET_USD="${MAX_BUDGET_USD:-50}"
MODEL="${MODEL:-claude-sonnet-4-5}"
SKIP_BASELINE="${SKIP_BASELINE:-0}"

mkdir -p "$REPO_DIR/slurm_logs" "$RUN_ROOT"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Partition: $SLURM_JOB_PARTITION  GPUs: $(nvidia-smi -L)"
echo "Run config: TASK=$TASK ARM=$ARM SEED=$SEED MAX_TURNS=$MAX_TURNS MAX_BUDGET_USD=$MAX_BUDGET_USD MODEL=$MODEL"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv at $VENV"
  uv venv "$VENV" --python 3.12.13
fi

"$VENV/bin/python" - <<'PYEOF'
import importlib, subprocess, sys
need = []
for pkg, mod in [("claude-agent-sdk", "claude_agent_sdk"),
                 ("torch", "torch"),
                 ("numpy<2.0", "numpy"),
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

if ! command -v claude >/dev/null 2>&1; then
  echo "[setup] installing claude CLI via npm (one-time)"
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm required to install claude CLI; load a node module first" >&2
    exit 1
  fi
  npm install -g @anthropic-ai/claude-code
fi

# Verify shared OWT + starter checkpoint are in place before we burn API budget.
DATA_ROOT="$SCRATCH_ROOT/shared-data/openwebtext"
CKPT_ROOT="$SCRATCH_ROOT/shared-data/restricted_mlm"
for f in train.bin val.bin unigrams.pt bigrams_forward.pt bigrams_backward.pt; do
  [ -f "$DATA_ROOT/$f" ] || { echo "ERROR: missing $DATA_ROOT/$f  (run setup_mlm_data + setup_mlm_pretrain first)" >&2; exit 2; }
done
[ -f "$CKPT_ROOT/basic_model.pt" ] || { echo "ERROR: missing $CKPT_ROOT/basic_model.pt  (run setup_mlm_pretrain)" >&2; exit 2; }

if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -f "$REPO_DIR/code/.env" ]; then
  set -a; source "$REPO_DIR/code/.env"; set +a
fi
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:?must be set}"
export PYTHONUNBUFFERED=1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
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
