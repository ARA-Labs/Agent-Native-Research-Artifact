# Datasets & Motivation — Improvement Plan

## Current Status: MOSTLY COMPLETE

All primary data exists and is verified:
- Information gap: 23 papers, 8,921 requirements, all numbers match
- Exploration tax: 24,008 runs, all numbers match
- Tables 1-3 populated and accurate

## Improvements to Make

### 1. Clarify Token Waste vs Cost Waste (Table 3)

**Problem**: Table 3 conflates two metrics — "44.8% tokens" and "90.2% cost"
measure different things. Token waste is 59.2% (44.8 dead-end + 14.4 redundant),
cost waste is 90.2%. The discrepancy is unexplained.

**Fix**: Add a clarifying sentence after Table 3:

> The cost waste (90.2%) exceeds token waste (59.2%) because failed runs
> disproportionately involve expensive frontier models operating at maximum
> context — high per-token cost amplifies the raw token ratio.

Or restructure Table 3 to show both:
```
Metric                        | Tokens  | Cost
Dead-end exploration          | 44.8%   | --
Redundant re-discovery        | 14.4%   | --
Total waste                   | 59.2%   | 90.2%
```

### 2. Use Median Failed-to-Success Ratio

**Current**: "8.6x" (mean) — underwhelming
**Available**: Median is 112.9x — much more dramatic and robust to outliers

**Fix**: Change from:
> Failed runs consume 8.6× more tokens than successful ones

To:
> Failed runs consume a median of **112× more tokens** than successful ones
> (mean: 8.6×; the mean is pulled down by easy tasks where failures are short).

### 3. Add Per-Benchmark Breakdown

**Available data**:
- RE-Bench: 545 runs, 73.4% failure, most research-like
- HCAST: 15,176 runs, 47.0% failure, moderate difficulty
- SWAA: 8,287 runs, 0.7% failure, well-defined tasks

**Fix**: Add one sentence:
> The waste concentrates where research happens: RE-Bench tasks fail 73.4%
> of the time compared to 0.7% for well-defined SWAA tasks, with HCAST (47.0%)
> representing the middle ground.

### 4. Mention Annotation Confidence (Brief)

**Data**: 63.9% high confidence, 35.8% medium, 0.2% low

**Fix**: Add to the information gap paragraph:
> (Annotation confidence: 64% high, 36% medium, <1% low; see
> Appendix~\ref{app:eval-details} for methodology.)

### 5. Optional: Fine-Grained Category Mini-Table

The most dramatic gap types tell a compelling story. Could add as a supplement
to Table 1 or move to appendix:

```
Fine-Grained Category              | Sufficient | Partial | Absent
Dataset & Model Acquisition        | 5.4%       | 69.1%   | 25.5%
Evaluation, Metrics & Benchmarking | 30.0%      | 64.7%   | 5.3%
Logging & Monitoring               | 33.3%      | 55.6%   | 11.1%
Environment & Setup                | 65.7%      | 31.6%   | 2.7%
Data Processing & Pipeline         | 66.9%      | 32.0%   | 1.2%
```

**Decision**: This may be too detailed for the main text. Could go in appendix
and be referenced with one sentence in the main text.

## What NOT to Change

- Table 1 (info gap by task category): solid, keep as-is
- Table 2 (gap type distribution): solid, keep as-is
- ARA generation paragraph: clear and sufficient
- Baseline paragraph: well-articulated
- Overall structure and narrative flow: strong

## Implementation

These are small edits to paper/sections/evaluation.tex, lines ~95-125.
Estimated effort: 20 minutes of targeted editing.
