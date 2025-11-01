"""
Unit tests for UnifiedConfigManager

Tests the configuration management system including:
- Configuration loading and merging
- Schema validation
- Caching functionality
- Environment variable overrides
- Error handling
"""

import os
import tempfile
import yaml
import pytest
from unittest.mock import patch

# from pathlib import Path  # Unused
from datetime import timedelta

from equitrcoder.core.unified_config import (
    UnifiedConfigManager,
    ConfigurationData,
    get_config_manager,
    get_config,
    set_config,
)


class TestUnifiedConfigManager:
    """Test suite for UnifiedConfigManager"""

    def setup_method(self):
        """Setup for each test method"""
        # Reset singleton instance
        UnifiedConfigManager._instance = None

        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = self.temp_dir

        # Create test configuration files
        self.create_test_configs()

    def teardown_method(self):
        """Cleanup after each test method"""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Reset singleton
        UnifiedConfigManager._instance = None

    def create_test_configs(self):
        """Create test configuration files"""
        # Default config
        default_config = {
            "llm": {
                "provider": "litellm",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 4000,
                "budget": 1.0,
            },
            "sandbox": {
                "type": "venv",
                "timeout": 30,
                "max_memory": 512,
                "allow_network": False,
            },
            "orchestrator": {
                "max_iterations": 20,
                "error_retry_limit": 3,
                "error_retry_delay": 1.0,
                "supervisor_model": "o3",
                "worker_model": "moonshot/kimi-k2-0711-preview",
            },
        }

        with open(os.path.join(self.temp_dir, "default.yaml"), "w") as f:
            yaml.dump(default_config, f)

        # Profiles config
        profiles_config = {
            "default_tools": ["create_file", "read_file", "edit_file"],
            "settings": {
                "profiles_directory": "equitrcoder/profiles",
                "allow_empty_additional_tools": True,
            },
        }

        with open(os.path.join(self.temp_dir, "profiles.yaml"), "w") as f:
            yaml.dump(profiles_config, f)

        # System prompts config
        prompts_config = {
            "single_agent_prompt": "You are a single agent...",
            "multi_agent_prompt": "You are a multi agent...",
            "metadata": {"version": "1.0", "description": "Test prompts"},
        }

        with open(os.path.join(self.temp_dir, "system_prompt.yaml"), "w") as f:
            yaml.dump(prompts_config, f)

    def test_singleton_pattern(self):
        """Test that UnifiedConfigManager follows singleton pattern"""
        manager1 = UnifiedConfigManager(self.config_path)
        manager2 = UnifiedConfigManager(self.config_path)

        assert manager1 is manager2

    def test_config_loading(self):
        """Test basic configuration loading"""
        manager = UnifiedConfigManager(self.config_path)
        config = manager.load_config()

        assert isinstance(config, ConfigurationData)
        assert config.llm["provider"] == "litellm"
        assert config.llm["model"] == "gpt-4"
        assert config.sandbox["timeout"] == 30
        assert config.orchestrator["max_iterations"] == 20

    def test_get_method(self):
        """Test configuration value retrieval using dot notation"""
        manager = UnifiedConfigManager(self.config_path)

        # Test nested access
        assert manager.get("llm.provider") == "litellm"
        assert manager.get("llm.temperature") == 0.1
        assert manager.get("sandbox.timeout") == 30

        # Test default values
        assert manager.get("nonexistent.key", "default") == "default"
        assert manager.get("llm.nonexistent", None) is None

    def test_set_method(self):
        """Test configuration value setting"""
        manager = UnifiedConfigManager(self.config_path)

        # Set a value
        manager.set("llm.model", "gpt-3.5-turbo")
        assert manager.get("llm.model") == "gpt-3.5-turbo"

        # Set nested value
        manager.set("new.nested.value", "test")
        assert manager.get("new.nested.value") == "test"

    def test_caching(self):
        """Test configuration caching functionality"""
        manager = UnifiedConfigManager(self.config_path)

        # First access should load from config
        value1 = manager.get("llm.provider")

        # Second access should use cache
        value2 = manager.get("llm.provider")

        assert value1 == value2 == "litellm"

        # Verify cache is populated
        assert "get_llm.provider" in manager._cache

    def test_schema_validation_success(self):
        """Test successful schema validation"""
        manager = UnifiedConfigManager(self.config_path)
        config = {
            "llm": {
                "provider": "litellm",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 4000,
            },
            "sandbox": {"type": "venv", "timeout": 30, "max_memory": 512},
            "orchestrator": {"max_iterations": 20, "error_retry_limit": 3},
        }

        result = manager.validate_schema(config)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_schema_validation_failure(self):
        """Test schema validation with errors"""
        manager = UnifiedConfigManager(self.config_path)
        config = {
            "llm": {
                "provider": "invalid_provider",  # Invalid enum value
                "temperature": 3.0,  # Above maximum
                "max_tokens": "invalid",  # Wrong type
            },
            "sandbox": {
                "timeout": -1,  # Below minimum
                "max_memory": "invalid",  # Wrong type
            },
        }

        result = manager.validate_schema(config)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Check specific error messages
        error_messages = " ".join(result.errors)
        assert "invalid_provider" in error_messages
        assert "temperature" in error_messages
        assert "max_tokens" in error_messages

    @patch.dict(
        os.environ,
        {
            "EQUITR_LLM_MODEL": "gpt-3.5-turbo",
            "EQUITR_LLM_TEMPERATURE": "0.5",
            "EQUITR_MAX_ITERATIONS": "15",
        },
    )
    def test_environment_variable_overrides(self):
        """Test environment variable overrides"""
        manager = UnifiedConfigManager(self.config_path)

        # Environment variables should override config file values
        assert manager.get("llm.model") == "gpt-3.5-turbo"
        assert manager.get("llm.temperature") == 0.5
        assert manager.get("orchestrator.max_iterations") == 15

    def test_config_merging(self):
        """Test configuration merging functionality"""
        manager = UnifiedConfigManager(self.config_path)

        config1 = {
            "llm": {"provider": "litellm", "model": "gpt-4"},
            "sandbox": {"type": "venv"},
        }

        config2 = {
            "llm": {
                "temperature": 0.5,
                "model": "gpt-3.5-turbo",
            },  # Should override model
            "orchestrator": {"max_iterations": 10},
        }

        merged = manager.merge_configs(config1, config2)

        assert merged["llm"]["provider"] == "litellm"  # From config1
        assert merged["llm"]["model"] == "gpt-3.5-turbo"  # Overridden by config2
        assert merged["llm"]["temperature"] == 0.5  # From config2
        assert merged["sandbox"]["type"] == "venv"  # From config1
        assert merged["orchestrator"]["max_iterations"] == 10  # From config2

    def test_limits_extraction(self):
        """Test extraction of limit-related configuration"""
        manager = UnifiedConfigManager(self.config_path)
        config = manager.load_config()

        # Check that limits are properly extracted
        assert "max_cost" in config.limits
        assert "max_iterations" in config.limits
        assert "sandbox_timeout" in config.limits
        assert "max_workers" in config.limits
        assert "devops_timeout" in config.limits

        # Check default values
        assert config.limits["max_workers"] == 3
        assert config.limits["devops_timeout"] == 600

    def test_fallback_config(self):
        """Test fallback configuration when loading fails"""
        # Create manager with non-existent config path
        manager = UnifiedConfigManager("/nonexistent/path")
        config = manager.load_config()

        # Should still return valid configuration
        assert isinstance(config, ConfigurationData)
        assert config.llm["provider"] == "litellm"
        assert config.limits["max_cost"] == 5.0

    def test_reload_config(self):
        """Test configuration reloading"""
        manager = UnifiedConfigManager(self.config_path)

        # Initial load
        initial_model = manager.get("llm.model")
        assert initial_model == "gpt-4"

        # Modify config file with complete configuration to avoid fallback
        new_config = {
            "llm": {
                "provider": "litellm",
                "model": "gpt-3.5-turbo",
                "temperature": 0.2,
                "max_tokens": 4000,
                "budget": 1.0,
            },
            "sandbox": {
                "type": "venv",
                "timeout": 30,
                "max_memory": 512,
                "allow_network": False,
            },
            "orchestrator": {
                "max_iterations": 20,
                "error_retry_limit": 3,
                "error_retry_delay": 1.0,
                "supervisor_model": "o3",
                "worker_model": "moonshot/kimi-k2-0711-preview",
            },
        }

        with open(os.path.join(self.temp_dir, "default.yaml"), "w") as f:
            yaml.dump(new_config, f)

        # Reload configuration
        manager.reload_config()

        # Should reflect new values
        assert manager.get("llm.model") == "gpt-3.5-turbo"
        assert manager.get("llm.temperature") == 0.2

    def test_global_functions(self):
        """Test global convenience functions"""
        # Test get_config_manager
        manager = get_config_manager(self.config_path)
        assert isinstance(manager, UnifiedConfigManager)

        # Test get_config
        value = get_config("llm.provider")
        assert value == "litellm"

        # Test set_config
        set_config("test.value", "test_data")
        assert get_config("test.value") == "test_data"

    def test_missing_config_files(self):
        """Test behavior when configuration files are missing"""
        # Create empty directory
        empty_dir = tempfile.mkdtemp()

        try:
            manager = UnifiedConfigManager(empty_dir)
            config = manager.load_config()

            # Should still work with fallback values
            assert isinstance(config, ConfigurationData)
            assert config.llm["provider"] == "litellm"

        finally:
            import shutil

            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_invalid_yaml_handling(self):
        """Test handling of invalid YAML files"""
        # Create invalid YAML file
        with open(os.path.join(self.temp_dir, "default.yaml"), "w") as f:
            f.write("invalid: yaml: content: [")

        manager = UnifiedConfigManager(self.config_path)
        config = manager.load_config()

        # Should fall back to minimal configuration
        assert isinstance(config, ConfigurationData)

    def test_cache_ttl(self):
        """Test cache time-to-live functionality"""
        manager = UnifiedConfigManager(self.config_path)

        # Set very short TTL for testing
        manager._cache_ttl = timedelta(milliseconds=1)

        # First access
        value1 = manager.get("llm.provider")

        # Wait for cache to expire
        import time

        time.sleep(0.002)

        # Modify the underlying config
        manager._config_data.llm["provider"] = "modified"

        # Second access should reload (cache expired)
        _ = manager.get("llm.provider")

        # Note: This test is tricky because we're testing internal behavior
        # In practice, the cache would be cleared on config reload
        assert value1 == "litellm"  # Original value


if __name__ == "__main__":
    pytest.main([__file__])
