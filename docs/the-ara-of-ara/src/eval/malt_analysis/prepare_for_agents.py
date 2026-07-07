"""
Prepare condensed research failure samples for each task.
For each task, output a readable text file with:
1. Diverse hypothesis-failure pairs (sampled across models)
2. Sorted by diversity (not just frequency)
"""

import json
import os
import re
from collections import Counter, defaultdict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Stronger infrastructure filter
INFRA_PATTERNS = re.compile("|".join([
    r"no module named", r"modulenotfounderror", r"importerror", r"cannot import",
    r"missing module", r"filenotfounderror", r"no such file", r"does not exist",
    r"not found", r"rate.?limit", r"too many requests", r"asyncopenai",
    r"permission denied", r"access denied", r"state_dict", r"load_state_dict",
    r"syntaxerror", r"syntax error", r"indentation", r"not defined",
    r"pip install", r"command not found", r"package.*not installed",
    r"connection.*refused", r"connection.*reset", r"connection.*timeout",
    r"missing.*function", r"function.*missing", r"required function",
    r"unexpected key", r"missing key.*in", r"unexpected argument",
    r"get_trained_model", r"generate_solution.*missing",
    r"missing.*argument", r"positional argument",
    r"missing.*import", r"import.*missing", r"forgot to import",
]), re.IGNORECASE)

# Also filter by failure summary — keep only those with research substance
RESEARCH_KEYWORDS = re.compile("|".join([
    r"overfit", r"underfit", r"diverge", r"converge", r"loss.*high", r"loss.*increas",
    r"accuracy.*low", r"accuracy.*decreas", r"performance.*degrad", r"performance.*worse",
    r"wrong.*result", r"incorrect.*output", r"incorrect.*result", r"invalid.*submission",
    r"exceeded.*limit", r"exceed.*flop", r"exceed.*budget", r"exceed.*constraint",
    r"timeout", r"too slow", r"too long", r"takes too long",
    r"out of memory", r"oom", r"memory.*exceed", r"cuda.*memory",
    r"shape.*mismatch", r"dimension.*mismatch", r"size.*mismatch",
    r"nan", r"inf\b", r"numerical.*instab", r"gradient.*explod", r"gradient.*vanish",
    r"reward.*negative", r"reward.*zero", r"reward.*nan",
    r"compilation.*error", r"kernel.*error", r"triton.*error",
    r"forbidden", r"restricted", r"not allowed", r"violat",
    r"does not support", r"unsupported", r"not.*implement",
    r"wrong.*approach", r"inefficient", r"infeasib",
    r"fail.*to.*improv", r"no improvement", r"not.*improv",
    r"overshoot", r"undershoot", r"unstable",
    r"scaling.*law", r"extrapolat", r"interpol", r"fit.*fail",
    r"curve.*fit", r"regression.*fail",
    r"brute.?force", r"permutation", r"search.*space",
    r"layer.?norm", r"batch.?norm", r"normalization",
    r"embedding", r"weight.*ti", r"corrupt",
    r"fLOPs", r"compute.*budget",
]), re.IGNORECASE)


def is_research_failure(f):
    """More aggressive filter: must have research substance."""
    summary = f.get("failure_summary", "")
    hypothesis = f.get("hypothesis", "")

    # Must have a real hypothesis
    if not hypothesis or len(hypothesis) < 30:
        return False

    # Exclude if summary is purely infrastructure
    if INFRA_PATTERNS.search(summary):
        # Exception: if it also has research keywords, keep it
        if not RESEARCH_KEYWORDS.search(summary) and not RESEARCH_KEYWORDS.search(hypothesis):
            return False

    return True


def deduplicate_by_content(failures, max_output=80):
    """Deduplicate by semantic similarity (approximate: first 80 chars of hypothesis)."""
    seen_hypotheses = set()
    result = []

    for f in failures:
        # Normalize hypothesis for dedup
        h_norm = re.sub(r'\s+', ' ', f["hypothesis"][:80].lower().strip())
        if h_norm in seen_hypotheses:
            continue
        seen_hypotheses.add(h_norm)
        result.append(f)
        if len(result) >= max_output:
            break

    return result


for task in ['fix_embedding', 'nanogpt_chat_rl', 'restricted_mlm',
             'rust_codecontests', 'small_scaling_law', 'triton_cumsum']:

    with open(os.path.join(OUT_DIR, f"research_failures_{task}.json")) as f:
        data = json.load(f)

    # Filter to research-level
    research = [d for d in data if is_research_failure(d)]

    # Deduplicate
    deduped = deduplicate_by_content(research, max_output=80)

    # Write readable text file
    out_path = os.path.join(OUT_DIR, f"research_summary_{task}.txt")
    with open(out_path, "w") as f:
        f.write(f"# {task}: Research-Level Failure Modes from MALT Traces\n")
        f.write(f"# Total raw failures: {len(data)}\n")
        f.write(f"# After research filter: {len(research)}\n")
        f.write(f"# After dedup: {len(deduped)}\n\n")

        for i, d in enumerate(deduped):
            freq = d.get("frequency", 1)
            models = d.get("models_affected", [])
            f.write(f"--- Failure {i+1} (freq={freq}, models={','.join(m.split('/')[-1][:25] for m in models)}) ---\n")
            f.write(f"HYPOTHESIS: {d['hypothesis'][:500]}\n")
            f.write(f"FAILURE: {d['failure_summary'][:500]}\n\n")

    print(f"{task}: {len(data)} raw -> {len(research)} research -> {len(deduped)} deduped -> {out_path}")
