from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class FlowContext:
    run_id: str
    user_id: str
    workspace_id: str | None
    conversation_id: str | None = None
    attempt: int = 0


class FlowFactory:
    """Allowlisted factory for durable upstream flow adapters.

    Factories construct AgentRuntime-compatible flows; state is supplied by the
    durable run context/checkpoint store, never held in process-global flow state.
    """

    def __init__(self):
        self._factories: dict[str, Callable[..., Any]] = {}

    def register(self, key: str, factory: Callable[..., Any]) -> None:
        normalized = key.strip().lower()
        if not normalized or len(normalized) > 80:
            raise ValueError("flow_key_invalid")
        if normalized in self._factories:
            raise ValueError(f"Flow already registered: {normalized}")
        if not callable(factory):
            raise TypeError("flow_factory_must_be_callable")
        self._factories[normalized] = factory

    def create(self, key: str, **dependencies: Any) -> Any:
        normalized = key.strip().lower()
        try:
            factory = self._factories[normalized]
        except KeyError as exc:
            raise LookupError(f"Flow is not enabled: {normalized}") from exc
        instance = factory(**dependencies)
        if not callable(getattr(instance, "execute", None)):
            raise TypeError("durable_flow_must_implement_execute")
        return instance

    def create_for_run(self, key: str, context: FlowContext, **dependencies: Any) -> Any:
        flow = self.create(key, **dependencies)
        binder = getattr(flow, "bind_run_context", None)
        if callable(binder):
            binder(context)
        return flow

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))
