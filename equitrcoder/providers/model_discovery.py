from typing import Any, Dict, List
from urllib.parse import urljoin

import httpx


class LiteLLMModelDiscovery:
    """Dynamic model discovery for LiteLLM proxy servers."""

    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url.rstrip("/")
        self.models_endpoint = urljoin(self.base_url, "/v1/models")

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Fetch available models from LiteLLM proxy.

        Returns:
            List of model dictionaries with 'id', 'object', 'created', 'owned_by'
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.models_endpoint)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            print(f"Error fetching models from {self.models_endpoint}: {e}")
            return []

    def get_available_models_sync(self) -> List[Dict[str, Any]]:
        """Synchronous version of get_available_models."""
        try:
            with httpx.Client() as client:
                response = client.get(self.models_endpoint)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            print(f"Error fetching models from {self.models_endpoint}: {e}")
            return []

    def get_model_names(self, sync: bool = False) -> List[str]:
        """
        Get just the model IDs/names.

        Args:
            sync: Whether to use synchronous or async method

        Returns:
            List of model names/IDs
        """
        if sync:
            models = self.get_available_models_sync()
        else:
            # For async context, caller should use get_available_models()
            return []

        return [model.get("id", "") for model in models if model.get("id")]

    def is_model_available(self, model_name: str, sync: bool = False) -> bool:
        """Check if a specific model is available."""
        available_models = self.get_model_names(sync=sync)
        return model_name in available_models

    def validate_lite_llm_connection(self) -> bool:
        """Test if LiteLLM proxy is accessible."""
        try:
            models = self.get_available_models_sync()
            return len(models) > 0
        except Exception:
            return False
