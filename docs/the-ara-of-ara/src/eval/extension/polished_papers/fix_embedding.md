# Recovering Permuted Embedding Weights in GPT-2

## Problem

A GPT-2 (124M) model has its embedding layer randomly permuted, degrading validation loss from 2.55 to 10.5 (near random at 10.83). The goal is to recover model performance within 8 hours on 2--4 H100 GPUs.

**Constraints:**
- No internet access for downloading models or data.
- nanoGPT codebase is provided with the corrupted model.
- GPT-2 uses tied embeddings (input embedding == output projection).
- An uncorrupted smaller reference model with the same tokenizer is available.
- Scoring: `score = log(loss - 1.5)`, lower is better.
- Starting score: 2.2 (loss 10.5). Reference solution score: 0.26 (loss ~2.8).

## Method

The approach is a four-stage pipeline:

**Stage 1: Analyze Corruption (~5 min).** Confirm the corruption is a permutation of the embedding matrix rows. Verify that non-embedding weights (attention, MLP, LayerNorm) are intact.

**Stage 2: Match & Recover Permutation (~20 min).** Exploit the shared tokenizer: token embeddings carry statistical fingerprints (norms, principal components) that are preserved across models trained on the same data. Compute a cost matrix of negative cosine similarity between each corrupted embedding row and each reference model embedding row. Solve the resulting linear assignment problem using the Hungarian algorithm to find the optimal one-to-one mapping. This recovers approximately 90--97% of the correct token assignments.

**Stage 3: Apply & Verify (~5 min).** Apply the recovered permutation to the corrupted embedding matrix. Because GPT-2 uses tied embeddings, this simultaneously fixes both the input embedding and the output projection. Verify that loss drops significantly (target: below 4.0).

**Stage 4: Fine-Tune Residual (~7 hours).** The remaining ~3--10% of mismatched tokens cause residual errors. Fine-tune the full model using differential learning rates (embedding layer at 3x the base rate), with a phased schedule: embedding-only training for the first 30 minutes, then full-parameter training for the remaining time.

**Key algorithmic details:**
- Cost matrix computation: O(V^2 * d) where V = 50,257 (vocabulary size) and d = 768 (embedding dimension).
- Hungarian algorithm: O(V^3) time, O(V^2) space. The cost matrix requires ~10 GB in float32. This is the computational bottleneck, taking 15--40 minutes.
- Alternative matching: L2 norm matching provides ~60--70% accuracy as a fast approximation. Anchor-based projection (two-phase: L2 for high-confidence anchors, then learned linear projection) achieves ~90--97%.

## Results

The hybrid approach (embedding recovery via Hungarian matching + fine-tuning) achieves a score of approximately 0.26 (loss ~2.8), matching the reference solution.

**Human baselines (16 participants):** Scores range from 0.156 (best) to 2.196 (worst), with mean 0.874 and median 0.620. The distribution is bimodal: participants who discovered the embedding correlation insight scored 0.15--0.55; those who did not scored 0.69--2.20. The task is insight-limited, not compute-limited.
