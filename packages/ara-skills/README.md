# @ara-commons/ara-skills

One-command installer for the six **Agent-Native Research Artifact (ARA)** skills:

| Skill | Invoke | What it does |
|-------|--------|--------------|
| `compiler`         | `/compiler <input>`        | Convert a paper, repo, or notes into a complete ARA artifact |
| `research-manager` | `/research-manager`        | Post-session recorder that captures decisions, dead ends, and claims |
| `rigor-reviewer`   | `/rigor-reviewer <dir>`    | ARA Seal Level 2 semantic epistemic review across six dimensions |
| `research-visualizer` | `/research-visualizer <dir>` | Render an ARA into one interactive, self-contained trajectory.html |
| `research-foresight` | `/research-foresight <dir> "<query>"` | Ask the ARA anything and get a grounded, falsifiable answer — read-only, no API key |
| `submit-ara`       | `/submit-ara <dir>`        | Validate/compile, visualize, publish to your GitHub, and list on the ARA Hub |

## Quick start

```bash
# interactive (auto-detects Claude Code, Cursor, Gemini CLI, OpenCode, Codex, Hermes)
npx @ara-commons/ara-skills

# install everything to every detected agent (global / user-level)
npx @ara-commons/ara-skills install --all

# install just the compiler to Claude Code
npx @ara-commons/ara-skills install --skill compiler --agent claude-code

# install into the current project instead of $HOME
npx @ara-commons/ara-skills install --all --local
```

## Commands

```
ara-skills                             # interactive
ara-skills install  [--all] [--skill <id>] [--agent <id>] [--local] [--force]
ara-skills update   [--agent <id>] [--local]
ara-skills uninstall [--skill <id>] [--agent <id>] [--local]
ara-skills list                        # what is installed, where
ara-skills skills                      # what's available to install
ara-skills agents                      # which agents are supported / detected
```

All `--skill` and `--agent` flags are repeatable.

## Agent targets

| Agent        | Global dir                    | Local dir                   |
|--------------|-------------------------------|-----------------------------|
| claude-code  | `~/.claude/skills/`           | `.claude/skills/`           |
| cursor       | `~/.cursor/skills/`           | `.cursor/skills/`           |
| gemini-cli   | `~/.gemini/skills/`           | `.gemini/skills/`           |
| opencode     | `~/.opencode/skills/`         | `.opencode/skills/`         |
| codex        | `~/.codex/skills/`            | `.codex/skills/`            |
| hermes       | `~/.hermes/skills/`           | `.hermes/skills/`           |
| generic      | `~/.skills/`                  | `./skills/`                 |

After install, each skill lives at `<target>/<skill-id>/SKILL.md`. A small `.ara-skills.json` lock file records what was installed so `update` and `uninstall --all` work.

## Development

```bash
cd packages/ara-skills
npm install
node bin/cli.js install --skill compiler --local --force
```

In dev mode the CLI reads skills from the sibling `../../skills/` directory. On `npm pack` / `npm publish`, `prepack` copies that directory into `packages/ara-skills/skills/` so the tarball is self-contained; `postpack` removes the copy afterward.

## Upstream source of truth

The six skill directories live at the repo root under `skills/`. Edit them there — never edit the copy inside this package, which is created on demand by `prepack`.
