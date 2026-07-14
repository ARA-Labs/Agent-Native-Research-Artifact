#!/bin/bash
# Run 3 additional ARA seeds (5, 6, 7) in parallel for rust_codecontests.
# Uses the updated ARA artifact (model adaptation guide added to heuristics.md).

set -euo pipefail

ARA_DRAFT="/Users/amberljc/Desktop/github-project/writing/ara-draft"
EXT_DIR="$ARA_DRAFT/code/eval/extension"
SCRIPT="$EXT_DIR/run_extension.py"
LOG_DIR="$EXT_DIR/logs"
RESULTS_DIR="$EXT_DIR/results"
SEND="$ARA_DRAFT/send.py"

mkdir -p "$LOG_DIR"

send_email() {
  python3 "$SEND" --subject "$1" --body "$2" 2>/dev/null || echo "[email] send failed"
}

get_best_score() {
  local cond=$1 seed=$2
  local traj="$RESULTS_DIR/rust_codecontests_${cond}_seed${seed}/_score_trajectory.json"
  if [ -f "$traj" ] && [ -s "$traj" ]; then
    python3 -c "
import json
data = json.load(open('$traj'))
if data:
    best = max(e['score'] for e in data)
    final = data[-1]['score']
    print(f'{final:.2f} (best={best:.2f})')
else:
    print('N/A')
" 2>/dev/null || echo "N/A"
  else
    echo "N/A"
  fi
}

run_one() {
  local cond=$1 seed=$2
  local log="$LOG_DIR/rust_${cond}_seed${seed}.log"
  echo "[batch] Starting rust_codecontests $cond seed$seed → $log"
  cd "$ARA_DRAFT/code" && python3 "$SCRIPT" run rust_codecontests "$cond" --seed "$seed" \
    > "$log" 2>&1
  local ec=$?
  echo "[batch] Finished rust_codecontests $cond seed$seed (exit $ec)"
  return $ec
}

send_email "rust_codecontests — ARA Extra Seeds Starting" \
"Launching 3 additional ARA seeds (5, 6, 7) in parallel.
Using updated ARA artifact with Model Adaptation Guide (heuristics.md now separates
model-agnostic principles from model-specific GPT-3.5 calibration).

Existing ARA results: seed0=0.65, seed1=0.45, seed2=0.40, seed3/4=running
Existing Baseline: seed0=0.60, seed1=0.80, seed2=0.35, seed3=0.85"

echo "========================================"
echo "[batch] Launching ARA seeds 5, 6, 7 in parallel"
echo "========================================"

run_one ara 5 &
PID5=$!
run_one ara 6 &
PID6=$!
run_one ara 7 &
PID7=$!

wait $PID5; EC5=$?
wait $PID6; EC6=$?
wait $PID7; EC7=$?

SCORE5=$(get_best_score ara 5)
SCORE6=$(get_best_score ara 6)
SCORE7=$(get_best_score ara 7)

FINAL_MSG="ARA extra seeds complete.

New ARA results:
  seed5: $SCORE5 (exit $EC5)
  seed6: $SCORE6 (exit $EC6)
  seed7: $SCORE7 (exit $EC7)

Existing ARA: seed0=0.65, seed1=0.45, seed2=0.40
Running (existing batch): seed3, seed4

Logs: $LOG_DIR/"

send_email "rust_codecontests — ARA Extra Seeds COMPLETE" "$FINAL_MSG"

echo "========================================"
echo "[batch] ALL DONE"
echo "$FINAL_MSG"
echo "========================================"
