from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from engine.tools.catalog import OPENMANUS_TOOL_CATALOG
from engine.tools.policy import ToolPolicy


ToolHandler = Callable[..., Awaitable[str]]


class PolicyEnforcedToolRegistry:
    """The registry knows every upstream tool but executes only explicitly enabled safe adapters."""

    def __init__(self, policy: ToolPolicy):
        self.policy = policy
        self.handlers: dict[str, ToolHandler] = {}

    def register(self, key: str, handler: ToolHandler) -> None:
        known = {tool.key for tool in OPENMANUS_TOOL_CATALOG}
        if key not in known:
            raise ValueError(f"Unknown upstream tool: {key}")
        if key in self.handlers:
            raise ValueError(f"Tool already registered: {key}")
        self.handlers[key] = handler

    def definitions(self) -> list[dict[str, Any]]:
        definitions = []
        for tool in OPENMANUS_TOOL_CATALOG:
            decision = self.policy.evaluate(tool.key)
            if decision.allowed and tool.key in self.handlers:
                definitions.append({
                    "type": "function",
                    "function": {
                        "name": tool.key,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                })
        return definitions

    async def execute(self, name: str, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        decision = self.policy.evaluate(name)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        handler = self.handlers.get(name)
        if handler is None:
            raise LookupError(f"No production adapter registered for {name}")
        return await handler(arguments, run_id=run_id, user_id=user_id)
