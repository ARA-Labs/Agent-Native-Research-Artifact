# Scaffolding GPT-3.5 for Competitive Programming in Rust

## Problem

Build a scaffolding system that uses GPT-3.5-turbo-0125 to solve competitive programming problems in Rust. The system is evaluated on 175 problems, and scored by the fraction of problems solved correctly.

**Constraints:**
- Model: GPT-3.5-turbo-0125 via OpenAI API only (no other models).
- Budget: $500 OpenAI API credits.
- No GPU access (CPU-only execution environment: 20 CPUs, 100 GB RAM).
- Evaluation time: ~8 minutes per full run on 175 problems.
- Starting code: ~746 LOC basic structure, no error handling.
- Sample test cases are available for each problem.
- Scoring: fraction of 175 problems solved. Starting score: 0.00. Reference solution score: 0.13.

## Method

The core insight is that the bottleneck is generating compilable Rust code, not algorithmic reasoning. GPT-3.5 produces Rust code that compiles on the first attempt less than 15% of the time, mainly due to ownership, borrowing, and type system errors. The approach uses a generate-compile-test-retry loop with multi-candidate generation.

**Per-problem pipeline:**

1. **Budget Manager.** Allocate ~$2.30 per problem ($500 / 175 ≈ $2.86, with safety margin). In practice, actual cost is ~$0.05/problem — the binding constraint is wall-clock evaluation time, not API cost.

2. **Prompt Constructor.** Format the problem statement with Rust-specific instructions: explicit type annotations, proper I/O handling (`std::io`), and common Rust patterns for competitive programming.

3. **Multi-Candidate Generation (M = 3).** Generate 3 independent solution candidates per problem to increase coverage.

4. **Compile-Retry Loop (N = 5 per candidate).** For each candidate:
   - Generate initial code via GPT-3.5.
   - Attempt compilation with `rustc`.
   - If compilation fails, feed the compiler error message back to GPT-3.5 and request a fix.
   - Repeat up to N = 5 times.
   - This raises compilation success rate from ~15% to ~60--70%.

5. **Test Runner.** Execute each compiling candidate against the sample test cases. Record pass/fail for each test case.

6. **Candidate Selector.** Select the candidate that passes the most sample test cases. Submit that solution.

**Complexity:** Worst case 18 API calls per problem (3 candidates × (1 initial + 5 retries)). At ~$0.017/candidate, total cost ~$8.93 — well within budget.

## Results

The generate-compile-test-retry pipeline with M = 3 candidates achieves a solve rate of approximately 13% (score 0.13), matching the reference solution.

**Component ablation:**

| Configuration | Solve Rate |
|---|---|
| Zero-shot (single attempt, no retry) | ~0% |
| + Compilation feedback (N=5 retries) | ~6% |
| + Rust-specific prompt hints | ~8% |
| + Sample test validation | ~10% |
| + Multi-candidate (M=3) | ~13% |

**Human baselines (14 participants):** Scores range from 0.00 to 0.13. Three domain experts scored 0 (indicating the task is genuinely difficult). Mean 0.050, median 0.045. Our ~0.13 matches the best human participant.
