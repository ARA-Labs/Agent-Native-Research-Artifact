# Problem

## Observations

### O1: PDF format optimized for human persuasion, not machine execution
- **Statement**: The CS research paper format has remained unchanged for decades, encoding knowledge in persuasive prose rather than structured, executable form.
- **Evidence**: Section 1 (Introduction)
- **Implication**: AI agents reverse-engineering experimental logic from narrative prose waste context tokens and hallucinate when implicit assumptions are unstated.

### O2: Reproducibility crisis is acute in ML
- **Statement**: Over 70% of researchers have failed to reproduce another scientist's experiments; fewer than 30% of ML papers can be independently reproduced even with code and data sharing mandates.
- **Evidence**: Baker 2016, Pineau 2021
- **Implication**: The root cause is format-level: papers are designed for persuasion, not specification.

### O3: Frontier LLMs fail on research implementation
- **Statement**: Even the strongest frontier LLMs correctly implement fewer than 40% of novel research contributions when given the full paper and codebase, with semantic misalignment as the dominant failure mode.
- **Evidence**: ResearchCodeBench (Hua et al. 2025)
- **Implication**: The information encoding in PDFs is structurally inadequate for agent consumption.

### O4: PDF information gap is systematic
- **Statement**: Across 23 PaperBench papers (8,921 rubric requirements), only 45.4% of reproduction requirements are fully specified in the PDF; 50.2% receive partial coverage and 4.4% are entirely absent. The gap is largest for code development (37.3% sufficient) and smallest for result analysis (60.6% sufficient). Missing hyperparameters (26.2%), vague descriptions (21.9%), and cross-reference-only specifications (13.4%) account for 61% of all gaps.
- **Evidence**: Own experiment — code/eval/results/info_gap_aggregate.json, 23 papers, 8,921 requirements
- **Implication**: The PDF format is structurally incapable of serving as a self-contained reproduction specification; the gap is systematic across subfields and requirement types.

## Gaps

### G1: No format jointly structures scientific logic, executable code, and decision history
- **Statement**: Existing approaches (FAIR, RO-Crate, Nanopublications, AGENTS.md) each address one dimension but none jointly solve structured logic + minimal executable code + preserved decision history.
- **Caused by**: O1, O2, O3
- **Existing attempts**: FAIR principles, RO-Crate, Nanopublications, AGENTS.md, S2ORC, OpenAlex
- **Why they fail**: FAIR addresses metadata not arguments; RO-Crate treats artifacts as archival bundles; Nanopublications lack execution semantics; AGENTS.md covers code repos but not epistemic structure.

### G2: Negative knowledge is systematically discarded
- **Statement**: Dead ends, rejected hypotheses, and convergence-critical tricks are lost to the narrative compression of the publication process.
- **Caused by**: O1
- **Why it matters**: Downstream agents waste compute re-exploring paths already proven fruitless.

## Key Insight
- **Insight**: Separate research knowledge into four orthogonal layers — structured scientific logic (Cognitive Layer /logic), minimal executable code (Physical Layer /src), preserved decision history (Exploration Graph /trace), and raw empirical results (Evidence Layer /evidence) — to create a machine-executable knowledge package that eliminates both the Storytelling Tax and Engineering Tax.
- **Derived from**: O1, O2, O3, O4, G1, G2
- **Enables**: Agent-native research artifacts that compound over time; each layer is independently queryable via standard tool calls without parsing prose or reverse-engineering repositories.

## Assumptions
- A1: Frontier LLMs have sufficient context windows (128k+) to process full papers in a single pass for ingestion.
- A2: Coding agents (Claude Code, Cursor) are the primary consumers of research artifacts.
- A3: The community will adopt structured formats if the tooling barrier is sufficiently low.
- A4: Machine-verifiable reproducibility is a higher priority than human readability for the primary artifact.
