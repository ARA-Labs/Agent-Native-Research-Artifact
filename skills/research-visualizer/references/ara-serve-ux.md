# Using the `ara serve` viewer

What the browser page actually does once it's open — pass this along (or the relevant bits) when
you hand the user a URL, especially if they haven't used the viewer before.

## Layout

Two panes: **map** (the exploration graph) and **detail** (the selected node's drill-down). A
header toolbar holds search/filter, a **stack | split** layout toggle, and a **graph | tree**
display toggle.

- **Stack** (default) — map on top (full width), detail below. **Split** — map left, detail
  right. Below ~800px width it always collapses to one column regardless of the toggle.
- The divider between panes is **draggable** to rebalance them; **double-click it** to reset to
  the default ratio.
- **Graph** (default) — the interactive SVG DAG. **Tree** — an indented list view (same rows,
  same selection, no pan/zoom) — useful for tab-order reading or feeding a screen reader, or just
  when a wide DAG is awkward to navigate as a graph.

## The graph pane

- **Pan**: click-drag on empty space. **Zoom**: mouse wheel (clamped so you can't zoom past
  useless extremes).
- **Select a node**: click it, or Tab to it and press Enter/Space (every node is keyboard
  focusable). Selection drives the detail pane on the right/below.
- **Read the shape, not the color**: node kind is a glyph + label — `Q` question, `✦` experiment,
  `→` decision, `✗` dead end, `!` insight, `•` other. Color is used for exactly one thing: dead
  ends are shown in the warning color with strikethrough. This is deliberate (colorblind-safe) —
  don't expect other node kinds to be color-coded.
- **Edges**: solid = parent/child, dashed = `depends_on`.
- Hovering a row in tree mode highlights what it depends on.

## The detail pane

Selecting a node shows, in order (each block omitted if the ARA has no data for it):
header (id, title, kind, `support_level`, `isolated` pill if applicable) → description →
type-specific fields (an `Experiment` shows its result; a `Decision` shows choice → rationale →
alternatives; a `DeadEnd` leads with `why_failed`) → evidence/claims with
supported/refuted/hypothesis status → **BUILT ON** chips → **DEPENDS ON** chips (click one to
jump straight to that node) → results (figures/tables/captions) → source-ref provenance chips.
Collapsible sections (`<details>`) show an item count so you know there's more before opening it.
An empty node just says "Nothing recorded for this node."

## Toolbar controls

- **Search** — case-insensitive, matches label/id/kind/bound-claim text as you type.
- **Type filter** — a dropdown of the node kinds actually present in this ARA.
- **Dead ends only** — checkbox.
- Filtering **dims** non-matching nodes rather than removing them, so the graph's shape stays
  stable while you narrow in. Filtering and selection are independent — you can select a dimmed
  node.

## Replay stepper

`‹ prev` / `▶ Replay` (toggles to `⏸ Pause`) / `next ›` walks the shared selection through nodes
in the ARA's own order (pre-order, i.e. how the trace was written). Play auto-advances every
1.3s and stops at the last node (no looping). Left/Right arrow keys do the same prev/next, unless
a search box is focused. This is the fastest way to "just replay the run" front-to-back without
manually clicking through the graph.

## Header disclosures

When the ARA carries them, the toolbar surfaces **Context**, **Glossary** (term cards with
notation/definition/boundary/related), **Dependencies**, and **Solution files** as modal
disclosures, each with a count badge. An ARA without a layer simply has no button for it.

## Things it won't do (yet)

- No per-step plain-language narrative ("what this did / why it mattered") — the detail pane shows
  the ARA's structured fields as written. No inline figure images or verbatim exhibit tables
  (sources render as name chips), no in-text glossary popovers or per-node concept chips, no
  per-node code/artifact pointers. These are tracked as `ara-cli` enhancement issues; until they
  land, export mode is the view that has them.
- No LLM calls, ever, at view time — everything above comes straight from the ARA's own files.
- Selection/pan/zoom/filter state is in-memory only (resets on a full page reload, though it
  survives a live-reload triggered by an edit — see the main SKILL.md).
