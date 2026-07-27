# Heuristics

## H01: Default to identity shortcuts (Option A) for parameter-free residual learning
- **Rationale**: Adds zero parameters/FLOPs beyond an element-wise add, isolating the effect of having a residual path from any capacity increase; empirically close to the more expensive options (see C04).
- **Status**: active
- **Provenance**: ai-executed
- **Sensitivity**: low — the residual-learning gain is dominated by having a shortcut, not by which kind.
- **Code ref**: [pending]
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — Clean logic: zero-parameter shortcuts isolate what you're actually trying to measure (the effect of a residual path) from a capacity increase, which a projection shortcut would confound.

## H02: Place batch norm right after every conv and before the activation; no dropout
- **Rationale**: Keeps forward-signal variance non-zero through a deep stack — this is what lets the vanishing-gradient explanation for degradation be ruled out with confidence (N04); every experiment in this trajectory runs under this convention.
- **Status**: active
- **Provenance**: ai-executed
- **Sensitivity**: medium — every result in this trajectory presumes it.
- **Code ref**: [pending]

## H03: Warm up the LR for the 110-layer CIFAR ResNet
- **Rationale**: At depth 110, the standard learning rate stalls early progress; a short low-LR warmup phase lets the optimizer reach a basin where the standard rate then trains stably.
- **Status**: active
- **Provenance**: ai-executed
- **Sensitivity**: medium for the 110-layer CIFAR variant; low for the 1202-layer variant, which the paper notes doesn't need it.
- **Code ref**: [pending]
- **Taste** (optional):
  - [2026-07-27] `reject` on `priority` — This is essentially the same finding as C07 written up a second time as its own heuristic entry. Giving it a whole dedicated heuristic, on top of the claim, overstates how load-bearing it is — the source itself frames it as a minor stability aid, not something worth a standalone entry.

## H04: Use bottleneck blocks (1×1 → 3×3 → 1×1) once depth exceeds ~50 layers
- **Rationale**: A 3-layer bottleneck block matches the per-block cost of the 2-layer block used at shallower depths, making 50/101/152-layer nets tractable without a proportional compute increase (see C05).
- **Status**: active
- **Provenance**: ai-executed
- **Sensitivity**: high — at large depths, dropping bottlenecks would substantially raise compute and memory.
- **Code ref**: [pending]
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — Agree this is the right call past 50 layers; the FLOPs comparison against the 34-layer non-bottleneck is a concrete number, not a rule-of-thumb hand-wave.

## H05: Down-sample by stride-2 convolutions, not pooling
- **Rationale**: Folds spatial reduction into a learnable layer at each stage boundary, keeping per-stage time complexity roughly constant rather than adding a separate pooling step.
- **Status**: active
- **Provenance**: ai-executed
- **Sensitivity**: low — a design convention rather than a tuned trick.
- **Code ref**: [pending]

## H06: Match shortcut down-sampling to the residual function's stride
- **Rationale**: When the residual branch down-samples, the shortcut must down-sample by the same amount, or the element-wise add either fails on shape or silently misaligns features.
- **Status**: active
- **Provenance**: ai-executed
- **Sensitivity**: high — a mismatched shortcut stride breaks the block.
- **Code ref**: [pending]
