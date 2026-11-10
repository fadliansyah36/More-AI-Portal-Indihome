from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class DurablePlanStore(Protocol):
    async def create(self, *, run_id: str, title: str, steps: list[str]) -> dict[str, Any]: ...
    async def get(self, *, run_id: str) -> dict[str, Any]: ...
    async def mark_step(self, *, run_id: str, step_index: int, status: str, notes: str | None = None) -> dict[str, Any]: ...


@dataclass(frozen=True)
class FlowContext:
    run_id: str
    user_id: str
    workspace_id: str | None


class FlowFactory:
    """Preserves upstream flow selection while requiring durable adapters."""

    def __init__(self):
        self._factories: dict[str, Any] = {}

    def register(self, key: str, factory: Any) -> None:
        normalized = key.strip().lower()
        if normalized in self._factories:
            raise ValueError(f"Flow already registered: {normalized}")
        self._factories[normalized] = factory

    def create(self, key: str, **dependencies: Any) -> Any:
        try:
            factory = self._factories[key.strip().lower()]
        except KeyError as exc:
            raise LookupError(f"Flow is not enabled: {key}") from exc
        return factory(**dependencies)

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))
