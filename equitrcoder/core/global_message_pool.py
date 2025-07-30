# equitrcoder/core/global_message_pool.py

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class AgentMessage:
    """A simple, clean message structure for inter-agent communication."""
    sender: str
    recipient: Optional[str]  # None for broadcast
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class GlobalMessagePool:
    """A simple, clean, in-memory message bus for agent communication."""

    def __init__(self):
        self._messages: List[AgentMessage] = []
        self._lock = asyncio.Lock()
        self._agent_queues: Dict[str, asyncio.Queue] = {}

    async def register_agent(self, agent_id: str):
        """Register an agent to receive messages."""
        async with self._lock:
            if agent_id not in self._agent_queues:
                self._agent_queues[agent_id] = asyncio.Queue()

    async def post_message(self, sender: str, content: str, recipient: Optional[str] = None, metadata: Optional[Dict] = None):
        """Post a message to the pool."""
        msg = AgentMessage(sender=sender, recipient=recipient, content=content, metadata=metadata or {})
        
        async with self._lock:
            self._messages.append(msg)
            
            if recipient:
                # Direct message
                if recipient in self._agent_queues:
                    await self._agent_queues[recipient].put(msg)
            else:
                # Broadcast message
                for agent_id, queue in self._agent_queues.items():
                    if agent_id != sender: # Don't send to self
                        await queue.put(msg)

    async def get_messages(self, agent_id: str) -> List[AgentMessage]:
        """Get all pending messages for an agent."""
        messages = []
        if agent_id in self._agent_queues:
            queue = self._agent_queues[agent_id]
            while not queue.empty():
                messages.append(queue.get_nowait())
        return messages

# Create a single, global instance to be used by all agents.
global_message_pool = GlobalMessagePool()