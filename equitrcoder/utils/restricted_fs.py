"""
Restricted file system utilities for secure agent operations.
"""
import fnmatch
from pathlib import Path
from typing import List, Set


class RestrictedFileSystem:
    """File system access control for agents with restricted scope."""
    
    def __init__(self, allowed_paths: List[str], project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
        self.allowed_files: Set[Path] = set()
        self._build_allowed_files()

    def _build_allowed_files(self):
        """Build set of allowed files based on scope paths."""
        for path in self.allowed_paths:
            if path.is_file():
                self.allowed_files.add(path)
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        self.allowed_files.add(file_path)

    def is_allowed(self, file_path: str) -> bool:
        """Check if a file path is allowed."""
        try:
            resolved_path = Path(file_path).resolve()

            # Check if it's within any allowed path
            for allowed_path in self.allowed_paths:
                try:
                    resolved_path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue

            # Check exact file match
            return resolved_path in self.allowed_files
        except Exception:
            return False

    def list_allowed_files(self) -> List[str]:
        """List all allowed files."""
        return [str(p) for p in sorted(self.allowed_files)]

    def glob_files(self, pattern: str) -> List[str]:
        """Find files matching pattern within allowed paths."""
        matches = []
        for allowed_path in self.allowed_paths:
            if allowed_path.is_dir():
                for file_path in allowed_path.rglob(pattern):
                    if file_path.is_file() and self.is_allowed(str(file_path)):
                        matches.append(str(file_path))
            elif allowed_path.is_file() and fnmatch.fnmatch(allowed_path.name, pattern):
                matches.append(str(allowed_path))
        return sorted(matches)

    def get_relative_path(self, file_path: str) -> str:
        """Get relative path from project root if file is allowed."""
        if not self.is_allowed(file_path):
            raise PermissionError(f"Access denied to file: {file_path}")
        
        resolved_path = Path(file_path).resolve()
        try:
            return str(resolved_path.relative_to(self.project_root))
        except ValueError:
            return str(resolved_path)

    def validate_write_access(self, file_path: str) -> bool:
        """Check if file can be written to (must be in allowed paths)."""
        return self.is_allowed(file_path)

    def add_allowed_path(self, path: str):
        """Add a new allowed path and rebuild file list."""
        new_path = Path(path).resolve()
        if new_path not in self.allowed_paths:
            self.allowed_paths.append(new_path)
            self._build_allowed_files()

    def remove_allowed_path(self, path: str):
        """Remove an allowed path and rebuild file list."""
        path_to_remove = Path(path).resolve()
        if path_to_remove in self.allowed_paths:
            self.allowed_paths.remove(path_to_remove)
            self._build_allowed_files()

    def get_stats(self) -> dict:
        """Get statistics about the restricted file system."""
        return {
            "allowed_paths": len(self.allowed_paths),
            "allowed_files": len(self.allowed_files),
            "project_root": str(self.project_root)
        } 