# Heuristics

## H01: Default to identity shortcuts (Option A) for parameter-free residual learning
- **Rationale**: Identity shortcuts add zero parameters and zero FLOPs beyond an element-wise add, so they cleanly isolate the effect of residual learning from increases in capacity. Empirically, A is within ~0.65 top-1 of the more expensive C on ResNet-34 (Table 3).
- **Sensitivity**: low — the residual learning gain is dominated by *having* a shortcut, not by which kind.
- **Bounds**: Use Option A only when input/output dimensions match (or fall back to zero-padding for new channels). For deeper bottleneck nets, default to Option B (projection only on dimension changes) to avoid the "no residual learning at the dimension change" blind spot of A.
- **Code ref**: [src/execution/residual_block.py](../../src/execution/residual_block.py)
- **Source**: §3.2; §"Identity vs. Projection Shortcuts"; Table 3.
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — Clean logic: zero-parameter shortcuts isolate what you're actually trying to measure (the effect of having a residual path) from a capacity increase, which a projection shortcut would confound.

## H02: Place BN right after every conv and before the activation, no dropout
- **Rationale**: BN keeps forward-signal variance non-zero in deep stacks (rules out vanishing-signal explanations for any residual dynamics). Combining BN with no dropout simplifies the picture and lets the depth ablation be clean.
- **Sensitivity**: medium — the paper consistently reports degraded plain-net results without BN. BN ↔ activation order is held fixed at "BN before ReLU" throughout.
- **Bounds**: Applies to ImageNet and CIFAR-10 training. For Faster R-CNN fine-tuning (Appendix A), BN statistics are *frozen* (BN behaves as an affine transform) to save memory.
- **Code ref**: [src/execution/residual_block.py](../../src/execution/residual_block.py)
- **Source**: §3.4 "Implementation"; Appendix A.

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

## H05: Down-sample by stride-2 convolutions, not pooling
- **Rationale**: Putting the stride on the first convolution of each stage (`conv3_1`, `conv4_1`, `conv5_1`) folds spatial reduction into a learnable layer and matches the VGG-style "halve resolution ⇒ double channels" rule, keeping per-layer time complexity roughly constant across stages.
- **Sensitivity**: low — a design convention rather than a tuned trick; ResNets are not reported to be sensitive to swapping pooling for strided conv at these stages.
- **Bounds**: Applies to the residual stages on ImageNet (and the analogous 32×32 → 16×16 → 8×8 progression on CIFAR-10). The 3×3 max-pool stride-2 in `conv1` is the only pooling used.
- **Code ref**: [src/execution/residual_block.py](../../src/execution/residual_block.py)
- **Source**: §3.3 design rules; Table 1.

## H06: Match shortcut down-sampling to the residual function's stride
- **Rationale**: When the residual function does stride-2 down-sampling, the shortcut must do the same — by stride-2 sampling (Option A) or stride-2 1×1 conv (Option B/C). Otherwise the element-wise add fails on shape, or worse, silently mis-aligns features.
- **Sensitivity**: high — wrong shortcut stride breaks the block.
- **Bounds**: Only triggers at stage boundaries (`conv3_1`, `conv4_1`, `conv5_1`).
- **Code ref**: [src/execution/residual_block.py](../../src/execution/residual_block.py)
- **Source**: §"Residual Network" paragraph in §3.3 ("when the shortcuts go across feature maps of two sizes, they are performed with a stride of 2").
