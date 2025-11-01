"""
Unified Configuration Manager for EQUITR Coder

This module provides a centralized configuration management system that:
- Consolidates all scattered YAML configuration files
- Eliminates hardcoded values throughout the codebase
- Provides comprehensive schema validation
- Implements intelligent caching to avoid repeated file reads
- Supports hierarchical configuration merging
- Enables environment variable overrides
"""

import os
import yaml
import logging
from typing import Any, Dict, List, Optional

# from pathlib import Path  # Unused
from dataclasses import dataclass, field

# from functools import lru_cache  # Unused
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation"""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ConfigurationData:
    """Consolidated configuration data structure"""

    # LLM Configuration
    llm: Dict[str, Any] = field(default_factory=dict)

    # Sandbox Configuration
    sandbox: Dict[str, Any] = field(default_factory=dict)

    # Session Configuration
    session: Dict[str, Any] = field(default_factory=dict)

    # Repository Configuration
    repository: Dict[str, Any] = field(default_factory=dict)

    # Orchestrator Configuration
    orchestrator: Dict[str, Any] = field(default_factory=dict)

    # Profile Configuration
    profiles: Dict[str, Any] = field(default_factory=dict)

    # System Prompts
    prompts: Dict[str, Any] = field(default_factory=dict)

    # Performance and Limits
    limits: Dict[str, Any] = field(default_factory=dict)

    # Logging Configuration
    logging: Dict[str, Any] = field(default_factory=dict)

    # Validation Configuration
    validation: Dict[str, Any] = field(default_factory=dict)


from .interfaces import IConfigurable, Result  # noqa: E402


class UnifiedConfigManager(IConfigurable):
    """
    Unified Configuration Manager that consolidates all configuration sources
    and provides a single point of access with caching and validation.
    """

    _instance: Optional["UnifiedConfigManager"] = None
    _lock = threading.Lock()

    def __new__(cls, config_path: Optional[str] = None):
        """Singleton pattern to ensure single configuration instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.config_path = config_path or self._get_default_config_path()
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
        self._schema = self._load_schema()
        self._config_data: Optional[ConfigurationData] = None

        # Load initial configuration
        self.reload_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration directory path"""
        return os.path.join(os.path.dirname(__file__), "..", "config")

    def _load_schema(self) -> Dict[str, Any]:
        """Load configuration schema for validation"""
        return {
            "llm": {
                "required": ["provider"],
                "properties": {
                    "provider": {
                        "type": "string",
                        "enum": ["litellm", "openai", "anthropic"],
                    },
                    "model": {"type": "string"},
                    "api_base": {"type": "string"},
                    "budget": {"type": "number", "minimum": 0},
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                    "max_tokens": {"type": "integer", "minimum": 1},
                },
            },
            "sandbox": {
                "required": ["type", "timeout", "max_memory"],
                "properties": {
                    "type": {"type": "string", "enum": ["venv", "docker", "local"]},
                    "timeout": {"type": "integer", "minimum": 1},
                    "max_memory": {"type": "integer", "minimum": 64},
                    "allow_network": {"type": "boolean"},
                },
            },
            "orchestrator": {
                "required": ["max_iterations", "error_retry_limit"],
                "properties": {
                    "max_iterations": {"type": "integer", "minimum": 1},
                    "error_retry_limit": {"type": "integer", "minimum": 0},
                    "error_retry_delay": {"type": "number", "minimum": 0},
                    "supervisor_model": {"type": "string"},
                    "worker_model": {"type": "string"},
                },
            },
            "limits": {
                "properties": {
                    "max_cost": {"type": "number", "minimum": 0},
                    "max_workers": {"type": "integer", "minimum": 1},
                    "max_depth": {"type": "integer", "minimum": 1},
                    "devops_timeout": {"type": "integer", "minimum": 1},
                }
            },
        }

    def load_config(self) -> ConfigurationData:
        """Load and return the complete configuration"""
        if self._config_data is None:
            self.reload_config()
        assert self._config_data is not None
        return self._config_data

    def reload_config(self) -> None:
        """Reload configuration from all sources"""
        try:
            # Load all configuration files
            config_files = {
                "default": "default.yaml",
                "profiles": "profiles.yaml",
                "prompts": "system_prompt.yaml",
            }

            configs: Dict[str, Any] = {}
            for name, filename in config_files.items():
                file_path = os.path.join(self.config_path, filename)
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        configs[name] = yaml.safe_load(f) or {}
                else:
                    logger.warning(f"Configuration file not found: {file_path}")
                    configs[name] = {}

            # Merge configurations with environment variable overrides
            merged_config = self.merge_configs(configs["default"], configs["profiles"])
            merged_config = self._apply_env_overrides(merged_config)

            # Create consolidated configuration data
            self._config_data = ConfigurationData(
                llm=merged_config.get("llm", {}),
                sandbox=merged_config.get("sandbox", {}),
                session=merged_config.get("session", {}),
                repository=merged_config.get("repository", {}),
                orchestrator=merged_config.get("orchestrator", {}),
                profiles=configs["profiles"],
                prompts=configs["prompts"],
                limits=self._extract_limits(merged_config),
                logging=merged_config.get("logging", self._get_default_logging()),
                validation=merged_config.get(
                    "validation", self._get_default_validation()
                ),
            )

            # Validate configuration
            validation_result = self.validate_schema(merged_config)
            if not validation_result.is_valid:
                logger.error(
                    f"Configuration validation failed: {validation_result.errors}"
                )
                # Check if we have critical missing sections
                critical_errors = [
                    e
                    for e in validation_result.errors
                    if "Missing required section" in e
                ]
                if (
                    len(critical_errors) >= 2
                ):  # Missing multiple critical sections, use fallback
                    logger.warning(
                        "Critical configuration sections missing, using fallback configuration"
                    )
                    self._config_data = self._get_fallback_config()
                    return
                # Continue with warnings but log errors
                for error in validation_result.errors:
                    logger.error(f"Config validation error: {error}")

            # Clear cache after reload
            self._cache.clear()
            self._cache_timestamps.clear()

            logger.info("Configuration reloaded successfully")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            # Always provide fallback configuration on error
            self._config_data = self._get_fallback_config()

    def _extract_limits(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract limit-related configuration into a separate section"""
        limits: Dict[str, Any] = {}

        # Extract from various sections
        if "llm" in config:
            if "budget" in config["llm"]:
                limits["max_cost"] = config["llm"]["budget"]
            if "max_tokens" in config["llm"]:
                limits["max_tokens"] = config["llm"]["max_tokens"]

        if "orchestrator" in config:
            if "max_iterations" in config["orchestrator"]:
                limits["max_iterations"] = config["orchestrator"]["max_iterations"]
            if "error_retry_limit" in config["orchestrator"]:
                limits["error_retry_limit"] = config["orchestrator"][
                    "error_retry_limit"
                ]

        if "sandbox" in config:
            if "timeout" in config["sandbox"]:
                limits["sandbox_timeout"] = config["sandbox"]["timeout"]
            if "max_memory" in config["sandbox"]:
                limits["max_memory"] = config["sandbox"]["max_memory"]

        # Add hardcoded values that need to be configurable
        limits.setdefault("max_workers", 3)
        limits.setdefault("max_depth", 3)
        limits.setdefault("devops_timeout", 600)  # 10 minutes
        limits.setdefault("context_max_tokens", 4000)
        limits.setdefault("summary_max_tokens", 1000)

        return limits

    def _get_default_logging(self) -> Dict[str, Any]:
        """Get default logging configuration"""
        return {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "handlers": ["console"],
            "structured": True,
            "correlation_ids": True,
        }

    def _get_default_validation(self) -> Dict[str, Any]:
        """Get default validation configuration"""
        return {
            "strict_mode": False,
            "validate_on_startup": True,
            "schema_validation": True,
            "type_checking": True,
        }

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        env_mappings: Dict[str, List[str]] = {
            "EQUITR_LLM_MODEL": ["llm", "model"],
            "EQUITR_LLM_PROVIDER": ["llm", "provider"],
            "EQUITR_LLM_API_BASE": ["llm", "api_base"],
            "EQUITR_LLM_BUDGET": ["llm", "budget"],
            "EQUITR_LLM_TEMPERATURE": ["llm", "temperature"],
            "EQUITR_LLM_MAX_TOKENS": ["llm", "max_tokens"],
            "EQUITR_SANDBOX_TIMEOUT": ["sandbox", "timeout"],
            "EQUITR_SANDBOX_MAX_MEMORY": ["sandbox", "max_memory"],
            "EQUITR_MAX_ITERATIONS": ["orchestrator", "max_iterations"],
            "EQUITR_ERROR_RETRY_LIMIT": ["orchestrator", "error_retry_limit"],
            "EQUITR_SUPERVISOR_MODEL": ["orchestrator", "supervisor_model"],
            "EQUITR_WORKER_MODEL": ["orchestrator", "worker_model"],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Navigate to the correct nested dictionary
                current: Any = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Convert value to appropriate type
                final_key = config_path[-1]
                if final_key in ["budget", "temperature"]:
                    current[final_key] = float(env_value)
                elif final_key in [
                    "max_tokens",
                    "timeout",
                    "max_memory",
                    "max_iterations",
                    "error_retry_limit",
                ]:
                    current[final_key] = int(env_value)
                else:
                    current[final_key] = env_value

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation (e.g., 'llm.model')
        Uses caching to avoid repeated lookups
        """
        cache_key = f"get_{key}"

        # Check cache first
        if cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key)
            if timestamp and datetime.now() - timestamp < self._cache_ttl:
                return self._cache[cache_key]

        # Load configuration if not loaded
        if self._config_data is None:
            self.load_config()

        # Navigate through the configuration using dot notation
        keys = key.split(".")
        current: Any = (
            self._config_data.__dict__ if self._config_data is not None else {}
        )

        try:
            for k in keys:
                if isinstance(current, dict):
                    current = current[k]
                else:
                    current = getattr(current, k)

            # Cache the result
            self._cache[cache_key] = current
            self._cache_timestamps[cache_key] = datetime.now()

            return current

        except (KeyError, AttributeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        if self._config_data is None:
            self.load_config()

        keys = key.split(".")
        current = self._config_data.__dict__ if self._config_data is not None else {}

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value

        # Clear relevant cache entries
        cache_keys_to_clear = [
            k for k in list(self._cache.keys()) if k.startswith(f"get_{key}")
        ]
        for cache_key in cache_keys_to_clear:
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)

    def validate_schema(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema"""
        errors: List[str] = []
        warnings: List[str] = []

        try:
            for section_name, section_schema in self._schema.items():
                if section_name not in config:
                    if section_schema.get("required"):
                        errors.append(f"Missing required section: {section_name}")
                    continue

                section_config = config[section_name]

                # Check required fields
                required_fields = section_schema.get("required", [])
                for req_field in required_fields:
                    if req_field not in section_config:
                        errors.append(
                            f"Missing required field: {section_name}.{req_field}"
                        )

                # Check field properties
                properties = section_schema.get("properties", {})
                for field_name, field_config in section_config.items():
                    if field_name in properties:
                        field_schema = properties[field_name]
                        validation_error = self._validate_field(
                            f"{section_name}.{field_name}", field_config, field_schema
                        )
                        if validation_error:
                            errors.append(validation_error)

        except Exception as e:
            errors.append(f"Schema validation error: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def _validate_field(
        self, field_path: str, value: Any, schema: Dict[str, Any]
    ) -> Optional[str]:
        """Validate a single field against its schema"""
        field_type = schema.get("type")

        if field_type == "string" and not isinstance(value, str):
            return f"{field_path}: expected string, got {type(value).__name__}"
        elif field_type == "integer" and not isinstance(value, int):
            return f"{field_path}: expected integer, got {type(value).__name__}"
        elif field_type == "number" and not isinstance(value, (int, float)):
            return f"{field_path}: expected number, got {type(value).__name__}"
        elif field_type == "boolean" and not isinstance(value, bool):
            return f"{field_path}: expected boolean, got {type(value).__name__}"

        # Check enum values
        if "enum" in schema and value not in schema["enum"]:
            return (
                f"{field_path}: value '{value}' not in allowed values {schema['enum']}"
            )

        # Check numeric constraints
        if field_type in ["integer", "number"]:
            if "minimum" in schema and value < schema["minimum"]:
                return (
                    f"{field_path}: value {value} is below minimum {schema['minimum']}"
                )
            if "maximum" in schema and value > schema["maximum"]:
                return (
                    f"{field_path}: value {value} is above maximum {schema['maximum']}"
                )

        return None

    def get_cached_config(self) -> ConfigurationData:
        """Get cached configuration data"""
        if self._config_data is None:
            self.load_config()
        assert self._config_data is not None
        return self._config_data

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries"""
        result: Dict[str, Any] = {}

        for config in configs:
            if not config:
                continue

            for key, value in config.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = self.merge_configs(result[key], value)
                else:
                    result[key] = value

        return result

    def _get_fallback_config(self) -> ConfigurationData:
        """Get minimal fallback configuration when loading fails"""
        return ConfigurationData(
            llm={
                "provider": "litellm",
                "model": "",
                "temperature": 0.1,
                "max_tokens": 4000,
                "budget": 1.0,
            },
            sandbox={
                "type": "venv",
                "timeout": 30,
                "max_memory": 512,
                "allow_network": False,
            },
            orchestrator={
                "max_iterations": 20,
                "error_retry_limit": 3,
                "error_retry_delay": 1.0,
                "supervisor_model": "o3",
                "worker_model": "moonshot/kimi-k2-0711-preview",
            },
            limits={
                "max_cost": 5.0,
                "max_workers": 3,
                "max_depth": 3,
                "devops_timeout": 600,
                "context_max_tokens": 4000,
                "summary_max_tokens": 1000,
            },
            logging=self._get_default_logging(),
            validation=self._get_default_validation(),
        )

    # IConfigurable interface implementation
    def configure(self, config: Dict[str, Any]) -> Result[bool]:
        """Configure the component with given settings (IConfigurable interface)"""
        try:
            # Validate the configuration first
            validation_result = self.validate_schema(config)
            if not validation_result.is_valid:
                return Result(
                    success=False,
                    data=False,
                    error=f"Configuration validation failed: {', '.join(validation_result.errors)}",
                )

            # Apply the configuration by updating internal state
            if self._config_data is None:
                self._config_data = self._get_fallback_config()
            for key, value in config.items():
                if hasattr(self._config_data, key):
                    setattr(self._config_data, key, value)

            # Clear cache to force reload
            self._cache.clear()
            self._cache_timestamps.clear()

            return Result(success=True, data=True)

        except Exception as e:
            return Result(success=False, data=False, error=str(e))

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration (IConfigurable interface)"""
        if self._config_data is None:
            self.load_config()
        assert self._config_data is not None

        return {
            "llm": self._config_data.llm,
            "sandbox": self._config_data.sandbox,
            "session": self._config_data.session,
            "repository": self._config_data.repository,
            "orchestrator": self._config_data.orchestrator,
            "profiles": self._config_data.profiles,
            "prompts": self._config_data.prompts,
            "limits": self._config_data.limits,
            "logging": self._config_data.logging,
            "validation": self._config_data.validation,
        }

    def validate_configuration(self, config: Dict[str, Any]) -> Result[bool]:
        """Validate configuration before applying (IConfigurable interface)"""
        try:
            validation_result = self.validate_schema(config)

            if validation_result.is_valid:
                return Result(success=True, data=True)
            else:
                return Result(
                    success=False,
                    data=False,
                    error=f"Validation failed: {', '.join(validation_result.errors)}",
                )

        except Exception as e:
            return Result(success=False, data=False, error=str(e))


# Global configuration instance
_config_manager: Optional[UnifiedConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> UnifiedConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = UnifiedConfigManager(config_path)
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """Convenience function to get configuration value"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> None:
    """Convenience function to set configuration value"""
    get_config_manager().set(key, value)
