import os
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, Any]


class ChatResponse(BaseModel):
    content: str
    tool_calls: List[ToolCall] = []
    usage: Dict[str, Any] = {}
    cost: float = 0.0


class OpenRouterProvider:
    def __init__(
        self, api_key: str, model: str, api_base: str = "https://openrouter.ai/api/v1"
    ):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/equitr/EQUITR-coder",
                "X-Title": "EQUITR Coder",
            },
            timeout=60.0,
        )

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
    ) -> ChatResponse:
        """Send a chat completion request to OpenRouter."""

        # Convert messages to OpenAI format
        formatted_messages = []
        for msg in messages:
            formatted_msg = {"role": msg.role, "content": msg.content}
            # Add tool-specific fields if present
            if msg.tool_call_id:
                formatted_msg["tool_call_id"] = msg.tool_call_id
            if msg.name:
                formatted_msg["name"] = msg.name
            if msg.tool_calls:
                formatted_msg["tool_calls"] = msg.tool_calls
            formatted_messages.append(formatted_msg)

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add tools if provided
        if tools:
            # Convert tools to OpenAI function calling format
            functions = []
            for tool in tools:
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
            payload["tools"] = functions
            payload["tool_choice"] = "auto"

        try:
            response = await self.client.post(
                f"{self.api_base}/chat/completions", json=payload
            )
            response.raise_for_status()

            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]

            # Extract content
            content = message.get("content", "") or ""

            # Extract tool calls
            tool_calls = []
            if "tool_calls" in message and message["tool_calls"]:
                for tc in message["tool_calls"]:
                    tool_calls.append(
                        ToolCall(id=tc["id"], type=tc["type"], function=tc["function"])
                    )

            # Calculate cost (rough estimation)
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            # Rough cost calculation (varies by model)
            cost = (prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000

            return ChatResponse(
                content=content, tool_calls=tool_calls, usage=usage, cost=cost
            )

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except Exception:
                error_detail = str(e)

            raise Exception(f"OpenRouter API error: {error_detail}")

        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @classmethod
    def from_env(cls, model: str = "anthropic/claude-3-haiku") -> "OpenRouterProvider":
        """Create provider from environment variables."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Get your API key from https://openrouter.ai"
            )

        return cls(api_key=api_key, model=model)
