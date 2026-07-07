#!/bin/bash
#SBATCH --job-name=rust_repro
#SBATCH --output=slurm_logs/rust_repro_%j.out
#SBATCH --error=slurm_logs/rust_repro_%j.err
#SBATCH --time=02:00:00
#SBATCH --partition=sapphire
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
RUST_TOOLS="$SCRATCH_ROOT/tools"
WORKDIR="$SCRATCH_ROOT/tmp/rust_verify/workdir"

mkdir -p "$REPO_DIR/slurm_logs"
cd "$WORKDIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "Workdir: $WORKDIR"

# Rust toolchain
export CARGO_HOME="$RUST_TOOLS/cargo"
export RUSTUP_HOME="$RUST_TOOLS/rustup"
export PATH="$CARGO_HOME/bin:$VENV/bin:$PATH"
echo "rustc: $(rustc --version)"

# API key
set -a; source "$REPO_DIR/code/.env"; set +a
export OPENAI_API_KEY="${OPENAI_API_KEY:?must be set}"
export PYTHONUNBUFFERED=1

echo "[start] $(date) reference reproduction on test.jsonl"
"$VENV/bin/python" local_score.py \
    --module_path solution.py \
    --problems_file data/test.jsonl \
    --batch_size 20 \
    --max_workers 32 \
    --max_time_per_batch 600
echo "[done] $(date)"
