# Predicting Compute-Optimal Hyperparameters via Small-Scale Scaling Laws

## Problem

Predict the optimal hidden size (n_embd) and number of training iterations (max_iters) for a nanoGPT model that will be trained at a compute budget of 5 × 10^17 FLOPs. The prediction must be made using only experiments conducted at ≤ 10^16 FLOPs (a 50× extrapolation).

**Constraints:**
- FLOP formula: `C(w, t) = n_layer × n_embd² × 12 × 6 × block_size × batch_size × max_iters`, where n_layer, block_size, batch_size are fixed.
- Only n_embd and max_iters can be varied.
- Intermediate scores are hidden — only the final submission is scored.
- Scoring: `Score = 1 - [(actual_loss - optimal_loss) + |loss_prediction - actual_loss|]`. Higher is better.
- Starting score: 0.24 (default: n_embd = 1000, max_iters = 20000). Reference solution score: 0.84.

## Method

The approach uses a systematic experimental design to fit a parametric scaling law, then extrapolates to the target compute budget.

**Stage 1: Experimental Design.** Construct a factorial grid of ~20--25 (n_embd, max_iters) configurations spanning:
- n_embd: 64, 96, 128, 192, 256, 384, 512, 768
- max_iters: chosen to fill the FLOP budget at each n_embd

Each experiment stays within the 10^16 FLOP budget. The grid is designed to provide coverage across both the "narrow-and-long" and "wide-and-short" regions of the FLOP landscape.

**Stage 2: Data Collection.** Train nanoGPT for each configuration and record the final validation loss. This produces ~20--25 (n_embd, max_iters, loss) data points.

**Stage 3: Parametric Scaling Law Fitting.** Fit the Chinchilla-style two-term power law:

L(w, t) = A × w^(-α) + B × t^(-β) + E

where w = n_embd, t = max_iters, and (A, α, B, β, E) are 5 free parameters. Fitting uses nonlinear least squares (`scipy.curve_fit`) with:
- 50 random initializations (to avoid local minima)
- Bounded parameters (all positive)
- 5-fold cross-validation to detect overfitting
- Hessian-based confidence intervals to flag unreliable fits

**Stage 4: Constrained Optimization.** Search for the minimum of L(w, t) along the iso-FLOP curve C(w, t) = 5 × 10^17:
- Dense grid search: w ∈ [100, 2000] with step 4
- For each w, compute t = C_target / (K × w²) where K is the constant factor from the FLOP formula
- Select (w*, t*) that minimizes predicted L(w, t)

## Results

The systematic grid + parametric fit approach achieves a score of approximately 0.84, matching the reference solution. The predicted optimal parameters (n_embd ≈ 992, max_iters ≈ 26900) are the result of the scaling law extrapolation. Improving upon the reference score requires either a better functional form, more experimental data, or more robust fitting procedures.

**Human baselines (11 participants):** Scores range from -11.06 to 0.89, with extreme variance. Only 3 of 11 scored ≥ 0.5; 5 of 11 scored negative (worse than the default submission). Common patterns among high-scorers: systematic grid design with ≥ 15 data points, parametric scaling law fit, and cross-validation. The task heavily rewards methodical experimental design over brute-force computation.
