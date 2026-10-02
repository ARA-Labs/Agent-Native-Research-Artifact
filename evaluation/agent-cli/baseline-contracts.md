# Baseline skills and artifact access contracts
**Date:** 2026-10-01

## TL;DR

The Files baseline contains exact skill and reference bytes from verified protocol remote commit `e52a925e9d03b4ada3008653e72f99b04116fca2`. These are new live pins, not a verified historical paper skill revision. The available paper configuration contains 465 native question IDs, while the published evidence page reports 450; both facts remain recorded, and neither the published subset nor its skill mapping is guessed. The operation inventory contains 107 source operations, and no row claims unobserved CLI coverage.

## What is pinned and why

[source-lock.json](source-lock.json) records the HTTPS remote URL, full revision, exact source path, SHA256, byte count, archive path, license, and reference closure. Remote `main` was checked with `git ls-remote`, then fetched; source bytes were read from the fetched full commit using `git show`, not copied from an installed skill. The archive lives under `baselines/live-e52a925e9d03b4ada3008653e72f99b04116fca2/`, retaining the original `skills/` layout and MIT license. Pin digests use sorted source paths with length-delimited path/content bytes, as specified in the lock.

| Pin | Entry point | Included contract closure | Selection |
|---|---|---|---|
| research-foresight | `skills/research-foresight/SKILL.md` | CONTRACT, RETRIEVE, PREDICT, plus research-manager's reader-report template | Current live reader; not paper-corresponding |
| research-manager | `skills/research-manager/SKILL.md` | event-taxonomy, taste-comments, reader-report template | Current live single-writer PM |
| compiler | `skills/compiler/SKILL.md` | ara-schema, exploration-tree-spec, figure-extraction-guide, validation-checklist | Current live source-grounded compiler |

The archive contains all 13 files in these three source trees and the unchanged root LICENSE. Reference edges include the reader's transitive report template and the manager's taxonomy/taste back-references. Source schema, figure extraction recipes, validation instructions, templates, role declarations, stopping rules, evidence requirements, and original formatting are all part of the baseline. Changes to current source pages do not rewrite this archive. A new source revision requires a new pin rather than replacing files under this identifier.

## Which historical task mappings are known

The protocol remote contains `examples/the-ara-of-ara/src/eval/questions/`, prompt templates, paper registry, and understanding-evaluation runners. The lock records hashes for all 62 question files and the relevant runner/prompt/registry/evidence pages, yielding 70 available configuration files. [task-skill-map.json](task-skill-map.json) enumerates each of their 465 native question IDs with its source file, JSON pointer, category, paper ID, and grading source. The generic ARA prompt tells an agent to discover and search the artifact; it is not an invocation of the current research-foresight skill.

The published evidence page reports 450 questions and points to result blobs not checked into the artifact. The available files do not establish which 450 questions were used, their exact published-run prompt/grading/runner revisions, their source artifact snapshot, or a historical skill revision. Historical rows therefore have null skill_pin, entrypoint, and loaded_references, with an explicit unresolved reason. The task map records two available grading policies: the understanding runner uses gold_answer, while the token-efficiency runner selects ara_gold_answer when present for the ARA condition. Neither is identified as the published-run grader. The observed current prompt path is configuration evidence, not an assigned historical task skill. The `ara-paperbench` remote at `62e9b54b2d4efe45b97f25676a16784530dd552a` is a 32-artifact collection; its extra question files do not repair this missing mapping.

Three `live.*` tasks in the task map are newly authored packaging smoke requests, not paper questions. They load the named archive entry point and complete reference closure. They have no benchmark grading source and no claimed run result. A future live reader comparison must state that it is not a reproduction. Scored experiments remain deferred.

## What counts as an artifact operation

[operation-coverage.json](operation-coverage.json) uses `format: ara.skill-operations/v1`. Each row has a stable operation_id, skill_pin, source_clause with exact pinned path/line range/quote, layer, native_selector, access, access_policy, required, applicability, full payload/history/provenance contracts, role, proposed CLI operation and batch tag, required F decisions, coverage_status, proof_reference, and blocked_reason. Line ranges refer to the immutable pin, not a current page after later clarifications. Conditional operations such as taste or rubric generation are required when their source trigger applies; they are not silently optional capabilities.

