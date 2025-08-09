"""
Live model discovery with function calling support validation.
"""

import logging
from typing import Any, Dict, List, Optional

import litellm

logger = logging.getLogger(__name__)


class FunctionCallingModelDiscovery:
    """Discover and validate models with function calling support."""

    def __init__(self):
        self._cache = {}
        self._cache_timeout = 3600  # 1 hour cache

    async def discover_models(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover all available models with function calling support.

        Args:
            provider: Specific provider to check (e.g., 'openai', 'anthropic')
                     If None, checks all providers

        Returns:
            List of model information dictionaries
        """
        try:
            # Get all available models
            all_models = litellm.model_list

            # Filter and validate models
            supported_models = []

            for model in all_models:
                model_info = await self._get_model_info(model)
                if model_info and model_info["supports_function_calling"]:
                    if provider is None or model_info["provider"] == provider:
                        supported_models.append(model_info)

            return supported_models

        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return await self._get_fallback_models(provider)

    async def _get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a model."""
        try:
            # Parse provider from model name
            provider = None
            model_name = model

            if "/" in model:
                provider, model_name = model.split("/", 1)
            else:
                # Default provider mappings
                provider = self._infer_provider(model)

            # Check function calling support
            supports_fc = litellm.supports_function_calling(model)
            supports_pfc = litellm.supports_parallel_function_calling(model)

            return {
                "name": model,
                "model_name": model_name,
                "provider": provider,
                "supports_function_calling": supports_fc,
                "supports_parallel_function_calling": supports_pfc,
                "full_name": model,
            }

        except Exception as e:
            logger.warning(f"Error checking model {model}: {e}")
            return None

    def _infer_provider(self, model: str) -> str:
        """Infer provider from model name."""
        model_lower = model.lower()

        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower:
            return "google"
        elif "mistral" in model_lower:
            return "mistral"
        elif "cohere" in model_lower:
            return "cohere"
        else:
            return "unknown"

    async def _get_fallback_models(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get fallback models when live discovery fails."""
        fallback_models = {
            "openai": [
                {
                    "name": "gpt-4-turbo-preview",
                    "provider": "openai",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
                {
                    "name": "gpt-4",
                    "provider": "openai",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": False,
                },
                {
                    "name": "gpt-3.5-turbo-1106",
                    "provider": "openai",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
                {
                    "name": "gpt-3.5-turbo",
                    "provider": "openai",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": False,
                },
            ],
            "anthropic": [
                {
                    "name": "claude-3-opus",
                    "provider": "anthropic",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
                {
                    "name": "claude-3-sonnet",
                    "provider": "anthropic",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
                {
                    "name": "claude-3-haiku",
                    "provider": "anthropic",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
            ],
            "openrouter": [
                {
                    "name": "anthropic/claude-3-opus",
                    "provider": "openrouter",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
                {
                    "name": "anthropic/claude-3-sonnet",
                    "provider": "openrouter",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
                {
                    "name": "openai/gpt-4-turbo-preview",
                    "provider": "openrouter",
                    "supports_function_calling": True,
                    "supports_parallel_function_calling": True,
                },
            ],
        }

        if provider:
            return fallback_models.get(provider, [])
        else:
            # Return all models
            all_models = []
            for models in fallback_models.values():
                all_models.extend(models)
            return all_models

    async def validate_model(self, model: str) -> Dict[str, Any]:
        """
        Validate if a specific model supports function calling.

        Args:
            model: Full model name (e.g., "openai/gpt-4")

        Returns:
            Validation result dictionary
        """
        try:
            supports_fc = litellm.supports_function_calling(model)
            supports_pfc = litellm.supports_parallel_function_calling(model)

            # Parse provider
            provider = None
            if "/" in model:
                provider = model.split("/")[0]
            else:
                provider = self._infer_provider(model)

            return {
                "name": model,
                "provider": provider,
                "supports_function_calling": supports_fc,
                "supports_parallel_function_calling": supports_pfc,
                "valid": supports_fc,
                "error": (
                    None if supports_fc else "Model does not support function calling"
                ),
            }

        except Exception as e:
            return {
                "name": model,
                "provider": None,
                "supports_function_calling": False,
                "supports_parallel_function_calling": False,
                "valid": False,
                "error": str(e),
            }

    def get_provider_list(self) -> List[str]:
        """Get list of supported providers."""
        return [
            "openai",
            "anthropic",
            "openrouter",
            "azure",
            "bedrock",
            "vertexai",
            "cohere",
            "together",
            "replicate",
        ]


# Global instance
function_calling_discovery = FunctionCallingModelDiscovery()


async def discover_function_calling_models(provider: Optional[str] = None) -> List[str]:
    """
    Convenience function to get model names that support function calling.

    Args:
        provider: Specific provider or None for all

    Returns:
        List of model names
    """
    models = await function_calling_discovery.discover_models(provider)
    return [model["name"] for model in models]


async def validate_model_for_use(model: str) -> bool:
    """
    Validate if a model can be used with EQUITR Coder.

    Args:
        model: Model name to validate

    Returns:
        True if model supports function calling
    """
    result = await function_calling_discovery.validate_model(model)
    return result["valid"]
