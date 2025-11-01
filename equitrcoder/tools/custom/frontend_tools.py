"""
Frontend development tools for building, serving, and testing web applications.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Type

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class BuildProjectArgs(BaseModel):
    build_command: str = Field(
        default="npm run build", description="Command to build the project"
    )
    output_dir: str = Field(default="dist", description="Expected output directory")
    timeout: int = Field(default=300, description="Build timeout in seconds")


class BuildProject(Tool):
    def get_name(self) -> str:
        return "build_project"

    def get_description(self) -> str:
        return "Build a frontend project using npm, yarn, or other build tools"

    def get_args_schema(self) -> Type[BaseModel]:
        return BuildProjectArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Run build command
            result = subprocess.run(
                args.build_command.split(),
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )

            # Check if build output exists
            output_path = Path(args.output_dir)
            build_success = result.returncode == 0 and output_path.exists()

            # Get build artifacts info
            artifacts = []
            if output_path.exists():
                for file_path in output_path.rglob("*"):
                    if file_path.is_file():
                        artifacts.append(
                            {
                                "path": str(file_path),
                                "size": file_path.stat().st_size,
                                "type": file_path.suffix,
                            }
                        )

            return ToolResult(
                success=build_success,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": args.build_command,
                    "output_dir": args.output_dir,
                    "artifacts": artifacts,
                    "total_artifacts": len(artifacts),
                },
                error=result.stderr if not build_success else None,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False, error=f"Build timed out after {args.timeout} seconds"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ServeDevArgs(BaseModel):
    serve_command: str = Field(
        default="npm run dev", description="Command to start dev server"
    )
    port: int = Field(default=3000, description="Port to serve on")
    host: str = Field(default="localhost", description="Host to serve on")
    background: bool = Field(default=True, description="Run in background")


class ServeDev(Tool):
    def get_name(self) -> str:
        return "serve_dev"

    def get_description(self) -> str:
        return "Start a development server for frontend applications"

    def get_args_schema(self) -> Type[BaseModel]:
        return ServeDevArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Set environment variables for port and host
            env = os.environ.copy()
            env["PORT"] = str(args.port)
            env["HOST"] = args.host

            cmd_parts = args.serve_command.split()

            if args.background:
                # Start dev server in background
                process = subprocess.Popen(
                    cmd_parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )

                # Give it time to start
                import time

                time.sleep(3)

                # Check if process is still running
                if process.poll() is None:
                    return ToolResult(
                        success=True,
                        data={
                            "message": f"Dev server started on {args.host}:{args.port}",
                            "pid": process.pid,
                            "command": args.serve_command,
                            "url": f"http://{args.host}:{args.port}",
                            "background": True,
                        },
                    )
                else:
                    stdout, stderr = process.communicate()
                    return ToolResult(
                        success=False,
                        error=f"Dev server failed to start: {stderr}",
                        data={"stdout": stdout, "stderr": stderr},
                    )
            else:
                # Run in foreground for testing
                result = subprocess.run(
                    cmd_parts, capture_output=True, text=True, timeout=10, env=env
                )

                return ToolResult(
                    success=result.returncode == 0,
                    data={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "return_code": result.returncode,
                        "command": args.serve_command,
                    },
                    error=result.stderr if result.returncode != 0 else None,
                )

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Dev server command timed out")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class InstallDependenciesArgs(BaseModel):
    package_manager: str = Field(
        default="npm", description="Package manager to use (npm, yarn, pnpm)"
    )
    dev_dependencies: bool = Field(
        default=False, description="Install dev dependencies only"
    )
    packages: List[str] = Field(
        default_factory=list, description="Specific packages to install (empty for all)"
    )


class InstallDependencies(Tool):
    def get_name(self) -> str:
        return "install_dependencies"

    def get_description(self) -> str:
        return "Install frontend project dependencies using npm, yarn, or pnpm"

    def get_args_schema(self) -> Type[BaseModel]:
        return InstallDependenciesArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Build install command
            if args.package_manager == "npm":
                cmd = ["npm", "install"]
                if args.dev_dependencies:
                    cmd.append("--only=dev")
            elif args.package_manager == "yarn":
                cmd = ["yarn", "install"]
                if args.dev_dependencies:
                    cmd.append("--dev")
            elif args.package_manager == "pnpm":
                cmd = ["pnpm", "install"]
                if args.dev_dependencies:
                    cmd.append("--dev")
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported package manager: {args.package_manager}",
                )

            # Add specific packages if provided
            if args.packages:
                cmd.extend(args.packages)

            # Run install command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for installs
            )

            return ToolResult(
                success=result.returncode == 0,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": " ".join(cmd),
                    "package_manager": args.package_manager,
                },
                error=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False, error="Package installation timed out after 5 minutes"
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error=f"{args.package_manager} not found. Please install it first.",
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ValidateHtmlArgs(BaseModel):
    file_path: str = Field(..., description="Path to HTML file to validate")
    check_accessibility: bool = Field(
        default=True, description="Check basic accessibility rules"
    )


class ValidateHtml(Tool):
    def get_name(self) -> str:
        return "validate_html"

    def get_description(self) -> str:
        return "Validate HTML files for syntax and basic accessibility issues"

    def get_args_schema(self) -> Type[BaseModel]:
        return ValidateHtmlArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            file_path = Path(args.file_path)
            if not file_path.exists():
                return ToolResult(
                    success=False, error=f"HTML file not found: {args.file_path}"
                )

            # Read HTML content
            html_content = file_path.read_text(encoding="utf-8")

            issues = []
            warnings = []

            # Basic HTML validation
            if not html_content.strip().startswith("<!DOCTYPE"):
                issues.append("Missing DOCTYPE declaration")

            if "<html" not in html_content:
                issues.append("Missing <html> tag")

            if "<head>" not in html_content:
                issues.append("Missing <head> section")

            if "<title>" not in html_content:
                issues.append("Missing <title> tag")

            # Basic accessibility checks
            if args.check_accessibility:
                if "<img" in html_content and "alt=" not in html_content:
                    warnings.append(
                        "Images should have alt attributes for accessibility"
                    )

                if "<input" in html_content and "label" not in html_content.lower():
                    warnings.append("Form inputs should have associated labels")

                if "color:" in html_content and "background-color:" not in html_content:
                    warnings.append(
                        "Consider specifying background colors when setting text colors"
                    )

            # Count tags for basic structure analysis
            tag_counts = {
                "div": html_content.count("<div"),
                "span": html_content.count("<span"),
                "p": html_content.count("<p"),
                "h1": html_content.count("<h1"),
                "h2": html_content.count("<h2"),
                "h3": html_content.count("<h3"),
            }

            return ToolResult(
                success=len(issues) == 0,
                data={
                    "file_path": args.file_path,
                    "issues": issues,
                    "warnings": warnings,
                    "tag_counts": tag_counts,
                    "file_size": len(html_content),
                    "line_count": html_content.count("\n") + 1,
                },
                error=f"Found {len(issues)} validation issues" if issues else None,
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))
