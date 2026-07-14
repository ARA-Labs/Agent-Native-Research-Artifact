#!/usr/bin/env python3
"""Judge both ARA and baseline runs on bam_T1, including incomplete runs."""
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_reproduction import generate_judge_prompt, load_tasks
from run_agent import _read_agent_outputs, RESULTS_DIR, JUDGE_MODEL

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

import anthropic

def judge_run(paper, task, condition, seed):
    tag = f"{task['task_id']}_{condition}_seed{seed}"
    output_dir = RESULTS_DIR / tag
    judge_path = output_dir / "_judge_result.json"

    if judge_path.exists():
        print(f"[judge] {tag}: already judged, loading...")
        return json.loads(judge_path.read_text())

    # Build prompt
    judge_prompt = generate_judge_prompt(paper, task, condition, seed)
    agent_output = _read_agent_outputs(output_dir)
    full_prompt = (
        judge_prompt
        + "\n\n---\n\n## Agent Output Files\n\n"
        + agent_output
    )

    print(f"[judge] {tag} ... ({len(full_prompt)} chars)", end=" ", flush=True)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=8192,
        temperature=0,
        messages=[{"role": "user", "content": full_prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    judge_result = json.loads(raw)
    judge_result["token_usage"] = {
        "input": response.usage.input_tokens,
        "output": response.usage.output_tokens,
    }
    judge_path.write_text(json.dumps(judge_result, indent=2))

    sr = judge_result.get("summary", {}).get("success_rate", "?")
    print(f"success_rate={sr}")
    return judge_result


def main():
    tasks = load_tasks("bam")
    task = next(t for t in tasks if t["task_id"] == "bam_T1")

    results = {}
    for cond in ["ara", "baseline"]:
        try:
            results[cond] = judge_run("bam", task, cond, 0)
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()
            results[cond] = {"error": str(e)}

    # Print comparison
    print("\n" + "="*60)
    print("COMPARISON: ARA vs Baseline on bam_T1")
    print("="*60)
    for cond in ["ara", "baseline"]:
        r = results[cond]
        if "error" in r:
            print(f"\n{cond.upper()}: ERROR - {r['error']}")
            continue
        summary = r.get("summary", {})
        print(f"\n{cond.upper()}:")
        print(f"  Success rate: {summary.get('success_rate', '?')}")
        print(f"  Yes/Partial/No: {summary.get('yes', '?')}/{summary.get('partial', '?')}/{summary.get('no', '?')}")
        verdicts = r.get("verdicts", [])
        for v in verdicts:
            print(f"    [{v.get('verdict', '?'):7s}] {v.get('requirement_id', '?')}: {v.get('explanation', '')[:80]}")

if __name__ == "__main__":
    main()
