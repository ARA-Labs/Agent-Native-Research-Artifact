---
name: submit-ara
description: |
  ARA Submitter. Takes a research directory, makes sure it is a valid Agent-Native Research
  Artifact (ARA) — compiling it with the `compiler` skill when it is not — guarantees it carries
  an interactive visualization (`research-visualizer`), then publishes it to the ARA Hub and hands
  back one link plus an update token. The token is stored in the artifact's own `.ara_env`, so the
  next submission of the same work REPLACES it in place instead of creating a second entry.
  Publishes through the user's GitHub account when they have one, and straight to the Hub when
  they do not — no account required either way.

  TRIGGERS: submit, submit ara, publish ara, upload ara, share ara, push ara to github, add to
  ara hub, submit-ara, publish artifact, make my ara public, submit to a conference,
  update my submission, resubmit
argument-hint: "[ara-dir] [--title <t>] [--hosted] [--github] [--new] [--no-viz] [--dry-run]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(gh *|git *|python3 *|curl *|cat *|ls *|find *|mkdir *|cp *|rm *|test *|basename *|jq *|open *)
metadata:
  author: ara-commons
  category: research-tooling
  version: "2.0.0"
  tags: [research, publishing, ara-hub, conferences, visualization]
---

# ARA Submitter

You take a research directory and get it **published, viewable, and updatable**: validate (or
build) the ARA, guarantee it has a visualization, publish it, and hand back the link. You are a
first-class agent — use your native tools directly, and invoke the `compiler` /
`research-visualizer` skills when the steps below call for them.

## What changed, and why it matters

A submission is not a one-shot event. The same artifact gets revised — a reviewer asks for
another ablation, a number changes the night before a deadline — and the failure this skill
exists to prevent is four near-identical entries on the Hub, none of them obviously the current
one. So **every submission writes an `.ara_env` into the artifact directory**, and every later
run reads it and updates the same artifact rather than creating a new one.

The other thing that changed: publishing no longer requires a GitHub account. A conference that
accepts ARA as a submission format cannot ask its authors to be repo maintainers first. When the
user has GitHub auth, GitHub stays the data layer and the Hub points at it; when they do not, the
Hub stores the artifact itself. **Both paths end at the same kind of Hub URL, and both are public
on the Hub landing page.** Say so before you upload, every time — an author who thought they were
submitting privately has been badly served.

## Set expectations FIRST

Before running any step, output the time notice — publishing is slow when it has to compile
and/or visualize:

> ⏳ **Publishing an ARA can take ~15 minutes.** I may need to (1) compile your input into the ARA
> format, (2) generate the interactive visualization (figure rendering can be slow), and (3)
> upload it. The artifact will be **publicly listed on the ARA Hub**. I'll report progress at each
> step — please keep this session open.

Then announce each step as you start it (`▶ Step 3/5: …`).

## Arguments

- First positional path → the ARA directory (or raw research input). Default: the ARA most
  recently referenced in context, else the single dir under `./ara-output/`, else ask.
- `--title <t>` → artifact title. Default: `PAPER.md`'s title.
- `--hosted` / `--github` → force a route instead of auto-detecting (Step 4).
- `--new` → submit as a separate artifact even though `.ara_env` exists. Rare; say why.
- `--no-viz` → skip visualization (only if the dir already has one).
- `--dry-run` → show what would be uploaded and stop.

## Workflow (5 steps)

```
1. RESOLVE the input directory
2. VALIDATE it is an ARA   → if not, COMPILE with the `compiler` skill
3. VISUALIZE               → ensure trajectory.html, else run `research-visualizer`
4. ROUTE                   → update in place / GitHub / hosted
5. PUBLISH + REPORT        → one link, plus where the token went
```

### Step 1 — Resolve the input

Resolve the argument to an absolute path and confirm it is a directory. Its name and location are
irrelevant; only its structure matters (Step 2). You will never `git init` inside the user's
working tree.

### Step 2 — Validate it is an ARA (compile if not)

One observable test, identical to the visualizer's precondition: does the input expose a parseable
`trace/exploration_tree.yaml` with **≥1 node**, in a standard ARA layout (`PAPER.md`, `logic/`,
`src/`, `trace/`, `evidence/`)?

- **Complete ARA** → Step 3.
- **Not an ARA** (a paper, a repo, run logs, notes) → **invoke the `compiler` skill** to produce
  one under `./ara-output/<slug>/`, then use that. Never hand-roll an ARA.
- **Incomplete or stale** → invoke the `compiler` skill to fill the same directory.

Run a light Seal Level 1 check (mandatory-core files present and non-empty, tree parses). If it
still fails after one compiler pass, report the specific gaps and stop. Never publish a broken
artifact.

