#!/usr/bin/env python3
"""
Sanity-check that custom tools are discoverable and minimally runnable.
This does not guarantee correctness; it ensures they load and accept their schemas.
Where possible, run a quick success-oriented scenario.
"""
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from equitrcoder.tools.discovery import discover_tools


async def success_args(tool_name: str) -> Dict[str, Any] | None:
    """Provide quick success-oriented args for selected tools."""
    if tool_name == "create_notebook":
        tmp = Path(tempfile.mkdtemp()) / "demo.ipynb"
        return {"path": str(tmp), "cells": ["print('ok')"]}
    if tool_name == "run_notebook":
        tmpdir = Path(tempfile.mkdtemp())
        nb = tmpdir / "demo.ipynb"
        nb.write_text(json.dumps({
            "cells": [{"cell_type": "code", "metadata": {}, "source": "x=1\nprint(x)", "outputs": [], "execution_count": None}],
            "metadata": {"kernelspec": {"name": "python3", "display_name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }), encoding="utf-8")
        return {"path": str(nb), "timeout": 60}
    if tool_name == "run_experiments":
        tmpdir = Path(tempfile.mkdtemp())
        exp = {"experiments": [{"name": "echo", "command": "echo ok", "timeout": 30}]}
        cfg = tmpdir / "experiments.yaml"
        cfg.write_text(json.dumps(exp), encoding="utf-8")
        return {"config_path": str(cfg)}
    if tool_name == "run_tests":
        return {"test_path": "tests/unit", "test_pattern": "test_*", "verbose": False}
    return None


async def run_tool(tool) -> Dict[str, Any]:
    name = tool.get_name()
    # Prefer success-oriented args when available
    sa = await success_args(name)
    if sa is None:
        # Build minimal args based on schema defaults
        schema = tool.get_args_schema()
        sa = {}
        for _, field in schema.model_fields.items():
            if field.default is not None:
                sa[field.alias or field.title or _] = field.default
            else:
                anno = field.annotation
                if anno in (str,):
                    sa[field.alias or field.title or _] = ""
                elif anno in (int,):
                    sa[field.alias or field.title or _] = 1
                elif anno in (bool,):
                    sa[field.alias or field.title or _] = False
                elif anno in (list,):
                    sa[field.alias or field.title or _] = []
                elif anno in (dict,):
                    sa[field.alias or field.title or _] = {}
                else:
                    sa[field.alias or field.title or _] = None
    try:
        res = await tool.run(**sa)
        return {
            "discovery": True,
            "invoked": True,
            "tool": name,
            "result_success": res.success,
            "error": res.error,
            "args_used": sa,
        }
    except Exception as e:
        return {"discovery": True, "invoked": False, "tool": name, "error": str(e), "args_used": sa}


async def main():
    tools = discover_tools()
    custom = [t for t in tools if t.__class__.__module__.startswith("equitrcoder.tools.custom.")]
    print(f"Found {len(custom)} custom tools")
    results = []
    for t in custom:
        r = await run_tool(t)
        results.append(r)
        status = "OK" if r.get("invoked") else "FAIL"
        print(f"[{status}] {t.get_name()} -> success={r.get('result_success')} error={r.get('error')} args={r.get('args_used')}")
    ok = sum(1 for r in results if r.get("invoked"))
    print(f"Summary: invoked {ok}/{len(results)} tools")

if __name__ == "__main__":
    asyncio.run(main()) 