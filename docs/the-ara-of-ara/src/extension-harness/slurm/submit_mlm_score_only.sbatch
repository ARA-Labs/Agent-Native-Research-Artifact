#!/bin/bash
#SBATCH --job-name=ext_mlm_score
#SBATCH --output=slurm_logs/ext_mlm_score_%j.out
#SBATCH --error=slurm_logs/ext_mlm_score_%j.err
#SBATCH --time=00:45:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=13
#SBATCH --gres=gpu:1
#SBATCH --mem=100G

# Score-only sbatch for restricted_mlm. Runs local_score.py on a specified
# checkpoint inside an existing workdir. Optionally swaps a different
# checkpoint into basic_model.pt before scoring.
#
# Required env vars:
#   SCORE_WORKDIR  — workdir containing solution/, score.sh, local_score.py
# Optional env vars:
#   CHECKPOINT     — path (relative to SCORE_WORKDIR/solution/) to the
#                    checkpoint to score. Default: 'basic_model.pt' (no swap).
#                    e.g. CHECKPOINT=basic_model_ft3.pt
#   KEEP_SWAP      — if "1", leave basic_model.pt pointing to CHECKPOINT after
#                    scoring. Useful before a resume run. Default: restore.

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"

if [ -z "${SCORE_WORKDIR:-}" ]; then
  echo "ERROR: SCORE_WORKDIR env var required" >&2; exit 2
fi
if [ ! -f "$SCORE_WORKDIR/score.sh" ] || [ ! -f "$SCORE_WORKDIR/local_score.py" ]; then
  echo "ERROR: $SCORE_WORKDIR missing score.sh or local_score.py" >&2; exit 2
fi

CHECKPOINT="${CHECKPOINT:-basic_model.pt}"
KEEP_SWAP="${KEEP_SWAP:-0}"

OUT_DIR="$(dirname "$SCORE_WORKDIR")/score_only_${CHECKPOINT%.pt}_job${SLURM_JOB_ID}"
mkdir -p "$REPO_DIR/slurm_logs" "$OUT_DIR"

cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Partition: $SLURM_JOB_PARTITION  GPU: $(nvidia-smi -L 2>/dev/null | head -1)"
echo "SCORE_WORKDIR: $SCORE_WORKDIR"
echo "CHECKPOINT:    $CHECKPOINT"
echo "KEEP_SWAP:     $KEEP_SWAP"
echo "OUT_DIR:       $OUT_DIR"

if [ ! -x "$VENV/bin/python" ]; then echo "ERROR: venv missing at $VENV" >&2; exit 1; fi
export PATH="$VENV/bin:$PATH"
export PYTHONUNBUFFERED=1

cd "$SCORE_WORKDIR"

# Snapshot current state for safe restore
ORIG_SHA=""
if [ -f solution/basic_model.pt ]; then
  ORIG_SHA=$(stat -c '%s_%Y' solution/basic_model.pt)
fi
echo "[score-only] basic_model.pt orig stat: $ORIG_SHA"

# Optional checkpoint swap
if [ "$CHECKPOINT" != "basic_model.pt" ]; then
  CKPT_PATH="solution/$CHECKPOINT"
  if [ ! -f "$CKPT_PATH" ]; then
    echo "ERROR: $CKPT_PATH not found in workdir" >&2; exit 2
  fi
  echo "[score-only] backing up basic_model.pt -> /tmp/basic_model_pre_swap.pt"
  cp solution/basic_model.pt /tmp/basic_model_pre_swap.pt
  echo "[score-only] swapping in $CHECKPOINT (size: $(du -h "$CKPT_PATH" | cut -f1))"
  cp "$CKPT_PATH" solution/basic_model.pt
  SWAPPED=1
else
  SWAPPED=0
fi

restore_basic_model() {
  if [ "$SWAPPED" = "1" ] && [ "$KEEP_SWAP" != "1" ]; then
    echo "[score-only] restoring basic_model.pt from /tmp/basic_model_pre_swap.pt"
    cp /tmp/basic_model_pre_swap.pt solution/basic_model.pt
    rm -f /tmp/basic_model_pre_swap.pt
  elif [ "$SWAPPED" = "1" ] && [ "$KEEP_SWAP" = "1" ]; then
    echo "[score-only] KEEP_SWAP=1: leaving basic_model.pt as $CHECKPOINT"
    rm -f /tmp/basic_model_pre_swap.pt
  fi
}
trap restore_basic_model EXIT

echo ""
echo "[score-only] running bash score.sh ..."
RUN_LOG="$OUT_DIR/score_run.log"
( bash score.sh ) 2>&1 | tee "$RUN_LOG"

# Extract canonical JSON output
LAST_JSON=$(grep -oE '\{"score":[^}]*"compliant":[^}]*\}' "$RUN_LOG" | tail -1 || true)
if [ -n "$LAST_JSON" ]; then
  printf '{"result": %s, "checkpoint": "%s"}\n' "$LAST_JSON" "$CHECKPOINT" > "$OUT_DIR/final_score.json"
  echo ""
  echo "[score-only] FINAL: $(cat "$OUT_DIR/final_score.json")"
else
  echo "WARN: could not extract canonical score JSON; check $RUN_LOG" >&2
fi

echo "[done] artifacts in $OUT_DIR"
