---
name: research-foresight-cli
description: >
  ARA World Model — read-only reasoning engine over ONE Agent-Native Research Artifact (ARA), run
  LOCALLY with the coding agent itself as the LLM (no SDK, no API key). Given an ARA directory and a
  free-text query, it answers any question about the ARA — a forward "what if I change X", but
  equally why-did-this-work, what-should-I-try, is-this-sound, how-do-these-compare, or anything
  else — by retrieving precedent through ara from the ARA's native files (references/RETRIEVE.md) and answering
  as the Predictor (references/PREDICT.md): a bold, grounded, falsifiable Answer shaped to what the
  question actually calls for.
  TRIGGERS: ask the world model, wm predict, predict with the world model, what if I change X,
  forecast the loss curve, will this help, why did this work, what should I try next,
  is this claim sound, compare these, retrieve precedent, what precedent surfaces.
allowed-tools: Read, Grep, Glob, Bash(ara *)
metadata:
  author: ara-commons
  category: research-tooling
  version: "1.1.0"
  tags: [research, world-model, retrieval, prediction, grounded-answering]
---

# research-foresight — the ARA World Model

## CLI-only access boundary

Every knowledge-layer or root `PAPER.md` read/write in this page uses `ara -C <artifact>`; the
words read, open, search, write, append and edit retain their original procedural meaning,
but never authorize direct knowledge-file tools. For complete source use
`show --document <native-path> --source --full --json` (exact content and SHA-256 digest);
`ls`, `find`, `path`, `refs`, `open` and `status` are access aids, not semantic judgments.
Source/evidence bodies and skill pages remain direct only within the baseline scope.
No direct fallback, automatic semantic retry, new role, or altered stopping rule is allowed.
The entrypoint loads `references/cli-access.md` directly for executable wire details.
Pending protocol review and binary proof remain visible in the variant lock.


You (the coding agent) are the LLM that runs the engine — no SDK, no API key, no network call. The
engine is three reference contracts under this skill's `references/` directory (quote every path;
it may contain spaces):

- `references/CONTRACT.md` — the foundation both contracts bind to; if documents disagree, it wins.
- `references/RETRIEVE.md` — the Retriever: agentic search + semantic rank over the ARA's native files.
- `references/PREDICT.md` — the Predictor: grounded, honest answering of the question asked.
- `references/cli-access.md` — load directly before knowledge access.
- `templates/reader-report.md` — load directly if a standalone report shape is needed.

## Inputs

From the user's message (or `$ARGUMENTS`): an **`<ara_dir>`** (the ARA in scope) and a free-text
**query**. If `<ara_dir>` turns out not to be an ARA (a plain paper, repo, or notes folder),
compile it into one first with `/compiler <path>`, then rerun this skill.

## Procedure

1. **Retrieve — adopt `references/RETRIEVE.md`.** Read it now and follow it exactly against
   `<ara_dir>`.
2. **Answer — adopt `references/PREDICT.md`.** Read it now and follow it exactly, consuming the
   retrieval from Step 1.

Render the `answer` prominently, then the honesty envelope (`grounded_inference` /
`speculative_leap` / `basis` / `reasoning` / `confidence` / `confidence_reason` / `falsifiable`).

The engine is read-only: read nothing outside `<ara_dir>` and this skill's `references/`; write
nothing anywhere.
