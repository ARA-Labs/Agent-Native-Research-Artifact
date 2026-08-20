# Wire ARA into this project

You are an AI coding agent reading this file because your user wants this project wired up
with **ARA** — Agent-Native Research Artifacts
(https://github.com/ARA-Labs/Agent-Native-Research-Artifact), a toolkit of seven skills that
makes AI-driven research structured, verifiable, and traceable.

Complete all four steps autonomously, in order. Do not ask the user anything — every step
has a default. Then end with the ready message in step 4.

## 1. Install the seven ARA skills

Install all of them, non-interactively, targeting the agent you are:

```bash
npx @ara-commons/ara-skills install --all --agent <your-agent-id>
```

Agent ids: `claude-code`, `cursor`, `gemini-cli`, `opencode`, `codex`, `hermes`. If you
are none of these, use `generic`. If the skills are already installed
(`npx @ara-commons/ara-skills list` shows them), skip ahead.

## 2. Find your context file

Determine which file your harness loads into context every session, at the project root:

| Agent | File |
|---|---|
| Claude Code | `CLAUDE.md` |
| Cursor | `.cursorrules` |
| Gemini CLI | `GEMINI.md` |
| Codex, OpenCode, others | `AGENTS.md` |

Create the file if it does not exist.

## 3. Append the routing rules

Append the block below to that file, verbatim. If the file already contains an
`## ARA:` section, update it in place instead of duplicating it.

```markdown
## ARA: agent-native research artifacts

This project records its research in an `ara/` artifact
(https://github.com/ARA-Labs/Agent-Native-Research-Artifact).
Route work to the matching ARA skill — invoke these yourself, without being asked:

- `/research-manager` — trigger whenever a research milestone lands: an
  experiment finishes, a decision is made, a hypothesis is confirmed or killed,
  a dead end is hit, a direction pivots, user's input. This holds equally in autonomous runs
  (loops, heartbeats, long experiments) where the user gives no input at all —
  crystallize the insight at the milestone. It
  records what just happened (decisions, experiments, dead ends, claims) into
  `ara/`. Skip when nothing research-significant happened (greetings, pure formatting).
- `/compiler <path>` — when turning an existing paper, repo, logs, or notes into
  a structured artifact.
- `/rigor-reviewer <dir>` — before trusting, publishing, or submitting an artifact.
- `/research-visualizer <ara-dir>` — to inspect the research trajectory as an
  interactive process map (add `--serve` for a live local viewer, `--check` to
  validate/lint via the `ara` CLI).
- `/research-foresight <ara-dir> "<question>"` — to answer "what should I try
  next / why did this work / what if I change X", grounded in the artifact.
- `/context-drop <path>` — when a file, folder, or artifact needs to reach
  somebody else's agent as one link.
- `/research-fuzzer` — for any open-ended investigation without a known map
  (experiments, debugging, data analysis, literature or market research). Fire
  it when the investigation starts, after every action or batch that returned
  results, and before stating any conclusion: predict before each action,
  settle after, keep the queue of untried leads and unexplained results, and
  gate conclusions behind a self-refutation attempt. Skip for trivial
  single-step tasks.
```

## 4. Tell the user they are ready

From this turn onward, honor the rules yourself — in particular, trigger
`/research-manager` whenever a research milestone lands, user-prompted or
autonomous, without being asked.

Close by telling the user they can now start doing AI-native research, in roughly these
words (adapt naturally, keep the substance):

> ✅ ARA is wired in. You can now do AI-native research — just work with me as usual.
>
> - As we work, I will automatically record every decision, experiment, dead end, and
>   claim into the **`ara/` directory** at the project root — that is your living
>   research artifact.
> - Have an existing paper, repo, or pile of notes? Say "compile it" and I'll turn it
>   into an artifact with `/compiler`.
> - Want to see the research trajectory so far? Ask for the process map
>   (`/research-visualizer ara/`).
> - Stuck on what to try next? Ask the artifact (`/research-foresight ara/ "<question>"`).
> - When results are ready to share: I'll review rigor (`/rigor-reviewer ara/`) and
>   hand the artifact to anyone's agent as one link (`/context-drop ara/`).
