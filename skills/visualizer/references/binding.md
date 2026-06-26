# Binding — the claim-hub drill-down chain + the `ARA_DATA` schema

This is the read step. For each normalized trace node you build one drill-down bundle by following
the artifact's **claim-mediated** cross-layer links, then you emit the whole thing as one `ARA_DATA`
object that the scaffold renders.

## Why claim-mediated (and not node → `.py` + table)

Current ARAs usually have **no per-step source file**: `src/` is `artifacts.md` (a pointer index into
an external run store) + `environment.md`. The binding hub is `logic/claims.md`. A trace node points
at claims via `evidence: [C##]`; the claim carries the *why*, the grounded *result* (verbatim
`Sources` quotes with `file:line`), the verification (`Proof: [E##]`), and the figures/tables that
cite it. So the real grounded numbers are **already inside the ARA** — you do not need the external
store (v1 leaves those as pointers).

## Resolution chain (per node)

```
NODE (type, content+outcome, support_level, source_refs, evidence:[C##], also_depends_on, isolated)
  ├─ WHAT        → node title + body (+ outcome) ............................ → node.title / node.body
  ├─ WHY         → evidence:[C##] → logic/claims.md ......................... → node.why[]
  │                 each claim: Statement, Status, Conditions, Falsification,
  │                 Dependencies, provenance
  ├─ HOW VERIFIED→ claim.Proof:[E##] → logic/experiments.md ................. → node.verified_by[]
  │                 each experiment: Run (pointer), Setup, Metrics
  ├─ RESULT      → claim.Sources «quote ← file:line» + Evidence basis ....... → node.result.sources[]
  │              + evidence/README.md reverse-lookup: figures/tables citing C## → node.result.figures[]/tables[]
  │              + evidence/data/*.json (raw, in-artifact) .................. → node.result.data[]
  └─ CODE/ARTIFACT→ src/artifacts.md pointer(s) + logic/solution/* recipe ... → node.artifact[]
```

### evidence/README.md reverse-lookup
`evidence/README.md` has a `Claims` column mapping each figure/table file → the `C##` it grounds.
Build a map `claim_id → [evidence files]` once. For a node, union the evidence of all its claims.
Fallback if no README row: scan the figure/table `.md` for an inline `Supports C##` / `grounds C##`.

### Figures
- Real raster (`evidence/figures/<name>.png` beside the `.md`) → base64-inline into `figures[].img`.
- Data-only figure markdown (no raster) → render its data table as a `tables[]` entry instead.
- A figure's caption/title comes from the first heading or the `What it shows` section of its `.md`.

### What counts as "code" now
There is usually no `src/execution/*.py`. Populate `artifact[]` from `src/artifacts.md` (the run-index
row / `record_configs/` path / named submitted variant file) plus the relevant
`logic/solution/*.md` recipe section. Only when a real transcribed `src/execution/*.py` exists
(legacy / paper-only code) do you point at that file. **Never resolve the external store in v1** —
the pointer text is the value.

## The `ARA_DATA` object (exact schema the scaffold reads)

```jsonc
{
  "meta": {
    "title":  "<PAPER.md frontmatter title>",
    "authors": ["..."],            // [] if none
    "year":   "", "venue": "", "ara_dir": "<dir name>",
    "abstract": "<PAPER.md abstract>"   // "" to hide the Abstract disclosure
  },

  // Traversal order for Replay and ← →. A flat list of node ids in the order to step through
  // (typically a pre-order DFS of the tree). If omitted, the scaffold derives a DFS from `parent`.
  "order": ["N01", "N02", "N03", "..."],

  "nodes": [
    {
      "id": "N02",
      "type": "experiment",        // question|experiment|decision|dead_end|pivot|insight|<other ok>
      "parent": "N01",             // id of the nesting parent, or null for a root
      "title": "<normalized step title>",            // see parsing.md
      "body":  "<what the step did / its outcome>",
      "support_level": "explicit", // "explicit"|"inferred"|null
      "isolated": false,           // true → rendered in a separated dashed box
      "depends_on": ["N00"],       // also_depends_on cross-edges (ids); [] if none
      "source_refs": ["<external path:line — shown as a chip, NOT resolved>"],

      "why": [                     // from evidence:[C##] → claims.md
        { "id":"C01", "title":"...", "statement":"<verbatim Statement>",
          "status":"supported", "conditions":"...", "falsification":"...",
          "dependencies":["C00"], "provenance":"<as stated in source, else null>" }
      ],

      "result": {
        "sources": [ { "quote":"<verbatim Sources quote>", "ref":"<file:line>" } ],
        "figures": [ { "id":"<figure id>", "caption":"...", "kind":"quantitative_plot",
                       "img":"data:image/png;base64,<...>" } ],
        "tables":  [ { "id":"<table id>", "caption":"...", "markdown":"| col | ... |\n|---|...|" } ],
        "data":    [ { "id":"<data id>", "path":"evidence/data/<name>.json", "note":"raw" } ]
      },

      "verified_by": [             // from claim.Proof:[E##] → experiments.md
        { "id":"E01", "title":"...", "run":"<Run pointer text>", "setup":"...", "metrics":"..." }
      ],

      "artifact": [                // src/artifacts.md pointers + solution recipe refs (pointer text only)
        { "name":"<artifact / family name>", "pointer":"<src/artifacts.md pointer text>", "what":"pointer index entry" }
      ]
    }
    // ... one object per trace node
  ]
}
```

