---
name: collective-research-cli
description: >
  Common collective-research role and failure controls for independent one-host ARA forks.
  Load in every collective condition, including Files and plain CLI controls, before choosing
  or executing shared research work. Frontier and intentions are independent opt-in components.
argument-hint: "[run configuration; installed component set]"
allowed-tools: Read, Bash(ara *|python *)
metadata:
  author: ara-commons
  version: "1.0.0"
  tags: [collective-research, role-controls, failure-policy]
---

# Common collective controls

This is a separately versioned collective intervention, never an implicit part of
`research-foresight-cli`, `research-manager-cli` or `compiler-cli`. It changes no baseline
procedure merely by being installed. Read these pages directly:

- `references/roles.md` — identical common roles in every collective condition.
- `references/failure-policy.md` — identical common budget and failure controls.
- `references/frontier.md` — load directly only when frontier is selected.
- `references/intentions.md` — load directly only when intentions are selected.

Load neither component unless the immutable run configuration selects it. Frontier-only
installs `collective-frontier-cli`; intention-only installs `collective-intentions-cli`;
both install both component surfaces. Each carries the same common pages so either is
independently installable. Load common controls once by digest when both are composed;
record every actually supplied page and its tokens, not an estimated smaller bundle.
The plain Files and plain CLI collective controls also load these exact common pages.
The interface-only noncollective CLI/Files skills load none of this extension.

Check the pinned `evaluation/agent-cli/collective-contract.json`, roles, component set,
run identities, budgets, logical refresh/expiry parameters and failure policy before work.
Do not silently add a component, role, agent, merge advisor or budget allocation. Protocol
and writer-role approval is pending upstream review; local disposable smoke use is not
approval or scored research evidence. A real bounded standalone protocol consumer is
provided under `evaluation/agent-cli/community-smoke-scenarios/`; external runtime/harness
integration and all measurements remain deferred to plan15. Do not describe one-host
filesystem publication as multi-host deployment or an ara network capability.
