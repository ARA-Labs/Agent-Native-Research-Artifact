"""Synthetic error injection for ARA Seal Level 2 evaluation.

Injects 5 categories of known errors into each ARA and records per-error
ground-truth manifests. Output goes to code/artifacts_injected/{paper}/.

Error types:
  1. fabricated_claim        - new claim cites a non-existent experiment
  2. missing_falsification   - remove `Falsification criteria` from a claim
  3. orphan_experiment       - new experiment not referenced by any claim
  4. over_claim              - broaden Statement, leave falsification untouched
  5. rebutted_branch_leak    - new claim advocates an explored-and-rejected branch
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = REPO_ROOT / "code" / "artifacts"
OUTPUT_DIR = REPO_ROOT / "code" / "artifacts_injected"


@dataclass
class Injection:
    error_id: str
    type: str
    target_file: str
    target_entity: str | None
    ground_truth_signal: str
    content_added: str | None = None
    content_removed: str | None = None
    line_hint: str | None = None


# ---------- Parsing helpers ----------

CLAIM_HEADER_RE = re.compile(r"^## (C\d+):\s*(.+)$", re.M)
EXP_HEADER_RE = re.compile(r"^## (E\d+):\s*(.+)$", re.M)


def parse_sections(text: str, header_re: re.Pattern[str]) -> list[tuple[str, str, int, int]]:
    """Return list of (id, title, start, end) for each section header match."""
    matches = list(header_re.finditer(text))
    result = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result.append((m.group(1), m.group(2).strip(), start, end))
    return result


def next_id(ids: list[str], prefix: str) -> str:
    nums = [int(x[len(prefix):]) for x in ids if x.startswith(prefix)]
    return f"{prefix}{(max(nums) + 1) if nums else 1:02d}"


def fake_id(ids: list[str], prefix: str) -> str:
    """Return an id guaranteed not to exist."""
    nums = [int(x[len(prefix):]) for x in ids if x.startswith(prefix)]
    base = (max(nums) if nums else 0) + 50
    return f"{prefix}{base:02d}"


# ---------- Injection implementations ----------

def inject_fabricated_claim(adir: Path, rng: random.Random, paper: str) -> Injection:
    claims_path = adir / "logic" / "claims.md"
    exp_path = adir / "logic" / "experiments.md"
    claims_text = claims_path.read_text()
    exp_text = exp_path.read_text() if exp_path.exists() else ""

    claim_ids = [s[0] for s in parse_sections(claims_text, CLAIM_HEADER_RE)]
    exp_ids = [s[0] for s in parse_sections(exp_text, EXP_HEADER_RE)]

    new_c = next_id(claim_ids, "C")
    phantom_e = fake_id(exp_ids, "E")

    block = (
        f"\n## {new_c}: Method Generalizes to All Unseen Tasks Within 1% of In-Distribution Performance\n"
        f"- **Statement**: The proposed method generalizes to arbitrary unseen tasks with average performance within 1% of in-distribution performance, with no task-specific tuning.\n"
        f"- **Status**: supported\n"
        f"- **Falsification criteria**: Average unseen-task performance drops by more than 5% relative to in-distribution performance.\n"
        f"- **Proof**: [{phantom_e}]\n"
        f"- **Dependencies**: none\n"
        f"- **Tags**: generalization, unseen tasks\n"
    )
    new_text = claims_text.rstrip() + "\n" + block
    claims_path.write_text(new_text)

    return Injection(
        error_id=f"{paper.upper()}-FAB-01",
        type="fabricated_claim",
        target_file="logic/claims.md",
        target_entity=new_c,
        ground_truth_signal=(
            f"Claim {new_c} cites experiment {phantom_e}, which does not exist in experiments.md. "
            f"The claim content itself is not grounded in any actual experiment in this artifact."
        ),
        content_added=block,
        line_hint=f"appended at end of claims.md",
    )


def inject_missing_falsification(adir: Path, rng: random.Random, paper: str) -> Injection:
    claims_path = adir / "logic" / "claims.md"
    text = claims_path.read_text()
    sections = parse_sections(text, CLAIM_HEADER_RE)
    if not sections:
        raise RuntimeError(f"{paper}: no claims found")

    # Pick a claim that actually has a falsification criteria line
    candidates = [s for s in sections if "**Falsification criteria**" in text[s[2]:s[3]]]
    if not candidates:
        raise RuntimeError(f"{paper}: no claim has falsification criteria to remove")
    target = rng.choice(candidates)
    cid, _, start, end = target
    block = text[start:end]

    # Remove the falsification line (until next newline)
    pattern = re.compile(r"^- \*\*Falsification criteria\*\*:.*(?:\n(?!- ).*)*\n?", re.M)
    m = pattern.search(block)
    if not m:
        raise RuntimeError(f"{paper}/{cid}: falsification line not matched")
    removed = m.group(0)
    new_block = block[:m.start()] + block[m.end():]
    new_text = text[:start] + new_block + text[end:]
    claims_path.write_text(new_text)

    return Injection(
        error_id=f"{paper.upper()}-MFC-01",
        type="missing_falsification",
        target_file="logic/claims.md",
        target_entity=cid,
        ground_truth_signal=(
            f"Claim {cid} is missing the required `Falsification criteria` field "
            f"(schema requires all of Statement/Status/Falsification criteria/Proof)."
        ),
        content_removed=removed.rstrip(),
        line_hint=f"inside {cid}",
    )


def inject_orphan_experiment(adir: Path, rng: random.Random, paper: str) -> Injection:
    exp_path = adir / "logic" / "experiments.md"
    if not exp_path.exists():
        raise RuntimeError(f"{paper}: experiments.md missing")
    exp_text = exp_path.read_text()
    exp_ids = [s[0] for s in parse_sections(exp_text, EXP_HEADER_RE)]
    new_e = next_id(exp_ids, "E")
    phantom_c = "C99"  # not referenced by real claims and not verified by design

    block = (
        f"\n## {new_e}: Auxiliary Probing — Hidden-State Norm Stability\n"
        f"- **Verifies**: {phantom_c}\n"
        f"- **Setup**:\n"
        f"  - Model: same as main experiments\n"
        f"  - Hardware: Single A100 GPU\n"
        f"  - Dataset: same as main experiments\n"
        f"  - System: probe hidden-state L2 norms across layers during training\n"
        f"- **Procedure**:\n"
        f"  1. Instrument hidden-state norms at each transformer layer.\n"
        f"  2. Log per-step norm statistics for 5000 steps.\n"
        f"  3. Compare norm drift across method and baselines.\n"
        f"- **Metrics**: layer-wise hidden-state L2 norm mean and std over training.\n"
        f"- **Expected outcome**:\n"
        f"  - Norms remain bounded throughout training\n"
        f"- **Baselines**: none\n"
        f"- **Dependencies**: none\n"
    )
    new_text = exp_text.rstrip() + "\n" + block
    exp_path.write_text(new_text)

    return Injection(
        error_id=f"{paper.upper()}-ORPH-01",
        type="orphan_experiment",
        target_file="logic/experiments.md",
        target_entity=new_e,
        ground_truth_signal=(
            f"Experiment {new_e} is declared in experiments.md but is not referenced "
            f"by any claim in claims.md (its `Verifies:` field points to {phantom_c} which does not exist). "
            f"This is orphan evidence."
        ),
        content_added=block,
        line_hint=f"appended at end of experiments.md",
    )


def inject_over_claim(adir: Path, rng: random.Random, paper: str) -> Injection:
    claims_path = adir / "logic" / "claims.md"
    text = claims_path.read_text()
    sections = parse_sections(text, CLAIM_HEADER_RE)
    if not sections:
        raise RuntimeError(f"{paper}: no claims")

    # Pick a claim whose Statement mentions concrete scope (numbers / dataset / model names)
    scope_markers = re.compile(r"\b(\d+%|\d+\.\d+|RoBERTa|T5|LLaMA|MNLI|SST2|CNN/DM|GLUE|ImageNet|CIFAR|COCO|SQuAD|ARC|MMLU|HellaSwag|TruthfulQA|Alpaca|Mistral|GPT|BERT|ResNet|ViT)\b")
    candidates = []
    for s in sections:
        cid, _, start, end = s
        block = text[start:end]
        m = re.search(r"^- \*\*Statement\*\*:\s*(.+)$", block, re.M)
        if not m:
            continue
        if scope_markers.search(m.group(1)):
            candidates.append((s, m))
    if not candidates:
        # Fall back: any claim with a Statement line
        for s in sections:
            block = text[s[2]:s[3]]
            m = re.search(r"^- \*\*Statement\*\*:\s*(.+)$", block, re.M)
            if m:
                candidates.append((s, m))
    if not candidates:
        raise RuntimeError(f"{paper}: no statement to overbroaden")

    (cid, title, start, end), stmt_match = rng.choice(candidates)
    original_stmt = stmt_match.group(0)
    # Replace with a universally stronger, scope-stripped version
    broadened = (
        "- **Statement**: The proposed method achieves state-of-the-art results across all models, "
        "datasets, and sparsity or capacity regimes, without requiring method-specific tuning."
    )
    block = text[start:end]
    new_block = block.replace(original_stmt, broadened, 1)
    new_text = text[:start] + new_block + text[end:]
    claims_path.write_text(new_text)

    return Injection(
        error_id=f"{paper.upper()}-OVC-01",
        type="over_claim",
        target_file="logic/claims.md",
        target_entity=cid,
        ground_truth_signal=(
            f"Claim {cid} Statement was broadened to universal scope ('all models, all datasets, "
            f"all regimes') while the Falsification criteria still reference the original narrow scope. "
            f"The claim now over-reaches beyond what the cited evidence can support."
        ),
        content_removed=original_stmt,
        content_added=broadened,
        line_hint=f"Statement line of {cid}",
    )


def inject_rebutted_branch_leak(adir: Path, rng: random.Random, paper: str) -> Injection:
    tree_path = adir / "trace" / "exploration_tree.yaml"
    claims_path = adir / "logic" / "claims.md"
    if not tree_path.exists():
        raise RuntimeError(f"{paper}: exploration_tree.yaml missing")

    tree_text = tree_path.read_text()
    # Find dead_end / rejected nodes
    node_blocks = re.findall(
        r"- id:\s*(N[\w\-]+)\s*\n\s*type:\s*(dead_end|pivot)\s*\n\s*title:\s*\"([^\"]+)\"",
        tree_text,
    )
    if not node_blocks:
        # try without quotes
        node_blocks = re.findall(
            r"- id:\s*(N[\w\-]+)\s*\n\s*type:\s*(dead_end|pivot)\s*\n\s*title:\s*(.+)",
            tree_text,
        )
    if not node_blocks:
        raise RuntimeError(f"{paper}: no dead_end/pivot nodes found in exploration_tree")

    nid, ntype, ntitle = rng.choice(node_blocks)
    ntitle = ntitle.strip().strip('"').strip()

    claims_text = claims_path.read_text()
    claim_ids = [s[0] for s in parse_sections(claims_text, CLAIM_HEADER_RE)]
    exp_ids_text = (adir / "logic" / "experiments.md").read_text() if (adir / "logic" / "experiments.md").exists() else ""
    exp_ids = [s[0] for s in parse_sections(exp_ids_text, EXP_HEADER_RE)]
    new_c = next_id(claim_ids, "C")
    # Reuse a real experiment id so this looks locally plausible
    anchor_e = rng.choice(exp_ids) if exp_ids else "E01"

    block = (
        f"\n## {new_c}: Adopting the Approach Described in {nid} Yields Strong Results\n"
        f"- **Statement**: The approach \"{ntitle}\" is adopted as the final design and yields the reported performance improvements.\n"
        f"- **Status**: supported\n"
        f"- **Falsification criteria**: Adopting this approach does not produce the reported gains on the main benchmarks.\n"
        f"- **Proof**: [{anchor_e}]\n"
        f"- **Dependencies**: none\n"
        f"- **Tags**: design choice, main approach\n"
    )
    new_text = claims_text.rstrip() + "\n" + block
    claims_path.write_text(new_text)

    return Injection(
        error_id=f"{paper.upper()}-RBL-01",
        type="rebutted_branch_leak",
        target_file="logic/claims.md",
        target_entity=new_c,
        ground_truth_signal=(
            f"Claim {new_c} advocates the approach in exploration-tree node {nid} ('{ntitle}'), "
            f"but {nid} is marked `{ntype}` in trace/exploration_tree.yaml, meaning the authors "
            f"explored and rejected this branch. The claim contradicts the exploration record."
        ),
        content_added=block,
        line_hint=f"appended at end of claims.md; rebutted node={nid} ({ntype})",
    )


INJECTORS = [
    ("fabricated_claim", inject_fabricated_claim),
    ("missing_falsification", inject_missing_falsification),
    ("orphan_experiment", inject_orphan_experiment),
    ("over_claim", inject_over_claim),
    ("rebutted_branch_leak", inject_rebutted_branch_leak),
]


# ---------- Orchestration ----------

def is_paperbench_artifact(adir: Path) -> bool:
    return (adir / "rubric").is_dir() and (adir / "logic" / "claims.md").exists()


def seeded_rng(paper: str) -> random.Random:
    h = hashlib.sha256(paper.encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def inject_artifact(src: Path, dst: Path) -> dict:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    paper = src.name
    rng = seeded_rng(paper)

    injections: list[Injection] = []
    errors: list[dict] = []
    used_entities: set[str] = set()
    for name, fn in INJECTORS:
        # Retry up to a few times to avoid colliding on the same claim/entity
        # across injections that pick from existing entities.
        inj = None
        last_exc: Exception | None = None
        for _ in range(6):
            snapshot_claims = (dst / "logic" / "claims.md").read_text() if (dst / "logic" / "claims.md").exists() else None
            snapshot_exps = (dst / "logic" / "experiments.md").read_text() if (dst / "logic" / "experiments.md").exists() else None
            try:
                candidate = fn(dst, rng, paper)
            except Exception as exc:
                last_exc = exc
                break
            if candidate.target_entity and candidate.target_entity in used_entities:
                if snapshot_claims is not None:
                    (dst / "logic" / "claims.md").write_text(snapshot_claims)
                if snapshot_exps is not None:
                    (dst / "logic" / "experiments.md").write_text(snapshot_exps)
                continue
            inj = candidate
            break
        if inj is None:
            errors.append({"type": name, "error": str(last_exc) if last_exc else "could not avoid entity collision"})
            continue
        if inj.target_entity:
            used_entities.add(inj.target_entity)
        injections.append(inj)

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return str(p)

    manifest = {
        "paper": paper,
        "source_artifact": _rel(src),
        "injected_artifact": _rel(dst),
        "seed_basis": paper,
        "num_injections": len(injections),
        "injections": [asdict(i) for i in injections],
        "errors": errors,
    }
    (dst / "injection_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="only inject these paper names")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    targets: list[Path] = []
    for adir in sorted(ARTIFACTS_DIR.iterdir()):
        if not adir.is_dir() or adir.name.startswith("_"):
            continue
        if args.only and adir.name not in args.only:
            continue
        if not is_paperbench_artifact(adir):
            continue
        targets.append(adir)

    print(f"Injecting into {len(targets)} PaperBench artifact(s) -> {args.output}")
    summary = {"artifacts": [], "total_injections": 0, "total_errors": 0}
    for src in targets:
        dst = args.output / src.name
        m = inject_artifact(src, dst)
        summary["artifacts"].append({
            "paper": m["paper"],
            "num_injections": m["num_injections"],
            "errors": m["errors"],
        })
        summary["total_injections"] += m["num_injections"]
        summary["total_errors"] += len(m["errors"])
        print(f"  {src.name:<42} injections={m['num_injections']} errors={len(m['errors'])}")

    (args.output / "_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nTotal injections: {summary['total_injections']}")
    print(f"Total errors:     {summary['total_errors']}")
    print(f"Summary: {args.output / '_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
