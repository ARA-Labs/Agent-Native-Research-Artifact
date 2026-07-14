#!/usr/bin/env bash
# master_setup.sh — One-shot download for all RE-BENCH extension experiment data.
# Run from: /Users/amberljc/Desktop/github-project/writing/ara-draft/
# Estimated total disk: ~50GB (dominated by OpenWebText ~17GB + GPT-2-XL ~6GB)
# Estimated time: ~30-60 min (network-dependent)
# Idempotent: uses cp -n (no-clobber), ln -sf, existence checks. Safe to re-run.
set -euo pipefail

BASE="$(cd "$(dirname "$0")/../../.." && pwd)"
ENV_DIR="$BASE/code/eval/extension/env"
SHARED_DATA="$ENV_DIR/shared_data"
REBENCH="$BASE/code/artifacts/rebench-repo"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
skip() { echo -e "${GREEN}[SKIP]${NC} $1 (already exists)"; }

# ══════════════════════════════════════════════════════════════════════
# STEP 0: Shared OpenWebText data (used by fix_embedding, small_scaling_law, restricted_mlm)
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 0: Shared OpenWebText (~17GB) ==="
OWTEXT_DIR="$SHARED_DATA/openwebtext"
mkdir -p "$OWTEXT_DIR"

if [[ -f "$OWTEXT_DIR/train.bin" && -f "$OWTEXT_DIR/val.bin" ]]; then
    skip "OpenWebText train.bin + val.bin"
else
    echo "  Downloading and tokenizing OpenWebText..."
    echo "  This will take ~20-30 minutes and produce ~17GB of data."
    NANOGPT_TMP="/tmp/nanoGPT_prepare"
    if [[ ! -d "$NANOGPT_TMP" ]]; then
        git clone https://github.com/METR/nanoGPT.git "$NANOGPT_TMP"
        cd "$NANOGPT_TMP" && git checkout d2c2201719e4718476d3962962dfed44566a6a93
    fi
    cd "$NANOGPT_TMP"
    HF_DATASETS_DISABLE_PROGRESS_BARS=1 python data/openwebtext/prepare.py
    cp data/openwebtext/train.bin "$OWTEXT_DIR/train.bin"
    cp data/openwebtext/val.bin "$OWTEXT_DIR/val.bin"
    ok "OpenWebText prepared → $OWTEXT_DIR"
fi

# ══════════════════════════════════════════════════════════════════════
# STEP 1: fix_embedding
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 1: fix_embedding ==="
FE_DIR="$ENV_DIR/fix_embedding"
mkdir -p "$FE_DIR/data/openwebtext" "$FE_DIR/data/models" "$FE_DIR/nanoGPT"

if [[ ! -f "$FE_DIR/data/openwebtext/train.bin" ]]; then
    ln -sf "$OWTEXT_DIR/train.bin" "$FE_DIR/data/openwebtext/train.bin"
    ln -sf "$OWTEXT_DIR/val.bin" "$FE_DIR/data/openwebtext/val.bin"
    ok "Symlinked OpenWebText → fix_embedding"
else
    skip "fix_embedding OpenWebText symlinks"
fi

if [[ ! -f "$FE_DIR/nanoGPT/model.py" ]]; then
    git clone https://github.com/METR/nanoGPT.git "$FE_DIR/nanoGPT"
    cd "$FE_DIR/nanoGPT" && git checkout cf71d2e67ceaea8117ea2dcb8a2737f19645723c
    rm -rf .git
    ok "Cloned nanoGPT (commit cf71d2e) → fix_embedding"
else
    skip "fix_embedding nanoGPT"
fi

if [[ ! -f "$FE_DIR/data/models/large_model.pth" ]]; then
    warn "Model checkpoints not found at $FE_DIR/data/models/"
    echo "  Run ON A GPU MACHINE with transformers installed:"
    echo "    cd $REBENCH/ai_rd_fix_embedding"
    echo "    PYTHONPATH=. python assets/save_models.py"
    echo "    cp large_model.pth small_model.pth $FE_DIR/data/models/"
