"""
Worker Agent with restricted file system access and limited tool set.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from ..tools.base import Tool, ToolResult
from ..tools.builtin.ask_supervisor import AskSupervisor
from ..utils.restricted_fs import RestrictedFileSystem
from .base_agent import BaseAgent


class RestrictedFileTool(Tool):
    """Base class for file tools with restricted access."""

    def __init__(self, file_system: RestrictedFileSystem):
        self.file_system = file_system
        super().__init__()


class ReadFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to read")


class ReadFileTool(RestrictedFileTool):
    """Tool to read files with restricted access."""

    def get_name(self) -> str:
        return "read_file"

    def get_description(self) -> str:
        return "Read content from a file (restricted to allowed paths)"

    def get_args_schema(self) -> Type[BaseModel]:
        return ReadFileArgs

    async def run(self, file_path: str) -> ToolResult:
        if not self.file_system.is_allowed(file_path):
            return ToolResult(
                success=False, error=f"Access denied to file: {file_path}"
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ToolResult(success=True, data=content)
        except Exception as e:
            return ToolResult(
                success=False, error=f"Failed to read file {file_path}: {e}"
            )


class EditFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to edit")
    content: str = Field(..., description="New content for the file")


class EditFileTool(RestrictedFileTool):
    """Tool to edit files with restricted access."""

    def get_name(self) -> str:
        return "edit_file"

    def get_description(self) -> str:
        return "Edit content of a file (restricted to allowed paths)"

    def get_args_schema(self) -> Type[BaseModel]:
        return EditFileArgs

    async def run(self, file_path: str, content: str) -> ToolResult:
        if not self.file_system.is_allowed(file_path):
            return ToolResult(
                success=False, error=f"Access denied to file: {file_path}"
            )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(
                success=True, data=f"File {file_path} updated successfully"
            )
        except Exception as e:
            return ToolResult(
                success=False, error=f"Failed to write file {file_path}: {e}"
            )


class RunCommandArgs(BaseModel):
    cmd: str = Field(..., description="Shell command to execute")


class RunCommandTool(Tool):
    """Tool to run shell commands."""

    def get_name(self) -> str:
        return "run_cmd"

    def get_description(self) -> str:
        return "Run a shell command and return the result"

    def get_args_schema(self) -> Type[BaseModel]:
        return RunCommandArgs

    async def run(self, cmd: str) -> ToolResult:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return ToolResult(
                success=True,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitCommitArgs(BaseModel):
    message: str = Field(..., description="Commit message")


class GitCommitTool(Tool):
    """Tool to perform git commits."""

    def get_name(self) -> str:
        return "git_commit"

    def get_description(self) -> str:
        return "Perform a git commit with the given message"

    def get_args_schema(self) -> Type[BaseModel]:
        return GitCommitArgs

    async def run(self, message: str) -> ToolResult:
        try:
            result = subprocess.run(
                f'git commit -m "{message}"', shell=True, capture_output=True, text=True
            )
            return ToolResult(
                success=True,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WorkerAgent(BaseAgent):
    """Worker agent with restricted file system access and limited tool set."""

    def __init__(
        self,
        worker_id: str,
        scope_paths: List[str],
        allowed_tools: List[str],
        project_root: str = ".",
        provider=None,
        **kwargs,
    ):
        # Initialize base agent
        super().__init__(agent_id=worker_id, **kwargs)

        self.scope_paths = scope_paths
        self.allowed_tools = set(allowed_tools)
        self.project_root = Path(project_root)
        self.provider = provider

        # Initialize restricted components
        self.file_system = RestrictedFileSystem(scope_paths, project_root)

        # Setup restricted tools
        self._setup_restricted_tools()

    def _setup_restricted_tools(self):
        """Setup tools based on allowed_tools list."""
        if "read_file" in self.allowed_tools:
            self.add_tool(ReadFileTool(self.file_system))

        if "edit_file" in self.allowed_tools:
            self.add_tool(EditFileTool(self.file_system))

        if "run_cmd" in self.allowed_tools:
            self.add_tool(RunCommandTool())

        if "git_commit" in self.allowed_tools:
            self.add_tool(GitCommitTool())

        if "ask_supervisor" in self.allowed_tools and self.provider:
            self.add_tool(AskSupervisor(self.provider))

    def can_access_file(self, file_path: str) -> bool:
        """Check if worker can access a file."""
        return self.file_system.is_allowed(file_path)

    def list_allowed_files(self) -> List[str]:
        """List all files the worker can access."""
        return self.file_system.list_allowed_files()

    def get_scope_stats(self) -> Dict[str, Any]:
        """Get statistics about the worker's scope."""
        return {
            "scope_paths": [str(p) for p in self.scope_paths],
            "allowed_tools": list(self.allowed_tools),
            "file_system_stats": self.file_system.get_stats(),
            "project_root": str(self.project_root),
        }

    async def execute_restricted_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with restricted access checks."""
        if tool_name not in self.allowed_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not allowed for worker {self.agent_id}",
            }

        return await self.call_tool(tool_name, **kwargs)

    def add_allowed_path(self, path: str):
        """Add a new allowed path to the worker's scope."""
        self.file_system.add_allowed_path(path)
        if str(Path(path).resolve()) not in self.scope_paths:
            self.scope_paths.append(str(Path(path).resolve()))

    def remove_allowed_path(self, path: str):
        """Remove an allowed path from the worker's scope."""
        self.file_system.remove_allowed_path(path)
        path_str = str(Path(path).resolve())
        if path_str in self.scope_paths:
            self.scope_paths.remove(path_str)

    def get_worker_status(self) -> Dict[str, Any]:
        """Get comprehensive worker status including base agent status."""
        base_status = self.get_status()
        worker_specific = self.get_scope_stats()

        return {**base_status, "worker_specific": worker_specific}
