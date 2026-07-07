# Heuristics

## H01: Data over Narrative as the core design principle
- **Rationale**: Structured logic and executable evidence are the primary research object; the narrative paper is a compiled view. This eliminates the Storytelling Tax by encoding all knowledge as typed, queryable data.
- **Provenance**: user
- **Sensitivity**: high
- **Code ref**: [paper/sections/protocol.tex]

## H02: Progressive disclosure via 3-level context loading
- **Rationale**: Agent context windows are finite. Loading an entire artifact before determining relevance wastes tokens. L1 (~500 tokens) for relevance check, L2 for layer-level detail, L3 for full depth.
- **Provenance**: user
- **Sensitivity**: medium
- **Code ref**: [paper/sections/protocol.tex, Agent Skills standard]

## H03: Kernel vs. Repository mode based on contribution type
- **Rationale**: Algorithmic contributions can be cleanly separated from scaffolding (Kernel mode); systems contributions where engineering IS the contribution require full annotated codebase (Repository mode). One size does not fit all.
- **Provenance**: user
- **Sensitivity**: high
- **Code ref**: [paper/sections/protocol.tex]

## H04: Directional verification over exact numerical matching
- **Rationale**: Legacy papers routinely omit details needed for exact reproduction. Verifying directional properties (A > B on metric X) demonstrates the code kernel captures the core algorithmic insight without requiring exact numerical matches that are impossible from incomplete specifications.
- **Provenance**: user
- **Sensitivity**: medium
- **Code ref**: [paper/sections/protocol.tex — Seal Level 3]

## H05: Ingestor uses LLM as sole cognitive engine (no multi-stage NLP pipeline)
- **Rationale**: A programmatic pipeline fragments the paper across processing stages, losing holistic reasoning. A single LLM with 128k+ context preserves global context for forensic binding. The I/O shell stays intentionally "dumb."
- **Provenance**: user
- **Sensitivity**: high
- **Code ref**: [code/ingestor/agent.py, code/ingestor/prompt.py]

## H06: 4-stage epistemic chain-of-thought for ingestion
- **Rationale**: Mandated structured reasoning (Semantic Deconstruction → Cognitive Mapping → Physical Stubbing → Exploration Graph Extraction) ensures each ARA layer is populated from the appropriate abstraction level and provides an auditable reasoning trace.
- **Provenance**: user
- **Sensitivity**: high
- **Code ref**: [code/ingestor/prompt.py]

## H07: Seal as both quality gate AND training signal
- **Rationale**: The Ingestor runs Seal L1 checks within its agentic loop, treating validation failures as immediate actionable feedback. The generate→validate→fix loop converges in 2-3 refinement rounds.
- **Provenance**: ai-suggested
- **Sensitivity**: medium
- **Code ref**: [code/ingestor/agent.py]

## H09: Prompt caching for batched PDF evaluation (~97% input cost savings)
- **Rationale**: When evaluating many rubric requirements against the same PDF, the PDF dominates input tokens (~50-110K per call). Anthropic's prompt caching with `cache_control: ephemeral` on the document block means the PDF is cached after the first batch call, and subsequent batches read from cache at 10% cost. For 23 papers with 8,921 total requirements, this reduced effective input cost from ~$160 to ~$5.
- **Provenance**: ai-executed
- **Sensitivity**: high
- **Code ref**: [code/eval/pdf_information_gap.py — evaluate_batch function, cache_control on document block]

## H10: Ghostscript compression for oversized arXiv PDFs
- **Rationale**: Some arXiv PDFs are 20-27MB due to uncompressed figures, exceeding API limits. `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook` reduces these to <2MB with acceptable quality loss for text extraction. bridging-data-gaps: 21.6MB→783KB, stochastic-interpolants: 27MB→1.1MB.
- **Provenance**: ai-executed
- **Sensitivity**: low
- **Code ref**: [bash: gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook]

## H11: Skill as interface — NL specification replaces predetermined API
- **Rationale**: Research interaction is open-ended; a fixed API (query/run/log/verify) cannot enumerate all useful operations without becoming too narrow or too broad. A natural language skill document teaches the agent how to interact with any conforming artifact using its existing tools (read, write, edit, run). The skill is extensible (update the document, not ship a new API version), composable (no SDK dependencies), and improvable (stronger LLMs interpret the same skill with greater nuance).
- **Provenance**: user
- **Sensitivity**: high
- **Code ref**: [.claude/skills/pm/SKILL.md, paper/sections/live_pm.tex]

## H12: Minimal kernel = algorithm notes with inline snippets, not raw code files
- **Rationale**: Full code dumps (200-700 lines) in src/kernel/ cause context dilution — the agent spends tokens parsing boilerplate that's already described in official_solution_notes.md. The notes contain the core algorithm with key code snippets inline, which is sufficient for comprehension while being 5-10x smaller. Raw .py files should be removed; agents can regenerate full implementations from notes + configs.
- **Provenance**: user-revised
- **Sensitivity**: high
- **Code ref**: [code/artifacts/rebench-*/src/kernel/official_solution_notes.md]

