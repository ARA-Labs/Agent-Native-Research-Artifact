# Frontier component

Install independently from shared intentions. This page is only loaded when the pinned component
set includes `frontier`. The common roles/failure pages are loaded directly from the component
entrypoint and are identical to every collective control. This component adds no intention
publication, remote synchronization, agent, network call, LLM or budget allocation.

Before choosing work, build a source-qualified frontier from the exact selected artifact:

```sh
ara -C <fork> status --json
ara -C <fork> open --full --json
ara -C <fork> ls --json
ara -C <fork> show --document PAPER.md --source --full --json
ara -C <fork> show --document staging/observations.yaml --source --full --json
ara -C <fork> show --document trace/exploration_tree.yaml --source --full --json
ara -C <fork> refs <native-selector> --json
```

Retrieve every relevant complete logic/session/merge/conflict body via `show --document ...
--source --full --json`. Respect the source skill's scope and roles. `open` reasons and excerpts
are aids, not a complete research judgment. Include unresolved questions, unpromoted or stale
observations, pending forensic bindings, unfinished claims, unresolved merge conflicts, and
relevant negative evidence. Use ls/full show to recover items outside open's bounded categories.
No new public frontier command is assumed.

Return context for the agent's original reasoning, not an automatic priority schedule. Example
schema (values are illustrative, not observed proof):

```json
{
  "format": "ara.collective-frontier/v1",
  "source_identity": "fork-a",
  "artifact_revision": "content:<actual digest from the selected artifact>",
  "intention_snapshot": {"installed": false},
  "current_local": [{"native_ref": "trace:N01", "kind": "question", "reason": "unresolved", "body_digest": "sha256:<actual full-show digest>"}],
  "imported": [],
  "remote_intentions": {"active": [], "stale": []},
  "conflicts": [],
  "choice_rationale": "<agent judgment grounded in complete verified bodies>"
}
```

Keep current-local facts separate from imported facts whose source key/revision/native ref comes
from the portable merge ledger; equal local IDs or display labels are not identity proof.
Each fact carries native ref, exact source-qualified revision and verified full body/digest.
Use merge reports/retained conflict candidates, never an optimistic synthesized resolution.
If intentions are also installed, obtain their authoritative committed snapshot separately,
record `installed: true`, sequence/round and active/stale source-qualified intention context.
Without that component explicitly report it absent; never imply open includes unseen forks.
Remote planned/completed/expired records are advisory intentions, not imported knowledge facts
or evidence that a question is answered. Stale records remain visible as stale context.

The agent may reason about priority under its unchanged research procedures and same total
budget. Preserve uncertainty, relevant negatives, full source grounding and normal decision/
trace/session history. Do not auto-promote staged material, settle contradictions, suppress an
item merely because another actor owns it, or equate pending work with a result. Deliberate
verification remains allowed. Report the chosen native refs, source revision and rationale to
the authorized fork PM; when intentions are installed also preserve observed sequence/round
and publication receipt. The extension changes context supplied to selection, not the evidence
standard or stopping/closure criteria.
