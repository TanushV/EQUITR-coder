# Built-in tools for EQUITR Coder

from __future__ import annotations

# Avoid eager importing of submodules that may have optional dependencies.
# Submodules can be imported directly, e.g.,
#   from equitrcoder.tools.builtin.grep_search import GrepSearch

__all__ = [
    "communication",
    "fs",
    "git",
    "git_auto",
    "search",
    "shell",
    "todo",
]
