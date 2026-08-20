# Upload & Hub mechanics

Copy-paste-safe procedures for `submit-ara` Steps 4–5. All commands use `git -C` / absolute paths
and never `cd` into the user's tree.

The Hub's canonical base is `https://www.agenticresearch.sh` (`https://www.evolvinglab.ai` serves
the same app). `ARA_HUB_API` overrides it, and exists for local and staging Hubs only — the user
never needs to set it.

---

## `.ara_env` — the file that decides identity

Written into the ARA directory by whichever path published it, and read on every later run. Its
presence means *this artifact already exists somewhere*; creating a second one for the same
directory is a bug unless the user passed `--new`.

```ini
# hosted
ARA_SLUG=Xk3n2Qv8
ARA_TOKEN=<24 random bytes, base64url>
ARA_URL=https://www.agenticresearch.sh/ara/hosted/Xk3n2Qv8

# GitHub-backed
ARA_GITHUB=AmberLJC/ara-andes-defining-and-enhancing-qoe
ARA_URL=https://www.agenticresearch.sh/ara/AmberLJC/ara-andes-defining-and-enhancing-qoe
```

`ARA_TOKEN` is stored hashed server-side and is **not recoverable**. It must never be committed:
the uploader appends `.ara_env` to the ARA's `.gitignore`, and the GitHub path must not stage it
into the repo it pushes.

---

## Hosted path

One command does the whole thing — bundle, upload or update, write `.ara_env`, gitignore it:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/submit.py" "$ARA_DIR" --title "$TITLE"
```

No-install mirror, for a machine without the skill:

```bash
curl -fsSL https://www.agenticresearch.sh/s/submit-ara.py | python3 - "$ARA_DIR" --title "$TITLE"
```

Flags: `--author` (repeatable), `--domain`, `--headline`, `--abstract`, `--steps`, `--dead-ends`,
`--trajectory` (default `trajectory.html`), `--include-hidden`, `--new`, `--dry-run`, `--json`.

### The API underneath

`POST /api/ara` — create. Body is the whole artifact in one JSON request: text files as `text`,
everything else base64 in `b64`.

```json
{
  "title": "Andes: Defining and Enhancing QoE in LLM-Based Text Streaming",
  "files": [
    { "path": "trajectory.html", "text": "<!doctype html>…" },
    { "path": "evidence/figures/fig1.png", "b64": "iVBORw0KG…" }
  ],
  "authors": ["Jiachen Liu", "…"],
  "domain": "Systems / LLM Serving",
  "headline": "one-sentence finding",
  "abstract": "2–3 sentences",
  "steps": 24,
  "deadEnds": 5,
  "trajectory": "trajectory.html"
}
```

`201` returns `{ ok, slug, url, raw_url, manifest_url, update_token, file_count, total_bytes,
revision }`. **`update_token` is shown once.** The bundle is rejected if it has no
`trajectory.html` — the Hub renders that file, and an artifact whose viewer is blank is worse than
a refused submission.

`PUT /api/ara/<slug>` with header `x-ara-token: <token>` — replace the artifact wholesale (not a
merge: files the author deleted actually disappear). Same body, same validation. Returns the new
`revision`.

`GET /api/ara/<slug>` — the manifest: title, revision, and every file with its `raw` URL. Public.

`DELETE /api/ara/<slug>` with the same header — withdraw the artifact and its registry row.

Caps: 800 files, 12 MB per binary, 6 MB per text file, 40 MB total, 50 submissions per IP per day.

---

## GitHub path

### Slug derivation

```bash
# title from PAPER.md frontmatter (between the first --- pair)
TITLE=$(python3 - "$ARA_DIR/PAPER.md" <<'PY'
import sys, re
src = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'^---\s*$(.*?)^---\s*$', src, re.S | re.M)
fm = m.group(1) if m else src
t = re.search(r'^title:\s*"?(.*?)"?\s*$', fm, re.M)
print((t.group(1) if t else "").strip())
PY
)
# kebab-case slug, ascii-only, prefixed, length-capped
SLUG=$(python3 - "$TITLE" "$ARA_DIR" <<'PY'
import sys, re, os
title = sys.argv[1].strip()
base = title or os.path.basename(os.path.normpath(sys.argv[2]))
s = re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')
s = re.sub(r'-{2,}', '-', s)[:46].strip('-')
if not s.startswith('ara-'):
    s = 'ara-' + s
print(s[:50].strip('-'))
PY
)
```

### Preflight

```bash
gh auth status                       # failure is not an error: it means the hosted path
OWNER="${OWNER_OVERRIDE:-$(gh api user -q .login)}"
if gh repo view "$OWNER/$SLUG" >/dev/null 2>&1; then echo EXISTS; else echo NEW; fi
```

An existing repo with no `.ara_env` pointing at it is ambiguous — ask before pushing into it.

### Publish

Stage a **clean copy** — never `git init` inside the user's working tree or `ara-output/`.

```bash
STAGE="$SCRATCH/$SLUG"               # $SCRATCH = the session scratchpad dir
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$ARA_DIR/." "$STAGE/"

