# Source-faithful property authoring

This contract governs compiler, compiler-cli, research-manager, and research-manager-cli. Load it before capturing or revising claims, staging obligations, or authoring declarations. Each workflow loads its local `references/property-authoring.md`; these references point to this single maintained source and are materialized when installed. Source preservation overrides instructions to generalize a Statement or remove named configurations and quantitative assertions. This contract changes authoring semantics, not the workflow's file/CLI access boundary, closure signals, roles, or experiment authorization.

## What must survive

A source assertion may be a bounded empirical comparison, a hypothesis, a qualitative assertion, or a mechanism claim. Preserve its exact assertion and source anchor before interpreting it. Named methods, configuration variants, values, units, and statistical commitments may appear in a Statement when they belong to the assertion. Ground every load-bearing number from the source; do not copy evidence numbers into an executable spec. A synthesis is a separate interpretation with its own identity and explicit links to the preserved assertions. A narrowed subclaim never silently replaces the full obligation.

Use existing ARA fields and links, not a new core schema. Keep neutral source content in ordinary claim/evidence records: `Statement`, `Conditions`, `Sources`, `Evidence basis`, `Proof`, and evidence captions/headers. Before crystallization, preserve the assertion and scope in an existing staged observation's `content` and `context`, linking a neutral evidence record if needed. Keep candidate relations, executable operand selections, feedback, and check records in separately linked authoring records, not embedded in neutral source records.

Persist records in the native syntax from the workflow's schema reference. A claim uses an exact `## C01: title` heading and exact bullet fields such as `- **Statement**: <verbatim assertion>`, `- **Status**: hypothesis`, `- **Falsification criteria**: ...` (or the supported research-manager `Falsification` alias), `- **Proof**: [...]`, and `- **Tags**: ...`. Do not replace field names with presentation labels such as `Verbatim assertion / Statement`, insert prose metadata before the first field, or invent a status such as `preserved`. Put obligation versions and semantic details inside supported fields or linked receipts. Persist staged observations as the existing YAML records, not a Markdown rendering that only describes them. Validate actual saved records with the installed readers; fix format without changing the assertion and retain the rejected initial output.

Use each workflow's native proof dialect. The compiler links real experiment IDs; if no supporting experiment is available, use `- **Proof**: [pending]` with the reason in `Evidence basis`. The research manager retains real relevant evidence-file references directly and uses `pending` only when its required support or binding is missing. Do not replace valid observational, documentary, or formal evidence because no experiment ID exists, or manufacture an experiment ID. An empty proof list may be rejected by a consumer even though an unsupported obligation is valid research content; keep that obligation staged until its existing closure signal, or use the native `pending` convention in a crystallized record.

For every selected assertion, preserve this information explicitly; use an attributed unknown rather than a guessed value:

| Information | What to preserve |
|---|---|
| Identity | Original source revision and anchor, verbatim assertion, ARA claim or observation ID, immutable version/content digest, and correspondence when claims split or merge |
| Meaning | Metric, units, direction, exact method variant and baseline, dataset/task scope, quantifier, aggregation, statistical unit, uncertainty commitment, and every conjunct |
| Evidence | Evidence references, original headers and axis order, method identities, canonical labels, approximation markers, extraction confidence, and provenance |
| Availability | Missing evidence, unresolved meaning, unsupported relation, approximate measurement, and absent variance as separate reasons; absent variance is never zero |
| Authoring | Candidate origin, allowed input access, skill/model/catalog versions, tools, attempt and repair allowance, initial output, every failed attempt, feedback, repair, human help, and check-record identities |

An unsupported obligation stays in the all-selected-assertions ledger with its reason, even when absent from `aratest/spec.yaml`. No relation fit and no evidence are different outcomes. The ledger may be an existing staged observation plus linked session/authoring records; do not force it into a settled claim or an empty executable property. Source claim IDs, not the number of generated subclaims, define coverage.

## Author in this order

1. **Capture.** Record the verbatim assertion, source anchor, identity/version, and all conjuncts before selecting a relation. Separate reported assertions from explanations inferred by the author. For live work, stage the obligation at the first recording opportunity, before results when available. Record when evidence already existed; a later record is not preregistration.
2. **Resolve evidence meaning.** Check method variants, metric identities, headers, axes, units, task scope, quantifier, aggregation, statistical unit, and uncertainty against the allowed inputs. Preserve conflicting headers or ambiguous aliases as unresolved; do not pick the interpretation that makes a check hold. A label alias may join only names for the same method, never fixed and adaptive variants. Missing uncertainty does not license a significance test or a zero-variance assumption.
3. **Choose a faithful declaration or a reason.** Read the installed relation catalog and its schemas. Map the whole assertion, including every conjunct, to supported relations and operands. If only part fits, retain the full unsupported obligation and identify the narrowed subclaim separately. Do not weaken all-tasks to some-tasks, replace a task-dependent variant with a fixed one, substitute final for average accuracy, or discard a resource-use conjunct.
4. **Review meaning before execution.** Compare the initial candidate with the captured assertion. Record semantic-field differences and unresolved conditions separately from schema validation and operand resolution. Preserve the initial candidate and every repaired version. A loadable, bindable, holding declaration can still be a semantic failure.
5. **Execute only authorized reported-evidence checks.** When an executable declaration and runtime are available, load, bind, check, save the check record, and replay through `aratest` production APIs. Keep holds, violations, inconclusive outcomes, and operational failures. No automatic paid/model collection, regeneration campaign, fresh scientific experiment, catalog family run, retry loop, or extra attempt is authorized by this contract. Missing runtime is an explicit unperformed check, not a fabricated verdict.

