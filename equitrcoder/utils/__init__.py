"""
Utility modules for equitrcoder.
"""

from .git_manager import GitManager, create_git_manager
from .paths import (
    get_equitr_home,
    get_extension_search_paths,
    get_project_config_dir,
    get_user_extensions_root,
)
from .restricted_fs import RestrictedFileSystem
from .scaffold import (
    ScaffoldError,
    ensure_extension_structure,
    resolve_extension_root,
    scaffold_mode,
    scaffold_profile,
    scaffold_tool,
)

__all__ = [
    "RestrictedFileSystem",
    "GitManager",
    "create_git_manager",
    "get_equitr_home",
    "get_project_config_dir",
    "get_user_extensions_root",
    "get_extension_search_paths",
    "ensure_extension_structure",
    "resolve_extension_root",
    "scaffold_tool",
    "scaffold_profile",
    "scaffold_mode",
    "ScaffoldError",
]
