# Agent CLI write and merge contracts
**Date:** 2026-10-01

## TL;DR

The implementation plan is approved; F1 through F7 and the detailed choices below await upstream PR review. No approval or merged protocol revision has been recorded. The contract proposal preserves native references and exact historical text, restricts edits to named transitions, and records every imported identity in portable artifact files. CLI-backed skills need reviewed decisions and pinned binary proof for every required operation before passing integration review.

## Problem

The live project manager (PM) must update sessions, mark stale observations, attach taste comments, and preserve complete logic revision history. The baseline also calls trace and staging immutable. A writer needs explicit exceptions rather than a general permission to edit YAML. Directory merges need an import record even when an imported ID did not change, because local IDs and display labels do not establish fork identity.

The exact source is remote commit `e52a925e9d03b4ada3008653e72f99b04116fca2`. The [source lock](../evaluation/agent-cli/source-lock.json) records its unchanged bytes and reference closure. The [operation inventory](../evaluation/agent-cli/operation-coverage.json) covers research-foresight, compiler, and research-manager. The [baseline contract](../evaluation/agent-cli/baseline-contracts.md) records source contradictions without changing either experiment condition's procedures.

## Constraints

Every rule introduced here is a proposed disposition, not a statement that upstream accepted it. [protocol-decisions.json](../evaluation/agent-cli/protocol-decisions.json) records F1 through F7 separately with `upstream_status: pending-review`, `approved_revision: null`, consumers, and review gates. Implementations may exercise these choices on disposable fixtures, but release and skill-variant review must expose their pending status. Do not silently substitute plan approval for protocol approval.

Readers remain read-only and PM remains the sole live writer. Compiler owns initial compilation and `logic/experiments.md`; this proposal does not transfer experiment-plan ownership to PM. Source/evidence body access remains direct where the pinned skill permits it. No LLM, online service, semantic deduplication, global entry-ID scheme, viewer change, collective writer role, or scored experiment is part of this contract.

## Proposed approach

### Which decision is being proposed

| Decision | Concrete disposition for review | Consumers | Approval state |
|---|---|---|---|
| F1 | Append-only aliases plus a portable merge ledger record all source-qualified import identities, including identity mappings. Alias chains resolve without cycles. | Guarded writes, batch apply, directory merge | Pending upstream review |
| F2 | Keep ordinary local IDs. Establish a stable explicit source key separately from display label and source revision; recognize shared ancestry only from verified base content. | Directory merge | Pending upstream review |
| F3 | Preserve atomic in-place promotion pointers. Agreeing target and closure tuples converge; differing tuples remain conflicts. | Staging, batch apply, directory merge | Pending upstream review |
| F4 | Permit only the detailed transitions below, including full session history, rolling session views, staleness, additive annotations, and audited protected repair. | Guarded writes, staging/sessions, batch apply, directory merge | Pending upstream review |
| F5 | Append `same_as` from a later trace node to an earlier distinct node, without removing either or creating a directed cycle. | Same-as links, graph reads, merge | Pending upstream review |
| F6 | Preserve complete claim fields, native concept identities, arbitrary document bodies, and optional node `artifacts`/`concepts`. | Agent read model, read commands, writer, CLI-backed skills | Pending upstream review; issues 61/62/63 remain separate viewer work |
| F7 | Change only access instructions in CLI-backed copies after complete coverage proof. Preserve reader isolation, PM ownership, compiler procedures, and all epistemic rules. | CLI-backed skills, external evaluation | Pending upstream review |

### How selectors preserve native identity

Selectors consist of an artifact-relative path and, where needed, a native ID or a section heading path. `trace:N109`, `logic/claims.md#C05`, `logic/concepts.md#warmup-schedule`, and `logic/solution/method.md#step-3` remain valid native references. The existing observation pointer spelling `logic/claims.md:C07` is also retained. Concept names, unnumbered related-work entries, problem subsections, and arbitrary solution headings are not assigned invented numeric IDs. Problem `O1` headings are scoped to `logic/problem.md` and are not staging `O01` identities.

Full reads expose the exact complete source body as well as any parsed fields. Unknown fields, prose, equations, comments, order, quotes, and pending markers are retained. A structured section selector names the full heading path or a unique native anchor; an ambiguous repeated heading rejects with candidates rather than choosing the first. Document selectors include `PAPER.md`, every `logic/` document, complete sessions/indexes/reasoning/taste files, and explicitly registered additional knowledge documents. A machine representation never replaces the body needed for grounding.

