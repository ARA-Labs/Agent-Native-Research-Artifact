#!/usr/bin/env python3
"""research-fuzzer panel: compute the readings from fuzz-notebook.jsonl.

Stdlib only. Usage:  python tally.py [path/to/fuzz-notebook.jsonl]
Exit code 1 if the notebook violates the protocol (settle without bet,
edits out of order), so harnesses can treat protocol breaks as failures.
"""
import json
import sys
from collections import Counter

CIRCLE_WINDOW = 10     # max trend window; adapts down when few settles
MIN_TREND = 5          # below this many settles, report counts but no trend advice
REFRAME_AT = 3         # rule 4: unresolved anomalies that force a reframe


def load(path):
    """Strict JSONL: one record per line. Malformed lines are skipped and
    reported — scripts/log.py writes correct lines by construction."""
    recs, bad = [], []
    for n, line in enumerate(open(path), 1):
        if not line.strip():
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            bad.append(n)
    if bad:
        print(f"note: skipped {len(bad)} malformed line(s) {bad} — append records with scripts/log.py")
    return recs


def main(path):
    recs = load(path)
    problems = []

    frames = [r for r in recs if r.get("type") == "frame"]
    reframes = [r for r in recs if r.get("type") == "reframe"]
    bets = {r["id"]: r for r in recs if r.get("type") == "bet"}
    settles = [r for r in recs if r.get("type") == "settle"]
    claims = [r for r in recs if r.get("type") == "claim"]

    if not frames:
        problems.append("no frame record — start with one (rule: the map is a draft, but there must be a draft)")
    version = 1 + len(reframes)

    # ---- protocol validation -------------------------------------------------
    bet_order = [r["id"] for r in recs if r.get("type") == "bet"]
    settled_ids = set()
    for s in settles:
        b = s.get("bet")
        if b not in bets:
            problems.append(f"settle references unknown bet '{b}'")
            continue
        if bet_order.index(b) > len(bet_order):  # defensive; order is append-only
            pass
        if b in settled_ids:
            problems.append(f"bet '{b}' settled twice")
        settled_ids.add(b)
        if s.get("verdict") not in ("confirmed", "surprised", "anomaly"):
            problems.append(f"settle of '{b}': verdict must be confirmed|surprised|anomaly")
        if s.get("verdict") == "surprised" and not s.get("update"):
            problems.append(f"settle of '{b}': surprised but no 'update' — rule 2")
        if "doors" not in s:
            problems.append(f"settle of '{b}': missing 'doors' (may be empty list) — rule 3")

    unsettled = [b for b in bet_order if b not in settled_ids]

    # ---- corridors (chalk marks) ---------------------------------------------
    by_target = Counter(bets[s["bet"]].get("target", "?") for s in settles if s.get("bet") in bets)

    # ---- doors ----------------------------------------------------------------
    doors_seen = []  # (desc, opened_at_index)
    for i, s in enumerate(settles):
        for d in s.get("doors", []) or []:
            doors_seen.append((d, i))
    entered_actions = {bets[s["bet"]].get("action", "") for s in settles if s.get("bet") in bets}
    dead = [s for s in settles if s.get("verdict") == "anomaly" and s.get("dead")] + \
           [r for r in recs if r.get("type") == "settle" and r.get("dead")]
    # a door counts as entered if any later bet's action mentions it (loose match by inclusion)
    door_status = []
    all_actions = [b.get("action", "") for b in bets.values()]
    for desc, seen_i in doors_seen:
        hit = any(desc.lower() in a.lower() or a.lower() in desc.lower() for a in all_actions)
        door_status.append((desc, seen_i, "entered" if hit else "open"))
    open_doors = [(d, i) for d, i, st in door_status if st == "open"]
    entered_doors = [(d, i) for d, i, st in door_status if st == "entered"]

    # ---- circle alarm (window adapts to pace) -----------------------------------
    win = min(CIRCLE_WINDOW, len(settles))
    recent = settles[-win:] if win else []
    rc = Counter(s.get("verdict") for s in recent)

    # ---- anomalies --------------------------------------------------------------
    resolved = set()
    for r in reframes:
        resolved.update(r.get("trigger", []))
    for c in claims:
        resolved.update(c.get("limitations", []))
    anomalies = [s for s in settles if s.get("verdict") == "anomaly" and s.get("bet") not in resolved
                 and not s.get("resolved")]

    # ---- gate ---------------------------------------------------------------------
    kill_shots = [c for c in claims if c.get("kill_shot") in settled_ids]
    gate_blockers = []
    if anomalies:
        gate_blockers.append(f"{len(anomalies)} unexplained result(s) open")
    has_kill = any(bets.get(bid, {}).get("kill_shot") for bid in bets) or \
               any("kill" in (bets[s["bet"]].get("target", "") or "") for s in settles if s["bet"] in bets)
    if not has_kill and not kill_shots:
        gate_blockers.append("no kill-shot bet on record")

    # ---- print panel ------------------------------------------------------------
    print(f"PANEL — frame v{version} · {len(settles)} bets settled, {len(unsettled)} pending")
    if by_target:
        print("  explored    :", " · ".join(f"{t} {n}" for t, n in by_target.most_common()))
    if doors_seen:
        oldest = min(open_doors, key=lambda x: x[1]) if open_doors else None
        line = f"  leads       : {len(open_doors)} untried · {len(entered_doors)} followed"
        print(line)
        if oldest:
            age = len(settles) - oldest[1]
            print(f"                oldest untried: \"{oldest[0]}\" (seen {age} settles ago)")
    else:
        print("  leads       : none recorded yet — every settle must ask what it opened (rule 3)")
    if recent:
        print(f"  novelty     : last {len(recent)} settles → "
              f"{rc.get('confirmed',0)} confirmed, {rc.get('surprised',0)} surprised, {rc.get('anomaly',0)} anomaly")
        if len(recent) < MIN_TREND:
            print(f"                (only {len(settles)} settles so far — counts only, no trend yet)")
        elif rc.get("confirmed", 0) >= 0.8 * len(recent):
            print("                nothing new here lately — consider a far lead (confirmed streak = leave signal)")
    if anomalies:
        print(f"  unexplained : {len(anomalies)} open → " +
              "; ".join(f"{a['bet']}: {a.get('outcome','')[:60]}" for a in anomalies[:3]))
        if len(anomalies) >= REFRAME_AT:
            print(f"                {len(anomalies)} open — REFRAME is mandatory (rule 4): what axis is missing?")
    else:
        print("  unexplained : none")
    if len(recent) >= MIN_TREND:
        tgt = Counter(bets[s["bet"]].get("target", "?") for s in recent if s.get("bet") in bets)
        top, n = tgt.most_common(1)[0]
        if n >= 0.7 * len(recent):
            print(f"  spread      : {n} of your last {len(recent)} bets probed the same area ({top})")
        else:
            print(f"  spread      : last {len(recent)} bets across {len(tgt)} areas")
    print(f"  gate        : {'BLOCKED (' + '; '.join(gate_blockers) + ')' if gate_blockers else 'open — remember the scope line'}")

    if problems:
        print("\nPROTOCOL VIOLATIONS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fuzz-notebook.jsonl")
