#!/usr/bin/env python3
"""CLI: Generate Level 2 (Information Fidelity) questions from a paper's PDF.

Generates 10 understanding questions spanning 6 categories and 4 difficulty
tiers, using the PDF as source to avoid format bias.

Usage:
    python run_question_gen.py --paper-id andes
    python run_question_gen.py --paper-id andes --model claude-sonnet-4-6
    python run_question_gen.py --paper-id 2312.08298 --pdf-dir pdfs

Outputs:
    code/eval/questions/{paper_id}.json  — 10 L2 understanding questions
"""

import argparse
import json
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

from eval.generate_questions import generate_questions


def main():
    parser = argparse.ArgumentParser(
        description="Generate L2 understanding questions from a paper PDF"
    )
    parser.add_argument(
        "--paper-id", required=True,
        help="Paper identifier (e.g., andes, 2312.08298)"
    )
    parser.add_argument(
        "--pdf-dir", default=None,
        help="Directory containing PDFs (default: code/pdfs)"
    )
    parser.add_argument(
        "--pdf-path", default=None,
        help="Explicit path to PDF (overrides --pdf-dir)"
    )
    parser.add_argument(
        "--artifact-dir", default=None,
        help="ARA artifact dir for title extraction (default: code/artifacts/{paper_id})"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory (default: code/eval/questions)"
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-6",
        help="Model for question generation (default: claude-sonnet-4-6)"
    )
    args = parser.parse_args()

    # Resolve PDF path
    if args.pdf_path:
        pdf_path = Path(args.pdf_path)
    else:
        pdf_dir = Path(args.pdf_dir) if args.pdf_dir else CODE_DIR / "pdfs"
        pdf_path = pdf_dir / f"{args.paper_id}.pdf"
        if not pdf_path.exists():
            # Try common alternatives
            for alt in pdf_dir.glob(f"{args.paper_id}*"):
                if alt.suffix == ".pdf":
                    pdf_path = alt
                    break

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        print(f"  Available PDFs in {pdf_path.parent}:")
        for f in sorted(pdf_path.parent.glob("*.pdf")):
            print(f"    {f.name}")
        sys.exit(1)

    # Resolve artifact dir (optional, for title)
    artifact_dir = args.artifact_dir
    if artifact_dir is None:
        candidate = CODE_DIR / "artifacts" / args.paper_id
        if candidate.exists():
            artifact_dir = str(candidate)

    # Resolve output dir
    output_dir = args.output_dir or str(CODE_DIR / "eval" / "questions")

    result = generate_questions(
        pdf_path=str(pdf_path),
        paper_id=args.paper_id,
        output_dir=output_dir,
        model=args.model,
        artifact_dir=artifact_dir,
    )

    if result["questions"] is None:
        print("\nERROR: Question generation failed.")
        sys.exit(1)

    # Print summary
    data = result["questions"]
    questions = data["questions"]
    print(f"\n{'─' * 60}")
    print(f"Paper: {data['paper_title']}")
    print(f"Level: {data['eval_level']}")
    print(f"Questions: {data['n_questions']}")
    print(f"Categories: {data['category_distribution']}")
    print(f"Tiers: {data['tier_distribution']}")
    print(f"{'─' * 60}")

    for q in questions:
        print(f"\n  {q['id']} [{q['category']}] [{q['difficulty']}] "
              f"[{q['grading_type']}]")
        print(f"  Q: {q['question'][:120]}{'...' if len(q['question']) > 120 else ''}")
        gold = q.get('gold_answer', '')
        print(f"  A: {gold[:120]}{'...' if len(gold) > 120 else ''}")

    print(f"\nOutput: {result['output_path']}")


if __name__ == "__main__":
    main()
