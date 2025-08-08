from pathlib import Path
from typing import List, Optional, Type, Dict, Any
import fnmatch
import re

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator

from ..base import Tool, ToolResult


class GrepSearchArgs(BaseModel):
    pattern: str = Field(..., description="Regex pattern to search for")
    path: str = Field(default=".", description="Base directory to search from (relative or absolute)")
    include: Optional[str] = Field(default=None, description="Glob pattern to include (e.g., '*.py')")
    exclude: Optional[str] = Field(default=None, description="Glob pattern to exclude (e.g., 'node_modules/*')")
    case_sensitive: bool = Field(default=False, description="Whether the search is case sensitive")
    max_results: int = Field(default=200, ge=1, le=5000, description="Maximum number of matches to return")

    @field_validator("path")
    @classmethod
    def _validate_path(cls, v: str) -> str:
        # Disallow traversal attempts
        if not v:
            return "."
        p = Path(v)
        if ".." in v:
            raise ValueError("Path traversal not allowed. Use a safe, relative path.")
        real = None
        try:
            real = p.resolve()
        except Exception:
            # If resolve fails, keep original and let later checks handle it
            pass
        if real is not None:
            real_posix = real.as_posix()
            # Block sensitive system directories
            blocked_prefixes = [
                "/etc",
                "/private/etc",
                "/proc",
                "/sys",
                "/dev",
            ]
            for bp in blocked_prefixes:
                if real_posix == bp or real_posix.startswith(bp + "/"):
                    raise ValueError("Path traversal not allowed. Use a safe project or temp directory.")
        return v


class GrepSearch(Tool):
    """Read-only recursive search tool for text files.

    Scans files under a base directory and returns lines matching a regex pattern.
    Skips binary and very large files. Honors include/exclude glob filters.
    """

    def get_name(self) -> str:
        return "grep_search"

    def get_description(self) -> str:
        return (
            "Search recursively for a regex pattern in text files with optional include/exclude filters."
        )

    def get_args_schema(self) -> Type[BaseModel]:
        return GrepSearchArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

        base_path = Path(args.path)
        if not base_path.exists() or not base_path.is_dir():
            return ToolResult(success=False, error=f"Directory {base_path} does not exist or is not a directory")

        # Compile regex
        flags = 0 if args.case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(args.pattern, flags)
        except re.error as e:
            return ToolResult(success=False, error=f"Invalid regex pattern: {e}")

        # Directories to skip
        skip_dirs = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}

        matches: List[Dict[str, Any]] = []
        files_scanned = 0

        def should_include(file_path: Path) -> bool:
            rel = str(file_path)
            if args.include and not fnmatch.fnmatch(rel, args.include):
                return False
            if args.exclude and fnmatch.fnmatch(rel, args.exclude):
                return False
            return True

        # Walk directory manually to apply dir skips
        stack = [base_path]
        while stack and len(matches) < args.max_results:
            current = stack.pop()
            try:
                for entry in current.iterdir():
                    if entry.is_dir():
                        if entry.name in skip_dirs:
                            continue
                        stack.append(entry)
                        continue

                    # File
                    if not should_include(entry):
                        continue

                    # Skip very large files (>1.5MB)
                    try:
                        if entry.stat().st_size > 1_500_000:
                            continue
                    except OSError:
                        continue

                    # Read safely and detect binary
                    try:
                        with entry.open("rb") as fb:
                            chunk = fb.read(4096)
                            if b"\x00" in chunk:
                                # Likely binary
                                continue
                        # Read as text (ignore errors)
                        content = entry.read_text(encoding="utf-8", errors="ignore")
                    except (OSError, UnicodeError):
                        continue

                    files_scanned += 1

                    # Search line by line for performance and accurate line numbers
                    for i, line in enumerate(content.splitlines(), start=1):
                        if regex.search(line):
                            matches.append({
                                "path": str(entry),
                                "line_number": i,
                                "line": line
                            })
                            if len(matches) >= args.max_results:
                                break
            except PermissionError:
                continue

        return ToolResult(
            success=True,
            data={
                "base_path": str(base_path),
                "pattern": args.pattern,
                "case_sensitive": args.case_sensitive,
                "matches": matches,
                "total_matches": len(matches),
                "files_scanned": files_scanned,
            },
        ) 