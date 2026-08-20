# Using ARA as a Conference Submission Format

Record your research as you do it, then publish it as one link — the full trajectory, dead ends
included, that a reviewer or a visitor's agent can replay.

---

## 1. Set up

From your **project root**, paste this one line into your coding agent:

```
Read https://raw.githubusercontent.com/ARA-Labs/Agent-Native-Research-Artifact/main/wire-ara.md and follow its instructions.
```

That's the whole setup. The agent installs the skills and writes a routing block into its own
context file (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or `GEMINI.md`), so from then on it knows
which skill to fire and when — without you asking.

## 2. While you do research

**You do nothing.** Work as you normally do: run experiments, argue with your agent, change your
mind. At every research milestone — an experiment finishes, a hypothesis dies, a direction pivots —
the agent records what happened into `ara/` at your project root:

```
ara/
  PAPER.md      # manifest — what this artifact is, in ~200 tokens
  logic/        # claims, experiments, architecture, constraints
  src/          # configs + environment, with rationale
  trace/        # exploration_tree.yaml — the journey, dead ends included
  evidence/     # exact tables and figure data
```

Dead ends are first-class nodes, not noise to drop — that's the knowledge a paper always loses.
There's nothing to write up at the end of the day; the recording already happened.

Optionally, ask the artifact things as you go:

```
/research-foresight ara/ "what should I try next?"
```

### Already have a paper, repo, or a pile of notes?

Most people arrive at a conference with finished work, not a live `ara/`. Compile it:

```
/compiler ./path/to/paper.pdf
/compiler ./my-research-repo
/compiler ./notes/
```

The compiler extracts claims, methods, experiments, and evidence into a full ARA under
`ara-output/<slug>/`. A dense paper takes a few minutes. Then read it and fix what's wrong — the
agent's inferences are tagged `ai-suggested`, and your edits become `user-revised`.

## 3. See the trajectory

```
/research-visualizer ara/
```

Produces **`trajectory.html`** — one self-contained file, no server, no build. Left: the exploration
tree as a clickable process map, branches and dead ends included. Right: per-step drill-down — what
the step did in plain language, which claim it was testing, the verbatim numbers, inline figures and
tables, and a pointer to the code.

## 4. Publish it

```
/submit-ara ara/
```

One command validates the artifact, generates the visualization if it's missing, and uploads it to
the **[ARA Hub](https://www.agenticresearch.sh/)**. You get back one URL — that's what goes in the
submission form, on the poster as a QR code, or in an email.

- **No account needed.** If you have GitHub auth, your artifact lives in a repo you own; if you
  don't, the Hub hosts it directly. Either way you get the same kind of link.
- **Publicly listed on the Hub.**
- **Re-run it to update.** The first submission writes a token into `ara/.ara_env`; every later run
  replaces the same artifact instead of creating a second entry — so the link you pasted into a form
  stays current. Don't delete or commit that file; the token can't be recovered.
- **Allow ~15 minutes** if it has to compile and visualize. Keep the session open.

---

<details>
<summary><b>When it doesn't work</b></summary>

<br/>

| Symptom | Fix |
|---|---|
| The agent never records anything on its own | The routing block is missing — re-run the setup line from §1 at your project root |
| A slash command isn't recognized | `npx @ara-commons/ara-skills@latest install --all` |
| `ara/` is empty after a long session | Say `/research-manager` explicitly, then re-check the setup |
| The compiled ARA states things you disagree with | Edit `ara/logic/` directly — your edits are tagged `user-revised` |
| Publishing reports the upload failed | The artifact isn't on the Hub; re-run `/submit-ara ara/` — it prints the retry command |
| Lost `ara/.ara_env` | The old link is orphaned; `/submit-ara ara/` creates a fresh artifact and a new link |

</details>

---

- Toolkit and skill specs — [github.com/ARA-Labs/Agent-Native-Research-Artifact](https://github.com/ARA-Labs/Agent-Native-Research-Artifact)
- ARA Hub — [agenticresearch.sh](https://www.agenticresearch.sh/)
- Why agent-native research — [The Last Human-Written Paper](https://amberljc.github.io/blog/2026-04-24-the-last-human-written-paper.html)
