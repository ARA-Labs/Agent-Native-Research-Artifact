#!/usr/bin/env python3
"""Append one notebook record safely (the model supplies values; this script
owns the format: escaping, ids, timestamps, one-line JSONL). Stdlib only.

  log.py frame   --question Q [--subq A --subq B ...]
  log.py bet     --action A --prediction P [--confidence 0.6] [--target T]
  log.py settle  --bet ID --outcome O --verdict confirmed|surprised|anomaly
                 [--update U] [--door D --door D2 ...]
  log.py reframe --change C [--trigger b1 --trigger b2 ...]
  log.py claim   --statement S --scope SC [--kill-shot ID] [--limitation L ...]

Optional: --notebook PATH (default ./fuzz-notebook.jsonl)
Prints the appended line; exits 2 on rule violations it can catch at write time.
"""
import argparse, json, sys
from pathlib import Path


def load(nb):
    recs = []
    if nb.exists():
        buf = ""
        for line in nb.read_text().splitlines():
            buf = buf + ("\n" if buf else "") + line
            try:
                recs.append(json.loads(buf)); buf = ""
            except json.JSONDecodeError:
                continue
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["frame", "bet", "settle", "reframe", "claim"])
    ap.add_argument("--notebook", default="fuzz-notebook.jsonl")
    ap.add_argument("--question"); ap.add_argument("--subq", action="append", default=[])
    ap.add_argument("--action"); ap.add_argument("--prediction")
    ap.add_argument("--confidence", type=float); ap.add_argument("--target")
    ap.add_argument("--bet"); ap.add_argument("--outcome"); ap.add_argument("--verdict")
    ap.add_argument("--update"); ap.add_argument("--door", action="append", default=[])
    ap.add_argument("--change"); ap.add_argument("--trigger", action="append", default=[])
    ap.add_argument("--statement"); ap.add_argument("--scope")
    ap.add_argument("--kill-shot", dest="kill_shot"); ap.add_argument("--limitation", action="append", default=[])
    a = ap.parse_args()

    nb = Path(a.notebook)
    recs = load(nb)
    bets = {r.get("id") for r in recs if r.get("type") == "bet"}
    settled = {r.get("bet") for r in recs if r.get("type") == "settle"}

    def die(msg):
        print(f"REJECTED: {msg}", file=sys.stderr); sys.exit(2)

    if a.kind == "frame":
        if not a.question: die("frame needs --question")
        v = 1 + sum(1 for r in recs if r["type"] in ("frame", "reframe"))
        rec = {"type": "frame", "v": v, "question": a.question, "subq": a.subq}
    elif a.kind == "bet":
        if not (a.action and a.prediction): die("bet needs --action and --prediction (BEFORE acting)")
        rec = {"type": "bet", "id": f"b{sum(1 for r in recs if r['type']=='bet')+1}",
               "action": a.action, "prediction": a.prediction}
        if a.confidence is not None: rec["confidence"] = a.confidence
        if a.target: rec["target"] = a.target
    elif a.kind == "settle":
        if a.bet not in bets: die(f"settle references unknown bet '{a.bet}' — bet first (rule 1)")
        if a.bet in settled: die(f"bet '{a.bet}' already settled")
        if a.verdict not in ("confirmed", "surprised", "anomaly"): die("verdict must be confirmed|surprised|anomaly")
        if a.verdict == "surprised" and not a.update: die("surprised requires --update (rule 2)")
        if not a.outcome: die("settle needs --outcome")
        rec = {"type": "settle", "bet": a.bet, "outcome": a.outcome,
               "verdict": a.verdict, "doors": a.door}
        if a.update: rec["update"] = a.update
    elif a.kind == "reframe":
        if not a.change: die("reframe needs --change")
        v = sum(1 for r in recs if r["type"] in ("frame", "reframe"))
        rec = {"type": "reframe", "from": v, "to": v + 1, "trigger": a.trigger, "change": a.change}
    else:  # claim
        if not (a.statement and a.scope): die("claim needs --statement and --scope (rule 5)")
        rec = {"type": "claim", "statement": a.statement, "scope": a.scope,
               "kill_shot": a.kill_shot, "limitations": a.limitation}

    line = json.dumps(rec, ensure_ascii=False)
    with open(nb, "a") as f:
        f.write(line + "\n")
    print(line)


if __name__ == "__main__":
    main()