### Where initialization and root writes stop

The `artifact.init` operation is a bounded bootstrap, not a generic filesystem writer. The PM seed profile contains the directories in the baseline initialization clause and `PAPER.md`, `trace/sessions/session_index.yaml`, `trace/exploration_tree.yaml`, `trace/pm_reasoning_log.yaml`, `staging/observations.yaml`, `logic/claims.md`, `logic/problem.md`, `logic/solution/heuristics.md`, and `evidence/README.md`. The compiler seed profile contains the mandatory core: root PAPER, problem, claims, concepts, experiments, related work, solution constraints, source environment, exploration tree, and evidence index. Actual input supplies the complete content and evidence afterward. Initialization never asserts completed compilation or Seal success.

Initialization defaults to strict new-or-empty-root behavior (`missing_only: false`). Explicit `missing_only: true` supports a partially populated artifact: create absent seeds only and retain every existing generated-default file byte-identically, even when its content differs from the default. Caller-supplied PAPER or document content must match an existing file's bytes exactly or reject the complete batch. Raw source and evidence files remain untouched. Final artifact validation still applies; this mode is not implicit reinitialization or overwrite permission.

`PAPER.md` is the only implicit root knowledge document. Its frontmatter and body can be created or revised with caller-authored exact before/after history and Layer Index consistency. `rubric/requirements.md` is the fixed additional knowledge path. Other source-warranted knowledge files require caller-supplied `knowledge_paths: [relative/path.md]` in PAPER frontmatter through paper edit or initialization. Registration accepts normalized relative Markdown paths only and rejects duplicates, symlinks, special files, absolute paths, path escape, and reserved `src/`, `evidence/`, `trace/`, `staging/`, `.git/`, and `.ara/` namespaces. Registered documents use the same guarded complete-body/section operations and exact source digests as logic documents. The CLI never infers registration or grants generic filesystem access. Source, data, and evidence bodies retain the pinned skill's direct-access rules.

`paper.edit` accepts an optional strict `audit` RevisionContext with `session`, `turn`, `signal`, `provenance`, and optional `note`. When supplied, it records the complete actual PAPER bytes before and after the edit and requires the owning session's next turn in the same atomic batch. Source-conformant PM/compiler revisions supply this audit plus the owning `session.log`. Omitting the low-level audit does not fabricate historical metadata; initialization does not invent a prior PAPER revision.

### What may change after initialization

The table is the complete proposed permission list. Missing permission means reject, not infer intent. Creation retains the full supplied payload. Each accepted transaction validates selectors, field kinds, native references, graph constraints, and history before publishing any file. Rejected transactions leave artifact bytes, aliases, merge records, and conflict records unchanged.

