# Parsing tolerance — normalize the exploration tree across ARA variants

The canonical `exploration-tree-spec.md` uses **generic** field names; many real artifacts instead
use **type-named** fields. Parse against the *model*, tolerate the *variants*. Never
hardcode to one example; never assume a fixed field set. The goal: **every node yields an `id`,
`type`, `title`, `body`, and a `parent`** (plus optional metadata), no matter which dialect.

## 1. Root form

Accept both:
- `tree:` → a **list** of root nodes (canonical).
- `root:` → a **single** root node. Treat it as a one-element root list.

Children nest under each node's `children:` list. A node's `parent` is the nearest enclosing node;
top-level nodes have `parent: null`.

## 2. Node identity & type

- `id` — required (any stable identifier the tree uses, e.g. `N01`, `E07`). Keep verbatim.
- `type` — one of `question | experiment | decision | dead_end | pivot | insight` (or anything else;
  unknown types still render with a neutral glyph). Keep verbatim.
- `support_level` — `explicit | inferred` if present, else `null`.
- `source_refs` — list of strings if present, else `[]`. **External pointers; shown, never resolved.**
- `isolated: true` — carry through (renders in a separated box).
- `also_depends_on: [ids]` → emit as `depends_on` (DAG cross-edges).
- `thinking` — verbatim agent deliberation, **passed straight through** (the primary reasoning block).
  Absent ⇒ omit. Never paraphrase or synthesize it.
- `code_change` — when the compiler wrote one onto the node (`base_artifact` / `variant_artifact` /
  `lang` / `diff_file`), **pass it through**. The `diff_file`→`diff` inlining and the top-level
  `artifacts[]` index are done in the binding/inline step (binding.md); the visualizer never computes a
  diff itself. Absent ⇒ omit.

## 3. Title + body normalization (the dialect bridge)

For each node, derive a **display title** and a **body** by probing known fields **in order**, per type.
Use the first non-empty match; fall back gracefully so nothing is blank.

| type        | title — try in order                          | body — try in order                                   |
|-------------|-----------------------------------------------|-------------------------------------------------------|
| question    | `title` → `question`                          | `description` → `question` (if used as title, leave body empty) |
| experiment  | `title` → first sentence of `experiment`      | `result` → `outcome` → `experiment`                   |
| decision    | `title` → first sentence of `decision`        | `choice` (+ `alternatives`) → `decision`              |
| dead_end    | `title` → first sentence of `dead_end`        | `failure_mode`/`why_failed` (+ `hypothesis`,`lesson`) → `dead_end` |
| pivot       | `title` → `trigger`                           | `from` → `to` → `trigger`                              |
| insight     | `title` → first sentence of `insight`         | `description` → `insight`                              |
| *(other)*   | `title` → `<type>` field → `description`       | the `<type>` field → `description`                     |

Rules:
- "first sentence of X" = X truncated at the first `. ` or ~80 chars — only when there is no separate
  `title`. If a single field is both the only content and long, use a truncated form as title and the
  full text as body.
- `decision`: append `alternatives` to the body as "alternatives: a; b" when present.
- `dead_end`: prefer to show *why it failed* in the body — it is the most valuable content.
- Never emit an empty title. If truly nothing usable, use the `id`.

## 4. `evidence:` routing

A node's `evidence:` (and a decision's `evidence:` string) may mix kinds. Split tokens and route:
- `C\d+` → claim IDs → drive the `why` / `result` binding (see `binding.md`).
- `Figure N` / `Table N` / a figure/table filename → evidence file refs → `result.figures`/`tables`.
- `§...` / prose → keep as a `source_refs`-style chip (context only).

## 5. Provenance

May appear as:
- a per-claim `provenance:` / `Provenance:` field, **or**
- prose in the `claims.md` header ("all claims are `ai-executed`; C06, C08 are `user-revised`").

