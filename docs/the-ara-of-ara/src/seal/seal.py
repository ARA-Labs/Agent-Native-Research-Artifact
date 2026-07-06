"""ARA Seal Validator: Level 1 (Structural Integrity), Level 2 (Information Fidelity), Level 3 (Execution)."""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict


@dataclass
class Check:
    check: str
    passed: bool
    message: str = ""


@dataclass
class LevelResult:
    level: str
    passed: bool
    checks: list[Check] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.checks:
            return 0.0
        return sum(1 for c in self.checks if c.passed) / len(self.checks)


@dataclass
class SealReport:
    artifact_id: str
    artifact_path: str
    level_1: LevelResult | None = None
    level_2: LevelResult | None = None
    level_3: LevelResult | None = None
    test_cases: list | None = None
    feedback_for_ingestor: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @property
    def summary(self) -> str:
        lines = [f"=== ARA Seal Report: {self.artifact_id} ==="]
        for level, label in [
            (self.level_1, "Structural Integrity"),
            (self.level_2, "Information Fidelity"),
            (self.level_3, "Execution Reproducibility"),
        ]:
            if not level:
                continue
            n_pass = sum(c.passed for c in level.checks)
            n_total = len(level.checks)
            lines.append(
                f"Level {level.level} ({label}): "
                f"{'PASS' if level.passed else 'FAIL'} "
                f"({level.pass_rate:.0%}, {n_pass}/{n_total} checks)"
            )
            for c in level.checks:
                if not c.passed:
                    lines.append(f"  FAIL: {c.check} — {c.message}")
        if self.test_cases:
            lines.append(f"Test cases: {len(self.test_cases)} generated")
        if self.feedback_for_ingestor:
            lines.append(f"\nFeedback for Ingestor:\n{self.feedback_for_ingestor}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Level 1: Structural Validation
# ---------------------------------------------------------------------------

MANDATORY_DIRS = ["logic", "logic/solution", "src", "src/configs", "trace", "evidence"]
MANDATORY_FILES = [
    "PAPER.md",
    "logic/problem.md",
    "logic/claims.md",
    "logic/concepts.md",
    "logic/experiments.md",
    "logic/solution/architecture.md",
    "logic/solution/algorithm.md",
    "logic/solution/constraints.md",
    "logic/solution/heuristics.md",
    "logic/related_work.md",
    "src/configs/training.md",
    "src/configs/model.md",
    "src/environment.md",
    "trace/exploration_tree.yaml",
    "evidence/README.md",
]

# Required fields per structured file (field name patterns to search for)
REQUIRED_FIELDS = {
    "logic/claims.md": {
        "claim_block": r"##\s+C\d+",
        "Statement": r"\*\*Statement\*\*",
        "Status": r"\*\*Status\*\*",
        "Falsification criteria": r"\*\*Falsification criteria\*\*",
        "Proof": r"\*\*Proof\*\*",
    },
    "logic/concepts.md": {
        "concept_block": r"##\s+.+",  # at least one concept section
        "Definition": r"\*\*Definition\*\*",
    },
    "logic/problem.md": {
        "observation_block": r"###\s+O\d+",
        "gap_block": r"###\s+G\d+",
        "Key Insight": r"(##\s+Key Insight|\*\*Insight\*\*)",
    },
    "logic/experiments.md": {
        "experiment_block": r"##\s+E\d+",
        "Verifies": r"\*\*Verifies\*\*",
        "Setup": r"\*\*Setup\*\*",
        "Procedure": r"\*\*Procedure\*\*",
        "Expected outcome": r"\*\*Expected (results|outcome)\*\*",
    },
    "logic/solution/heuristics.md": {
        "heuristic_block": r"##\s+H\d+",
        "Rationale": r"\*\*Rationale\*\*",
        "Sensitivity": r"\*\*Sensitivity\*\*",
        "Bounds": r"\*\*Bounds\*\*",
    },
    "logic/related_work.md": {
        "rw_block": r"##\s+RW\d+",
        "Type": r"\*\*Type\*\*",
        "Delta": r"\*\*Delta\*\*",
    },
    # trace/exploration_tree.yaml is validated separately via YAML parsing
}


def _check_yaml_frontmatter(paper_md_path: Path) -> Check:
    """Check that PAPER.md has valid YAML frontmatter."""
    text = paper_md_path.read_text()
    if not text.startswith("---"):
        return Check("yaml_frontmatter", False, "PAPER.md does not start with YAML frontmatter (---)")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return Check("yaml_frontmatter", False, "PAPER.md has unclosed YAML frontmatter")
    try:
        import yaml
        meta = yaml.safe_load(parts[1])
        if not isinstance(meta, dict):
            return Check("yaml_frontmatter", False, "YAML frontmatter is not a mapping")
        required_keys = ["title", "authors", "year"]
        missing = [k for k in required_keys if k not in meta]
        if missing:
            return Check("yaml_frontmatter", False, f"YAML frontmatter missing keys: {missing}")
    except Exception as e:
        return Check("yaml_frontmatter", False, f"YAML parse error: {e}")
    return Check("yaml_frontmatter", True)


def _check_concepts_count(concepts_path: Path) -> Check:
    """Check that concepts.md has at least 5 concept entries."""
    content = concepts_path.read_text()
    count = len(re.findall(r"^##\s+", content, re.MULTILINE))
    ok = count >= 5
    return Check(
        "concepts_count",
        ok,
        "" if ok else f"Need >= 5 concepts in concepts.md, found {count}"
    )


def _check_experiments_count(experiments_path: Path) -> Check:
    """Check that experiments.md has at least 3 experiment plans."""
    content = experiments_path.read_text()
    count = len(re.findall(r"^##\s+E\d+", content, re.MULTILINE))
    ok = count >= 3
    return Check(
        "experiments_count",
        ok,
        "" if ok else f"Need >= 3 experiments in experiments.md, found {count}"
    )


def _collect_yaml_tree_nodes(nodes: list[dict]) -> list[dict]:
    """Recursively collect all nodes from the nested YAML tree."""
    collected = []
    for node in nodes:
        collected.append(node)
        if "children" in node and isinstance(node["children"], list):
            collected.extend(_collect_yaml_tree_nodes(node["children"]))
    return collected


def _check_exploration_tree_structure(tree_path: Path) -> list[Check]:
    """Validate the exploration tree YAML DAG structure."""
    import yaml

    checks = []
    content = tree_path.read_text()

    try:
        data = yaml.safe_load(content)
    except Exception as e:
        checks.append(Check("tree_yaml_parse", False, f"YAML parse error: {e}"))
        return checks

    if not isinstance(data, dict) or "tree" not in data:
        checks.append(Check("tree_has_root", False, "exploration_tree.yaml missing top-level 'tree' key"))
        return checks

    checks.append(Check("tree_yaml_parse", True))

    # Collect all nodes recursively
    all_nodes = _collect_yaml_tree_nodes(data["tree"])
    node_ids = {n.get("id") for n in all_nodes if n.get("id")}

    # Check minimum node count
    ok = len(node_ids) >= 8
    checks.append(Check(
        "tree_node_count",
        ok,
        "" if ok else f"Need >= 8 nodes in exploration_tree.yaml, found {len(node_ids)}"
    ))

    # Check node types
    valid_types = {"question", "decision", "experiment", "dead_end", "pivot"}
    type_counts = {}
    for node in all_nodes:
        ntype = node.get("type", "")
        type_counts[ntype] = type_counts.get(ntype, 0) + 1
        if ntype not in valid_types:
            checks.append(Check(
                f"tree_valid_type:{node.get('id', '?')}",
                False,
                f"Node {node.get('id', '?')} has invalid type '{ntype}'"
            ))

    # Check that at least one dead_end exists
    has_dead_end = type_counts.get("dead_end", 0) > 0
    checks.append(Check(
        "tree_has_dead_end",
        has_dead_end,
        "" if has_dead_end else "Exploration tree has no dead_end nodes"
    ))

    # Check that at least one decision exists
    has_decision = type_counts.get("decision", 0) > 0
    checks.append(Check(
        "tree_has_decision",
        has_decision,
        "" if has_decision else "Exploration tree has no decision nodes"
    ))

    # Check required fields per type
    type_required_fields = {
        "question": ["description"],
        "experiment": ["result"],
        "dead_end": ["hypothesis", "failure_mode", "lesson"],
        "decision": ["choice", "alternatives"],
        "pivot": ["from", "to", "trigger"],
    }
    for node in all_nodes:
        ntype = node.get("type", "")
        nid = node.get("id", "?")
        required = type_required_fields.get(ntype, [])
        for field_name in required:
            has_field = field_name in node and node[field_name]
            if not has_field:
                checks.append(Check(
                    f"tree_field:{nid}:{field_name}",
                    False,
                    f"Node {nid} (type={ntype}) missing required field '{field_name}'"
                ))

    # Check also_depends_on references resolve
    for node in all_nodes:
        deps = node.get("also_depends_on", [])
        if isinstance(deps, list):
            for dep_id in deps:
                ok = dep_id in node_ids
                if not ok:
                    checks.append(Check(
                        f"tree_dep_resolves:{dep_id}",
                        False,
                        f"also_depends_on reference '{dep_id}' not found in tree"
                    ))

    # Check every node has id and type
    for node in all_nodes:
        if not node.get("id"):
            checks.append(Check("tree_node_has_id", False, f"Node missing 'id' field: {node}"))
        if not node.get("type"):
            checks.append(Check(
                f"tree_node_has_type:{node.get('id', '?')}",
                False,
                f"Node {node.get('id', '?')} missing 'type' field"
            ))

    return checks


def run_level_1(ara_dir: Path) -> LevelResult:
    """Level 1: Structural Integrity — is the artifact well-formed and internally consistent?

    Merges structural validation (schema, files, dirs) with cross-layer
    binding (reference resolution, claim grounding, component mapping).
    """
    checks = []

    # 1a. Mandatory directories
    for d in MANDATORY_DIRS:
        path = ara_dir / d
        exists = path.is_dir()
        checks.append(Check(
            f"dir_exists:{d}",
            exists,
            "" if exists else f"Missing directory: {d}"
        ))

    # 1b. Mandatory files
    for f in MANDATORY_FILES:
        path = ara_dir / f
        exists = path.is_file()
        non_empty = exists and path.stat().st_size > 10
        if not exists:
            checks.append(Check(f"file_exists:{f}", False, f"Missing file: {f}"))
        elif not non_empty:
            checks.append(Check(f"file_nonempty:{f}", False, f"File is empty or trivial: {f}"))
        else:
            checks.append(Check(f"file_exists:{f}", True))

    # 1c. YAML frontmatter in PAPER.md
    paper_md = ara_dir / "PAPER.md"
    if paper_md.is_file():
        checks.append(_check_yaml_frontmatter(paper_md))
        # Check PAPER.md has Layer Index
        paper_content = paper_md.read_text()
        has_layer_index = bool(re.search(r'Layer Index|layer index|## .*(Layer|Index)', paper_content, re.IGNORECASE))
        checks.append(Check(
            "paper_has_layer_index",
            has_layer_index,
            "" if has_layer_index else "PAPER.md missing Layer Index section"
        ))

    # 1c2. evidence/README.md has a file index table
    evidence_readme = ara_dir / "evidence" / "README.md"
    if evidence_readme.is_file():
        readme_content = evidence_readme.read_text()
        has_table = bool(re.search(r'\|.*\|.*\|', readme_content))
        checks.append(Check(
            "evidence_readme_has_index",
            has_table,
            "" if has_table else "evidence/README.md missing file index table"
        ))

    # 1d. Required fields in structured files
    for filepath, field_patterns in REQUIRED_FIELDS.items():
        full_path = ara_dir / filepath
        if not full_path.is_file():
            continue
        content = full_path.read_text()
        for field_name, pattern in field_patterns.items():
            found = bool(re.search(pattern, content))
            checks.append(Check(
                f"field_present:{filepath}:{field_name}",
                found,
                "" if found else f"Missing required field/block '{field_name}' in {filepath}"
            ))

    # 1e. Check concept count in concepts.md
    concepts_path = ara_dir / "logic" / "concepts.md"
    if concepts_path.is_file():
        checks.append(_check_concepts_count(concepts_path))

    # 1f. Check experiment count in experiments.md
    experiments_path = ara_dir / "logic" / "experiments.md"
    if experiments_path.is_file():
        checks.append(_check_experiments_count(experiments_path))

    # 1g. Check for code stubs
    exec_dir = ara_dir / "src" / "execution"
    if exec_dir.is_dir():
        py_files = list(exec_dir.glob("*.py"))
        has_code = len(py_files) >= 1
        checks.append(Check(
            "code_stubs_count",
            has_code,
            "" if has_code else f"Need >= 1 code stub in src/execution/, found {len(py_files)}"
        ))
    else:
        checks.append(Check("execution_dir_exists", False, "Missing directory: src/execution"))

    # 1h. Evidence data files: tables and/or figures must exist with actual data
    evidence_dir = ara_dir / "evidence"
    tables_dir = evidence_dir / "tables"
    figures_dir = evidence_dir / "figures"
    table_files = list(tables_dir.glob("*.md")) if tables_dir.is_dir() else []
    figure_files = list(figures_dir.glob("*.md")) if figures_dir.is_dir() else []
    evidence_files = table_files + figure_files
    has_evidence = len(evidence_files) >= 1
    checks.append(Check(
        "evidence_data_count",
        has_evidence,
        "" if has_evidence else "Need >= 1 evidence data file in evidence/tables/ or evidence/figures/"
    ))
    # Each evidence file must contain a Markdown table (pipe-delimited rows)
    for ef in evidence_files:
        content = ef.read_text()
        has_table = bool(re.search(r'\|.*\|.*\|', content))
        checks.append(Check(
            f"evidence_has_table:{ef.relative_to(ara_dir)}",
            has_table,
            "" if has_table else f"Evidence file {ef.name} has no Markdown table with data"
        ))
        has_source = bool(re.search(r'\*\*Source\*\*', content))
        checks.append(Check(
            f"evidence_has_source:{ef.relative_to(ara_dir)}",
            has_source,
            "" if has_source else f"Evidence file {ef.name} missing **Source** field"
        ))

    # 1i. Exploration tree structure (YAML)
    tree_path = ara_dir / "trace" / "exploration_tree.yaml"
    if tree_path.is_file():
        checks.extend(_check_exploration_tree_structure(tree_path))

    # ---------------------------------------------------------------------------
    # Cross-layer binding checks (previously Level 2, now part of Level 1)
    # ---------------------------------------------------------------------------

    claims_path = ara_dir / "logic" / "claims.md"
    experiments_path = ara_dir / "logic" / "experiments.md"

    # Collect experiment IDs from experiments.md
    experiment_ids = set()
    if experiments_path.is_file():
        exp_content = experiments_path.read_text()
        experiment_ids = set(re.findall(r'##\s+(E\d+)', exp_content))

    # Collect claim IDs from claims.md
    claim_ids = set()
    if claims_path.is_file():
        claims_content = claims_path.read_text()
        claim_ids = set(re.findall(r'##\s+(C\d+)', claims_content))

    # 2a. Claim Proof → experiment ID resolution
    if claims_path.is_file():
        content = claims_path.read_text()
        proof_refs = re.findall(r'\*\*Proof\*\*:\s*\[([^\]]+)\]', content)
        for ref in proof_refs:
            individual_refs = [r.strip() for r in ref.split(",")]
            for ref_clean in individual_refs:
                # Check experiment ID references (E01, E02, etc.)
                exp_matches = re.findall(r'E\d+', ref_clean)
                for eid in exp_matches:
                    found = eid in experiment_ids
                    checks.append(Check(
                        f"proof_refs_experiment:{eid}",
                        found,
                        "" if found else f"Claim proof references experiment '{eid}' not found in experiments.md"
                    ))
                # Also allow direct evidence/ or src/ path references
                ref_path = ref_clean.strip().lstrip("/")
                if ref_path.startswith("evidence/") or ref_path.startswith("src/"):
                    target = ara_dir / ref_path
                    exists = target.exists() or any(ara_dir.glob(ref_path + "*"))
                    checks.append(Check(
                        f"proof_uri_resolves:{ref_path}",
                        exists,
                        "" if exists else f"Proof URI '{ref_path}' not found"
                    ))

    # 2b. Experiment Verifies → claim ID resolution
    if experiments_path.is_file():
        content = experiments_path.read_text()
        verifies_refs = re.findall(r'\*\*Verifies\*\*:\s*(.+)', content)
        for ref_line in verifies_refs:
            ref_claim_ids = re.findall(r'C\d+', ref_line)
            for cid in ref_claim_ids:
                found = cid in claim_ids
                checks.append(Check(
                    f"experiment_verifies_claim:{cid}",
                    found,
                    "" if found else f"Experiment references claim '{cid}' not found in claims.md"
                ))

    # 2c. code_ref resolution: heuristics → src/execution/
    heuristics_path = ara_dir / "logic" / "solution" / "heuristics.md"
    if heuristics_path.is_file():
        content = heuristics_path.read_text()
        code_refs = re.findall(r'\*\*Code ref\*\*:\s*\[([^\]]+)\]', content)
        for ref in code_refs:
            ref_clean = ref.strip().lstrip("/")
            # Strip arrow/anchor notation: "src/execution/x.py → `func()`"
            file_part = re.split(r'[→#]', ref_clean)[0].strip()
            if not file_part.startswith("src/"):
                continue
            target = ara_dir / file_part
            exists = target.exists()
            checks.append(Check(
                f"code_ref_resolves:{file_part}",
                exists,
                "" if exists else f"Code ref '{file_part}' not found"
            ))

    # 2d. Architecture components → code stubs (fuzzy match)
    arch_path = ara_dir / "logic" / "solution" / "architecture.md"
    exec_dir = ara_dir / "src" / "execution"
    if arch_path.is_file() and exec_dir.is_dir():
        arch_content = arch_path.read_text()
        components = re.findall(r'##\s+(.+)', arch_content)
        all_code = ""
        for f in exec_dir.glob("*.py"):
            all_code += f.read_text().lower() + "\n"

        skip_words = {"the", "and", "with", "from", "this", "that", "overview",
                      "component", "graph", "diagram", "interaction", "notes",
                      "implementation", "components", "summary", "design",
                      "system", "high", "level", "architecture", "specifications",
                      "executor", "server", "client", "flow", "data",
                      "descriptions", "description", "details", "interfaces"}
        for comp in components[:10]:
            comp_lower = comp.lower().strip()
            words = re.findall(r'[a-z]+', comp_lower)
            significant_words = [w for w in words if len(w) > 3 and w not in skip_words]
            if not significant_words:
                continue
            found = any(w in all_code for w in significant_words)
            checks.append(Check(
                f"arch_component_has_code:{comp.strip()[:50]}",
                found,
                "" if found else f"Architecture component '{comp.strip()[:50]}' has no matching code stub"
            ))

    # 2e. Exploration tree evidence references → claims (YAML)
    tree_path = ara_dir / "trace" / "exploration_tree.yaml"
    if tree_path.is_file():
        try:
            import yaml
            tree_data = yaml.safe_load(tree_path.read_text())
            if isinstance(tree_data, dict) and "tree" in tree_data:
                all_tree_nodes = _collect_yaml_tree_nodes(tree_data["tree"])
                for node in all_tree_nodes:
                    evidence = node.get("evidence", [])
                    if isinstance(evidence, str):
                        evidence = [evidence]
                    if isinstance(evidence, list):
                        for ref in evidence:
                            ref_claim_ids = re.findall(r'C\d+', str(ref))
                            for cid in ref_claim_ids:
                                found = cid in claim_ids
                                checks.append(Check(
                                    f"tree_evidence_resolves:{node.get('id', '?')}:{cid}",
                                    found,
                                    "" if found else f"Tree node {node.get('id', '?')} references claim '{cid}' not found in claims.md"
                                ))
        except Exception:
            pass  # YAML parse errors are caught in Level 1

    passed = all(c.passed for c in checks)
    return LevelResult("1_structural_integrity", passed, checks)


# ---------------------------------------------------------------------------
# Level 2: Information Fidelity — Sub-agent Q&A comparison
# ---------------------------------------------------------------------------

def run_level_2(ara_dir: Path, pdf_path: str | Path | None = None,
                model: str = "claude-sonnet-4-6") -> LevelResult:
    """Level 2: Information Fidelity — is the artifact a faithful representation?

    Runs a sub-agent Q&A comparison between ARA and source PDF.
    A bank of factual questions is answered from both formats;
    an independent judge compares answers in a blinded evaluation.
    Near-parity confirms lossless transformation.

    This is the same protocol as the Tier 1 (Information Preservation) eval.
    If pdf_path is not provided, this level is skipped.
    """
    if pdf_path is None:
        return LevelResult(
            "2_information_fidelity", False,
            [Check("l2_no_pdf", False, "PDF path not provided; cannot run fidelity check")]
        )

    # Import the eval pipeline lazily to avoid circular deps
    try:
        from eval.run_ab_eval import (
            load_questions, build_ara_context, build_pdf_context,
            call_answerer, call_judge, deblind_and_summarize,
        )
    except ImportError:
        return LevelResult(
            "2_information_fidelity", False,
            [Check("l2_import_error", False, "Could not import eval pipeline (eval.run_ab_eval)")]
        )

    ara_dir = Path(ara_dir)
    pdf_path = Path(pdf_path)
    questions_path = ara_dir / "questions.json"
    if not questions_path.exists():
        # Try code/eval/questions/ directory
        code_root = Path(__file__).resolve().parent.parent
        questions_path = code_root / "eval" / "questions" / f"{ara_dir.name}_catA.json"
    if not questions_path.exists():
        questions_path = code_root / "eval" / "questions" / f"{ara_dir.name}.json"

    if not questions_path.exists():
        return LevelResult(
            "2_information_fidelity", False,
            [Check("l2_no_questions", False, f"No questions found for {ara_dir.name}")]
        )

    checks = []
    try:
        questions = load_questions(questions_path, n=10)
        ara_context = build_ara_context(ara_dir)
        pdf_context = build_pdf_context(pdf_path)

        import anthropic
        # Run ARA and PDF answerers
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_ara = pool.submit(call_answerer, "ARA", ara_context, questions)
            f_pdf = pool.submit(call_answerer, "PDF", pdf_context, questions)
            result_ara = f_ara.result()
            result_pdf = f_pdf.result()

        # Judge
        judge_result = call_judge(
            questions,
            result_ara["answers"] or [],
            result_pdf["answers"] or [],
        )
        summary = deblind_and_summarize(judge_result)
        s = summary["summary"]

        # Pass if ARA score is within 80% of PDF score (near-parity)
        ara_avg = s["ara_avg_score"]
        pdf_avg = s["pdf_avg_score"]
        parity_ratio = ara_avg / max(pdf_avg, 0.01)
        is_parity = parity_ratio >= 0.8

        checks.append(Check(
            "l2_fidelity_parity",
            is_parity,
            f"ARA avg={ara_avg:.1f}, PDF avg={pdf_avg:.1f}, ratio={parity_ratio:.2f}"
        ))
        checks.append(Check(
            "l2_ara_wins",
            True,  # informational
            f"ARA wins={s['ara_wins']}, PDF wins={s['pdf_wins']}, ties={s['ties']}"
        ))

    except Exception as e:
        checks.append(Check("l2_error", False, f"Level 2 failed: {e}"))

    passed = all(c.passed for c in checks)
    return LevelResult("2_information_fidelity", passed, checks)


# ---------------------------------------------------------------------------
# Level 3: Execution Reproducibility — LLM-Generated Reproduction Tests
# ---------------------------------------------------------------------------

_TEST_GEN_PROMPT_TEMPLATE = """You are an expert at designing reproduction tests for research papers. You are given an ARA (Agent-native Research Artifact) containing structured knowledge about a paper, including its claims, experiments, and a **code kernel** — a minimal implementation of the core algorithm.

Your task: design exactly 3 reproduction test cases that a coding agent can execute using the code kernel. Each test must verify a key property of the paper.

# ARA Contents

## Claims (logic/claims.md)
<<CLAIMS>>

## Experiments (logic/experiments.md)
<<EXPERIMENTS>>

## Code Kernel — Available Functions and Classes
<<CODE_KERNEL>>

## Evidence Tables
<<EVIDENCE>>

# Requirements

1. **Pick 3 claims** that are best testable with the code kernel above. Prioritize:
   - Claims where the code kernel provides the actual algorithm being tested
   - Claims with clear directional properties (A > B, metric increases with X)
   - Diverse claims (don't pick 3 variants of the same claim)

2. For each test case, provide:
   - `claim_id`: The claim ID from claims.md (e.g., "C01")
   - `claim`: The claim statement
   - `experiment`: Short name for the test
   - `setup`: What synthetic data/environment to create. Be specific about:
     - What objects to instantiate (reference actual classes from the code kernel)
     - Parameter ranges and distributions
     - Scale (number of items, iterations, etc.)
   - `procedure`: Step-by-step instructions using actual function names from the code kernel.
     Tell the agent exactly which functions to call and how.
   - `expected_results`: Specific directional properties to check, with reference values from the paper.
   - `success_criteria`: Concrete pass/fail checks. E.g., "Venn JCT < FIFO JCT" not just "Venn is better".
   - `code_hints`: Brief hints on how to use the code kernel (e.g., "Call venn_sched(groups, pool) to get scheduling assignments. The return is Dict[key, (job, devices)].")

3. **Key principle**: The coding agent uses synthetic data, not real datasets. Absolute numbers WILL differ from the paper. Tests must verify DIRECTIONAL properties only (rankings, orderings, trends). Design tests that are robust to magnitude differences.

4. **Avoid**: Claims that require external datasets, pre-trained models, or hardware-specific benchmarks. Focus on algorithmic properties testable with synthetic inputs.

Return ONLY a JSON array of 3 test cases. No markdown fences, no other text — just the raw JSON array."""


def _read_ara_for_test_gen(ara_dir: Path) -> dict[str, str]:
    """Read key ARA files needed for LLM-based test case generation."""
    result = {}

    # Claims
    claims_path = ara_dir / "logic" / "claims.md"
    result["claims"] = claims_path.read_text() if claims_path.is_file() else "(not found)"

    # Experiments
    exp_path = ara_dir / "logic" / "experiments.md"
    result["experiments"] = exp_path.read_text() if exp_path.is_file() else "(not found)"

    # Code kernel — read all .py files in src/execution/
    exec_dir = ara_dir / "src" / "execution"
    code_parts = []
    if exec_dir.is_dir():
        for py_file in sorted(exec_dir.glob("*.py")):
            content = py_file.read_text()
            code_parts.append(f"### {py_file.name}\n```python\n{content}\n```")
    result["code_kernel"] = "\n\n".join(code_parts) if code_parts else "(no code kernel found)"

    # Evidence tables — read up to 5 evidence files
    evidence_parts = []
    for subdir in ["tables", "figures"]:
        edir = ara_dir / "evidence" / subdir
        if edir.is_dir():
            for md_file in sorted(edir.glob("*.md"))[:5]:
                content = md_file.read_text()
                if len(content) > 4000:
                    content = content[:4000] + "\n... (truncated)"
                evidence_parts.append(f"### {subdir}/{md_file.name}\n{content}")
    result["evidence"] = "\n\n".join(evidence_parts) if evidence_parts else "(no evidence files)"

    return result


def _generate_test_cases(ara_dir: Path, model: str = "claude-sonnet-4-6") -> list[dict]:
    """Use an LLM to generate targeted reproduction test cases from the ARA.

    Reads the code kernel, claims, experiments, and evidence to produce
    3 test cases that are actually feasible to reproduce with the code kernel.
    """
    import anthropic

    ara_content = _read_ara_for_test_gen(ara_dir)

    if ara_content["claims"] == "(not found)" or ara_content["code_kernel"] == "(no code kernel found)":
        return []

    prompt = (_TEST_GEN_PROMPT_TEMPLATE
              .replace("<<CLAIMS>>", ara_content["claims"])
              .replace("<<EXPERIMENTS>>", ara_content["experiments"])
              .replace("<<CODE_KERNEL>>", ara_content["code_kernel"])
              .replace("<<EVIDENCE>>", ara_content["evidence"]))

    print("  [L3] Generating test cases from ARA...")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # Extract JSON from response (may be wrapped in ```json ... ```)
    json_match = re.search(r'```json\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    try:
        test_cases = json.loads(text)
        if not isinstance(test_cases, list):
            print("  [L3] Warning: LLM returned non-list, wrapping")
            test_cases = [test_cases]
        # Ensure test_id is set
        for i, tc in enumerate(test_cases):
            tc.setdefault("test_id", f"T{i + 1}")
        tokens = response.usage.input_tokens + response.usage.output_tokens
        print(f"  [L3] Generated {len(test_cases)} test cases ({tokens:,} tokens)")
        return test_cases[:3]
    except json.JSONDecodeError as e:
        print(f"  [L3] Error parsing test cases: {e}")
        print(f"  [L3] Raw response: {text[:500]}")
        return []


def run_level_3(ara_dir: str | Path, model: str = "claude-sonnet-4-6") -> tuple[LevelResult, list[dict]]:
    """Level 3: Execution Reproducibility — spawn coding agents to reproduce claims.

    1. Uses an LLM to read the ARA and generate 3 targeted test cases
       that are feasible to reproduce with the code kernel.
    2. For each test case, spawns a coding agent that writes and runs
       a test script, then reports whether the claim is directionally reproduced.

    This is expensive (LLM calls + code execution). Run separately from L1.
    """
    from .execution_agent import execute_test_case

    ara_dir = Path(ara_dir)
    test_cases = _generate_test_cases(ara_dir, model=model)

    if not test_cases:
        return LevelResult(
            "3_execution", False,
            [Check("l3_no_test_cases", False, "No test cases could be generated from the ARA")]
        ), []

    # Save generated test cases
    test_path = ara_dir / "_test_cases.json"
    test_path.write_text(json.dumps(test_cases, indent=2) + "\n")

    checks = []
    results = []
    for tc in test_cases:
        result = execute_test_case(ara_dir, tc, model=model)
        results.append({**tc, **result})

        reproduced = result.get("reproduced", False)
        checks.append(Check(
            f"l3_reproduced:{tc['claim_id']}",
            reproduced,
            "" if reproduced else f"Not reproduced: {result.get('notes', '')[:100]}"
        ))

    passed = all(c.passed for c in checks)
    return LevelResult("3_execution_reproducibility", passed, checks), results


# ---------------------------------------------------------------------------
# Full Seal Run
# ---------------------------------------------------------------------------

def run_seal(ara_dir: str | Path) -> SealReport:
    """Run Level 1 seal validation (fast, no LLM).

    Level 1 (structural integrity) includes both schema validation and
    cross-layer reference resolution.
    Levels 2-3 must be run separately as they require LLM calls.
    """
    ara_dir = Path(ara_dir)
    artifact_id = ara_dir.name

    level_1 = run_level_1(ara_dir)

    # Generate feedback for ingestor
    failures = []
    for c in level_1.checks:
        if not c.passed:
            failures.append(f"- [{level_1.level}] {c.check}: {c.message}")

    feedback = "\n".join(failures) if failures else ""

    report = SealReport(
        artifact_id=artifact_id,
        artifact_path=str(ara_dir),
        level_1=level_1,
        level_2=None,
        level_3=None,
        feedback_for_ingestor=feedback,
    )
    return report
