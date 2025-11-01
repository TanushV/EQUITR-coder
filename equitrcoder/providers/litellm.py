import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import litellm
import threading


@dataclass
class Message:
    role: str
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ToolCall:
    id: str
    type: str = "function"
    function: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0


logger = logging.getLogger(__name__)


class LiteLLMProvider:
    """Unified LLM provider using LiteLLM for multiple providers."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
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
        litellm.drop_params = True
        litellm.set_verbose = False

        # Additional provider-specific settings
        self.provider_kwargs = kwargs

        # Exponential backoff configuration
        self.max_retries = 5
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 60.0  # Maximum delay in seconds
        self.backoff_multiplier = 2.0

        # Instance-local rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests (instance-level)

        # Global rate limiting (shared across all providers)
        # Defaults can be overridden via environment variables
        try:
            self.global_min_interval = float(
                os.environ.get("EQUITR_LLM_GLOBAL_MIN_INTERVAL", "2.0")
            )
        except Exception:
            self.global_min_interval = 2.0
        try:
            self.global_max_concurrency = int(
                os.environ.get("EQUITR_LLM_GLOBAL_MAX_CONCURRENCY", "2")
            )
        except Exception:
            self.global_max_concurrency = 2

        # Initialize global primitives (module-level singletons)
        _RateLimitGlobals.init(self.global_max_concurrency)

        # Simple in-memory response cache (disabled by default via env)
        self._enable_cache = os.environ.get("EQUITR_ENABLE_LLM_CACHE", "1") == "1"
        self._cache: Dict[str, ChatResponse] = {}

    def _setup_api_key(self, api_key: Optional[str] = None) -> None:
        if self.provider == "moonshot":
            if api_key:
                os.environ["MOONSHOT_API_KEY"] = api_key
            os.environ.setdefault("MOONSHOT_API_BASE", "https://api.moonshot.ai/v1")
            return

        if not api_key:
            return

        if self.provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif self.provider == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif self.provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        else:
            os.environ["API_KEY"] = api_key

    def _get_api_key_env_var(self) -> str:
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

    def _setup_api_base(self, api_base: str) -> None:
        if self.provider == "openai":
            os.environ["OPENAI_API_BASE"] = api_base
        elif self.provider == "openrouter":
            os.environ["OPENROUTER_API_BASE"] = api_base
        elif self.provider == "moonshot":
            os.environ["MOONSHOT_API_BASE"] = api_base

    async def _exponential_backoff_retry(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                await self._rate_limit()
                await self._global_gate()
                if attempt > 0:
                    print(
                        f"🔄 Retry attempt {attempt}/{self.max_retries} for the SAME request..."
                    )
                try:
                    result = await func(*args, **kwargs)
                finally:
                    _RateLimitGlobals.release_slot()
                return result
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                if any(
                    k in error_msg
                    for k in [
                        "authentication",
                        "unauthorized",
                        "invalid key",
                        "api key",
                        "invalid_api_key",
                    ]
                ):
                    print(f"❌ Authentication error, not retrying: {e}")
                    raise e
                if any(
                    k in error_msg
                    for k in [
                        "model not found",
                        "invalid model",
                        "model does not exist",
                        "unsupported model",
                    ]
                ):
                    print(f"❌ Model error, not retrying: {e}")
                    raise e
                is_rate_limit = any(
                    k in error_msg
                    for k in [
                        "rate limit",
                        "quota",
                        "429",
                        "too many requests",
                        "retry-after",
                    ]
                )
                is_server_error = any(
                    k in error_msg
                    for k in [
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
                is_json_error = any(
                    k in error_msg
                    for k in ["json", "parsing", "decode", "invalid response format"]
                )
                should_retry = is_rate_limit or is_server_error or is_json_error
                if not should_retry:
                    print(f"❌ Non-retryable error: {str(e)[:100]}...")
                    raise e
                if attempt >= self.max_retries:
                    print(
                        f"❌ Max retries ({self.max_retries}) reached for the same request"
                    )
                    raise e
                delay = min(
                    self.base_delay * (self.backoff_multiplier**attempt), self.max_delay
                )
                jitter = random.uniform(0.1, 0.3) * delay
                total_delay = delay + jitter
                error_type = (
                    "Rate limit"
                    if is_rate_limit
                    else ("Server error" if is_server_error else "JSON error")
                )
                print(
                    f"⚠️  {error_type} (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)[:80]}..."
                )
                print(
                    f"⏱️  Retrying SAME request in {total_delay:.1f}s with exponential backoff..."
                )
                await asyncio.sleep(total_delay)
        raise last_exception

    async def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(
                f"⏱️  Rate limiting: waiting {sleep_time:.1f}s (minimum {self.min_request_interval}s between requests)"
            )
            await asyncio.sleep(sleep_time)
        self.last_request_time = time.time()

    async def _global_gate(self):
        """Global gate enforcing max concurrency and minimum interval across all providers."""
        # Enforce global min interval (coarse-grained) by sleeping between tokens
        # Use a simple timestamp shared across processes via _RateLimitGlobals
        sleep_needed = _RateLimitGlobals.seconds_until_next_allowed(
            self.global_min_interval
        )
        if sleep_needed > 0:
            print(
                f"⏱️  Global rate limiting: waiting {sleep_needed:.1f}s (min interval {self.global_min_interval}s)"
            )
            await asyncio.sleep(sleep_needed)
        # Acquire concurrency slot (async-compatible via thread pool semaphore pattern)
        acquired = await _RateLimitGlobals.acquire_slot_async()
        if not acquired:
            # As a fallback, wait briefly and continue
            await asyncio.sleep(self.global_min_interval)
            await _RateLimitGlobals.acquire_slot_async()

    # --- Provider request helpers and chat implementation ---
    async def _make_completion_request(self, **params):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: litellm.completion(**params))

    async def _make_responses_request(self, **params):
        """Call provider Responses API via LiteLLM in a worker thread.

        This enables modern reasoning models (e.g. GPT-5 family) to interleave
        tool calls during reasoning. We call the blocking SDK in a thread to
        avoid blocking the event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: litellm.responses(**params))

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ChatResponse:
        try:
            # Cache key based on model + messages + tools
            if self._enable_cache:
                try:
                    import hashlib
                    import json as _json

                    cache_payload = {
                        "model": self.model,
                        "messages": [
                            (
                                msg
                                if isinstance(msg, dict)
                                else {"role": msg.role, "content": msg.content}
                            )
                            for msg in messages
                        ],
                        "tools": tools or [],
                    }
                    cache_key = hashlib.sha256(
                        _json.dumps(cache_payload, sort_keys=True).encode("utf-8")
                    ).hexdigest()
                    if cache_key in self._cache:
                        return self._cache[cache_key]
                except Exception:
                    cache_key = None
            else:
                cache_key = None
            formatted_messages: List[Dict[str, Any]] = []
            for msg in messages:
                if isinstance(msg, dict):
                    formatted_messages.append(msg)
                    continue
                formatted_msg: Dict[str, Any] = {
                    "role": msg.role,
                    "content": msg.content,
                }
                if getattr(msg, "tool_call_id", None):
                    formatted_msg["tool_call_id"] = msg.tool_call_id
                if getattr(msg, "name", None):
                    formatted_msg["name"] = msg.name
                if getattr(msg, "tool_calls", None):
                    formatted_msg["tool_calls"] = msg.tool_calls
                formatted_messages.append(formatted_msg)

            params: Dict[str, Any] = {
                "model": self.model,
                "messages": formatted_messages,
                **self.provider_kwargs,
                **kwargs,
            }
            # Only include temperature when supported; OpenAI o-series and gpt-5 ignore temperature
            effective_temp = (
                temperature if temperature is not None else self.temperature
            )
            if effective_temp is not None:
                if not (
                    self.model.startswith("gpt-5")
                    or self.model.startswith("gpt-4.1")
                    or self.model.startswith("o3")
                ):
                    params["temperature"] = effective_temp
            # Token parameter handling: avoid sending unsupported keys by default
            # Only include token limits when explicitly requested
            requested_tokens = max_tokens if max_tokens is not None else self.max_tokens
            if requested_tokens is not None:
                # Some newer models require 'max_completion_tokens' or 'max_output_tokens'
                if self.model.startswith("gpt-5") or self.model.startswith("gpt-4.1"):
                    params["max_completion_tokens"] = requested_tokens
                elif self.model.startswith("o3") or ("grok" in self.model.lower()):
                    params["max_output_tokens"] = requested_tokens
                else:
                    params["max_tokens"] = requested_tokens

            # Enable reasoning/thinking when supported by the model
            try:
                supports_reason = hasattr(
                    litellm, "supports_reasoning"
                ) and litellm.supports_reasoning(model=self.model)
            except Exception:
                supports_reason = False
            if supports_reason:
                # Prefer modern reasoning params for GPT-5 and o-series; fall back to legacy where needed
                reasoning_effort = "high"
                try:
                    from ..core.unified_config import (
                        get_config,
                    )  # local import to avoid cycles

                    enable_thinking = get_config("llm.enable_thinking", True)
                    budget_tokens = get_config("llm.reasoning_budget_tokens", 1024)
                except Exception:
                    enable_thinking = True
                    budget_tokens = 1024
                if self.model.startswith("gpt-5") or self.model.startswith("o3"):
                    # Use modern 'reasoning' object; do NOT send reasoning_effort param
                    params["reasoning"] = {"effort": reasoning_effort}
                else:
                    # Legacy/other models: use reasoning_effort and optional thinking
                    params["reasoning_effort"] = reasoning_effort
                    if enable_thinking and "thinking" not in params:
                        try:
                            params["thinking"] = {
                                "type": "enabled",
                                "budget_tokens": int(budget_tokens),
                            }
                        except Exception:
                            # Fallback silently if budget invalid
                            params["thinking"] = {"type": "enabled"}

            # Prepare tools/functions for either API style
            if tools:
                supports_tools = litellm.supports_function_calling(self.model)
                if supports_tools:
                    functions: List[Dict[str, Any]] = []
                    for tool in tools:
                        if isinstance(tool, dict) and tool.get("type") == "function":
                            functions.append(tool)
                        else:
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

            # Decide API: use Responses API for GPT-5 family and similar if available
            # Prefer Responses API when available to allow mid-reasoning tool use.
            # Try broadly (with safe fallback) so compatible models beyond GPT-5/Grok also benefit.
            should_try_responses = hasattr(litellm, "responses") and (
                self.model.startswith("gpt-5")
                or self.model.startswith("o3")
                or ("grok" in self.model.lower())
                or bool(tools)  # optimistic: try when tools are provided
            )

            if should_try_responses:
                # Map params -> responses params
                responses_params: Dict[str, Any] = {
                    k: v for k, v in params.items() if k != "messages"
                }
                responses_params["input"] = formatted_messages
                # Tokens: prefer max_output_tokens for responses
                if "max_completion_tokens" in responses_params:
                    responses_params["max_output_tokens"] = responses_params.pop(
                        "max_completion_tokens"
                    )
                # Call responses API (safe fallback to chat.completions on error)
                try:
                    response = await self._exponential_backoff_retry(
                        self._make_responses_request, **responses_params
                    )
                except Exception:
                    response = None

                # Attempt to parse either classic fields or responses output items
                content_parts: List[str] = []
                tool_calls: List[ToolCall] = []

                # First, check if LiteLLM normalized to choices/message
                if response is not None:
                    try:
                        choice = getattr(response, "choices", [None])[0]
                        message = getattr(choice, "message", None)
                        if message is not None:
                            content_text = getattr(message, "content", "") or ""
                            if content_text:
                                content_parts.append(content_text)
                            if hasattr(message, "tool_calls") and message.tool_calls:
                                for tc in message.tool_calls:
                                    function_data = getattr(tc, "function", {})
                                    if hasattr(function_data, "model_dump"):
                                        function_data = function_data.model_dump()
                                    elif hasattr(function_data, "dict"):
                                        function_data = function_data.dict()
                                    elif not isinstance(function_data, dict):
                                        function_data = {
                                            "name": getattr(
                                                function_data,
                                                "name",
                                                str(function_data),
                                            ),
                                            "arguments": getattr(
                                                function_data, "arguments", "{}"
                                            ),
                                        }
                                    tool_calls.append(
                                        ToolCall(
                                            id=getattr(tc, "id", ""),
                                            type=getattr(tc, "type", "function"),
                                            function=function_data,
                                        )
                                    )
                    except Exception:
                        pass

                # If no normalized choices, parse responses.output
                if response is not None and (not content_parts or not tool_calls):
                    try:
                        output_items = getattr(response, "output", None)
                        if output_items:
                            import json as _json  # local import to avoid global dependency

                            for item in output_items:
                                item_type = str(getattr(item, "type", "") or "").lower()
                                # Aggregate text content from message/content segments
                                if hasattr(item, "content") and getattr(
                                    item, "content"
                                ):
                                    for piece in getattr(item, "content", []) or []:
                                        text_value = getattr(piece, "text", None)
                                        if isinstance(text_value, str) and text_value:
                                            content_parts.append(text_value)
                                # Detect tool use segments
                                if item_type in ("tool_use", "tool_call"):
                                    call_id = (
                                        getattr(item, "id", None)
                                        or getattr(item, "tool_call_id", None)
                                        or f"call_{len(tool_calls)+1}"
                                    )
                                    function_name = (
                                        getattr(item, "name", None)
                                        or getattr(
                                            getattr(item, "function", None),
                                            "name",
                                            None,
                                        )
                                        or "tool"
                                    )
                                    raw_args = getattr(
                                        item, "arguments", None
                                    ) or getattr(item, "input", None)
                                    if isinstance(raw_args, str):
                                        arguments_str = raw_args
                                    else:
                                        try:
                                            arguments_str = _json.dumps(raw_args or {})
                                        except Exception:
                                            arguments_str = "{}"
                                    function_payload = {
                                        "name": function_name,
                                        "arguments": arguments_str,
                                    }
                                    tool_calls.append(
                                        ToolCall(
                                            id=str(call_id),
                                            type="function",
                                            function=function_payload,
                                        )
                                    )
                    except Exception:
                        pass

                # Usage mapping
                usage: Dict[str, Any] = {}
                try:
                    if (
                        response is not None
                        and hasattr(response, "usage")
                        and response.usage
                    ):
                        raw_usage = response.usage
                        if hasattr(raw_usage, "model_dump"):
                            u = raw_usage.model_dump()
                        elif hasattr(raw_usage, "dict"):
                            u = raw_usage.dict()
                        else:
                            u = {
                                "input_tokens": getattr(raw_usage, "input_tokens", 0),
                                "output_tokens": getattr(raw_usage, "output_tokens", 0),
                                "total_tokens": getattr(raw_usage, "total_tokens", 0),
                            }
                        usage = {
                            "prompt_tokens": int(
                                u.get("input_tokens", u.get("prompt_tokens", 0)) or 0
                            ),
                            "completion_tokens": int(
                                u.get("output_tokens", u.get("completion_tokens", 0))
                                or 0
                            ),
                            "total_tokens": int(
                                u.get("total_tokens", 0)
                                or (
                                    int(u.get("input_tokens", 0) or 0)
                                    + int(u.get("output_tokens", 0) or 0)
                                )
                            ),
                        }
                except Exception:
                    usage = {}

                content = ("\n".join(content_parts)).strip()
                cost = self._calculate_cost(usage, self.model)
                if response is not None:
                    resp = ChatResponse(
                        content=content, tool_calls=tool_calls, usage=usage, cost=cost
                    )
                    if self._enable_cache and cache_key:
                        self._cache[cache_key] = resp
                    return resp

            # Default: classic Chat Completions path
            response = await self._exponential_backoff_retry(
                self._make_completion_request, **params
            )

            choice = response.choices[0]
            message = choice.message
            content = getattr(message, "content", "") or ""

            tool_calls: List[ToolCall] = []
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    function_data = tc.function
                    if hasattr(function_data, "model_dump"):
                        function_data = function_data.model_dump()
                    elif hasattr(function_data, "dict"):
                        function_data = function_data.dict()
                    elif not isinstance(function_data, dict):
                        function_data = {
                            "name": getattr(function_data, "name", str(function_data)),
                            "arguments": getattr(function_data, "arguments", "{}"),
                        }
                    tool_calls.append(
                        ToolCall(id=tc.id, type=tc.type, function=function_data)
                    )

            usage: Dict[str, Any] = {}
            if hasattr(response, "usage") and response.usage:
                if hasattr(response.usage, "model_dump"):
                    usage = response.usage.model_dump()
                elif hasattr(response.usage, "dict"):
                    usage = response.usage.dict()
                else:
                    usage = {
                        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(
                            response.usage, "completion_tokens", 0
                        ),
                        "total_tokens": getattr(response.usage, "total_tokens", 0),
                    }

            cost = self._calculate_cost(usage, self.model)
            resp = ChatResponse(
                content=content, tool_calls=tool_calls, usage=usage, cost=cost
            )
            if self._enable_cache and cache_key:
                self._cache[cache_key] = resp
            return resp

        except Exception as e:
            error_msg = self._format_error(e)
            print(f"❌ LiteLLM request failed: {error_msg}")
            raise Exception(f"LiteLLM request failed: {error_msg}")

    def _calculate_cost(self, usage: Dict[str, Any], model: str) -> float:
        try:
            # Prefer accurate pricing from litellm
            prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens = int(usage.get("completion_tokens", 0) or 0)
            # cost_per_token returns absolute USD cost for the given token counts
            prompt_usd, completion_usd = (0.0, 0.0)
            try:
                if hasattr(litellm, "cost_per_token"):
                    prompt_usd, completion_usd = litellm.cost_per_token(
                        model=self.model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    )
            except Exception:
                # If litellm doesn't support this model, fall back to zero cost
                prompt_usd, completion_usd = (0.0, 0.0)
            total = float(prompt_usd or 0.0) + float(completion_usd or 0.0)
            return total
        except Exception:
            return 0.0

    def _format_error(self, error: Exception) -> str:
        error_str = str(error)
        error_patterns = {
            "authentication": "Invalid API key. Please check your API key configuration.",
            "rate_limit": "Rate limit exceeded. Please try again later.",
            "quota": "API quota exceeded. Please check your billing settings.",
            "model_not_found": f"Model '{self.model}' not found. Please check the model name.",
            "invalid_request": "Invalid request format. Please check your parameters.",
            "network": "Network error. Please check your internet connection.",
            "timeout": "Request timed out. Please try again.",
        }
        for pattern, message in error_patterns.items():
            if pattern in error_str.lower():
                return message
        return error_str


