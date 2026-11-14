from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


class AgentState(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"
    EXHAUSTED = "EXHAUSTED"
    ERROR = "ERROR"


@dataclass
class ToolFunction:
    name: str
    arguments: str


@dataclass
class ToolCall:
    id: str
    function: ToolFunction
    type: str = "function"


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    name: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls is not None:
            result["tool_calls"] = [
                {"id": call.id, "type": call.type, "function": {"name": call.function.name, "arguments": call.function.arguments}}
                for call in self.tool_calls
            ]
        if self.name is not None:
            result["name"] = self.name
        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id
        return result

    @classmethod
    def user_message(cls, content: str) -> "Message":
        return cls("user", content)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        return cls("system", content)

    @classmethod
    def assistant_message(
        cls, content: str | None = None, tool_calls: list[ToolCall] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "Message":
        return cls("assistant", content, tool_calls, metadata=metadata or {})

    @classmethod
    def tool_message(cls, content: str, *, name: str, tool_call_id: str) -> "Message":
        return cls("tool", content, name=name, tool_call_id=tool_call_id)


@dataclass
class AgentMemory:
    messages: list[Message] = field(default_factory=list)
    max_messages: int = 100

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def add_messages(self, messages: list[Message]) -> None:
        for message in messages:
            self.add_message(message)

    def clear(self) -> None:
        self.messages.clear()

    def to_dict_list(self) -> list[dict[str, Any]]:
        return [message.to_dict() for message in self.messages]
