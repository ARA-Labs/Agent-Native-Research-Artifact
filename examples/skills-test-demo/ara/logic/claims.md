# Claims

## C01: Plain CNNs exhibit a depth-induced degradation problem
- **Statement**: For sufficiently deep "plain" CNNs (no shortcuts), increasing depth strictly increases *training* error on both CIFAR-10 and ImageNet, even with BN and competent initialization.
- **Status**: supported
- **Falsification criteria**: A controlled depth scan (e.g. plain-{18, 34, 56, 110}) trained with BN and standard SGD in which deeper models show monotonically lower or equal training error.
- **Proof**: [E01]
- **Evidence basis**: Table 2 (plain-18 = 27.94%, plain-34 = 28.54% top-1 ImageNet val); Fig. 4 left (training-error curves cross with deeper plain-34 above plain-18 throughout training); Fig. 6 left for plain-{20, 32, 44, 56, 110} on CIFAR-10.
- **Interpretation**: The authors argue (but do not formally prove) that this reflects an *optimization* difficulty rather than overfitting or vanishing gradients.
- **Dependencies**: none
- **Tags**: degradation, optimization, depth-scaling, plain-baseline
- **Taste** (optional):
  - [2026-07-27] `endorse` on `evidence` — Exactly the controlled comparison the falsification criteria calls for: matched training setup, depth as the only variable, training error (not just test error) reported so it isn't confoundable with overfitting.

## C02: Residual learning eliminates the degradation problem
- **Statement**: Replacing each pair of stacked 3×3 layers in a plain net with a residual block F(x) + x (with identity shortcut, no extra parameters) makes the deeper variant achieve *lower* training and validation error than the shallower one for matched depths.
- **Status**: supported
- **Falsification criteria**: Under the same depth/width/training pipeline, ResNet-34 fails to improve over ResNet-18 on ImageNet validation, or ResNet-34 has higher training error than plain-34.
- **Proof**: [E01, E02]
- **Evidence basis**: Table 2 (ResNet-18 = 27.88, ResNet-34 = 25.03 top-1 ImageNet val; ResNet-34 better than ResNet-18 by 2.85 pts; ResNet-34 better than plain-34 by 3.51 pts); Fig. 4 right (training-error curves of ResNet-34 lie below ResNet-18 throughout training).
- **Interpretation**: The result is consistent with the hypothesis that residual reformulation makes the optimization landscape easier to traverse, but does not by itself prove a representational advantage.
- **Dependencies**: C01
- **Tags**: residual-learning, identity-shortcut, optimization
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — This is the paper's core result and the evidence basis is about as clean as this kind of comparison gets: matched depth, matched pipeline, both training and validation error move the same direction.

## C03: Residual networks gain accuracy from increased depth up to 152 layers on ImageNet
- **Statement**: Deeper ResNets (50, 101, 152) achieve monotonically lower top-1 and top-5 ImageNet validation error than shallower ResNets, with the 152-layer model still having lower complexity (11.3 GFLOPs) than VGG-16/19 (15.3/19.6 GFLOPs).
- **Status**: supported
- **Falsification criteria**: A ResNet-152 trained with the same recipe fails to improve top-1 over ResNet-101 (or ResNet-101 over ResNet-50) by a margin larger than the noise floor (~0.1%).
- **Proof**: [E03]
- **Evidence basis**: Table 3 (ResNet-50 = 22.85 / 6.71, ResNet-101 = 21.75 / 6.05, ResNet-152 = 21.43 / 5.71 top-1 / top-5 with 10-crop testing; FLOPs from Table 1).
- **Interpretation**: Within the depths studied, depth alone (rather than added parameters) is the source of the gain because residual blocks add no extra parameters relative to plain counterparts.
- **Dependencies**: C02
- **Tags**: depth-scaling, imagenet, complexity

## C04: Identity shortcuts are sufficient; projection shortcuts give only marginal gains
- **Statement**: Among shortcut options A (zero-padding identity), B (projection only when dimensions change), and C (projection on every shortcut), the differences in ImageNet top-1 error are small (≤0.65 pts on ResNet-34); identity shortcuts (A) suffice to fix degradation, and option C is rejected as not worth its parameter / memory cost.
- **Status**: supported
- **Falsification criteria**: A controlled comparison in which option C beats option A or B by more than ~1 top-1 point under identical training, indicating projection shortcuts are essential rather than convenience.
- **Proof**: [E04]
- **Evidence basis**: Table 3 (ResNet-34 A = 25.03, B = 24.52, C = 24.19 top-1 with 10-crop); §"Identity vs. Projection Shortcuts" attributes the small B>A gap to A's zero-padded dimensions having "no residual learning" and the small C>B gap to extra parameters from 13 projection shortcuts.
- **Interpretation**: Identity shortcuts are the right default for parameter efficiency; B is used in deeper bottleneck nets where dimension changes are rarer.
- **Dependencies**: C02
- **Tags**: shortcut-design, ablation
- **Taste** (optional):
  - [2026-07-27] `uncertain` on `evidence` — The ≤0.65pt gap is doing a lot of work here ("sufficient", "marginal", "rejected") but it's a single ImageNet run per option with no repeated-trial variance reported — that gap could plausibly be run-to-run noise rather than a real ordering between A/B/C.

