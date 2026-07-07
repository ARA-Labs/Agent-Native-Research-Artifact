# Related Work

Typed dependency graph. Each entry uses one of three dependency types:
- **imports**: ARA inherits a definition, framework, or methodology from this work
- **bounds**: This work establishes a constraint or baseline that ARA's claims must satisfy or surpass
- **baseline**: Direct performance comparison in evaluation

## Machine-Readable Research Artifacts

### FAIR Principles (Wilkinson et al. 2016)
- **Type**: imports
- **What**: Findable, Accessible, Interoperable, Reusable metadata standards for scientific data
- **How ARA extends**: FAIR addresses metadata formats, not scientific arguments or executable logic. ARA imports the FAIR principle of machine-readability and extends it to cover structured reasoning, executable code, and decision history within a single protocol.

### Nanopublications (Groth et al. 2010)
- **Type**: imports
- **What**: Atomic claim decomposition with provenance metadata
- **How ARA extends**: ARA's claims.md inherits atomic claim structure and provenance tagging (user / ai-suggested / ai-executed / user-revised). Extension: ARA adds execution semantics and cross-layer bindings absent from nanopublications.

### RO-Crate (Soiland-Reyes et al. 2022)
- **Type**: imports
- **What**: Self-describing research object bundles with linked metadata
- **How ARA extends**: ARA's file-system ontology imports the self-describing bundle concept. Extension: RO-Crate treats artifacts as archival; ARA is agent-interactive with live updating and progressive disclosure.

### "Stop Writing Papers" (Canini 2026)
- **Type**: imports
- **What**: Argues the paper format is a "compression format for human readers" that should yield to structured knowledge objects
- **How ARA extends**: ARA shares the framing but adds concrete protocol, tooling (Compiler, Live PM, Seal), and empirical evidence that structured artifacts improve agent performance.

### Discovery Engine (Baulin et al. 2025)
- **Type**: imports
- **What**: Distills publications into structured knowledge artifacts encoded in a Conceptual Tensor
- **How ARA extends**: ARA addresses the same goal but adds execution semantics (src/), decision history (trace/), and machine-verifiable reproducibility guarantees (Seal).

## Reproducibility Infrastructure

### PaperBench (Starace et al. 2025)
- **Type**: bounds + baseline
- **What**: Benchmark of 23 ML papers with expert-authored reproduction rubrics (8,921 leaf requirements); measures agent reproduction capability
- **Bounds**: ARA must not reduce reproduction fidelity vs. PDF baseline on PaperBench
- **Baseline**: Baseline agent receives paper PDF + companion GitHub repo; ARA agent receives ARA artifact only; difficulty-weighted score is primary metric
- **Key finding from prior work**: Even frontier models cannot recover knowledge that PDFs leave implicit

### RE-Bench (Wijk et al. 2025) / METR MALT
- **Type**: bounds + baseline
- **What**: 7 R&D hill-climbing tasks with automated scoring; 24,008 agent run transcripts with documented failure episodes
- **Bounds**: ARA must outperform polished-summary baseline (trace stripped) on majority of tasks
- **Baseline**: Baseline receives problem statement and best-known score; ARA receives full artifact including trace layer
- **Key finding from prior work**: 73.4% failure rate on RE-Bench; failed runs consume 113× more tokens than successful ones (median)

### ResearchCodeBench (Hua et al. 2025)
- **Type**: bounds
- **What**: Benchmark measuring LLM implementation accuracy on novel research contributions
- **Bounds**: Establishes the baseline: frontier LLMs implement < 40% of contributions correctly from PDF; ARA should improve this
- **Dependency target**: C01 (Storytelling Tax claim)

### EXP-Bench (Kon et al. 2025)
- **Type**: bounds
- **What**: Agents achieve only 0.5% end-to-end success on real experiment tasks despite 20-35% component accuracy
- **Bounds**: Confirms that unstructured PDFs are a bottleneck; ARA's structured format should close this gap

### SciCoQA (Baumgartner et al. 2026)
- **Type**: bounds
- **What**: Best LLMs detect fewer than 46% of paper-code discrepancies
- **Bounds**: ARA's Seal verification must outperform unstructured LLM checking; Level 2 (fidelity) provides structural mechanism for verification

## Negative Knowledge and Failed Trajectories

### AgentErrorBench (Zhu et al. 2025) / AgenTracer (Zhang et al. 2025)
- **Type**: imports
- **What**: Failure traces become actionable when annotated with root-cause taxonomies and counterfactual step-savings
- **How ARA extends**: ARA's dead_end node schema (hypothesis, failure_mode, lesson) directly instantiates this taxonomy. Extension: ARA encodes this at authoring time; AgentErrorBench operates post-hoc on existing transcripts.

### HPO-B / NAS-Bench / OpenML
- **Type**: bounds
- **What**: Retain >99.99% more search history than corresponding papers report
- **Bounds**: Establishes scale of publication-time information loss; ARA's trace layer should recover this knowledge for agent use

### AI Scientist v2 (Yamada et al. 2025)
- **Type**: bounds
- **What**: Confirms that agentic scientists explore extensive dead ends that never surface in final write-up
- **Bounds**: Validates the framing of the Storytelling Tax at the research-process level

## Agent-Oriented Tooling

### AGENTS.md (OpenAI 2025) / Codified Context (Vasilopoulos 2026)
- **Type**: imports
- **What**: Structured, layered representations (repository-level guidance, three-tier memory) outperform flat documentation for agent consumption
- **How ARA extends**: ARA imports the layered representation principle and extends it from repository-level to research-process-level, adding cognitive and evidence layers absent from AGENTS.md

### Voyager (Wang et al. 2023) / Agent Skills Standard (2025)
- **Type**: imports
- **What**: Agent skill libraries compound over time; NL skill specifications are preferred over programmatic APIs
- **How ARA extends**: ARA's Live Research Manager adopts NL skill specification as its agent-facing interface; the skill pattern is imported directly

### PaperCoder (Seo et al. 2025)
- **Type**: baseline
- **What**: Multi-agent pipeline converting papers into runnable repositories; outperforms baselines on PaperBench
- **Relationship**: Complementary: PaperCoder targets code generation without structuring epistemic content; ARA structures the epistemic content and decision history that PaperCoder does not capture

### xKG (Luo et al. 2025)
- **Type**: baseline
- **What**: Technique-code extraction from background literature for up to 10.9% PaperBench gains
- **Relationship**: xKG extracts knowledge from background literature; ARA structures the target contribution's own decision history and epistemic content. Complementary, not competing.

### ScienceClaw (Wang et al. 2026)
- **Type**: imports
- **What**: Independently operating agents achieve emergent convergence through an artifact layer preserving computational lineage as a DAG
- **How ARA relates**: Validates ARA's core premise: structured, machine-readable artifacts, not natural-language papers, are the natural unit of exchange for agent-driven science

## Verification and Provenance

### AAR (Rasheed et al. 2026) / DecMetrics (Huang et al. 2025) / AIBOM (Radanliev et al. 2026)
- **Type**: imports
- **What**: AAR defines provenance coverage, soundness, and contradiction transparency; DecMetrics scores claim decomposition quality; AIBOM advocates cryptographic provenance
- **How ARA extends**: ARA's Seal Certificates operationalize all three dimensions: L1 (structural = AAR provenance coverage), L2 (fidelity = DecMetrics claim verification), L3 (execution = directional reproducibility with cryptographic binding potential)