| Object or field | Permitted transition | Required history and bounds |
|---|---|---|
| `logic/` complete bodies and sections | Create, revise, split, merge, generalize, or replace source-grounded present-state prose and typed fields. | PM/compiler existing-knowledge revision uses `logic.revise` with complete Body/fields and its owning `session.log` in one atomic batch. Caller supplies exact before/after, actual signal, turn/session, and provenance; preserve untouched spans and unknown fields. |
| `logic/experiments.md` | Compiler create/revise only; directional plans with full Setup/Procedure and Run/Evidence links. | PM has no write path here. No taste attachment. Exact results stay in evidence. |
| Claim status | Source transition rules, with `revised` recorded as a transition and resting state `testing` or `hypothesis`. | `refuted`/`withdrawn` require explicit signals; revival requires explicit user direction. Supported-to-weakened contradiction is flagged rather than inferred. |
| Typed rename | Change an existing logic ID or concept/section identity, update modeled mutable inbound refs, and append a redirect from each old selector. | Full before/after for every changed entry; historical references stay byte-identical and resolve through redirects. A missing/ambiguous target, redirect cycle, or unsupported inbound reference prevents the rename. |
| Typed remove | Claims use source withdrawal/merge semantics and retain the old entry. Other current-state removal uses an existing replacement redirect when references remain; `to: null` is allowed only after proving no remaining typed or historical reference to the removed locator. | Archive exact removed bytes in session history regardless. Validate the complete final candidate and reference inventory. Never remove trace/staging/session/taste/reasoning history or leave a referenced locator dangling. |
| Existing observation | Set `promoted`, `promoted_to`, and `crystallized_via` atomically once, or repeat the identical tuple. | Content, context, original provenance, timestamp, potential type, and bindings remain unchanged. Target must exist in the same transaction. |
| Observation `stale` | `false` or absent to `true` after neither promotion nor reference for at least three session-days. | Record the relevant days/references and reason. No automatic deletion or promotion; unsetting stale is not implied by this rule and requires explicit audited adjudication. |
| Trace cross-edge | Append a validated `also_depends_on` target. | Never remove or replace an earlier edge. Reject missing target, self-link, duplicate logical edge, or cycle including parent/nesting edges. Record relation append reason. |
| Trace same-as | Append distinct earlier target to later node's `same_as`. | Keep both nodes, content, and provenance. Reject self-link, missing target, duplicate, or directed same-as cycle. Writer direction uses available timestamp or append-order evidence; readers do not invent chronology or rewrite legacy source. |
| Conflict annotation | Append `<!-- CONFLICT: see REF -->` to logic or `# CONFLICT: see REF` adjacent to a trace/staging record. | Retain prior body and comments, target refs, positive conflicting evidence, and unresolved decision node. No field-content edit disguised as a comment. |
| Session historical arrays | Append `events_logged`, `ai_actions`, `claims_touched`, `logic_revisions`, and `key_context` records to the active same-date session. | Earlier records stay unchanged. Exact `before`/`after` strings and their signal/provenance remain intact. |
| Session rolling lists | Replace the complete `open_threads` and `ai_suggestions_pending` views, or append where appropriate. | Archive exact prior/new lists in the append-only reasoning log with session/turn and reason; completing a thread does not erase its history. |
| Session current metadata | Update `last_turn`, `turn_count`, and rolling `summary`. | `id`, `date`, and `started` are stable. Archive prior/new values in reasoning entries. `last_turn` and count advance monotonically under one writer; no undocumented old-day edit. |
| Session index | Create/update that session's `summary`, `turn_count`, `events_count`, `claims_touched`, and `open_threads` count. | Recompute from its complete session; preserve other rows, identity/date, and prior/new row in reasoning history. Path is `trace/sessions/session_index.yaml`. |
| PM reasoning log | Append complete `entries` with `turn` and all `notes`. | Keep chosen/rejected signals, near-misses, organizing decisions, metadata/list history, and provenance. Never rewrite earlier notes. |
| Logic taste | Append inline Taste bullet to an existing claim or heuristic only. | Confirm target first; exact user comment, date, attitude, object of judgment; no prior bullet edits, status change, or provenance upgrade. |
| Trace taste | Append a `Txx` record to `trace/taste_log.yaml`. | Target an existing experiment/decision/dead_end/pivot, never a question; retain timestamp, target, attitude, object, and verbatim user comment. Never edit target node. |
| Import/redirect/conflict histories | Append records under the formats below. | Preserve every earlier record and full candidate bytes; no cache-only identity or status replacement. |
| Protected historical repair | Explicit audited `merge repair` records captured immutable conflict evidence and either rejects incoming content or restores the exact previously captured base. | Retain every competing body. Require exact current fingerprint, full before/after session history, reason, and immutable decision record. Arbitrary new immutable text is not permitted; corrective history is a separately linked append. |

Compiler coverage repair revises existing logic and root manifest through caller-authored `logic.revise` Body/fields and `session.log` in one atomic batch. Low-level `document.replace` changes bytes but does not invent before/after history, research signals, or provenance; it is not a source-conformant PM/compiler revision by itself. Initial document creation and initialization do not fabricate a prior revision. During compilation, the compiler can append source-grounded trace nodes, but an existing immutable payload needs the explicit protected repair path rather than a silent validation fix.

### Which source dialects writers must understand

