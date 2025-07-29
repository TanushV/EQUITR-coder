import asyncio
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import litellm

from ..core.config import Config

# Import shared models from openrouter for consistency
from .openrouter import ChatResponse, Message, ToolCall

logger = logging.getLogger(__name__)


class LiteLLMProvider:
    """Unified LLM provider using LiteLLM for multiple providers."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ):
        """Initialize LiteLLM provider.

        Args:
            model: Model in "provider/model" format (e.g., "openai/gpt-4", "anthropic/claude-3")
            api_key: API key for the provider
            api_base: Custom API base URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Parse provider from model string
        if "/" in model:
            self.provider, self.model_name = model.split("/", 1)
        else:
            # Default to OpenAI if no provider specified
            self.provider = "openai"
            self.model_name = model

        # Set up API key based on provider
        self._setup_api_key(api_key)

        # Set custom API base if provided
        if api_base:
            self._setup_api_base(api_base)

        # Configure LiteLLM settings
        litellm.drop_params = True  # Drop unsupported params instead of erroring
        litellm.set_verbose = False  # Reduce logging noise

        # Additional provider-specific settings
        self.provider_kwargs = kwargs

        # Exponential backoff configuration
        self.max_retries = 5
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 60.0  # Maximum delay in seconds
        self.backoff_multiplier = 2.0

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests

    def _setup_api_key(self, api_key: Optional[str] = None) -> None:
        """Set up API key for the provider."""
        # For Moonshot, avoid hard-coding secrets. If an API key is supplied, use it;
        # otherwise rely on the existing environment variable. Always ensure the
        # default base URL is present, but without exposing any credentials.
        if self.provider == "moonshot":
            if api_key:
                os.environ["MOONSHOT_API_KEY"] = api_key
            # Set a sensible default for the API base if it is not already set.
            os.environ.setdefault("MOONSHOT_API_BASE", "https://api.moonshot.ai/v1")
            return

        # If no API key provided, return early for other providers
        if not api_key:
            return

        if self.provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif self.provider == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif self.provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        else:
            # Generic fallback
            os.environ["API_KEY"] = api_key

    def _get_api_key_env_var(self) -> str:
        """Get the expected API key environment variable for the provider."""
        provider_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "together": "TOGETHER_API_KEY",
            "replicate": "REPLICATE_API_TOKEN",
            "cohere": "COHERE_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
            "bedrock": "AWS_ACCESS_KEY_ID",
            "azure": "AZURE_API_KEY",
            "vertexai": "VERTEXAI_PROJECT",
            "palm": "PALM_API_KEY",
        }
        return provider_key_map.get(self.provider, f"{self.provider.upper()}_API_KEY")

    def _get_common_api_key_variations(self) -> List[str]:
        """Get common API key variations for backward compatibility."""
        base_key = self._get_api_key_env_var()
        variations = [base_key]

        # Add common variations
        if self.provider == "anthropic":
            variations.extend(["CLAUDE_API_KEY", "ANTHROPIC_API_KEY"])
        elif self.provider == "openai":
            variations.extend(["OPENAI_API_KEY", "OPENAI_KEY"])
        elif self.provider == "openrouter":
            variations.extend(["OPENROUTER_API_KEY", "OPENROUTER_KEY"])

        return variations

    def _setup_api_base(self, api_base: str) -> None:
        """Set up custom API base URL."""
        if self.provider == "openai":
            os.environ["OPENAI_API_BASE"] = api_base
        elif self.provider == "openrouter":
            os.environ["OPENROUTER_API_BASE"] = api_base
        elif self.provider == "moonshot":
            os.environ["MOONSHOT_API_BASE"] = api_base
        # Add more providers as needed

    async def _exponential_backoff_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry for the SAME request."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting before each attempt (minimum 2 seconds)
                await self._rate_limit()

                if attempt > 0:
                    print(
                        f"🔄 Retry attempt {attempt}/{self.max_retries} for the SAME request..."
                    )

                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                # Don't retry on authentication errors
                if any(
                    auth_term in error_msg
                    for auth_term in [
                        "authentication",
                        "unauthorized",
                        "invalid key",
                        "api key",
                        "invalid_api_key",
                    ]
                ):
                    print(f"❌ Authentication error, not retrying: {e}")
                    raise e

                # Don't retry on model not found errors
                if any(
                    model_term in error_msg
                    for model_term in [
                        "model not found",
                        "invalid model",
                        "model does not exist",
                        "unsupported model",
                    ]
                ):
                    print(f"❌ Model error, not retrying: {e}")
                    raise e

                # Check if this is a retryable error
                is_rate_limit = any(
                    keyword in error_msg
                    for keyword in [
                        "rate limit",
                        "quota",
                        "429",
                        "too many requests",
                        "retry-after",
                    ]
                )
                is_server_error = any(
                    keyword in error_msg
                    for keyword in [
                        "500",
                        "502",
                        "503",
                        "504",
                        "internal server error",
                        "bad gateway",
                        "service unavailable",
                        "gateway timeout",
                        "connection",
                        "timeout",
                        "network",
                    ]
                )

                # Also retry on JSON parsing errors which can be transient
                is_json_error = any(
                    keyword in error_msg
                    for keyword in [
                        "json",
                        "parsing",
                        "decode",
                        "invalid response format",
                    ]
                )

                # Retry for rate limits, server errors, and transient JSON errors
                should_retry = is_rate_limit or is_server_error or is_json_error

                if not should_retry:
                    print(f"❌ Non-retryable error: {str(e)[:100]}...")
                    raise e

                if attempt >= self.max_retries:
                    print(
                        f"❌ Max retries ({self.max_retries}) reached for the same request"
                    )
                    raise e

                # Calculate delay with exponential backoff and jitter
                delay = min(
                    self.base_delay * (self.backoff_multiplier**attempt),
                    self.max_delay,
                )
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.3) * delay
                total_delay = delay + jitter

                error_type = (
                    "Rate limit"
                    if is_rate_limit
                    else "Server error" if is_server_error else "JSON error"
                )
                print(
                    f"⚠️  {error_type} (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)[:80]}..."
                )
                print(
                    f"⏱️  Retrying SAME request in {total_delay:.1f}s with exponential backoff..."
                )
                await asyncio.sleep(total_delay)

        # Should not reach here, but just in case
        raise last_exception

    async def _rate_limit(self):
        """Enforce rate limiting between requests (minimum 2 seconds)."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(
                f"⏱️  Rate limiting: waiting {sleep_time:.1f}s (minimum {self.min_request_interval}s between requests)"
            )
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    async def _make_completion_request(self, **params):
        """Make a single completion request."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: litellm.completion(**params))

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ChatResponse:
        """Send a chat completion request using LiteLLM.

        Args:
            messages: List of messages
            tools: Optional list of tools/functions
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional parameters

        Returns:
            ChatResponse with unified format
        """
        try:
            # Convert messages to OpenAI format
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    # Already in dict format
                    formatted_messages.append(msg)
                    continue

                formatted_msg = {"role": msg.role, "content": msg.content}

                # Add tool-specific fields if present
                if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                    formatted_msg["tool_call_id"] = msg.tool_call_id
                if hasattr(msg, "name") and msg.name:
                    formatted_msg["name"] = msg.name
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    formatted_msg["tool_calls"] = msg.tool_calls

                formatted_messages.append(formatted_msg)

            # Prepare parameters
            params = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                **self.provider_kwargs,
                **kwargs,
            }

            # Add tools if provided with proper format validation
            if tools:
                # Check if we support function calling for this model
                supports_tools = litellm.supports_function_calling(self.model)

                if supports_tools:
                    # Handle both formats: OpenAI format and simple format
                    functions = []
                    for tool in tools:
                        if "type" in tool and tool["type"] == "function":
                            # Already in OpenAI format
                            functions.append(tool)
                        else:
                            # Convert simple format to OpenAI format
                            functions.append(
                                {
                                    "type": "function",
                                    "function": {
                                        "name": tool["name"],
                                        "description": tool["description"],
                                        "parameters": tool["parameters"],
                                    },
                                }
                            )
                    params["tools"] = functions
                    params["tool_choice"] = "auto"
                else:
                    print(
                        f"⚠️ Model {self.model} does not support function calling, tools will be ignored"
                    )

            # Make async request to LiteLLM with exponential backoff and retry
            response = await self._exponential_backoff_retry(
                self._make_completion_request, **params
            )

            # Extract response data
            choice = response.choices[0]
            message = choice.message

            # Extract content
            content = getattr(message, "content", "") or ""

            # Extract tool calls - support parallel function calling
            tool_calls = []
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    # Handle different formats of function data
                    function_data = tc.function
                    if hasattr(function_data, "model_dump"):
                        function_data = function_data.model_dump()
                    elif hasattr(function_data, "dict"):
                        function_data = function_data.dict()
                    elif not isinstance(function_data, dict):
                        # Convert to dict if it's an object
                        function_data = {
                            "name": getattr(function_data, "name", str(function_data)),
                            "arguments": getattr(function_data, "arguments", "{}"),
                        }

                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            type=tc.type,
                            function=function_data,
                        )
                    )

            # Extract usage and calculate cost
            usage = {}
            if hasattr(response, "usage") and response.usage:
                if hasattr(response.usage, "model_dump"):
                    usage = response.usage.model_dump()
                elif hasattr(response.usage, "dict"):
                    usage = response.usage.dict()
                else:
                    # Convert to dict manually
                    usage = {
                        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(
                            response.usage, "completion_tokens", 0
                        ),
                        "total_tokens": getattr(response.usage, "total_tokens", 0),
                    }

            cost = self._calculate_cost(usage, self.model)

            return ChatResponse(
                content=content, tool_calls=tool_calls, usage=usage, cost=cost
            )

        except Exception as e:
            # Unified error handling with retry for tool calling issues
            error_msg = self._format_error(e)
            print(f"❌ LiteLLM request failed: {error_msg}")
            raise Exception(f"LiteLLM request failed: {error_msg}")

    async def embedding(
        self, text: Union[str, List[str]], model: Optional[str] = None, **kwargs
    ) -> List[List[float]]:
        """Generate embeddings using LiteLLM.

        Args:
            text: Text or list of texts to embed
            model: Override default model for embeddings
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        try:
            # Use embedding model if specified, otherwise use text-embedding-ada-002
            embedding_model = model or self._get_embedding_model()

            # Ensure text is a list
            if isinstance(text, str):
                text = [text]

            # Make async request to LiteLLM
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: litellm.embedding(model=embedding_model, input=text, **kwargs),
            )

            # Extract embeddings
            embeddings = []
            for data in response.data:
                embeddings.append(data.embedding)

            return embeddings

        except Exception as e:
            error_msg = self._format_error(e)
            raise Exception(f"LiteLLM embedding request failed: {error_msg}")

    def _get_embedding_model(self) -> str:
        """Get appropriate embedding model for the provider."""
        embedding_models = {
            "openai": "text-embedding-ada-002",
            "openrouter": "openai/text-embedding-ada-002",
            "anthropic": "openai/text-embedding-ada-002",  # Fallback to OpenAI
            "cohere": "embed-english-v2.0",
            "huggingface": "sentence-transformers/all-MiniLM-L6-v2",
        }

        return embedding_models.get(self.provider, "text-embedding-ada-002")

    def _calculate_cost(self, usage: Dict[str, Any], model: str) -> float:
        """Calculate approximate cost based on usage."""
        try:
            # Get token counts
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            # Simple cost estimation - these are approximate rates
            cost_per_1k_tokens = {
                "openai/gpt-4": {"prompt": 0.03, "completion": 0.06},
                "openai/gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
                "anthropic/claude-3": {"prompt": 0.008, "completion": 0.024},
                "anthropic/claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
                "openrouter/anthropic/claude-3-haiku": {
                    "prompt": 0.00025,
                    "completion": 0.00125,
                },
            }

            # Default rates if model not found
            default_rates = {"prompt": 0.001, "completion": 0.002}
            rates = cost_per_1k_tokens.get(model, default_rates)

            # Calculate cost
            prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
            completion_cost = (completion_tokens / 1000) * rates["completion"]

            return prompt_cost + completion_cost

        except Exception:
            # Return 0 if calculation fails
            return 0.0

    def _format_error(self, error: Exception) -> str:
        """Format error message for unified error handling."""
        error_str = str(error)

        # Common error patterns and their user-friendly messages
        error_patterns = {
            "authentication": "Invalid API key. Please check your API key configuration.",
            "rate_limit": "Rate limit exceeded. Please try again later.",
            "quota": "API quota exceeded. Please check your billing settings.",
            "model_not_found": f"Model '{self.model}' not found. Please check the model name.",
            "invalid_request": "Invalid request format. Please check your parameters.",
            "network": "Network error. Please check your internet connection.",
            "timeout": "Request timed out. Please try again.",
        }

        # Check for known error patterns
        for pattern, message in error_patterns.items():
            if pattern in error_str.lower():
                return message

        # Return original error if no pattern matches
        return error_str

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "LiteLLMProvider":
        """Create provider from configuration dictionary."""
        # Filter out unsupported parameters that LiteLLM doesn't accept
        supported_params = {"model", "api_key", "api_base", "temperature", "max_tokens"}
        filtered_config = {k: v for k, v in config.items() if k in supported_params}

        return cls(
            model=filtered_config.get("model", "openai/gpt-3.5-turbo"),
            api_key=filtered_config.get("api_key"),
            api_base=filtered_config.get("api_base"),
            temperature=filtered_config.get("temperature", 0.1),
            max_tokens=filtered_config.get("max_tokens", 4000),
        )

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported providers."""
        return [
            "openai",
            "anthropic",
            "claude",
            "openrouter",
            "together",
            "replicate",
            "cohere",
            "huggingface",
            "bedrock",
            "azure",
            "vertexai",
            "palm",
        ]

    @classmethod
    def get_provider_models(cls, provider: str) -> List[str]:
        """Get available models for a provider."""
        # This is a simplified list - in production, you might want to query the provider's API
        provider_models = {
            "openai": ["gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "openrouter": [
                "anthropic/claude-3-opus",
                "anthropic/claude-3-sonnet",
                "anthropic/claude-3-haiku",
                "openai/gpt-4",
                "openai/gpt-3.5-turbo",
            ],
            "together": [
                "meta-llama/Llama-2-70b-chat-hf",
                "NousResearch/Nous-Hermes-2-Yi-34B",
            ],
            "cohere": ["command", "command-light"],
        }

        return provider_models.get(provider, [])

    async def close(self):
        """Clean up resources."""
        # LiteLLM doesn't require explicit cleanup, but this method is provided for interface consistency
        pass