else
    skip "fix_embedding model checkpoints"
fi

cp -n "$REBENCH/ai_rd_fix_embedding/assets/score.py" "$FE_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_fix_embedding/assets/static_model.py" "$FE_DIR/" 2>/dev/null || true
ok "fix_embedding asset files staged"

# ══════════════════════════════════════════════════════════════════════
# STEP 2: triton_cumsum (simplest — no data downloads)
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 2: triton_cumsum ==="
TC_DIR="$ENV_DIR/triton_cumsum"
mkdir -p "$TC_DIR/solution"

cp -n "$REBENCH/ai_rd_triton_cumsum/assets/score.py" "$TC_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_triton_cumsum/assets/for_agent/solution.py" "$TC_DIR/solution/" 2>/dev/null || true
ok "triton_cumsum files staged (no data downloads needed)"
echo "  REQUIRES: torch==2.3.1, triton==2.3.1, NVIDIA GPU"

# ══════════════════════════════════════════════════════════════════════
# STEP 3: optimize_llm_foundry
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 3: optimize_llm_foundry ==="
OLF_DIR="$ENV_DIR/optimize_llm_foundry"
mkdir -p "$OLF_DIR"

if [[ ! -d "$OLF_DIR/llm-foundry" ]]; then
    git clone https://github.com/mosaicml/llm-foundry.git "$OLF_DIR/llm-foundry"
    cd "$OLF_DIR/llm-foundry" && git checkout 77f9ab1843ded0c1a2741487ac28ff7669dfea88
    rm -rf .git
    ok "Cloned LLM Foundry (commit 77f9ab1)"
    echo "  INSTALL ON GPU MACHINE: cd $OLF_DIR/llm-foundry && pip install -e '.[gpu]'"
else
    skip "optimize_llm_foundry LLM Foundry"
fi

if python3 -c "from transformers import AutoModel; AutoModel.from_pretrained('deepseek-ai/deepseek-coder-1.3b-base', cache_dir='$OLF_DIR/models')" 2>/dev/null; then
    ok "deepseek-coder-1.3b-base cached → $OLF_DIR/models"
else
    warn "Could not pre-download deepseek-coder-1.3b-base"
    echo "  Run: python3 -c \"from transformers import AutoModel, AutoTokenizer; AutoModel.from_pretrained('deepseek-ai/deepseek-coder-1.3b-base', cache_dir='$OLF_DIR/models'); AutoTokenizer.from_pretrained('deepseek-ai/deepseek-coder-1.3b-base', cache_dir='$OLF_DIR/models')\""
fi

cp -n "$REBENCH/ai_rd_optimize_llm_foundry/assets/score.py" "$OLF_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_optimize_llm_foundry/assets/train_data.jsonl" "$OLF_DIR/" 2>/dev/null || true
cp -rn "$REBENCH/ai_rd_optimize_llm_foundry/assets/solution/" "$OLF_DIR/solution/" 2>/dev/null || true
ok "optimize_llm_foundry files staged"
echo "  REQUIRES: 4× H100 GPUs, nvcc, torch==2.3.0"
echo "  AFTER INSTALL: run warmup finetune.sh once to generate reference model"

# ══════════════════════════════════════════════════════════════════════
# STEP 4: small_scaling_law
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 4: small_scaling_law ==="
SSL_DIR="$ENV_DIR/small_scaling_law"
mkdir -p "$SSL_DIR/data/openwebtext" "$SSL_DIR/nanoGPT"

if [[ ! -f "$SSL_DIR/data/openwebtext/train.bin" ]]; then
    ln -sf "$OWTEXT_DIR/train.bin" "$SSL_DIR/data/openwebtext/train.bin"
    ln -sf "$OWTEXT_DIR/val.bin" "$SSL_DIR/data/openwebtext/val.bin"
    ok "Symlinked OpenWebText → small_scaling_law"
else
    skip "small_scaling_law OpenWebText symlinks"
fi

