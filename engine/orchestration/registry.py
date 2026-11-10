from __future__ import annotations

from engine.agents.protocol import AgentRuntime


class AgentRegistry:
    """Explicit allowlisted registry; unknown agent keys fail closed."""

    def __init__(self):
        self._agents: dict[str, AgentRuntime] = {}

    def register(self, key: str, runtime: AgentRuntime) -> None:
        normalized = key.strip().lower()
        if not normalized or len(normalized) > 80:
            raise ValueError("Agent key must contain 1 to 80 characters")
        if normalized in self._agents:
            raise ValueError(f"Agent already registered: {normalized}")
        self._agents[normalized] = runtime

    def resolve(self, key: str) -> AgentRuntime:
        normalized = key.strip().lower()
        try:
            return self._agents[normalized]
        except KeyError as exc:
            raise LookupError(f"Agent is not enabled: {normalized}") from exc

    def enabled_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._agents))
