#!/bin/bash
#SBATCH --job-name=nanogpt_rl_stress
#SBATCH --output=slurm_logs/nanogpt_rl_stress_%j.out
#SBATCH --error=slurm_logs/nanogpt_rl_stress_%j.err
#SBATCH --time=01:00:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=13
#SBATCH --gres=gpu:1
#SBATCH --mem=80G

# Stress-test the nanogpt_chat_rl scoring Replicate dependency by running
# TWO scorers concurrently on the same GPU. Each issues ~1024 Llama-3-8b
# judge calls at max_workers=20, so the combined in-flight count is up to
# ~40. That's right at the documented Replicate burst limit of 50 for low
# credit accounts -- if we blow it, we should see 429s / None responses
# surface in the logs.

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
SCORING_DIR="$REPO_DIR/code/extension-harness/scoring/nanogpt_chat_rl"
DATA_ROOT="$SCRATCH_ROOT/shared-data/nanogpt_chat_rl"
STRESS_ROOT="$SCRATCH_ROOT/extension-runs/nanogpt_rl_stress_job${SLURM_JOB_ID}"

mkdir -p "$STRESS_ROOT" "$REPO_DIR/slurm_logs"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "GPU: $(nvidia-smi -L | head -1)"
echo "Stress root: $STRESS_ROOT"

if [ -z "${REPLICATE_API_TOKEN:-}" ] && [ -f "$REPO_DIR/code/.env" ]; then
  set -a; source "$REPO_DIR/code/.env"; set +a
fi
export REPLICATE_API_TOKEN="${REPLICATE_API_TOKEN:?must be set}"
export PYTHONUNBUFFERED=1
export PATH="$VENV/bin:$PATH"

# Ensure replicate is installed (harness venv already has torch/tiktoken/tqdm)
"$VENV/bin/python" -c "import replicate" 2>/dev/null || \
  "$VENV/bin/uv" pip install --python "$VENV/bin/python" "replicate~=0.32.1" "transformers~=4.44.2" "tiktoken~=0.7.0"

# Stage two independent workdirs that mirror what harness setup_workdir
# produces for nanogpt_chat_rl: score.py + evaluation.py + solution/ +
# finetuned_model (copy of gpt2xl_base.pt).
stage_workdir() {
  local dir="$1"
  mkdir -p "$dir/solution"
  cp "$SCORING_DIR/score.py"         "$dir/score.py"
  cp "$SCORING_DIR/evaluation.py"    "$dir/evaluation.py"
  cp "$SCORING_DIR/model.py"         "$dir/solution/model.py"
  cp "$SCORING_DIR/padding_text.txt" "$dir/solution/padding_text.txt"
  # Copy-not-symlink so two scorers can't race on the same inode if either
  # decides to re-save. Scorer only reads it, but belt-and-suspenders.
  cp "$DATA_ROOT/gpt2xl_base.pt"     "$dir/finetuned_model"
}

W1="$STRESS_ROOT/w1"
W2="$STRESS_ROOT/w2"
stage_workdir "$W1"
stage_workdir "$W2"

# Run two scorers concurrently. Each hits Replicate ~1024 times via
# asyncio.Semaphore(20). Surface all stderr to per-worker log files AND
# to the slurm out file so we can see rate-limit exceptions live.
(
  cd "$W1"
  echo "[$(date +%H:%M:%S)] W1 start (pid $$)"
  "$VENV/bin/python" score.py --model_path finetuned_model \
    2>&1 | sed 's/^/[W1] /' | tee "$STRESS_ROOT/w1.log"
  echo "[$(date +%H:%M:%S)] W1 done"
) &
PID1=$!

# Small stagger so generation GPU allocation doesn't OOM from simultaneous
# fp32 cold-load spikes. Judge phase will still overlap heavily.
sleep 10

(
  cd "$W2"
  echo "[$(date +%H:%M:%S)] W2 start (pid $$)"
  "$VENV/bin/python" score.py --model_path finetuned_model \
    2>&1 | sed 's/^/[W2] /' | tee "$STRESS_ROOT/w2.log"
  echo "[$(date +%H:%M:%S)] W2 done"
) &
PID2=$!

wait "$PID1" "$PID2"

echo "[$(date +%H:%M:%S)] both scorers finished"
echo "--- W1 final line ---"
tail -1 "$STRESS_ROOT/w1.log"
echo "--- W2 final line ---"
tail -1 "$STRESS_ROOT/w2.log"

# Surface any Replicate/HTTP errors or None responses (the judge swallows
# exceptions by printing repr + returning None, so these show up in the
# per-worker logs as ReplicateError / 429 / None responses).
echo "--- error / None / rate-limit lines ---"
grep -Ei "replicateerror|rate.?limit|429|timeout|None$|evaluation response is none|returned none" "$STRESS_ROOT"/w*.log | head -80 || true
