#!/usr/bin/env python3
"""Submit an ARA to the Hub: upload it, get a link, keep the token that lets
the next submission replace it rather than duplicate it.

    python3 submit.py ./ara --title "Andes: Defining and Enhancing QoE"

Standard library only, and no account: an author facing a conference deadline
should not have to create one, and a submission that needs a sign-up is a
submission that does not happen. What stands in for auth is the update token
handed back on the first upload. It is written into <ara>/.ara_env, and every
later run of this script finds it there and issues an update, so revising the
work the night before the deadline leaves one artifact with two revisions
instead of two artifacts.

Lose .ara_env and you lose the ability to update that artifact — the token is
stored hashed on the server and cannot be recovered. Keep it out of git; this
script adds it to the ARA's .gitignore on the way out.
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = (os.environ.get("ARA_HUB_API") or "__ARA_BASE__").rstrip("/")
if API_BASE.startswith("__"):
    API_BASE = "https://www.agenticresearch.sh"

# Mirrors of the server's caps (lib/hostedAra.js). Enforced here too so an
# oversized artifact is reported file by file instead of as one 400.
MAX_FILES = 800
MAX_FILE_BYTES = 12 * 1024 * 1024
MAX_TEXT_BYTES = 6 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024

CRED_FILE = ".ara_env"

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".next", ".nuxt", "dist", "build",
    "__pycache__", ".venv", "venv", "env", ".tox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".ipynb_checkpoints", ".terraform",
    "target", ".gradle", ".idea", ".vscode", "wandb",
}
SKIP_NAMES = {
    ".DS_Store", "Thumbs.db", ".npmrc", ".netrc", "credentials",
    "id_rsa", "id_ed25519", "id_dsa", ".git-credentials", CRED_FILE,
}
SKIP_SUFFIXES = {
    ".pyc", ".pyo", ".so", ".dylib", ".o", ".a", ".class", ".lock",
    ".pem", ".key", ".p12", ".pfx", ".keystore", ".crt",
}


def looks_secret(name: str) -> bool:
    lower = name.lower()
    return (
        lower == ".env"
        or lower.startswith(".env.")
        or lower.endswith(".env")
        or "secret" in lower
        or "credential" in lower
    )


def decode_text(data: bytes):
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def collect(root: Path, include_hidden: bool):
    """Walk the ARA into (relative_path, absolute_path) pairs.

    Paths are relative to the ARA directory itself, with no leading folder
    name: the Hub renders <slug>/trajectory.html, so the file has to arrive as
    `trajectory.html` and not `my-ara/trajectory.html`."""
    found, skipped = [], []

    def visit(path: Path, rel: str):
        if path.is_dir():
            for child in sorted(path.iterdir()):
                name = child.name
                if not include_hidden and name.startswith(".") and name != ".gitignore":
                    skipped.append((f"{rel}/{name}" if rel else name, "hidden"))
                    continue
                if child.is_dir() and name in SKIP_DIRS:
                    skipped.append((f"{rel}/{name}" if rel else name, "build/vendor dir"))
                    continue
                visit(child, f"{rel}/{name}" if rel else name)
            return
        if not path.is_file():
            return
        name = path.name
        if name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES:
            skipped.append((rel, "excluded type"))
            return
        if looks_secret(name):
            skipped.append((rel, "looks like a credential"))
            return
        found.append((rel, path))

    visit(root, "")
    return found, skipped


def read_credentials(ara: Path):
    """The slug and token of a previous submission of this same directory."""
    path = ara / CRED_FILE
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def write_credentials(ara: Path, slug: str, token: str, url: str):
    (ara / CRED_FILE).write_text(
        "# ARA Hub submission credentials — written by the submit-ara skill.\n"
        "# ARA_TOKEN is the only way to update this artifact and cannot be\n"
        "# recovered from the server. Keep this file; do not commit it.\n"
        f"ARA_SLUG={slug}\n"
        f"ARA_TOKEN={token}\n"
        f"ARA_URL={url}\n",
        encoding="utf-8",
    )
    try:
        os.chmod(ara / CRED_FILE, 0o600)
    except OSError:
        pass

    # An artifact directory is usually inside a git repo, and a token committed
    # once is a token everyone with read access can use to overwrite the
    # submission. Cheap to prevent here, impossible to take back later.
    ignore = ara / ".gitignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.is_file() else []
    if CRED_FILE not in [l.strip() for l in lines]:
        with ignore.open("a", encoding="utf-8") as fh:
            if lines and lines[-1].strip():
                fh.write("\n")
            fh.write(f"# Hub submission token — never commit this.\n{CRED_FILE}\n")


def paper_metadata(ara: Path):
    """Title and abstract off PAPER.md, so a plain `submit.py ./ara` still
    arrives with the artifact's own name on it rather than a directory slug."""
    paper = ara / "PAPER.md"
    if not paper.is_file():
        return {}
    text = paper.read_text(encoding="utf-8", errors="replace")
    meta = {}

    front = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    body = text[front.end():] if front else text
    if front:
        for line in front.group(1).splitlines():
            key, _, value = line.partition(":")
            key, value = key.strip().lower(), value.strip().strip('"').strip("'")
            if key == "title" and value:
                meta["title"] = value
            elif key in {"abstract", "summary"} and value:
                meta["abstract"] = value

    if "title" not in meta:
        heading = re.search(r"^#\s+(.+)$", body, re.M)
        if heading:
            meta["title"] = heading.group(1).strip()

    if "abstract" not in meta:
        section = re.search(r"^#+\s*abstract\s*$\n+(.+?)(?=\n#|\Z)", body, re.M | re.S | re.I)
        if section:
            meta["abstract"] = " ".join(section.group(1).split())[:1200]

    return meta