| Object | Scalar/text fields | Sequence, mapping, and reference fields |
|---|---|---|
| Trace node | `id`, `type`, `title`, `timestamp`, `provenance`, `support_level`, `description`, `choice`, `result`, `hypothesis`, `failure_mode`, `lesson`, `from`, `to`, `trigger`, `status`, `parent`, optional verbatim `thinking` | `children` node sequence; `alternatives`, `source_refs`, `also_depends_on`, `same_as` sequences; `evidence` permits the pinned scalar-prose and sequence dialects; optional `artifacts` sequence of `{name,pointer,what}` with unknown extra fields retained; `concepts` sequence of existing exact concept-name identities or native concept refs, never minted numeric IDs. |
| Observation | `id`, `timestamp`, `provenance`, complete `content`/`context`, `potential_type`, boolean `promoted`/`stale`, nullable text `promoted_to`/`crystallized_via` | `bound_to` node-ref sequence; absent additive fields remain absent until used. |
| Claim | Complete Markdown Statement/Conditions/Provenance/Falsification or Falsification criteria/Evidence basis/Status/Tags/Last revised and additional prose | Preserve Proof/Dependencies/Sources/Taste structures and original spelling; do not split prose solely on commas. PM Proof may contain native evidence refs; compiler Proof uses experiment IDs. Both dialects remain readable and round-trip without conversion. |
| Heuristic | Complete Rationale/Sensitivity/Bounds/Status/Provenance/Source/Last revised | Preserve Code ref/Sources/Taste including source quotes and unknown fields. Compiler has Bounds/Source; PM adds current status/provenance. Missing fields are not guessed. |
| Concept, related work, problem, solution | Exact heading/section identity and arbitrary Markdown/LaTeX body | Native concept-name links; existing `RWxx` blocks where present, otherwise path/heading identity; problem O/G/A selectors scoped to their document. |
| Experiment plan | Native `Exx` heading and full Setup/Procedure/Metrics/Expected outcome or Expected results/Baselines | Verifies claims; Evidence and Run refs; Dependencies plans; unknown fields retained. |
| Session | `session` mapping with text id/date/started/last_turn/summary and nonnegative integer turn_count | All seven lists retain complete native shapes. `logic_revisions` has entry/field/before/after/signal/provenance/note; index counts are nonnegative integers, index claims_touched a sequence. |
| Reasoning/taste | Reasoning turn text and notes; taste id/timestamp/target/tag/object/comment | Reasoning `entries` and taste `entries` sequences. No shortening of comments, before/after, context, or notes in a full read. |
| Root manifest | Text title/venue/doi/ara_version/domain/abstract and integer year, complete root body/Layer Index | Authors, keywords, claims_summary sequences; optional additive knowledge_paths sequence of safe caller-registered relative Markdown paths. Unknown original frontmatter remains intact when not targeted. |

A node has exactly one type: question, decision, experiment, dead_end, or pivot. Required payloads are respectively description; choice and alternatives (PM also records evidence); result; hypothesis/failure_mode/lesson; from/to/trigger. Dead ends are leaves. A `parent` resumes an earlier branch; it is a node reference, not free text. Nesting and explicit parent must agree or surface a conflict, not normalize one away. Pivot `from`/`to`/`trigger` are source text, not automatically node IDs. Compiler support_level is explicit or inferred; explicit source_refs are retained. PM-only timestamp/provenance fields must not be invented for older compiler nodes.

Authored scalar values follow the union of the pinned source dialects, without rewriting unsupported historical values. Claim resting statuses are `hypothesis`, `untested`, `testing`, `supported`, `weakened`, `refuted`, and `withdrawn`; `revised` is a recorded transition, not a resting status. Heuristic statuses are `active`, `weakened`, and `retired`. Sensitivity accepts `low`, `medium`, `high`, `unknown`, or the compiler's exact `Not specified in paper`. Global provenance values are `user`, `ai-suggested`, `ai-executed`, and `user-revised`; accepting a spelling does not justify a provenance upgrade or an empirical judgment. `verified`, `partial`, and other unsupported legacy status text remain readable and unchanged when not targeted, but are not new authored statuses.

Reads retain unknown or unsupported values and the entire raw source. Writes reject unsupported field kinds rather than coerce a string to a list or lose a mapping. A parseable unsupported incoming merge value becomes a conflict with complete incoming and local text. Invalid YAML, duplicate identity, unresolved selector ambiguity, or incomplete source IO prevents merge publication; diagnostics retain available raw text, but there is no duplicate-truncated successful manifest.

### How promotions and source contradictions are handled

Promotion targets are claim (`logic/claims.md:Cxx`), heuristic (`logic/solution/heuristics.md:Hxx`), concept (`logic/concepts.md#name`), constraint (`logic/solution/constraints.md#section`), architecture (`logic/solution/architecture.md#section`), and dead_end (`trace:Nxx`) when empirical resolution refutes the observation. `unknown` stays staged. The caller supplies the closure signal, typed target content, evidence/bindings, provenance choice, and session history; the offline CLI validates the operation without deciding research maturity. The original observation remains, including original provenance. Only explicit verbal affirmation upgrades the new typed entry's provenance according to the source rule.

