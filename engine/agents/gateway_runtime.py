from __future__ import annotations

from typing import Any, Protocol

from engine.agents.memory import ConversationMemoryStore
from engine.agents.protocol import AgentRunContext, AgentRunResult, CheckpointWriter
from engine.agents.types import Message


class ChatGateway(Protocol):
    async def stream(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "chat", workspace_id: str | None = None, partner_id: str | None = None): ...


class GatewayManusRuntime:
    """Metered Manus text runtime with optional durable, owner-scoped conversation memory."""

    def __init__(self, gateway: ChatGateway, memory_store: ConversationMemoryStore | None = None):
        self.gateway = gateway
        self.memory_store = memory_store

    async def execute(self, context: AgentRunContext, payload: dict[str, Any], checkpoint: CheckpointWriter, cancelled: Any) -> AgentRunResult:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("agent_prompt_required")
        if cancelled.is_set():
            raise RuntimeError("run_cancelled")

        system_message = Message.system_message(
            "You are MoreAI Manus, a helpful assistant. Provide grounded answers. "
            "Never claim a tool action occurred unless an authorized tool confirms it. "
            "Do not reveal private reasoning or secrets."
        )
        user_message = Message.user_message(prompt[:100_000])
        history: list[Message] = []
        if self.memory_store is not None and context.conversation_id:
            history = await self.memory_store.load(
                conversation_id=context.conversation_id,
                user_id=context.user_id,
                workspace_id=context.workspace_id,
                limit=100,
            )
            await self.memory_store.append(
                conversation_id=context.conversation_id,
                user_id=context.user_id,
                workspace_id=context.workspace_id,
                run_id=context.run_id,
                message=user_message,
                message_key=f"{context.run_id}:user",
            )

        messages = [system_message.to_dict()]
        messages.extend(
            message.to_dict()
            for message in history
            if message.role != "system"
        )
        messages.append(user_message.to_dict())

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

        if self.memory_store is not None and context.conversation_id:
            await self.memory_store.append(
                conversation_id=context.conversation_id,
                user_id=context.user_id,
                workspace_id=context.workspace_id,
                run_id=context.run_id,
                message=Message.assistant_message(answer),
                message_key=f"{context.run_id}:assistant",
            )
        await checkpoint("manus.response", {"provider_key": provider_key, "model_key": model_key})
        return AgentRunResult({"text": answer, "provider_key": provider_key, "model_key": model_key})
