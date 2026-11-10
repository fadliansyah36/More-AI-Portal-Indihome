from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from engine.agents.types import AgentMemory, AgentState, Message


class LLMClient(Protocol):
    async def ask(self, messages: list[dict[str, Any]], *, system_prompt: str | None = None) -> str: ...
    async def ask_tool(self, messages: list[dict[str, Any]], *, system_prompt: str | None, tools: list[dict[str, Any]], tool_choice: str = "auto") -> Any: ...


class ToolExecutor(Protocol):
    def definitions(self) -> list[dict[str, Any]]: ...
    async def execute(self, name: str, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str: ...


@dataclass
class AgentContext:
    run_id: str
    user_id: str
    workspace_id: str | None = None
    conversation_id: str | None = None
    cancelled: asyncio.Event = field(default_factory=asyncio.Event)


class BaseAgent(ABC):
    """Per-run agent state; never stored in process-global mutable singletons."""

    def __init__(self, *, name: str, llm: LLMClient, memory: AgentMemory | None = None, max_steps: int = 10):
        self.name = name
        self.llm = llm
        self.memory = memory or AgentMemory()
        self.max_steps = max_steps
        self.state = AgentState.IDLE
        self.current_step = 0

    async def run(self, request: str, context: AgentContext) -> str:
        if self.state is not AgentState.IDLE:
            raise RuntimeError("Agent instance can only execute one run")
        self.memory.add_message(Message.user_message(request))
        self.state = AgentState.RUNNING
        results: list[str] = []
        try:
            while self.current_step < self.max_steps and self.state is AgentState.RUNNING:
                if context.cancelled.is_set():
                    self.state = AgentState.FINISHED
                    break
                self.current_step += 1
                results.append(await self.step(context))
            return "\n".join(results)
        except Exception:
            self.state = AgentState.ERROR
            raise

    @abstractmethod
    async def step(self, context: AgentContext) -> str: ...


class ReActAgent(BaseAgent):
    async def step(self, context: AgentContext) -> str:
        raise NotImplementedError("Concrete ReAct agent must implement think/act")


class ToolCallAgent(ReActAgent):
    def __init__(self, *, name: str, llm: LLMClient, tools: ToolExecutor, system_prompt: str, next_step_prompt: str, max_steps: int = 30):
        super().__init__(name=name, llm=llm, max_steps=max_steps)
        self.tools = tools
        self.system_prompt = system_prompt
        self.next_step_prompt = next_step_prompt

    async def step(self, context: AgentContext) -> str:
        response = await self.llm.ask_tool(
            self.memory.to_dict_list() + [Message.user_message(self.next_step_prompt).to_dict()],
            system_prompt=self.system_prompt,
            tools=self.tools.definitions(),
            tool_choice="auto",
        )
        content = getattr(response, "content", None)
        calls = getattr(response, "tool_calls", None) or []
        self.memory.add_message(Message.assistant_message(content, calls))
        if not calls:
            if content:
                self.state = AgentState.FINISHED
                return content
            return "No tool call or response was produced"
        results: list[str] = []
        for call in calls:
            if context.cancelled.is_set():
                break
            name = call.function.name
            import json
            args = json.loads(call.function.arguments or "{}")
            output = await self.tools.execute(name, args, run_id=context.run_id, user_id=context.user_id)
            self.memory.add_message(Message.tool_message(output, name=name, tool_call_id=call.id))
            results.append(output)
        return "\n\n".join(results)


class ManusAgent(ToolCallAgent):
    """OpenManus general-purpose agent identity, with tools injected by policy."""


class SWEAgent(ToolCallAgent):
    """OpenManus software-engineering agent; execution tools must be sandbox adapters."""


class PlanningAgent(ToolCallAgent):
    """OpenManus planning agent; requires a durable plan store via its injected tools."""