The pinned PM crystallization procedure requests `From staging`/`Crystallized via` in logic, but its later snapshot contract excludes them. The proposed disposition uses the later current-state snapshot rule: the observation and creation/revision session record carry the source observation and closure; logic remains a current snapshot. This is a recorded ambiguity requiring upstream review, not a rewrite of the baseline. The selected contract must be the same for both conditions of any new comparison. Historical reproduction remains unresolved until its exact contract is known.

Session rolling lists and metadata are current views despite the general immutable-layer statement. The proposed exceptions archive their complete before/after in reasoning records. Claim falsification spellings and PM/compiler Proof dialects remain distinct source spellings rather than being silently repaired. Compiler reference pages also disagree about indexing run logs in `src/artifacts.md`; the proposed disposition follows the compiler main rule and current codebase-index section, with runs under evidence. This does not permit changing the pinned procedures in only one condition.

### How source keys differ from labels and revisions

`source_key` is a stable opaque caller-declared identity for one artifact lineage. It is not an entry ID, path, checkout directory, branch label, or `--as` display label. First import of an untracked directory requires an explicit `--source-key`; subsequent imports use the same key and verify its registered lineage/base metadata. A fork receives a new key and an explicit verified base checkpoint. Copying bytes or reusing the display label does not establish a new revision of the same source. A portable ledger carries the key across transfer, so no private cache is necessary.

A source revision records the actual content fingerprint and optional full Git identity. A dirty tree cannot be described by the commit alone. The fingerprint is SHA256 over ASCII `ara.artifact/v1` followed by NUL, then each existing captured file in sorted UTF-8 relative-path order: unsigned 64-bit big-endian path byte length, path bytes, unsigned 64-bit big-endian content length, and exact file bytes. Capture includes `PAPER.md`, `.gitignore`, all logic/trace/staging/src/evidence descendants, the fixed rubric document, and explicitly registered knowledge documents, while excluding `.ara/` and `.git/`. Captured external bodies establish complete source evidence, not permission to write them. Alias and merge-log bytes participate in the fingerprint; only their recursive storage is excluded from revision.files, with transport records retaining their exact incoming bytes.

Directory advancement requires the supplied base to match the preceding source fingerprint or a Git-proven predecessor. A label can change without changing source_key; reuse for another key needs the explicit key and stays disambiguated. Label-only resolution rejects ambiguity. Unverified advancement does not publish a new revision.

Only exact verified shared-base bodies establish unchanged shared ancestry. Equal native IDs, equal titles, equal labels, or semantic similarity are insufficient. A matching raw body can establish the same shared record when the source and destination both cite its verified base checkpoint; two independently authored equal-looking records otherwise keep distinct source identities. Forks continue allocating ordinary local N/C/H/E/O/T/session IDs.

### What the portable alias and merge files contain

The following is a proposed wire example, not a merge run. IDs and digests in examples are symbolic. Implementations write real digests, revisions, and times.

```yaml
# trace/aliases.yaml
format: ara.aliases/v1
aliases:
  - source_key: fork-b
    label: bob
    original: N01
    target: N17
    revision: SOURCE_FINGERPRINT
  - source_key: fork-b
    label: bob
    original: C02
    target: C02
    revision: SOURCE_FINGERPRINT
```

Aliases record `(source_key, original)` separately from label and revision. A source qualifier is `key-or-label:original`; label-only lookup rejects ambiguity. Native originals are bare N/O/C/H/E/T IDs, bare `YYYY-MM-DD_NNN` sessions, session file paths, existing RW IDs, `logic/concepts.md#term`, arbitrary Markdown `path#ancestor/heading`, reasoning `trace/pm_reasoning_log.yaml#entries/ordinal`, and whole-file paths including opaque content. No native ID is invented for a concept or prose section. Lookup resolves the imported target and any local structural redirect with a visited set. Reject cyclic aliases, missing targets, or incompatible destinations for one identity. The unchanged C02 mapping prevents a repeated import from allocating a new identity. An unresolved candidate remains a conflict rather than an installed alias.

Reject source key/label scopes that collide with native `trace` selectors or registered root Markdown document namespaces rather than guessing which grammar the caller meant. Source-only retired numeric identities reserve fresh destination mappings even for null removals; this reservation does not fabricate replacement content for historical protected references.