### Field rules
- Every node MUST have `id`, `type`, `title`, `parent` (or null). All other arrays default to `[]`,
  scalars to `null`/`""`. The scaffold tolerates missing optional fields.
- Put **only what the source contains**. Empty `why`/`result`/`verified_by`/`artifact` is fine and
  common (e.g. a bare `decision` node) — the viewer simply omits those blocks.
- `status` is lower-cased by the viewer for styling; pass it as written (`Supported`, `hypothesis`, …).

### Size guards
- Inline every figure (they are the point), but cap a single inlined table/log render at a few hundred
  lines; if longer, truncate and append a final row/line `… +N more (truncated)`.
- If the assembled file would be very large, prefer truncating `tables`/`data` text over dropping
  figures, and never drop nodes.

---

# The four enrichment layers — schema additions + cross-linking

These surface `logic/problem.md` / `logic/concepts.md` / `logic/related_work.md` / `logic/solution/*`
(parsed per `parsing.md` §8). **Everything here is OPTIONAL and additive** — omit any key whose source
is absent; a payload with none of these stays byte-compatible with the prior schema and the renderer is
inert for any key it doesn't see.

## Schema additions

A shared **typed-ref** primitive (used by every layer's `refs`/`grounding`):
```jsonc
{ "raw": "<verbatim token, always shown>",
  "kind": "claim|concept|related_work|observation|gap|assumption|experiment|node|source|figure|pr|arxiv|doi|url|unknown",
  "target": "<in-ARA anchor id, or null>" }   // non-null ONLY when it resolves inside THIS ARA
```

Four OPTIONAL top-level keys:
```jsonc
"context": {                 // logic/problem.md ; omit if absent
  "title":"Problem", "summary":"",
  "sections":[ { "role":"setting|observations|gaps|insight|assumptions|other", "heading":"<verbatim H2>",
    "present":true,           // false ⇒ greyed "(not specified)" stub for an expected-but-absent role
    "entries":[ { "ent_id":"O2", "inferred_id":false, "ent_title":"", "text":"<verbatim>",
                  "unstructured":false, "fields":[{"label":"<verbatim>","value":"<verbatim>"}], "refs":[/*typed-ref*/] } ] } ] },
"glossary": {                // logic/concepts.md ; omit ⇒ popovers disabled
  "title":"Concepts", "groups":[{"name":"","term_ids":["G07"]}],
  "terms":[ { "term_id":"G07", "name":"<verbatim, the match key>", "aliases":[], "group":"",
              "definition":"<verbatim, may hold $LaTeX$>", "fields":[{"label":"","value":""}], "related":["G08"], "refs":[] } ],
  "lexicon": { "<lowercased surface>":"G07" } },   // precomputed surface→term_id for popovers
"dependencies": {            // logic/related_work.md ; omit if absent
  "title":"Related Work / Dependencies", "preamble":"", "legend":[{"type":"extends","gloss":""}], "attribution":"",
  "entries":[ { "rw_id":"RW02", "inferred_id":false, "name":"", "relation_raw":"<verbatim, compound/transition kept>",
                "relation_norm":"baseline|imports|extends|bounds|refutes|", "delta":"", "adopted":"",
                "grounding":[/*typed-ref: pr|arxiv|doi|source|url*/], "claims":["C03"], "cross_agent":false, "is_footprint":false } ],
  "footprint":[ {"ref_id":"16","citation":"<verbatim one-liner>"} ] },
"recipes": {                 // logic/solution/* ; omit if dir absent
  "title":"Solution",
  "files":[ { "file":"method.md", "role":"constraints|method|heuristics|algorithm|architecture|recipe", "file_title":"",
    "sections":[ { "sec_id":"", "heading":"<verbatim, never normalized>", "kind":"table|steps|kv|code|math|prose",
                   "markdown":"", "steps":[], "fields":[], "code":"", "text":"<verbatim fallback>", "warn":"", "refs":[] } ] } ] }
```

Four OPTIONAL per-NODE fields (default `[]`):
```jsonc
"built_on":     [ {"rw_id":"RW02","name":"","relation_raw":""} ],   // baseline/imports/extends deps a node's claims cite
"rejected_here":[ {"rw_id":"RW10","name":"","relation_raw":""} ],   // bounds/refutes deps
"recipe_refs":  [ {"file":"","sec_id":"","heading":"","role":""} ], // recipe sections a node's claims cite
"concepts":     [ "<verbatim term name>" ]                          // glossary terms mentioned in this node (popover anchors)
```
Field rules: every new key omittable; `text`/`definition`/`delta`/`value`/relations/headings/quotes/cells
**verbatim**; `relation_raw` always preserved (compound/transition survive), `relation_norm` is color-only
and may be `""`; `target` non-null only on in-ARA resolution (off-ARA `pr`/`arxiv`/`doi`/`§`/file:line stay
`null` → inert chip); no fabrication.

## Cross-linking (the binder runs AFTER nodes + claims are parsed)

The hub stays `logic/claims.md`. All linking is best-effort, computed once into lookup maps, then attached.

- **B.0 anchors:** `claimIds` (the `## C\d+` set), `nodeIds`, `nodeByClaim` (invert each node's `why[].id`),
  `conceptNames` (lowercased `glossary` names+aliases), `rwIds`.
- **B.1 claim-ref resolution (single pass over all layers' refs):** `kind:"claim"` ref → `target` if
  `∈ claimIds`, else `target:null` and **flag dangling** (renderer greys it "broken link" — never a live
  dead link). Same for `related_work`/`concept`/`node` targets against their id sets.
- **B.2 dependencies ↔ claims/nodes:** forward edge is in-data (`entries[].claims[]`). Build the reverse
  `claim_id → [rw_id]`; also harvest `claims.md`'s own `**Dependencies.**` lines as extra rw-edges (so the
  edge exists even when related_work omits the back-ref).
- **B.3 per-node `built_on` / `rejected_here` (the chips):** `rwSet = ⋃ over n.why[].id of reverse(claim→rw)`.
  For each rw, bucket by `relation_norm`: `∈{baseline,imports,extends}` → `built_on`; `∈{bounds,refutes}` →
  `rejected_here`; `""`/transition → first keyword, default `built_on`, **keep `relation_raw` literal**.
  Dedupe by `rw_id`; empty buckets stay `[]` (no chip row). Cross-agent deps render a distinct "↔ other-agent"
  ribbon.
- **B.4 concepts ↔ everything:** concepts are leaf provenance (no `trace:N` refs). Build `node.concepts[]` by
  **sideways name-match** — whole-word, case-insensitive scan of each node's `title`+`body`+claim statements
  against `conceptNames`. The Concept overlay's "used by" is that scan inverted, marked **"mentions
  (inferred)"** and visually distinct from id-resolved links. Outbound concept `refs` resolve normally.
- **B.5 recipes ↔ claims/nodes (`recipe_refs[]`):** a node's `recipe_refs` = recipe sections whose `refs[]`
  cite one of the node's `why` claims (∪ sections a node's claim cites back); dedupe by `(file,sec_id)`.
  Unresolvable `C##` ⇒ inert muted chip ("referenced but not linked"), never dropped.
- **B.6 determinism & cost:** all maps built once, O(nodes+claims+refs); stable source order; a wrong/no
  match never blocks rendering. The browser-side `lexicon` is precomputed so no source regex runs at runtime.
