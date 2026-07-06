# Training a Masked Language Model Under Primitive Constraints

## Problem

Build and train a masked language model that achieves low validation loss while using only a restricted set of PyTorch primitives. The model processes 128-token GPT-2 sequences with 15% token masking (mask token ID 50256).

**Allowed primitives:** `nn.Linear`, `nn.Embedding`, `torch.matmul`, `torch.einsum`, `tensor.sum`, element-wise multiplication, element-wise addition, `F.relu`, and indexing/reshaping operations.

**Forbidden operations:** Division, exponentiation, `F.softmax`, `F.gelu`, boolean/comparison operators, `tensor.mean`, and any operation not explicitly listed above.

**Constraints:**
- Runtime enforcement via `torch_rule_enforcer.py` — forbidden operations cause runtime errors.
- Compute: 2--4 H100 GPUs, ~50 minutes per full training run.
- Scoring: `log(loss - 1.5)`, lower is better.
- Starting score: 1.81 (loss 7.64). Reference solution score: 1.13 (loss 4.60). Best human score: 0.34 (loss ~2.90).

## Method

The approach redesigns the standard transformer encoder to comply with the primitive restrictions, replacing softmax attention, LayerNorm, and GELU with compliant alternatives.

**Architecture: Modified Transformer Encoder.**

Token Embedding + Position Embedding → Scale Normalization → N Restricted Transformer Blocks → Output Projection (vocab size)

**ReLU Attention (replaces softmax attention).**
Compute attention scores Q @ K^T, scale by a precomputed constant `1/sqrt(d_head)`, apply ReLU (zeroing negative affinities), then scale by precomputed `1/seq_len` to bound magnitudes. Apply to values V. This produces non-negative, sparse attention weights. Note: multiplication by a precomputed constant (e.g., `x * 0.0078125` for `1/128`) is allowed because it uses only element-wise multiplication, even though division is forbidden.

**Stacked ReLU FFN (replaces GELU FFN).**
Three linear layers with ReLU activations between the first two:
`FFN(x) = Linear_3(ReLU(Linear_2(ReLU(Linear_1(x)))))`
Two stacked ReLU layers compose piecewise-linear functions with O(d_ff²) linear regions, providing sufficient expressiveness.

**Scale Normalization (replaces LayerNorm).**
`ScaleNorm(x) = x * inv_d * learnable_gain`
where `inv_d = 1/d_model` is a precomputed constant. No centering, no variance normalization — just a learned per-channel scaling. This uses only multiplication and is constraint-compliant.

**Skip connections** use only addition and are essential for training stability with deep ReLU networks.

**Loss computation** is exempt from primitive restrictions (standard cross-entropy loss is used).

## Results

The ReLU attention + stacked ReLU FFN + scale normalization architecture achieves a loss of approximately 4.60 (score 1.13), matching the reference solution. Training takes ~50 minutes on 2 H100 GPUs.

**Human baselines (11 participants):** Scores range from 0.34 (loss 2.90) to 1.79 (loss 7.50). Median score 0.95, mean 0.997. Only 2 of 11 (18%) achieved score < 0.5 (strong performance); 5 of 11 (45%) scored > 1.0 (weak, near starting code). The challenge is discovering constraint-compliant alternatives to standard components, particularly the "precomputed constant" trick for replacing division.
