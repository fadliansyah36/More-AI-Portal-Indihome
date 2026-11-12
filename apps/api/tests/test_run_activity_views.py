from app.routers.agent_runs import _safe_run_activity, _thinking_message


def test_durable_activity_view_redacts_private_payload_fields():
    row = {
        "id": "event-1",
        "sequence": 7,
        "event_type": "tool.started",
        "created_at": "2026-11-12T10:00:00Z",
        "payload": {
            "tool": "workspace_read_file",
            "round": 2,
            "index": 0,
            "arguments": {"path": "private.txt"},
            "prompt": "private prompt",
            "observation": "private file contents",
            "api_key": "secret",
        },
    }
    activity = _safe_run_activity(row)
    assert activity["tool"] == "workspace_read_file"
    assert activity["round"] == 2
    assert activity["index"] == 0
    assert "arguments" not in activity
    assert "prompt" not in activity
    assert "observation" not in activity
    assert "api_key" not in activity


def test_thinking_view_maps_durable_tool_and_terminal_events():
    tool = _thinking_message({
        "event_type": "tool.completed",
        "timestamp": "2026-11-12T10:00:00Z",
        "sequence": 8,
        "tool": "google_search",
        "status": "succeeded",
    })
    assert tool["message"] == "Tool completed: google_search"
    assert tool["type"] == "thinking"
    assert tool["status"] == "succeeded"

    terminal = _thinking_message({
        "event_type": "run.completed",
        "timestamp": "2026-11-12T10:01:00Z",
        "sequence": 9,
    })
    assert terminal["message"] == "Agent run completed"
    assert terminal["type"] == "conclusion"


def test_thinking_view_marks_failures_as_errors():
    activity = _thinking_message({
        "event_type": "run.timed_out",
        "timestamp": "2026-11-12T10:02:00Z",
        "sequence": 10,
    })
    assert activity["type"] == "error"
    assert activity["message"] == "Agent run timed out"


def test_planning_checkpoint_becomes_owner_visible_thinking_step():
    activity = _thinking_message({
        "event_type": "worker.checkpoint",
        "timestamp": "2026-11-12T08:00:00Z",
        "sequence": 11,
        "checkpoint_key": "planning.step.2.completed",
    })
    assert activity["message"] == "Planning step 2 completed"
    assert activity["type"] == "thinking"

def test_customer_run_lifecycle_routes_are_registered():
    from app.main import app

    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    assert ("/api/v1/customer/agent-runs", "GET") in routes
    assert ("/api/v1/customer/agent-runs/{run_id}", "GET") in routes
    assert ("/api/v1/customer/agent-runs/{run_id}/steps", "GET") in routes
    assert ("/api/v1/customer/agent-runs/{run_id}/cancel", "POST") in routes
    assert ("/api/v1/customer/agent-runs/{run_id}/stream", "GET") in routes
