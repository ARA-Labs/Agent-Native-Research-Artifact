#!/bin/bash
#SBATCH --job-name=smoke_mlm_score
#SBATCH --output=slurm_logs/smoke_mlm_score_%j.out
#SBATCH --error=slurm_logs/smoke_mlm_score_%j.err
#SBATCH --time=0:30:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=60G

set -euo pipefail
SCRATCH=/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project
VENV=$SCRATCH/venvs/extension-harness
STAGE=$SCRATCH/shared-data/restricted_mlm/.score_smoke

cd $STAGE
export PYTHONUNBUFFERED=1
$VENV/bin/python local_score.py
