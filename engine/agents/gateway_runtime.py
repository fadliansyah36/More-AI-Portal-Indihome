from __future__ import annotations

from typing import Any, Protocol

from engine.agents.protocol import AgentRunContext, AgentRunResult, CheckpointWriter


class ChatGateway(Protocol):
    async def stream(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "chat", workspace_id: str | None = None, partner_id: str | None = None): ...


class GatewayManusRuntime:
    """Safe text-only Manus runtime with durable token checkpoints; tools are injected separately."""

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
        parts: list[str] = []
        chunk_index = 0
        provider_key = None
        model_key = None
        async for item in self.gateway.stream(
            user_id=context.user_id,
            run_id=context.run_id,
            request_key=f"{context.run_id}:manus",
            messages=messages,
            task_type="chat",
            workspace_id=context.workspace_id,
        ):
            if cancelled.is_set():
                raise RuntimeError("run_cancelled")
            if item.get("type") == "delta":
                text = item.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
                    chunk_index += 1
                    await checkpoint(f"stream.chunk.{chunk_index:06d}", {"text": text})
            elif item.get("type") == "done":
                provider_key = item.get("provider_key")
                model_key = item.get("model_key")
        answer = "".join(parts)
        if not answer:
            raise RuntimeError("llm_empty_response")
        await checkpoint("manus.response", {"provider_key": provider_key, "model_key": model_key})
        return AgentRunResult({"text": answer, "provider_key": provider_key, "model_key": model_key})
