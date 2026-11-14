from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class ToolPolicy:
    """Default-deny policy; high-risk tools require both enablement and explicit approval."""

    HIGH_RISK = frozenset({
        "bash",
        "python_execute",
        "browser_use",
        "workspace_restore_version",
        "str_replace_editor",
        "gmail_send",
        "calendar_create_event",
    })
    DEFAULT_DENY = HIGH_RISK

    def __init__(self, enabled_tools: set[str] | None = None, approved_tools: set[str] | None = None):
        self.enabled_tools = {x.strip().lower() for x in (enabled_tools or set())}
        self.approved_tools = {x.strip().lower() for x in (approved_tools or set())}

    def evaluate(self, tool_key: str) -> ToolDecision:
        key = tool_key.strip().lower()
        if key not in self.enabled_tools:
            return ToolDecision(False, key in self.HIGH_RISK, "tool_not_enabled")
        if key in self.HIGH_RISK and key not in self.approved_tools:
            # The handler must pause for a run-scoped approval and atomically consume it
            # before execution. Listing the tool here only advertises that gated flow.
            return ToolDecision(True, True, "explicit_approval_required")
        if key in self.approved_tools:
            return ToolDecision(True, False, "explicitly_approved")
        return ToolDecision(True, False, "enabled_by_policy")
