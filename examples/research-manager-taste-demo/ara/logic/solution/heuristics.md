# Heuristics

## H01: Default to identity shortcuts (Option A) for parameter-free residual learning
- **Rationale**: Identity shortcuts add zero parameters and zero FLOPs beyond an element-wise add, so they cleanly isolate the effect of residual learning from increases in capacity. Empirically, A is within ~0.65 top-1 of the more expensive C on ResNet-34 (Table 3).
- **Sensitivity**: low — the residual learning gain is dominated by *having* a shortcut, not by which kind.
- **Bounds**: Use Option A only when input/output dimensions match (or fall back to zero-padding for new channels). For deeper bottleneck nets, default to Option B (projection only on dimension changes) to avoid the "no residual learning at the dimension change" blind spot of A.
- **Code ref**: [src/execution/residual_block.py](../../src/execution/residual_block.py)
- **Source**: §3.2; §"Identity vs. Projection Shortcuts"; Table 3.
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — Clean logic: zero-parameter shortcuts isolate what you're actually trying to measure (the effect of having a residual path) from a capacity increase, which a projection shortcut would confound.

## H03: Warm up the LR for the 110-layer CIFAR ResNet
- **Rationale**: At depth 110, LR 0.1 from iter 0 is "slightly too large to start converging" cleanly. Pre-warming at LR 0.01 for ~400 iterations until training error drops below ~80% lets the optimizer enter a basin where LR 0.1 then trains stably.
- **Sensitivity**: medium for the 110-layer CIFAR variant (controls whether early training stalls); low for ResNet-1202 (the paper notes no optimization difficulty there).
- **Bounds**: Trigger only when very deep CIFAR ResNets fail to start converging at the default LR. The paper notes that LR 0.1 from start eventually reaches similar accuracy "after several epochs (about 90% error)" — warmup is a stability heuristic, not a fundamental requirement.
- **Code ref**: [src/execution/training_recipe.py](../../src/execution/training_recipe.py)
- **Source**: §4.2 paragraph on n=18; footnote 5.
- **Taste** (optional):
  - [2026-07-27] `reject` on `priority` — This is essentially the same finding as C07 written up a second time as its own heuristic entry. Giving it a whole dedicated heuristic, on top of the claim, overstates how load-bearing it is — the paper itself frames it as a minor stability aid, not something worth a standalone entry.

## H04: Use bottleneck blocks (1×1 → 3×3 → 1×1) once depth exceeds ~50 layers
- **Rationale**: A 3-layer bottleneck block has the same per-block time complexity as a 2-layer 3×3 block but lets the 3×3 operate on a low-dimensional bottleneck. This makes 50/101/152-layer ResNets tractable at FLOPs comparable to a 34-layer non-bottleneck (3.8 vs. 3.6 GFLOPs at 50 layers).
- **Sensitivity**: high — at large depths, dropping bottlenecks would substantially raise compute and memory.
- **Bounds**: Use only with identity shortcuts on the high-dimensional ends; replacing those identities with projections doubles complexity and model size.
- **Code ref**: [src/execution/residual_block.py](../../src/execution/residual_block.py)
- **Source**: §"Deeper Bottleneck Architectures"; Fig. 5; Table 1.
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — Agree this is the right call past 50 layers; the FLOPs comparison against the 34-layer non-bottleneck (3.8 vs. 3.6 GFLOPs) is a concrete number, not a rule-of-thumb hand-wave.
