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
