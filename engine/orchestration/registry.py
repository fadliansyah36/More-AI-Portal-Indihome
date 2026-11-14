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

    def capability_snapshot(self) -> dict[str, object]:
        """Describe capabilities from registered runtime adapters, not static catalog claims."""
        runtimes: dict[str, dict[str, object]] = {}
        for key, runtime in sorted(self._agents.items()):
            tool_runtime = runtime
            if key == "planning":
                tool_runtime = getattr(runtime, "step_executor", runtime)
            registry = getattr(tool_runtime, "tools", None)
            definitions = registry.definitions() if registry is not None else []
            tool_keys: list[str] = []
            for definition in definitions:
                if not isinstance(definition, dict):
                    continue
                function = definition.get("function")
                name = function.get("name") if isinstance(function, dict) else None
                if isinstance(name, str) and name:
                    tool_keys.append(name)
            runtimes[key] = {"tool_keys": sorted(set(tool_keys))}
        all_tool_keys = {
            key for descriptor in runtimes.values()
            for key in descriptor.get("tool_keys", [])
            if isinstance(key, str)
        }
        return {
            "runtimes": runtimes,
            "media": {
                "image_generation": "image_generate" in all_tool_keys,
                "video_generation": "video_generate" in all_tool_keys,
                "file_generation": "file_saver" in all_tool_keys,
            },
            "source": "registered_worker_adapters",
        }
