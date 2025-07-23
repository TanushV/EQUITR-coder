"""Agent communication tools for inter-agent messaging."""

from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..base import Tool, ToolResult
from ...core.message_pool import message_pool, MessageType


class SendMessageArgs(BaseModel):
    content: str = Field(..., description="The message content to send")
    message_type: str = Field(
        default="info",
        description="Type of message: info, request, response, status_update, coordination, error",
    )
    recipient_agent: Optional[str] = Field(
        default=None,
        description="Specific agent to send to (None for broadcast to all agents)",
    )
    task_id: Optional[str] = Field(
        default=None, description="Task ID this message relates to"
    )
    thread_id: Optional[str] = Field(
        default=None, description="Thread ID for message grouping"
    )
    priority: int = Field(
        default=5, description="Message priority (1-10, higher is more urgent)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata for the message"
    )


class ReceiveMessagesArgs(BaseModel):
    timeout: float = Field(
        default=0.1, description="Timeout in seconds to wait for messages"
    )
    message_type_filter: Optional[str] = Field(
        default=None, description="Filter messages by type"
    )


class GetMessageHistoryArgs(BaseModel):
    task_id: Optional[str] = Field(default=None, description="Filter by task ID")
    thread_id: Optional[str] = Field(default=None, description="Filter by thread ID")
    message_type: Optional[str] = Field(
        default=None, description="Filter by message type"
    )
    limit: int = Field(default=50, description="Maximum number of messages to return")


class GetActiveAgentsArgs(BaseModel):
    pass


class SendMessage(Tool):
    """Tool for sending messages to other agents."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__()

    def get_name(self) -> str:
        return "send_agent_message"

    def get_description(self) -> str:
        return "Send a message to other agents in the multi-agent system. For complex coordination, strategic planning, or when messages require deep analysis and synthesis, use a stronger reasoning model to craft comprehensive and insightful communications."

    def get_args_schema(self) -> Type[BaseModel]:
        return SendMessageArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Validate message type
            try:
                msg_type = MessageType(args.message_type)
            except ValueError:
                return ToolResult(
                    success=False,
                    error=f"Invalid message type: {args.message_type}. Valid types: {[t.value for t in MessageType]}",
                )

            # Send message
            message_id = await message_pool.send_message(
                sender_agent=self.agent_name,
                content=args.content,
                message_type=msg_type,
                recipient_agent=args.recipient_agent,
                task_id=args.task_id,
                thread_id=args.thread_id,
                metadata=args.metadata or {},
                priority=args.priority,
            )

            return ToolResult(
                success=True,
                data={
                    "message_id": message_id,
                    "sent_to": args.recipient_agent or "all_agents",
                    "message_type": args.message_type,
                    "content": args.content,
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReceiveMessages(Tool):
    """Tool for receiving messages from other agents."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__()

    def get_name(self) -> str:
        return "receive_agent_messages"

    def get_description(self) -> str:
        return "Receive pending messages from other agents"

    def get_args_schema(self) -> Type[BaseModel]:
        return ReceiveMessagesArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Get messages for this agent
            messages = await message_pool.get_messages_for_agent(
                self.agent_name, timeout=args.timeout
            )

            # Filter by message type if specified
            if args.message_type_filter:
                try:
                    filter_type = MessageType(args.message_type_filter)
                    messages = [m for m in messages if m.message_type == filter_type]
                except ValueError:
                    return ToolResult(
                        success=False,
                        error=f"Invalid message type filter: {args.message_type_filter}",
                    )

            # Convert messages to serializable format
            message_data = []
            for msg in messages:
                message_data.append(
                    {
                        "id": msg.id,
                        "sender_agent": msg.sender_agent,
                        "message_type": msg.message_type.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "task_id": msg.task_id,
                        "thread_id": msg.thread_id,
                        "priority": msg.priority,
                        "metadata": msg.metadata,
                    }
                )

            return ToolResult(
                success=True,
                data={
                    "messages": message_data,
                    "count": len(message_data),
                    "agent": self.agent_name,
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetMessageHistory(Tool):
    """Tool for getting message history with filters."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__()

    def get_name(self) -> str:
        return "get_message_history"

    def get_description(self) -> str:
        return "Get message history with optional filters. For complex analysis of agent communications, strategic insights, or when synthesizing patterns across multiple conversations, use a stronger reasoning model to provide deep understanding and actionable insights."

    def get_args_schema(self) -> Type[BaseModel]:
        return GetMessageHistoryArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Validate message type if provided
            message_type_enum = None
            if args.message_type:
                try:
                    message_type_enum = MessageType(args.message_type)
                except ValueError:
                    return ToolResult(
                        success=False,
                        error=f"Invalid message type: {args.message_type}",
                    )

            # Get message history
            messages = await message_pool.get_message_history(
                agent_name=self.agent_name,
                task_id=args.task_id,
                thread_id=args.thread_id,
                message_type=message_type_enum,
                limit=args.limit,
            )

            # Convert to serializable format
            message_data = []
            for msg in messages:
                message_data.append(
                    {
                        "id": msg.id,
                        "sender_agent": msg.sender_agent,
                        "recipient_agent": msg.recipient_agent,
                        "message_type": msg.message_type.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "task_id": msg.task_id,
                        "thread_id": msg.thread_id,
                        "priority": msg.priority,
                        "metadata": msg.metadata,
                    }
                )

            return ToolResult(
                success=True,
                data={
                    "messages": message_data,
                    "count": len(message_data),
                    "filters": {
                        "agent_name": self.agent_name,
                        "task_id": args.task_id,
                        "thread_id": args.thread_id,
                        "message_type": args.message_type,
                        "limit": args.limit,
                    },
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetActiveAgents(Tool):
    """Tool for getting list of active agents."""

    def get_name(self) -> str:
        return "get_active_agents"

    def get_description(self) -> str:
        return "Get list of currently active agents in the system"

    def get_args_schema(self) -> Type[BaseModel]:
        return GetActiveAgentsArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            active_agents = await message_pool.get_active_agents()
            pool_status = await message_pool.get_pool_status()

            return ToolResult(
                success=True,
                data={
                    "active_agents": active_agents,
                    "agent_count": len(active_agents),
                    "pool_status": pool_status,
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


def create_agent_communication_tools(agent_name: str) -> List[Tool]:
    """Create communication tools for a specific agent."""
    return [
        SendMessage(agent_name),
        ReceiveMessages(agent_name),
        GetMessageHistory(agent_name),
        GetActiveAgents(),
    ]
