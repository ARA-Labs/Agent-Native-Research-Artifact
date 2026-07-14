# Verification Plan

Experiment logic only. Ground-truth numbers live exclusively in `../evidence/`. This file enables blind reproduction: an agent verifying directional properties should not consult evidence until after running.

## E1: Information Gap Analysis (motivates C09, C11, C12)

**Status**: completed
**Evidence output**: [evidence/README.md → Information Gap Analysis]

**Question**: Does the PDF format systematically withhold reproduction-critical information?

**Setup**: For each rubric requirement across PaperBench, classify the corresponding PDF section as sufficient / partial / absent using a structured rubric (Section: exact operationalization in Appendix).

**Prediction (directional)**: Sufficient rate < 60% overall; Code Development has lower sufficient rate than Result Analysis; missing hyperparameters, vague descriptions, and cross-reference-only specs are the dominant gap types.

**Falsification condition**: Sufficient rate > 80%, or no operational hierarchy in coverage rates.

## E2: Exploration Tax Analysis (motivates C13, C14)

**Status**: completed
**Evidence output**: [evidence/README.md → Exploration Tax Analysis]

**Question**: What fraction of agent compute is consumed by failed exploration?

**Setup**: Analyze METR eval-analysis-public runs; classify each run as successful (score > 0) or failed (score = 0); compute token and dollar cost by outcome category.

**Prediction (directional)**: Failed runs consume a disproportionate share of total tokens; token ratio failed:successful > 10× at median; waste rate is higher on open-ended research tasks than on well-defined programming tasks.

**Falsification condition**: Token ratio < 5× at median, or waste fraction < 30%.

## E3: Understanding Evaluation (tests C04, C06, C16)

**Status**: completed
**Evidence output**: [evidence/README.md → Understanding Evaluation]

**Question**: Does ARA preserve source information and surface knowledge that PDF leaves implicit?

**Setup**: 450 questions across three categories (A: fidelity, B: configuration recovery, C: failure knowledge); one ARA agent and one baseline agent per question; blinded judge scoring.

**Predictions (directional)**:
- Cat A: ARA accuracy ≥ baseline (parity threshold; ARA should not lose fidelity)
- Cat B: ARA accuracy > baseline by substantial margin (hyperparameter recovery)
- Cat C: ARA accuracy >> baseline (failure knowledge absent from baseline format)
- Token efficiency: Cat A ARA uses fewer or equal tokens per question (indexed lookup vs. linear scan)

**Falsification condition**: ARA drops >5pp vs. baseline on Cat A; no significant advantage on Cat B or C.

## E4: Reproduction Evaluation (tests C05, C16)

**Status**: completed
**Evidence output**: [evidence/README.md → Reproduction Evaluation]

**Question**: Does ARA enable higher reproduction success than PDF + GitHub?

**Setup**: 15 PaperBench papers, 10 subtasks each (150 total), stratified by difficulty; ARA agent vs. baseline (PDF + repo); blinded judge; difficulty-weighted scoring (easy×1, medium×2, hard×3).

**Predictions (directional)**:
- ARA difficulty-weighted score > baseline overall
- Gap grows with difficulty (hard subtasks show larger advantage than easy)
- Papers with complex multi-step pipelines or non-obvious hyperparameter interactions show largest ARA advantage

**Falsification condition**: No statistically significant overall advantage; advantage does not increase with difficulty.

## E5: Extension Evaluation (tests C06, C16)

**Status**: running (6/7 tasks complete; optimize_llm_foundry pending)
**Evidence output**: [evidence/README.md → Extension Evaluation]

**Question**: Does failure knowledge in the trace layer accelerate downstream research?

**Setup**: 7 RE-Bench tasks; ARA agent (full trace) vs. baseline (trace stripped); automated scoring function; 70 dead-end nodes mined from real METR MALT transcripts.

**Predictions (directional)**:
- ARA achieves better score on majority of tasks
- Dead-end density (nodes per task) correlates with ARA advantage magnitude
- ARA agent's failed attempts overlap less with documented dead ends than baseline's (redundant exploration rate lower for ARA)

**Falsification condition**: ARA wins < 4/7 tasks; no correlation between dead-end density and advantage; baseline wins on high-density tasks.

## E6: ARA Seal Validation (tests C07)

**Status**: planned
**Evidence output**: pending

**Question**: Does the three-level Seal catch malformed or inconsistent artifacts with acceptable precision and recall?

**Setup**: Inject known errors into a set of valid ARAs (missing required fields, broken cross-references, inconsistent claims, non-reproducible numerical results); measure Seal L1/L2/L3 detection rates and false positive rate on valid artifacts.

**Predictions (directional)**:
- L1 (structural): detects all schema violations; false positive rate < 5%
- L2 (fidelity): detects >90% of information infidelity; false positive rate < 15%
- L3 (execution): detects directional claim violations; does not require exact numerical matching

**Falsification condition**: Seal fails to detect > 20% of injected errors at each level; false positive rate > 30% on valid artifacts.
