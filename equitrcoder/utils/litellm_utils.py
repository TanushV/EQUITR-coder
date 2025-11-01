"""Utility functions for LiteLLM model compatibility and function calling support."""

import os
from typing import Any, Dict, List

import litellm


def check_function_calling_support(model: str) -> bool:
    """
    Check if a model supports function calling.

    Args:
        model: Model name (e.g., "gpt-4", "claude-3-opus", "moonshot/moonshot-v1-8k")

    Returns:
        bool: True if model supports function calling
    """
    # Normalize model name
    model_lower = model.lower()

    # OpenAI models with function calling support
    openai_function_models = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4.1",
        "gpt-4-1106-preview",
        "gpt-4-0125-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-1106",
    ]

    # Anthropic models with function calling support
    anthropic_function_models = [
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3-5-sonnet",
        "claude-2.1",
    ]

    # Moonshot AI models with function calling support
    moonshot_function_models = [
        "moonshot/moonshot-v1-8k",
        "moonshot/moonshot-v1-32k",
        "moonshot/moonshot-v1-128k",
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k",
    ]

    # Google models with function calling support
    google_function_models = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]

    # Check if model supports function calling
    if any(
        supported_model in model_lower for supported_model in openai_function_models
    ):
        return True
    if any(
        supported_model in model_lower for supported_model in anthropic_function_models
    ):
        return True
    if any(
        supported_model in model_lower for supported_model in moonshot_function_models
    ):
        return True
    if any(
        supported_model in model_lower for supported_model in google_function_models
    ):
        return True

    # Try LiteLLM's built-in function calling support check
    try:
        return litellm.supports_function_calling(model)
    except Exception:
        # If LiteLLM doesn't recognize the model, assume no function calling
        return False


def check_parallel_function_calling_support(model: str) -> bool:
    """
    Check if a model supports parallel function calling.

    Args:
        model: Model name

    Returns:
        bool: True if model supports parallel function calling
    """
    model_lower = model.lower()

    # Models with confirmed parallel function calling support
    parallel_models = [
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4-1106-preview",
        "gpt-4-0125-preview",
        "gpt-3.5-turbo-1106",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-5-sonnet",
    ]

    # Moonshot models currently don't support parallel function calling
    moonshot_models = ["moonshot/", "moonshot-v1"]
    if any(moonshot_model in model_lower for moonshot_model in moonshot_models):
        return False

    return any(parallel_model in model_lower for parallel_model in parallel_models)


def get_model_compatibility(model: str) -> Dict[str, Any]:
    """
    Get comprehensive compatibility information for a model.

    Args:
        model: Model name

    Returns:
        Dict containing compatibility information
    """
    compatibility = {
        "model": model,
        "supported": True,  # Assume supported unless proven otherwise
        "function_calling": check_function_calling_support(model),
        "parallel_support": check_parallel_function_calling_support(model),
        "warnings": [],
    }

    # Add specific warnings
    if not compatibility["function_calling"]:
        compatibility["warnings"].append(
            f"Model {model} does not support function calling. Tool usage will be limited."
        )
    elif not compatibility["parallel_support"]:
        compatibility["warnings"].append(
            f"Model {model} does not support parallel function calling. Only sequential tool execution will be available."
        )

    # Moonshot-specific warnings
    if "moonshot" in model.lower():
        if "MOONSHOT_API_KEY" not in os.environ:
            compatibility["warnings"].append(
                "MOONSHOT_API_KEY environment variable not set. Please set your Moonshot AI API key."
            )

    return compatibility


def get_compatible_tools(
    tools: List[Dict[str, Any]], model: str, force_enable: bool = True
) -> List[Dict[str, Any]]:
    """
    Filter tools based on model compatibility.

    Args:
        tools: List of tool definitions
        model: Model name to check compatibility against
        force_enable: If True, return all tools regardless of compatibility

    Returns:
        List of compatible tools
    """
    if force_enable:
        return tools

    if not check_function_calling_support(model):
        # Model doesn't support function calling, return empty list
        return []

    # For now, return all tools if function calling is supported
    # In the future, we could filter based on specific tool requirements
    return tools


def get_supported_moonshot_models() -> List[str]:
    """
    Get list of supported Moonshot AI models.

    Returns:
        List of supported Moonshot model names
    """
    return [
        "moonshot/moonshot-v1-8k",
        "moonshot/moonshot-v1-32k",
        "moonshot/moonshot-v1-128k",
    ]


def setup_moonshot_provider(api_key: str) -> None:
    """
    Set up Moonshot AI provider with API key.

    Args:
        api_key: Moonshot AI API key
    """
    import os

    os.environ["MOONSHOT_API_KEY"] = api_key

    # Verify the API key format (basic validation)
    if not api_key or len(api_key) < 10:
        raise ValueError("Invalid Moonshot API key format")


def get_model_provider(model: str) -> str:
    """
    Determine the provider for a given model.

    Args:
        model: Model name

    Returns:
        Provider name
    """
    model_lower = model.lower()

    if model_lower.startswith("gpt-") or "openai" in model_lower:
        return "openai"
    elif model_lower.startswith("claude-") or "anthropic" in model_lower:
        return "anthropic"
    elif "moonshot" in model_lower:
        return "moonshot"
    elif model_lower.startswith("gemini-") or "google" in model_lower:
        return "google"
    elif "llama" in model_lower:
        return "meta"
    else:
        return "unknown"
