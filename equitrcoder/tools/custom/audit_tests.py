"""
Audit-only test management tools.

Provides operations to create tests scoped to a task group section, inspect
statuses, and bulk-mark/remove defective tests. Mutating operations require
an auth token to enforce that only the audit agent can modify tests.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Type

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult

# Registry paths (under repo)
REGISTRY_DIR = Path("tests") / "audit"
REGISTRY_FILE = REGISTRY_DIR / "_registry.json"
DEFECTIVE_DIR = REGISTRY_DIR / "_defective"


def _ensure_dirs() -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    DEFECTIVE_DIR.mkdir(parents=True, exist_ok=True)


def _load_registry() -> Dict[str, Dict[str, Dict[str, bool]]]:
    """Load registry mapping group_id -> { test_path: {"defective": bool} }"""
    _ensure_dirs()
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_registry(data: Dict[str, Dict[str, Dict[str, bool]]]) -> None:
    _ensure_dirs()
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _discover_source_files(section_paths: List[str]) -> List[Path]:
    files: List[Path] = []
    for sp in section_paths:
        base = Path(sp)
        if base.is_file() and base.suffix == ".py":
            files.append(base.resolve())
        elif base.is_dir():
            for fp in base.rglob("*.py"):
                # Skip tests
                if "tests" in fp.parts:
                    continue
                files.append(fp.resolve())
    # De-duplicate while preserving order
    seen = set()
    unique: List[Path] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def _extract_functions(source_text: str) -> List[str]:
    names: List[str] = []
    try:
        pattern = r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
        for m in re.finditer(pattern, source_text, re.MULTILINE):
            names.append(m.group(1))
    except Exception:
        pass
    return names[:10]


def _generate_test_content_for_file(src: Path) -> str:
    try:
        content = src.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        content = ""
    funcs = _extract_functions(content)
    src_str = str(src)
    lines: List[str] = []
    lines.append("from pathlib import Path")
    lines.append("import importlib.util")
    lines.append("")
    lines.append(f"SOURCE_FILE = {repr(src_str)}")
    lines.append("")
    lines.append("def _load_module_from_path(path_str: str):")
    lines.append("    path = Path(path_str)")
    lines.append(
        "    spec = importlib.util.spec_from_file_location(path.stem, path_str)"
    )
    lines.append("    mod = importlib.util.module_from_spec(spec)")
    lines.append("    assert spec and spec.loader is not None")
    lines.append("    spec.loader.exec_module(mod)")
    lines.append("    return mod")
    lines.append("")
    lines.append("def test_can_import_source_module():")
    lines.append("    mod = _load_module_from_path(SOURCE_FILE)")
    lines.append("    assert mod is not None")
    for name in funcs:
        lines.append("")
        lines.append(f"def test_has_function_{name}():")
        lines.append("    mod = _load_module_from_path(SOURCE_FILE)")
        lines.append(f"    assert hasattr(mod, {repr(name)})")
    return "\n".join(lines) + "\n"


def _group_test_dir(group_id: str) -> Path:
    d = REGISTRY_DIR / group_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _make_test_path(group_id: str, source_path: Path) -> Path:
    base_name = f"test_{source_path.stem}.py"
    return _group_test_dir(group_id) / base_name


def _matches_any_pattern(p: Path, patterns_or_paths: List[str]) -> bool:
    s = str(p)
    for pat in patterns_or_paths:
        if pat in s:
            return True
        try:
            if Path(pat).resolve() == p.resolve():
                return True
        except Exception:
            # Ignore resolve errors for non-path patterns
            pass
    return False


class _AuthMixin:
    REQUIRED_ENV_KEY = "EQUITR_AUDIT_TOKEN"

    @staticmethod
    def _check_auth_token(provided: Optional[str]) -> Optional[str]:
        import os

        expected = os.environ.get(_AuthMixin.REQUIRED_ENV_KEY, "")
        if not expected:
            # If no expected token configured, allow only if provided equals "DEV_ALLOW"
            return "DEV_ALLOW" if provided == "DEV_ALLOW" else None
        return provided if provided == expected else None


class CreateGroupTestsArgs(BaseModel):
    group_id: str = Field(..., description="Task group identifier")
    section_paths: List[str] = Field(
        ..., description="Paths to source files or folders"
    )
    auth_token: str = Field(..., description="Audit auth token for write operations")
    overwrite: bool = Field(
        default=False, description="Overwrite existing tests if present"
    )


class CreateGroupTests(Tool, _AuthMixin):
    def get_name(self) -> str:
        return "audit_create_group_tests"

    def get_description(self) -> str:
        return (
            "Create skeleton tests for Python sources under section_paths, stored under "
            "tests/audit/<group_id>/. Requires audit auth token."
        )

    def get_args_schema(self) -> Type[BaseModel]:
        return CreateGroupTestsArgs

    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        if not self._check_auth_token(args.auth_token):
            return ToolResult(
                success=False, error="Unauthorized: invalid audit auth token"
            )

        created: List[str] = []
        skipped: List[str] = []
        registry = _load_registry()
        group_map = registry.get(args.group_id, {})

        sources = _discover_source_files(args.section_paths)
        for src in sources:
            test_path = _make_test_path(args.group_id, src)
            if test_path.exists() and not args.overwrite:
                skipped.append(str(test_path))
                # Ensure present in registry
                group_map[str(test_path)] = {"defective": False}
                continue

            test_content = _generate_test_content_for_file(src)
            test_path.write_text(test_content, encoding="utf-8")
            created.append(str(test_path))
            group_map[str(test_path)] = {"defective": False}

        registry[args.group_id] = group_map
        _save_registry(registry)

        return ToolResult(
            success=True,
            data={
                "created": created,
                "skipped": skipped,
                "group_id": args.group_id,
                "total": len(created) + len(skipped),
            },
        )


class GetGroupTestStatusesArgs(BaseModel):
    group_id: str = Field(..., description="Task group identifier")
    pytest_args: List[str] = Field(
        default_factory=list, description="Extra pytest CLI args"
    )


class GetGroupTestStatuses(Tool):
    def get_name(self) -> str:
        return "audit_get_group_test_statuses"

    def get_description(self) -> str:
        return "Run pytest for the group's audit tests and return summarized results."

    def get_args_schema(self) -> Type[BaseModel]:
        return GetGroupTestStatusesArgs

    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        test_dir = _group_test_dir(args.group_id)
        if not test_dir.exists():
            return ToolResult(
                success=True,
                data={
                    "group_id": args.group_id,
                    "exists": False,
                    "summary": "no tests",
                },
            )

        cmd = ["python", "-m", "pytest", str(test_dir), "-q"] + list(args.pytest_args)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="pytest timed out for group")
        stdout = proc.stdout
        stderr = proc.stderr
        return_code = proc.returncode

        # Parse summary line (e.g., "3 passed, 1 failed in 0.12s")
        summary_line = ""
        for line in stdout.splitlines()[::-1]:
            if " passed" in line or " failed" in line or " no tests" in line:
                summary_line = line.strip()
                break

        missing_pytest = "No module named pytest" in (stderr or "")
        return ToolResult(
            success=return_code == 0,
            data={
                "group_id": args.group_id,
                "exists": True,
                "return_code": return_code,
                "summary": summary_line,
                "stdout": stdout,
                "stderr": stderr,
                "command": " ".join(cmd),
                "missing_pytest": missing_pytest,
            },
            error=(
                None
                if return_code == 0
                else (stderr or summary_line or "pytest failed")
            ),
        )


class ListGroupTestsArgs(BaseModel):
    group_id: str = Field(..., description="Task group identifier")


class ListGroupTests(Tool):
    def get_name(self) -> str:
        return "audit_list_group_tests"

    def get_description(self) -> str:
        return "List tests registered for a task group with defective flags."

    def get_args_schema(self) -> Type[BaseModel]:
        return ListGroupTestsArgs

    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        registry = _load_registry()
        group_map = registry.get(args.group_id, {})
        files: List[Dict[str, object]] = []
        for path_str, meta in group_map.items():
            p = Path(path_str)
            files.append(
                {
                    "path": path_str,
                    "exists": p.exists(),
                    "defective": bool(meta.get("defective", False)),
                }
            )
        return ToolResult(
            success=True, data={"group_id": args.group_id, "tests": files}
        )


class MarkDefectiveTestsArgs(BaseModel):
    group_id: str = Field(..., description="Task group identifier")
    test_patterns_or_paths: List[str] = Field(
        ..., description="Patterns or exact paths to mark defective"
    )
    auth_token: str = Field(..., description="Audit auth token for write operations")


class MarkDefectiveTests(Tool, _AuthMixin):
    def get_name(self) -> str:
        return "audit_mark_defective_tests"

    def get_description(self) -> str:
        return (
            "Mark matching tests as defective and move them to the audit/_defective folder. "
            "Requires audit auth token."
        )

    def get_args_schema(self) -> Type[BaseModel]:
        return MarkDefectiveTestsArgs

    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        if not self._check_auth_token(args.auth_token):
            return ToolResult(
                success=False, error="Unauthorized: invalid audit auth token"
            )

        registry = _load_registry()
        group_map = registry.get(args.group_id, {})

        affected: List[str] = []
        for path_str in list(group_map.keys()):
            p = Path(path_str)
            if not _matches_any_pattern(p, args.test_patterns_or_paths):
                continue
            # Move file if exists
            if p.exists():
                dest_dir = DEFECTIVE_DIR / args.group_id
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / p.name
                try:
                    shutil.move(str(p), str(dest))
                except Exception:
                    # If move fails, leave in place but still mark defective
                    pass
            group_map[path_str]["defective"] = True
            affected.append(path_str)

        registry[args.group_id] = group_map
        _save_registry(registry)

        return ToolResult(
            success=True, data={"group_id": args.group_id, "marked_defective": affected}
        )


class RemoveDefectiveTestsArgs(BaseModel):
    group_id: str = Field(..., description="Task group identifier")
    auth_token: str = Field(..., description="Audit auth token for write operations")
    remove_files: bool = Field(
        default=False, description="If true, delete archived files permanently"
    )


class RemoveDefectiveTests(Tool, _AuthMixin):
    def get_name(self) -> str:
        return "audit_remove_defective_tests"

    def get_description(self) -> str:
        return (
            "Remove defective tests from the registry and optionally delete archived files. "
            "Requires audit auth token."
        )

    def get_args_schema(self) -> Type[BaseModel]:
        return RemoveDefectiveTestsArgs

    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        if not self._check_auth_token(args.auth_token):
            return ToolResult(
                success=False, error="Unauthorized: invalid audit auth token"
            )

        registry = _load_registry()
        group_map = registry.get(args.group_id, {})
        removed: List[str] = []

        # Remove entries flagged as defective
        for path_str, meta in list(group_map.items()):
            if bool(meta.get("defective", False)):
                removed.append(path_str)
                del group_map[path_str]

        registry[args.group_id] = group_map
        _save_registry(registry)

        # Optionally delete archived files
        if args.remove_files:
            archive_dir = DEFECTIVE_DIR / args.group_id
            if archive_dir.exists():
                for fp in archive_dir.glob("*.py"):
                    try:
                        fp.unlink(missing_ok=True)
                    except Exception:
                        pass

        return ToolResult(
            success=True,
            data={
                "group_id": args.group_id,
                "removed": removed,
                "deleted_files": bool(args.remove_files),
            },
        )
