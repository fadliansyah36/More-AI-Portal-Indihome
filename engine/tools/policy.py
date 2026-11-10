from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class ToolPolicy:
    """Default-deny tool policy. High-risk upstream tools remain blocked."""

    HIGH_RISK = frozenset({"bash", "python_execute", "browser_use"})
    DEFAULT_DENY = HIGH_RISK

    def __init__(self, enabled_tools: set[str] | None = None, approved_tools: set[str] | None = None):
        self.enabled_tools = {x.strip().lower() for x in (enabled_tools or set())}
        self.approved_tools = {x.strip().lower() for x in (approved_tools or set())}

    def evaluate(self, tool_key: str) -> ToolDecision:
        key = tool_key.strip().lower()
        if key in self.DEFAULT_DENY:
            return ToolDecision(False, True, "isolated_runtime_and_explicit_approval_required")
        if key not in self.enabled_tools:
            return ToolDecision(False, False, "tool_not_enabled")
        if key in self.approved_tools:
            return ToolDecision(True, False, "explicitly_approved")
        return ToolDecision(False, True, "approval_required")
