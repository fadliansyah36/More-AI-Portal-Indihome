import pytest

from engine.tools.catalog import OPENMANUS_TOOL_CATALOG, tool_catalog
from engine.tools.policy import ToolPolicy
from engine.tools.registry import PolicyEnforcedToolRegistry
from engine.prompts.manus import SYSTEM_PROMPT


def test_upstream_and_moreai_tool_inventory_is_complete_and_default_disabled():
    keys = {tool.key for tool in OPENMANUS_TOOL_CATALOG}
    assert keys == {
        "bash", "browser_use", "create_chat_completion", "file_saver",
        "google_search", "knowledge_ingest", "knowledge_search", "planning",
        "python_execute", "run", "str_replace_editor", "terminate",
        "workspace_read_file", "workspace_restore_version",
    }
    assert all(item["enabled_by_default"] is False for item in tool_catalog())


def test_policy_registry_never_exposes_unapproved_tools():
    registry = PolicyEnforcedToolRegistry(ToolPolicy())
    assert registry.definitions() == []
    with pytest.raises(PermissionError):
        import asyncio
        asyncio.run(registry.execute("bash", {}, run_id="r", user_id="u"))


def test_moreai_prompts_do_not_request_private_reasoning():
    assert "Never reveal private reasoning" in SYSTEM_PROMPT
