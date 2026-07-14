# MALT Run → ARA Content Compiler

You are an ARA content compiler. You read one agent run from a MALT transcript and produce
ARA-structured content (trace nodes, evidence rows, heuristic/claim insights) ready to be
merged into the final artifact.

## Primary References

Read both of these before doing anything else:

1. **PIPELINE.md** (this directory): governs RE-Bench-specific rules — source provenance,
   filtering, what goes where, hallucination prevention. **PIPELINE.md takes priority over
   the ingestor skill in all conflicts.**

2. **Ingestor skill** (`.agents/skills/ingestor/SKILL.md` + its references): governs ARA
   format — how to write trace nodes, claims, heuristics, evidence tables, experiments.
   Use its schema definitions and field formats.

## Your Inputs

- **JSONL file**: `{JSONL_PATH}`
- **Run index**: `{RUN_INDEX}` (0-based)
- **Task slug**: `{TASK_SLUG}` (e.g. `triton_cumsum`, `fix_embedding`)
- **Task card path**: `{TASK_CARD_PATH}` (e.g. `code/rebench-pipeline/tasks/{TASK_SLUG}.md` — the source of truth for this task's scoring)
- **Reference score threshold**: `{REFERENCE_SCORE}` (numeric threshold from the task card)
- **Score direction**: `{SCORE_DIRECTION}` — either `lower_better` or `higher_better`
- **Score formula label**: `{SCORE_FORMULA}` (e.g. `ln(time_ms)`, `log(loss-1.5)`, `win_rate`, `pass_rate`, `two_term_loss`)
- **Metric name**: `{METRIC_NAME}` (e.g. `time_ms`, `loss`, `win_rate`, `pass_rate`) — the raw quantity under the log/transform, read from the score message
- **Metric unit**: `{METRIC_UNIT}` (e.g. `ms`, `nats`, `%`, or empty) — used only for display
- **Node ID start**: `{NODE_ID_START}` (first N-id to use, e.g. N25 — assigned by orchestrator to avoid collisions)
- **Experiment ID start**: `{EXP_ID_START}` (first E-id to use)
- **Output directory**: `{OUTPUT_DIR}` (write all output files here)

## Step 1: Read PIPELINE.md, the task card, and the ingestor skill

```
Read: code/rebench-pipeline/PIPELINE.md
Read: {TASK_CARD_PATH}
Read: .agents/skills/ingestor/SKILL.md
Read: .agents/skills/ingestor/references/ara-schema.md
```

Internalize all four. The task card overrides PIPELINE.md on any task-specific detail (score formula, file list, dev-history stages, known hazards). PIPELINE.md overrides the ingestor skill on any conflict.

## Step 2: Load the run

```python
import json
with open("{JSONL_PATH}") as f:
    runs = [json.loads(l) for l in f]
run = runs[{RUN_INDEX}]
messages = run["messages"]
run_id = run["run_id"]
model = run["model"]
```

## Step 3: Read messages sequentially, chunk by chunk (~50 at a time)

Read ALL messages in order. Build a running understanding of:
- What the agent is currently trying (method/approach)
- What the agent has learned so far
- What has succeeded or failed and why

### 🚫 NO TRUNCATION — READ FULL MESSAGE CONTENT

**Hard rule (non-negotiable)**: You must read the **full content** of every message, not
a truncated preview. Do NOT slice message content with `content[:200]`,
`preview[:800]`, or similar. Long tool outputs, tracebacks, error messages, and
agent reasoning often contain the exact detail that distinguishes one failure
mode from another. Truncating them silently drops the information you were
sent to extract.

**Recommended reading pattern** (handles large messages without context blowup):

```python
import json
with open("{JSONL_PATH}") as f:
    runs = [json.loads(l) for l in f]
messages = runs[{RUN_INDEX}]["messages"]

# Dump full messages to temp files in chunks of ~20-50 messages each,
# then use the Read tool to read each chunk file in full.
import os, tempfile
tmpdir = tempfile.mkdtemp()
CHUNK = 30
for start in range(0, len(messages), CHUNK):
    chunk = messages[start:start+CHUNK]
    path = f"{tmpdir}/chunk_{start:04d}_{start+len(chunk):04d}.txt"
    with open(path, "w") as f:
        for i, msg in enumerate(chunk, start=start):
            f.write(f"\n===== MSG {i} role={msg.get('role')} =====\n")
            content = msg.get('content', '')
            if isinstance(content, str):
                f.write(content)
            else:
                f.write(json.dumps(content, indent=2))
            f.write("\n")
print(tmpdir)  # then Read each chunk file in turn
```

Then use the **Read tool** on each chunk file (Read handles large files natively
with pagination). This way you see full content of every message without
stuffing everything into a single Bash output.

### 🚫 NEVER SKIP CHUNKS — READ EVERY SINGLE ONE

**Hard rule (non-negotiable)**: You MUST call the Read tool on **every chunk file** you
dumped, in order, from chunk 0 to the last chunk. Do NOT skip chunks for ANY reason,
including:

- You detected a `trim` / `context-truncation` marker and believe later messages are a replay
- You ran a Python script (regex, role counts, fingerprint, dedup) that "proved" later chunks
  are redundant
- Token budget is getting tight
- You already have enough information to draft outputs
- You spot-checked one chunk and inferred the others

Structural analysis (regex, role counts, fingerprinting) is a useful *supplement*, but it is
**never a substitute** for Read-tool coverage of every chunk. Replays can contain new
reasoning, new errors, or a new score submission buried in the middle — you cannot prove
the absence of novel content without reading. If token budget is genuinely a concern,
compact your own working notes between chunks (per the section below), but still Read
every chunk.

When you write your final report, list every chunk file and state that you Read each one.

### 💾 Compact your own memory as you go

If the chunks start to crowd your context, **compact your own working notes**
between chunks: after each chunk, write a short running summary (what was
tried, scores observed, errors seen, lessons) and rely on that summary instead
of holding raw chunk text in context. Never solve the context problem by
truncating input.

### Score-message parsing — READ THE TASK CARD FIRST

Score submissions appear as `role=function` messages. **The exact shape is task-specific, and several tasks diverge from the naïve `{score, message:{METRIC_NAME:value}}` mental model.** Before writing any extractor code, read the "MALT transcript shape" section of `{TASK_CARD_PATH}` to learn:

1. Whether the `role=function` **content is a dict or a string** (some tasks encode it as a JSON string, some as a Python-repr string — you must parse before indexing).
2. Whether `status` is always present (some tasks omit it on success).
3. The exact key under `message.*` that holds the raw metric — the task card specifies `{METRIC_NAME}` for you.
4. Whether the task is **score-hidden** (score is always `null`; metric is never exposed) — in that case skip the per-attempt score filter entirely; see "Score-hidden tasks" below.
5. Whether the raw metric **equals the score itself** (no transform) — the "degenerate metric" case; see below.

Illustrative shapes (non-exhaustive; the task card is authoritative):

```
# triton_cumsum: content is a dict; METRIC_NAME=time_ms (under message.time)
{'status': 'invalidSubmission', 'score': None, 'message': {'results_match': False, 'time': 947.3, ...}}
{'status': 'ok', 'score': 0.89, 'message': {'time': 2437.5, ...}}

# fix_embedding: content is a STRING (JSON or Python-repr); METRIC_NAME=loss_validation
'{"scoredAt":...,"score":2.196,"message":{"loss_train":10.42,"loss_validation":10.49}}'
"{'status': 'scoringSucceeded', 'score': ..., 'message': {'loss_validation': ..., 'loss_train': ...}}"

# restricted_mlm: content is a dict; METRIC_NAME=loss
{'status': 'scoringSucceeded', 'score': 1.8468, 'message': {'execution_time': ..., 'loss': 7.8396}}

# rust_codecontests (degenerate): no separate metric key; metric_value := score
{'status': 'scoringSucceeded', 'score': 0.0545, 'message': {'n_successes': 9, 'n_problems': 165, 'standard_error': ...}}

# nanogpt_chat_rl (degenerate): no message.win_rate; metric_value := score
{'status': 'scoringSucceeded', 'score': 0.569, 'message': {'score_time': 244.15, 'win_vs_gpt2-alpaca': 0.455, 'win_vs_gpt2-xl': 0.683}}

# small_scaling_law (score-hidden): score is always null; no score or loss components exposed
{'status': 'scoringSucceeded', 'score': None, 'message': {'is_valid': True, 'frac_flops_used': 0.0042}}
```

- `score: None` (or `status: invalidSubmission`) = invalid / wrong output / correctness failure.
- `score: float` = valid scored attempt.

### Degenerate-metric tasks (metric_value := score)

When the task card says "degenerate metric" (e.g. `rust_codecontests`, `nanogpt_chat_rl`), the raw metric **is** the top-level `score` itself. In that case:
- Set `metric_value := score` in trace nodes and evidence rows.
- Collapse the evidence-table metric column so you don't emit the same number twice — see "Evidence table header" below.
- Do not invent a `message.{METRIC_NAME}` key that does not exist.

### Score-hidden tasks

When the task card says "score-hidden" (e.g. `small_scaling_law`), **the transcript never exposes a per-attempt score**. In that case:
- Do not apply the beat-reference filter — there is no score to filter against. Every attempt that represents a submission becomes a node.
- `score: null` in every trace node for that task.
- Use whatever auxiliary quantity the card names (e.g. `frac_flops_used`) as the `{METRIC_NAME}` value, and note in `approach_context` that the score is hidden by task design.

**Filtering rule (PIPELINE.md §2, §3 rule 7)** — direction-aware:

- Define `beats_reference`:
  - If `{SCORE_DIRECTION} == lower_better`: `score is not null AND score < {REFERENCE_SCORE}`
  - If `{SCORE_DIRECTION} == higher_better`: `score is not null AND score > {REFERENCE_SCORE}`
- Include every attempt that does NOT beat reference (including invalid/null-score attempts — they are dead ends).
- Exclude every attempt that beats reference.
- **Non-monotonic, per-attempt**: a lower-better run may go 1.5 → 0.8 → 0.3 (excluded) → 0.6 → 1.1 — include 1.5, 0.8, 0.6, 1.1 and exclude only 0.3. A higher-better run with reference 0.85 may go 0.5 → 0.7 → 0.9 (excluded) → 0.6 — include 0.5, 0.7, 0.6 and exclude 0.9.
- **Do not stop reading after a beating attempt** — read through to the end of the run.
- **Score-hidden tasks**: if the task card marks the task score-hidden (score is always null), the filter is a no-op. Every submission becomes a node; record `beats_reference: null` in internal notes so the merge layer does not re-apply the scrub.

## Step 4: Produce ARA output files

Write the following files to `{OUTPUT_DIR}/`:

---

### `trace_nodes.yaml`

Exploration tree nodes for this run. Format follows ingestor schema (ara-schema.md).

Each included attempt becomes either:
- A `dead_end` node: if score is null (wrong output), or compile/runtime error
- An `experiment` node: if score is valid float (worse than reference)

Group attempts that use essentially the same method into one node with
`runs_observed: 1` (since this is one run). Truly distinct approaches = distinct nodes.

```yaml
# MALT run {run_id} — {model}
nodes:
  - id: N{NODE_ID_START}
    type: dead_end | experiment
    title: "{concise title of approach}"
    provenance: MALT
    source: "MALT run_id={run_id} model={model}"
    timestamp: null   # not available from transcript

    # For dead_end:
    hypothesis: "{what the agent tried and expected}"
    failure_mode: "{specific error or wrong output — include error messages if visible}"
    lesson: "{what this rules out or teaches — specific to this task}"

    # For experiment (valid score, did not beat reference per {SCORE_DIRECTION}):
    method: "{specific approach: algorithm, architecture, key hyperparameters}"
    result: "{score=X.XX — did not beat reference {REFERENCE_SCORE}}"   # embed metric details inline only if task card says so
    score: {float}
    {METRIC_NAME}: {float or null}   # raw metric value keyed by the task card's METRIC_NAME

    # Both types:
    approach_context: "{1-2 sentences on what the agent was reasoning about, what led to this attempt}"
```

Task-mode variants for the `experiment` fields:

- **Degenerate-metric tasks** (e.g. `rust_codecontests`, `nanogpt_chat_rl`): `{METRIC_NAME}` field equals `score`; do NOT emit a second identical line. Instead record auxiliary components in `approach_context` (e.g. "9/165 solved" or "win_vs_xl=0.68, win_vs_alpaca=0.45").
- **Score-hidden tasks** (e.g. `small_scaling_law`): set `score: null` for every attempt. Emit the auxiliary metric named by the task card (e.g. `frac_flops_used: 0.0042`) in place of `{METRIC_NAME}`. The filter rule is a no-op; classify by transcript structure and reasoning content only.
- **Empty `{METRIC_UNIT}`**: never emit ` ({METRIC_UNIT})` as literal `()`. Drop the parenthetical entirely when the unit is empty.

Nest nodes if the agent's attempts build directly on each other (e.g., "tried X, failed,
then modified X to fix the bug → tried X'"). Use flat structure if attempts are independent.

---

### `evidence_rows.md`

Rows to append to `evidence/tables/malt_attempts.md`. Only included attempts (the ones that did NOT beat reference).

```markdown
| {run_id} | {model_short} | {attempt_N} | {approach_summary} | {score} | {metric_value} | valid |
| {run_id} | {model_short} | {attempt_N} | {approach_summary} | null | {metric_value_or_blank} | invalid ({failure_kind}) |
```

Header (include only in first run's output, omit otherwise — orchestrator handles merging). The metric column header is task-specific; compose it from the task card's parameters, not mechanically from the template.

Standard form (separate score transform and raw metric):
```markdown
| run_id | model | attempt | approach | score ({SCORE_FORMULA}) | {METRIC_NAME}[ ({METRIC_UNIT})] | status |
```
- Omit ` ({METRIC_UNIT})` if `{METRIC_UNIT}` is empty — do not emit `()` with nothing in it.

Degenerate-metric form (score IS the metric; collapse to one numeric column):
```markdown
| run_id | model | attempt | approach | score ({SCORE_FORMULA}) | status |
```
- Add a secondary context column only if the task card names a natural auxiliary (e.g. `n_successes/n_problems` for `rust_codecontests`; the two component win-rates for `nanogpt_chat_rl`). Keep it as prose, not a second numeric column.

Score-hidden form (score is always null; emit auxiliary metric):
```markdown
| run_id | model | attempt | approach | {METRIC_NAME} | status |
```
- e.g. `small_scaling_law`: `| ... | frac_flops_used | status |`. Omit the score column entirely.

Concrete examples:
```markdown
# triton_cumsum (standard, METRIC_UNIT=ms):
| run_id | model | attempt | approach | score (ln(time_ms)) | time (ms) | status |

# fix_embedding (standard, METRIC_UNIT=""):
| run_id | model | attempt | approach | score (log(loss_validation-1.5)) | loss_validation | status |

# rust_codecontests (degenerate, with aux context):
| run_id | model | attempt | approach | score (pass_rate) | n_successes/n_problems | status |

# nanogpt_chat_rl (degenerate):
| run_id | model | attempt | approach | score (win_rate) | win_vs_xl / win_vs_alpaca | status |

# small_scaling_law (score-hidden):
| run_id | model | attempt | approach | frac_flops_used | status |
```

---

### `insights.yaml`

Heuristics or claim-supporting observations derived from this run. Only include if the
run reveals something non-obvious that generalizes beyond this single attempt.

```yaml
insights:
  - type: heuristic | claim_support | claim_refute
    content: "{specific, falsifiable observation}"
    source: "MALT run_id={run_id}"
    evidence: "{which attempt(s) support this}"
    # e.g.: "tl.scan does not exist in Triton 2.3.1 — AttributeError observed in run 344673 attempt 2"
    # e.g.: "PyTorch cumsum chain achieves ~950ms (score ~6.8) on N=10^8, not sub-2ms"
```

---

### `run_summary.yaml`

```yaml
run_id: {int}
run_index: {int}
model: "{string}"
total_messages: {int}
total_attempts: {int}
included_attempts: {int}
excluded_attempts: {int}
best_score_overall: {float or null}
best_included_score: {float or null}
arc_description: >
  {2-4 sentences: what did this agent try, what did it learn, how did it progress.
   Written as a narrative useful for ARA context.}
```

---

## Critical Rules (PIPELINE.md overrides ingestor on all of these)

1. **Read every message IN FULL** — do not skip, do not truncate. No `content[:N]`
   previews. Dump messages to chunk files and Read them with the Read tool, which
   paginates natively. Reasoning between score actions is where the method design
   and failure lessons live, and long tool outputs / tracebacks carry the exact
   error text you must capture.

2. **Describe methods specifically** — "Triton kernel with BLOCK_SIZE=1024,
   tl.associative_scan over (count, v_even, v_odd) composite state, two-pass" is useful.
   "tried a Triton kernel" is not.

3. **Lessons must be specific and transferable** — "tl.scan does not exist in Triton 2.3.1;
   the correct primitive is tl.associative_scan" teaches something. "it didn't work" does not.

4. **All provenance tagged** — every node carries `source: MALT run_id=X model=Y`.

5. **No invented content** — if a message is ambiguous, note the ambiguity. Do not guess
   what the agent tried or invent scores.

6. **No planned/hypothetical experiments** — everything in this run already happened.
   Use past tense. No status: planned.

7. **No src/ content** — MALT runs do not contribute to `src/`. That layer comes from the
   official solution only.
