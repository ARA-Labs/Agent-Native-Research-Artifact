#!/bin/bash
#SBATCH --job-name=ext_triton_baseline
#SBATCH --output=slurm_logs/ext_triton_baseline_%j.out
#SBATCH --error=slurm_logs/ext_triton_baseline_%j.err
#SBATCH --time=00:30:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=13
#SBATCH --gres=gpu:1
#SBATCH --mem=100G

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
RUN_ROOT="$SCRATCH_ROOT/extension-runs/baseline_smoke_${SLURM_JOB_ID}"
VENV="$SCRATCH_ROOT/venvs/extension-triton"

mkdir -p "$REPO_DIR/slurm_logs" "$RUN_ROOT"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
nvidia-smi -L

if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv at $VENV"
  uv venv "$VENV" --python 3.12.13
fi

# Triton 2.3.1 needs CUDA-compatible torch 2.3.1
uv pip install --python "$VENV/bin/python" --quiet "torch==2.3.1" "triton==2.3.1" "numpy<2.0" setuptools wheel

# Stage workdir with the official solution
cp code/artifacts/rebench-triton_cumsum-paper/src/tao_correct_solution.py "$RUN_ROOT/solution.py"
cp code/extension-harness/scoring/triton_cumsum/score.py "$RUN_ROOT/score.py"

echo "=== sanity import ==="
"$VENV/bin/python" -c "
import sys; sys.path.insert(0, '$RUN_ROOT')
import torch, triton
print('torch', torch.__version__, 'cuda', torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no-cuda')
print('triton', triton.__version__)
import solution
print('solution.prefix_sum =', solution.prefix_sum)
"

echo "=== running score (length 100M) ==="
cd "$RUN_ROOT"
"$VENV/bin/python" score.py --solution solution.py | tee result.json

echo "=== artifacts ==="
ls -la "$RUN_ROOT"