## Executable declarations

Use `aratest/spec.yaml` format version 7. Its evidence map supplies metric and axis meaning for existing parsed evidence; `labels` normalizes equivalent spellings; each claim's `properties` is a conjunction of catalog relations. Put one property per required supported conjunct. Properties address measurements by canonical coordinates, not copied values. Record author provenance using the supported model; put richer workflow history in linked authoring/session records rather than inventing spec fields. Families that generate fresh cases need separate authorization and are not part of reported-evidence authoring by default.

For example, a source assertion that Fixed-A has higher average accuracy **and** lower memory on every named task requires both comparisons with their own directions. An average-accuracy property that holds cannot discharge the memory obligation. If the supported catalog cannot express one conjunct, the full assertion remains unsupported even if a separately identified accuracy subclaim executes.

Schema acceptance, operand binding, execution outcome, replay compatibility, and independently reviewed source fidelity are distinct recorded outcomes. A witness can identify cells to inspect; it cannot decide which source assertion should have been written. Never select a declaration because it holds, or label source-informed compiler authoring as independent ARA-only extraction.

## Revisions and check identity

A mutable claim is a current snapshot; staged observations and trace history remain append-only except existing forward-reference updates. Before changing method, scope, units, quantifier, aggregation, uncertainty, conjuncts, tolerance, or decision policy, preserve the old obligation and candidate identity and append a new version with full before/after content in the existing session revision record. Give each saved candidate and evidence input an immutable identity (for example a content digest); retain the source and skill revisions too. A file path alone is not a version.

Link every check to the exact obligation version, declaration digest, evidence digest, relation/catalog version, decision policy, and saved record ID it checked. Use the production record's identities and a linked authoring receipt for information the runtime does not encode. Never claim the runtime certifies obligation/source fidelity merely because it snapshots executable inputs. After a semantic or decision-policy revision, the previous check remains historical evidence for its old inputs and is not a check of the new obligation. Load/bind/check/replay the new executable candidate separately; unsupported revisions remain explicitly unchecked. Keep initial and repaired outcomes separate.

Recording an obligation does not crystallize it. The research manager still requires an actual closure signal under its existing maturity rules; a request to record, a spec being drafted, or a holding reported-evidence check alone does not establish researcher affirmation or empirical resolution. A prospective hypothesis can remain staged with an executable candidate.

## Isolated ARA-only extraction

Prepare a pinned, allowlisted input view before extraction, then use a fresh context with access only to that view and the pinned relation schemas. The manifest records included files and fields, their digests, source artifact revision, and exclusions from linked records. Do not hand the extractor the original artifact with instructions merely not to read excluded files. Do not copy the original source packet into the view or grant access to it through links, tool mounts, history, or another workflow's context.

| Retain as neutral compilation output | Exclude as authoring or review answers |
|---|---|
| Preserved source quotations and source anchors, ordinary claim/evidence records, conditions, units, scope, uncertainty commitments, provenance, raw table headers and numbers | Original source packet access, compiler candidate specs and relations, executable operand selections, check results, validation/repair feedback, reviewer annotations, and repair answers |
| Axis/label meaning that describes evidence independently of a proposed test | A map selecting treatment/baseline cells or scope for an authored candidate |
| Neutral linked evidence and source metadata | Linked records containing candidates, operands, check/repair history, or reviewer answers |

Separate neutral content from authoring answers when first writing the ARA so exclusions do not erase the assertion or evidence semantics. Audit the materialized view, including transitive linked content, for both retention and leakage. A source quotation retained by compilation is allowed; following its source anchor to the original packet is not. Keep unsupported obligations visible in the view and denominator without exposing their proposed relation answers.

## Engineering checks and research limits

Exercise compiler capture and live recording on exposed inputs. Include method-variant confusion, swapped average/final headers, an omitted conjunct, an unsupported obligation, and a semantic revision. Preserve baseline and revised outputs where available. Use actual loading, binding, checking, saving, and replay for executable candidates; no mocked execution or source-text assertions establish workflow behavior. Label constructed development examples and do not count them as research outcomes.

Record instruction changes against observed failure boundaries, remaining failures, and effort. Fix model, catalog, tools, and attempts for any targeted comparison, or disclose differences without assigning their effects to instructions alone. Engineering examples do not establish effectiveness or independent source fidelity. Prospective scoring requires a separately authorized, registered cohort, pinned workflow/input manifest, resource caps, and independent source annotations and candidate review. Low coverage and failures are valid outcomes; never tune the cohort until a desired success count appears.

The historical `evaluation/agent-cli` locks and access-only proof remain tied to their original source revisions. This source-faithful authoring revision changes both workflows' research instructions, so those old variant digests and semantic-equivalence claims do not apply to the current entrypoints. Verify the frozen interface-only condition at its recorded commit; register a new authoring revision before any current comparison. Do not rewrite old locks or reuse old model/binary proof as evidence for these instructions.
