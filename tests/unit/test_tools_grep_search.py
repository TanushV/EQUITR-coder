import asyncio
from pathlib import Path

import pytest

from equitrcoder.tools.builtin.grep_search import GrepSearch


@pytest.mark.asyncio
async def test_grep_search_basic_match(tmp_path: Path):
    file_a = tmp_path / "a.py"
    file_a.write_text("""\nprint('Hello')\n# TODO: implement\n""", encoding="utf-8")

    tool = GrepSearch()
    res = await tool.run(pattern=r"TODO", path=str(tmp_path))

    assert res.success is True
    assert res.data["total_matches"] == 1
    match = res.data["matches"][0]
    assert match["path"].endswith("a.py")
    assert "TODO" in match["line"]


@pytest.mark.asyncio
async def test_grep_search_include_exclude(tmp_path: Path):
    (tmp_path / "keep.txt").write_text("findme\n", encoding="utf-8")
    (tmp_path / "skip.md").write_text("findme\n", encoding="utf-8")

    tool = GrepSearch()
    # include only *.txt
    res = await tool.run(pattern=r"findme", path=str(tmp_path), include="*.txt")
    assert res.success is True
    assert res.data["total_matches"] == 1
    assert res.data["matches"][0]["path"].endswith("keep.txt")

    # exclude *.txt
    res2 = await tool.run(pattern=r"findme", path=str(tmp_path), exclude="*.txt")
    assert res2.success is True
    # only skip.md remains
    assert res2.data["total_matches"] == 1
    assert res2.data["matches"][0]["path"].endswith("skip.md")


@pytest.mark.asyncio
async def test_grep_search_case_sensitivity(tmp_path: Path):
    (tmp_path / "case.py").write_text("Token\ntoken\n", encoding="utf-8")

    tool = GrepSearch()
    res_insensitive = await tool.run(pattern=r"token", path=str(tmp_path), case_sensitive=False)
    assert res_insensitive.success is True
    assert res_insensitive.data["total_matches"] == 2

    res_sensitive = await tool.run(pattern=r"token", path=str(tmp_path), case_sensitive=True)
    assert res_sensitive.success is True
    assert res_sensitive.data["total_matches"] == 1


@pytest.mark.asyncio
async def test_grep_search_path_safety(tmp_path: Path):
    tool = GrepSearch()
    # absolute path should be rejected
    res_abs = await tool.run(pattern=r".", path="/etc")
    assert res_abs.success is False
    assert "Path traversal" in (res_abs.error or "")

    # traversal should be rejected
    res_trav = await tool.run(pattern=r".", path="../")
    assert res_trav.success is False
    assert "Path traversal" in (res_trav.error or "") 