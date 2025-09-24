#!/usr/bin/env python3
"""Command-line interface for markdown2rich."""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown


def render_markdown(content: str, force_terminal: bool = True) -> str:
    """Render markdown content using rich and return as text."""
    console = Console(record=True, force_terminal=force_terminal)
    md = Markdown(content)
    console.print(md)
    return console.export_text()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Render Markdown files using Python's rich library",
        prog="markdown2rich"
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Markdown file to render (default: read from stdin)"
    )

    parser.add_argument(
        "--no-force-terminal",
        action="store_true",
        help="Don't force terminal output (allows rich to auto-detect)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="markdown2rich 0.1.0"
    )

    args = parser.parse_args()

    try:
        # Read input
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File '{args.file}' not found", file=sys.stderr)
                sys.exit(1)
            content = file_path.read_text(encoding="utf-8")
        else:
            content = sys.stdin.read()

        # Render and output
        force_terminal = not args.no_force_terminal
        rendered = render_markdown(content, force_terminal=force_terminal)
        sys.stdout.write(rendered)

    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()