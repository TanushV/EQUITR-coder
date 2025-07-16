import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch

from src.tools.ask_supervisor import create_ask_supervisor_tool


class RestrictedFileSystem:
    def __init__(self, allowed_paths: List[str], project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
        self.allowed_files = set()
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


class RestrictedToolRegistry:
    def __init__(self, allowed_tools: List[str]):
        self.allowed_tools = set(allowed_tools)
        self.tool_registry = {}
        self._setup_tools()

    def _setup_tools(self):
        """Setup available tools based on allowed_tools."""
        if "read_file" in self.allowed_tools:
            self.tool_registry["read_file"] = self._read_file
        if "edit_file" in self.allowed_tools:
            self.tool_registry["edit_file"] = self._edit_file
        if "run_cmd" in self.allowed_tools:
            self.tool_registry["run_cmd"] = self._run_cmd
        if "git_commit" in self.allowed_tools:
            self.tool_registry["git_commit"] = self._git_commit
        if "ask_supervisor" in self.allowed_tools:
            self.tool_registry["ask_supervisor"] = create_ask_supervisor_tool()

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if a tool can be used."""
        return tool_name in self.allowed_tools

    def get_tool(self, tool_name: str):
        """Get a tool by name."""
        return self.tool_registry.get(tool_name)

    def _read_file(self, file_path: str) -> str:
        """Read file content (restricted)."""
        if not hasattr(self, "file_system"):
            raise RuntimeError("File system not initialized")

        if not self.file_system.is_allowed(file_path):
            raise PermissionError(f"Access denied to file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {file_path}: {e}")

    def _edit_file(self, file_path: str, content: str):
        """Edit file content (restricted)."""
        if not hasattr(self, "file_system"):
            raise RuntimeError("File system not initialized")

        if not self.file_system.is_allowed(file_path):
            raise PermissionError(f"Access denied to file: {file_path}")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise RuntimeError(f"Failed to write file {file_path}: {e}")

    def _run_cmd(self, cmd: str) -> Dict[str, Any]:
        """Run command (restricted)."""
        import subprocess

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"error": str(e)}

    def _git_commit(self, message: str) -> Dict[str, Any]:
        """Git commit (restricted)."""
        return self._run_cmd(f'git commit -m "{message}"')


class WorkerAgent:
    def __init__(
        self,
        worker_id: str,
        scope_paths: List[str],
        allowed_tools: List[str],
        project_root: str = ".",
    ):
        self.worker_id = worker_id
        self.scope_paths = scope_paths
        self.allowed_tools = allowed_tools
        self.project_root = Path(project_root)

        # Initialize restricted components
        self.file_system = RestrictedFileSystem(scope_paths, project_root)
        self.tool_registry = RestrictedToolRegistry(allowed_tools)

        # Connect file system to tool registry
        self.tool_registry.file_system = self.file_system

        # Initialize supervisor tool
        if "ask_supervisor" in allowed_tools:
            self.ask_supervisor = create_ask_supervisor_tool()

    def get_status(self) -> Dict[str, Any]:
        """Get worker status."""
        return {
            "worker_id": self.worker_id,
            "scope_paths": self.scope_paths,
            "allowed_tools": self.allowed_tools,
            "allowed_files_count": len(self.file_system.allowed_files),
            "available_tools": list(self.tool_registry.tool_registry.keys()),
        }

    def can_access_file(self, file_path: str) -> bool:
        """Check if worker can access a file."""
        return self.file_system.is_allowed(file_path)

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if worker can use a tool."""
        return self.tool_registry.can_use_tool(tool_name)

    def list_allowed_files(self) -> List[str]:
        """List all files the worker can access."""
        return self.file_system.list_allowed_files()

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool with given arguments."""
        if not self.can_use_tool(tool_name):
            raise PermissionError(
                f"Tool '{tool_name}' not allowed for worker {self.worker_id}"
            )

        tool = self.tool_registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found")

        return tool(**kwargs)
