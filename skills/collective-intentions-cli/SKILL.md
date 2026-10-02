---
name: collective-intentions-cli
description: >
  Independently installable intentions context component for one-host collective ARA
  research. Trigger when the immutable collective run configuration enables intentions;
  preserves common roles, failure policy and the same total allocation across all conditions.
argument-hint: "[pinned run configuration]"
allowed-tools: Read, Bash(ara *|python *)
metadata:
  author: ara-commons
  version: "1.0.0"
  tags: [collective-research, intentions]
---

# Independent intentions component

This install surface is separate from interface-only CLI skills and from the other component.
Read directly, in this order:

- `references/roles.md` — exact common authority page used by every collective control.
- `references/failure-policy.md` — exact common budget/failure page used by every control.
- `references/intentions.md` — only this selected component's additional context/protocol.

Do not load the other component unless separately installed and selected by the immutable run
configuration. Both components can compose, deduplicating common pages by their exact digest
but recording/counting every supplied page. The plain Files and plain CLI collective controls
must receive the same common roles/failure pages. Noncollective interface-only copies receive
none of these pages. Check the exact contract/run/component/role approval revision before a
scored run; upstream roles/protocol approval and external harness15 integration are pending.
Standalone deterministic community-smoke scenarios are transport/fidelity checks, not scored
experiments, performance equivalence, distributed deployment or a hidden extra reasoning agent.