Local structural redirects use `trace/logic_mutations.yaml` with an append-only top-level `mutations` sequence. Generated records contain `action: rename|remove`, `from`, `to`, `from_selector`, `to_selector`, exact full `before`/`after`, `session`, `turn`, `signal`, `provenance`, and `historical_references` (unchanged historical file paths using the old identity). Generated selectors use strict EntrySelector objects with `document` and `heading: [literal ancestor titles, literal final title]`; a slash inside one title stays inside its one array element and is not a hierarchy separator. A permitted unreferenced removal has `to: null` and `to_selector: null`. The `from`/`to` strings retain the normalized native interface: full ancestor-qualified heading paths for named sections/title-only changes, and canonical numeric native IDs for true ID changes. Both `#` native concept refs and existing observation `path:id` references resolve through this exact mapping; historical text is not rewritten.

Renames and referenced removals point to existing retained replacement content. Reject cycles, conflicting targets, or dangling redirects. An unreferenced mutable entry may be removed with `to: null` only when the complete final candidate and reference inventory prove that no typed or historical reference remains. Its full before-body still lives in session history. Claim merge/withdrawal retains its old entry under the pinned procedure. Every changed mutable inbound reference has its own complete revision record. Native reads, reference queries, and source-body reads consume the mutation mappings; a mapping is not merely an audit note.

Redirect lookup follows chains using exact generated selectors. Legacy short headings may resolve only through an unambiguous archive suffix; ambiguous headings require explicit ancestor arrays. Reject reused live origins, cycles, dangling targets, and C/H/E numeric namespace changes. Redirect origins cannot lie in trace, staging, source, or evidence namespaces.

The explicit selectors make newly generated records lossless, for example `{"document":"logic/concepts.md","heading":["Root","Title/with/slash"]}`. A slash-separated display string is not enough to distinguish a literal title from a hierarchy.

`trace/merge_log.yaml` has `format: ara.merge-log/v1` and an append-only `records` sequence. Each record is encoded as one inline JSON object under the YAML sequence. The three captured-byte payloads below use canonical padded RFC 4648 standard base64 strings, preserving arbitrary bytes without YAML scalar-style conversion. The record shapes are:

| `kind` | Required payload | Meaning |
|---|---|---|
| `enrollment` | `source_key`, `label`, `time` | First explicit source enrollment. |
| `label` | `source_key`, `label`, `time` | Add a display label without changing identity. |
| `revision` | `source_key`, `fingerprint`, `base`, nullable `predecessor`, `time`, nullable `git`, `files`, `mappings` | Full source content checkpoint and every import identity. `files` maps safe relative paths to canonical base64 strings of the exact file bytes. |
| `conflict` | `conflict` object described below | Persist complete competing bodies, identity, and allowed resolution choices. |
| `resolution` | `conflict_id`, `take`, `time`, `session`, `turn`, `signal`, `provenance`, `prior_fingerprint`, `selected_fingerprint`, `applied_fingerprint` | Audit an ordinary mutable conflict selection. Keep the original chosen source fingerprint separately from the actual relocated destination fingerprint. |
| `imported_resolution` | `source_key`, `revision`, `conflict_id`, `evidence` | Retain the exact JSON bytes of a valid upstream resolution record as canonical base64, allowing a later audited source resolution to clear an imported unresolved conflict. |
| `transport` | `source_key`, `revision`, `path`, `bytes` | Retain a foreign ledger/alias file as canonical base64 of its exact bytes and its full provenance without treating it as local authority. |
| `protected_decision` | Complete `conflict`, `decision`, `reason`, `expected_current`, `session`, `turn`, `signal`, `provenance` | Separately audit rejected incoming immutable evidence or exact restoration of a retained base. |

The shared captured-byte codec rejects malformed/noncanonical text, missing or
excess padding, whitespace, URL-safe alphabet and legacy numeric arrays. Empty
bytes encode as the empty string. Fingerprints bind the decoded original bytes;
encoding does not change identity. Duplicate file paths and unknown record fields
remain errors. Public conflict/report `MergeValue.bytes` remains an unsigned-byte
array. This compact representation is the unpublished native wire cutover, not a
compatibility alias or a second record grammar.

The pair `(source_key, fingerprint)` identifies the import revision. Alias `revision` joins that revision record to its timestamp, base, predecessor, exact source bytes, and complete mappings; date and import identity are not inferred from display label. Mapping targets use the same native forms as originals, with path/layer context retained. Foreign ledgers are retained as transport provenance and are not granted local write authority.