# strip anything that must not be published
rm -rf "$STAGE/.git" "$STAGE/.ara_env"

cat > "$STAGE/README.md" <<EOF
# $TITLE

Agent-Native Research Artifact (ARA).

- 🎞️ **Interactive visualization:** open \`trajectory.html\`, or view it rendered at
  https://cdn.jsdelivr.net/gh/$OWNER/$SLUG@main/trajectory.html
- 🌐 **ARA Hub:** https://www.agenticresearch.sh/ara/$OWNER/$SLUG

Compiled with the [ARA toolchain](https://github.com/ARA-Labs/Agent-Native-Research-Artifact).
EOF

# minimal .gitignore — DO NOT ignore trajectory.html
cat > "$STAGE/.gitignore" <<'EOF'
.DS_Store
__pycache__/
*.pyc
node_modules/
.ara_env
EOF

git -C "$STAGE" init -q
git -C "$STAGE" add -A
git -C "$STAGE" commit -q -m "Publish ARA: $TITLE"
git -C "$STAGE" branch -M main

gh repo create "$OWNER/$SLUG" \
  --public \
  --source "$STAGE" \
  --remote origin \
  --push \
  --description "$TITLE — Agent-Native Research Artifact"
```

**Update path** (`.ara_env` carries `ARA_GITHUB`):

```bash
git -C "$STAGE" remote add origin "https://github.com/$OWNER/$SLUG.git"
git -C "$STAGE" push -u origin main --force-with-lease   # tell the user before force-pushing
```

**jsDelivr note:** the CDN caches aggressively. A freshly pushed `trajectory.html` may take a few
minutes to appear, or can be purged via
`https://purge.jsdelivr.net/gh/<owner>/<slug>@main/trajectory.html`. Mention this if the user
reports a stale view right after publishing.

### Register with the Hub

Pushing to GitHub does **not** put the artifact on the Hub; this POST does.

```json
{
  "slug": "ara-andes-defining-and-enhancing-qoe",
  "title": "Andes: Defining and Enhancing Quality-of-Experience in LLM-Based Text Streaming Services",
  "owner": "AmberLJC",
  "repo": "ara-andes-defining-and-enhancing-qoe",
  "branch": "main",
  "domain": "Systems / LLM Serving / User Experience",
  "authors": ["Jiachen Liu", "Jae-Won Chung", "..."],
  "trajectory": "trajectory.html",
  "submittedAt": "2026-06-27"
}
```

Pull `title`, `domain`, `authors` from `PAPER.md` frontmatter. Set `submittedAt` from the date
already in the session — do not fabricate a clock.

```bash
ARA_HUB_API="${ARA_HUB_API:-https://www.agenticresearch.sh}"
# -w prints the status on its own line; do NOT use -f (it hides the response body on errors)
curl -sS -X POST "$ARA_HUB_API/api/submit" \
  -H 'Content-Type: application/json' \
  --data-binary @entry.json \
  -w '\n--- HTTP %{http_code} ---\n'
```

Success is `HTTP 201` with `{"ok":true,"backend":"supabase",…}`. Anything else is a failure: say
the artifact is on GitHub but **not** on the Hub, and print the retry command.

Then write `.ara_env`:

```bash
printf '# ARA Hub submission — written by the submit-ara skill.\nARA_GITHUB=%s/%s\nARA_URL=%s\n' \
  "$OWNER" "$SLUG" "$ARA_HUB_API/ara/$OWNER/$SLUG" > "$ARA_DIR/.ara_env"
grep -qxF '.ara_env' "$ARA_DIR/.gitignore" 2>/dev/null || echo '.ara_env' >> "$ARA_DIR/.gitignore"
```

---

## URL contract

Both paths land on the same route; only the file source differs.

| | GitHub-backed | Hosted |
|---|---|---|
| Hub page | `/ara/<owner>/<repo>` | `/ara/hosted/<slug>` |
| Full-screen viewer | `/raw/<owner>/<repo>/trajectory.html` | `/raw/hosted/<slug>/trajectory.html` |
| Source of the bytes | `raw.githubusercontent.com` (via jsDelivr in-page) | the Hub's own storage |
| Canonical source | the GitHub repo | the artifact itself |

Identity in the registry is `(owner, repo, subdir)`. Hosted artifacts reserve the owner `hosted`
and use the slug as the repo, which is why every route above works for both without a special
case in the viewer.
