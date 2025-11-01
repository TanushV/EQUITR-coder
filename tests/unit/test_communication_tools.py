import pytest

from equitrcoder.core.global_message_pool import global_message_pool
from equitrcoder.tools.builtin.communication import (
    SendMessage,
    ReceiveMessages,
)


@pytest.mark.asyncio
async def test_communication_broadcast():
    sender = "agent_a"
    receiver = "agent_b"

    await global_message_pool.register_agent(sender)
    await global_message_pool.register_agent(receiver)

    send_tool = SendMessage(sender_id=sender)
    recv_tool = ReceiveMessages(agent_id=receiver)

    # Send a broadcast message (recipient None)
    res_send = await send_tool.run(content="hello team", recipient=None)
    assert res_send.success is True

    res_recv = await recv_tool.run()
    assert res_recv.success is True
    data = res_recv.data
    assert isinstance(data, list)
    assert data and data[0]["from"] == sender
    assert data[0]["content"] == "hello team"


@pytest.mark.asyncio
async def test_communication_direct_message():
    sender = "agent_c"
    receiver = "agent_d"

    await global_message_pool.register_agent(sender)
    await global_message_pool.register_agent(receiver)

    send_tool = SendMessage(sender_id=sender)
    recv_tool = ReceiveMessages(agent_id=receiver)

    # Send a direct message
    res_send = await send_tool.run(content="psst", recipient=receiver)
    assert res_send.success is True

    res_recv = await recv_tool.run()
    assert res_recv.success is True
    data = res_recv.data
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["from"] == sender
    assert data[0]["content"] == "psst"