| Source skill | Rows | Required knowledge access families |
|---|---|---|
| research-foresight | 16 | Complete discovery/search; root manifest; problem/method prose; claims, concepts, experiment plans, related work; every trace type and full DAG; negatives; full grounding-body reads; source/evidence follow-up; output-only reports and transitive template |
| research-manager | 51 | Initialization; full state/IDs/briefing/sessions/reasoning/observations; every journey node type and cross-edge; staging; six promotion targets; stale; contradiction/report adjudication; claim/heuristic/concept revision; status/split/merge/generalize/rename/remove/dependency repair; complete constraint/architecture bodies; all session lists/metadata/index; taste; knowledge-side grounding through CLI; direct evidence/source grounding |
| compiler | 40 | Input acquisition; full mandatory initialization; whole PAPER/problem/claims/concepts/experiments/related-work/solution bodies; arbitrary method and appendix prose; explicit rubric knowledge document; every trace type/cross-edge; complete coverage reads and targeted repairs; knowledge-side binding checks through CLI; direct semantic/source validation; environment/code/config/data/run/log/evidence/figure bodies and real screenshots; complete file/byte/native-entry counts and observed validation reporting |

`access_policy: cli-required` marks knowledge-layer operations that CLI-only variants must route through `ara`. `direct-access-allowed` marks source/evidence acquisition or body work permitted by the source. `output-only` prevents a reader report from being mistaken for a write path. `skill-reference-access` refers to instruction pages, not artifact knowledge. These distinctions do not widen reader scope or permit PM access to compiler-owned experiment plans.

Coverage states are proposed, covered, or blocked. A command name is only a proposal. Covered requires a full pinned CLI revision and an observed proof covering the row's complete payload, history, native refs, provenance, role, and failure boundary. Direct-access and output rows do not imply CLI proof. Missing required coverage blocks the affected skill variant; it must not be replaced by a direct knowledge-file write. This PR creates the inventory and baseline packaging, not a false coverage certificate.

## Which source contradictions remain visible

| Source clauses in the pin | Conflict | Proposed disposition for upstream review |
|---|---|---|
| PM crystallization step 4 versus current-state snapshot text | First requests From staging/Crystallized via in logic; later excludes them. | Follow later snapshot placement: observation plus creation/revision trace history retain closure/source. Baseline remains unchanged. |
| PM immutable-layer rule versus session schema/per-turn procedure | Complete session arrays, rolling lists, summary/counts and index require updates. | Historical arrays append; rolling views/metadata/index replace only with exact prior/new values retained in reasoning history. |
| PM immutable staging versus stale-flagging | Stale must become true after three unreferenced/unpromoted session-days. | Explicit narrow metadata exception with session-day evidence; no deletion, promotion, or content rewrite. |
| Compiler Proof-to-experiment rule versus PM Proof-to-evidence spelling | Native claim proof bodies differ. | Retain both source dialects and falsification spellings, including complete unknown fields and prose; do not normalize. |
| Compiler main codebase/run separation versus older schema/checklist run-index clauses | Some clauses put logs/runs in src/artifacts while the current main rule puts them in evidence. | Follow main/current codebase-index rule for new contracts, retain the original contradictory pin, require the same selected contract in both new comparison conditions. |

[protocol-decisions.json](protocol-decisions.json) and [the protocol contract](../../docs/agent-cli-contracts.md) record these proposed dispositions separately. All F1 through F7 have `approved_revision: null` and upstream review pending. Approval of the implementation plan is not evidence of upstream merge or acceptance. Current source pages only link the pending proposal; their research procedures have not been replaced.

## How to audit the package without running an experiment

The new `verify-packaging.py` script loads the lock, all archive files, reference edges, task map, inventory, decision status, and declared smoke tasks. It checks exact hashes/byte counts, complete archive membership, transitive closure, valid source clause citations, source question-ID membership when `--git-source` is supplied, and honesty of pending/coverage states. It then loads each smoke entry point and every declared reference from the archive. This is packaging verification, not an agent reasoning run, CLI capability proof, Seal certification, or scored evaluation.

```bash
python3 evaluation/agent-cli/verify-packaging.py --git-source .
```

`smoke-tasks.json` supplies bounded live reader/PM/compiler requests and expected source-native record shapes. A runtime can load those exact pinned pages and exercise the fixture artifact. No source/evidence benchmark is invented. The implementation worker did not run the script, builds, tests, formatters, skill runtime, or experiments; integration validation belongs to the owning parent task.

## Next Steps

1. Review F1 through F7 and record real upstream approval evidence after review, without changing the archived baseline bytes.
2. Run packaging verification and then prove required operations against the actual pinned CLI binary. Keep unproved rows proposed or blocked.
3. Resolve the published 450-question subset and historical configuration/skill mapping before claiming reproduction.
4. Derive access-only CLI skill copies from the named live pins after complete coverage. Preserve source procedures and keep collective coordination separate from the interface comparison.
