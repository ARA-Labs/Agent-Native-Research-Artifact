---
title: "Agent-Native Research Artifacts"
authors: ["Amber Liu", "Zechen Zhang"]
venue: "NeurIPS 2026"
status: draft
date_created: "2026-03-12"
last_updated: "2026-04-27"
abstract: >
  We propose the Agent-Native Research Artifact (ARA), a file-system protocol
  that replaces the narrative paper with a machine-executable research package
  organized across four interlocking layers: a Cognitive Layer (/logic)
  encoding structured scientific reasoning, a Physical Layer (/src) containing
  the executable code kernel, an Exploration Graph (/trace) preserving the
  full branching research trajectory including dead ends, and an Evidence
  Layer (/evidence) grounding every claim in raw empirical results. PDF
  publication imposes two structural costs on autonomous research: a
  Storytelling Tax (failed experiments and rejected hypotheses are discarded
  to fit a linear narrative) and an Engineering Tax (the gap between
  reviewer-sufficient prose and agent-sufficient specification leaves critical
  implementation details unwritten). On PaperBench and RE-Bench, ARA raises
  question-answering accuracy from 72.4% to 93.7% and reproduction success
  from 57.4% to 64.4%; on RE-Bench's five open-ended extension tasks, the
  failure traces preserved in ARA accelerate research progress by helping the
  agent avoid pitfalls prior runs already mapped, but for a sufficiently
  capable model the same recorded playbook can constrain a more creative
  agent that would otherwise step outside the prior-run box.
layers:
  logic: logic/
  src: src/
  trace: trace/
  evidence: evidence/
  staging: staging/
---

# Layer Semantics

| Layer | Role | Updated by |
|-------|------|------------|
| `logic/` | Current understanding — claims, experiments, heuristics. Updated at milestones when understanding crystallizes. | Live PM at milestones |
| `src/` | Executable code kernel — eval pipelines, extension harness, Seal verifier. Curated subset of the working repo's `code/`. | Live PM at milestones |
| `evidence/` | Accumulated measurements — all real numbers from all runs, append-only. Never deleted. | Live PM after every experiment |
| `trace/` | Full history — every decision, experiment, dead end, pivot since project start. Append-only. | Live PM every session |
| `staging/` | Unclassified observations awaiting promotion. Reviewed by Maturity Tracker. | Live PM every session |

> Note: `src/` holds this paper's own experiment code (~6.6MB, 281 files) trimmed from the ~1.4GB working repo — cloned baseline repos (`repos/`), downloaded PDF corpus (`pdfs/`), generated eval-run blobs (results/logs/checkpoints, all >1MB regenerable data already excluded by the working repo's own `.gitignore`), and superseded artifact backups were left out as noise, not signal. The agent-facing skill implementations (ingestor, PM) still live in `.agents/skills/` outside this artifact, since skills are shared infrastructure rather than this paper's own experiment code.
>
> Curation also removed 3 stale/dangerous files caught after the initial trim: a one-off script with a hardcoded live API key and non-portable paths (`run_bbox_api_eval.py`), a single-paper pilot script superseded by the general-purpose `run_reproduction.py` (`run_stochastic_interpolants_pilot.py`), and the blinded A/B judging script explicitly discarded in favor of absolute-correctness scoring per the exploration trace (`run_ab_eval.py`). Conversely, the dual-source question-generation pipeline the trace credits with the paper's final numbers (`generate_catA_dual.py`, `generate_catB_questions.py`, `generate_catC_questions.py`, `run_question_generation.py`, `batch_reingest.py`) had been deleted from the working repo's main branch (commit `b6a3df3` and `36df6c2`) and only survived in git history — recovered here via `git show 84083d5:...` from the last commit before deletion, superseding the single-source `generate_questions.py` that was left in its place.

# Layer Index

- **Cognitive** (`logic/`): structured scientific reasoning
  - `problem.md` — observations, gaps, key insight
  - `claims.md` — 16 falsifiable claims with status and proof pointers
  - `experiments.md` — verification plan (E1-E6)
  - `related_work.md` — typed citation dependency graph
  - `solution/heuristics.md` — 23 design decisions with rationale and sensitivity
- **Physical** (`src/`): executable code kernel (~7MB curated from ~1.4GB working repo)
  - `seal/` — ARA Seal verifier (L1 structural checks)
  - `eval/` — understanding/reproduction/extension eval pipelines, question generation, info-gap and MALT analysis scripts
  - `extension-harness/` — SDK harness, per-task scoring, SLURM templates, plot scripts for the extension-from-reference evals
  - `rebench-pipeline/` — RE-Bench ARA-building pipeline and task specs
  - `utils/`, `scripts/`, `send.py`, `requirements.txt` — shared utilities and entry points
- **Exploration** (`trace/`): full branching research trajectory
  - `exploration_tree.yaml` — 114-node decision DAG (decisions, experiments, dead ends)
  - `sessions/` — 38 session logs (2026-03-12 to 2026-04-26); see `session_index.yaml` for the chronological summary
  - `pm_reasoning_log.yaml` — Live PM reasoning trace
- **Evidence** (`evidence/`): raw empirical results
  - `README.md` — index of all evaluation data and file pointers, including the post-paper extension-from-reference cross-model rebench evals (sonnet-4-5 / 4-6, paper vs ara) and pointers to `code/extension-harness/` (the de-facto src layer for those evals)
- **Staging** (`staging/`): unpromoted observations awaiting crystallization
  - `observations.yaml` — 94 preliminary observations (latest O89-O94: 2026-04-26 subagent-tmp scoring source, nanogpt pushback-ceiling exhaustion as failure mode, MLM cross-model flip mechanism via documented-option currency, clean-attribution methodology, cross-task synthesis on ARA help-mechanism diversity, independent-rediscovery as evidence pattern)