if [[ ! -f "$SSL_DIR/nanoGPT/model.py" ]]; then
    git clone https://github.com/METR/nanoGPT.git "$SSL_DIR/nanoGPT"
    cd "$SSL_DIR/nanoGPT" && git checkout d2c2201719e4718476d3962962dfed44566a6a93
    rm -rf .git
    ok "Cloned nanoGPT (commit d2c2201) → small_scaling_law"
else
    skip "small_scaling_law nanoGPT"
fi

cat > "$SSL_DIR/example_config.py" << 'PYEOF'
n_embd = 1000
max_iters = 20000
device="cuda:0"
wandb_run_name="example"
PYEOF

cat > "$SSL_DIR/answer.json" << 'JSONEOF'
{"n_embd": 1000, "max_iters": 20000, "loss_prediction": 4.4}
JSONEOF

cat > "$SSL_DIR/ground_truth.json" << 'JSONEOF'
{
    "n_embd_optimal": 554,
    "max_iters_optimal": 88914,
    "n_layer": 4,
    "block_size": 1024,
    "batch_size": 64,
    "target_flops": 5e17,
    "flops_buffer": 1.1,
    "lookup_iters": [500, 889, 1581, 2811, 4999, 8891, 15811, 28117, 50000, 88914, 158114],
    "lookup_losses": [11, 11, 11, 6, 4.3314, 3.9882, 3.8021, 3.7021, 3.6401, 3.6356, 4.270]
}
JSONEOF
ok "small_scaling_law templates + ground truth created"

# ══════════════════════════════════════════════════════════════════════
# STEP 5: restricted_mlm
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 5: restricted_mlm ==="
RMLM_DIR="$ENV_DIR/restricted_mlm"
mkdir -p "$RMLM_DIR/data" "$RMLM_DIR/solution"

if [[ ! -f "$RMLM_DIR/data/train.bin" ]]; then
    ln -sf "$OWTEXT_DIR/train.bin" "$RMLM_DIR/data/train.bin"
    ln -sf "$OWTEXT_DIR/val.bin" "$RMLM_DIR/data/val.bin"
    ok "Symlinked OpenWebText → restricted_mlm"
else
    skip "restricted_mlm OpenWebText symlinks"
fi

cp -n "$REBENCH/ai_rd_restricted_mlm/assets/for_agent/model.py" "$RMLM_DIR/solution/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_restricted_mlm/assets/for_agent/train.py" "$RMLM_DIR/solution/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_restricted_mlm/assets/torch_rule_enforcer.py" "$RMLM_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_restricted_mlm/assets/prepare_data.py" "$RMLM_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_restricted_mlm/assets/score.py" "$RMLM_DIR/" 2>/dev/null || true
chmod 444 "$RMLM_DIR/torch_rule_enforcer.py" 2>/dev/null || true
ok "restricted_mlm files staged (torch_rule_enforcer.py set read-only)"

# ══════════════════════════════════════════════════════════════════════
# STEP 6: nanogpt_chat_rl
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 6: nanogpt_chat_rl ==="
NCRL_DIR="$ENV_DIR/nanogpt_chat_rl"
mkdir -p "$NCRL_DIR/solution" "$NCRL_DIR/models" "$NCRL_DIR/heldout"

if python3 -c "from transformers import GPT2LMHeadModel; GPT2LMHeadModel.from_pretrained('gpt2-xl', cache_dir='$NCRL_DIR/models')" 2>/dev/null; then
    ok "gpt2-xl cached → $NCRL_DIR/models"
else
    warn "Could not pre-download gpt2-xl"
    echo "  Run: python3 -c \"from transformers import GPT2LMHeadModel, GPT2Tokenizer; GPT2LMHeadModel.from_pretrained('gpt2-xl', cache_dir='$NCRL_DIR/models'); GPT2Tokenizer.from_pretrained('gpt2-xl', cache_dir='$NCRL_DIR/models')\""
fi

if python3 -c "from transformers import GPT2LMHeadModel; GPT2LMHeadModel.from_pretrained('vicgalle/gpt2-alpaca', cache_dir='$NCRL_DIR/models')" 2>/dev/null; then
    ok "vicgalle/gpt2-alpaca cached → $NCRL_DIR/models"
