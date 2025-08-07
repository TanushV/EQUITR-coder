#!/usr/bin/env python3
"""
Generate a comprehensive text report of the repository.

Appends the full contents of a curated set of important files.

Usage (from repo root):
    python generate_repo_report.py [-o OUTPUT_FILE] [--root PATH]

Defaults:
    OUTPUT_FILE: repo_contents.txt
    PATH: current working directory (repo root)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def build_minimal_tree(root: Path, prefix: str = "") -> List[str]:
    """
    Build a minimal tree representation for specified files and directories.
    """
    lines = []
    include_paths = ["equitrcoder", "examples", "README.md", "setup.py"]
    
    # Process top-level entries first
    top_level_entries = sorted(
        [p for p in root.iterdir() if p.name in include_paths],
        key=lambda p: (p.is_file(), p.name.lower())
    )

    for idx, entry in enumerate(top_level_entries):
        connector = "└── " if idx == len(top_level_entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            child_prefix = prefix + ("    " if idx == len(top_level_entries) - 1 else "│   ")
            lines.extend(_build_full_subtree(entry, child_prefix))
            
    return lines

def _build_full_subtree(root: Path, prefix: str) -> List[str]:
    """Helper to build a full directory subtree recursively."""
    lines = []
    try:
        entries = sorted(
            [p for p in root.iterdir() if not p.name.startswith(".")],
            key=lambda p: (p.is_file(), p.name.lower())
        )
    except FileNotFoundError:
        return []

    for idx, entry in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if idx == len(entries) - 1 else "│   "
            lines.extend(_build_full_subtree(entry, prefix + extension))
    return lines


def iter_target_files(root: Path, extensions: Iterable[str]) -> Iterable[Path]:
    """Yield files that match specific inclusion criteria."""
    extensions = tuple(ext.lower() for ext in extensions)

    # Define inclusion rules
    include_dirs = ["equitrcoder", "examples"]
    include_files = ["README.md", "setup.py"]

    # Use a set to avoid yielding duplicates
    yielded_paths = set()

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        # Exclude __pycache__ directories
        if "__pycache__" in path.parts:
            continue

        rel_path_str = str(path.relative_to(root))

        # Check against allowed extensions first
        if path.suffix.lower() not in extensions:
            continue

        is_included = False
        # 1. Check if it's one of the specific root files
        if rel_path_str in include_files:
            is_included = True

        # 2. Check if it's within one of the included directories
        if not is_included:
            for include_dir in include_dirs:
                if rel_path_str.startswith(f"{include_dir}/"):
                    is_included = True
                    break

        if is_included and path not in yielded_paths:
            yielded_paths.add(path)
            yield path


# ----------------------------------------------------------------------------
# Core logic
# ----------------------------------------------------------------------------

def generate_report(root: Path, output: Path) -> None:
    """Generate the repository report at *output* path."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        fh.write("Repository Map:\n")
        fh.write("\n".join(build_minimal_tree(root)))
        fh.write("\n\n")

        extensions = [".py", ".md", ".yaml", ".yml"]
        for file_path in iter_target_files(root, extensions):
            rel_path = file_path.relative_to(root)
            separator = "=" * 80
            fh.write(f"{separator}\n{rel_path}\n{separator}\n")
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception as err:  # pragma: no cover  # In case of read errors
                content = f"<Failed to read file: {err}>\n"
            fh.write(content)
            if not content.endswith("\n"):
                fh.write("\n")
            fh.write("\n")

    print(f"Report generated at: {output}")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a repository report with file contents.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Root directory of the repository (default: current directory)")
    parser.add_argument("-o", "--output", type=Path, default=Path("repo_contents.txt"), help="Output file path (default: repo_contents.txt in current dir)")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    root = args.root.resolve()
    output = args.output.resolve()

    if not root.exists() or not root.is_dir():
        print(f"Error: root path '{root}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    generate_report(root, output)


if __name__ == "__main__":
    main() 