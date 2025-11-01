"""
Unit tests for ModelManager
"""

import os
from unittest.mock import patch

import pytest

from equitrcoder.core.model_manager import ModelManager, ModelValidationResult


class TestModelManager:
    """Test cases for ModelManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model_manager = ModelManager()

    def test_get_provider_from_model(self):
        """Test provider extraction from model strings."""
        assert self.model_manager._get_provider_from_model("openai/gpt-4") == "openai"
        assert (
            self.model_manager._get_provider_from_model("anthropic/claude-3-sonnet")
            == "anthropic"
        )
        assert self.model_manager._get_provider_from_model("gpt-4") == "openai"
        assert (
            self.model_manager._get_provider_from_model("claude-3-haiku") == "anthropic"
        )
        assert self.model_manager._get_provider_from_model("unknown-model") == "unknown"

    def test_supports_function_calling(self):
        """Test function calling support detection."""
        # Should support function calling
        assert self.model_manager._supports_function_calling("gpt-4")
        assert self.model_manager._supports_function_calling("openai/gpt-3.5-turbo")
        assert self.model_manager._supports_function_calling(
            "anthropic/claude-3-sonnet"
        )

        # Should not support function calling (unknown models)
        assert not self.model_manager._supports_function_calling("unknown-model")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_check_api_key_available_with_key(self):
        """Test API key availability check when key is present."""
        assert self.model_manager._check_api_key_available("openai")

    @patch.dict(os.environ, {}, clear=True)
    def test_check_api_key_available_without_key(self):
        """Test API key availability check when key is missing."""
        assert not self.model_manager._check_api_key_available("openai")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_validate_model_success(self):
        """Test successful model validation."""
        result = await self.model_manager.validate_model("gpt-4")

        assert result.model == "gpt-4"
        assert result.is_valid
        assert result.supports_function_calling
        assert result.provider == "openai"
        assert result.availability_status == "available"
        assert result.error_message is None

    @patch.dict(os.environ, {}, clear=True)
    async def test_validate_model_missing_api_key(self):
        """Test model validation with missing API key."""
        result = await self.model_manager.validate_model("gpt-4")

        assert result.model == "gpt-4"
        assert not result.is_valid
        assert result.availability_status == "api_key_missing"
        assert "API key not found" in result.error_message

    async def test_validate_model_no_function_calling(self):
        """Test model validation for models without function calling."""
        with patch.object(
            self.model_manager, "_supports_function_calling", return_value=False
        ):
            with patch.object(
                self.model_manager, "_check_api_key_available", return_value=True
            ):
                result = await self.model_manager.validate_model("some-model")

                assert not result.is_valid
                assert result.availability_status == "no_function_calling"
                assert "does not support function calling" in result.error_message

    def test_estimate_cost(self):
        """Test cost estimation functionality."""
        estimate = self.model_manager.estimate_cost("gpt-4", 1000, 500)

        assert estimate.model == "gpt-4"
        assert estimate.estimated_tokens == 1500
        assert estimate.estimated_cost > 0
        assert "prompt_cost" in estimate.cost_breakdown
        assert "completion_cost" in estimate.cost_breakdown
        assert "total_cost" in estimate.cost_breakdown

    @patch.dict(
        os.environ, {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"}
    )
    def test_get_compatible_models(self):
        """Test getting compatible models."""
        compatible = self.model_manager.get_compatible_models()

        assert len(compatible) > 0
        assert any("gpt" in model for model in compatible)
        assert any("claude" in model for model in compatible)

    def test_get_model_suggestions(self):
        """Test model suggestion functionality."""
        suggestions = self.model_manager.get_model_suggestions("gpt-4")

        assert len(suggestions) <= 5
        # Should prioritize similar models (GPT models first for GPT input)
        gpt_models = [s for s in suggestions if "gpt" in s.lower()]
        if gpt_models:
            assert suggestions.index(gpt_models[0]) == 0

    def test_format_model_error_api_key_missing(self):
        """Test error message formatting for missing API key."""
        validation_result = ModelValidationResult(
            model="gpt-4",
            is_valid=False,
            supports_function_calling=True,
            provider="openai",
            estimated_cost_per_1k_tokens=0.03,
            availability_status="api_key_missing",
            error_message="API key not found for provider 'openai'",
        )

        error_msg = self.model_manager.format_model_error("gpt-4", validation_result)

        assert "❌ API key missing" in error_msg
        assert "OPENAI_API_KEY" in error_msg
        assert "https://platform.openai.com" in error_msg
        assert "Alternative models" in error_msg

    def test_format_model_error_no_function_calling(self):
        """Test error message formatting for no function calling support."""
        validation_result = ModelValidationResult(
            model="some-model",
            is_valid=False,
            supports_function_calling=False,
            provider="unknown",
            estimated_cost_per_1k_tokens=0.001,
            availability_status="no_function_calling",
            error_message="Model doesn't support function calling",
        )

        error_msg = self.model_manager.format_model_error(
            "some-model", validation_result
        )

        assert "❌ Model 'some-model' doesn't support function calling" in error_msg
        assert "EQUITR Coder requires models that support function calling" in error_msg
        assert "Recommended alternatives" in error_msg


if __name__ == "__main__":
    pytest.main([__file__])
