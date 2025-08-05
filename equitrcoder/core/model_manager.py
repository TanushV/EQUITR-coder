"""
Model Manager for EQUITR Coder

This module provides centralized model validation, cost estimation, and availability checking.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


from ..providers.litellm import LiteLLMProvider


@dataclass
class ModelValidationResult:
    """Result of model validation."""

    model: str
    is_valid: bool
    supports_function_calling: bool
    provider: str
    estimated_cost_per_1k_tokens: float
    availability_status: str
    error_message: Optional[str] = None


@dataclass
class CostEstimate:
    """Cost estimation for a model and token count."""

    model: str
    estimated_tokens: int
    estimated_cost: float
    cost_breakdown: Dict[str, float]
    confidence_level: float


class ModelManager:
    """Centralized model management and validation."""

    def __init__(self):
        self.model_cache: Dict[str, ModelValidationResult] = {}
        self.cost_cache: Dict[str, Dict[str, float]] = {}
        self._initialize_cost_data()

    def normalize_model_name(self, model: str) -> str:
        """Convert legacy model names to correct LiteLLM format."""
        # Handle moonshot models - convert legacy format to correct LiteLLM format
        if model.startswith("moonshot-v1-"):
            return f"moonshot/{model}"

        # Return as-is for other models
        return model

    def _initialize_cost_data(self):
        """Initialize cost data for different models."""
        self.cost_cache = {
            "openai/gpt-4": {"prompt": 0.03, "completion": 0.06},
            "openai/gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "openai/gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
            "anthropic/claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "anthropic/claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "anthropic/claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
            # Moonshot models (correct LiteLLM format)
            "moonshot/moonshot-v1-8k": {"prompt": 0.001, "completion": 0.002},
            "moonshot/moonshot-v1-32k": {"prompt": 0.002, "completion": 0.004},
            "moonshot/moonshot-v1-128k": {"prompt": 0.004, "completion": 0.008},
            "moonshot/kimi-k2-0711-preview": {"prompt": 0.001, "completion": 0.002},
            # Legacy format for backward compatibility
            "moonshot-v1-8k": {"prompt": 0.001, "completion": 0.002},
            "moonshot-v1-32k": {"prompt": 0.002, "completion": 0.004},
            "moonshot-v1-128k": {"prompt": 0.004, "completion": 0.008},
        }

    def _get_provider_from_model(self, model: str) -> str:
        """Extract provider from model string."""
        if "/" in model:
            return model.split("/", 1)[0]
        elif model.startswith("gpt"):
            return "openai"
        elif model.startswith("claude"):
            return "anthropic"
        elif model.startswith("moonshot"):
            return "moonshot"
        else:
            return "unknown"

    def _check_api_key_available(self, provider: str) -> bool:
        """Check if API key is available for the provider."""
        key_mappings = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "together": "TOGETHER_API_KEY",
            "cohere": "COHERE_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
        }

        env_var = key_mappings.get(provider, f"{provider.upper()}_API_KEY")
        return bool(os.getenv(env_var))

    def _supports_function_calling(self, model: str) -> bool:
        """Check if model supports function calling."""
        # List of models known to support function calling
        function_calling_models = {
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            # Moonshot models support function calling
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
            "moonshot/moonshot-v1-8k",
            "moonshot/moonshot-v1-32k",
            "moonshot/moonshot-v1-128k",
            "moonshot/kimi-k2-0711-preview",
        }

        return model in function_calling_models

    async def validate_model(
        self, model: str, test_call: bool = False
    ) -> ModelValidationResult:
        """Validate a model and return detailed information."""
        # Check cache first
        if model in self.model_cache and not test_call:
            return self.model_cache[model]

        provider = self._get_provider_from_model(model)
        api_key_available = self._check_api_key_available(provider)
        supports_function_calling = self._supports_function_calling(model)

        # Determine availability status
        if not api_key_available:
            availability_status = "api_key_missing"
            error_message = f"API key not found for provider '{provider}'. Set {provider.upper()}_API_KEY environment variable."
        elif not supports_function_calling:
            availability_status = "no_function_calling"
            error_message = f"Model '{model}' does not support function calling, which is required for EQUITR Coder."
        else:
            availability_status = "available"
            error_message = None

        # Perform test call if requested and model seems available
        if test_call and availability_status == "available":
            try:
                provider_instance = LiteLLMProvider(model=model)
                await provider_instance.chat(
                    messages=[{"role": "user", "content": "Test"}], max_tokens=1
                )
                availability_status = "verified"
            except Exception as e:
                availability_status = "test_failed"
                error_message = f"Test call failed: {str(e)}"

        # Get cost estimate
        cost_per_1k = self.cost_cache.get(model, {"prompt": 0.001, "completion": 0.002})
        estimated_cost = (cost_per_1k["prompt"] + cost_per_1k["completion"]) / 2

        result = ModelValidationResult(
            model=model,
            is_valid=availability_status in ["available", "verified"],
            supports_function_calling=supports_function_calling,
            provider=provider,
            estimated_cost_per_1k_tokens=estimated_cost,
            availability_status=availability_status,
            error_message=error_message,
        )

        # Cache the result
        self.model_cache[model] = result
        return result

    def estimate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> CostEstimate:
        """Estimate cost for a model and token usage."""
        cost_data = self.cost_cache.get(model, {"prompt": 0.001, "completion": 0.002})

        prompt_cost = (prompt_tokens / 1000) * cost_data["prompt"]
        completion_cost = (completion_tokens / 1000) * cost_data["completion"]
        total_cost = prompt_cost + completion_cost

        return CostEstimate(
            model=model,
            estimated_tokens=prompt_tokens + completion_tokens,
            estimated_cost=total_cost,
            cost_breakdown={
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "total_cost": total_cost,
            },
            confidence_level=0.8 if model in self.cost_cache else 0.5,
        )

    def get_compatible_models(self, require_function_calling: bool = True) -> List[str]:
        """Get list of compatible models based on requirements."""
        compatible = []

        for model in self.cost_cache.keys():
            if require_function_calling and not self._supports_function_calling(model):
                continue

            provider = self._get_provider_from_model(model)
            if self._check_api_key_available(provider):
                compatible.append(model)

        return compatible

    def get_model_suggestions(self, error_model: str) -> List[str]:
        """Get model suggestions when a model fails."""
        compatible = self.get_compatible_models()

        # Prioritize similar models
        if "gpt" in error_model.lower():
            compatible.sort(key=lambda x: 0 if "gpt" in x.lower() else 1)
        elif "claude" in error_model.lower():
            compatible.sort(key=lambda x: 0 if "claude" in x.lower() else 1)

        return compatible[:5]  # Return top 5 suggestions

    def format_model_error(
        self, model: str, validation_result: ModelValidationResult
    ) -> str:
        """Format a helpful error message for model issues."""
        if validation_result.availability_status == "api_key_missing":
            provider = validation_result.provider
            setup_instructions = {
                "openai": "Get your API key from https://platform.openai.com/api-keys",
                "anthropic": "Get your API key from https://console.anthropic.com/",
                "openrouter": "Get your API key from https://openrouter.ai/keys",
                "together": "Get your API key from https://api.together.xyz/settings/api-keys",
                "cohere": "Get your API key from https://dashboard.cohere.ai/api-keys",
            }

            instruction = setup_instructions.get(
                provider, f"Get your API key from the {provider} provider"
            )

            return f"""❌ API key missing for model '{model}'

{validation_result.error_message}

Setup instructions:
1. {instruction}
2. Set the environment variable: export {provider.upper()}_API_KEY="your-api-key"
3. Restart your application

Alternative models you can use:
{chr(10).join(f"  - {m}" for m in self.get_model_suggestions(model))}"""

        elif validation_result.availability_status == "no_function_calling":
            return f"""❌ Model '{model}' doesn't support function calling

EQUITR Coder requires models that support function calling for tool usage.

Recommended alternatives:
{chr(10).join(f"  - {m}" for m in self.get_model_suggestions(model))}"""

        elif validation_result.availability_status == "test_failed":
            return f"""❌ Model '{model}' failed test call

{validation_result.error_message}

This could be due to:
- Network connectivity issues
- API service temporarily unavailable
- Invalid API key or insufficient credits
- Model name not recognized by provider

Try these alternatives:
{chr(10).join(f"  - {m}" for m in self.get_model_suggestions(model))}"""

        else:
            return f"❌ Model '{model}' is not available: {validation_result.error_message}"


# Global model manager instance
model_manager = ModelManager()
