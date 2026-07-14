#!/bin/bash
#SBATCH --job-name=ext_nanogpt_smoke
#SBATCH --output=slurm_logs/ext_nanogpt_smoke_%j.out
#SBATCH --error=slurm_logs/ext_nanogpt_smoke_%j.err
#SBATCH --time=00:30:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G

# Smoke-test nanogpt_chat_rl score.py end-to-end on the baseline model.
# - Builds a workdir via harness.setup_workdir.
# - Runs `bash score.sh` with --max_prompts 8 to cap Replicate spend (~16 judge calls).
# - Expects score ~0.54 (baseline) but anything with a numeric score passes.

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"

mkdir -p "$REPO_DIR/slurm_logs"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "GPU: $(nvidia-smi -L | head -1)"

set -a; source "$REPO_DIR/code/.env"; set +a
export REPLICATE_API_TOKEN="${REPLICATE_API_TOKEN:?must be set}"
export PYTHONUNBUFFERED=1
export PATH="$VENV/bin:$PATH"

SMOKE_ROOT="$(mktemp -d -p "$SCRATCH_ROOT" nanogpt_smoke_XXXX)"
trap 'rm -rf "$SMOKE_ROOT"' EXIT
echo "[smoke] workdir root: $SMOKE_ROOT"

"$VENV/bin/python" - <<PYEOF
import pathlib, sys
sys.path.insert(0, "$REPO_DIR/code/extension-harness")
import harness
spec = harness.TASKS["nanogpt_chat_rl"]
wd = harness.setup_workdir(spec, arm="paper", run_root=pathlib.Path("$SMOKE_ROOT"), run_id="smoke")
print(f"[smoke] workdir: {wd}")
PYEOF

WD="$SMOKE_ROOT/smoke/workdir"
echo "[smoke] running score.py with --max_prompts 8 (baseline gpt2-xl)..."
cd "$WD"
# Override max_prompts for the smoke run.
export REPLICATE_API_TOKEN="${REPLICATE_API_TOKEN}"
python score.py --model_path finetuned_model --max_prompts 8 --max_workers 4 2>&1 | tail -30

echo "[smoke] done"
