from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from engine.tools.catalog import OPENMANUS_TOOL_CATALOG, ToolDefinition
from engine.tools.policy import ToolPolicy


ToolHandler = Callable[..., Awaitable[str]]
ApprovalGate = Callable[[str, str, str, dict[str, Any]], Awaitable[bool]]


def _validate_arguments(schema: dict[str, Any], value: Any, *, path: str = "arguments") -> None:
    """Validate the JSON-Schema subset used by the canonical OpenManus tool catalog."""
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{path}_must_be_object")
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ValueError(f"{path}_missing_{key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                raise ValueError(f"{path}_unknown_fields")
        for key, item in value.items():
            if key in properties:
                _validate_arguments(properties[key], item, path=f"{path}.{key}")
        return

    if expected == "string":
        if not isinstance(value, str):
            raise ValueError(f"{path}_must_be_string")
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValueError(f"{path}_too_short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValueError(f"{path}_too_long")
    elif expected == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path}_must_be_array")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValueError(f"{path}_too_many_items")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate_arguments(item_schema, item, path=f"{path}[{index}]")
    elif expected == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{path}_must_be_integer")
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{path}_below_minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"{path}_above_maximum")
    elif expected == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{path}_must_be_number")
    elif expected == "boolean" and not isinstance(value, bool):
        raise ValueError(f"{path}_must_be_boolean")

    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}_not_allowed")


class PolicyEnforcedToolRegistry:
    """Default-deny dispatcher with catalog validation and per-tool execution deadlines."""

    def __init__(self, policy: ToolPolicy, approval_gate: ApprovalGate | None = None):
        self.policy = policy
        self.approval_gate = approval_gate
        self.handlers: dict[str, ToolHandler] = {}
        self.catalog: dict[str, ToolDefinition] = {tool.key: tool for tool in OPENMANUS_TOOL_CATALOG}

    def register(self, key: str, handler: ToolHandler) -> None:
        normalized = key.strip().lower()
        if normalized not in self.catalog:
            raise ValueError(f"Unknown upstream tool: {key}")
        if normalized in self.handlers:
            raise ValueError(f"Tool already registered: {normalized}")
        if not callable(handler):
            raise TypeError("Tool handler must be callable")
        self.handlers[normalized] = handler

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

    async def execute(self, name: str, arguments: dict[str, Any], *, run_id: str, user_id: str, workspace_id: str | None = None) -> str:
        normalized = name.strip().lower() if isinstance(name, str) else ""
        tool = self.catalog.get(normalized)
        if tool is None:
            raise LookupError("unknown_tool")
        decision = self.policy.evaluate(normalized)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        handler = self.handlers.get(normalized)
        if handler is None:
            raise LookupError(f"No production adapter registered for {normalized}")
        _validate_arguments(tool.input_schema, arguments)
        if decision.requires_approval:
            if self.approval_gate is None:
                raise PermissionError("tool_approval_gate_not_configured")
            if not await self.approval_gate(run_id, user_id, normalized, arguments):
                raise PermissionError("tool_approval_denied_expired_or_already_consumed")
        try:
            output = await asyncio.wait_for(
                handler(arguments, run_id=run_id, user_id=user_id, **({"workspace_id": workspace_id} if normalized in {"str_replace_editor", "workspace_restore_version", "workspace_read_file", "knowledge_ingest", "knowledge_search", "run"} else {})),
                timeout=tool.timeout_seconds,
            )
        except TimeoutError as exc:
            raise TimeoutError(f"tool_execution_timeout:{normalized}") from exc
        if not isinstance(output, str):
            raise TypeError("tool_handler_must_return_text")
        return output
