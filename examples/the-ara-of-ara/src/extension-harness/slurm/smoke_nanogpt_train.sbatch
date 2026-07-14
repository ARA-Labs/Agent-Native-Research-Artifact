#!/bin/bash
#SBATCH --job-name=ext_nanogpt_train_smoke
#SBATCH --output=slurm_logs/ext_nanogpt_train_smoke_%j.out
#SBATCH --error=slurm_logs/ext_nanogpt_train_smoke_%j.err
#SBATCH --time=01:30:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=26
#SBATCH --gres=gpu:2
#SBATCH --mem=200G

# Timing-probe smoke: run Tao's reference starter at 1/8 scale to pin down
# per-step wall-clock (compilation + 2 steps @ 256 prompts, best_of=8).
# Extrapolate: full_run_time ~= compile + 4 * (measured_per_step * 8)

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"

mkdir -p "$REPO_DIR/slurm_logs"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "GPUs: $(nvidia-smi -L)"

set -a; source "$REPO_DIR/code/.env"; set +a
export REPLICATE_API_TOKEN="${REPLICATE_API_TOKEN:?must be set}"
export PYTHONUNBUFFERED=1
export PATH="$VENV/bin:$PATH"

SMOKE_ROOT="$(mktemp -d -p "$SCRATCH_ROOT" nanogpt_train_smoke_XXXX)"
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
cd "$WD"

echo "[smoke] launching Tao starter in timing_probe mode..."
echo "[smoke] START timestamp=$(date +%s)"
t_start=$(date +%s)

RL_MODE=timing_probe python solution/rl_finetune.py 2>&1 | tee train.log

t_end=$(date +%s)
echo "[smoke] END   timestamp=$t_end"
echo "[smoke] total wall-clock: $((t_end - t_start))s"
echo "[smoke] --- per-step extrapolation ---"
grep -E "compilation took|step took|setup took" train.log || true

echo "[smoke] --- scoring the trained checkpoint at 32 prompts ---"
python score.py --model_path finetuned_model --max_prompts 32 --max_workers 8 2>&1 | tail -10

echo "[smoke] done"
