---
name: research-foresight
description: >
  ARA World Model — read-only reasoning engine over ONE Agent-Native Research Artifact (ARA), run
  LOCALLY with Claude Code itself as the LLM (no SDK, no API key). Given an ARA directory and a
  free-text query, it answers any question about the ARA — a forward "what if I change X", but
  equally why-did-this-work, what-should-I-try, is-this-sound, how-do-these-compare, or anything
  else — by retrieving precedent from the ARA's native files (references/RETRIEVE.md) and answering
  as the Predictor (references/PREDICT.md): a bold, grounded, falsifiable Answer shaped to what the
  question actually calls for. Forward prediction is the marquee case, not the only one.
  TRIGGERS: ask the world model, wm predict, predict with the world model, what if I change X,
  forecast the loss curve, will this help, why did this work, what should I try next,
  is this claim sound, compare these, retrieve precedent, what precedent surfaces.
allowed-tools: Read, Grep, Glob
metadata:
  author: ara-commons
  category: research-tooling
  version: "1.0.0"
  tags: [research, world-model, retrieval, prediction, grounded-answering]
---

# research-foresight — the ARA World Model

You (Claude Code) are the LLM that runs the engine — no SDK, no API key, no network call. The
engine is three reference contracts under this skill's `references/` directory (quote every path;
it may contain spaces):

- `references/CONTRACT.md` — the foundation both contracts bind to; if documents disagree, it wins.
- `references/RETRIEVE.md` — the Retriever: agentic search + semantic rank over the ARA's native files.
- `references/PREDICT.md` — the Predictor: grounded, honest answering of the question asked.

## Inputs

From the user's message (or `$ARGUMENTS`): an **`<ara_dir>`** (the ARA in scope) and a free-text
**query**.

## Procedure

1. **Retrieve — adopt `references/RETRIEVE.md`.** Read it now and follow it exactly against
   `<ara_dir>`.
2. **Answer — adopt `references/PREDICT.md`.** Read it now and follow it exactly, consuming the
   retrieval from Step 1.

Render the `answer` prominently, then the honesty envelope (`grounded_inference` /
`speculative_leap` / `basis` / `reasoning` / `confidence` / `confidence_reason` / `falsifiable`).

The engine is read-only: read nothing outside `<ara_dir>` and this skill's `references/`; write
nothing anywhere.
