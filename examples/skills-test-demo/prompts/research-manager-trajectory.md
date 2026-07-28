# research-manager End-to-End Trajectory Replay

Copy everything below the line into your agent, in a checkout of this repo, whenever
you've changed anything `research-manager` depends on (`skills/research-manager/SKILL.md`
or any file under `skills/research-manager/references/`). Unlike a fixture that only
exercises one capability, this replays a real research trajectory through the *entire*
skill — Context Harvester, Event Router, Maturity Tracker, Logic Layer Reconciliation, and
the taste-comment capability — so a reviewer can read the resulting ARA and judge whether
the routing/staging/crystallization decisions look right. That judgment is inherently a
human one; nothing here scripts a pass/fail verdict on it.

**Why this trajectory, not an invented one**: every event below is grounded in the actual
research narrative "Deep Residual Learning for Image Recognition" (He et al., 2015) tells
about itself (§1, §3, §4) — the paper's own account of noticing degradation, ruling out
two explanations, reformulating the approach, validating it, and scaling it. Nothing about
*what happened* is invented; the only thing not drawn from the paper is the turn-by-turn
framing itself (how one already-real event maps onto research-manager's own event types),
and the live taste-comment reactions at the end, which are inherently synthesized at
test-time — that's what the capability is for.

---

You are acting as the `research-manager` skill, replaying a research trajectory from
scratch. Start from an ARA that doesn't exist yet at `examples/skills-test-demo/ara/` (if
it currently has content from a prior run, that's the artifact you're regenerating — read
it for calibration, then rebuild it turn by turn rather than patching it). Read
`skills/research-manager/SKILL.md` and every file under `skills/research-manager/references/`
first — that is the current spec, not this prompt; follow whatever it currently says even
if it has changed since this prompt was written.

## The trajectory

Process each event below as its own turn (Context Harvester → Event Router → Maturity
Tracker → Logic Layer Reconciliation, per SKILL.md's Per-Turn Procedure), in order. For
each: classify it per `event-taxonomy.md`, decide direct-vs-staged, and — for staged
events — check whether a closure signal has fired *this turn or a later one*, per the real
closure-signal taxonomy (don't force premature crystallization; also don't hold something
staged past the point where a real signal already fired).

1. **Opening question**: is learning better networks as easy as stacking more layers? The
   paper motivates this with CIFAR-10 curves at two depths where the deeper net trains
   worse, not just tests worse.
2. **AI action**: before running anything, note the paper's stated training methodology —
   batch-norm placement (right after each conv, before the activation, no dropout).
3. **Experiment**: a plain-net depth scan on CIFAR-10 across several depths — deeper nets
   degrade.
4. **Experiment**: the same plain-vs-depth comparison repeated on ImageNet at two depths —
   degradation confirmed at a different scale, not CIFAR-specific.
5. **Dead end**: vanishing gradients considered and ruled out — signal norms stay healthy
   with batch norm in place, and the deeper plain net still reaches decent accuracy, so
   optimization is progressing, just slowly.
6. **Dead end**: training longer (3x iterations) considered and ruled out per a footnote —
   the degradation persists.
7. **Pivot**: since neither training-procedure explanation held up, reformulate the target
   of each block to a residual mapping instead of a direct one.
8. **Decision**: realize that reformulation via a parameter-free identity shortcut, rather
   than a gated or fully-projected one.
9. **Experiment**: residual vs. plain nets at two depths on ImageNet — degradation removed.
10. **Experiment**: an ablation across a spectrum of shortcut designs from parameter-free to
    fully-projected — differences are small.
11. **Dead end**: a single-layer residual function considered and ruled out — no observed
    benefit over a plain linear layer.
12. **Decision**: adopt a 3-layer bottleneck block design for depths beyond ~50 layers, to
    keep compute from scaling with depth.
13. **Experiment**: a depth scan with bottleneck blocks at three depths on ImageNet —
    monotonic improvement, state-of-the-art result.
14. **Experiment**: a CIFAR-10 depth scan across a wide range including two extreme depths —
    the deepest variant still trains but shows a generalization gap.
15. **Decision**: adopt a learning-rate warmup phase specifically for one of the deepest
    CIFAR variants, where the standard rate stalls early progress.
16. **Experiment**: transfer the deeper backbone into an object detector, swapping out a
    non-residual backbone — substantial gains on two detection benchmarks.

## Live taste phase

Once the trajectory above is fully processed, switch roles: you are now the person actually
running this test, reading the ARA you just built and reacting to it as yourself, out loud,
per `references/taste-comments.md`. This part is NOT drawn from the paper — it's your own
live reaction, which is what taste comments are for. Produce 4-6 reactions covering:

- At least one claim and one heuristic or trace node.
- A mix of attitudes (`endorse | uncertain | reject`) and objects of judgment
  (`claim | evidence | framing | priority`).
- At least one reaction that also contains an actionable suggestion, so the taste/pipeline
  co-firing rule gets exercised — the suggestion should independently route through the
  normal pipeline (e.g. as a new `question` node), not get absorbed into the taste comment's
  free text.

Follow the confirm-before-write procedure as written — narrate which element you resolved
each reaction to and why before writing it.

## When done

Show a diff of everything under `examples/skills-test-demo/ara/` and a short summary: how
many turns were direct-routed vs. staged, how many staged observations crystallized and via
which signal, and the taste reactions you added. If the result reads like something the spec
actually intends, commit the updated `ara/` as part of your PR — the reference ARA in this
repo is then whatever the most recent contributor's real run produced. If a routing or
crystallization decision looks wrong on review, that's a bug (or an ambiguity worth
resolving) in the skill you're testing, not in this prompt. That review — reading the
resulting `ara/` and judging whether the routing/staging/crystallization decisions look
right — is the actual test; nothing here scripts a pass/fail verdict on it.
