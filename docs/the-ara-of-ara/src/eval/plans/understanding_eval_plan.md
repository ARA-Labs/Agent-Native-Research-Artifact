# Understanding Layer Evaluation — Full Experiment Plan

## Overview

This plan describes the end-to-end workflow for evaluating ARA's understanding
layer: whether agents can extract the same or better technical knowledge from
an ARA artifact compared to the traditional PDF+GitHub baseline.

Three question categories test progressively stronger hypotheses:
- **Category A** (Lossless): ARA >= PDF — information preservation
- **Category B** (Detail): ARA > PDF+GitHub — richer configuration recovery
- **Category C** (Failure): ARA >> PDF — failure knowledge access

**Scope**: 3 benchmarks, ~31 papers/tasks, 20 questions each = ~620 Q&A pairs.

---

## Step 0: Inventory & Artifact Preparation

### 0.1 Verify Existing Artifacts

Check which papers/tasks already have complete ARA artifacts:

```
Benchmark       | Count | ARA Status
----------------|-------|------------------------------------------
PaperBench      |  23   | Only 1 has ARA (test-time-model-adaptation)
                |       | Other 22 need generation via Universal Ingestor
RE-Bench        |   7   | All 7 have ARAs (rebench-*)
MLE-bench Spdrn |   1   | 1 has ARA (nanogpt-speedrun)
```

### 0.2 Generate Missing PaperBench ARAs

For each of the 22 PaperBench papers without an ARA:

