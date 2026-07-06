#!/bin/bash
#SBATCH --job-name=setup_mlm_data
#SBATCH --output=slurm_logs/setup_mlm_data_%j.out
#SBATCH --error=slurm_logs/setup_mlm_data_%j.err
#SBATCH --time=6:00:00
#SBATCH --partition=sapphire
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=26
#SBATCH --mem=200G

# One-time tokenization of OpenWebText -> train.bin/val.bin shared across
# every restricted_mlm run. CPU-only. Downloads & caches OWT via HF.

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
DATA_ROOT="$SCRATCH_ROOT/shared-data/openwebtext"
HF_CACHE="$SCRATCH_ROOT/hf_cache"

mkdir -p "$REPO_DIR/slurm_logs" "$DATA_ROOT" "$HF_CACHE"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "DATA_ROOT=$DATA_ROOT"
echo "HF_CACHE=$HF_CACHE"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv at $VENV"
  uv venv "$VENV" --python 3.12.13
fi

"$VENV/bin/python" - <<'PYEOF'
import importlib, subprocess, sys
need = []
for pkg, mod in [("datasets", "datasets"),
                 ("tiktoken", "tiktoken"),
                 ("numpy<2.0", "numpy"),
                 ("tqdm", "tqdm")]:
    try:
        importlib.import_module(mod)
    except ImportError:
        need.append(pkg)
if need:
    subprocess.check_call(["uv", "pip", "install", "--python", sys.executable, *need])
PYEOF

if [ -f "$REPO_DIR/code/.env" ]; then
  set -a; source "$REPO_DIR/code/.env"; set +a
fi

export HF_HOME="$HF_CACHE"
export HF_HUB_CACHE="$HF_CACHE"
export TRANSFORMERS_CACHE="$HF_CACHE"
export PYTHONUNBUFFERED=1

# Stage prepare_data.py into DATA_ROOT so it writes train.bin/val.bin there
# (the script is CWD-relative: data_dir = "data", which we create as a local
# symlink to DATA_ROOT itself).
STAGE="$DATA_ROOT/.staging"
mkdir -p "$STAGE"
cp "$REPO_DIR/code/extension-harness/scoring/restricted_mlm/prepare_data.py" "$STAGE/prepare_data.py"
cd "$STAGE"
rm -rf data
ln -s "$DATA_ROOT" data

"$VENV/bin/python" prepare_data.py

echo "[done] wrote:"
ls -lh "$DATA_ROOT/"{train.bin,val.bin}
rm -rf "$STAGE"
