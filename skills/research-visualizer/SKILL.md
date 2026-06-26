---
name: research-visualizer
description: |
  Research Visualizer. Renders an existing Agent-Native Research Artifact (ARA) into ONE
  self-contained, interactive HTML file showing the AI scientist's step-by-step research process:
  a clickable process map of the exploration tree (branches and dead ends included) on the left,
  and a per-step drill-down on the right — what the step did (its narrative written in plain language a
  person can follow), why (the linked claim), the real result (verbatim grounded numbers + inline figures
  + tables), and the code/artifact pointer.
  Read-only consumer of the artifact — it never changes how research is done.
  When the ARA carries them, it also surfaces (each optional, only when present) the related-work
  dependency graph, the problem framing, a concepts glossary with in-text term popovers, and the
  solution recipes — reached from header disclosures without leaving the process map.
  Accepts either an existing ARA or raw research input (a paper, repo, run logs, or notes); when the
  input is not yet an ARA it is compiled into one first, then visualized.

  TRIGGERS: visualize, visualizer, trajectory view, render the ARA, see the steps, step-by-step view,
  process map, replay the trajectory, watch the agent work, drill into steps,
  visualize a paper, visualize a repo, visualize a run
argument-hint: "[ara-dir] [--output <path>]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 *|base64 *|find *|ls *|open *)
metadata:
  author: ara-commons
  category: research-tooling
  version: "1.0.0"
  tags: [research, visualization, trajectory, exploration-tree, html]
---

# Research Visualizer

You render an existing ARA into a single portable HTML view of the agent's step-by-step process.
You are a **read-only consumer**: you read the artifact and emit a file; you never edit the ARA.

You operate as a first-class agent — use your native tools directly. The heavy rendering logic is
**already written** in `references/trajectory-template.html`; you do NOT rewrite it. Your job is to
parse the ARA into one `ARA_DATA` JSON object, inline the figures, and inject that object into the
template's data slot.

## What you produce

One self-contained file, default `<ara-dir>/trajectory.html` (override with `--output`):
- All data, tables, and figures (base64) inlined — no server, no network, no CDN. Double-click to open.
- Built by populating the canonical scaffold, so every generated view is structurally consistent.

## v1 boundaries (do not exceed)

- **Post-hoc** visualization of a finished/in-progress ARA. No live/real-time mode.
- **Self-contained from the ARA directory alone.** Do NOT open or inline anything outside the ARA dir.
  `src/artifacts.md` run-store pointers and node `source_refs` (external journal `file:line`) are shown
  **as pointers/chips, not resolved**. (External resolution is a planned future extension — out of scope.)
- **Single ARA.** No cross-ARA comparison.

## Pipeline

1. **Args.** Resolve `<ara-dir>` (default: the ARA in the current working context / most-recently
   referenced). Resolve `--output` (default `<ara-dir>/trajectory.html`).
1b. **Precondition — the input must be an ARA; if it is not, compile it first.** Decide with one
   observable test: does the resolved input expose a parseable `trace/exploration_tree.yaml`
   (**≥1 node**) — directly, or as a standard ARA directory layout?
   - **It is an ARA** → continue to Validate unchanged.
   - **It is not an ARA** — the input is raw research material (a paper/PDF, a code repository, a
     run/log directory, notes, or any directory with no exploration tree) → **invoke the `compiler`
     skill on that input to produce an ARA**, then set `<ara-dir>` to the compiler's output artifact
     and continue. Do not hand-roll an ARA yourself; the compiler is the only path that builds one.
     Default `--output` to `<compiled-ara-dir>/trajectory.html` unless the user set it.
   Only if the compiler still yields no exploration tree does the Validate step's "no process" message apply.
2. **Validate — the exploration tree is the ONLY hard requirement.** Confirm
   `trace/exploration_tree.yaml` exists and parses to **≥1 node**; if not (and the precondition's
   compile step has already run), tell the user there is no process to show (this replaces the old
   `PAPER.md` "is-this-an-ARA?" guard). Everything else —
   `PAPER.md`, `logic/`, `src/`, `evidence/`, and the four enrichment layers — is **optional
   enrichment**: glob whatever is present. If `PAPER.md` is absent, synthesize a minimal `meta` (title
   from a tree-level `title:` or the dir name; empty `abstract` hides the disclosure). This is the
   **raw-trajectory path**: the skill produces a useful step-by-step view from *just the tree* (a raw
   agent run), not only a fully-compiled ARA — see `references/parsing.md` §7.
