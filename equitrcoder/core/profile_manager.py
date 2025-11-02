import copy
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..utils.paths import get_extension_search_paths
from .unified_config import get_config_manager

logger = logging.getLogger(__name__)


class ProfileManager:
    def __init__(self, profiles_dir: str = "equitrcoder/profiles"):
        self._config_manager = get_config_manager()
        base_dir = Path(__file__).resolve().parent.parent
        manual_path = Path(profiles_dir)
        if not manual_path.is_absolute():
            manual_path = (
                base_dir / (profiles_dir.replace("equitrcoder/", ""))
            ).resolve()

        self.profile_dirs = self._build_profile_dirs(manual_path)
        self.profiles_dir = (
            str(self.profile_dirs[0]) if self.profile_dirs else str(manual_path)
        )
        self.profiles = self._load_profiles()
        self.profiles_config = self._load_profiles_config()
        self.system_prompt_config = self._load_system_prompt_config()
        self.default_tools = self.profiles_config.get("default_tools", [])

    def _build_profile_dirs(self, manual_path: Path) -> List[Path]:
        config = self._config_manager.get_cached_config()
        configured_paths: List[str] = []

        if isinstance(config.extensions, dict):
            configured_paths.extend(config.extensions.get("profiles", []) or [])

        profiles_settings = {}
        if isinstance(config.profiles, dict):
            profiles_settings = config.profiles.get("settings", {}) or {}
            configured_paths.extend(
                profiles_settings.get("profile_search_paths", []) or []
            )

        extension_paths = get_extension_search_paths(
            "profiles",
            configured_paths=configured_paths,
            project_root=Path.cwd(),
        )

        directories: List[Path] = []
        if manual_path.exists() and not any(
            manual_path.resolve() == p.resolve() for p in extension_paths
        ):
            directories.append(manual_path.resolve())

        for path in extension_paths:
            resolved = Path(path).resolve()
            if resolved.exists() and resolved not in directories:
                directories.append(resolved)

        return directories

    def _load_profiles(self) -> Dict[str, Any]:
        """Load individual profile files from the profiles directory."""
        profiles = {}
        for directory in self.profile_dirs:
            if not directory.exists():
                continue

            yaml_files = list(directory.glob("*.yml")) + list(directory.glob("*.yaml"))
            for filepath in sorted(yaml_files):
                profile_name = filepath.stem
                if profile_name in profiles:
                    continue
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    profile_data = yaml.safe_load(f) or {}
                    profiles[profile_name] = profile_data
        return profiles

    def _load_profiles_config(self) -> Dict[str, Any]:
        """Load the profiles configuration from unified configuration."""
        config_data = self._config_manager.get_cached_config()

        # Get profiles configuration from unified config
        profiles_config = config_data.profiles

        # Return with fallbacks
        return (
            profiles_config
            if profiles_config
            else {
                "default_tools": [
                    "create_file",
                    "read_file",
                    "edit_file",
                    "list_files",
                    "git_commit",
                    "git_status",
                    "git_diff",
                    "run_command",
                    "web_search",
                    "list_task_groups",
                    "list_all_todos",
                    "list_todos_in_group",
                    "update_todo_status",
                    "bulk_update_todo_status",
                    "ask_supervisor",
                    "send_message",
                    "receive_messages",
                ],
                "settings": {"allow_empty_additional_tools": True},
            }
        )

    def _load_system_prompt_config(self) -> Dict[str, Any]:
        """Load the system prompt configuration from unified configuration."""
        config_data = self._config_manager.get_cached_config()

        # Get prompts configuration from unified config
        prompts_config = config_data.prompts

        merged_prompts: Dict[str, Any] = (
            copy.deepcopy(prompts_config) if isinstance(prompts_config, dict) else {}
        )

        if not merged_prompts:
            merged_prompts = {
                "base_system_prompt": (
                    "You are {agent_id}, an AI coding agent powered by {model}.\n\n"
                    "Tools available: {available_tools}\n\n"
                    "IMPORTANT: Aggressively leverage the ask_supervisor tool for any non-trivial decisions, architectural choices, ambiguities, or whenever you are uncertain.\n"
                    "Prefer over-communication with the supervisor to making assumptions. Consult early and often.\n\n"
                    "Repository context (live):\n{mandatory_context_json}\n\n"
                    "Current assignment and operating directives:\n{task_description}"
                )
            }

        for directory in reversed(self.profile_dirs):
            for candidate_name in ("system_prompt.yaml", "system_prompt.yml"):
                candidate = directory / candidate_name
                if not candidate.exists():
                    continue
                try:
                    with open(candidate, "r", encoding="utf-8") as handle:
                        data = yaml.safe_load(handle) or {}
                        if isinstance(data, dict):
                            self._merge_dicts(merged_prompts, data)
                except Exception as exc:
                    logger.warning(
                        f"Failed to load system prompt override {candidate}: {exc}"
                    )

        return merged_prompts

    def _merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value

    def get_default_tools(self) -> List[str]:
        """Get the default tools that all agents should have."""
        return self.default_tools.copy()

    def get_base_system_prompt(self) -> str:
        """Get the base system prompt that all agents should have."""
        return self.system_prompt_config.get(
            "base_system_prompt", "You are {agent_id}, an AI coding agent."
        )

    def get_profile(self, name: str) -> Dict[str, Any]:
        """Get a profile and merge it with default tools."""
        profile = self.profiles.get(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found.")

        # Create a copy to avoid modifying the original
        enhanced_profile = profile.copy()

        # Merge default tools with profile-specific tools
        profile_tools = enhanced_profile.get("allowed_tools", [])
        all_tools = list(set(self.default_tools + profile_tools))  # Remove duplicates
        enhanced_profile["allowed_tools"] = all_tools

        return enhanced_profile

    def get_default_agent_config(self) -> Dict[str, Any]:
        """Get configuration for a default agent (no profile)."""
        return {
            "name": "Default Agent",
            "description": "A general-purpose agent with default tools and system prompt",
            "allowed_tools": self.get_default_tools(),
            "system_prompt": None,  # Will use base system prompt only
        }

    def get_agent_config(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get agent configuration - either default or profile-based."""
        if profile_name is None or profile_name == "default":
            return self.get_default_agent_config()
        else:
            return self.get_profile(profile_name)

    def list_profiles(self) -> List[str]:
        """List all available profiles, including 'default'."""
        profiles = list(self.profiles.keys())
        profiles.insert(0, "default")  # Add default as first option
        return profiles
