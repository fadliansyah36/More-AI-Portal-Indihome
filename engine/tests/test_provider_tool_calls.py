import pytest

from engine.llm.providers.openai_compatible import _tool_calls


def test_provider_tool_calls_are_parsed_as_structured_arguments():
    calls = _tool_calls({
        "tool_calls": [{
            "id": "call_123",
            "function": {"name": "google_search", "arguments": '{"query":"weather"}'},
        }]
    })
    assert calls == [{
        "id": "call_123",
        "type": "function",
        "function": {"name": "google_search", "arguments": {"query": "weather"}},
        "index": 0,
    }]


def test_provider_tool_call_rejects_malformed_json_arguments():
    with pytest.raises(RuntimeError, match="provider_tool_arguments_invalid"):
        _tool_calls({
            "tool_calls": [{
                "id": "call_123",
                "function": {"name": "google_search", "arguments": "{invalid"},
            }]
        })


def test_provider_tool_call_rejects_non_object_arguments():
    with pytest.raises(RuntimeError, match="provider_tool_arguments_must_be_object"):
        _tool_calls({
            "tool_calls": [{
                "id": "call_123",
                "function": {"name": "google_search", "arguments": '["not", "an", "object"]'},
            }]
        })
