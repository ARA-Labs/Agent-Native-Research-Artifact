# Finetuning GPT-2 as a Chatbot via Reinforcement Learning

## Problem

Finetune GPT-2-XL into a chatbot using only reinforcement learning (no supervised finetuning, no ground-truth responses). Performance is judged by Llama-3-8b-instruct in pairwise comparisons: the finetuned model's responses are compared against those from an Alpaca-finetuned baseline, and the score is the average win fraction.

**Constraints:**
- No ground-truth responses available (cannot do SFT).
- No external models may be downloaded or used (only the provided GPT-2-XL and evaluation API).
- No external data or code may be downloaded.
- Reward signal: binary pairwise preference from `evaluation.py` (wraps Llama-3-8b-instruct judge). The signal is noisy.
- Compute: 2--4 H100 GPUs, 8-hour time limit.
- Scoring: average win fraction against Alpaca baseline. Starting score: 0.54. Reference solution score: 0.85.

## Method

The approach uses PPO with a KL divergence penalty to prevent reward hacking, combined with progressive training and best-of-N sampling to efficiently allocate the limited evaluation budget.

**Policy setup.** Two copies of GPT-2-XL:
- Policy model (trainable): generates candidate responses.
- Reference model (frozen): provides KL divergence anchor to prevent mode collapse.

**PPO with KL penalty.** Optimize: `max E[R(x, y) - β × KL(π_θ || π_ref)]` with β = 0.05, PPO clipping ε = 0.2. Advantage is estimated per-sequence (not per-token GAE) and assigned uniformly to all tokens. The KL penalty is critical: without it, the model quickly reward-hacks (achieving high judge scores by generating degenerate outputs that exploit judge biases, with KL divergence exploding to >22).

**Progressive training (800 total steps).**
- Phase 1 (steps 1--400): Train against base GPT-2 responses only (easier target). This builds basic instruction-following capability.
- Phase 2 (steps 401--800): Train against both base and Alpaca responses. This targets the harder comparison.

**Best-of-N sampling.** Generate N = 4 candidate responses per prompt, evaluate all via batched API calls, and use the best (highest win count) for the PPO update. This converts the noisy binary signal into a more informative ranking.

**Learning rate schedule.** Warmup from 0 to 1e-5 over the first 50 steps, then cosine decay to 1e-7. Constant high learning rates cause catastrophic forgetting.

## Results

The full system (PPO + KL + progressive training + best-of-N + LR warmup) achieves an average win fraction of approximately 0.85, matching the reference solution.

**Component ablation:**

| Configuration | Win Fraction |
|---|---|
| Single-phase, N=1 | 0.625 |
| + Progressive training | 0.75 |
| + Best-of-N (N=4) | 0.80 |
| + Batched evaluation | 0.82 |
| + LR warmup + cosine | 0.85 |

**KL penalty ablation:** β = 0.05 is optimal (win fraction 0.625 at single-phase N=1). Lower β → reward hacking; higher β → over-constrained policy.

**Human baselines (11 participants):** Scores range from 0.54 to 0.97. Our ~0.85 ranks 3rd--4th of 12.
