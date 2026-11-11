import asyncio
import json

import pytest

from engine.agents.runtime import AgentContext, ManusAgent, ToolCallAgent
from engine.agents.types import AgentState


class FakeLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    async def ask(self, messages, *, system_prompt=None):
        raise AssertionError("ask() should not be used by the tool-call runtime")

    async def ask_tool(self, messages, *, system_prompt, tools, tool_choice="auto"):
        self.calls.append({"messages": messages, "tools": tools, "tool_choice": tool_choice})
        return next(self.responses)


class FakeTools:
    def __init__(self, output="ok", error=None):
        self.output = output
        self.error = error
        self.executions = []

    def definitions(self):
        return [{"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}]

    async def execute(self, name, arguments, *, run_id, user_id):
        self.executions.append((name, arguments, run_id, user_id))
        if self.error:
            raise self.error
        return self.output


@pytest.mark.asyncio
async def test_tool_call_runtime_executes_tool_then_returns_final_answer():
    llm = FakeLLM([
        {"content": None, "tool_calls": [{"id": "call-1", "type": "function", "function": {"name": "lookup", "arguments": "{\"q\":\"hello\"}"}}]},
        {"content": "Found it", "tool_calls": []},
    ])
    tools = FakeTools("observation")
    agent = ManusAgent(name="manus", llm=llm, tools=tools, system_prompt="system", next_step_prompt="continue")
    result = await agent.run("find something", AgentContext(run_id="r1", user_id="u1"))

    assert result == "observation\nFound it"
    assert agent.state is AgentState.FINISHED
    assert tools.executions == [("lookup", {"q": "hello"}, "r1", "u1")]
    assert agent.memory.messages[-2].role == "tool"
    assert agent.memory.messages[-2].tool_call_id == "call-1"


@pytest.mark.asyncio
async def test_tool_call_runtime_accepts_provider_object_shapes():
    class Function:
        name = "lookup"
        arguments = {"term": "structured"}

    class Call:
        id = "call-object"
        function = Function()

    class Response:
        content = None
        tool_calls = [Call()]

    llm = FakeLLM([Response(), {"content": "done", "tool_calls": []}])
    tools = FakeTools("observed")
    agent = ToolCallAgent(name="test", llm=llm, tools=tools, system_prompt="", next_step_prompt="next")
    await agent.run("request", AgentContext(run_id="r2", user_id="u2"))
    assert tools.executions[0][1] == {"term": "structured"}


@pytest.mark.asyncio
async def test_tool_failure_becomes_redacted_tool_observation():
    llm = FakeLLM([
        {"tool_calls": [{"id": "call-err", "function": {"name": "lookup", "arguments": "{}"}}]},
        {"content": "recovered", "tool_calls": []},
    ])
    tools = FakeTools(error=RuntimeError("secret token must not leak"))
    agent = ToolCallAgent(name="test", llm=llm, tools=tools, system_prompt="", next_step_prompt="next")
    await agent.run("request", AgentContext(run_id="r3", user_id="u3"))
    observation = agent.memory.messages[-2].content
    assert "secret token" not in observation
    assert json.loads(observation) == {
        "error": "tool_execution_failed",
        "error_type": "RuntimeError",
        "tool": "lookup",
    }


@pytest.mark.asyncio
async def test_invalid_tool_arguments_fail_closed():
    llm = FakeLLM([{"tool_calls": [{"id": "call-bad", "function": {"name": "lookup", "arguments": "[]"}}]}])
    tools = FakeTools()
    agent = ToolCallAgent(name="test", llm=llm, tools=tools, system_prompt="", next_step_prompt="next")
    with pytest.raises(ValueError, match="arguments_must_be_object"):
        await agent.run("request", AgentContext(run_id="r4", user_id="u4"))
    assert tools.executions == []
    assert agent.state is AgentState.ERROR


@pytest.mark.asyncio
async def test_agent_cancellation_and_max_step_exhaustion_are_terminal():
    llm = FakeLLM([{"tool_calls": [{"id": "call-1", "function": {"name": "lookup", "arguments": "{}"}}]}] * 3)
    tools = FakeTools()
    cancelled = asyncio.Event()
    cancelled.set()
    agent = ToolCallAgent(name="test", llm=llm, tools=tools, system_prompt="", next_step_prompt="next")
    await agent.run("request", AgentContext(run_id="r5", user_id="u5", cancelled=cancelled))
    assert agent.state is AgentState.CANCELLED
    assert not llm.calls

    exhausted = ToolCallAgent(name="test", llm=llm, tools=tools, system_prompt="", next_step_prompt="next", max_steps=1)
    await exhausted.run("request", AgentContext(run_id="r6", user_id="u6"))
    assert exhausted.state is AgentState.EXHAUSTED
