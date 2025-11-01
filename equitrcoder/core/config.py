import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = "litellm"  # Use LiteLLM as default
    model: str = ""  # No default model - users must select one
    api_base: str = ""
    api_key: str = ""
    budget: float = 1.0
    temperature: float = 0.1
    max_tokens: int = 4000

    # No hardcoded model configurations
    models: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Active model selection - empty means no model selected
    active_model: str = ""

    # Provider-specific settings
    provider_settings: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ToolsConfig(BaseModel):
    enabled: List[str] = Field(default_factory=lambda: ["fs", "git", "shell", "search"])
    disabled: List[str] = Field(default_factory=list)


class SandboxConfig(BaseModel):
    type: str = "venv"
    timeout: int = 30
    max_memory: int = 512
    allow_network: bool = False


class SessionConfig(BaseModel):
    persist: bool = True
    max_context: int = 100000
    session_dir: str = "~/.EQUITR-coder/sessions"


class RepositoryConfig(BaseModel):
    index_on_start: bool = True
    ignore_patterns: List[str] = Field(
        default_factory=lambda: [
            "*.pyc",
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "*.log",
        ]
    )


class OrchestratorConfig(BaseModel):
    max_iterations: int = 20
    error_retry_limit: int = 3
    error_retry_delay: float = 1.0
    use_multi_agent: bool = False  # Enable strong/weak agent paradigm
    tool_log_file: str = str(Path.home() / ".EQUITR-coder" / "tool_calls.log")
    log_tool_calls: bool = True
    debug: bool = False
    supervisor_model: str = ""
    worker_model: str = ""


class ProfilesConfig(BaseModel):
    default: str = "default"
    available: List[str] = Field(
        default_factory=lambda: ["ml_researcher", "app_developer"]
    )


