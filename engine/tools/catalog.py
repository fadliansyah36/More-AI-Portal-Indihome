from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDefinition:
    key: str
    source_path: str
    risk: str
    execution_boundary: str
    approval_required: bool
    enabled_by_default: bool = False


# Complete upstream tool inventory. A catalog entry is not an executable permission.
OPENMANUS_TOOL_CATALOG = (
    ToolDefinition("bash", "app/tool/bash.py", "critical", "apps/sandbox/bash", True),
    ToolDefinition("browser_use", "app/tool/browser_use_tool.py", "high", "apps/sandbox/browser", True),
    ToolDefinition("create_chat_completion", "app/tool/create_chat_completion.py", "medium", "engine/llm/gateway", False),
    ToolDefinition("file_saver", "app/tool/file_saver.py", "medium", "engine/tools/workspace_files", True),
    ToolDefinition("google_search", "app/tool/google_search.py", "medium", "engine/tools/search_provider", True),
    ToolDefinition("planning", "app/tool/planning.py", "low", "engine/orchestration/durable_plan_store", False),
    ToolDefinition("python_execute", "app/tool/python_execute.py", "critical", "apps/sandbox/python", True),
    ToolDefinition("run", "app/tool/run.py", "high", "apps/sandbox/process", True),
    ToolDefinition("str_replace_editor", "app/tool/str_replace_editor.py", "high", "apps/sandbox/workspace", True),
    ToolDefinition("terminate", "app/tool/terminate.py", "low", "engine/agents/cancellation", False),
)


def tool_catalog() -> list[dict[str, object]]:
    return [
        {
            "key": item.key,
            "source_path": item.source_path,
            "risk": item.risk,
            "execution_boundary": item.execution_boundary,
            "approval_required": item.approval_required,
            "enabled_by_default": item.enabled_by_default,
        }
        for item in OPENMANUS_TOOL_CATALOG
    ]
