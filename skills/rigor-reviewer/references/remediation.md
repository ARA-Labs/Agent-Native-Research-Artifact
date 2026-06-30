# Remediation contract (Seal Level 3)

Load and follow this file **only after** the Level 2 report is written AND the user has explicitly
authorized fixing (Step 8 of SKILL.md). It defines the *closed-loop remediation* the reviewer is
permitted to perform on the ARA. Treat every rule here as binding — when a rule and convenience
conflict, the rule wins.

You are now applying the review's own findings to the ARA: auto-execute the fixes that can be done
honestly from data already in the ARA, route everything else to a deferred worklist, and re-seal
after each change. You never invent data.

## The fabrication firewall — the one rule that makes auto-fixing safe

> **A fix may only re-express, relocate, scope, or re-file knowledge that already exists in the ARA
> or its cited sources. It may NEVER create a new empirical result.**

A new evidence table is allowed *only* if every number in it is transcribed from an already-read
source (a THREAD/log, a README, a runs index, an existing evidence file) — tag it `Extraction type:
derived_subset` and carry the source ref. If a fix would require a number the ARA does not already
have, it is **deferred**, not invented. Re-running Seal Level 1 after every change is the backstop.

## Which findings you may apply

Act only on findings whose `fix_class` ends in `-auto`:

| fix_class | apply? | action |
|---|---|---|
| `authoring-auto` | YES | reword a claim, soften an over-claim, move a mechanism from Statement to Interpretation, split/merge a tree node, add a cross-ref, fix terminology, add an attribution note |
| `data-derivable-auto` | YES (firewall applies) | file a new evidence table/figure whose every value is transcribed from a cited source; `fix_action.source_for_data` MUST be present |
| `compute-bound-defer` | NO — defer | needs a new run / rerun / ablation / paired-seed protocol / measurement |
| `external-defer` | NO — defer | needs fetching a URL / paper / repo not in the ARA |
| `judgment-defer` | NO — defer | a research decision only the author can make |

If a finding lacks a `fix_class`, classify it yourself with this test: *can every cell of the fix be
quoted from a source already in the ARA?* Yes → an `-auto` class; any cell needs running something →
a `-defer` class. **When unsure, defer** (a missed auto-fix is cheap; a fabricated one is fatal).

A finding can split: "restate the claim AND rerun to confirm" → the restate is `authoring-auto`
(apply it); the rerun is `compute-bound-defer` (queue it).

## Procedure (one round)

1. **Apply each `-auto` finding, in severity order** (critical→suggestion), with the *minimal* edit
   (prefer a targeted edit over a rewrite).
   - For a new evidence object: write the markdown **and render a sibling PNG** (Level 1 requires a
     `.png` next to every `evidence/tables/*.md` and `evidence/figures/*.md`); wire it into the
     relevant claim's `Evidence basis` and into `evidence/README.md`.
   - **Provenance**: the user directed this remediation → `user-revised`; you inferred a fix
     autonomously → `ai-suggested`.
   - **Preserve falsifiability**: a reworded claim must stay a falsifiable assertion with intact
     Falsification criteria. If a fix would make a claim un-falsifiable, do NOT apply it — reclassify
     it `judgment-defer` and surface it.
   - **Idempotent**: skip a fix already present.
   - **Append-only journey**: never edit `trace/sessions/*` or `staging/*` except to append.
2. **Re-run Seal Level 1** (`references/seal1_check.py <ara_dir>`, or inline the checks). If any
   check fails, repair the regression before continuing — a remediation that breaks Level 1 is
   rejected.
3. **Re-review only the changed entities** (Level 2 delta). Confirm each finding's weakness is
   genuinely addressed and no new weakness was introduced.
4. **Record the round** (see below).
5. **Loop or stop**: loop if this round resolved ≥1 finding and `-auto` findings remain (a fix can
   expose a follow-on, e.g. a ledger entry); cap at **3 rounds**. Stop when only `-defer` findings
   remain.

## Anti-gaming

Do **not** raise a dimension score merely because you self-applied a fix. A score rises only if the
underlying epistemic ceiling actually moved (e.g. a previously ungrounded claim now cites filed
data). If the binding constraint is a deferred compute item, the ceiling is only *mitigated* — hold
the score and say so. Inflating the grade by self-remediation is gaming and is forbidden.

## Recording the round (provenance + journey)

1. **`level2_report.json`**: append a `remediation_round_N` object — `policy`, per-finding
   `findings_status` (`resolved` / `partially_resolved` / `deferred`) with the `action` taken, a
   `deferred_requiring_compute` (and `_external` / `_judgment`) list, and `grade_after` /
   `mean_after` (unchanged unless a ceiling genuinely moved).
2. **`trace/sessions/YYYY-MM-DD_NNN.yaml`** (append-only): a session record with `logic_revisions`
   (before/after for every `logic/` edit), `ai_actions` (files changed, validation result), and an
   `open_threads` entry per deferred item. **If the research-manager skill is available, invoke it
   for this instead of hand-writing the record**, passing the remediation as the turn's activity —
   it owns the trace-journey schema.
3. **`trace/pm_reasoning_log.yaml`**: one entry noting the triage decisions and any near-miss (a
   finding you considered auto-fixing but deferred, and why).
4. Update `trace/sessions/session_index.yaml`.

## Stop / report

When only `-defer` findings remain, stop and report: rounds run; findings resolved / partially /
deferred (counts); Level 1 status; whether the grade moved and why/why-not; and the deferred queue
(each item: finding id + what compute/decision it needs). Be explicit that the deferred items are
the reason the grade did or did not improve.

## Hard rules (recap)

1. **Fabrication firewall** — never create a new empirical number; defer instead.
2. **Re-seal after every round** — a fix that breaks Level 1 is repaired before reporting.
3. **Defer honestly** — compute/experiment/external/judgment findings go to the human, never faked or dropped.
4. **No score gaming** — self-remediation never raises a score unless the ceiling truly moved.
5. **Preserve falsifiability** — never rewrite a claim into an un-falsifiable form.
6. **Append-only journey; record before/after** for every `logic/` edit.
7. **Minimal, idempotent edits; cap at 3 rounds.**
