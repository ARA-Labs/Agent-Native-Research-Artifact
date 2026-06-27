# Contributing to ARA Skills

Thanks for your interest in contributing! This project contains agent skills for structured research knowledge management.

## How to add a new skill

1. Create a directory under `skills/` with your skill name (lowercase, hyphens only):
   ```
   skills/my-skill/
   ├── SKILL.md              # Required — main instructions
   ├── references/           # Optional — detailed docs loaded on demand
   └── templates/            # Optional — starter templates
   ```

2. Write `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: >
     What it does AND when to use it. Include trigger keywords.
     Max 1024 chars. Third person.
   argument-hint: "[optional args description]"
   allowed-tools: Read, Write, Edit, Glob, Grep
   metadata:
     author: your-name
     version: "1.0.0"
     tags: [keyword1, keyword2]
   ---
   ```

3. Keep `SKILL.md` under 500 lines. Move detailed content to `references/`.

4. Reference files should be one level deep only (no chaining `SKILL.md -> file1.md -> file2.md`).

## Quality checklist

Before submitting a PR:

- [ ] `SKILL.md` has `name` and `description` in frontmatter
- [ ] Description is specific and includes trigger keywords
- [ ] Main instructions are under 500 lines
- [ ] References are one level deep from SKILL.md
- [ ] Tested with real usage (not just hypothetical scenarios)
- [ ] No hardcoded paths, API keys, or project-specific references

## How to improve an existing skill

1. Fork and branch
2. Make your changes
3. Test by copying the skill to `~/.claude/skills/` and invoking it
4. Submit a PR with:
   - What you changed
   - Why (what problem or improvement)
   - How you tested it

## Publishing (how skills reach npm)

You do **not** need npm credentials, and you do **not** need to be the package
owner. Publishing is fully automated by CI (`.github/workflows/publish-ara-skills.yml`)
using a repository secret — it runs the same for every contributor.

- Land your skill change on `main` (push or merged PR).
- CI detects the change under `skills/**` and **auto-bumps the patch version**,
  then publishes `@ara-commons/ara-skills` to npm. You don't have to run
  `npm version` yourself.
- Want a deliberate **minor/major** bump instead of an auto patch? Manually set a
  higher version in `packages/ara-skills/package.json` and CI will respect it.

End users then pick up your change with `npx @ara-commons/ara-skills update`.

## Style

- Write instructions for an AI agent, not a human. Be precise about expected outputs.
- Use checklists (`- [ ]`) for multi-step workflows.
- Prefer concrete examples over abstract descriptions.
- Every claim about format should include an example.

## Code of Conduct

Be respectful and constructive. We're building tools to accelerate research — keep that mission in focus.