## H13: Context dilution creates a Cat A vs Cat C trade-off in ARA evaluation
- **Rationale**: Adding src/ content to RE-Bench ARAs improves Cat A (implementation detail retrieval: +10pp on RE-Bench) but hurts Cat C (failure knowledge retrieval: -22.5pp). The exploration tree must compete for agent attention with configs and algorithm notes. The current minimal kernel configuration (90% Cat A, 57.5% Cat C) appears to be the Pareto optimum — further trimming would recover Cat C but lose Cat A gains.
- **Provenance**: ai-suggested
- **Sensitivity**: high
- **Code ref**: [code/eval/results/understanding/understanding_eval_report.json]

## H14: 2-hop rubric-alignment as ARA-exclusive evaluation pattern
- **Rationale**: Questions requiring (1) rubric/requirements.md lookup by topic (find requirement about X) + (2) cross-reference with a specific ARA file create a structural advantage for ARA. PDF+repo agents must parse raw rubric JSON (123-789 leaf nodes, no R-number index) and have no pre-built file mapping — forcing them to search unstructured data. ARA agents have a structured R-number directory with explicit coverage file pointers. Discovery-style framing ("find the requirement about X") tests navigation ability, not just recall.
- **Provenance**: ai-suggested
- **Sensitivity**: high
- **Code ref**: [code/eval/questions/*_catB.json, code/artifacts/*/rubric/requirements.md]

## H15: Repo ingestion skip filter: binary/image/archive + cache dirs + 64KB limit
- **Rationale**: Raw GitHub repos contain large non-textual artifacts (model weights, compiled objects, images) and generated caches that consume tokens without information value. Three-tier filtering — extension-based (30+ types: .pyc, .pt, .pkl, .png, .zip, etc.), directory-based (.git, __pycache__, node_modules, dist, venv, etc.), and size-based (64KB cap) — keeps the repo footprint manageable for LLM context. The 64KB cap is set high enough to include most source files (median Python file ~3KB) while excluding accidentally committed large binaries.
- **Provenance**: ai-suggested
- **Sensitivity**: low
- **Code ref**: [code/ingestor/agent.py — _REPO_SKIP_EXTENSIONS, _REPO_SKIP_DIRS, _REPO_MAX_FILE_SIZE]

## H16: Atomic checkpoint writes and multi-level fallbacks for long-running eval harnesses
- **Rationale**: Long-running eval runs (4+ hours, 200+ turns) are routinely terminated by API connection errors, rate limits, or content filter rejections. Three defenses compound: (1) atomic .tmp-rename checkpoints after every score observation prevent total data loss even on hard crash; (2) exception-safe run() ensures _save_results() is called on all exit paths; (3) per-problem fallback generators (e.g., Claude → gpt-5-mini or vice versa) ensure content-filter rejections on individual problems don't zero out an entire scoring batch. Without all three, a single API blip can silently discard hours of compute.
- **Provenance**: user
- **Sensitivity**: medium
- **Code ref**: [code/eval/extension/run_extension.py — _save_checkpoint(), _api_call_with_retry(), run(); code/eval/extension/env/rust_codecontests/local_score.py — _generate_with_claude_fallback()]

## H17: Serial execution (max_workers=1) as the minimal-complexity 429-prevention strategy
- **Rationale**: Multiple concurrent asyncio coroutines competing for a rate-limited API create thundering-herd 429 bursts: they all back off together, then all retry together. The simplest fix is to serialize requests entirely (max_workers=1): one problem runs at a time, one API call at a time. The rate limiter still enforces MIN_INTERVAL pacing, but with queue depth ≤ 1 there is never a burst. This trades throughput for reliability — at 8 req/min, serial mode processes ~1 problem/minute on average, comparable to the burst-and-wait cycle of concurrent mode but without failures.
- **Provenance**: ai-suggested
- **Sensitivity**: medium
- **Code ref**: [code/eval/extension/results/rust_codecontests_baseline_seed10/solution_v6.py — batch_size=5, max_workers=1 in local_score.py invocation]

## H18: Use the harness's own semaphore for API rate-limiting in eval solution modules
- **Rationale**: The local_score.py harness passes an asyncio.Semaphore (value = --max_workers) to generate_solution(). Acquiring this semaphore inside every LLM call limits concurrency to exactly max_workers concurrent API calls across all problems in a batch — no custom rate limiter needed. Custom token buckets, module-level semaphores, and sleep-based throttling all fail in multi-process environments because they cannot observe sibling processes sharing the same API key. The harness semaphore, combined with backoff library retry on 429s, is both simpler and more robust.
- **Provenance**: ai-executed
- **Sensitivity**: high
- **Code ref**: [code/eval/extension/results/rust_codecontests_ara_seed10/solution_final.py, code/eval/extension/results/rust_codecontests_ara_seed10/solution_v9.py — call_llm() with async with semaphore:]