def request(method: str, url: str, payload: dict, token: str = None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("x-ara-token", token)
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        try:
            message = json.loads(detail).get("error", detail)
        except json.JSONDecodeError:
            message = detail
        sys.exit(f"error: the Hub refused the submission ({e.code}): {message}")
    except urllib.error.URLError as e:
        sys.exit(f"error: could not reach {API_BASE}: {e.reason}")


def human(n: int) -> str:
    return f"{n / 1024:.1f} KB" if n < 1024 * 1024 else f"{n / 1024 / 1024:.1f} MB"


def main():
    ap = argparse.ArgumentParser(description="Submit an ARA to the Hub.")
    ap.add_argument("path", help="the ARA directory")
    ap.add_argument("--title", help="artifact title (default: from PAPER.md)")
    ap.add_argument("--author", action="append", default=[], help="repeatable")
    ap.add_argument("--domain", default="", help="research area, e.g. 'systems'")
    ap.add_argument("--headline", default="", help="one-sentence finding")
    ap.add_argument("--abstract", default="", help="2-3 sentence overview")
    ap.add_argument("--steps", type=int, help="research steps in the trajectory")
    ap.add_argument("--dead-ends", type=int, help="abandoned branches")
    ap.add_argument("--trajectory", default="trajectory.html", help="the file the Hub renders")
    ap.add_argument("--include-hidden", action="store_true")
    ap.add_argument("--new", action="store_true",
                    help="submit as a separate artifact even though .ara_env exists")
    ap.add_argument("--dry-run", action="store_true", help="list what would go up")
    ap.add_argument("--json", action="store_true", help="print the raw API response")
    args = ap.parse_args()

    ara = Path(args.path).expanduser()
    if not ara.is_dir():
        sys.exit(f"error: not a directory: {args.path}")
    ara = ara.resolve()

    found, skipped = collect(ara, args.include_hidden)
    if not found:
        sys.exit("error: nothing to submit — the directory is empty or entirely excluded.")
    if not any(rel == args.trajectory for rel, _ in found):
        sys.exit(
            f"error: no {args.trajectory} in {ara.name}. The Hub renders that file — "
            "run the research-visualizer skill first."
        )
    if len(found) > MAX_FILES:
        sys.exit(f"error: {len(found)} files (limit {MAX_FILES}).")

    files, total = [], 0
    for rel, path in found:
        raw = path.read_bytes()
        text = decode_text(raw)
        size = len(raw)
        limit = MAX_TEXT_BYTES if text is not None else MAX_FILE_BYTES
        if size > limit:
            sys.exit(f"error: {rel} is {human(size)} (limit {human(limit)}).")
        total += size
        if total > MAX_TOTAL_BYTES:
            sys.exit(f"error: the artifact exceeds {human(MAX_TOTAL_BYTES)}.")
        files.append({"path": rel, "text": text} if text is not None
                     else {"path": rel, "b64": base64.b64encode(raw).decode("ascii")})

    meta = paper_metadata(ara)
    title = args.title or meta.get("title") or ara.name
    payload = {
        "title": title,
        "files": files,
        "authors": args.author,
        "domain": args.domain,
        "headline": args.headline,
        "abstract": args.abstract or meta.get("abstract", ""),
        "trajectory": args.trajectory,
    }
    if args.steps is not None:
        payload["steps"] = args.steps
    if args.dead_ends is not None:
        payload["deadEnds"] = args.dead_ends

    creds = {} if args.new else read_credentials(ara)
    slug, token = creds.get("ARA_SLUG"), creds.get("ARA_TOKEN")
    updating = bool(slug and token)

    # This artifact was published through GitHub, so its files come from the
    # repo and uploading them here would fork it: two Hub entries for one piece
    # of work, diverging from the next push onward.
    if not updating and creds.get("ARA_GITHUB"):
        sys.exit(
            f"error: {ara.name} is already published as {creds['ARA_GITHUB']}. "
            "Update it with git push, then re-register it with POST /api/submit. "
            f"To submit it here as a separate hosted artifact anyway, pass --new."
        )

    if skipped:
        print(f"Left out {len(skipped)} path(s):")
        for rel, why in skipped[:12]:
            print(f"  - {rel} ({why})")
        if len(skipped) > 12:
            print(f"  … and {len(skipped) - 12} more")

    if args.dry_run:
        verb = f"update {slug}" if updating else "create a new artifact"
        print(f"\nWould {verb} with {len(files)} files, {human(total)}:")
        for rel, _ in found[:40]:
            print(f"  {rel}")
        if len(found) > 40:
            print(f"  … and {len(found) - 40} more")
        return

    if updating:
        result = request("PUT", f"{API_BASE}/api/ara/{slug}", payload, token)
    else:
        result = request("POST", f"{API_BASE}/api/ara", payload)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    if not updating:
        write_credentials(ara, result["slug"], result["update_token"], result["url"])

    verb = f"Updated (revision {result.get('revision')})" if updating else "Submitted"
    print(f"\n✓ {verb} — {result.get('file_count')} files, {human(result.get('total_bytes', total))}")
    print(f"\n  {result['url']}\n")
    print(f"  Full screen  {result.get('raw_url', '')}")
    if updating:
        print(f"  Token        reused from {CRED_FILE} — the same URL, replaced in place")
    else:
        print(f"  Token        written to {ara / CRED_FILE} (gitignored)")
        print("               Keep it: it is the only way to update this artifact.")


if __name__ == "__main__":
    main()