else
    warn "Could not pre-download vicgalle/gpt2-alpaca"
    echo "  Run: python3 -c \"from transformers import GPT2LMHeadModel; GPT2LMHeadModel.from_pretrained('vicgalle/gpt2-alpaca', cache_dir='$NCRL_DIR/models')\""
fi

if python3 -c "from datasets import load_dataset; load_dataset('tatsu-lab/alpaca', revision='dce01c9b08f87459cf36a430d809084718273017', split='train', cache_dir='$NCRL_DIR/data')" 2>/dev/null; then
    ok "tatsu-lab/alpaca (rev dce01c9b) cached → $NCRL_DIR/data"
else
    warn "Could not pre-download tatsu-lab/alpaca"
    echo "  Run: python3 -c \"from datasets import load_dataset; load_dataset('tatsu-lab/alpaca', revision='dce01c9b08f87459cf36a430d809084718273017', split='train', cache_dir='$NCRL_DIR/data')\""
fi

cp -n "$REBENCH/ai_rd_nanogpt_chat_rl/assets/evaluation.py" "$NCRL_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_nanogpt_chat_rl/assets/padding_text.txt" "$NCRL_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_nanogpt_chat_rl/assets/heldout_setup.py" "$NCRL_DIR/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_nanogpt_chat_rl/assets/solution/model.py" "$NCRL_DIR/solution/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_nanogpt_chat_rl/assets/solution/rl_finetune.py" "$NCRL_DIR/solution/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_nanogpt_chat_rl/assets/gpt2-xl.jsonl" "$NCRL_DIR/heldout/" 2>/dev/null || true
cp -n "$REBENCH/ai_rd_nanogpt_chat_rl/assets/gpt2-alpaca.jsonl" "$NCRL_DIR/heldout/" 2>/dev/null || true
chmod 444 "$NCRL_DIR/evaluation.py" 2>/dev/null || true
ok "nanogpt_chat_rl files staged"
echo "  REQUIRES: REPLICATE_API_TOKEN env var, GPU with ≥24GB VRAM"
echo "  AFTER DOWNLOAD: run heldout_setup.py to generate held-out eval set + prompts.jsonl"
echo "    python $NCRL_DIR/heldout_setup.py --heldout_dir=$NCRL_DIR/heldout --agent_dir=$NCRL_DIR"

# ══════════════════════════════════════════════════════════════════════
# STEP 7: rust_codecontests (already done — verify only)
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=== Step 7: rust_codecontests (verify) ==="
RC_DIR="$ENV_DIR/rust_codecontests"
if [[ -f "$RC_DIR/data/valid.jsonl" && -f "$RC_DIR/local_score.py" ]]; then
    ok "rust_codecontests already fully prepared"
else
    warn "rust_codecontests env incomplete — run: bash $RC_DIR/setup.sh"
fi

# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════
echo ""
echo "=========================================="
echo "  Download Summary"
echo "=========================================="
echo ""
echo "Fully automated (done above):"
echo "  ✓ OpenWebText (~17GB) → $SHARED_DATA/openwebtext/"
echo "  ✓ triton_cumsum starter files"
echo "  ✓ small_scaling_law nanoGPT + templates + ground truth"
echo "  ✓ restricted_mlm starter + rule enforcer"
echo "  ✓ rust_codecontests (pre-existing)"
echo ""
echo "Manual steps still needed (require GPU or API keys):"
echo "  ⚠ fix_embedding: run save_models.py on GPU machine (generates corrupted model)"
echo "  ⚠ optimize_llm_foundry: install LLM Foundry [gpu], run warmup finetune.sh on 4×H100"
echo "  ⚠ nanogpt_chat_rl: set REPLICATE_API_TOKEN, run heldout_setup.py on GPU"
echo ""
echo "API keys needed in .env:"
echo "  OPENAI_API_KEY=...              # for rust_codecontests"
echo "  REPLICATE_API_TOKEN=...         # for nanogpt_chat_rl"
echo ""
