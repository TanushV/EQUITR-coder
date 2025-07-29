import asyncio
import os
import tempfile
import venv
from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class RunCommandArgs(BaseModel):
    command: str = Field(..., description="Bash command to execute")
    timeout: int = Field(
        default=120, description="Command timeout in seconds (default: 2 minutes)"
    )
    use_venv: bool = Field(
        default=False, description="Run command in virtual environment"
    )


class RunCommand(Tool):
    def get_name(self) -> str:
        return "run_command"

    def get_description(self) -> str:
        return "Execute bash commands with configurable timeout. Commands run in bash shell with 2-minute default timeout."

    def get_args_schema(self) -> Type[BaseModel]:
        return RunCommandArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Security check - block dangerous commands
            dangerous_commands = [
                "rm -rf /",
                "sudo rm",
                "sudo dd",
                "format",
                "del /",
                "rmdir /s",
                ":(){ :|:& };:",
                "fork()",
                "while true; do",
                "shutdown",
                "reboot",
                "halt",
            ]

            for dangerous in dangerous_commands:
                if dangerous.lower() in args.command.lower():
                    return ToolResult(
                        success=False,
                        error=f"Command contains potentially dangerous pattern: {dangerous}",
                    )

            if args.use_venv:
                return await self._run_in_venv(args.command, args.timeout)
            else:
                return await self._run_bash(args.command, args.timeout)

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _run_bash(self, command: str, timeout: int) -> ToolResult:
        """Run command directly in bash."""
        try:
            # Use bash explicitly
            process = await asyncio.create_subprocess_exec(
                "/bin/bash",
                "-c",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False, error=f"Command timed out after {timeout} seconds"
                )

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            return ToolResult(
                success=process.returncode == 0,
                data={
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "return_code": process.returncode,
                    "command": command,
                    "timeout": timeout,
                },
                error=stderr_str if process.returncode != 0 else None,
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _run_in_venv(self, command: str, timeout: int) -> ToolResult:
        """Run command in a virtual environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "sandbox_venv"

            # Create virtual environment
            venv.create(venv_path, with_pip=True, clear=True)

            # Determine activation script path and command
            if os.name == "nt":  # Windows
                activate_script = venv_path / "Scripts" / "activate.bat"
                full_command = f'"{activate_script}" && {command}'
            else:  # Unix/Linux/macOS
                activate_script = venv_path / "bin" / "activate"
                full_command = f'source "{activate_script}" && {command}'

            try:
                # Use bash for venv commands too
                process = await asyncio.create_subprocess_exec(
                    "/bin/bash",
                    "-c",
                    full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.getcwd(),
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return ToolResult(
                        success=False,
                        error=f"Command timed out after {timeout} seconds",
                    )

                stdout_str = stdout.decode("utf-8", errors="replace")
                stderr_str = stderr.decode("utf-8", errors="replace")

                return ToolResult(
                    success=process.returncode == 0,
                    data={
                        "stdout": stdout_str,
                        "stderr": stderr_str,
                        "return_code": process.returncode,
                        "command": command,
                        "timeout": timeout,
                        "sandboxed": True,
                    },
                    error=stderr_str if process.returncode != 0 else None,
                )

            except Exception as e:
                return ToolResult(success=False, error=str(e))
