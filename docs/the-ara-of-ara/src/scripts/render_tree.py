#!/usr/bin/env python3
"""CLI: Render an ARA exploration_tree.yaml as interactive HTML.

Usage:
    python render_tree.py <ara_dir>              # writes trace/exploration_tree.html
    python render_tree.py <ara_dir> -o out.html  # custom output path
    python render_tree.py <yaml_file>            # standalone YAML file
"""

import argparse
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

from utils.render_tree import load_tree, load_metadata, render, render_artifact


def main():
    parser = argparse.ArgumentParser(
        description="Render an ARA exploration_tree.yaml as interactive HTML."
    )
    parser.add_argument(
        "path",
        help="Path to an ARA artifact directory or a standalone exploration_tree.yaml",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output HTML path (default: trace/exploration_tree.html inside the artifact)",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="Open the output in the default browser",
    )
    args = parser.parse_args()

    path = Path(args.path).resolve()

    if path.is_dir() and not args.output:
        # Fast path: use render_artifact directly
        out_path = render_artifact(path)
        if out_path is None:
            print(f"Error: {path / 'trace' / 'exploration_tree.yaml'} not found", file=sys.stderr)
            sys.exit(1)
    elif path.is_dir():
        # Directory with custom output
        yaml_path = path / "trace" / "exploration_tree.yaml"
        if not yaml_path.is_file():
            print(f"Error: {yaml_path} not found", file=sys.stderr)
            sys.exit(1)
        tree = load_tree(yaml_path)
        meta = load_metadata(path)
        title = meta.get("title", "")
        domain = meta.get("domain", "")
        subtitle = f"Research DAG &middot; {title}" if title else f"Research DAG &middot; {domain}" if domain else "Research DAG"
        html = render(tree, path.name, subtitle)
        out_path = Path(args.output)
        out_path.write_text(html)
    elif path.is_file() and path.suffix in (".yaml", ".yml"):
        tree = load_tree(path)
        artifact_id = path.parent.parent.name if path.parent.name == "trace" else path.stem
        html = render(tree, artifact_id, "Research DAG")
        out_path = Path(args.output) if args.output else path.with_suffix(".html")
        out_path.write_text(html)
    else:
        print(f"Error: {path} is not a directory or YAML file", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{out_path}")


if __name__ == "__main__":
    main()
