"""Master script for Understanding evaluation question generation.

Runs all three question categories across all papers:
- Category A: 10 lossless questions per paper (all 31)
- Category B: 5 detail-recovery questions (23 PaperBench papers)
- Category C: 5 failure-knowledge questions (8 RE-Bench + Speedrun)

Uses ThreadPoolExecutor for parallel API calls within each category.
"""

import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add code/ to path so eval.* imports work
_code_dir = str(Path(__file__).resolve().parent.parent)
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

from eval.generate_catA_dual import generate_catA_dual
from eval.generate_catB_questions import generate_catB_questions
from eval.generate_catC_questions import generate_catC_questions

# ROOT = project root (parent of code/), so registry paths like "code/artifacts/..." resolve correctly
ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT / "code" / "eval" / "paper_registry.json"
OUTPUT_DIR = str(ROOT / "code" / "eval" / "questions")
MAX_WORKERS = 5  # Parallel API calls


def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def run_category_a(registry: dict, skip_existing: bool = True):
    """Generate Category A questions using dual-source (PDF + ARA) generation."""
    papers = registry["papers"]
    tasks = []

    for p in papers:
        pid = p["paper_id"]
        out_file = Path(OUTPUT_DIR) / f"{pid}_catA.json"
        if skip_existing and out_file.exists():
            print(f"[catA] SKIP {pid} (already exists)")
            continue

        artifact_dir = str(ROOT / p["artifact_dir"])

        if p["benchmark"] == "paperbench":
            pdf_path = str(ROOT / p["pdf_path"])
            if not os.path.isfile(pdf_path):
                print(f"[catA] SKIP {pid} (no PDF)")
                continue
            tasks.append((pid, pdf_path, artifact_dir, None))
        else:
            # RE-Bench / Speedrun: baseline_dir is the task description
            baseline_dir = str(ROOT / p.get("baseline_dir", p["artifact_dir"]))
            tasks.append((pid, None, artifact_dir, baseline_dir))

    print(f"\n[catA] Generating dual-source Category A questions for {len(tasks)} papers...")
    results = {"success": 0, "failed": 0}

    def _gen(task_info):
        pid, pdf_path, artifact_dir, baseline_dir = task_info
        try:
            r = generate_catA_dual(
                paper_id=pid,
                pdf_path=pdf_path,
                artifact_dir=artifact_dir,
                output_dir=OUTPUT_DIR,
                baseline_dir=baseline_dir,
            )
            return pid, r.get("questions") is not None
        except Exception as e:
            print(f"[catA] ERROR {pid}: {e}")
            traceback.print_exc()
            return pid, False

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_gen, t): t for t in tasks}
        for future in as_completed(futures):
            pid, success = future.result()
            if success:
                results["success"] += 1
                print(f"[catA] OK: {pid}")
            else:
                results["failed"] += 1
                print(f"[catA] FAIL: {pid}")

    print(f"[catA] Done: {results['success']} OK, {results['failed']} failed")
    return results


def run_category_b(registry: dict, skip_existing: bool = True):
    """Generate Category B questions for PaperBench papers."""
    papers = [p for p in registry["papers"] if p["benchmark"] == "paperbench"]
    tasks = []

    for p in papers:
        pid = p["paper_id"]
        out_file = Path(OUTPUT_DIR) / f"{pid}_catB.json"
        if skip_existing and out_file.exists():
            print(f"[catB] SKIP {pid} (already exists)")
            continue

        rubric_path = str(ROOT / p["rubric_path"])
        info_gap_path = str(ROOT / p["info_gap_path"])
        if not os.path.isfile(info_gap_path):
            print(f"[catB] SKIP {pid} (no info gap results)")
            continue
        tasks.append((pid, rubric_path, info_gap_path))

    print(f"\n[catB] Generating Category B questions for {len(tasks)} papers...")
    results = {"success": 0, "failed": 0}

    def _gen(task_info):
        pid, rubric, info_gap = task_info
        try:
            r = generate_catB_questions(pid, rubric, info_gap, OUTPUT_DIR)
            return pid, r["questions"] is not None
        except Exception as e:
            print(f"[catB] ERROR {pid}: {e}")
            traceback.print_exc()
            return pid, False

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_gen, t): t for t in tasks}
        for future in as_completed(futures):
            pid, success = future.result()
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

    print(f"[catB] Done: {results['success']} OK, {results['failed']} failed")
    return results


def run_category_c(registry: dict, skip_existing: bool = True):
    """Generate Category C questions for RE-Bench + Speedrun tasks."""
    papers = [p for p in registry["papers"]
              if p["benchmark"] in ("rebench", "speedrun")]
    tasks = []

    for p in papers:
        pid = p["paper_id"]
        out_file = Path(OUTPUT_DIR) / f"{pid}_catC.json"
        if skip_existing and out_file.exists():
            print(f"[catC] SKIP {pid} (already exists)")
            continue

        artifact_dir = str(ROOT / p["artifact_dir"])
        baseline_dir = str(ROOT / p.get("baseline_dir", p["artifact_dir"]))
        tasks.append((pid, artifact_dir, baseline_dir))

    print(f"\n[catC] Generating Category C questions for {len(tasks)} tasks...")
    results = {"success": 0, "failed": 0}

    def _gen(task_info):
        pid, artifact, baseline = task_info
        try:
            r = generate_catC_questions(pid, artifact, baseline, OUTPUT_DIR)
            return pid, r["questions"] is not None
        except Exception as e:
            print(f"[catC] ERROR {pid}: {e}")
            traceback.print_exc()
            return pid, False

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_gen, t): t for t in tasks}
        for future in as_completed(futures):
            pid, success = future.result()
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

    print(f"[catC] Done: {results['success']} OK, {results['failed']} failed")
    return results


def main():
    registry = load_registry()
    print(f"Paper registry: {registry['total']} papers")

    skip = "--no-skip" not in sys.argv

    t0 = time.time()

    # Run all categories
    cat_filter = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("A", "B", "C") else None

    if cat_filter is None or cat_filter == "A":
        a_results = run_category_a(registry, skip_existing=skip)
    if cat_filter is None or cat_filter == "B":
        b_results = run_category_b(registry, skip_existing=skip)
    if cat_filter is None or cat_filter == "C":
        c_results = run_category_c(registry, skip_existing=skip)

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"Question generation complete in {elapsed:.0f}s")

    # Count total questions generated
    q_dir = Path(OUTPUT_DIR)
    total_q = 0
    for f in q_dir.glob("*_cat*.json"):
        try:
            data = json.loads(f.read_text())
            total_q += data.get("n_questions", 0)
        except Exception:
            pass
    print(f"Total question files: {len(list(q_dir.glob('*_cat*.json')))}")
    print(f"Total questions: {total_q}")


if __name__ == "__main__":
    main()