Foreign enrollment, revision, and mapping records are unioned with native source identities remapped to the destination. Never replace their source keys with a transport label. Conflicting immutable foreign checkpoints or mappings reject publication with the complete ledger evidence. A destination cannot resolve an unsafe foreign conflict by making a local selection: an `imported_resolution` requires the source's valid audited resolution as exact retained evidence. All historical targets reserve allocation slots; a retired inactive target is not a live alias terminal.

Each revision mapping contains `source_key`, `original`, `target`, `layer`, and `path`. Its coverage includes every imported native entry and whole-document/opaque identity: trace nodes, claims, heuristics, experiment plans, staging observations, taste comments, concepts/related work/problem/solution sections, root manifest, registered knowledge documents, sessions, index rows, and reasoning records. Whole-document and native section selectors are used when no numeric ID exists. Append-only rows without a native ID use their containing selector plus turn/ordinal and exact retained bytes in the source checkpoint; this is ledger bookkeeping, not a new native ref grammar. No identity is omitted because its local ID stayed the same. A conflict record captures an uninstalled competing identity without falsely mapping it to the selected view. File presence/deletion is captured explicitly in the checkpoint/conflict evidence.

### How repeated merges and conflicts behave

A repeated merge of the same source key/revision/content and imported record identities performs no writes. It reports retained conflicts and prior mappings. It does not allocate fresh IDs, duplicate aliases or session events, or mark unresolved work settled. Advancing revisions compare source and destination to the recorded base. Identical concurrent logic changes converge; an unchanged side accepts the other side's permitted change with full history. Divergent mutable changes, edit/delete disagreements, and parseable unsupported values retain complete candidates in persistent conflict state. A protected historical violation rejects the entire merge without modifying artifact or ledger files and returns complete captured evidence for a separate explicit repair decision.

Promotion is a tuple, not a boolean. Unpromoted versus promoted converges only when source body, target identity, closure signal, evidence and creation history agree with the validated target. Two promoted observations with distinct targets or closure/evidence histories remain conflicted even when both have `promoted: true`. A deletion cannot erase an observation, trace node, session record, taste record, or reasoning entry. Mutable deletion requires the retained replacement/redirect rule above and remains conflicted when the other side edited it.

Same-date sessions from distinct source keys are distinct histories, even when both are named `YYYY-MM-DD_001`. Allocate a destination `NNN` on collision and ledger every imported session/turn identity. Do not fuse their turn arrays, take maximum counts as reconciliation, or concatenate two different `turn: 1` histories. A known same-source session can advance only by preserving its earlier record prefixes. Divergent rolling metadata/lists become conflicts unless complete history proves an identical change. Rebuild index values from the selected complete session and retain both prior index records in conflict/history evidence.

A conflict has `id`, `kind`, `source_key`, `source_revision`, `path`, `selector`, `field`, complete `base`/`ours`/`theirs` candidates, `allowed`, `locator`, and nullable `predecessor`. Each candidate has `present`, exact `bytes: u8[]`, and `fingerprint`; absence is distinct from an empty file or field. Allowed ordinary choices are `ours`, `theirs`, or `base`. The locator adapter is `document` with no extra selector, `yaml` with `keys` (path key/index strings) and `field`, or `markdown` with `entry` and `field`. It names a guarded source span and never grants unrestricted filesystem access.

Conflict identity includes source identity, target/path/field identity, base fingerprint, conflict kind, and candidate fingerprints. Re-importing the same candidates reuses the unresolved conflict. A later conflicting revision retains and links the earlier evidence instead of overwriting it. Status is derived from append-only resolution/decision records, not a mutable resolved flag. Full reads include candidate bytes, provenance, base identity, and all resolutions.

### How an explicit resolution repairs a protected record

Ordinary mutable conflicts use `ara merge resolve CONFLICT_ID --take ours|theirs|base --session SESSION --turn N --signal SIGNAL --provenance TAG`. Resolution validates the current fingerprint, all native targets, field kinds, graph constraints, promotion tuple, and complete history before publication. It appends a resolution record with prior/selected fingerprints and exact session before/after. It cannot accept a protected immutable field, erase the losing candidate, or bypass the field whitelist. Dry-run reports the planned transaction without writes.

Protected historical evidence uses a separate bounded command:

```bash
ara merge repair --conflict-file captured-conflict.json \
  --decision reject_incoming --expected-current CURRENT_FINGERPRINT \
  --session 2026-10-01_001 --turn 3 --signal user-directive \
  --provenance user-revised --reason "Keep the original historical record"
```