## C05: Bottleneck blocks make 50/101/152-layer ResNets practical
- **Statement**: Replacing the 2-layer 3×3 building block with a 3-layer 1×1 → 3×3 → 1×1 *bottleneck* block of the same per-block time complexity allows construction of 50/101/152-layer ResNets that achieve lower error than the 34-layer ResNet without exploding compute.
- **Status**: supported
- **Falsification criteria**: A 50- or 101-layer non-bottleneck ResNet matches the bottleneck ResNet at equal compute, eliminating the practical need for bottlenecks; or bottleneck ResNets fail to improve over ResNet-34.
- **Proof**: [E03]
- **Evidence basis**: Table 1 (3.8/7.6/11.3 GFLOPs for ResNet-{50,101,152}, comparable to ResNet-34 at 3.6 GFLOPs); Table 3 top-1 error drops from 24.19 (ResNet-34 C) to 22.85 / 21.75 / 21.43 for ResNet-50/101/152.
- **Interpretation**: Identity shortcuts are particularly important for bottleneck designs because a projection shortcut on a bottleneck doubles its time complexity and model size (§"Deeper Bottleneck Architectures").
- **Dependencies**: C02, C04
- **Tags**: bottleneck, architecture, complexity

## C06: Residual nets generalize to extreme CIFAR-10 depths (110 layers; 1202 layers without optimization difficulty)
- **Statement**: On CIFAR-10, ResNets at depths {20, 32, 44, 56, 110} all train successfully, with the 110-layer model achieving 6.43% test error (best mean ± std 6.61 ± 0.16); a 1202-layer ResNet trains with no optimization difficulty (final training error <0.1%) although it overfits to 7.93% test error on this small dataset.
- **Status**: supported
- **Falsification criteria**: A CIFAR ResNet at depth ≥110 trained with the same recipe fails to converge to <10% test error, or its training error fails to decrease below the 56-layer model's.
- **Proof**: [E05]
- **Evidence basis**: Table 6 (ResNet-{20=8.75, 32=7.51, 44=7.17, 56=6.97, 110=6.43, 1202=7.93}% test error); §"Exploring Over 1000 layers" notes 1202-layer training error <0.1% with no optimization difficulty.
- **Interpretation**: The 1202-layer model worsens on test only because of overfitting on a 50k-image dataset, not because optimization breaks down.
- **Dependencies**: C02, C03
- **Tags**: cifar-10, extreme-depth, generalization, overfitting
- **Taste** (optional):
  - [2026-07-27] `uncertain` on `framing` — "Just overfitting, not optimization breakdown" is stated as settled, but the claim doesn't separate the two cleanly — there's no matched-capacity smaller model shown as a control, so low training error plus high test error is consistent with overfitting but doesn't rule out a milder optimization issue that a stronger regularizer happens to paper over.

## C07: Warming up the learning rate is necessary for the 110-layer CIFAR ResNet
- **Statement**: A 110-layer ResNet on CIFAR-10 fails to start converging cleanly with the default initial LR of 0.1; warming up at LR 0.01 for ~400 iterations until training error drops below ~80%, then restoring LR 0.1, restores convergence.
- **Status**: supported
- **Falsification criteria**: Training a 110-layer ResNet on CIFAR-10 from scratch at LR 0.1 from iteration 0 reliably reaches the same final test error as the warmup recipe under the same total budget.
- **Proof**: [E05]
- **Evidence basis**: §4.2 paragraph on n=18 (110-layer): "0.1 is slightly too large to start converging" with footnote 5 noting LR 0.1 reaches similar accuracy after several epochs of >90% error but the warmup variant is the chosen recipe.
- **Interpretation**: Warmup is a stability heuristic, not a fundamental requirement of residual learning — only a minor optimization aid for very deep CIFAR variants.
- **Dependencies**: C06
- **Tags**: training-recipe, warmup, very-deep
- **Taste** (optional):
  - [2026-07-27] `uncertain` on `framing` — Statement reads as "warmup restores convergence" (existence), but the cited footnote says LR 0.1 without warmup reaches similar accuracy eventually, just slower — that's a convergence-speed effect, not a convergence-existence one. The claim as framed overstates what the footnote supports.

## C08: ResNet representations transfer to detection, giving large COCO gains over VGG-16
- **Statement**: Replacing the VGG-16 backbone with ResNet-101 in baseline Faster R-CNN improves COCO val mAP@[.5,.95] from 21.2 to 27.2, a 6.0-point absolute (28% relative) increase, attributed solely to the better learned representations.
- **Status**: supported
- **Falsification criteria**: A controlled VGG-16 → ResNet-101 swap in Faster R-CNN with the same hyperparameters fails to improve COCO mAP@[.5,.95] by ≥3 absolute points.
- **Proof**: [E06]
- **Evidence basis**: Table 8 (baseline Faster R-CNN: VGG-16 = 41.5 mAP@.5 / 21.2 mAP@[.5,.95]; ResNet-101 = 48.4 / 27.2 on COCO val); Table 7 (PASCAL VOC 07 mAP: 73.2 → 76.4; VOC 12: 70.4 → 73.8).
- **Interpretation**: Depth of representations matters not only for classification but for downstream localization-sensitive tasks; mAP@[.5,.95] (which rewards tighter boxes) gains ≈ mAP@.5 gains, suggesting deeper features help both recognition and localization.
- **Dependencies**: C03
- **Tags**: transfer-learning, object-detection, coco, pascal-voc, faster-rcnn
