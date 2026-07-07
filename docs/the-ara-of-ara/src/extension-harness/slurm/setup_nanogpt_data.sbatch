#!/bin/bash
#SBATCH --job-name=ext_nanogpt_setup
#SBATCH --output=slurm_logs/ext_nanogpt_setup_%j.out
#SBATCH --error=slurm_logs/ext_nanogpt_setup_%j.err
#SBATCH --time=02:00:00
#SBATCH --partition=kempner_h100
#SBATCH --account=kempner_sompolinsky_lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G

# One-time setup for nanogpt_chat_rl:
#   1. Download tatsu-lab/alpaca at the fixed METR revision, split 512 held-out
#      / rest, write prompts_train.jsonl and heldout/prompts.jsonl.
#   2. Copy pre-generated reference completions (gpt2-xl.jsonl, gpt2-alpaca.jsonl)
#      from the METR task assets into heldout/reference_outputs/.
#   3. Download gpt2-xl via HF, save in nanoGPT (GPT.save) format as
#      gpt2xl_base.pt — the initial finetuned_model the agent starts from.
#
# Produces under $SCRATCH/shared-data/nanogpt_chat_rl/:
#   prompts_train.jsonl
#   gpt2xl_base.pt                    (~6 GB, bf16)
#   heldout/prompts.jsonl
#   heldout/reference_outputs/gpt2-xl.jsonl
#   heldout/reference_outputs/gpt2-alpaca.jsonl

set -euo pipefail

REPO_DIR="/n/home04/zechenzhang/ara-project"
SCRATCH_ROOT="/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project"
VENV="$SCRATCH_ROOT/venvs/extension-harness"
METR_TASK_DIR="$SCRATCH_ROOT/metr-re-bench/ai_rd_nanogpt_chat_rl"
DATA_ROOT="$SCRATCH_ROOT/shared-data/nanogpt_chat_rl"
HELDOUT_DIR="$DATA_ROOT/heldout"
REF_DIR="$HELDOUT_DIR/reference_outputs"
HF_CACHE="$SCRATCH_ROOT/hf-cache"

mkdir -p "$REPO_DIR/slurm_logs" "$DATA_ROOT" "$HELDOUT_DIR" "$REF_DIR" "$HF_CACHE"
cd "$REPO_DIR"

echo "Job $SLURM_JOB_ID on $(hostname): $(date)"
echo "GPU: $(nvidia-smi -L | head -1)"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv at $VENV"
  uv venv "$VENV" --python 3.12.13
fi

"$VENV/bin/python" - <<'PYEOF'
import importlib, subprocess, sys
need = []
for pkg, mod in [
    ("datasets~=2.21.0", "datasets"),
    ("transformers~=4.44.2", "transformers"),
    ("tiktoken~=0.7.0", "tiktoken"),
    ("torch", "torch"),
    ("numpy<2.0", "numpy"),
    ("tqdm", "tqdm"),
    ("replicate~=0.32.1", "replicate"),
]:
    try:
        importlib.import_module(mod)
    except ImportError:
        need.append(pkg)
if need:
    subprocess.check_call(["uv", "pip", "install", "--python", sys.executable, *need])
PYEOF

export PATH="$VENV/bin:$PATH"
export HF_HOME="$HF_CACHE"
export HF_HUB_CACHE="$HF_CACHE/hub"
export TRANSFORMERS_CACHE="$HF_CACHE"
export PYTHONUNBUFFERED=1

# ---------------------------------------------------------------------------
# 1. Alpaca prompt split
# ---------------------------------------------------------------------------
echo "[setup] step 1/3: split alpaca prompts (512 held-out / rest train)"
"$VENV/bin/python" - <<PYEOF
import json, os
import datasets

DATA_ROOT = "$DATA_ROOT"
HELDOUT = "$HELDOUT_DIR"
HELDOUT_SIZE = 512

os.makedirs(HELDOUT, exist_ok=True)

ds = datasets.load_dataset(
    "tatsu-lab/alpaca",
    revision="dce01c9b08f87459cf36a430d809084718273017",
    split="train",
)
prompts = [x.split("### Response:\n")[0] + "### Response:\n" for x in ds["text"]]
prompts_test = prompts[:HELDOUT_SIZE]
prompts_train = prompts[HELDOUT_SIZE:]

def write_jsonl(strings, path, key):
    with open(path, "w") as f:
        for s in strings:
            f.write(json.dumps({key: s}) + "\n")

write_jsonl(prompts_train, os.path.join(DATA_ROOT, "prompts_train.jsonl"), "prompt")
write_jsonl(prompts_test, os.path.join(HELDOUT, "prompts.jsonl"), "prompt")
print(f"[setup] wrote {len(prompts_train)} train + {len(prompts_test)} held-out prompts")
PYEOF

# ---------------------------------------------------------------------------
# 2. Pre-generated reference completions (shipped with METR task)
# ---------------------------------------------------------------------------
echo "[setup] step 2/3: copy reference completions (gpt2-xl, gpt2-alpaca)"
for f in gpt2-xl.jsonl gpt2-alpaca.jsonl; do
  src="$METR_TASK_DIR/assets/$f"
  [ -f "$src" ] || { echo "ERROR: missing $src" >&2; exit 2; }
  cp "$src" "$REF_DIR/$f"
done
ls -la "$REF_DIR"

# ---------------------------------------------------------------------------
# 3. Seed GPT-2-XL base in nanoGPT save format
# ---------------------------------------------------------------------------
echo "[setup] step 3/3: save gpt2-xl (HF) as nanoGPT GPT.save()-format checkpoint"
"$VENV/bin/python" - <<PYEOF
import os, sys
sys.path.insert(0, "$REPO_DIR/code/extension-harness/scoring/nanogpt_chat_rl")
import torch
from model import GPT

out_path = os.path.join("$DATA_ROOT", "gpt2xl_base.pt")
if os.path.exists(out_path):
    print(f"[setup] {out_path} already exists, skipping")
    sys.exit(0)

model = GPT.from_pretrained("gpt2-xl")
model.save(out_path)
size_gb = os.path.getsize(out_path) / 1e9
print(f"[setup] wrote gpt2-xl base checkpoint: {out_path} ({size_gb:.2f} GB)")
PYEOF

echo "[done] nanogpt_chat_rl shared data ready under $DATA_ROOT"
ls -la "$DATA_ROOT" "$HELDOUT_DIR" "$REF_DIR"
