---
name: ara-cli-viewer
description: |
  ARA CLI Viewer. Launches the official `ara` Rust runtime (github.com/ARA-Labs/ara-cli) to
  validate, lint, and serve an Agent-Native Research Artifact (ARA) as a live, local,
  interactive DAG viewer — renders an ARA directly and deterministically, live-reloading on
  every save, with zero LLM calls at view time. Also provide linting to an ARA.

  TRIGGERS: ara serve, live view, local viewer, cli viewer, watch the ara, live-reload,
  validate the ara, lint the ara, ara check, ara validate, check my ara, is this a valid ara,
  view without an llm, deterministic view, serve the artifact locally, browse ara examples,
  ara hub mode, open the ara in a browser, does this ara pass ci
argument-hint: "[ara-dir] [--port <n>] [--hub --ara-root <dir>] [--check] [--fix] [--strict]"
allowed-tools: Read, Glob, Grep, Bash(ara *|which *|curl *|open *|lsof *|pkill *|brew *|cargo *|sleep *)
metadata:
  author: ara-commons
  category: research-tooling
  version: "1.0.0"
  tags: [research, visualization, cli, ara-cli, validation, live-reload]
---

# ARA CLI Viewer

You launch the **official `ara` binary** against an ARA directory. You do not parse YAML,
author narrative, or generate HTML yourself — `ara` does all of that, natively and
deterministically, and re-renders on every save. Your job is orchestration: find the binary,
validate/lint the artifact, start (or stop) the server, and report back a working URL.

## Why this exists next to `research-visualizer`

Both skills show an ARA. They are not redundant — they trade off differently, and reaching for
the wrong one wastes the user's time:

| | `ara-cli-viewer` (this skill) | `research-visualizer` |
|---|---|---|
| Renders via | the `ara` binary, parsing YAML natively | the agent, reading YAML and writing HTML |
| Output | a running local server (live) | one portable static `.html` file |
| LLM calls at view time | zero | none either, but authored once by an LLM |
| Narrative | none — structured fields only | plain-language rewrite of each step |
| Enrichment (glossary, dependencies, recipes) | not supported | supported when present |
| Updates on edit | live-reloads automatically | must be regenerated |
| Needs | the `ara` binary installed | nothing beyond the agent itself |
| Good for | active editing, quick checks, CI gating | sharing, publishing, Hub submission |

If the user is mid-edit on an ARA and wants to see it update as they go, or just wants to know
"does this still validate" — this skill. If they want something to hand to someone else or
publish (`submit-ara` already calls `research-visualizer` for exactly this) — that skill.
If genuinely unsure which the user wants, ask; don't silently pick one.

## Pipeline

1. **Resolve `<ara-dir>`.** Default to the ARA in the current working context or most recently
   referenced. For hub mode (`--hub`), resolve `--ara-root <dir>` instead — a directory whose
   immediate subdirectories are each their own ARA (e.g. this repo's `examples/`).

2. **Confirm the binary exists and its version**: `which ara` then `ara --version`. If missing,
   follow `references/install.md` (Homebrew recommended; Cargo-from-source as a fallback that
   first checks for `cargo`) — never install anything without the user's confirmation first. If
   present, check it against this repo's pinned CI version per `references/install.md` and flag
   (don't silently upgrade) if it's older.

3. **Lint first.** Run `ara check <dir>` (add `--strict` if the user wants warnings to fail
   too). This is cheap and catches the common issues before you spend a cycle on `serve`:
   - Clean → continue.
   - Fixable issues and the user wants them fixed → `ara check <dir> --fix`, then re-run
     `ara check <dir>` to confirm and report exactly what changed.
   - Hard errors (e.g. `<dir>` isn't an ARA at all — no `trace/exploration_tree.yaml`) → this
     is raw research input, not a finished artifact. Say so; this skill only views/lints an
     *existing* ARA. Point the user at the `compiler` skill to build one first (don't build it
     yourself here), then come back to this skill once it exists.
   `--json` on any of `validate`/`check`/`layout` gives a machine-readable report if the user
   wants it piped into something (e.g. a CI step) rather than read directly.

4. **Serve it.** Pick a port (default `8080`; if it's already bound, `lsof -i :<port>` will show
   what's using it — try another port rather than killing an unrelated process). Start in the
   background so you don't block:
   - Single ARA: `ara serve <dir> --port <port>`
   - Many ARAs at once (e.g. the whole `examples/` corpus): `ara serve --hub --ara-root <dir> --port <port>`
   Confirm it actually came up before declaring success — `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:<port>/` should return `200`. Read the process's own stdout line
   (`ara serve: http://…` or `ara serve --hub: http://…`) to get the exact bound URL rather than
   assuming it matched the port you asked for.

5. **Hand it back.** Report the URL, and open it for the user (`open <url>` on macOS, or drive
   it with the browser tools if you have them and the user wants a screenshot/visual check in
   this session). Tell them plainly:
   - It's a **live** server: edits to files under `<dir>` reload the view automatically (add
     `--poll` only if they mention a filesystem where the default watcher misses changes, e.g.
     some network/VM-mounted mounts).
   - It keeps running until stopped — tell them how (`pkill -f "ara serve"`, or however you
     started it) so it doesn't linger as an orphaned process after the conversation ends.

## Boundaries (do not exceed)

- **Never author the view.** If `ara serve` can't render something the user wants (e.g. a
  narrative rewrite, a glossary, figure inlining for sharing), that is `research-visualizer`'s
  job, not a gap to patch by generating HTML yourself here. Say so and hand off.
- **Never silently install software or kill unrelated processes.** Confirm with the user before
  `brew install`/`cargo install`, and before `pkill`-ing anything that isn't the server you
  yourself started this session.
- **Read-only w.r.t. the ARA content itself**, except for `ara check --fix`, which only applies
  `ara`'s own safe, re-parse-guarded format fixes (`ARA001`–`ARA004`) — never hand-edit the
  artifact's files yourself to "fix" a lint issue; that defeats the point of a deterministic
  linter.
- **One ARA (or one `--hub` root) at a time** per invocation; don't chain multiple `serve`
  processes without telling the user each is still running and on which port.

## Verify

No named fixtures required — run against whatever ARA(s) are on hand and confirm:
- `which ara` missing → clear install instructions offered, nothing installed without asking.
- `ara check <dir>` on a clean ARA reports `0 error(s), 0 warning(s)`; on a non-ARA directory it
  fails with a clear "no `trace/exploration_tree.yaml`" error, and you route to `compiler`
  rather than trying to serve it anyway.
- `ara serve <dir> --port <p>` comes up, `curl` returns `200` at the logged URL, and touching a
  file under `<dir>` is reflected without restarting the process.
- `ara serve --hub --ara-root <dir> --port <p>` serves the hub index at `/` and each artifact
  at `/a/<id>/`, both `200`.
- The server is left running only with the user told how to stop it — never silently orphaned.
