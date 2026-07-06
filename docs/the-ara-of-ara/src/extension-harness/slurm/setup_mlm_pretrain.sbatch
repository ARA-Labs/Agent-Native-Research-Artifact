#!/bin/bash
#SBATCH --job-name=setup_mlm_pretrain
#SBATCH --output=slurm_logs/setup_mlm_pretrain_%j.out
#SBATCH --error=slurm_logs/setup_mlm_pretrain_%j.err
#SBATCH --time=0:30:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=60G

# One-time pretrain of METR's basic-MLP starter:
#   train_starter.py for 500 steps -> basic_model.pt in
#   shared-data/restricted_mlm/ (symlinked from every run's workdir).
#
# Assumes setup_mlm_data.sbatch already produced train.bin + val.bin.

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
DATA_ROOT="$SCRATCH_ROOT/shared-data/openwebtext"
CKPT_ROOT="$SCRATCH_ROOT/shared-data/restricted_mlm"
SCORING_SRC="$REPO_DIR/code/extension-harness/scoring/restricted_mlm"

mkdir -p "$REPO_DIR/slurm_logs" "$CKPT_ROOT"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Partition: $SLURM_JOB_PARTITION  GPU: $(nvidia-smi -L | head -1)"

if [ ! -f "$DATA_ROOT/train.bin" ] || [ ! -f "$DATA_ROOT/val.bin" ]; then
  echo "ERROR: missing OWT bins at $DATA_ROOT -- run setup_mlm_data.sbatch first" >&2
  exit 2
fi

if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv at $VENV"
  uv venv "$VENV" --python 3.12.13
fi

"$VENV/bin/python" - <<'PYEOF'
import importlib, subprocess, sys
need = []
for pkg, mod in [("torch", "torch"), ("numpy<2.0", "numpy"), ("tqdm", "tqdm")]:
    try:
        importlib.import_module(mod)
    except ImportError:
        need.append(pkg)
if need:
    subprocess.check_call(["uv", "pip", "install", "--python", sys.executable, *need])
PYEOF

export PYTHONUNBUFFERED=1

# Step 1: bigram tables (writes into DATA_ROOT; all runs share them).
if [ -f "$DATA_ROOT/unigrams.pt" ] \
    && [ -f "$DATA_ROOT/bigrams_forward.pt" ] \
    && [ -f "$DATA_ROOT/bigrams_backward.pt" ]; then
  echo "[pretrain] bigram tables already present at $DATA_ROOT, skipping step 1"
else
  echo "[pretrain] step 1: measure bigrams -> $DATA_ROOT"
  "$VENV/bin/python" "$SCORING_SRC/measure_bigrams.py" \
      --data-dir "$DATA_ROOT" --out-dir "$DATA_ROOT"
fi

# Step 2: pretrain. Stage a workdir layout matching the runtime one so
# train_starter.py's relative ../data path resolves correctly.
STAGE="$CKPT_ROOT/.pretrain_stage"
rm -rf "$STAGE"
mkdir -p "$STAGE/solution" "$STAGE/data"
cp "$SCORING_SRC/model_starter.py"     "$STAGE/solution/model.py"
cp "$SCORING_SRC/train_starter.py"     "$STAGE/solution/train.py"
cp "$SCORING_SRC/torch_rule_enforcer.py" "$STAGE/torch_rule_enforcer.py"
for f in train.bin val.bin unigrams.pt bigrams_forward.pt bigrams_backward.pt; do
  ln -sf "$DATA_ROOT/$f" "$STAGE/data/$f"
done

cd "$STAGE/solution"
echo "[pretrain] step 2: training 100K steps (ConvMLMWithBiBigrams)"
"$VENV/bin/python" train.py

if [ ! -f "$STAGE/solution/basic_model.pt" ]; then
  echo "ERROR: training finished but basic_model.pt missing" >&2
  exit 3
fi

mv "$STAGE/solution/basic_model.pt" "$CKPT_ROOT/basic_model.pt"
rm -rf "$STAGE"

echo "[done] checkpoint: $(ls -lh "$CKPT_ROOT/basic_model.pt")"