class Config(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    profiles: ProfilesConfig = Field(default_factory=ProfilesConfig)


class ConfigManager:
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.user_config_dir = Path.home() / ".EQUITR-coder"
        self.user_config_dir.mkdir(exist_ok=True)

    def load_config(self, profile: str = "default") -> Config:
        # Start with default config
        config_data = self._load_yaml_file(self.config_dir / "default.yaml")

        # Override with profile-specific config if different from default
        if profile != "default":
            profile_file = self.config_dir / f"{profile}.yaml"
            if profile_file.exists():
                profile_data = self._load_yaml_file(profile_file)
                config_data = self._merge_configs(config_data, profile_data)

        # Override with user config if exists
        user_config_file = self.user_config_dir / "config.yaml"
        if user_config_file.exists():
            user_data = self._load_yaml_file(user_config_file)
            config_data = self._merge_configs(config_data, user_data)

        # Override with environment variables
        config_data = self._apply_env_overrides(config_data)

        # Normalize any special values (e.g., session.max_context: "auto")
        config_data = self._normalize_config(config_data)

        return Config(**config_data)

    # Back-compatibility alias used in older modules / UI code
    def get_config(self, profile: str = "default") -> Config:  # noqa: D401
        """Alias for ``load_config`` kept for backward compatibility."""
        return self.load_config(profile)

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        # Force UTF-8 to handle emoji and non-ASCII in YAML (Windows safe)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return yaml.safe_load(f) or {}

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        env_mappings = {
            "OPENROUTER_API_KEY": ("llm", "api_key"),
            "CLAUDE_AGENT_MODEL": ("llm", "model"),
            "CLAUDE_AGENT_BUDGET": ("llm", "budget"),
            "CLAUDE_AGENT_PROFILE": ("profiles", "default"),
        }

        for env_var, (section, key) in env_mappings.items():
            if env_var in os.environ:
                if section not in config_data:
                    config_data[section] = {}
                value: Any = os.environ[env_var]
                # Convert numeric values
                if key in ["budget"]:
                    value = float(value)
                config_data[section][key] = value

        return config_data

    def _normalize_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize special string values into concrete types expected by models."""
        session_cfg: Dict[str, Any] = config_data.get("session", {}) or {}
        max_ctx_value: Any = session_cfg.get("max_context")

        if isinstance(max_ctx_value, str) and max_ctx_value.lower() == "auto":
            # Default large character-based context window suitable for code
            resolved_max_context = 100000

            # Optionally derive from limits.context_max_tokens or llm.max_tokens if available
            try:
                limits_cfg = config_data.get("limits", {}) or {}
                candidate_tokens = limits_cfg.get(
                    "context_max_tokens"
                ) or config_data.get("llm", {}).get("max_tokens")
                if isinstance(candidate_tokens, (int, float)) and candidate_tokens > 0:
                    # Convert tokens to characters using a conservative multiplier
                    estimated_chars = int(candidate_tokens * 8)
                    # Keep within a reasonable range
                    resolved_max_context = max(16000, min(estimated_chars, 100000))
            except Exception:
                # Fall back to default if any issue occurs
                resolved_max_context = 100000

            session_cfg["max_context"] = int(resolved_max_context)
            config_data["session"] = session_cfg

        return config_data

    def save_user_config(self, config: Config):
        """Save configuration to user config file."""
        config_file = self.user_config_dir / "config.yaml"
        with open(config_file, "w", encoding="utf-8", errors="ignore") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False)

    def get_active_model_config(self, config: Config) -> Dict[str, Any]:
        """Get the configuration for the currently active model."""
        active_model = config.llm.active_model
        if active_model in config.llm.models:
            model_config = config.llm.models[active_model].copy()

            # Apply global overrides
            if config.llm.api_key:
                model_config["api_key"] = config.llm.api_key
            if config.llm.api_base:
                model_config["api_base"] = config.llm.api_base
            if config.llm.budget:
                model_config["budget"] = config.llm.budget

            return model_config
        else:
            # Fallback to default config
            return {
                "provider": config.llm.provider,
                "model": config.llm.model,
                "api_key": config.llm.api_key,
                "api_base": config.llm.api_base,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens,
                "budget": config.llm.budget,
            }

    def switch_model(self, config: Config, model_name: str) -> Config:
        """Switch to a different model configuration."""
        if model_name in config.llm.models:
            # Validate that the model supports function calling
            model_config = config.llm.models[model_name]
            actual_model = model_config.get("model", "")
            if actual_model:
                from ..utils.litellm_utils import check_function_calling_support

                if not check_function_calling_support(actual_model):
                    raise ValueError(
                        f"Cannot switch to model '{actual_model}' as it does not support function calling, "
                        f"which is required for EQUITR Coder."
                    )

            config.llm.active_model = model_name
            return config
        else:
            raise ValueError(f"Model '{model_name}' not found in configuration")

    def add_model_config(
        self, config: Config, name: str, model_config: Dict[str, Any]
    ) -> Config:
        """Add a new model configuration."""
        # Validate that the model supports function calling
        model_name = model_config.get("model", "")
        if model_name:
            from ..utils.litellm_utils import check_function_calling_support

            if not check_function_calling_support(model_name):
                raise ValueError(
                    f"Model '{model_name}' does not support function calling, which is required for EQUITR Coder.\n"
                    f"Only models with function calling support can be added."
                )

        config.llm.models[name] = model_config
        return config

    def remove_model_config(self, config: Config, name: str) -> Config:
        """Remove a new model configuration."""
        if name in config.llm.models:
            del config.llm.models[name]
            # Switch to default if removing active model
            if config.llm.active_model == name:
                config.llm.active_model = "default"
        return config

    def get_available_models(self, config: Config) -> List[str]:
        """Get list of available model configurations."""
        return list(config.llm.models.keys())

    def discover_lite_llm_models(
        self, api_base: str = "http://localhost:4000"
    ) -> List[str]:
        """
        Discover available models from LiteLLM proxy.

        Args:
            api_base: Base URL of the LiteLLM proxy

        Returns:
            List of available model names
        """
        from equitrcoder.providers.model_discovery import LiteLLMModelDiscovery

        discovery = LiteLLMModelDiscovery(api_base)
        return discovery.get_model_names(sync=True)


# Global config manager instance
config_manager = ConfigManager()