## H08: Experiments.md contains directional outcomes only, never exact values
- **Rationale**: Withholding ground-truth numbers from experiment plans enables blind reproduction — a coding agent verifies directional properties without risk of fabricating results by copying expected values. Exact data lives exclusively in /evidence/.
- **Provenance**: user
- **Sensitivity**: high
- **Code ref**: [paper/sections/protocol.tex]

## H19: Layer Semantics section is mandatory in every PAPER.md
- **Rationale**: Agents navigating an ARA without temporal layer guidance treat all layers as static equivalents. A four-row table (src/ = current, logic/ = understanding, evidence/ = accumulated, trace/ = history) gives the agent an immediate mental model in ~100 tokens before it loads anything else.
- **Provenance**: user
- **Sensitivity**: high — omitting this causes agents to over-read trace/ as current state or under-use evidence/
- **Bounds**: Must appear before the Layer Index in PAPER.md
- **Code ref**: [ara/PAPER.md, .agents/skills/pm/references/ara-schema.md]
- **Source**: 2026-04-14 protocol audit

## H20: experiments.md tracks completed experiments, not just plans
- **Rationale**: An experiments.md that only contains forward-looking plans becomes orphaned as soon as experiments complete — the claim→experiment→evidence chain breaks. Each entry must carry Status (planned|running|completed|failed) and Evidence output refs after completion.
- **Provenance**: user
- **Sensitivity**: medium — affects blind reproduction: an agent should execute without seeing exact numbers, but must be able to find them afterward via Evidence output refs
- **Bounds**: Exact numbers never in experiments.md (they go in evidence/); directional outcomes only
- **Code ref**: [ara/logic/experiments.md, .agents/skills/ingestor/references/ara-schema.md]
- **Source**: 2026-04-14 protocol audit

## H21: Sub-agents with chunked transcript inputs must dump chunks to files and Read them paginated
- **Rationale**: Earlier MALT extraction sub-agents previewed transcripts via `content[:N]` slices and silently lost all data past the preview window — producing truncated trace_nodes.yaml with phantom "analyzed" coverage. The robust pattern: the orchestrator dumps each transcript chunk to a temp file, the sub-agent uses the Read tool with offset/limit pagination to consume each chunk in full, and never summarizes until every chunk has been read.
- **Provenance**: user-revised
- **Sensitivity**: high — truncation is invisible from the sub-agent's summary; the only detector is comparing extracted node count against upstream message count.
- **Bounds**: Any sub-agent task whose input is chunked transcripts, message arrays, or any structure too large to fit in a single Read call.
- **Code ref**: [code/rebench-pipeline/malt_extraction_agent_prompt.md §"🚫 NO TRUNCATION"]
- **Source**: 2026-04-14 RE-Bench pipeline v2 rollout; complements memory/feedback_subagent_no_truncation.md

## H22: NEVER SKIP CHUNKS — every chunk of every transcript must be read end-to-end
- **Rationale**: Complementary to H21. Even when paginated reads are used, a sub-agent that "samples" chunks or stops reading once it believes it has enough context will silently drop later attempts. MALT runs often place the most informative attempts (final submissions, post-feedback pivots) at the end of the transcript, so tail-skipping systematically biases the extracted trace toward early failures.
- **Provenance**: user-revised
- **Sensitivity**: high — silent bias; the sub-agent's self-report of "complete" is not verifiable without an independent count.
- **Bounds**: Any chunked-input extraction; enforce with explicit "read every chunk file in order, no skipping" language in the sub-agent prompt.
- **Code ref**: [code/rebench-pipeline/malt_extraction_agent_prompt.md §"🚫 NEVER SKIP CHUNKS"]
- **Source**: 2026-04-14 RE-Bench pipeline v2 rollout

## H23: Enforce filters at merge time as well as in the sub-agent prompt
- **Rationale**: The PIPELINE.md §3.7 beat-reference filter (exclude MALT attempts with score below the task reference) is stated in the sub-agent prompt, yet one of 22 triton_cumsum runs still emitted a sub-reference attempt (0.430 vs reference 0.47). Sub-agent compliance is best-effort under a long prompt; merge-time scrubs are a cheap belt-and-suspenders that catch these leaks deterministically.
- **Provenance**: ai-suggested
- **Sensitivity**: medium — a single leaked sub-reference attempt contaminates the ARA's "what works" evidence table but does not invalidate the whole artifact.
- **Bounds**: Any filter expressible as a score/status predicate on scored attempts. Not a substitute for prompt-level rules; an addition.
- **Code ref**: [code/rebench-pipeline/ORCHESTRATOR.md Phase 3 merge step]
- **Source**: 2026-04-14 RE-Bench pipeline v2 rollout
