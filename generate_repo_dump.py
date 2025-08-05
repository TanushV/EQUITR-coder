import os
import pathlib
from typing import List


BASE_DIR = pathlib.Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "repo_dump.txt"
EXCLUDE_DIRS = {"equitr-dev"}

# Only include files with these extensions
ALLOWED_EXTS = {".py", ".md", ".yaml", ".yml"}


def should_exclude_dir(dirname: str) -> bool:
    """Return True if a directory should be excluded from traversal."""
    return dirname.startswith(".") or dirname in EXCLUDE_DIRS


def should_include_file(filename: str) -> bool:
    """Return True if the file has an allowed extension."""
    return pathlib.Path(filename).suffix.lower() in ALLOWED_EXTS


def build_repo_map(start_dir: pathlib.Path) -> List[str]:
    """Return a list of strings representing the tree structure of the repo."""
    map_lines: List[str] = []
    for root, dirs, files in os.walk(start_dir):
        # Mutate dirs in-place to skip excluded directories during traversal
        dirs[:] = [d for d in dirs if not should_exclude_dir(d)]

        rel_root = pathlib.Path(root).relative_to(start_dir)
        indent_level = len(rel_root.parts)
        prefix = "  " * indent_level
        map_lines.append(f"{prefix}{rel_root.name if rel_root.name else '.'}/")
        for f in sorted(files):
            if should_include_file(f):
                map_lines.append(f"{prefix}  {f}")
    return map_lines


def dump_file_contents(start_dir: pathlib.Path, out_handle):
    """Write the contents of each file to the output handle, respecting exclusions."""
    for root, dirs, files in os.walk(start_dir):
        dirs[:] = [d for d in dirs if not should_exclude_dir(d)]
        for f in sorted(files):
            if not should_include_file(f):
                continue

            file_path = pathlib.Path(root) / f
            rel_path = file_path.relative_to(start_dir)
            out_handle.write(f"\n--- {rel_path} ---\n")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as fh:
                    contents = fh.read()
            except Exception as exc:
                contents = f"<Error reading file: {exc}>"
            out_handle.write(contents + "\n")


def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        # Write the repository map
        out.write("=== REPOSITORY MAP ===\n")
        repo_map = build_repo_map(BASE_DIR)
        out.write("\n".join(repo_map))

        # Separator
        out.write("\n\n=== FILE CONTENTS ===\n")
        dump_file_contents(BASE_DIR, out)

    print(f"Repository dump written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main() 