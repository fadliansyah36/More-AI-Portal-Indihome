from __future__ import annotations

import re


class RunPausedForApproval(Exception):
    """Durable pause committed and worker lease released pending an owner decision."""


class AgentExecutionError(Exception):
    """Sanitized, stable error contract shared by agent adapters and worker lifecycle."""

    def __init__(self, code: str, *, retryable: bool = False):
        if not isinstance(code, str) or not re.fullmatch(r"[a-z][a-z0-9_]{1,79}", code):
            raise ValueError("agent_error_code_invalid")
        self.code = code
        self.retryable = bool(retryable)
        super().__init__(code)


def classify_agent_exception(exc: Exception) -> AgentExecutionError:
    """Map implementation/provider exceptions to a safe, non-sensitive taxonomy."""
    if isinstance(exc, AgentExecutionError):
        return exc
    if isinstance(exc, PermissionError):
        return AgentExecutionError("agent_action_not_permitted")
    if isinstance(exc, LookupError):
        return AgentExecutionError("agent_capability_unavailable")
    if isinstance(exc, (ValueError, TypeError)):
        return AgentExecutionError("agent_request_invalid")
    if isinstance(exc, TimeoutError):
        return AgentExecutionError("agent_execution_timeout", retryable=True)
    # Do not classify arbitrary programming errors as transient: blind retries can
    # repeat side effects and hide deterministic implementation faults.
    return AgentExecutionError("agent_internal_error")
