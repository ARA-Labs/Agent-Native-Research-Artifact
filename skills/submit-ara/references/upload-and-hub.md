# Upload & Hub mechanics

Detailed, copy-paste-safe procedures for `submit-ara` Steps 4–6. All commands use `git -C` /
absolute paths and never `cd` into the user's tree.

---

## Slug derivation

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

`--name <repo>` overrides `$SLUG`. `--owner <login>` overrides the resolved owner.

---

## Preflight (Step 4)

```bash
gh auth status                       # must succeed; else tell user to: ! gh auth login
OWNER="${OWNER_OVERRIDE:-$(gh api user -q .login)}"
# existence check — non-zero exit means it does not exist
if gh repo view "$OWNER/$SLUG" >/dev/null 2>&1; then
  echo "EXISTS"                      # require --update, or pick a new --name
else
  echo "NEW"
fi
```

---

## Publish (Step 5)

Stage a **clean copy** — never `git init` inside the user's working tree or `ara-output/`.

```bash
STAGE="$SCRATCH/$SLUG"               # $SCRATCH = the session scratchpad dir
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$ARA_DIR/." "$STAGE/"

# strip any nested git metadata that may have been copied in
rm -rf "$STAGE/.git"

# README for the repo (GitHub landing page)
cat > "$STAGE/README.md" <<EOF
# $TITLE

Agent-Native Research Artifact (ARA).

- 🎞️ **Interactive visualization:** open \`trajectory.html\`, or view it rendered at
  https://cdn.jsdelivr.net/gh/$OWNER/$SLUG@main/trajectory.html
- 🌐 **ARA Hub:** ${ARA_HUB_URL:-https://www.evolvinglab.ai}/ara?repo=$OWNER/$SLUG

Compiled with the [ARA toolchain](https://github.com/ARA-Labs/Agent-Native-Research-Artifact).
EOF

# minimal .gitignore — DO NOT ignore trajectory.html
cat > "$STAGE/.gitignore" <<'EOF'
.DS_Store
__pycache__/
*.pyc
node_modules/
EOF

git -C "$STAGE" init -q
git -C "$STAGE" add -A
git -C "$STAGE" commit -q -m "Publish ARA: $TITLE"
git -C "$STAGE" branch -M main

# create + push in one shot (public by default; --private flips this)
gh repo create "$OWNER/$SLUG" \
  --public \
  --source "$STAGE" \
  --remote origin \
  --push \
  --description "$TITLE — Agent-Native Research Artifact"
```

**Update path** (`--update`, repo already exists):

```bash
git -C "$STAGE" remote add origin "https://github.com/$OWNER/$SLUG.git"
git -C "$STAGE" push -u origin main --force-with-lease   # tell the user before force-pushing
```

**jsDelivr note:** the CDN caches aggressively. A freshly pushed or updated `trajectory.html` may
take a few minutes to appear, or can be purged via
`https://purge.jsdelivr.net/gh/<owner>/<slug>@main/trajectory.html`. Mention this if the user reports
a stale view right after publishing.

---

## Register with the Hub (Step 6)

### Registry entry schema

One shared entry shape is used by both `POST /api/submit` (the primary path) and the
`docs/ara-hub/data/registry.json` fallback (shape `{ "artifacts": [ <entry>, ... ] }`). Build one
entry:

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

Pull `title`, `domain`, `authors` from `PAPER.md` frontmatter. `repo` == `$SLUG` unless `--name`
overrode it. Set `submittedAt` from the date the user provides / today's date in context — do not
fabricate a clock (scripts here have no live `date` need; use the date already in the session).

### Registering (zero setup — POST to the live Hub by default)

`ARA_HUB_API` **defaults to the deployed Hub** (`https://www.evolvinglab.ai`), so publishing needs no
configuration from the user. This POST is what makes the ARA appear on the Hub — it is required, not
optional. Write the entry to `entry.json` (use the Write tool or `cat`), then POST it and capture both
the body and the HTTP status so you can verify the Hub accepted it:

```bash
ARA_HUB_API="${ARA_HUB_API:-https://www.evolvinglab.ai}"
# -w prints the status on its own line; do NOT use -f (it hides the response body on errors)
curl -sS -X POST "$ARA_HUB_API/api/submit" \
  -H 'Content-Type: application/json' \
  --data-binary @entry.json \
  -w '\n--- HTTP %{http_code} ---\n'
```

A success looks like `{"ok":true,"backend":"supabase",...}` with `HTTP 201`. Treat anything else
(non-2xx, `ok:false`, connection error) as a failure and use the fallback below. The Hub's
`POST /api/submit` route (see `docs/ara-hub/app/api/submit/route.js`) is the contract: same JSON body,
same fields. Override `ARA_HUB_API` only to target a local/staging Hub.

**Fallback — only if that POST fails** (Hub unreachable or non-2xx): fall back to the local registry
so the submission isn't lost.
- If the hub repo is checked out and `docs/ara-hub/data/registry.json` exists and is writable, read
  it, append the entry to `artifacts` (dedupe by `owner/repo`), write it back.
- Otherwise, print the entry JSON and tell the user to retry, or paste it into that file.

### URL contract

- **GitHub repo:** `https://github.com/<owner>/<slug>`
- **Visualization (CDN, direct):** `https://cdn.jsdelivr.net/gh/<owner>/<slug>@<branch>/trajectory.html`
- **Hub viewer:** `${ARA_HUB_URL:-https://www.evolvinglab.ai}/ara?repo=<owner>/<slug>` (`ARA_HUB_URL`
  defaults to the live Hub `https://www.evolvinglab.ai`). The Hub's `/ara` page resolves `repo` → the
  jsDelivr URL above and embeds it. Keep these three consistent: the Hub viewer is just a framed
  wrapper around the CDN URL plus links back to the repo.
