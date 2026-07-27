# Heuristics

## H04: Use bottleneck blocks (1×1 → 3×3 → 1×1) once depth exceeds ~50 layers
- **Rationale**: A 3-layer bottleneck block has the same per-block time complexity as a 2-layer 3×3 block but lets the 3×3 operate on a low-dimensional bottleneck. This makes 50/101/152-layer ResNets tractable at FLOPs comparable to a 34-layer non-bottleneck (3.8 vs. 3.6 GFLOPs at 50 layers).
- **Sensitivity**: high — at large depths, dropping bottlenecks would substantially raise compute and memory.
- **Bounds**: Use only with identity shortcuts on the high-dimensional ends; replacing those identities with projections doubles complexity and model size.
- **Code ref**: [src/execution/residual_block.py](../../src/execution/residual_block.py)
- **Source**: §"Deeper Bottleneck Architectures"; Fig. 5; Table 1.
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — Agree this is the right call past 50 layers; the FLOPs comparison against the 34-layer non-bottleneck (3.8 vs. 3.6 GFLOPs) is a concrete number, not a rule-of-thumb hand-wave.
