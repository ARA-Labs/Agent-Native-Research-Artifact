# Claims

## C01: Plain CNNs exhibit a depth-induced degradation problem
- **Statement**: For sufficiently deep "plain" (shortcut-free) CNNs, increasing depth increases training error relative to a shallower counterpart, even with batch normalization and standard initialization — not explained by vanishing gradients or insufficient training time.
- **Conditions**: Observed on both a small-image benchmark (CIFAR-10, depths up to 110) and a large-image benchmark (ImageNet, depths 18 vs. 34), so not a small-scale artifact.
- **Sources**: [28.54 ← plain-34 ImageNet top-1 val error, Table 2 [result]; 27.94 ← plain-18 ImageNet top-1 val error, Table 2 [result]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: A controlled depth scan under matched training in which deeper plain nets show training error equal to or lower than shallower ones.
- **Proof**: [N02, N03]
- **Dependencies**: none
- **Tags**: degradation, optimization, depth-scaling
- **Last revised**: 2026-07-27 (2026-07-27_001#7)

## C02: Residual reformulation removes the degradation problem
- **Statement**: Replacing each pair of stacked layers with a residual block — a parameter-free identity shortcut around the block — makes a deeper network reach lower training and validation error than its shallower plain counterpart, at matched depth.
- **Conditions**: Demonstrated at 18-vs-34-layer depth on ImageNet with identity shortcuts; presented as depth-general.
- **Sources**: [25.03 ← ResNet-34 top-1 ImageNet val, Table 2 [result]; 27.88 ← ResNet-18 top-1 ImageNet val, Table 2 [result]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: ResNet-34 fails to improve over ResNet-18, or has higher training error than plain-34, under the same pipeline.
- **Proof**: [N07, N08]
- **Dependencies**: C01
- **Tags**: residual-learning, identity-shortcut

## C03: Accuracy keeps improving with depth up to 152 layers on ImageNet, once bottleneck blocks are used
- **Statement**: Within the depths studied, deeper bottleneck-block ResNets reach monotonically lower ImageNet validation error than shallower ones, at lower compute than a comparable non-residual network of similar accuracy.
- **Conditions**: Depths 50/101/152, bottleneck design, ImageNet.
- **Sources**: [22.85 ← ResNet-50 top-1, Table 3 [result]; 21.75 ← ResNet-101 top-1, Table 3 [result]; 21.43 ← ResNet-152 top-1, Table 3 [result]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: ResNet-152 fails to beat ResNet-101 (or 101 fails to beat 50) by more than the ~0.1% noise floor.
- **Proof**: [N11, N12]
- **Dependencies**: C02
- **Tags**: depth-scaling, imagenet

## C04: Identity shortcuts are sufficient; projection shortcuts give only marginal gains
- **Statement**: Among a spectrum of shortcut designs from parameter-free identity to fully projected, the accuracy difference is small; the parameter-free option is not measurably disadvantaged relative to the more expensive alternatives.
- **Conditions**: ResNet-34, ImageNet, 10-crop testing.
- **Sources**: [25.03 ← option A top-1, Table 3 [result]; 24.52 ← option B top-1, Table 3 [result]; 24.19 ← option C top-1, Table 3 [result]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: A projection-shortcut option beats identity by more than ~1 top-1 point under identical training.
- **Proof**: [N09]
- **Dependencies**: C02
- **Tags**: shortcut-design, ablation
- **Taste** (optional):
  - [2026-07-27] `uncertain` on `evidence` — The ≤0.65pt gap is doing a lot of work here ("sufficient", "marginal") but it's a single ImageNet run per option with no repeated-trial variance reported — that gap could plausibly be run-to-run noise rather than a real ordering between A/B/C.

## C05: Bottleneck blocks make 50/101/152-layer ResNets practical
- **Statement**: A 3-layer bottleneck block (dimension-reducing, then expanding) matches the per-block cost of the 2-layer block used at shallower depths, letting depth scale into the 50-152 range without a proportional compute blowup.
- **Conditions**: Applies at ≥50 layers.
- **Sources**: [3.8 ← ResNet-50 GFLOPs, Table 1 [input]; 3.6 ← ResNet-34 GFLOPs, Table 1 [input]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: A non-bottleneck ResNet at equal compute matches or beats the bottleneck version at the same depth.
- **Proof**: [N11, N12]
- **Dependencies**: C02, C04
- **Tags**: bottleneck, architecture

## C06: Residual nets generalize to extreme CIFAR-10 depths
- **Statement**: On a small-image benchmark, residual networks keep training successfully well beyond the depth a plain network tolerates; the deepest variant studied shows a train/test generalization gap, not a failure of training error to decrease.
- **Conditions**: CIFAR-10, depths 20 through 1202.
- **Sources**: [6.43 ← ResNet-110 CIFAR-10 test error, Table 6 [result]; 7.93 ← ResNet-1202 CIFAR-10 test error, Table 6 [result]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: A CIFAR ResNet at depth ≥110 under the same recipe fails to converge below 10% test error, or its training error fails to beat the 56-layer model's.
- **Proof**: [N13]
- **Dependencies**: C02, C03
- **Tags**: cifar-10, extreme-depth
- **Taste** (optional):
  - [2026-07-27] `uncertain` on `framing` — "Just a generalization gap, not an optimization failure" is stated as settled, but there's no matched-capacity smaller-model control shown — low training error plus high test error is consistent with overfitting but doesn't rule out a milder optimization issue a stronger regularizer happens to paper over.

## C07: The 110-layer CIFAR ResNet needs a warmup phase to start converging at the target learning rate
- **Statement**: At extreme CIFAR depth, starting training directly at the paper's standard learning rate stalls early progress; a short low-LR warmup phase before switching to the standard rate avoids the stall.
- **Conditions**: 110-layer CIFAR-10 ResNet specifically; the paper notes the 1202-layer variant does not need this.
- **Sources**: [0.01 ← warmup LR, §4.2 n=18 paragraph [input]; 400 ← warmup iteration count, §4.2 n=18 paragraph [input]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: Training from the standard LR at iteration 0 reaches the same final error, within the same budget, as the warmup recipe.
- **Proof**: [N13, N14]
- **Dependencies**: C06
- **Tags**: training-recipe, warmup
- **Taste** (optional):
  - [2026-07-27] `uncertain` on `framing` — Statement reads as "warmup restores convergence" (existence), but the paper's own follow-up note is that the standard LR without warmup reaches similar accuracy eventually, just slower — that's a convergence-speed effect, not a convergence-existence one. The claim as framed overstates what the source supports.

## C08: ResNet representations transfer to detection, improving over a VGG-16 backbone
- **Statement**: Swapping a deeper residual backbone into an otherwise-unchanged detector improves localization-sensitive downstream accuracy substantially, indicating the representational gain is not classification-specific.
- **Conditions**: Baseline Faster R-CNN, VGG-16 → ResNet-101 swap, COCO + PASCAL VOC.
- **Sources**: [21.2 ← VGG-16 backbone COCO mAP@[.5,.95], Table 8 [result]; 27.2 ← ResNet-101 backbone COCO mAP@[.5,.95], Table 8 [result]]
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification**: The same backbone swap fails to improve COCO mAP@[.5,.95] by ≥3 absolute points.
- **Proof**: [N12, N15]
- **Dependencies**: C03
- **Tags**: transfer-learning, object-detection
