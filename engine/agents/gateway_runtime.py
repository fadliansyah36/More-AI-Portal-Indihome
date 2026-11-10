from __future__ import annotations

from typing import Any, Protocol

from engine.agents.protocol import AgentRunContext, AgentRunResult, CheckpointWriter


class ChatGateway(Protocol):
    async def complete(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "chat") -> dict[str, Any]: ...


class GatewayManusRuntime:
    """Safe text-only Manus runtime. Tool execution is deliberately delegated to separately approved adapters."""

    def __init__(self, gateway: ChatGateway):
        self.gateway = gateway

    async def execute(self, context: AgentRunContext, payload: dict[str, Any], checkpoint: CheckpointWriter, cancelled: Any) -> AgentRunResult:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("agent_prompt_required")
        if cancelled.is_set():
            raise RuntimeError("run_cancelled")
        messages = [
            {"role": "system", "content": "You are MoreAI Manus, a helpful assistant. Provide grounded answers. Never claim a tool action occurred unless an authorized tool confirms it. Do not reveal private reasoning or secrets."},
            {"role": "user", "content": prompt[:100_000]},
        ]
        response = await self.gateway.complete(
            user_id=context.user_id,
            run_id=context.run_id,
            request_key=f"{context.run_id}:manus",
            messages=messages,
            task_type="chat",
        )
        if cancelled.is_set():
            raise RuntimeError("run_cancelled")
        text = response.get("text")
        if not isinstance(text, str) or not text:
            raise RuntimeError("llm_empty_response")
        await checkpoint("manus.response", {"provider_key": response.get("provider_key"), "model_key": response.get("model_key")})
        return AgentRunResult({"text": text, "provider_key": response.get("provider_key"), "model_key": response.get("model_key")})
