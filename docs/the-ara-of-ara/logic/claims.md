# Claims

## C01: Storytelling Tax is the binding constraint on agentic research
- **Statement**: The rhetorical structure of PDF papers (narrative arcs, hedged language, scattered details) forces agents to reverse-engineer experimental logic from prose, consuming context tokens and causing hallucination — this is the binding constraint on autonomous discovery.
- **Status**: hypothesis
- **Provenance**: user
- **Falsification criteria**: Show that agents achieve equivalent research task performance on PDFs as on structured formats.
- **Proof**: [evidence/README.md → ResearchCodeBench]
- **Dependencies**: []
- **Tags**: motivation, storytelling-tax

## C02: Engineering Tax compounds the Storytelling Tax
- **Statement**: Research repositories conflate novel contributions with environmental scaffolding (data loaders, distributed training wrappers, CI scripts), forcing agents to excavate codebases before reaching the novel contribution.
- **Status**: hypothesis
- **Provenance**: user
- **Falsification criteria**: Show that agents can reliably identify and extract novel contributions from raw repositories without structured guidance.
- **Proof**: [qualitative analysis, Section 2]
- **Dependencies**: [C01]
- **Tags**: motivation, engineering-tax

## C03: ARA's four-layer architecture eliminates both taxes
- **Statement**: The separation into Cognitive Layer (/logic), Physical Layer (/src), Exploration Graph (/trace), and Evidence Layer (/evidence) provides a machine-executable knowledge package that eliminates both the Storytelling Tax and Engineering Tax.
- **Status**: hypothesis
- **Provenance**: user
- **Falsification criteria**: Show that agents perform no better on ARA than on PDF+Code for execution tasks.
- **Proof**: [pending — Tier 3 eval]
- **Dependencies**: [C01, C02]
- **Tags**: core-contribution, protocol

## C04: Universal Ingestor produces lossless transformations
- **Statement**: The LLM-based Ingestor faithfully transforms PDF papers into ARA format without information loss, achieving near-parity on factual Q&A between ARA and source PDF.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: Systematic accuracy drop (>5%) on understanding questions from ARA vs. PDF.
- **Proof**: [evidence/README.md → understanding_eval; 450 Qs across Cat A/B/C]
- **Dependencies**: [C03]
- **Tags**: ingestor, fidelity

## C05: ARA unlocks execution capabilities PDFs cannot support
- **Statement**: ARA's structured code, configurations, and negative knowledge enable coding agents to reproduce research more effectively than PDF+GitHub, with advantages concentrated on harder tasks requiring configuration details and dependency specifications that PDFs systematically underspecify.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: No statistically significant improvement in execution success rate or difficulty-weighted score across 15 papers.
- **Proof**: [evidence/README.md → reproduction_eval; 15 papers, 150 tasks, 1,743 rubric requirements]
- **Dependencies**: [C03, C04]
- **Tags**: core-contribution, execution

## C06: Negative knowledge is the highest-value signal
- **Statement**: The Exploration Graph's dead-end documentation produces the largest accuracy gap in the entire evaluation — agents with failure traces answer questions about failed approaches that narrative formats make structurally unanswerable.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: Dead-end documentation produces no measurable improvement on failure-knowledge questions (Cat C); gap <10pp.
- **Proof**: [evidence/README.md → understanding_eval Cat C; evidence/README.md → extension_eval]
- **Dependencies**: [C05]
- **Tags**: exploration-graph, negative-knowledge

## C07: ARA Seal provides machine-verifiable reproducibility guarantees
- **Statement**: The three-level Seal (structural integrity, argumentative rigor, execution reproducibility) provides progressive verification that can serve as both a review gate and a structured evaluation interface for compiled artifacts.
- **Status**: hypothesis
- **Provenance**: user
- **Falsification criteria**: Seal checks fail to detect malformed or inconsistent artifacts, or produce excessive false positives.
- **Proof**: [pending — Tier 1 eval]
- **Dependencies**: [C03]
- **Tags**: seal, verification

