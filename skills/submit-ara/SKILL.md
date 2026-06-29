---
name: submit-ara
description: |
  ARA Submitter / Publisher. Takes a research directory, makes sure it is a valid Agent-Native
  Research Artifact (ARA) — compiling or updating it with the `compiler` skill when it is not —
  guarantees it carries an interactive visualization (running `research-visualizer` to produce
  `trajectory.html` when missing), then publishes it as a public GitHub repository on the
  authenticated user's own account and links it into the ARA Hub website so others can browse and
  replay it. GitHub is the data layer; the Hub fetches from it.

  TRIGGERS: submit, submit ara, publish ara, upload ara, share ara, push ara to github, add to
  ara hub, submit-ara, publish artifact, make my ara public
argument-hint: "[ara-dir] [--name <repo>] [--owner <login>] [--private] [--no-viz] [--update]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(gh *|git *|python3 *|curl *|cat *|ls *|find *|mkdir *|cp *|rm *|test *|basename *|jq *|open *)
metadata:
  author: ara-commons
  category: research-tooling
  version: "1.0.0"
  tags: [research, publishing, github, ara-hub, visualization]
---

# ARA Submitter / Publisher

You take a research directory and get it **published and viewable**: validate (or build) the ARA,
guarantee it has a visualization, push it to the user's own public GitHub repo, and register it with
the ARA Hub. You are a first-class agent — use your native tools (Read, Write, Bash, Glob, Grep)
directly, and invoke the `compiler` / `research-visualizer` skills when this skill's steps call for
them.

## Set expectations FIRST (do this before anything else)

The first thing you output, before running any step, is a clear time notice — publishing is slow
when it has to compile and/or visualize:

> ⏳ **Publishing an ARA can take ~15 minutes.** I may need to (1) compile your input into the ARA
> format, (2) generate the interactive visualization (figure rendering can be slow), and (3) create
> and push a GitHub repository. I'll report progress at each step — please be patient and keep this
> session open.

Then announce each of the 6 steps as you start it (`▶ Step 2/6: …`) so the user can follow along.

## Arguments

Interpret `$ARGUMENTS` flexibly:
- First positional path → the ARA directory (or raw research input). Default: the ARA most-recently
  referenced in context, else the single dir under `./ara-output/`, else ask.
- `--name <repo>` → override the GitHub repo name (default: derived slug, see Step 4).
- `--owner <login>` → override the GitHub account to publish under (default: the authenticated
  `gh` user).
- `--private` → create a private repo (default: **public** — the Hub can only fetch public repos).
- `--no-viz` → skip visualization (only if the dir already has one, or the user opts out).
- `--update` → the repo already exists; update it in place instead of failing on "already exists".

## Workflow (6 steps)

```
1. RESOLVE the input directory
2. VALIDATE it is an ARA  → if not (or incomplete), COMPILE / UPDATE with the `compiler` skill
3. VISUALIZE → ensure trajectory.html exists; if not, run the `research-visualizer` skill
4. PREFLIGHT GitHub → gh auth, resolve owner + repo slug
5. PUBLISH → create the public repo and push the ARA (incl. trajectory.html)
6. REGISTER + REPORT → emit a Hub registry entry; print repo URL + Hub viewer URL
```

### Step 1 — Resolve the input

Resolve the directory argument to an absolute path. Confirm it exists and is a directory. The
directory's **name and location are irrelevant** — it can live anywhere (inside this repo's working
tree, under `ara-output/`, or any other path) and be named anything. The only thing that matters is
that it carries a valid ARA structure (verified in Step 2). Regardless of where it lives, you'll
always publish a **clean copy** and never `git init` inside the user's working tree.

### Step 2 — Validate it is an ARA (compile/update if not)

Use ONE observable test, identical to the visualizer's precondition: does the input expose a
parseable `trace/exploration_tree.yaml` with **≥1 node**, in a standard ARA layout (`PAPER.md`,
`logic/`, `src/`, `trace/`, `evidence/`)?

- **It is a complete ARA** → continue to Step 3.
- **It is not an ARA** (raw paper/PDF, repo, run logs, notes, or a dir with no exploration tree) →
  **invoke the `compiler` skill on it** to produce an ARA under `./ara-output/<slug>/`, then set the
  ARA dir to the compiler's output. Do not hand-roll an ARA — the compiler is the only builder.
- **It is an ARA but incomplete or stale** (missing mandatory-core files, or the user passed
  `--update` after editing sources) → **invoke the `compiler` skill to update/fill** the same
  directory, then continue.

Run a light Seal Level 1 sanity check (mandatory-core dirs/files present and non-empty; tree
parses). If it still fails after a compiler pass, surface the specific gaps and stop — do not
publish a broken artifact.

### Step 3 — Ensure the visualization

The Hub's value is the step-by-step replay, so every published ARA must ship its visualization.

- Check for a self-contained visualization at `<ara-dir>/trajectory.html` (this is the
  `research-visualizer` default output).
- **Missing** (and not `--no-viz`) → **invoke the `research-visualizer` skill** with the ARA dir,
  writing to `<ara-dir>/trajectory.html`. This is typically the slowest step (figure inlining /
  rendering) — tell the user it's underway.
- **Present** → keep it. Offer to regenerate only if the ARA changed in Step 2.

`trajectory.html` is single-file and self-contained, so the Hub can load it straight from the
published repo over a CDN (no server, no build). It MUST be included in what you push in Step 5.

