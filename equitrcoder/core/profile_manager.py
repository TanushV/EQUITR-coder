import os
from typing import Any, Dict, List, Optional

import yaml

# from pathlib import Path  # Unused
from .unified_config import get_config_manager


class ProfileManager:
    def __init__(self, profiles_dir: str = "equitrcoder/profiles"):
        # Resolve profiles_dir relative to package root if a relative path was provided
        from pathlib import Path as _Path

        base_dir = _Path(__file__).resolve().parent.parent  # equitrcoder/
        p = _Path(profiles_dir)
        if not p.is_absolute():
            p = (base_dir / (profiles_dir.replace("equitrcoder/", ""))).resolve()
        self.profiles_dir = str(p)
        self.profiles = self._load_profiles()
        self.profiles_config = self._load_profiles_config()
        self.system_prompt_config = self._load_system_prompt_config()
        self.default_tools = self.profiles_config.get("default_tools", [])

    def _load_profiles(self) -> Dict[str, Any]:
        """Load individual profile files from the profiles directory."""
        profiles = {}
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                profile_name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.profiles_dir, filename)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    profile_data = yaml.safe_load(f)
                    profiles[profile_name] = profile_data
        return profiles

    def _load_profiles_config(self) -> Dict[str, Any]:
        """Load the profiles configuration from unified configuration."""
        config_manager = get_config_manager()
        config_data = config_manager.get_cached_config()

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
        config_manager = get_config_manager()
        config_data = config_manager.get_cached_config()

        # Get prompts configuration from unified config
        prompts_config = config_data.prompts

        # Return with fallbacks
        return (
            prompts_config
            if prompts_config
            else {
                "base_system_prompt": (
                    "You are {agent_id}, an AI coding agent powered by {model}.\n\n"
                    "Tools available: {available_tools}\n\n"
                    "IMPORTANT: Aggressively leverage the ask_supervisor tool for any non-trivial decisions, architectural choices, ambiguities, or whenever you are uncertain.\n"
                    "Prefer over-communication with the supervisor to making assumptions. Consult early and often.\n\n"
                    "Repository context (live):\n{mandatory_context_json}\n\n"
                    "Current assignment and operating directives:\n{task_description}"
                )
            }
        )

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
