# Common collective roles

Load this exact page in every collective condition, including Files, plain CLI, frontier-only,
intentions-only and combined. Its authority does not depend on the installed component.
Record its digest in the immutable run configuration. The proposed contributor role requires
explicit upstream writer-authority approval before a scored run; an intention or a transport
acknowledgment never grants knowledge-write authority. Disposable protocol-consumer smoke
runs do not assert that approval. Without approved contributor authority retain the source
reader-is-read-only and PM-is-single-writer rule.

| Role | Scope and authority |
|---|---|
| Reader | Reads only the authorized ARA under its source skill isolation; returns grounded answers/reports; never writes knowledge or canonical history. |
| Designated contributor | Only if explicitly approved and admitted: performs assigned research and proposes complete source-grounded changes in its own fork through the condition's access mechanism. No edits to another fork, canonical integration artifact or another actor's intention. |
| Fork PM | Exactly one authorized PM per fork owns continuity, closure/provenance, session arrays/index, full verbatim logic revisions, reasoning/near-misses and taste records. Contributor activity is input to its end-of-turn history, not permission to erase prior records. |
| Integration PM | Owns canonical directory/Git merges and researcher-directed conflict adjudication. Preserves source keys, revisions, native aliases, merge/conflict candidate bodies, complete sessions and provenance. Role privilege cannot settle a scientific disagreement. |
| External coordinator | Transport authority only: admitted identities, serialized durable events/snapshots/receipts, logical rounds, staleness and budget accounting. No LLM, semantic duplicate suppression, maturity choice, research inference, hidden extra agent or merge advice. |

The source research procedures remain in force: closure is externally observable, not an LM
judgment; staged raw/context/provenance survives promotion; full history survives current-state
rewrites; contradictory positive evidence remains visible; every assertion is grounded in full
verified native bodies. The access condition decides Files versus CLI, not these procedures.

A contributor sends the fork PM and integration PM a source-qualified proposal: stable
`source_identity`, exact `artifact_revision` (include actual content digest for dirty trees),
changed native refs, complete source/evidence/logic bodies and preserved trace/session history,
intention receipt if installed, and unresolved conflicts. Never replace this with a shortened
claim summary or copy only winners. Ordinary local IDs remain local; a display label/path is
not a stable lineage key. Use explicit opaque source keys and verified shared-base content.

The integration PM reviews merge reports and full candidate bodies, verifies original evidence,
keeps unresolved conflicts visible, and follows the original researcher-adjudication rules.
CLI access uses `ara -C <canonical> merge --source-key <opaque-key> --as <display-label>
--base <verified-base> --theirs <fork>` (or reviewed Git source). Never silently prefer an owner
or duplicate ID. A reader contradiction report remains output transported to the PM, never an
edit to apply verbatim. Preserve exact original and new identities, redirects and all prior
values for split/merge/generalization; no source or history disappears at integration.

Do not mutate roles or failure/budget/expiry settings within a run. New approvals or protocol
revisions require a new run configuration, not retrospective relabeling. Interface-only skills
retain their original single-writer roles and never load this role intervention.