### Step 4 — Preflight GitHub

- Run `gh auth status`. If not authenticated, STOP and tell the user to authenticate first —
  suggest they run `! gh auth login` in this session (the `!` prefix runs it inline). Do not try to
  log in for them.
- Resolve **owner**: `--owner` if given, else `gh api user -q .login` (the user's own account — this
  is the default by design: every user publishes to the account they already hold auth for).
- Resolve **repo slug**: `--name` if given, else derive from `PAPER.md` `title:` →
  kebab-case, strip punctuation, prefix `ara-`, cap length (~50 chars). Fallback: the ARA dir
  basename. Example: *"Andes: Defining and Enhancing QoE…"* → `ara-andes-defining-and-enhancing-qoe`.
- Check existence: `gh repo view "<owner>/<slug>"`. If it exists and `--update` was NOT passed,
  ask the user whether to update it or pick a new name — don't clobber silently.

### Step 5 — Publish to GitHub

Publish a **clean copy** of the ARA dir as a new public repo. Never run `git init` inside the user's
working tree or inside `ara-output/`. Full command sequence (copy-paste-safe, idempotent) is in
`${CLAUDE_SKILL_DIR}/references/upload-and-hub.md` §Publish. In summary:

1. Copy the ARA dir into a scratch staging dir.
2. Add a short `README.md` (title + abstract + a "View on ARA Hub" link) and a `.gitignore`
   (`trajectory.html` stays — do NOT ignore it).
3. `git init`, commit, branch `main`.
4. `gh repo create "<owner>/<slug>" --public --source <stage> --remote origin --push
   --description "<title> — Agent-Native Research Artifact"`.

The default branch is `main`; the Hub fetches `trajectory.html` from `main` via jsDelivr.

### Step 6 — Register with the Hub + report

The Hub only learns a new ARA exists when this skill **tells** it via the submit API. Registration is
a **REQUIRED step, not optional** — a published repo that is never registered will never appear on the
Hub landing page. Details in `${CLAUDE_SKILL_DIR}/references/upload-and-hub.md` §Register.

- **Always POST — zero setup required**: build the entry JSON (schema in the reference) and `curl` it
  to `${ARA_HUB_API:-https://www.evolvinglab.ai}/api/submit` with `Content-Type: application/json`.
  `ARA_HUB_API` defaults to the live Hub (`https://www.evolvinglab.ai`); the user does **not** need to
  set anything. Only override it to target a local/staging Hub.
- **Verify the response**: a success is HTTP `201` with `{"ok":true,"backend":"supabase"}`. Print the
  HTTP status and `ok`/`backend` so it is visible the Hub actually accepted it. Do not claim the ARA is
  "on the Hub" unless this POST returned 2xx.
- **Fallback** — only if that POST fails (Hub unreachable, non-2xx, or `ok:false`): say so explicitly,
  print the entry JSON so the user can retry, and, when the hub repo (`docs/ara-hub/`) is checked out
  locally and writable, append the entry to `docs/ara-hub/data/registry.json` (the `artifacts` array).

Final report (always print these):
- ✅ **GitHub repo**: `https://github.com/<owner>/<slug>`
- 🎞️ **Visualization (direct)**: `https://cdn.jsdelivr.net/gh/<owner>/<slug>@main/trajectory.html`
- 🌐 **ARA Hub viewer**: `${ARA_HUB_URL:-https://www.evolvinglab.ai}/ara?repo=<owner>/<slug>`
  (`ARA_HUB_URL` defaults to the live Hub at `https://www.evolvinglab.ai`)
- 📊 Stats: claims / experiments / tree nodes / evidence figures, and whether the ARA was compiled
  or visualized in this run.

## Critical rules

1. **Set the ~15-minute expectation up front** — before any step, every time.
2. **Never publish a broken ARA** — Step 2's validation must pass (after at most one compiler pass)
   before Step 5. If it can't, report the gaps and stop.
3. **Publish from a clean copy** — never `git init` in the user's working tree or in `ara-output/`;
   stage to scratch, then push.
4. **Public by default** — the Hub can only fetch public repos; warn explicitly if `--private`.
5. **The user's own account is the default owner** — they hold the auth; GitHub is the shared data
   layer. Only override with `--owner`.
6. **trajectory.html ships with the repo** — it is the thing the Hub renders. Generate it (Step 3)
   and include it in the push (Step 5); never `.gitignore` it.
7. **Don't reinvent the builders** — compiling is the `compiler` skill's job, visualizing is the
   `research-visualizer` skill's job. This skill orchestrates; it does not hand-roll either output.
8. **Idempotent + non-destructive** — check repo existence before creating; require `--update` to
   touch an existing repo; never force-push without telling the user.
9. **Registration is mandatory and verified** — Step 6's `POST /api/submit` is what makes the ARA show
   up on the Hub; it is not optional. Confirm it returned HTTP 2xx with `ok:true` before reporting
   success. If it failed, say the ARA is published to GitHub but **not yet on the Hub**, and give the
   retry command. Pushing to GitHub alone does NOT put it on the landing page.

## Reference files

Load on demand:
- `${CLAUDE_SKILL_DIR}/references/upload-and-hub.md` — exact gh/git publish commands, slug
  derivation, the Hub registry entry schema + jsDelivr/Hub URL contract, and the database seam.
