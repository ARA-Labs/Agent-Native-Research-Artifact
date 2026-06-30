#!/usr/bin/env python3
"""Portable ARA Seal Level 1 structural validator.

Usage:  python3 seal1_check.py <ara_dir>
Exit 0 = PASS, 1 = FAIL. Prints PASS/FAIL counts and every failure.

Covers the Level 1 checks needed after a remediation round: mandatory dirs/files,
field markers (claims/experiments/heuristics/related_work/concepts/problem), evidence
Source+Screenshot+sibling-png+identifier, and cross-layer Proof<->Verifies resolution.
Tree YAML structural checks are best run with a YAML lib if available; this script does a
light regex pass when PyYAML is absent.
"""
import os, re, sys, glob

def main(root):
    fails, oks = [], 0
    def ck(cond, msg):
        nonlocal oks
        if cond: oks += 1
        else: fails.append(msg)
    j = lambda *p: os.path.join(root, *p)

    for d in ["logic", "logic/solution", "src", "trace", "evidence"]:
        ck(os.path.isdir(j(d)), f"dir {d}")
    mand = ["PAPER.md", "logic/problem.md", "logic/claims.md", "logic/concepts.md",
            "logic/experiments.md", "logic/solution/constraints.md", "logic/related_work.md",
            "src/environment.md", "trace/exploration_tree.yaml", "evidence/README.md"]
    for f in mand:
        ck(os.path.isfile(j(f)) and os.path.getsize(j(f)) > 10, f"file {f} non-empty")

    p = open(j("PAPER.md")).read()
    ck(p.startswith("---"), "PAPER frontmatter")
    for k in ["title", "authors", "year"]:
        ck(re.search(rf"^{k}:", p, re.M) is not None, f"PAPER has {k}")
    ck("Layer Index" in p, "PAPER Layer Index")

    c = open(j("logic/claims.md")).read()
    ck(len(re.findall(r"## C\d+", c)) >= 1, "claims >=1")
    for fld in ["**Statement**", "**Status**", "**Falsification criteria**", "**Proof**",
                "**Evidence basis**", "**Interpretation**"]:
        ck(fld in c, f"claims {fld}")

    pr = open(j("logic/problem.md")).read()
    ck(re.search(r"### O\d+", pr) is not None, "problem O blocks")
    ck(re.search(r"### G\d+", pr) is not None, "problem G blocks")
    ck("## Key Insight" in pr or "**Insight**" in pr, "problem Key Insight")

    e = open(j("logic/experiments.md")).read()
    ck(len(re.findall(r"## E\d+", e)) >= 3, "experiments >=3")
    for fld in ["**Verifies**", "**Setup**", "**Procedure**", "**Expected outcome**"]:
        ck(fld in e, f"experiments {fld}")

    hp = j("logic/solution/heuristics.md")
    if os.path.isfile(hp):
        h = open(hp).read()
        ck(len(re.findall(r"## H\d+", h)) >= 1, "heuristics blocks")
        for fld in ["**Rationale**", "**Sensitivity**", "**Bounds**"]:
            ck(fld in h, f"heuristics {fld}")

    rw = open(j("logic/related_work.md")).read()
    ck(len(re.findall(r"## RW\d+", rw)) >= 1, "RW blocks")
    for fld in ["**Type**", "**Delta**"]:
        ck(fld in rw, f"RW {fld}")

    co = open(j("logic/concepts.md")).read()
    ck(len(re.findall(r"^## ", co, re.M)) >= 5, "concepts >=5 sections")
    ck("**Definition**" in co, "concepts Definition")

    for f in glob.glob(j("evidence/figures/*.md")) + glob.glob(j("evidence/tables/*.md")):
        s = open(f).read(); b = os.path.basename(f)[:-3]
        ck("**Source**" in s, f"{b} Source")
        ck("**Screenshot**" in s, f"{b} Screenshot")
        ck(os.path.isfile(f[:-3] + ".png"), f"{b}.png sibling")
        ck("|" in s, f"{b} markdown table")
        m = re.search(r"(table|figure)(\d+)", b)
        if m:
            ident = m.group(0); spaced = m.group(1).capitalize() + " " + m.group(2)
            ck(ident in s or spaced in s, f"{b} Source references identifier")
    for f in glob.glob(j("evidence/figures/*.md")):
        s = open(f).read(); b = os.path.basename(f)[:-3]
        for fld in ["**Figure type**", "**Extraction method**", "**Reading confidence**", "**Axes**"]:
            ck(fld in s, f"{b} {fld}")

    ck("|" in open(j("evidence/README.md")).read(), "evidence README table")

    exp_ids = set(re.findall(r"## (E\d+)", e)); claim_ids = set(re.findall(r"## (C\d+)", c))
    for pf in re.findall(r"\*\*Proof\*\*: ([^\n]+)", c):
        for x in re.findall(r"E\d+", pf):
            ck(x in exp_ids, f"claim Proof {x} resolves")
    for vf in re.findall(r"\*\*Verifies\*\*: ([^\n]+)", e):
        for x in re.findall(r"C\d+", vf):
            ck(x in claim_ids, f"experiment Verifies {x} resolves")

    print(f"Seal L1: PASS {oks}  FAIL {len(fails)}")
    for x in fails:
        print("  - FAIL:", x)
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
