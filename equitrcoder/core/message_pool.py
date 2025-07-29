"""Global message pool for inter-agent communication."""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class MessageType(Enum):
    """Types of messages agents can send."""

    INFO = "info"
    REQUEST = "request"
    RESPONSE = "response"
    STATUS_UPDATE = "status_update"
    COORDINATION = "coordination"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""

    id: str
    sender_agent: str
    recipient_agent: Optional[str]  # None for broadcast messages
    message_type: MessageType
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    task_id: Optional[str] = None
    thread_id: Optional[str] = None
    priority: int = 5  # 1-10, higher is more urgent

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        data["message_type"] = MessageType(data["message_type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class MessagePool:
    """Global message pool for agent communication."""

    def __init__(self, max_messages: int = 1000):
        self.max_messages = max_messages
        self.messages: List[AgentMessage] = []
        self.message_index: Dict[str, AgentMessage] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = (
            {}
        )  # agent -> set of message types
        self.message_queues: Dict[str, asyncio.Queue] = {}  # agent -> message queue
        self.lock = asyncio.Lock()
        self._message_counter = 0

    async def register_agent(
        self, agent_name: str, subscriptions: Optional[List[str]] = None
    ):
        """Register an agent with the message pool."""
        async with self.lock:
            if subscriptions is None:
                subscriptions = [msg_type.value for msg_type in MessageType]

            self.agent_subscriptions[agent_name] = set(subscriptions)
            self.message_queues[agent_name] = asyncio.Queue()

    async def unregister_agent(self, agent_name: str):
        """Unregister an agent from the message pool."""
        async with self.lock:
            self.agent_subscriptions.pop(agent_name, None)
            self.message_queues.pop(agent_name, None)

    async def send_message(
        self,
        sender_agent: str,
        content: str,
        message_type: MessageType = MessageType.INFO,
        recipient_agent: Optional[str] = None,
        task_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: int = 5,
    ) -> str:
        """Send a message to the pool."""
        async with self.lock:
            self._message_counter += 1
            message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._message_counter}"

            message = AgentMessage(
                id=message_id,
                sender_agent=sender_agent,
                recipient_agent=recipient_agent,
                message_type=message_type,
                content=content,
                metadata=metadata or {},
                timestamp=datetime.now(),
                task_id=task_id,
                thread_id=thread_id,
                priority=priority,
            )

            # Add to message history
            self.messages.append(message)
            self.message_index[message_id] = message

            # Trim messages if we exceed max
            if len(self.messages) > self.max_messages:
                old_message = self.messages.pop(0)
                self.message_index.pop(old_message.id, None)

            # Route message to appropriate agents
            await self._route_message(message)

            return message_id

    async def _route_message(self, message: AgentMessage):
        """Route message to appropriate agent queues."""
        target_agents = []

        if message.recipient_agent:
            # Direct message to specific agent
            if message.recipient_agent in self.message_queues:
                target_agents.append(message.recipient_agent)
        else:
            # Broadcast message to all subscribed agents
            for agent_name, subscriptions in self.agent_subscriptions.items():
                if (
                    message.message_type.value in subscriptions
                    and agent_name != message.sender_agent
                ):  # Don't send to sender
                    target_agents.append(agent_name)

        # Add message to target agent queues
        for agent_name in target_agents:
            if agent_name in self.message_queues:
                try:
                    await self.message_queues[agent_name].put(message)
                except asyncio.QueueFull:
                    # If queue is full, remove oldest message and add new one
                    try:
                        self.message_queues[agent_name].get_nowait()
                        await self.message_queues[agent_name].put(message)
                    except asyncio.QueueEmpty:
                        pass

    async def get_messages_for_agent(
        self, agent_name: str, timeout: float = 0.1
    ) -> List[AgentMessage]:
        """Get pending messages for an agent (non-blocking)."""
        if agent_name not in self.message_queues:
            return []

        messages = []
        queue = self.message_queues[agent_name]

        try:
            # Get all available messages without blocking
            while True:
                try:
                    message = queue.get_nowait()
                    messages.append(message)
                except asyncio.QueueEmpty:
                    break
        except Exception:
            pass

        # Sort by priority (higher priority first) and timestamp
        messages.sort(key=lambda m: (-m.priority, m.timestamp))
        return messages

    async def wait_for_message(
        self, agent_name: str, timeout: Optional[float] = None
    ) -> Optional[AgentMessage]:
        """Wait for a message for a specific agent (blocking)."""
        if agent_name not in self.message_queues:
            return None

        try:
            message = await asyncio.wait_for(
                self.message_queues[agent_name].get(), timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None

    async def get_message_history(
        self,
        agent_name: Optional[str] = None,
        task_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """Get message history with optional filters."""
        async with self.lock:
            filtered_messages = self.messages

            if agent_name:
                filtered_messages = [
                    m
                    for m in filtered_messages
                    if m.sender_agent == agent_name or m.recipient_agent == agent_name
                ]

            if task_id:
                filtered_messages = [
                    m for m in filtered_messages if m.task_id == task_id
                ]

            if thread_id:
                filtered_messages = [
                    m for m in filtered_messages if m.thread_id == thread_id
                ]

            if message_type:
                filtered_messages = [
                    m for m in filtered_messages if m.message_type == message_type
                ]

            # Return most recent messages first
            return filtered_messages[-limit:][::-1]

    async def get_active_agents(self) -> List[str]:
        """Get list of currently registered agents."""
        async with self.lock:
            return list(self.agent_subscriptions.keys())

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get status information about the message pool."""
        async with self.lock:
            return {
                "total_messages": len(self.messages),
                "active_agents": list(self.agent_subscriptions.keys()),
                "queue_sizes": {
                    agent: queue.qsize() for agent, queue in self.message_queues.items()
                },
                "message_types_count": {
                    msg_type.value: sum(
                        1 for m in self.messages if m.message_type == msg_type
                    )
                    for msg_type in MessageType
                },
            }

    async def clear_messages(self, older_than_hours: Optional[int] = None):
        """Clear messages from the pool."""
        async with self.lock:
            if older_than_hours is None:
                self.messages.clear()
                self.message_index.clear()
            else:
                cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
                self.messages = [
                    m for m in self.messages if m.timestamp.timestamp() > cutoff_time
                ]
                # Rebuild index
                self.message_index = {m.id: m for m in self.messages}


# Global message pool instance
message_pool = MessagePool()
