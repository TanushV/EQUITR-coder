from typing import List

import tiktoken

from ..providers.openrouter import Message


class ContextManager:
    """Manages conversation context and token limits."""

    def __init__(self, max_tokens: int = 100000, model: str = "gpt-3.5-turbo"):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model(
            "gpt-3.5-turbo"
        )  # Use default encoding

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback to rough estimation
            return len(text) // 4

    def count_message_tokens(self, message: Message) -> int:
        """Count tokens in a message."""
        return self.count_tokens(message.content) + 4  # +4 for message overhead

    def truncate_context(
        self, messages: List[Message], system_prompt: str = ""
    ) -> List[Message]:
        """Truncate context to fit within token limits."""
        if not messages:
            return messages

        # Always keep system prompt and first user message
        result: List[Message] = []
        total_tokens = self.count_tokens(system_prompt)

        # Keep the last message (most recent)
        if messages:
            last_msg = messages[-1]
            result.insert(0, last_msg)
            total_tokens += self.count_message_tokens(last_msg)

        # Add messages from the end, working backwards
        for i in range(len(messages) - 2, -1, -1):
            msg = messages[i]
            msg_tokens = self.count_message_tokens(msg)

            if total_tokens + msg_tokens > self.max_tokens:
                break

            result.insert(0, msg)
            total_tokens += msg_tokens

        return result

    def should_truncate(self, messages: List[Message], system_prompt: str = "") -> bool:
        """Check if context needs truncation."""
        total_tokens = self.count_tokens(system_prompt)
        total_tokens += sum(self.count_message_tokens(msg) for msg in messages)
        return total_tokens > self.max_tokens

    def get_context_summary(self, messages: List[Message]) -> str:
        """Generate a summary of the context."""
        if not messages:
            return "Empty conversation"

        total_messages = len(messages)
        total_tokens = sum(self.count_message_tokens(msg) for msg in messages)

        return f"Context: {total_messages} messages, ~{total_tokens} tokens"
