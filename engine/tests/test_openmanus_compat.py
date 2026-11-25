import pytest

from engine.tools.catalog import OPENMANUS_TOOL_CATALOG, tool_catalog
from engine.tools.policy import ToolPolicy
from engine.tools.registry import PolicyEnforcedToolRegistry
from engine.prompts.manus import SYSTEM_PROMPT


def test_upstream_and_moreai_tool_inventory_is_complete_and_permission_scoped():
    keys = {tool.key for tool in OPENMANUS_TOOL_CATALOG}
    assert keys == {
        "answer_assess", "bash", "browser_use", "calendar_create_event",
        "calendar_delete_event", "calendar_list_events", "calendar_update_event",
        "copy_engine_generate", "create_chat_completion", "file_saver",
        "gmail_search", "gmail_send", "google_search", "image_generate",
        "knowledge_ingest", "knowledge_search", "learning_path_create",
        "learning_progress_update", "lesson_generate", "planning",
        "python_execute", "quiz_generate", "run", "str_replace_editor",
        "terminate", "video_generate", "workspace_read_file",
        "workspace_restore_version",
    }
    catalog = tool_catalog()
    assert {item["key"] for item in catalog} == keys
    assert all(isinstance(item["enabled_by_default"], bool) for item in catalog)
    assert all(isinstance(item["permission_scope"], str) and item["permission_scope"] for item in catalog)
    assert all(isinstance(item["risk"], str) and item["risk"] for item in catalog)


def test_policy_registry_never_exposes_unapproved_tools():
    registry = PolicyEnforcedToolRegistry(ToolPolicy())
    assert registry.definitions() == []
    with pytest.raises(PermissionError):
        import asyncio
        asyncio.run(registry.execute("bash", {}, run_id="r", user_id="u"))


def test_moreai_prompts_do_not_request_private_reasoning():
    assert "Never reveal private reasoning" in SYSTEM_PROMPT
