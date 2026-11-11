from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class ToolPolicy:
    """Default-deny policy; high-risk tools need both an isolated adapter and approval."""

    HIGH_RISK = frozenset({"bash", "python_execute", "browser_use"})

    def __init__(
        self,
        enabled_tools: set[str] | None = None,
        approved_tools: set[str] | None = None,
        isolated_runtime_tools: set[str] | None = None,
    ):
        self.enabled_tools = {x.strip().lower() for x in (enabled_tools or set())}
        self.approved_tools = {x.strip().lower() for x in (approved_tools or set())}
        self.isolated_runtime_tools = {x.strip().lower() for x in (isolated_runtime_tools or set())}

    def evaluate(self, tool_key: str) -> ToolDecision:
        key = tool_key.strip().lower()
        if key not in self.enabled_tools:
            return ToolDecision(False, False, "tool_not_enabled")
        if key in self.HIGH_RISK:
            if key not in self.isolated_runtime_tools:
                return ToolDecision(False, True, "isolated_runtime_not_ready")
            if key not in self.approved_tools:
                return ToolDecision(False, True, "explicit_approval_required")
            return ToolDecision(True, False, "isolated_runtime_and_explicit_approval_verified")
        if key not in self.approved_tools:
            return ToolDecision(False, True, "approval_required")
        return ToolDecision(True, False, "explicitly_approved")