class _RateLimitGlobals:
    """Module-level global rate limiting primitives."""

    _semaphore: Optional[asyncio.Semaphore] = None
    _lock = threading.Lock()
    _last_request_ts: float = 0.0

    @classmethod
    def init(cls, max_concurrency: int) -> None:
        # Initialize once with the maximum of existing or requested capacity
        with cls._lock:
            if cls._semaphore is None:
                cls._semaphore = asyncio.Semaphore(max(1, max_concurrency))

    @classmethod
    async def acquire_slot_async(cls) -> bool:
        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(1)
        await cls._semaphore.acquire()
        return True

    @classmethod
    def release_slot(cls) -> None:
        try:
            if cls._semaphore is not None and cls._semaphore.locked():
                cls._semaphore.release()
        except Exception:
            # Swallow release errors to avoid masking upstream failures
            pass

    @classmethod
    def seconds_until_next_allowed(cls, min_interval: float) -> float:
        """Return seconds to wait to respect a global min interval."""
        with cls._lock:
            now = time.time()
            delta = now - cls._last_request_ts
            if delta < min_interval:
                wait = min_interval - delta
            else:
                wait = 0.0
            # Update last timestamp to projected next moment to serialize starts
            next_ts = now + (wait if wait > 0 else 0)
            cls._last_request_ts = next_ts
            return wait

    async def _make_completion_request(self, **params):
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
        try:
            formatted_messages: List[Dict[str, Any]] = []
            for msg in messages:
                if isinstance(msg, dict):
                    formatted_messages.append(msg)
                    continue
                formatted_msg: Dict[str, Any] = {
                    "role": msg.role,
                    "content": msg.content,
                }
                if getattr(msg, "tool_call_id", None):
                    formatted_msg["tool_call_id"] = msg.tool_call_id
                if getattr(msg, "name", None):
                    formatted_msg["name"] = msg.name
                if getattr(msg, "tool_calls", None):
                    formatted_msg["tool_calls"] = msg.tool_calls
                formatted_messages.append(formatted_msg)

            params: Dict[str, Any] = {
                "model": self.model,
                "messages": formatted_messages,
                **self.provider_kwargs,
                **kwargs,
            }
            # Only include temperature when supported; some Canary models accept default only
            effective_temp = (
                temperature if temperature is not None else self.temperature
            )
            if effective_temp is not None:
                if not (
                    self.model.startswith("gpt-5") or self.model.startswith("gpt-4.1")
                ):
                    params["temperature"] = effective_temp
            # Token parameter handling: avoid sending unsupported keys by default
            # Only include token limits when explicitly requested
            requested_tokens = max_tokens if max_tokens is not None else self.max_tokens
            if requested_tokens is not None:
                # Some newer models require 'max_completion_tokens' instead of 'max_tokens'
                if self.model.startswith("gpt-5") or self.model.startswith("gpt-4.1"):
                    params["max_completion_tokens"] = requested_tokens
                else:
                    params["max_tokens"] = requested_tokens

            # Enable reasoning/thinking when supported by the model
            try:
                supports_reason = hasattr(
                    litellm, "supports_reasoning"
                ) and litellm.supports_reasoning(model=self.model)
            except Exception:
                supports_reason = False
            if supports_reason:
                # Default to medium effort; allow overrides via provider_kwargs or config
                reasoning_effort = self.provider_kwargs.get("reasoning_effort")
                try:
                    from ..core.unified_config import (
                        get_config,
                    )  # local import to avoid cycles

                    reasoning_effort = reasoning_effort or get_config(
                        "llm.reasoning_effort", None
                    )
                    enable_thinking = get_config("llm.enable_thinking", True)
                    budget_tokens = get_config("llm.reasoning_budget_tokens", 1024)
                except Exception:
                    enable_thinking = True
                    budget_tokens = 1024
                if not reasoning_effort:
                    reasoning_effort = "medium"
                params["reasoning_effort"] = reasoning_effort
                if enable_thinking and "thinking" not in params:
                    try:
                        params["thinking"] = {
                            "type": "enabled",
                            "budget_tokens": int(budget_tokens),
                        }
                    except Exception:
                        # Fallback silently if budget invalid
                        params["thinking"] = {"type": "enabled"}

            if tools:
                supports_tools = litellm.supports_function_calling(self.model)
                if supports_tools:
                    functions: List[Dict[str, Any]] = []
                    for tool in tools:
                        if isinstance(tool, dict) and tool.get("type") == "function":
                            functions.append(tool)
                        else:
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

            response = await self._exponential_backoff_retry(
                self._make_completion_request, **params
            )

            choice = response.choices[0]
            message = choice.message
            content = getattr(message, "content", "") or ""

            tool_calls: List[ToolCall] = []
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    function_data = tc.function
                    if hasattr(function_data, "model_dump"):
                        function_data = function_data.model_dump()
                    elif hasattr(function_data, "dict"):
                        function_data = function_data.dict()
                    elif not isinstance(function_data, dict):
                        function_data = {
                            "name": getattr(function_data, "name", str(function_data)),
                            "arguments": getattr(function_data, "arguments", "{}"),
                        }
                    tool_calls.append(
                        ToolCall(id=tc.id, type=tc.type, function=function_data)
                    )

            usage: Dict[str, Any] = {}
            if hasattr(response, "usage") and response.usage:
                if hasattr(response.usage, "model_dump"):
                    usage = response.usage.model_dump()
                elif hasattr(response.usage, "dict"):
                    usage = response.usage.dict()
                else:
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
            error_msg = self._format_error(e)
            print(f"❌ LiteLLM request failed: {error_msg}")
            raise Exception(f"LiteLLM request failed: {error_msg}")

    async def embedding(
        self, text: Union[str, List[str]], model: Optional[str] = None, **kwargs
    ) -> List[List[float]]:
        try:
            embedding_model = model or self._get_embedding_model()
            if isinstance(text, str):
                text = [text]
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: litellm.embedding(model=embedding_model, input=text, **kwargs),
            )
            embeddings: List[List[float]] = []
            for data in response.data:
                embeddings.append(data.embedding)
            return embeddings
        except Exception as e:
            error_msg = self._format_error(e)
            raise Exception(f"LiteLLM embedding request failed: {error_msg}")

    def _get_embedding_model(self) -> str:
        embedding_models = {
            "openai": "text-embedding-ada-002",
            "openrouter": "openai/text-embedding-ada-002",
            "anthropic": "openai/text-embedding-ada-002",
            "cohere": "embed-english-v2.0",
            "huggingface": "sentence-transformers/all-MiniLM-L6-v2",
        }
        return embedding_models.get(self.provider, "text-embedding-ada-002")

    def _calculate_cost(self, usage: Dict[str, Any], model: str) -> float:
        try:
            # Prefer accurate pricing from litellm
            prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens = int(usage.get("completion_tokens", 0) or 0)
            # cost_per_token returns absolute USD cost for the given token counts
            prompt_usd, completion_usd = (0.0, 0.0)
            try:
                if hasattr(litellm, "cost_per_token"):
                    prompt_usd, completion_usd = litellm.cost_per_token(
                        model=self.model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    )
            except Exception:
                # If litellm doesn't support this model, fall back to zero cost
                prompt_usd, completion_usd = (0.0, 0.0)
            total = float(prompt_usd or 0.0) + float(completion_usd or 0.0)
            return total
        except Exception:
            return 0.0

    def _format_error(self, error: Exception) -> str:
        error_str = str(error)
        error_patterns = {
            "authentication": "Invalid API key. Please check your API key configuration.",
            "rate_limit": "Rate limit exceeded. Please try again later.",
            "quota": "API quota exceeded. Please check your billing settings.",
            "model_not_found": f"Model '{self.model}' not found. Please check the model name.",
            "invalid_request": "Invalid request format. Please check your parameters.",
            "network": "Network error. Please check your internet connection.",
            "timeout": "Request timed out. Please try again.",
        }
        for pattern, message in error_patterns.items():
            if pattern in error_str.lower():
                return message
        return error_str

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "LiteLLMProvider":
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
        pass
