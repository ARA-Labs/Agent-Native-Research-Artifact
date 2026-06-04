# Agent-Native Research Artifact (ARA)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-3%20skills-green)](skills/)
[![arXiv](https://img.shields.io/badge/arXiv-2604.24658-b31b1b.svg)](https://arxiv.org/abs/2604.24658)
[![Poster](https://img.shields.io/badge/Poster-PDF-orange.svg)](docs/poster.pdf)

> A protocol that recasts the primary research object from narrative document to **machine-executable knowledge package** — so AI agents can navigate, reproduce, and extend published research without re-discovering every dead end.

<p align="center">
  <img src="docs/figures/fig_legacy_vs_ara_v6.png" alt="Legacy PDF vs ARA" width="100%"/>
</p>

*Publishing compiles a rich research object into a lossy narrative (left); ARA preserves the original as a high-fidelity, machine-executable knowledge package (right).*

---

## The Problem

Research produces a branching knowledge object — months of hypotheses tested and rejected, implementation tricks discovered through trial and error, design alternatives weighed. Publishing compiles this into a linear narrative, discarding everything that doesn't fit the final story.

This was tolerable when every consumer was human. It is not when AI agents routinely read papers to reproduce experiments and extend published methods.

<p align="center">
  <img src="docs/figures/fig_info_gap.png" alt="Reproduction information gap" width="90%"/>
</p>

**The numbers:**
- Only **45.4%** of 8,921 reproduction requirements from 23 ICML 2024 papers are fully specified in their PDFs ([PaperBench](https://openai.com/index/paperbench/))
- Failed agent runs account for **90.2%** of total dollar cost across 24,008 runs on RE-Bench — agents without prior failure records rediscover every dead end independently

---

## What is ARA?

ARA organizes research into four interlocking layers:

```
artifact/
  PAPER.md                    # Root manifest + layer index (~200 tokens)
  logic/                      # Cognitive layer — What & Why
    problem.md                #   Observations → gaps → key insight
    claims.md                 #   Falsifiable assertions with proof refs
    concepts.md               #   Formal definitions
    experiments.md            #   Declarative experiment plans
    solution/
      architecture.md         #   System design + component graph
      algorithm.md            #   Math + pseudocode
      constraints.md          #   Boundary conditions
      heuristics.md           #   Implementation tricks + rationale
    related_work.md           #   Typed dependency graph
  src/                        # Physical layer — How
    configs/                  #   Hyperparameters with rationale
    environment.md            #   Dependencies, hardware, seeds
  trace/                      # Exploration graph — Journey
    exploration_tree.yaml     #   Research DAG with typed nodes + dead ends
  evidence/                   # Raw proof
    tables/                   #   Exact result tables
    figures/                  #   Extracted data points
```

<p align="center">
  <img src="docs/figures/fig_cross_layer_v2_attempt1.png" alt="Cross-layer bindings" width="90%"/>
</p>

*Cross-layer forensic bindings thread claims in `/logic` to code in `/src` and evidence in `/evidence`. Dead-end nodes (×) in the exploration graph preserve failure modes.*

### Key design principles

- **Progressive disclosure** — `PAPER.md` (~200 tokens) tells agents whether the artifact is relevant. Deeper files load on demand.
- **Cross-layer binding** — Claims reference experiments, experiments reference evidence, heuristics reference code. Everything is linked.
- **Dead ends preserved** — Failed approaches and rejected alternatives are first-class nodes in the exploration graph, preventing agents from rediscovering known failures.
- **Provenance tracking** — Every entry carries a tag (`user`, `ai-suggested`, `ai-executed`, `user-revised`) distinguishing human-confirmed facts from AI inferences.

---

## Skills

This repository ships three open-source agent skills that work with ARA:

| Skill | Description | Invoke |
|-------|-------------|--------|
| **[compiler](skills/compiler/)** | Compiles papers, repos, notes, or any research input into a structured ARA artifact | `/compiler <path>` |
| **[research-manager](skills/research-manager/)** | End-of-turn recorder that captures decisions, experiments, and dead ends with provenance tags | `/research-manager` |
| **[rigor-reviewer](skills/rigor-reviewer/)** | ARA Seal Level 2 semantic review — scores six dimensions of epistemic rigor | `/rigor-reviewer <artifact_dir>` |

### Compiler

<p align="center">
  <img src="docs/figures/fig_compiler_v2.png" alt="ARA Compiler" width="90%"/>
</p>

Converts ANY research input into a complete ARA artifact. Accepts PDFs, GitHub repos, experiment logs, code directories, raw notes, or combinations. Follows a 4-stage epistemic protocol:

1. **Semantic Deconstruction** — extract raw knowledge atoms
2. **Cognitive Mapping** — map to claims, concepts, experiments
3. **Physical Stubbing** — generate configs and code stubs
4. **Exploration Graph Extraction** — reconstruct the research DAG

```
/compiler path/to/paper.pdf
/compiler https://github.com/org/repo
/compiler path/to/paper.pdf path/to/code/ --output ./my-artifact/
```

See [skills/compiler/SKILL.md](skills/compiler/SKILL.md) for the full specification.

### Research Manager (Live Capture)

<p align="center">
  <img src="docs/figures/fig_lrm_lifecycle_v5_attempt2.png" alt="Research Manager lifecycle" width="90%"/>
</p>

An end-of-turn recorder that runs after every turn and writes research-significant events into the `ara/` artifact via a three-stage pipeline (Context Harvester → Event Router → Maturity Tracker). Trace events (decisions, experiments, dead ends, pivots) are recorded immediately; knowledge events (claims, heuristics, concepts, constraints) are staged and crystallize only on closure signals — so research knowledge accrues as a side-effect of ordinary development.

```
/research-manager
```

See [skills/research-manager/SKILL.md](skills/research-manager/SKILL.md) for the full specification.

### Rigor Reviewer (ARA Seal Level 2)

A semantic epistemic review that assumes Level 1 structural validation has passed, then scores six dimensions — evidence relevance, falsifiability, scope calibration, and more — producing a `level2_report.json` with severity-ranked findings and an overall recommendation.

```
/rigor-reviewer path/to/artifact/
```

See [skills/rigor-reviewer/SKILL.md](skills/rigor-reviewer/SKILL.md) for the full specification.

---

## Install

```bash
npx @ara-commons/ara-skills
```

Auto-detects Claude Code, Cursor, Gemini CLI, OpenCode, Codex, and Hermes, then prompts for skills, agents, and install scope (global vs. local).

Full CLI reference: [`packages/ara-skills/`](packages/ara-skills/).

---

## Compatibility

These skills follow the [Agent Skills open standard](https://agentskills.io/specification) and work with:

- [Claude Code](https://claude.ai/code) (Anthropic)
- [Codex CLI](https://github.com/openai/codex) (OpenAI)
- [GitHub Copilot](https://github.com/features/copilot)
- [Cursor](https://cursor.com)
- Any agent supporting the Agent Skills specification

---

## Citation

If you use ARA in your research, please cite:

```bibtex
@article{ara2026,
  title        = {The Last Human-Written Paper: Agent-Native Research Artifacts},
  author       = {Liu, Jiachen and Pei, Jiaxin and Huang, Jintao and Si, Chenglei and Qu, Ao and Tang, Xiangru and Lu, Runyu and Chen, Lichang and Bai, Xiaoyan and Zheng, Haizhong and Chen, Carl and Chen, Zhiyang and Ye, Haojie and Fu, Yujuan and He, Zexue and Jin, Zijian and Zhang, Zhenyu and Sun, Shangquan and Harmon, Maestro and Wang, John Dianzhuo and Zeng, Jianqiao and Sun, Jiachen and Wu, Mingyuan and Zhou, Baoyu and You, Chenyu and Lu, Shijian and Qiu, Yiming and Lai, Fan and Yuan, Yuan and Li, Yao and Hong, Junyuan and Zhu, Ruihao and Chen, Beidi and Pentland, Alex and Chen, Ang and Chowdhury, Mosharaf and Zhang, Zechen},
  year         = {2026},
  eprint       = {2604.24658},
  archivePrefix= {arXiv},
  url          = {https://arxiv.org/abs/2604.24658}
}
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add or improve skills, or contribute ARA artifacts to `ara-output/`.

## License

[MIT](LICENSE)
