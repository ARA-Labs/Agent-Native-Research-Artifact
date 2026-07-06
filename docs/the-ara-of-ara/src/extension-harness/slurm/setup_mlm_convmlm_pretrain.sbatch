#!/bin/bash
#SBATCH --job-name=setup_mlm_convmlm
#SBATCH --output=slurm_logs/setup_mlm_convmlm_%j.out
#SBATCH --error=slurm_logs/setup_mlm_convmlm_%j.err
#SBATCH --time=4:00:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=13
#SBATCH --gres=gpu:1
#SBATCH --mem=120G

# Pretrain Tao's ConvMLMWithBiBigrams starter on OpenWebText (100K steps,
# batch 16, bf16, ~3h on H100). Saves basic_model_convmlm.pt to
# shared-data/restricted_mlm/ without touching the current MLP starter.
# This is a reproduction probe: if the resulting checkpoint scores ~1.13 on
# local_score.py, we pivot the agent-facing starter back to ConvMLM.

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
DATA_ROOT="$SCRATCH_ROOT/shared-data/openwebtext"
CKPT_ROOT="$SCRATCH_ROOT/shared-data/restricted_mlm"
SCORING_SRC="$REPO_DIR/code/extension-harness/scoring/restricted_mlm"

NUM_STEPS="${NUM_STEPS:-100000}"

mkdir -p "$REPO_DIR/slurm_logs" "$CKPT_ROOT"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Partition: $SLURM_JOB_PARTITION  GPU: $(nvidia-smi -L | head -1)"
echo "NUM_STEPS=$NUM_STEPS"

for f in train.bin val.bin unigrams.pt bigrams_forward.pt bigrams_backward.pt; do
  [ -f "$DATA_ROOT/$f" ] || { echo "ERROR: missing $DATA_ROOT/$f" >&2; exit 2; }
done

if [ ! -x "$VENV/bin/python" ]; then
  echo "ERROR: venv missing at $VENV" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1

STAGE="$CKPT_ROOT/.convmlm_pretrain_stage"
rm -rf "$STAGE"
mkdir -p "$STAGE/data"
cp "$SCORING_SRC/pretrain_convmlm.py" "$STAGE/pretrain_convmlm.py"
for f in train.bin val.bin unigrams.pt bigrams_forward.pt bigrams_backward.pt; do
  ln -sf "$DATA_ROOT/$f" "$STAGE/data/$f"
done

cd "$STAGE"
echo "[pretrain] training ConvMLMWithBiBigrams for $NUM_STEPS steps"
NUM_STEPS="$NUM_STEPS" "$VENV/bin/python" pretrain_convmlm.py

if [ ! -f "$STAGE/basic_model_convmlm.pt" ]; then
  echo "ERROR: training finished but basic_model_convmlm.pt missing" >&2
  exit 3
fi

mv "$STAGE/basic_model_convmlm.pt" "$CKPT_ROOT/basic_model_convmlm.pt"
rm -rf "$STAGE"

echo "[done] checkpoint: $(ls -lh "$CKPT_ROOT/basic_model_convmlm.pt")"
