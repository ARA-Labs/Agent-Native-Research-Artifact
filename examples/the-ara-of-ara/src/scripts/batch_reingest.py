#!/usr/bin/env python3
"""Batch re-ingest PaperBench papers with rubric supplementation.

Regenerates ARAs for all 23 PaperBench papers using PDF + rubric as input.
Backs up existing ARAs before overwriting.

Usage:
    python scripts/batch_reingest.py                  # All 23 papers
    python scripts/batch_reingest.py adaptive-pruning  # Single paper
    python scripts/batch_reingest.py --dry-run          # Preview only
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))
load_dotenv(CODE_DIR / ".env")

REGISTRY_PATH = CODE_DIR / "eval" / "paper_registry.json"
ARTIFACTS_DIR = CODE_DIR / "artifacts"
PDFS_DIR = CODE_DIR / "pdfs"
RUBRICS_DIR = CODE_DIR / "eval" / "rubrics"
REPOS_DIR = CODE_DIR / "repos"
BACKUP_DIR = CODE_DIR / "artifacts" / "_backup_pre_rubric"

MAX_WORKERS = 3  # Conservative to avoid API rate limits


def load_paperbench_papers():
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    return [p for p in registry["papers"] if p["benchmark"] == "paperbench"]


def ingest_one(paper_id: str, dry_run: bool = False) -> tuple[str, bool, str]:
    """Ingest a single PaperBench paper with rubric + optional repo."""
    pdf_path = PDFS_DIR / f"{paper_id}.pdf"
    rubric_path = RUBRICS_DIR / f"{paper_id}.json"
    repo_path = REPOS_DIR / paper_id
    ara_dir = ARTIFACTS_DIR / paper_id

    if not pdf_path.exists():
        return paper_id, False, f"PDF not found: {pdf_path}"
    if not rubric_path.exists():
        return paper_id, False, f"Rubric not found: {rubric_path}"

    has_repo = repo_path.is_dir() and any(repo_path.iterdir())
    sources = f"PDF + rubric" + (f" + repo" if has_repo else "")

    if dry_run:
        return paper_id, True, f"Would ingest: {sources}"

    # Backup existing ARA
    if ara_dir.exists():
        backup = BACKUP_DIR / paper_id
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(ara_dir, backup)
        shutil.rmtree(ara_dir)

    try:
        from ingestor.ingestor import ingest

        ara_dir, paper_text, usage, report = ingest(
            pdf_path=str(pdf_path),
            paper_id=paper_id,
            output_dir=str(ARTIFACTS_DIR),
            rubric_path=str(rubric_path),
            repo_path=str(repo_path) if has_repo else None,
        )

        # Save usage
        usage_path = ara_dir / "_token_usage.json"
        usage["model"] = "claude-sonnet-4-6"
        usage["rubric_supplemented"] = True
        usage["repo_linked"] = has_repo
        usage_path.write_text(json.dumps(usage, indent=2) + "\n")

        passed = report.level_1.passed if report.level_1 else False
        return paper_id, True, f"OK (L1={'PASS' if passed else 'FAIL'}, turns={usage['turns']}, {sources})"

    except Exception as e:
        return paper_id, False, f"ERROR: {e}"


def main():
    parser = argparse.ArgumentParser(description="Batch re-ingest PaperBench with rubrics")
    parser.add_argument("paper_ids", nargs="*", help="Specific paper IDs (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Parallel workers")
    args = parser.parse_args()

    papers = load_paperbench_papers()

    if args.paper_ids:
        paper_ids = set(args.paper_ids)
        papers = [p for p in papers if p["paper_id"] in paper_ids]
        if not papers:
            print(f"No matching papers found for: {args.paper_ids}")
            sys.exit(1)

    print(f"{'=' * 60}")
    print(f"Batch Re-Ingestion: {len(papers)} PaperBench papers")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Workers: {args.workers}")
    print(f"{'=' * 60}\n")

    t0 = time.time()
    results = {"ok": [], "fail": []}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(ingest_one, p["paper_id"], args.dry_run): p["paper_id"]
            for p in papers
        }
        for future in as_completed(futures):
            pid, ok, msg = future.result()
            status = "OK" if ok else "FAIL"
            print(f"[{status}] {pid}: {msg}")
            if ok:
                results["ok"].append(pid)
            else:
                results["fail"].append(pid)

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"Done in {elapsed:.0f}s: {len(results['ok'])} OK, {len(results['fail'])} FAIL")
    if results["fail"]:
        print(f"Failed: {', '.join(results['fail'])}")


if __name__ == "__main__":
    main()