## C08: Live PM makes born-agent ARA practical
- **Statement**: The Live Research Project Manager, implemented as an agent skill, captures research decisions, dead ends, and evidence as side-effects of the coding process, producing a growing ARA that is nearly complete by submission time.
- **Status**: hypothesis
- **Provenance**: user
- **Falsification criteria**: The Live PM fails to capture significant research events or requires excessive researcher overhead.
- **Proof**: [trace/ — this paper's own artifact as proof-of-concept; 94 nodes, 36 sessions]
- **Dependencies**: [C03]
- **Tags**: live-pm, born-agent

## C09: PDF information gap is systematic across PaperBench
- **Statement**: The median PaperBench paper covers only 45% of its own reproduction requirements with concrete detail; 50% are partially specified and 4% are entirely absent.
- **Status**: supported
- **Provenance**: user
- **Falsification criteria**: Median coverage exceeds 80%.
- **Proof**: [evidence/README.md → info_gap_aggregate; 23 papers, 8,921 requirements]
- **Dependencies**: [C01]
- **Tags**: motivation, information-gap, paperbench

## C10: Results are format-driven, not model-specific
- **Statement**: Tier 2 fidelity and Tier 3 capability gaps are consistent across three frontier LLM families, confirming they are properties of the format.
- **Status**: hypothesis
- **Provenance**: user
- **Falsification criteria**: One model family shows dramatically different results, suggesting model-specific confounds.
- **Proof**: [pending — multi-model eval]
- **Dependencies**: [C04, C05]
- **Tags**: evaluation, robustness

## C11: The gap follows an operational hierarchy
- **Statement**: Papers describe results best (Result Analysis: 60.6% sufficient), then execution (Code Execution: 50.5%), and development tasks worst (Code Development: 37.3%). The more operational a requirement, the less likely the PDF covers it.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: Code Development requirements are equally or better covered than Result Analysis.
- **Proof**: [evidence/README.md → info_gap_aggregate by_task_category]
- **Dependencies**: [C09]
- **Tags**: motivation, information-gap, storytelling-tax

## C12: Three gap types account for 61% of all information gaps
- **Statement**: Missing hyperparameters (26.2%), vague descriptions (21.9%), and cross-reference-only specifications (13.4%) account for 61.5% of all non-sufficient requirements. All three are structurally addressed by ARA's layered format.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: Distribution is uniform across gap types (no dominant cluster).
- **Proof**: [evidence/README.md → info_gap_aggregate gap_distribution]
- **Dependencies**: [C09, C03]
- **Tags**: motivation, information-gap, ara-value-prop

## C13: 59% of agent compute is exploration waste
- **Statement**: Across 24,008 agent runs on METR's evaluation suite (21 models, 228 tasks), 59.2% of total tokens and 90.2% of dollar cost go to failed exploration. Waste concentrates on the most research-like workloads.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: Reanalysis shows waste below 30%, or waste is primarily from fatal errors rather than genuine dead-end exploration.
- **Proof**: [evidence/README.md → exploration_tax_findings]
- **Dependencies**: [C01, C06]
- **Tags**: motivation, exploration-waste, metr-data

## C14: Failed agent runs consume disproportionate resources
- **Statement**: Failed runs consume a median of 113x more tokens than successful ones (506K vs 4.5K at P50). For tasks requiring >1 hour of human effort, 96-98% of compute cost goes to failed exploration.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: Token ratio between failed and successful runs is <5x at median, or the asymmetry is explained by task selection bias.
- **Proof**: [evidence/README.md → exploration_tax_findings]
- **Dependencies**: [C13, C06]
- **Tags**: motivation, exploration-waste, dead-ends

## C15: A skill (NL specification) is the right agent interface for research artifacts
- **Statement**: A natural language skill document replaces a fixed programmatic API as ARA's agent-facing interface. Because research interaction is open-ended, a predetermined API either constrains the action space or bloats into a general-purpose shell. A skill is extensible without code changes, composable with any agent framework, and improvable as LLMs advance.
- **Status**: hypothesis
- **Provenance**: user
- **Falsification criteria**: Show that agents perform better with a fixed API than with a skill-based interface on diverse research tasks.
- **Proof**: [qualitative argument in §3 and §4; trace/ — this paper's PM skill as proof-of-concept]
- **Dependencies**: [C08, C03]
- **Tags**: core-contribution, skill-as-interface, protocol

## C16: Three-layer evaluation captures the full ARA value proposition
- **Statement**: Evaluating ARA across understanding, reproduction, and extension isolates three progressively stronger claims and covers the full spectrum from passive comprehension to active research acceleration. Each layer measures a distinct, non-redundant signal.
- **Status**: supported
- **Provenance**: user
- **Falsification criteria**: One or more layers fails to show meaningful ARA advantage, or the layers are redundant.
- **Proof**: [evidence/README.md → understanding_eval, reproduction_eval, extension_eval]
- **Dependencies**: [C03, C04, C05, C06]
- **Tags**: evaluation, experimental-design