3. **Parse the trace** into normalized nodes. The field conventions vary across ARAs — follow
   `references/parsing.md` exactly (handles `tree:` vs `root:`, generic vs type-named fields,
   `evidence:` routing, `isolated`, `also_depends_on`). Every node must yield a `title` + `body`.
4. **Parse the hub layers — each only when present (all optional now):** `logic/claims.md` (the
   binding hub *when it exists*), `logic/experiments.md`, `evidence/README.md` (figure/table ↔ claim
   reverse index), `src/artifacts.md`, `logic/solution/*`. A missing layer simply contributes nothing;
   the node still renders from its own `title`/`body`/`thinking`.
   **Also parse the four OPTIONAL enrichment layers when present, per `references/parsing.md` §8:**
   `logic/problem.md`→`context`, `logic/concepts.md`→`glossary` (+ build the `lexicon`),
   `logic/related_work.md`→`dependencies`, `logic/solution/*.md`→`recipes` (role-classify by content, not
   filename). A missing file/dir omits its key entirely. Reproduce statements/deltas/definitions/relations/
   headings/quotes/cells **verbatim**.
5. **Build each node's drill-down.** When `logic/claims.md` exists, follow the claim-hub chain in
   `references/binding.md` (node → `evidence:[C##]` → claims → {Sources quotes, figures/tables,
   experiments, artifact pointers}). When it does **not**, the drill-down is just the node's own
   narrative (`thinking`/`body`) — every claim/result/verified block is empty and omitted.
5b. **Bind the enrichment layers** per the "four enrichment layers" section of `references/binding.md`:
   build `claimIds`/`nodeByClaim`/`conceptNames`/`rwIds`; resolve every `refs[].target` (drop danglers,
   never link off-ARA); derive each node's `built_on`/`rejected_here` (dependency→claim→node, bucketed by
   `relation_norm`), `concepts` (whole-word name-match), and `recipe_refs` (recipe→claim→node); mark
   cross-agent entries. All per-node enrichment fields default `[]`.
5c. **Write each step's narrative as plain language (same layout, human words).** The trace's notes are
   written for an agent; rendered as-is they read like a log and a person can't follow what happened or
   why it mattered. For each node, write its narrative — `thinking`, and `body` if used — in plain
   language a reader who has NOT seen the ARA can follow: your own words, translating the trace's
   agent-facing deliberation, **not** a verbatim paste; expand jargon on first use and state the point,
   not the log line. This changes ONLY the prose that fills the existing reasoning block — keep every
   block and the layout exactly as they are. Stay grounded: introduce no number, name, or claim that is
   not already in that node, and keep claim `Statement`s, `Sources` quotes and table numbers **verbatim**
   in the why/result blocks — those are the receipts.
6. **Inline figures.** For each referenced figure that has a real raster (`evidence/figures/*.png`),
   base64-encode it and put the `data:` URI in `figures[].img`. Use Bash, e.g.
   `python3 -c "import base64,sys;print('data:image/png;base64,'+base64.b64encode(open(sys.argv[1],'rb').read()).decode())" <path>`.
   For data-only figure markdown (no raster), render its data table instead (as a `tables[]` entry).
   **Also inline code diffs + the artifact index:** for each node with `code_change.diff_file`, read that
   tracked `evidence/changes/<id>.diff.md` sidecar and inline its fenced diff text into `code_change.diff`
   (parallel to figures); build the top-level `artifacts[]` index from `src/artifacts.md` so
   `base_artifact`/`variant_artifact` ids resolve; carry each node's `thinking` (the plain-language
   narrative from 5c) through.
   Sanitize all three free-text fields per the Injection contract. The visualizer never computes a diff
   itself and never opens the external store — it only inlines what the ARA already contains.
7. **Assemble `ARA_DATA`** (exact schema in `references/binding.md`) and **inject** it: replace ONLY
   the JSON between `/* __ARA_DATA_BEGIN__ */` and `/* __ARA_DATA_END__ */` in the
   `<script id="ara-data">` block of a copy of the template. Write the result to the output path.
   Include `context`/`glossary`/`dependencies`/`recipes` and the per-node `built_on`/`rejected_here`/
   `recipe_refs`/`concepts` **only when their sources exist** — omit absent keys entirely (no empty
   stubs). A payload omitting all of them stays byte-compatible with the v1.0 schema.
8. **Report** the output path. Optionally open it (`open <path>` on macOS). Print a one-line summary
   (node count, dead ends, figures inlined, which of the four enrichment overlays were emitted with their
   term/dependency/recipe counts, danglers dropped, any pointers left unresolved).

## Injection contract (critical)

- The injected payload MUST be valid JSON (it is read with `JSON.parse`). The template strips only the
  two named marker comments before parsing, so the payload is otherwise pure JSON.
