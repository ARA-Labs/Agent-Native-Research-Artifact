#!/bin/bash
#SBATCH --job-name=ext_rust_score
#SBATCH --output=slurm_logs/ext_rust_score_%j.out
#SBATCH --error=slurm_logs/ext_rust_score_%j.err
#SBATCH --time=03:00:00
#SBATCH --partition=sapphire
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G

# Score-only run: invokes local_score.py on an existing solution.py.
# No SDK agent. Use to recover an official score for a workdir whose
# original run TIMEOUT'd before the harness could write final_score.json.
#
# Required env vars:
#   SCORE_WORKDIR  — workdir containing score.sh + solution.py + data/
# Optional env vars:
#   SOLUTION_FILE  — alternate solution path (copied to workdir/solution.py)
#   OUT_DIR        — where to write final_score.json (default: $SCORE_WORKDIR/..)

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
RUST_TOOLS="$SCRATCH_ROOT/tools"

if [ -z "${SCORE_WORKDIR:-}" ]; then
  echo "ERROR: SCORE_WORKDIR env var required" >&2; exit 2
fi
if [ ! -f "$SCORE_WORKDIR/score.sh" ] || [ ! -f "$SCORE_WORKDIR/local_score.py" ]; then
  echo "ERROR: $SCORE_WORKDIR missing score.sh or local_score.py" >&2; exit 2
fi

OUT_DIR="${OUT_DIR:-$(dirname "$SCORE_WORKDIR")/score_only_job${SLURM_JOB_ID}}"
mkdir -p "$REPO_DIR/slurm_logs" "$OUT_DIR"

if [ -n "${SOLUTION_FILE:-}" ]; then
  if [ ! -f "$SOLUTION_FILE" ]; then
    echo "ERROR: SOLUTION_FILE=$SOLUTION_FILE not found" >&2; exit 2
  fi
  echo "Overwriting $SCORE_WORKDIR/solution.py from $SOLUTION_FILE"
  cp "$SOLUTION_FILE" "$SCORE_WORKDIR/solution.py"
fi

cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Partition: $SLURM_JOB_PARTITION"
echo "SCORE_WORKDIR: $SCORE_WORKDIR"
echo "OUT_DIR:       $OUT_DIR"
echo "solution.py:   $(wc -l < "$SCORE_WORKDIR/solution.py") lines"

if [ ! -x "$VENV/bin/python" ]; then echo "ERROR: venv missing at $VENV" >&2; exit 1; fi

# Rust toolchain (local_score.py drives rustc compilation)
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
export OPENAI_API_KEY="${OPENAI_API_KEY:?must be set for rust task}"
export PYTHONUNBUFFERED=1

cd "$SCORE_WORKDIR"
echo ""
echo "[score-only] running local_score.py on solution.py..."
python local_score.py \
    --module_path solution.py \
    --problems_file data/test.jsonl \
    --batch_size 20 \
    --max_workers 32 \
    --max_time_per_batch 600 \
    2>&1 | tee "$OUT_DIR/score_run.log"

# Extract the final JSON line (local_score.py prints `Score: X | N successes / 165` then `{"score": ...}`)
LAST_JSON=$(grep -oE '\{"score":[^}]*\}' "$OUT_DIR/score_run.log" | tail -1 || true)
if [ -n "$LAST_JSON" ]; then
  printf '{"result": %s}\n' "$LAST_JSON" > "$OUT_DIR/final_score.json"
  echo ""
  echo "[score-only] final: $(cat "$OUT_DIR/final_score.json")"
else
  echo "WARN: could not extract score JSON from run log" >&2
fi

echo "[done] artifacts in $OUT_DIR"
