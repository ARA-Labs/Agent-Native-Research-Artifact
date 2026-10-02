# Shared-intention component

Install independently from the frontier component. Load only when `intentions` is selected in the
immutable run configuration; the same common roles/failure pages apply to every collective arm.
The transport is one host with one writable common runner directory, not distributed deployment:

`<run-root>/shared/community/<community-id>/intentions/`

This path is outside all `<run-root>/forks/<agent-id>/ara/` workspaces. Every actor uses that exact
channel. Only the external coordinator appends `events.jsonl` and atomically replaces
`snapshot.json`. Agents submit requests through their runner; private intention files or private
replicated snapshots do not satisfy publication/refresh. Ara remains offline and LLM-free.
The standalone smoke consumer has no scientific reasoning or extra agent; real runtime/plan15
integration and scored experiments remain deferred, not claimed from its local scenarios.

For a read-only reader engine, the external runner supplies snapshot context as input and
publishes the engine's output request; the reader itself neither opens the outside channel
nor writes requests. Its one-ARA knowledge/evidence scope and output-only contract remain.

## Pinned state and request schema

The contract is `ara.collective-contract/v1`; its consumer uses `ara.community-transport/v1` and
run config `ara.community-run/v1`. Pin run/community/coordinator identities, admitted actors
with stable `source_identity` and role, equal positive `allocation_per_actor`, whole-round
`refresh_cadence_rounds`, `expiry_rounds` (at least cadence), positive bounded `max_rounds`,
registered failures and component set before work. An actor process has one immutable actor ID.
These are reviewed design parameters, not empirically selected freshness thresholds.

An intention publishes all of:

- `community_id`, `actor_id`, `intention_id` (`<actor_id>:<portable-local-id>`), increasing
  `revision`: run-scoped identity, never an invented ARA node ID.
- `source_identity`, exact `artifact_revision`, `native_refs` as `{source_identity,native_ref}`
  records: preserve fork identity/native grounding and actual selected source revision.
- `action`, `question`, `experiment_signature`: planned action/motivation and reproducible
  configuration/source digest. A signature identifies likely overlap, not scientific equivalence.
- `verification_of`: null or `{source_identity,intention_id,revision}`; alternatively record a
  `verification_rationale` for deliberate replication. Never suppress legitimate verification.
- `state`: `planned`, `active`, `completed`, `abandoned` or `expired`; each transition preserves
  earlier state in event/history. Completion is a reported state, not proof of a correct result.
- `published_sequence`, `refresh_round`, `expires_after_round`: coordinator-owned increasing
  sequence and logical scheduling rounds. Local wall clocks cannot establish freshness.
- `budget_reserved`, `budget_used`, `result_refs`: same allocation accounting and full source-
  qualified outputs; reservations are not extra compute. New planned records have empty results
  and zero used budget. The coordinator adds these counters and retained history.

All requests carry a stable actor-prefixed `request_id`. Mutations also carry the last observed
`observed_sequence`/`observed_round`; intention changes carry `expected_revision`. A publish
expects revision0 and creates one new actor-owned intention. A refresh-intention targets the
same actor-owned ID and increments its revision while preserving every prior record. Another
actor can disclose an overlap, never complete/abandon/refresh the owner's work. Coordinator
validation rejects ownership, wrong run, stale observed snapshot, stale revision, invalid
transition or exhausted allocation before accepting work. Conflicting fresh signatures return
both owners/signatures for explicit agent judgment, not an exclusive lock or auto-deduplication.

## Refresh, publish and execution boundary

1. Refresh the latest **committed common** snapshot before each work-selection boundary, after
   every action result, before publication, and immediately before budget-consuming execution.
   Record snapshot sequence/round with your choice. Read full relevant knowledge through the
   source skill's access mechanism; do not infer unseen fork facts from local open output.
2. Choose under the original research procedures and shared total budget. If duplication is
   intentional, include verification reference/rationale. Do not treat a planned intention as
   an answered question, empirical result, maturity signal or new write authority.
3. Publish/refresh the complete actor-owned intention using the observed snapshot and expected
   revision. Coordinator checks CAS, assigns the next sequence, durably appends the event,
   fsyncs it, atomically replaces/fsyncs snapshot, and only then returns the durable receipt.
4. A changed snapshot/revision requires refresh and explicit reconsideration, not invisible
   overwrite/retry. A lost acknowledgment means uncertain publication: recover the same
   `request_id` and digest to learn the original durable outcome **before execution**. A
   duplicate identical request returns its original receipt; reused identity/different payload
   rejects. Never submit a fresh request merely because the receipt was lost.
5. Before consuming research budget, refresh again, obtain acknowledged current active intent,
   verify ownership/revision/freshness and same remaining allocation, and request execution
   accounting. Record reasoning/transport/research cost, receipt and exact knowledge revision.
   Execute only authorized work; preserve full source/evidence/PM history and output refs.
6. After the result, refresh, publish the new state/output/budget data, and finish the allotted
   action/turn. Only coordinator closes the round once every admitted actor finished or the
   registered failure policy closed it. Refresh retained work according to pinned cadence.

The standalone utility exposes `initialize`, `snapshot`, `refresh`, `publish`,
`refresh-intention`, `execute`, `finish-round`, `close-failure`, and `recover`. Its help provides
JSON request shapes; use the runner's exact pin/config/path and preserve external request files
outside knowledge bodies. `snapshot` is a billed refresh, not an unlogged zero-cost read.
Submission/deduplication/receipt recovery belong to the same billed request lifecycle; these
protocol-allocation units do not assert measured CPU/tokens or experimental equivalence.

The coordinator can recover an interrupted durable append/snapshot window using its retained
write-ahead request; it never drops a complete accepted event. A corrupt/truncated log without
matching recoverable intent is unavailable, not an empty channel. Default outage policy pauses
budget-consuming collective work until authoritative refresh/recovery or registered closure.
Record failed refresh/diagnostic/time, interrupted run and consumed allocation. Offline ara
commands remain usable, but cannot authorize collective execution during a channel outage.

Planned/active intentions expire when coordinator round **exceeds** `expires_after_round`
without owner refresh. Retain expired events/history; display them as stale context rather
than active reservations or disappearing evidence. A disappeared actor cannot reserve forever.
Old communities are not reused or silently copied into a new run. Keep all published/refresh/
expiry/recovery receipts available to audit a choice, including failed CAS and outage choices
where the consumer records them. Do not claim shared-channel integration until actual independent
fork processes publish/refresh and the pinned binary/merge surface is exercised.