Capture whichever exists and attach the right tag to each claim in `why[]`. If neither exists, omit
provenance — do not guess.

## 6. Claims, experiments, evidence index (the hub layers)

- `logic/claims.md` — split on `## C\d+` headings. Pull `Statement`, `Status`, `Conditions`,
  `Falsification criteria`, `Proof` (→ `E##`), `Sources` (verbatim «quote» + `← file:line`),
  `Dependencies`. Field labels are bold-prefixed (`**Statement.**` or `- **Statement**:`) — match both.
- `logic/experiments.md` — split on `## E\d+`. Pull `Verifies` (→ `C##`), `Run`, `Setup`, `Metrics`.
- `evidence/README.md` — parse the Tables/Figures index to build `claim_id → [evidence files]`.

## 7. Degrade, don't fail — the tree is the only hard requirement

Any missing/oddly-shaped field → fall back per the tables above and continue. A smaller honest view
is correct. **Hard-stop on exactly one condition: `trace/exploration_tree.yaml` is absent or parses to
zero nodes** (nothing to show). Minimal-validity guard = *the tree parses AND yields ≥1 node* — this
replaces the old "`PAPER.md` missing ⇒ not an ARA" guard, which no longer hard-stops (a missing
`PAPER.md` just means the visualizer synthesizes a minimal `meta` from a tree-level `title:` / the dir
name). Everything else — `logic/`, `evidence/`, `src/`, the four enrichment layers — is optional; absent
⇒ contributes nothing, never an error.

### 7a. Raw-trajectory input mode (first-class)

