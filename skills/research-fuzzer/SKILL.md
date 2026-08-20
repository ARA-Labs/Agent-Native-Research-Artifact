---
name: research-fuzzer
description: >
  Treat an open-ended investigation the way a fuzzer treats a program. After every
  action, reflect on two things a fuzzer always knows and an agent never does: did
  anything NEW happen, and where have I NOT been yet. Keeps an append-only notebook
  of predictions and outcomes; reports what you explored, the leads you saw but
  never followed, unexplained results, and a going-in-circles alarm. Use for ANY
  investigation
  without a known map: research experiments, debugging, data analysis, literature
  or market research, evaluations. Fire it (1) when starting an investigation,
  (2) after every action or batch of actions that returned results, (3) before
  stating any conclusion. Skip it for trivial single-step tasks.
---

# research-fuzzer — the fuzzer's feedback loop, for any investigation

A greybox fuzzer almost never finds the bug on a given run. It still wins,
because every single run answers one cheap question: **did that reach somewhere
new?** The answer steers the next input. An agent investigating an open-ended
question has no such loop by default: it reacts to its last result, grinds the
same corner, and stops when the budget runs out — sampling, not searching.

This skill gives you the fuzzer's loop. The mapping is exact:

| the fuzzer has | you keep (the panel's word) | plain words |
|---|---|---|
| coverage map | `explored` — settled bets, per sub-question | where you have already walked |
| seed queue | `leads` — noticed but never tried | doors you passed, never opened |
| crash reports | `unexplained` — outcomes you cannot explain | the confusion ledger |
| "no new coverage" | `novelty` — recent results that taught you nothing | the going-in-circles alarm |
| triage before reporting | `gate` — before any conclusion | no claim until the books are clean |

Fuzzing vocabulary stops here: the panel and the rules below use the neutral
words, so the skill does not nudge you toward software-shaped experiments when
your world is biology, markets, or people.

Nobody — you included — can know what fraction of the *world* you have covered;
that number needs a god's-eye view that does not exist. Every reading above is
computed from your own footprints instead. That is the whole trick, and it is
the same trick fuzzers use: coverage is always measured against what you have
seen, never against all possible behaviors.

## Works anywhere — by construction

- **Any domain.** An "action" is anything that returns information: an
  experiment, a query, a benchmark run, an interview, a paper read, a grep.
  Predictions may be quantitative ("loss < 0.5") or qualitative ("most users
  will cite price"); they only need to be falsifiable.
- **Any agent, any harness.** This file is the skill. Everything below is
  executable by hand with no tooling at all; `scripts/tally.py` (stdlib-only
  Python) is an optional convenience that computes the same panel faster. No
  network, no packages, no framework.
- **Any timescale.** The notebook is one append-only file at the investigation
  root — it survives context loss, session restarts, and handoffs to other
  agents. A new session starts by reading the notebook and printing the panel.
- **When not to use it.** Single-step lookups and trivial fixes. The loop earns
  its overhead only when the answer is genuinely unknown and multiple actions
  will be needed.
- **Investigation, not synthesis.** This loop is built for probing a world that
  already exists — *why is X happening, what law governs Y, where is the bug*.
  For creative work (designing a system, constructing a proof, writing), apply
  it only to the investigative episodes inside the work — "will this design
  choice survive load?" is a bet; the act of creation itself is not.

## The notebook

One append-only file at the investigation root: `fuzz-notebook.jsonl`.
Never edit or delete past lines — append corrections as new lines.

**Prefer the writer script** when Python is available — it owns the format
(escaping, ids, timestamps) and rejects rule violations at write time, so you
never hand-craft JSON:

```bash
python3 scripts/log.py bet    --action "interview 5 churned users" \
                              --prediction "most cite price" --confidence 0.6 --target "price?"
python3 scripts/log.py settle --bet b1 --outcome "4/5: need disappeared" \
                              --verdict surprised --update "churn may not be dissatisfaction" \
                              --door "interview RETAINED users"
```

Hand-append JSON lines only when no tooling exists — one record per line,
newlines inside strings escaped as `\n`. Five record types (entries may be
written in any language):

```jsonl
{"type":"frame","v":1,"question":"why are users churning?","subq":["price?","UX?","competitors?"]}
{"type":"bet","id":"b1","action":"interview 5 churned users","prediction":"most cite price","confidence":0.6,"target":"price?"}
{"type":"settle","bet":"b1","outcome":"4/5 said their need disappeared; price never mentioned","verdict":"surprised","update":"churn may not be dissatisfaction — add 'need evaporated?' branch","doors":["interview RETAINED users","segment churn by tenure"]}
{"type":"reframe","from":1,"to":2,"trigger":["b1","b4","b7"],"change":"added subq: need-evaporation; demoted price"}
{"type":"claim","statement":"churn is driven by X","scope":"within frame v2 and the doors entered","kill_shot":"b14","limitations":["door 'interview RETAINED users' never entered"]}
```

## The rules (hard — these ARE the skill)

**1. No action without a bet.** Before every action, append one `bet` line:
what you will do, **what you predict will happen**, how confident, and which
sub-question it serves. The prediction is written BEFORE you see the result —
that ordering is the entire defense against fooling yourself. A result you
would have "expected either way" teaches nothing; make the prediction sharp
enough to be wrong.

**2. Every settle picks exactly one verdict.**
- `confirmed` — the prediction held. You learned little. A streak of confirmed
  is a **leave signal, not an achievement**: no new coverage here.
- `surprised` — the prediction broke. You MUST write the `update`: which belief
  changed, in one sentence. A surprise without an update line is not settled.
- `anomaly` — you cannot explain it. It goes on the unexplained-results
  ledger, may never be silently dropped, and blocks the gate (rule 5) until
  resolved or explicitly carried as a limitation.

**3. Every settle asks: what did this open?** Each result exposes leads you now
know you could chase (a segment you noticed, a condition you held fixed, a
control you lack). Append them to `doors` — even when you do not take them.
This queue is your only honest measure of "how much is left": never "40% of
the world" (unknowable), always "9 leads seen and never tried" (exact).

**4. Three unresolved anomalies force a reframe.** When unexplained results cluster, stop
asking "which belief is wrong" and ask: **"what axis is missing from my frame
for these to make sense?"** Publish `frame v(N+1)` with the new sub-question.
A reframe is not an embarrassment; it is usually the most valuable single
discovery of the run — record it as one.

**5. The gate: no claim without passing it.** Before stating any conclusion:
- it must account for every settled bet, or the exceptions are listed;
- the unexplained-results ledger is empty, or each open item is named in `limitations`;
- you have bet and settled a **kill shot** — the one action you believe most
  likely to break the claim, aimed somewhere you have not yet tested;
- the claim carries its scope: *"within frame vN and the doors entered"* —
  never an unscoped "the answer is X".

## The panel

After each batch, produce the panel — run `python scripts/tally.py
fuzz-notebook.jsonl` if Python is available, otherwise compute it by hand from
the notebook (every reading is a count):

```
PANEL — frame v2 · 23 bets settled
  explored    : price? 6 · UX? 4 · need-evaporated? 8
  leads       : 9 untried · 5 followed
                oldest untried: "interview RETAINED users" (seen 12 settles ago)
  novelty     : last 10 settles → 8 confirmed, 1 surprised, 1 anomaly
                nothing new here lately — consider a far lead
  unexplained : 1 open (b17: retention spike in oldest cohort)
  spread      : 8 of your last 10 bets probed the same area (need-evaporated?)
  gate        : BLOCKED (1 unexplained open; no kill-shot bet on record)
```

The statistics window adapts to your pace: with only a handful of settles (slow,
expensive experiments), the panel reports plain counts and withholds trend
advice — a "last 10" reading means nothing when you have run 3.

Read it, then decide. **The panel informs; it never commands.** It only makes
your own footprints visible: where you walked, what you saw and skipped,
whether the last stretch taught you anything. State in one sentence what the
readings imply before placing the next bet — a reading that is never read is
not feedback.

## What this is not

- The panel steers; it never certifies. Passing the gate means "not yet proven
  wrong within what you explored" — never "correct".
- Confirmed streaks feel like progress. They are the fuzzer's strongest signal
  to move: this region yields no new coverage.
- The queue only contains doors you *noticed*. Doors you never saw are not on
  it — which is why conclusions carry scope, and why a fat queue is a sign of
  good peripheral vision, not of failure.
- Do not tune the instrument mid-run: no reclassifying anomalies as confirmed,
  no editing old lines, no writing bets after seeing results. Editing the
  instrument to please the reading is the exact failure this skill exists to
  prevent.
