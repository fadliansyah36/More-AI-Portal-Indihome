from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from engine.agents.types import AgentMemory, AgentState, Message, ToolCall, ToolFunction


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


def _field(value: Any, name: str, default: Any = None) -> Any:
    """Read provider SDK objects and plain dictionaries through one safe boundary."""
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _normalize_tool_calls(raw_calls: Any) -> list[ToolCall]:
    if raw_calls is None:
        return []
    if not isinstance(raw_calls, (list, tuple)):
        raise ValueError("llm_tool_calls_must_be_a_list")

    normalized: list[ToolCall] = []
    for index, raw in enumerate(raw_calls):
        function = _field(raw, "function")
        name = _field(function, "name")
        arguments = _field(function, "arguments", "{}")
        call_id = _field(raw, "id")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"llm_tool_call_{index}_missing_name")
        if not isinstance(call_id, str) or not call_id.strip():
            raise ValueError(f"llm_tool_call_{index}_missing_id")
        if isinstance(arguments, dict):
            arguments = json.dumps(arguments, separators=(",", ":"), ensure_ascii=False)
        if not isinstance(arguments, str):
            raise ValueError(f"llm_tool_call_{index}_arguments_must_be_json")
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ValueError(f"llm_tool_call_{index}_invalid_json") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"llm_tool_call_{index}_arguments_must_be_object")
        normalized.append(ToolCall(
            id=call_id,
            function=ToolFunction(name=name.strip(), arguments=json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)),
            type=_field(raw, "type", "function"),
        ))
    return normalized


class BaseAgent(ABC):
    """Per-run agent state; never stored in process-global mutable singletons."""

    def __init__(self, *, name: str, llm: LLMClient, memory: AgentMemory | None = None, max_steps: int = 10):
        if max_steps < 1:
            raise ValueError("max_steps_must_be_positive")
        self.name = name
        self.llm = llm
        self.memory = memory or AgentMemory()
        self.max_steps = max_steps
        self.state = AgentState.IDLE
        self.current_step = 0

    async def run(self, request: str, context: AgentContext) -> str:
        if self.state is not AgentState.IDLE:
            raise RuntimeError("Agent instance can only execute one run")
        if not isinstance(request, str) or not request.strip():
            raise ValueError("agent_request_required")
        self.memory.add_message(Message.user_message(request))
        self.state = AgentState.RUNNING
        results: list[str] = []
        try:
            while self.current_step < self.max_steps and self.state is AgentState.RUNNING:
                if context.cancelled.is_set():
                    self.state = AgentState.CANCELLED
                    break
                self.current_step += 1
                result = await self.step(context)
                if result:
                    results.append(result)
            if self.state is AgentState.RUNNING:
                self.state = AgentState.EXHAUSTED
            return "\n".join(results)
        except Exception:
            self.state = AgentState.ERROR
            raise

    @abstractmethod
    async def step(self, context: AgentContext) -> str: ...


class ReActAgent(BaseAgent):
    """ReAct loop base: subclasses implement one reasoning/action/observation cycle."""

    async def step(self, context: AgentContext) -> str:
        raise NotImplementedError("ReActAgent subclasses must implement a reasoning/action cycle")


class ToolCallAgent(ReActAgent):
    def __init__(self, *, name: str, llm: LLMClient, tools: ToolExecutor, system_prompt: str, next_step_prompt: str, max_steps: int = 30):
        super().__init__(name=name, llm=llm, max_steps=max_steps)
        self.tools = tools
        self.system_prompt = system_prompt
        self.next_step_prompt = next_step_prompt

    async def step(self, context: AgentContext) -> str:
        if context.cancelled.is_set():
            self.state = AgentState.CANCELLED
            return ""

        response = await self.llm.ask_tool(
            self.memory.to_dict_list() + [Message.user_message(self.next_step_prompt).to_dict()],
            system_prompt=self.system_prompt,
            tools=self.tools.definitions(),
            tool_choice="auto",
        )
        content = _field(response, "content")
        if content is not None and not isinstance(content, str):
            content = str(content)
        calls = _normalize_tool_calls(_field(response, "tool_calls"))
        self.memory.add_message(Message.assistant_message(content, calls or None))

        if not calls:
            if content and content.strip():
                self.state = AgentState.FINISHED
                return content
            raise RuntimeError("llm_returned_neither_content_nor_tool_calls")

        results: list[str] = []
        for call in calls:
            if context.cancelled.is_set():
                self.state = AgentState.CANCELLED
                break
            arguments = json.loads(call.function.arguments)
            try:
                output = await self.tools.execute(
                    call.function.name,
                    arguments,
                    run_id=context.run_id,
                    user_id=context.user_id,
                )
                if not isinstance(output, str):
                    raise TypeError("tool_output_must_be_text")
            except asyncio.CancelledError:
                self.state = AgentState.CANCELLED
                raise
            except Exception as exc:
                # Keep the failure attached to its tool_call_id so the model can
                # reason about the observation on the next iteration. Never leak
                # exception messages, credentials, or provider internals.
                output = json.dumps({
                    "error": "tool_execution_failed",
                    "error_type": type(exc).__name__,
                    "tool": call.function.name,
                }, separators=(",", ":"))
            self.memory.add_message(Message.tool_message(
                output,
                name=call.function.name,
                tool_call_id=call.id,
            ))
            results.append(output)
        return "\n\n".join(results)


class ManusAgent(ToolCallAgent):
    """OpenManus general-purpose agent identity, with tools injected by policy."""


class SWEAgent(ToolCallAgent):
    """OpenManus software-engineering agent; execution tools must be sandbox adapters."""


class PlanningAgent(ToolCallAgent):
    """OpenManus planning agent; requires a durable plan store via its injected tools."""