`captured-conflict.json` contains the complete conflict object returned by a rejected merge. `reject_incoming` keeps the protected content unchanged while atomically recording all evidence and the decision. `restore_base` may restore only the exact previously captured base bytes, with the expected-current fingerprint checked against the live target. Neither choice accepts arbitrary replacement text or promotes unsupported incoming history into valid data. The transaction appends a protected decision, complete session logic revision, and reasoning context; rejected merge bytes and every competing candidate remain recoverable.

The core interface is `plan_protected_resolution(snapshot, captured_conflict, decision, expected_current_fingerprint, session, turn, signal, provenance, reason) -> WorkingArtifact`. Its transport is the standalone CLI `merge repair`, returning JSON with format `ara.merge/v1`; ordinary `merge resolve` uses the same reply family. These operations are not JSONL WriteOperation tags and cannot be replaced by generic document edit. Audit authors the next owning session turn only (`turn_count + 1`) and appends the session log/revision; it rejects modification of a past turn. A corrective historical fact is a separate append through existing node/observation/history operations, explicitly referring to the disputed evidence.

A repeated identical resolution/decision is a no-op. A later contrary adjudication or new evidence is recorded as a new linked event and retains prior selection. Ordinary edit, forced merge, and whole-document replacement cannot alter protected records or conflict evidence. Any failed resolution/repair leaves every artifact and ledger file unchanged.

### Which examples reviewers must check

| Accepted proposed operation | Rejected operation |
|---|---|
| Import C02 without renumbering and append its identity alias/import record. | Log only renumbered N01 and assume future C02 imports are new work. |
| Import fork-b as label bob; later use another explicit key with the same label and disambiguate. | Treat `--as bob` as proof that an unrelated directory is the same source. |
| Repeat a merge with an unresolved O01 target disagreement and report the same conflict. | Settle it because both candidates say promoted true. |
| Mark an idle observation stale with three session-days and a reasoning record. | Rewrite observation content, unstage it, or infer withdrawal from age. |
| Replace rolling open_threads with exact old/new lists retained in reasoning; append all historical session arrays. | Replace logic_revisions or erase a pending suggestion without history. |
| Rename a concept with mutable inbound updates and an old-to-new redirect. | Rewrite earlier trace content or leave its old anchor dangling. |
| Audit rejected incoming protected evidence, or restore its exact captured base with current fingerprint and full history. | Use generic edit, install arbitrary new immutable text, or erase the losing candidate. |
| Append same_as to an earlier node without deleting either. | Self-link, cycle, or collapse the nodes into one. |

## Alternatives considered

A global ID grammar would change every native reader and source skill. Renumber-only aliases would not recognize unchanged-ID imports. A private cache would lose identity when the artifact moves. The proposed portable ledger avoids these problems without changing native entry refs. It requires explicit keys and verified checkpoints rather than trying to infer lineage from labels or text similarity.

A purely derived stale view would avoid metadata edits but would change the pinned PM instruction to set stale true. Append-only session arrays for open_threads would never represent closed work correctly. The proposed narrow stale transition and audited rolling views preserve the required behavior while retaining previous state. Both choices still need reviewer disposition.

## Tradeoffs

Full candidate text and full before/after history cost space but make historical repairs and repeat merges auditable. Exact source-preserving edits require a writer to reject unsupported syntax instead of reserializing a whole file. Explicit source keys add one first-import argument but prevent unrelated forks from sharing an identity when a label is reused.

## Migration

Existing artifacts and source skills remain valid. Additive alias, merge, conflict, and redirect records appear only when the relevant operation needs them. Missing optional fields remain absent. No baseline archive is rewritten; selecting a new source contract requires a new immutable pin and an explicit comparison decision. Current source pages link this pending proposal without changing research procedures.

## Next Steps

1. Review each F disposition and its detailed identity, session, promotion, dialect, and protected-repair choices; record the actual upstream approval revision only after review.
2. Consume the complete operation inventory in CLI batch/writer/read work. Mark a row covered only with a pinned CLI revision and observed end-to-end proof of its payload, history, and provenance contract.
3. Keep historical task-to-skill mappings unresolved until the published-run subset and skill/configuration provenance are verified. Live tasks may use the declared live pins but are not a paper reproduction.
4. Derive CLI-only skill copies only after coverage is complete. Keep collective frontier/intentions work separate and defer scored experiments.