### Step 3 — Ensure the visualization

The Hub renders `trajectory.html`, and both publish paths refuse a bundle without one.

- Check `<ara-dir>/trajectory.html`.
- **Missing** (and not `--no-viz`) → invoke the `research-visualizer` skill, writing to
  `<ara-dir>/trajectory.html`. This is usually the slowest step; say it is underway.
- **Present** → keep it; offer to regenerate only if Step 2 changed the ARA.

### Step 4 — Route

Check three things, in this order, and take the first that applies.

1. **`<ara-dir>/.ara_env` exists** → this artifact has been submitted before. Update it in place.
   Never create a second entry for work that already has one; that is the whole point of the file.
   - It carries `ARA_SLUG` + `ARA_TOKEN` → hosted. Re-run the uploader (Step 5); it finds the
     token itself.
   - It carries `ARA_GITHUB=<owner>/<repo>` → GitHub-backed. Push the updated files to that repo
     and re-register (Step 5, GitHub path).
2. **`gh auth status` succeeds** (and no `--hosted`) → the **GitHub path**. The user already has
   the account, so their artifact should live in a repo they own and can cite.
3. **Otherwise** → the **hosted path**. No account, no auth, no prerequisites.

State which route you took and why in one sentence. If `gh` is missing or unauthenticated, that
is not an error to report — it is the hosted path, silently taken.

### Step 5 — Publish and report

**Hosted path.** One command; it bundles the directory, uploads it, writes `.ara_env`, and adds
that file to the ARA's `.gitignore`:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/submit.py" <ara-dir> --title "<title>"
```

Useful flags: `--author` (repeatable), `--domain`, `--headline`, `--abstract`, `--steps`,
`--dead-ends`, `--dry-run`, `--json`. If `${CLAUDE_SKILL_DIR}` is unset, use this skill's own
directory, or the hosted mirror: `curl -fsSL https://www.agenticresearch.sh/s/submit-ara.py |
python3 - <ara-dir>`. A re-run on the same directory updates it; the script prints the revision
number.

**GitHub path.** Exact commands in `${CLAUDE_SKILL_DIR}/references/upload-and-hub.md` §Publish.
In summary: copy the ARA to a scratch dir, add a short `README.md` and a `.gitignore` (keeping
`trajectory.html`, ignoring `.ara_env`), `git init`, then `gh repo create <owner>/<slug> --public
--source <stage> --remote origin --push`. Then register it — `POST /api/submit` with the entry
JSON — and verify the response is 2xx with `ok:true` before claiming it is on the Hub. Write
`ARA_GITHUB=<owner>/<repo>` and `ARA_URL=<hub url>` into `<ara-dir>/.ara_env` so the next run
updates instead of duplicating.

Final report, always:

- 🌐 **Hub**: the artifact URL (this is the link to share or put in a submission form)
- 🎞️ **Full screen**: the `/raw/.../trajectory.html` URL
- 🔑 **Token**: written to `<ara-dir>/.ara_env`, gitignored, unrecoverable if lost — and the one
  thing that makes the next submission an update
- 📊 Stats: claims / experiments / tree nodes / evidence figures, and whether this run compiled,
  visualized, created, or updated

## Critical rules

1. **Set the ~15-minute expectation and the public-listing fact up front** — before any step.
2. **Never publish a broken ARA** — Step 2 must pass (after at most one compiler pass).
3. **`.ara_env` decides identity.** If it exists, you are updating. Creating a second artifact for
   the same directory requires `--new` and an explicit reason said out loud.
4. **Never commit the token.** The uploader gitignores `.ara_env`; on the GitHub path you must not
   stage it into the repo you push.
5. **The token cannot be recovered.** Say this when you print it. A lost `.ara_env` means a new
   artifact and a dead link in whatever form the old one was pasted into.
6. **Publish from a clean copy on the GitHub path** — never `git init` in the user's working tree
   or in `ara-output/`.
7. **trajectory.html ships with the artifact** — it is what the Hub renders; both paths reject a
   bundle without it, and it is never gitignored.
8. **Don't reinvent the builders** — compiling belongs to `compiler`, visualizing to
   `research-visualizer`. This skill orchestrates.
9. **Verify before claiming success** — the hosted upload must return 201/200, the GitHub path's
   `POST /api/submit` must return 2xx with `ok:true`. If it failed, say the artifact is not on the
   Hub and give the retry command.

## Reference files

Load on demand:
- `${CLAUDE_SKILL_DIR}/references/upload-and-hub.md` — the hosted API contract (`POST /api/ara`,
  `PUT /api/ara/<slug>`, the `.ara_env` format), the GitHub publish commands and slug derivation,
  the registry entry schema, and the Hub URL contract.
