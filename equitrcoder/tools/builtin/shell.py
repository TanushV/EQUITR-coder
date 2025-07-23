import asyncio
import os
import tempfile
import venv
from pathlib import Path
from typing import Type
from pydantic import BaseModel, Field
from ..base import Tool, ToolResult


class RunCommandArgs(BaseModel):
    command: str = Field(..., description="Shell command to execute")
    timeout: int = Field(default=30, description="Command timeout in seconds")
    use_venv: bool = Field(
        default=True, description="Run command in virtual environment"
    )


class RunCommand(Tool):
    def get_name(self) -> str:
        return "run_command"

    def get_description(self) -> str:
        return "Execute shell commands in a sandboxed environment. For complex system analysis, debugging intricate issues, or when understanding command outputs requires deep technical insight, use a stronger reasoning model to interpret results and suggest optimal solutions."

    def get_args_schema(self) -> Type[BaseModel]:
        return RunCommandArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Security check - block dangerous commands
            dangerous_commands = [
                "rm -rf",
                "sudo",
                "su",
                "chmod +x",
                "dd if=",
                "format",
                "del /",
                "rmdir /s",
                ":(){ :|:& };:",
                "fork()",
                "while true",
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
                return await self._run_direct(args.command, args.timeout)

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _run_in_venv(self, command: str, timeout: int) -> ToolResult:
        """Run command in a virtual environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "sandbox_venv"

            # Create virtual environment
            venv.create(venv_path, with_pip=True, clear=True)

            # Determine activation script path
            if os.name == "nt":  # Windows
                activate_script = venv_path / "Scripts" / "activate.bat"
                shell_cmd = f'"{activate_script}" && {command}'
                shell = True
            else:  # Unix/Linux/macOS
                activate_script = venv_path / "bin" / "activate"
                shell_cmd = f'source "{activate_script}" && {command}'
                shell = ["/bin/bash", "-c", shell_cmd]

            try:
                process = await asyncio.create_subprocess_exec(
                    *shell if isinstance(shell, list) else shell_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.getcwd(),
                    shell=isinstance(shell, bool) and shell,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )

                return ToolResult(
                    success=process.returncode == 0,
                    data={
                        "exit_code": process.returncode,
                        "stdout": stdout.decode("utf-8", errors="replace")[
                            -4000:
                        ],  # Limit output
                        "stderr": stderr.decode("utf-8", errors="replace")[-4000:],
                        "command": command,
                        "sandboxed": True,
                    },
                )

            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                return ToolResult(
                    success=False, error=f"Command timed out after {timeout} seconds"
                )

    async def _run_direct(self, command: str, timeout: int) -> ToolResult:
        """Run command directly (less secure but faster)."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            return ToolResult(
                success=process.returncode == 0,
                data={
                    "exit_code": process.returncode,
                    "stdout": stdout.decode("utf-8", errors="replace")[-4000:],
                    "stderr": stderr.decode("utf-8", errors="replace")[-4000:],
                    "command": command,
                    "sandboxed": False,
                },
            )

        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass
            return ToolResult(
                success=False, error=f"Command timed out after {timeout} seconds"
            )
