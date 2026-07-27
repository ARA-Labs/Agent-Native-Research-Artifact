# Claims

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