The minimum a node needs to render a useful step is `id` + (`title` **or** a type-named text field);
`body` / `thinking` are optional but make the step legible. So a **bare exploration tree with no
`logic/`, no `evidence/`, and no `PAPER.md`** — i.e. a raw agent run — is a fully supported input, not a
degraded one. Each node renders from its own normalized `title` / `body` (per §3) plus its `thinking`
(the agent's deliberation, when the source carries it — a verbatim pass-through field); the
`why` / `result` / `how-verified` blocks are simply empty and omitted.

**Adapter recipe (generic agent run → minimal tree).** A typical agent log is a sequence of steps, each
a `{thought, action, observation/result}`. Map it onto the tree:
- one tree node per step (or per meaningful decision/experiment); `id` = the step index/label.
- `type` from the step kind: a tried approach → `experiment`; a chosen direction → `decision`; an
  abandoned/failed approach → `dead_end`; an opening/guiding question → `question`.
- `title` = a one-line summary of the step (first sentence of the action, ≤80 chars).
- `thinking` = the agent's thought/deliberation for the step (**verbatim** — why it did/branched).
- `body` = what it actually did + what came back (action + observation).
- `source_refs` = a pointer back to the log line(s) (shown, never resolved).
- nesting via `children`; convergence via `also_depends_on`; a discarded branch via `isolated`.

No `logic/` or `evidence/` is required; enrich the same tree later (via the compiler) to add claims,
evidence, and per-node `code_change` diffs.

# 8. The four `logic/` enrichment layers (all optional)

These produce the OPTIONAL `context` / `glossary` / `dependencies` / `recipes` keys (and the per-node
`built_on` / `rejected_here` / `recipe_refs` / `concepts` fields, derived in `binding.md`). **Each is
independent and absent ⇒ omit its key entirely** (no empty stubs). The renderer is inert for any key
it doesn't see, so an ARA with none of these renders exactly as before.

**Governing rule — classify by markdown SHAPE + generic cross-ref regexes; NEVER key on field
vocabulary.** Do not look for "optimizer", "Fig.", "loss", "shortcut", etc. — only headings, bold-lead
labels, id tokens, and the ref battery below. Verbatim everywhere: `text`/`definition`/`delta`/`value`,
all numbers, quotes, table cells, relation strings, and headings are reproduced exactly; a missing
field is `""`/`[]`; positive-absence signals (`present:false`, `unstructured`, `is_footprint`,
`inferred_id`) are *shown*, never invented.

## 8.0 Shared sub-routines (define once, reuse for every layer)

- **`splitEntries(sectionText)`** — try delimiters in order, take the first that yields ≥1 hit:
  (a) `^### ` H3 headings; (b) `^## ` with a leading id token (`^##\s*([A-Za-z]{1,3}\d+|RW\d+|[OGA]\d+)`);
  (c) top-level bold-lead bullets `^\s*-\s*\*\*(.+?)\.?\*\*`; (d) blank-line-separated paragraph blocks.
  (d) always succeeds ⇒ prose-only dialects still yield entries.
- **`probeFields(entryText)`** — collect every `^\s*-?\s*\*\*([^*]+?)\*\*\s*[:—]` labeled leader into an
  **open** `[{label,value}]` list. **Labels verbatim, no whitelist.** Empty ⇒ `unstructured:true`,
  `fields:[]`.
- **`harvestRefs(text)` → `typed-ref[]`** — run the FULL union of patterns; never assume one scheme.
  The shared **typed-ref** is `{ "raw":"<verbatim token>", "kind":"…", "target":null }`; `target` is set
  later in the binding pass (it stays `null` for anything that doesn't resolve inside this ARA).

  | pattern | kind |
  |---|---|
  | `\[?\b(C\d{1,3})\b\]?` (optionally `(claims.md…)`) | `claim` |
  | `\bRW\d{1,3}\b` | `related_work` |
  | `\b([OGA])\d{1,3}\b` | `observation` / `gap` / `assumption` |
  | `\bK\d{1,3}\b` or a minted term-id | `concept` |
  | `PR\s*#?\d+` | `pr` |
  | `arXiv[:\s]\S+` | `arxiv` |
  | `10\.\d{4,}/\S+` | `doi` |
  | `[\w./-]+\.\w+:\d+(?:-\d+)?` · `trace:N\d+` · `logic/\S+#\w+` | `source` / `node` |
  | `§[\w".]+` · `Table\s*\S+` · `Fig\.?\s*\S+` · `Eqn\.?\s*\S+` | `figure` |
  | `https?://\S+` | `url` |

## 8.1 `logic/problem.md` → `context`
Absent ⇒ omit (do NOT fabricate context from claims). Split on `^## `; classify each heading by a
**case-insensitive role-synonym map** (NOT exact names): `setting ⇐ {setting,task,constraints,
background,context,problem statement}`; `observations ⇐ {observation*,findings,evidence}`;
`gaps ⇐ {gap*,open question*,challenges,limitations of prior work}`; `insight ⇐ {key insight,insight,
core idea,approach,thesis}`; `assumptions ⇐ {assumption*,scope,caveats}`. Unmatched ⇒ `role:"other"`,
heading kept verbatim, **never dropped**. **Merge** same-role sections. Any canonical role that never
appeared ⇒ emit a `{present:false}` stub (signals the compile, greys the chip). Per section run
`splitEntries`; `ent_id = \b([OGA]\d+)\b` (width-agnostic) else positional + `inferred_id:true`;
`ent_title` = text to the first `:`/`—`/`.` else first sentence; `probeFields` (empty ⇒
`unstructured:true`); `text` = verbatim body (mandatory); `harvestRefs`. `summary` = the insight
entry's first sentence (else `""`).

## 8.2 `logic/concepts.md` → `glossary`
Absent ⇒ omit (⇒ popovers globally disabled). **Detect grouping:** a `##` is a *group* (not a term)
iff it has no `—`/`:` id-separator AND the next non-blank line is a `- ` bullet AND no following
`**Definition`. Split terms via `splitEntries` (`^##\s+(.+)$` → `^- \*\*(.+?)\.?\*\*` → paragraphs).
Per term: `term_id` = leading `^(K|C|RW|[A-Z]{1,3})\d{2,}` before the separator, else **mint**
`G01,G02,…` positionally (a stable popover anchor); `name` = heading minus id/separator (mandatory);
`aliases` = split a trailing `(…)` and `/`; `definition` = `**Definition**:` value else whole body
(mandatory); `probeFields` (captures resnet-style `Notation`/`Boundary conditions`; nothing for
codex/ptb — correct); `related` = any `/relat/i`-labeled field split on commas (resolved to `term_id`s
in binding); `harvestRefs`. **Build `lexicon`** = lowercased `name` + each alias → `term_id`, skipping
tokens <3 chars and pure-numeric aliases, first-wins on collision (the renderer uses it for popovers).

## 8.3 `logic/related_work.md` → `dependencies`
Absent ⇒ omit. Strip the preamble before the first `## ` → `preamble`; parse `**word** (gloss)` pairs →
`legend[]`; capture a `> **Cross-agent attribution.**` blockquote → `attribution`. Split on `^## `,
match `^##\s*(RW\d+)?\s*[—:-]?\s*(.*)$`. If a heading has no `RW\d+` and matches `/brief|additional
referenced|citations/i`, parse its bullets into `footprint[]` (`{ref_id,citation}`) and skip structured
probing (`is_footprint` entries, or just the `footprint` tail). Per entry: `relation_raw` from a
` — **type** ` in the heading ELSE a `**Type:**` line — **kept verbatim**, incl. compound
(`bounds / refutes`) and transition (`extends → quarantined`); `relation_norm` = the first of
`{baseline,imports,extends,bounds,refutes}` found, else `""` (color only); `name` = heading after the
separator; `delta` = `**Delta**`/`What changed:`+`Why:` (concatenate) else body; `adopted` =
`**Adopted elements**`; `grounding`/`claims` = `harvestRefs` partitioned by kind; `cross_agent:true` if
the entry is named in `attribution` or its relation mentions another agent. Unnumbered ⇒ positional +
`inferred_id`. **Degrade:** an entry with no source and no claim keeps `grounding:[]`+`claims:[]` (the
renderer shows a muted "ungrounded").

## 8.4 `logic/solution/*` → `recipes`
Glob `logic/solution/*.md`; dir absent ⇒ omit. **Role-classify each file by content signal (priority):**
filename `constraints.md` → `constraints`; filename `method.md` OR title `/method|recipe|procedure|
process|pipeline/i` → `method`; uniform `^##\s*[A-Z]\d+:` entries → `heuristics`;
`## Mathematical formulation`/pseudocode fence/`$…$` → `algorithm`; repeated component `###` micro-schema
→ `architecture`; else → `recipe`. (Only the `constraints.md` filename is special — a universal ARA
convention, not a field term.) Split each file on `^## ` (recurse `###`). **`heading` kept verbatim —
never normalized.** Per section pick the **dominant `kind`** in order: table `| … |` → `table`
(`markdown`); typed bullets `- **K**: v` → `kv` (`fields`); numbered `^\d+\.` → `steps`;
fenced/ASCII-DAG → `code`; `$$…$$`/`$…$` → `math` (put TeX in `code`); else → `prose`. `text` = verbatim
body (mandatory fallback); `sec_id` = leading id; `warn` = body under a `/confound|cut-off|incomplete|
not specified|unverified/i` heading; `refs` = `harvestRefs` (harvest **bare** `C05` too, not only
`[C05]`). **Degrade:** only `constraints.md` present ⇒ render just it (no "method missing" stub);
`method.md` absent but `algorithm.md`/`architecture.md` present ⇒ those carry the method role.

## 8.5 Universal absence rule
Each key is independent; any combination is valid. A `minimal-artifact` (only `problem.md`+`claims.md`)
yields `context` only — `glossary`/`dependencies`/`recipes` omitted, all per-node enrichment fields
`[]`, nothing errors.