- It must not contain the literal substring `</script>`, nor the literal marker strings
  `/* __ARA_DATA_BEGIN__ */` / `/* __ARA_DATA_END__ */`. Escape any `<` in inlined markdown/text as `&lt;`
  (or `<`) — this also neutralizes `</script>`. (A bare `*/` inside a string value is harmless to
  `JSON.parse`; only the exact marker strings would be stripped.)
- **The verbatim free-text fields `thinking` and `code_change.diff` are the high-risk carriers** (source
  code routinely contains `/* … */`). If either marker token would appear in their text, break it (e.g.
  insert a zero-width space inside `__ARA_DATA_…`) so the global marker-strip can't delete it from inside
  a value. Re-validate: a node whose `thinking`/`diff` contains a marker token MUST round-trip intact.
- Do not touch anything else in the template — only the bytes between the two markers.
- After writing, re-validate: the file still parses (the embedded JSON loads). If a figure pushed the
  file very large, apply the size guards in `references/binding.md` (truncate logs/tables, keep figures).

## Faithfulness (hard rules)

- **Speak human in the narrative, quote the evidence.** A node's narrative (`thinking`/`body`) is plain
  language — your own words, a grounded translation (5c), not a verbatim paste. Everything that is
  *evidence* — claim `Statement`s, `Sources` quotes, table cells/numbers, relations, definitions — is
  reproduced **verbatim** in the why/result/overlay blocks. The narrative explains; the receipts prove. A
  narrative that states a number absent from the node fails; so does an evidence block that paraphrases.
- Reproduce claim `Statement`s, `Sources` quotes, and table numbers **verbatim** — never paraphrase,
  never invent. Missing data → set the field empty/omit (the viewer shows "No …"); never fabricate.
- Provenance, `support_level`, and `status` are shown **only if present** in the source; do not guess.
- Dead-end nodes and `isolated` subtrees must be carried through faithfully — they are the most
  valuable things to display, not noise to drop.
- For the enrichment layers: relation strings, definitions, constraint headings, and footprint citations
  are reproduced **verbatim**; relation enums are open (compound `bounds / refutes` / transition
  `extends → quarantined` kept as written; `relation_norm` is for color only). Never normalize a heading
  or invent a typed sub-field. A `refs[].target` is set only on real in-ARA resolution; dangling refs are
  flagged, never silently corrected or dropped. `built_on`/`concepts`/"used by" name-matches are
  best-effort hints (marked "inferred"), never asserted as facts.

## Verify

Run on any ARA and confirm these properties — no named fixtures required:
- Opens by double-click: no server, no network, no console errors.
- Full process map: nesting, branches, dead ends marked, any `isolated` subtree boxed, `depends_on` chips.
- Drill-down renders whichever blocks are present (what / why / result-with-inline-figure / how-verified /
  code-or-pointer), correctly under **both** field dialects in `references/parsing.md`.
- Verbatim quotes/numbers; nothing fabricated; self-contained from the ARA dir (no needed external refs).
- Re-running reproduces the same structure (data differs only as the ARA differs).
- **Enrichment layers:** a layer's header button appears only when its source exists; an ARA with none of
  the four layers renders identically to v1.0 (no layer bar, no node chips). Open each emitted overlay and
  confirm verbatim relations/definitions/recipe cells, ungrounded/dangling/cross-agent markers, and that
  the `built_on`/`rejected_here` chips + the `⊕/⊘` map marker deep-link into Dependencies. Glossary
  popovers fire on body terms; inline `$LaTeX$` renders with no network.
- **Degradation:** a `minimal-artifact` (only `problem.md`) shows only the Context button, others absent,
  popovers off, per-node chips empty, zero console errors.
- **Compile-first (non-ARA input):** pointing the skill at raw research material with no exploration
  tree (a paper, a repo, a run/log dir) triggers the `compiler` skill first, then visualizes the
  resulting ARA — the output is identical to running the compiler then the visualizer by hand.
- **Raw trajectory (the decoupled path):** a **tree-only** ARA — just `trace/exploration_tree.yaml`, no
  `PAPER.md`, no `logic/`, no `evidence/` — still renders the full process map + each step's narrative
  (`thinking`/`body`), with no layer bar and no claim/result/verified blocks, zero console errors. This
  is a first-class supported input, not a failure mode.

Cover the variant axes with whatever ARAs you have: both root forms (`tree:`/`root:`), both field
dialects (generic / type-named), figures present as real raster vs. data-markdown-only, `src/` as a
pointer index vs. transcribed code, and an `isolated` subtree if any artifact has one.
