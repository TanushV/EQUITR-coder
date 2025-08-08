"""
Testing tools for QA engineers and developers.
"""

import subprocess
import json
from typing import Type
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class RunTestsArgs(BaseModel):
    test_path: str = Field(default=".", description="Path to run tests from (default: current directory)")
    test_pattern: str = Field(default="test_*.py", description="Test file pattern to match")
    verbose: bool = Field(default=True, description="Run tests in verbose mode")


class RunTests(Tool):
    def get_name(self) -> str:
        return "run_tests"

    def get_description(self) -> str:
        return "Run Python tests using pytest with configurable options"

    def get_args_schema(self) -> Type[BaseModel]:
        return RunTestsArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            
            # Build pytest command
            cmd = ["python", "-m", "pytest"]
            
            if args.verbose:
                cmd.append("-v")
            
            cmd.extend([args.test_path, "-k", args.test_pattern])
            
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return ToolResult(
                success=result.returncode == 0,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": " ".join(cmd)
                },
                error=result.stderr if result.returncode != 0 else None
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Tests timed out after 5 minutes")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class TestCoverageArgs(BaseModel):
    source_path: str = Field(default=".", description="Source code path to analyze coverage for")
    test_path: str = Field(default="tests/", description="Test directory path")
    min_coverage: int = Field(default=80, description="Minimum coverage percentage required")


class TestCoverage(Tool):
    def get_name(self) -> str:
        return "test_coverage"

    def get_description(self) -> str:
        return "Run test coverage analysis and report coverage statistics"

    def get_args_schema(self) -> Type[BaseModel]:
        return TestCoverageArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            
            # Run coverage
            cmd = [
                "python", "-m", "coverage", "run", 
                "--source", args.source_path,
                "-m", "pytest", args.test_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return self._handle_coverage_run_failure(result)
            
            return self._generate_coverage_report(args)
                
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Coverage analysis timed out after 5 minutes")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _handle_coverage_run_failure(self, result):
        """Handle failure when running coverage"""
        return ToolResult(
            success=False, 
            error=f"Coverage run failed: {result.stderr}",
            data={"stdout": result.stdout, "stderr": result.stderr}
        )
    
    def _generate_coverage_report(self, args):
        """Generate and parse coverage report"""
        report_cmd = ["python", "-m", "coverage", "report", "--format=json"]
        report_result = subprocess.run(report_cmd, capture_output=True, text=True)
        
        if report_result.returncode != 0:
            return ToolResult(
                success=False,
                error=f"Coverage report failed: {report_result.stderr}"
            )
        
        try:
            coverage_data = json.loads(report_result.stdout)
            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            
            # Get text report too
            text_cmd = ["python", "-m", "coverage", "report"]
            text_result = subprocess.run(text_cmd, capture_output=True, text=True)
            
            return ToolResult(
                success=total_coverage >= args.min_coverage,
                data={
                    "coverage_percentage": total_coverage,
                    "min_required": args.min_coverage,
                    "passed_threshold": total_coverage >= args.min_coverage,
                    "detailed_report": text_result.stdout,
                    "coverage_data": coverage_data
                },
                error=f"Coverage {total_coverage:.1f}% is below minimum {args.min_coverage}%" if total_coverage < args.min_coverage else None
            )
        except json.JSONDecodeError:
            return ToolResult(
                success=False,
                error="Failed to parse coverage JSON report",
                data={"raw_output": report_result.stdout}
            )


class LintCodeArgs(BaseModel):
    path: str = Field(default=".", description="Path to lint (file or directory)")
    fix: bool = Field(default=False, description="Automatically fix issues where possible")
    config_file: str = Field(default="", description="Path to linting config file (optional)")


class LintCode(Tool):
    def get_name(self) -> str:
        return "lint_code"

    def get_description(self) -> str:
        return "Run code linting using ruff to check code quality and style"

    def get_args_schema(self) -> Type[BaseModel]:
        return LintCodeArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            
            # Build ruff command
            cmd = ["python", "-m", "ruff", "check"]
            
            if args.fix:
                cmd.append("--fix")
            
            if args.config_file:
                cmd.extend(["--config", args.config_file])
            
            cmd.append(args.path)
            
            # Run linting
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # Ruff returns 0 if no issues, 1 if issues found
            issues_found = result.returncode != 0
            
            return ToolResult(
                success=not issues_found,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "issues_found": issues_found,
                    "command": " ".join(cmd),
                    "fixed_issues": args.fix
                },
                error=f"Linting found {result.stdout.count('error')} errors and {result.stdout.count('warning')} warnings" if issues_found else None
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Linting timed out after 2 minutes")
        except FileNotFoundError:
            return ToolResult(success=False, error="ruff not found. Install with: pip install ruff")
        except Exception as e:
            return ToolResult(success=False, error=str(e))