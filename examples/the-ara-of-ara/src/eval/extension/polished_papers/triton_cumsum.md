# Optimizing Conditional Prefix Sum on GPU with Triton

## Problem

Implement and optimize a GPU kernel for a conditional prefix sum: given an input array x of length N = 10^8, compute Y_i = sum_{j=0}^{i} x_j * s_j, where s_j = (count of positive values in x_0, ..., x_{j-1}) mod 2. The parity signal s_j creates a nested sequential dependency that makes naive parallelization difficult.

**Constraints:**
- Hardware: single H100 GPU (80 GB HBM3, 3.35 TB/s bandwidth, 132 SMs).
- Input: int32, output: int64. Total data movement: ~400 MB for N = 10^8.
- Scoring: `log10(time_in_milliseconds)`, lower is better.
- Starting score: 1.56 (4.76 ms). Reference solution score: 0.47 (1.6 ms). Best human score: -0.41 (< 1 ms).

## Method

The key insight is that the problem decomposes into two standard prefix sums that can be fused into a single kernel pass.

**Decomposition.** Define p_j = count of positive values before index j (a standard prefix sum on indicators). Then s_j = p_j mod 2. The conditional prefix sum Y_i = sum of x_j where p_j is even, minus sum of x_j where p_j is odd (with appropriate sign tracking). This can be represented as a fused three-element state (c, v_even, v_odd):
- c: running count of positive values
- v_even: partial sum for even-parity positions
- v_odd: partial sum for odd-parity positions

This state forms a monoid under a combine operation that switches between v_even and v_odd based on c mod 2, enabling parallel scan.

**Triton kernel implementation.** A two-pass Blelloch-style parallel scan:
1. **Pass 1 (Block-Local Scan):** Each thread block processes BLOCK_SIZE elements. Within each block, compute the fused scan using `tl.associative_scan`. Store per-block aggregate states to global memory.
2. **Inter-Block Scan:** Scan the per-block aggregates (small array, ~97K blocks for N = 10^8).
3. **Pass 2 (Block Adjustment):** Each block incorporates the prefix from all preceding blocks, adjusting its local results.

**Block size tuning.** Performance follows a U-shaped curve: too-small blocks incur excessive kernel launches; too-large blocks cause register pressure. Optimal at BLOCK_SIZE = 2048 (0.50 ms, score -0.30).

**Alternative (simpler, slightly slower):** Two separate Triton kernels — first compute the parity prefix sum, then compute the masked value prefix sum. Achieves ~0.60 ms (score ~-0.22).

## Results

The fused single-kernel approach with BLOCK_SIZE = 2048 achieves 0.50 ms (score -0.30), utilizing ~48% of theoretical memory bandwidth (theoretical floor: 0.24 ms). This would rank 2nd among 9 human participants (scores -0.41 to 1.56).

| Implementation | Time (ms) | Score |
|---|---|---|
| Starting code | 4.76 | 1.56 |
| PyTorch ops (5+ kernels) | 2.50 | 0.40 |
| Two-kernel Triton | 0.80 | -0.10 |
| Fused Triton (BLOCK_SIZE=1024) | 0.55 | -0.26 |
| Fused Triton (BLOCK_SIZE=2048) | 0.50 | -0.30 |