1. Locate the PDF in `code/pdfs/{paper_id}.pdf`
2. Run the Universal Ingestor:
   - Input: PDF only (no GitHub repo — matches the Ingestor's standard mode)
   - Validation: ARA Seal Level 1, up to 3 refinement iterations
   - Output: `code/artifacts/{paper_id}/`
3. Verify the artifact has the full structure:
   - `PAPER.md`, `logic/` (claims, experiments, concepts, problem, solution/),
     `src/` (configs/, kernel/ or repo/), `trace/` (exploration_tree.yaml),
     `evidence/` (tables/, figures/)

**Parallelization**: Run up to 5 Ingestor jobs concurrently (API rate limits).
**Estimated cost**: ~$2-5 per paper × 22 = ~$44-110 total.
**Estimated time**: ~5-10 min per paper × 22 ÷ 5 parallel = ~25-45 min.

### 0.3 Identify Baseline Materials

For each paper/task, identify the baseline source material:

| Benchmark | ARA Source | Baseline (PDF agent gets) |
|-----------|-----------|---------------------------|
| PaperBench | `code/artifacts/{paper_id}/` | `code/pdfs/{paper_id}.pdf` |
| RE-Bench | `code/artifacts/rebench-{task}/` | `code/artifacts/rebench-repo/ai_rd_{task}/` (README, starter code, assets) |
| Speedrun | `code/artifacts/nanogpt-speedrun/` | Speedrun task description + starter code |

**Important**: For RE-Bench, the "PDF" baseline is the task description from the
official RE-Bench repo, NOT a research paper PDF. The baseline agent sees:
- `README.md` (task description, rules, scoring)
- Starter code and assets
- Any reference documentation included in the task

### 0.4 Paper ID Registry

Create a registry file mapping paper_id → paths:

```json
// code/eval/paper_registry.json
{
  "papers": [
    {
      "paper_id": "test-time-model-adaptation",
      "benchmark": "paperbench",
      "artifact_dir": "code/artifacts/test-time-model-adaptation",
      "pdf_path": "code/pdfs/test-time-model-adaptation.pdf",
      "rubric_path": "code/eval/rubrics/test-time-model-adaptation.json",
      "github_url": null
    },
    {
      "paper_id": "rebench-optimize_llm_foundry",
      "benchmark": "rebench",
      "artifact_dir": "code/artifacts/rebench-optimize_llm_foundry",
      "baseline_dir": "code/artifacts/rebench-repo/ai_rd_optimize_llm_foundry",
      "rubric_path": null,
      "github_url": null
    }
    // ... etc for all 31 papers/tasks
  ]
}
```

---

## Step 1: Question Generation

### 1.1 Category A — Lossless Information Recovery (10 questions per paper)

**Applied to**: All 31 papers/tasks (PaperBench + RE-Bench + Speedrun).

**Purpose**: Verify ARA preserves all information from the source without loss.

**Question characteristics**:
- Standard comprehension questions answerable from the source material alone
- Span: surface results, method descriptions, experimental conditions, design choices
- Generated from the source material (PDF or task description) to ensure fairness
  — neither format is advantaged by question design

**Difficulty distribution** (per 10 questions):
- T1 (Explicit): 2 — answer verbatim in one location
- T2 (Scattered): 4 — answer requires assembling from 2+ locations
- T3 (Implicit): 3 — answer requires inference
- Unanswerable: 1 — plausible but not answerable (control)

**Generation protocol**:

For PaperBench papers:
```
1. Read the PDF via Anthropic's native PDF document mode (base64)
2. Use the existing generate_questions.py SYSTEM_PROMPT (6 categories, 4 tiers)
3. Generate 10 questions using claude-sonnet-4-6
4. Validate: at least 1 question per category, correct tier distribution
5. Extract gold_answer from the PDF (with section/table/figure citations)
6. Save to code/eval/questions/{paper_id}_catA.json
```

For RE-Bench / Speedrun tasks:
```
1. Read the task README + starter code + any reference docs
2. Adapt the SYSTEM_PROMPT for task descriptions instead of papers:
   - Replace "paper" references with "task description"
   - Categories: task_objective, method_detail, configuration,
     scoring_criteria, constraints, edge_cases
3. Generate 10 questions using claude-sonnet-4-6
4. Validate and extract gold_answer from the task description
5. Save to code/eval/questions/{paper_id}_catA.json
```

**Gold answer construction**:
- Each gold_answer must cite the exact source location (section, table, line)
- For exact_numeric questions: the answer is a specific number
- For semantic questions: a reference answer with key concepts
- For unanswerable questions: "INSUFFICIENT INFORMATION" with justification
  for why it's genuinely unanswerable

### 1.2 Category B — Configuration & Detail Recovery (5 questions per paper)

**Applied to**: PaperBench papers only (23 papers).

**Purpose**: Test whether ARA captures details that PDFs under-specify.

**Question characteristics**:
- Target the specific gaps identified in the information gap analysis
- Focus on: hyperparameter values, environment specifications, preprocessing
  pipelines, evaluation configurations, dataset acquisition details
- Questions are HARDER than Category A — they ask for information that
  papers typically mention incompletely or omit

**Key design principle**: Questions are generated from the PaperBench rubric,
NOT from the PDF. The rubric specifies what information SHOULD exist for full
reproduction. We pick rubric requirements that are rated "partial" or "absent"
in our info gap analysis, then convert them into questions.

**Generation protocol**:
```
1. Load the PaperBench rubric: code/eval/rubrics/{paper_id}.json
2. Load the info gap results: code/eval/results/info_gap_{paper_id}.json
3. Filter for requirements rated "partial" or "absent" with gap_type in:
   - missing_hyperparameter
   - vague_description
   - missing_code_detail
   - missing_baseline_detail
4. Rank by importance (rubric weight) and diversity (different gap types)
5. Select top 5 requirements
6. For each requirement, generate a targeted question:
   - Frame as "What is the exact [hyperparameter/config/detail] for [X]?"
   - The gold_answer comes from the rubric requirement specification
   - The PDF is known to NOT fully specify this (rated partial/absent)
7. Difficulty distribution: 2 T2 (scattered) + 2 T3 (implicit) + 1 control
   (no T1 — by design these are NOT explicitly stated)
8. Save to code/eval/questions/{paper_id}_catB.json
```

**Gold answer construction**:
- Gold answers are derived from the PaperBench rubric leaf requirements
- Each answer specifies:
  - The specific information needed (from rubric)
  - What the PDF actually provides (from info gap analysis)
  - What a complete answer would look like
- This creates a 3-level grading: absent (PDF says nothing), partial
  (PDF hints), sufficient (full specification)

**Example**:
```json
{
  "id": "test-time-model-adaptation_B01",
  "category": "configuration_recovery",
  "difficulty": "T2_scattered",
  "question": "What are the exact optimizer settings (learning rate, weight decay, scheduler) used for the forward-only adaptation on ImageNet-C at severity level 5?",
  "gold_answer": "Learning rate 1e-3 with cosine annealing, AdamW optimizer with weight decay 0.01, 10 adaptation steps per batch...",
  "rubric_requirement_id": "req_142",
  "info_gap_rating": "partial",
  "gap_type": "missing_hyperparameter",
  "grading_type": "checklist"
}
```

### 1.3 Category C — Failure & Exploration Knowledge (5 questions per paper)

**Applied to**: RE-Bench (7 tasks) + Speedrun (1 task) = 8 papers/tasks.

**Purpose**: Test whether ARA's trace layer provides knowledge that PDFs
fundamentally cannot contain.

**Question characteristics**:
- Ask about failed experiments, dead-end approaches, abandoned configurations
- These are questions a researcher would genuinely ask when picking up a project
- The PDF/task description is EXPECTED to have no answer
- The ARA trace layer should answer from the exploration tree

**Key design principle**: Questions must be FAIR — they should be natural
questions any researcher would ask, NOT reverse-engineered from the ARA.
Generate from the task description + domain knowledge, then verify answers
exist in the ARA trace layer.

**Generation protocol**:
```
1. Read the task README (what the task asks the agent to do)
2. Generate 5 failure-knowledge questions using this prompt:

   "You are a researcher about to work on this task. You want to learn from
   previous attempts. Generate 5 questions about what approaches have been
   tried and failed, what configurations don't work, and what pitfalls to
   avoid. These are questions about NEGATIVE results — things that DIDN'T
   work. Frame as practical researcher questions."

   Categories:
   - failed_configurations: "What hyperparameter settings were tried but
     didn't improve the score?"
   - abandoned_approaches: "What algorithmic approaches were explored and
     abandoned, and why?"
   - dead_end_analysis: "What were the main failure modes encountered?"
   - resource_waste: "How much compute was spent on approaches that didn't
     work?"
   - lessons_learned: "What key lessons were learned from failed attempts?"

3. For each generated question, verify against the ARA trace layer:
   - Read trace/exploration_tree.yaml
   - Check that at least one dead_end node answers the question
   - Extract the gold_answer from the trace layer
   - If a question has no answer in the trace, replace it

4. Difficulty: All T3_implicit (these require trace-layer knowledge)
   Exception: 1 question can be unanswerable as control

5. Save to code/eval/questions/{paper_id}_catC.json
```

**Gold answer construction**:
- Gold answers are extracted from trace/exploration_tree.yaml
- Each answer references specific dead_end nodes:
  ```json
  {
    "gold_answer": "Three configurations were tried and abandoned: (1) FP8 quantization [N10] — failed because behavioral equivalence check failed, (2) Reducing training steps from 4 to 2 [N11] — loss increased by 15%, (3) Flash Attention [N12] — installation failed on the target environment.",
    "trace_nodes": ["N10", "N11", "N12"],
    "expected_pdf_behavior": "abstention"
  }
  ```

### 1.4 Question Quality Assurance

After generating all questions, run a validation pass:

```
For each question set:
  1. Check JSON schema validity
  2. Verify no duplicate questions across categories
  3. Verify difficulty distribution matches specification
  4. Verify gold_answers are non-trivial (not one-word answers)
  5. Verify Category B questions target actual info gaps (cross-check with
     info_gap results)
  6. Verify Category C gold_answers reference real trace nodes
  7. Flag any question where gold_answer confidence is low
```

Save validation report to `code/eval/results/question_validation.json`.

---

## Step 2: Agent Answering

### 2.1 Agent Configuration

Two agents answer each question independently:

| Config | ARA Agent | Baseline Agent |
|--------|-----------|----------------|
| Model | claude-sonnet-4-6 | claude-sonnet-4-6 |
| Max tokens | 4096 per answer | 4096 per answer |
| Temperature | 0 | 0 |
| Tools | Read, Glob, Grep | Read |
| Context | ARA artifact directory | PDF (or task dir for RE-Bench) |

**Critical: Both agents use the SAME model and temperature.** The only variable
is the source material they receive.

### 2.2 ARA Agent Protocol

For each (paper, question):

```
1. Load the ARA agent prompt template (code/eval/prompts/ara_agent.md)
2. Fill in {artifact_dir} and {questions_block}
3. Spawn a sub-agent with the filled prompt
4. The agent navigates the ARA:
   - Starts with PAPER.md (root manifest)
   - Uses Glob to find relevant files
   - Uses Read to extract specific information
   - Uses Grep to search for keywords
   - For Category C (failure questions): specifically reads
     trace/exploration_tree.yaml and trace/sessions/
5. Agent returns JSON: {"agent_type": "ARA", "answers": [...]}
6. Save raw response to code/eval/results/answers/{paper_id}_ara.json
```

**ARA agent prompt enhancement for failure questions (Category C)**:

Add to the existing ara_agent.md template:
```
For questions about failed experiments, dead ends, or negative results:
- Check `trace/exploration_tree.yaml` for nodes of type `dead_end`
- Check `trace/sessions/` for session records documenting failures
- Check `logic/claims.md` for claims with status `refuted` or `weakened`
- Check `logic/solution/heuristics.md` for sensitivity warnings
If no failure information exists in the artifact, say so explicitly.
```

### 2.3 Baseline Agent Protocol

**For PaperBench papers** (Categories A + B):

```
1. Load the PDF agent prompt template (code/eval/prompts/pdf_agent.md)
2. Fill in {pdf_path} and {questions_block}
3. Provide the PDF via Anthropic's native PDF document mode (base64)
4. If a GitHub repo URL is known, also provide:
   - README.md content
   - Key config files (if identifiable)
   - Note: most PaperBench papers don't have accessible repos,
     so PDF-only is the realistic baseline
5. Agent returns JSON: {"agent_type": "PDF", "answers": [...]}
6. Save to code/eval/results/answers/{paper_id}_pdf.json
```

**For RE-Bench / Speedrun tasks** (Categories A + C):

```
1. Load a modified baseline prompt:
   "You are a researcher answering questions about a task using only the
    official task description and starter code."
2. Provide: README.md, starter code files, any reference docs from
   code/artifacts/rebench-repo/ai_rd_{task}/
3. Agent answers based ONLY on what's in these files
4. Save to code/eval/results/answers/{paper_id}_baseline.json
```

### 2.4 Parallelization Strategy

```
Total Q&A pairs: ~620 (31 papers × 20 questions)
Agents per pair: 2 (ARA + baseline)
Total agent calls: ~62 (31 papers × 2 agents, each answering all questions)

Strategy:
- Process papers in batches of 5
- Within each batch, spawn 10 agents in parallel (5 ARA + 5 baseline)
- Each agent answers all questions for its paper in one call
- Wait for batch completion before starting next batch
- Estimated: 7 batches × ~3 min each = ~21 min total

API cost estimate:
- ARA agent: ~50K input tokens (artifact) + ~2K per answer × 20 = ~90K total
- PDF agent: ~30K input tokens (PDF) + ~2K per answer × 20 = ~70K total
- Per paper: ~160K tokens × 2 = ~$0.50
- Total: 31 × $0.50 = ~$15.50
```

---

## Step 3: Judging

### 3.1 Judge Configuration

| Config | Value |
|--------|-------|
| Model | claude-opus-4-6 |
| Temperature | 0 |
| Max tokens | 8192 |
| Blinding | Random A/B assignment per question |

### 3.2 Blinding Protocol

**Critical for fairness**: The judge must NOT know which agent is ARA vs PDF.

```
For each (paper, question):
  1. Flip a fair coin (random.random() < 0.5)
  2. If heads: Agent A = ARA, Agent B = PDF
     If tails: Agent A = PDF, Agent B = ARA
  3. Record the mapping in a separate blinding_key.json (NOT shown to judge)
  4. Present answers to judge as "Agent A" and "Agent B" only
```

### 3.3 Judge Prompt

Use the existing judge.md template with the following qa_blocks format:

```
### Question {q_id}: {question_text}

**Gold Answer**: {gold_answer}

**Agent A's Answer**:
{agent_a_answer}

**Agent B's Answer**:
{agent_b_answer}
```

**Enhancement**: Add gold_answer to the judge prompt so the judge can assess
absolute correctness, not just relative quality. This is critical for Category B
(where the gold answer comes from the rubric and may not appear in either agent's
answer) and Category C (where the PDF agent is expected to abstain).

### 3.4 Scoring

Per-question scoring (same as existing judge.md):
- **Correctness** (1-5): Facts, numbers, claims accuracy
- **Completeness** (1-5): Coverage of all aspects
- **Specificity** (1-5): Exact numbers, equations, section citations
- **Hallucination penalty** (0 to -3): Fabricated or unsupported claims
- **Total**: Sum of above (max 15, min -3)

Per-question verdict: "A", "B", or "Tie"

**Additional scoring for Category C**:
- **Abstention correctness**: If the question asks about failures and the agent
  correctly says "I cannot find this information", score abstention_correct=true
  (better than hallucinating failures)

### 3.5 Judge Parallelization

```
- Judge processes one paper at a time (all 20 questions in one call)
- 31 judge calls total, run in batches of 5
- Estimated: 7 batches × ~2 min = ~14 min
- Cost: ~$1 per paper × 31 = ~$31 (Opus is expensive)
```

### 3.6 De-blinding

After judging, de-blind the results:

```python
for each paper_result:
    for each question_result:
        # Look up blinding key
        if blinding_key[paper_id][question_id] == "ARA_is_A":
            ara_score = question_result["agent_a"]
            pdf_score = question_result["agent_b"]
            winner = remap(question_result["winner"])  # A->ARA, B->PDF
        else:
            ara_score = question_result["agent_b"]
            pdf_score = question_result["agent_a"]
            winner = remap(question_result["winner"])  # A->PDF, B->ARA
```

Save de-blinded results to `code/eval/results/understanding/{paper_id}_judged.json`.

---

## Step 4: Metrics & Analysis

### 4.1 Primary Metrics

**Per-category win rates** (the headline numbers):

```
Category A (Lossless): ARA wins / PDF wins / Ties  (across all 31 papers)
Category B (Detail):   ARA wins / PDF wins / Ties  (across 23 PaperBench papers)
Category C (Failure):  ARA wins / PDF wins / Ties  (across 8 RE-Bench+Speedrun)
```

**Per-category average scores**:
```
Category | ARA Avg Score | PDF Avg Score | Delta | p-value
---------|---------------|---------------|-------|--------
A        | X.X / 15      | X.X / 15      | +X.X  | 0.XXX
B        | X.X / 15      | X.X / 15      | +X.X  | 0.XXX
C        | X.X / 15      | X.X / 15      | +X.X  | 0.XXX
```

### 4.2 Secondary Metrics

**Per-difficulty breakdown** (within each category):
```
Difficulty | ARA Win% | PDF Win% | Tie% | ARA Avg | PDF Avg
-----------|----------|----------|------|---------|--------
T1_explicit|          |          |      |         |
T2_scattered|         |          |      |         |
T3_implicit|          |          |      |         |
Unanswerable|         |          |      |         |
```

**Per-benchmark breakdown**:
```
Benchmark  | Cat A Win% | Cat B Win% | Cat C Win% | Overall
-----------|------------|------------|------------|--------
PaperBench |            |     N/A    |    N/A     |
RE-Bench   |            |            |            |
Speedrun   |            |    N/A     |            |
```

**Hallucination analysis**:
- Per-category hallucination rate (% of answers with penalty > 0)
- Compare ARA vs PDF hallucination rates
- Especially important for Category C: does the PDF agent hallucinate
  failure knowledge, or does it correctly abstain?

**Abstention analysis** (for unanswerable questions + Category C):
- True abstention rate (correctly says "insufficient information")
- False abstention rate (says insufficient when answer exists)
- False confidence rate (gives wrong answer instead of abstaining)

### 4.3 Statistical Significance

For each category, run:
1. **McNemar's test** on win/loss counts (paired binary outcomes)
2. **Paired t-test** on total scores (continuous outcomes)
3. **Bootstrap confidence interval** (95%) on win rate difference

Report p-values and confidence intervals in the paper.

### 4.4 Qualitative Analysis

For the paper, select 2-3 illustrative examples per category:

- **Category A win for ARA**: Show a scattered question where ARA's structured
  layout made information easier to find
- **Category A win for PDF**: Show an explicit question where the PDF's
  verbatim text was more faithful
- **Category B win for ARA**: Show a rubric requirement rated "absent" in PDF
  but fully specified in ARA
- **Category C win for ARA**: Show a failure knowledge question where ARA's
  trace layer provided detailed dead-end analysis while PDF abstained

### 4.5 Failure Analysis

Identify systematic ARA weaknesses:
- Questions where ARA consistently loses across papers
- Information types the Ingestor systematically drops
- Papers where ARA performs worst (investigate why)
- Correlation between info_gap_rating and ARA advantage

---

## Step 5: Output Files

### 5.1 Generated Artifacts

```
code/eval/
  paper_registry.json                    # Paper/task → path mapping
  questions/
    {paper_id}_catA.json                 # Category A questions (all papers)
    {paper_id}_catB.json                 # Category B questions (PaperBench)
    {paper_id}_catC.json                 # Category C questions (RE-Bench+Speedrun)
  results/
    understanding/
      answers/
        {paper_id}_ara.json              # ARA agent raw answers
        {paper_id}_baseline.json         # Baseline agent raw answers
      judging/
        {paper_id}_judged.json           # De-blinded judge results
        blinding_key.json                # A/B assignment record
      analysis/
        category_summary.json            # Per-category win rates
        difficulty_breakdown.json        # Per-tier analysis
        benchmark_breakdown.json         # Per-benchmark analysis
        hallucination_analysis.json      # Hallucination rates
        statistical_tests.json           # p-values, CIs
        qualitative_examples.json        # Selected illustrative examples
        question_validation.json         # QA validation report
      understanding_eval_report.json     # Complete aggregate report
```

### 5.2 Report Format

The final `understanding_eval_report.json`:

```json
{
  "metadata": {
    "timestamp": "2026-03-13T...",
    "n_papers": 31,
    "n_questions_total": 620,
    "models": {"answerer": "claude-sonnet-4-6", "judge": "claude-opus-4-6"},
    "cost_total_usd": 46.50
  },
  "headline": {
    "category_a": {"ara_wins": X, "pdf_wins": X, "ties": X, "ara_avg": X.X, "pdf_avg": X.X},
    "category_b": {"ara_wins": X, "pdf_wins": X, "ties": X, "ara_avg": X.X, "pdf_avg": X.X},
    "category_c": {"ara_wins": X, "pdf_wins": X, "ties": X, "ara_avg": X.X, "pdf_avg": X.X}
  },
  "by_difficulty": { ... },
  "by_benchmark": { ... },
  "statistical_tests": { ... },
  "qualitative_examples": [ ... ],
  "failure_analysis": { ... }
}
```

---

## Execution Checklist

```
[ ] Step 0.1: Verify all 31 artifacts exist
[ ] Step 0.2: Generate missing PaperBench ARAs (22 papers)
[ ] Step 0.3: Create paper_registry.json
[ ] Step 1.1: Generate Category A questions (31 papers × 10 questions)
[ ] Step 1.2: Generate Category B questions (23 papers × 5 questions)
[ ] Step 1.3: Generate Category C questions (8 tasks × 5 questions)
[ ] Step 1.4: Run question validation
[ ] Step 2.1: Run ARA agents (31 papers)
[ ] Step 2.2: Run baseline agents (31 papers)
[ ] Step 3.1: Run blinded judging (31 papers)
[ ] Step 3.2: De-blind results
[ ] Step 4.1: Compute primary metrics
[ ] Step 4.2: Compute secondary metrics
[ ] Step 4.3: Run statistical tests
[ ] Step 4.4: Select qualitative examples
[ ] Step 4.5: Analyze failures
[ ] Step 5.1: Generate report
```

---

## Estimated Costs & Timeline

| Phase | API Cost | Wall Time |
|-------|----------|-----------|
| ARA generation (22 papers) | ~$100 | ~45 min |
| Question generation (31 papers × 3 cats) | ~$15 | ~20 min |
| Agent answering (62 agent calls) | ~$16 | ~21 min |
| Judging (31 judge calls) | ~$31 | ~14 min |
| Analysis | ~$0 | ~5 min |
| **Total** | **~$162** | **~105 min** |
