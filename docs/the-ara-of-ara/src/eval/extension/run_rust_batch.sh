#!/bin/bash
# Run remaining rust_codecontests seeds (ARA: 1,3,4 | Baseline: 2,3,4)
# Runs 2 in parallel (one per condition), sends email after each group.

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

get_score() {
  local cond=$1 seed=$2
  local meta="$RESULTS_DIR/rust_codecontests_${cond}_seed${seed}/_run_meta.json"
  if [ -f "$meta" ] && [ -s "$meta" ]; then
    python3 -c "import json; d=json.load(open('$meta')); print(d.get('best_achieved_score','N/A'))" 2>/dev/null || echo "N/A"
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

send_email "rust_codecontests — Batch Starting" \
"Starting 6 new seeds for rust_codecontests experiment.
ARA: seeds 1 (re-run), 3, 4
Baseline: seeds 2, 3, 4
Running in pairs (1 ARA + 1 Baseline in parallel).
Existing results: ARA seed0=0.65, seed2=0.50 | Baseline seed0=0.60, seed1=0.80"

echo "========================================"
echo "[batch] Group 1: ARA seed1 + Baseline seed2"
echo "========================================"
run_one ara 1 &
PID_ARA1=$!
run_one baseline 2 &
PID_BASE2=$!

wait $PID_ARA1; EC_ARA1=$?
wait $PID_BASE2; EC_BASE2=$?

SCORE_ARA1=$(get_score ara 1)
SCORE_BASE2=$(get_score baseline 2)
send_email "rust_codecontests — Group 1 Complete" \
"Group 1 results:
  ARA seed1: $SCORE_ARA1 (exit $EC_ARA1)
  Baseline seed2: $SCORE_BASE2 (exit $EC_BASE2)

Running total: ARA [seed0=0.65, seed1=$SCORE_ARA1, seed2=0.50] | Baseline [seed0=0.60, seed1=0.80, seed2=$SCORE_BASE2]"

echo "========================================"
echo "[batch] Group 2: ARA seed3 + Baseline seed3"
echo "========================================"
run_one ara 3 &
PID_ARA3=$!
run_one baseline 3 &
PID_BASE3=$!

wait $PID_ARA3; EC_ARA3=$?
wait $PID_BASE3; EC_BASE3=$?

SCORE_ARA3=$(get_score ara 3)
SCORE_BASE3=$(get_score baseline 3)
send_email "rust_codecontests — Group 2 Complete" \
"Group 2 results:
  ARA seed3: $SCORE_ARA3 (exit $EC_ARA3)
  Baseline seed3: $SCORE_BASE3 (exit $EC_BASE3)

Running total: ARA [seed0=0.65, seed1=$SCORE_ARA1, seed2=0.50, seed3=$SCORE_ARA3]
              Baseline [seed0=0.60, seed1=0.80, seed2=$SCORE_BASE2, seed3=$SCORE_BASE3]"

echo "========================================"
echo "[batch] Group 3: ARA seed4 + Baseline seed4"
echo "========================================"
run_one ara 4 &
PID_ARA4=$!
run_one baseline 4 &
PID_BASE4=$!

wait $PID_ARA4; EC_ARA4=$?
wait $PID_BASE4; EC_BASE4=$?

SCORE_ARA4=$(get_score ara 4)
SCORE_BASE4=$(get_score baseline 4)

# Compute summary stats
FINAL_MSG="All 6 seeds complete.

ARA scores:
  seed0=0.65, seed1=$SCORE_ARA1, seed2=0.50, seed3=$SCORE_ARA3, seed4=$SCORE_ARA4

Baseline scores:
  seed0=0.60, seed1=0.80, seed2=$SCORE_BASE2, seed3=$SCORE_BASE3, seed4=$SCORE_BASE4

Logs: $LOG_DIR/"

send_email "rust_codecontests — Batch COMPLETE" "$FINAL_MSG"

echo "========================================"
echo "[batch] ALL DONE"
echo "$FINAL_MSG"
echo "========================================"
