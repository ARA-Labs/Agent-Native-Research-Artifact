#!/usr/bin/env python3
"""Upload a file or a folder as a context drop and print the prompt to send.

    python3 drop.py ./my-notes --title "Loss spike"

The `context-drop` skill runs this; you can also run it directly. Standard
library only, on purpose — it has to work on a machine with nothing installed
but Python 3.

The whole bundle goes up in one JSON POST: text files as text, everything else
base64. That costs a third more bytes on binaries and buys a single request
with nothing half-uploaded to reconcile if it fails.

The ARA Hub serves a mirror of this file at https://www.agenticresearch.sh/s/drop.py
for people who have not installed the skill, with the hub's own origin baked
in. This copy ships inside the skill so installing it does not amount to
agreeing to run whatever is at that URL later.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Override with DROP_API to point at a different hub (a preview deployment, a
# self-hosted one). The mirror served by the hub substitutes its own origin
# here; this copy names the public one.
API_BASE = (os.environ.get("DROP_API") or "https://www.agenticresearch.sh").rstrip("/")

# Mirrors of the server's caps. Enforced here too so an oversized
# folder is reported file by file instead of coming back as one 400.
MAX_FILES = 400
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024

# Things nobody means to share. Build output and dependency trees are noise the
# recipient's agent would have to read past; the credential patterns are the
# reason this list is not merely a convenience.
SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".next", ".nuxt", "dist", "build",
    "__pycache__", ".venv", "venv", "env", ".env.d", ".tox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".ipynb_checkpoints", ".terraform",
    "target", ".gradle", ".idea", ".vscode", ".DS_Store", "wandb",
}
SKIP_NAMES = {
    ".DS_Store", "Thumbs.db", ".npmrc", ".netrc", "credentials",
    "id_rsa", "id_ed25519", "id_dsa", ".git-credentials",
}
SKIP_SUFFIXES = {
    ".pyc", ".pyo", ".so", ".dylib", ".o", ".a", ".class", ".lock",
    ".pem", ".key", ".p12", ".pfx", ".keystore", ".crt",
}


def looks_secret(name: str) -> bool:
    """A file whose name says it holds credentials. Skipped and announced —
    silently including someone's .env in a link they paste into a group chat is
    the one failure this tool must not have."""
    lower = name.lower()
    return (
        lower == ".env"
        or lower.startswith(".env.")
        or lower.endswith(".env")
        or "secret" in lower
        or "credential" in lower
    )


def decode_text(data: bytes):
    """Return the file as text, or None if it is binary. NUL bytes settle it
    for anything UTF-8 would otherwise accept."""
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def collect(roots, include_hidden: bool):
    """Walk the given paths into (relative_path, absolute_path) pairs.

    A folder keeps its own name as the top segment, so `drop ./results` arrives
    as results/loss.csv rather than a bare loss.csv — the folder name is often
    the only thing saying what the files are."""
    found, skipped = [], []

    def visit(path: Path, rel: str):
        if path.is_dir():
            for child in sorted(path.iterdir()):
                name = child.name
                if not include_hidden and name.startswith(".") and name not in {".gitignore"}:
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

    for root in roots:
        p = Path(root).expanduser()
        if not p.exists():
            sys.exit(f"error: no such path: {root}")
        p = p.resolve()
        visit(p, p.name if p.is_dir() else p.name)

    return found, skipped


def build_bundle(found):
    files, oversize = [], []
    total = 0
    for rel, path in found:
        data = path.read_bytes()
        text = decode_text(data)
        limit = MAX_TEXT_BYTES if text is not None else MAX_FILE_BYTES
        if len(data) > limit:
            oversize.append((rel, len(data)))
            continue
        if total + len(data) > MAX_TOTAL_BYTES:
            oversize.append((rel, len(data)))
            continue
        total += len(data)
        if text is not None:
            files.append({"path": rel, "text": text})
        else:
            files.append({"path": rel, "b64": base64.b64encode(data).decode("ascii")})
        if len(files) >= MAX_FILES:
            break
    return files, total, oversize


def human(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def post(payload: dict) -> dict:
    request = urllib.request.Request(
        f"{API_BASE}/api/drops",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "context-drop/1"},
        method="POST",
    )
    token = os.environ.get("DROP_TOKEN")
    if token:
        request.add_header("x-drop-token", token)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        try:
            message = json.loads(body).get("error", body)
        except json.JSONDecodeError:
            message = body
        sys.exit(f"error: upload failed ({error.code}): {message}")
    except urllib.error.URLError as error:
        sys.exit(f"error: could not reach {API_BASE}: {error.reason}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="drop",
        description="Share a file or folder as one URL an agent can read.",
    )
    parser.add_argument("paths", nargs="+", help="files or folders to share")
    parser.add_argument("--title", help="what this drop is (defaults to the folder name)")
    parser.add_argument("--note", help="one line of context for the reader")
    parser.add_argument("--from", dest="sender", help="who it is from")
    parser.add_argument("--days", type=int, default=30, help="days before it expires (default 30)")
    parser.add_argument("--include-hidden", action="store_true", help="include dotfiles")
    parser.add_argument("--dry-run", action="store_true", help="list what would go up, send nothing")
    parser.add_argument("--json", action="store_true", help="print the raw API response")
    args = parser.parse_args()

    found, skipped = collect(args.paths, args.include_hidden)
    if not found:
        sys.exit("error: nothing to share — every file was empty, hidden, or excluded.")

    if args.dry_run:
        for rel, path in found:
            print(f"  {rel}  ({human(path.stat().st_size)})")
        print(f"\n{len(found)} files would go up. Skipped {len(skipped)}.")
        return

    files, total, oversize = build_bundle(found)
    if not files:
        sys.exit("error: every file was over the size limit.")

    title = args.title or Path(args.paths[0]).expanduser().resolve().name
    result = post(
        {
            "title": title,
            "note": args.note,
            "sender": args.sender,
            "days": args.days,
            "files": files,
        }
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return

    secrets = [rel for rel, why in skipped if why == "looks like a credential"]
    print(f"\n✓ {len(files)} files, {human(total)} → {result['url']}\n")
    print(f"  Markdown  {result['md_url']}")
    print(f"  Expires   {result['expires_at'][:10]}")
    print(
        f"  Delete    curl -X DELETE -H \"x-drop-token: {result['delete_token']}\" "
        f"{API_BASE}/api/drops/{result['slug']}"
    )
    if secrets:
        print(f"\n  Left out (looked like credentials): {', '.join(secrets)}")
    if oversize:
        print(f"\n  Left out (too large): {', '.join(rel for rel, _ in oversize)}")

    print("\n─── send this ───────────────────────────────────────────────")
    print(result["prompt"])
    print("─────────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
