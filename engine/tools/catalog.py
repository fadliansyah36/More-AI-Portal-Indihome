from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolDefinition:
    key: str
    version: str
    description: str
    input_schema: dict[str, Any]
    capability_tags: tuple[str, ...]
    permission_scope: str
    risk: str
    approval_mode: str
    execution_environment: str
    timeout_seconds: int
    resource_limits: dict[str, Any]
    idempotency: str
    audit_category: str
    available_by_default: tuple[str, ...] = ()
    enabled_by_default: bool = False


# Full upstream inventory. Catalog presence never grants execution permission.
OPENMANUS_TOOL_CATALOG = (
    ToolDefinition("bash", "1.0.0", "Execute shell commands inside an isolated sandbox.", {"type": "object", "properties": {"command": {"type": "string", "maxLength": 20000}}, "required": ["command"], "additionalProperties": False}, ("process", "filesystem"), "workspace:execute", "critical", "explicit_approval", "apps/sandbox/bash", 30, {"cpu": "1", "memory_mb": 512, "pids": 32, "network": "disabled", "filesystem": "ephemeral"}, "non_idempotent", "tool.shell.execute"),
    ToolDefinition("browser_use", "1.0.0", "Automate an isolated browser session on approved domains.", {"type": "object", "properties": {"url": {"type": "string", "format": "uri", "maxLength": 2048}, "action": {"type": "string", "enum": ["navigate", "extract"]}}, "required": ["url", "action"], "additionalProperties": False}, ("browser", "web"), "workspace:browser", "high", "approval_by_action", "apps/sandbox/browser", 60, {"cpu": "1", "memory_mb": 768, "network": "allowlist_only", "downloads": "scanned"}, "non_idempotent", "tool.browser.action"),
    ToolDefinition("create_chat_completion", "1.0.0", "Call a routed model through MoreAI's metered LLM gateway.", {"type": "object", "properties": {"messages": {"type": "array", "maxItems": 100}, "task_type": {"type": "string", "maxLength": 80}}, "required": ["messages"], "additionalProperties": False}, ("llm", "chat", "streaming"), "user:llm", "medium", "metered_entitlement", "engine/llm/gateway", 90, {"max_input_tokens": "model_policy", "max_output_tokens": "model_policy"}, "idempotent_with_request_key", "tool.llm.completion", ("manus", "planning", "toolcall"), True),
    ToolDefinition("file_saver", "1.0.0", "Save an artifact to an owner-scoped Supabase Storage path.", {"type": "object", "properties": {"path": {"type": "string", "maxLength": 512}, "content": {"type": "string", "maxLength": 2000000}, "mime_type": {"type": "string", "maxLength": 120}}, "required": ["path", "content"], "additionalProperties": False}, ("artifact", "storage"), "user:artifact:write", "medium", "approval_for_overwrite_or_external_share", "engine/tools/storage", 30, {"max_bytes": 2000000, "path": "user-scoped", "mime_validation": True}, "idempotent_with_checksum", "tool.artifact.write", ("manus", "planning", "toolcall"), True),
    ToolDefinition("image_generate", "1.0.0", "Generate one image through the metered OpenAI Images API and persist it as a private owner-scoped artifact.", {"type": "object", "properties": {"prompt": {"type": "string", "minLength": 1, "maxLength": 12000}, "size": {"type": "string", "enum": ["auto", "1024x1024", "1536x1024", "1024x1536"]}, "quality": {"type": "string", "enum": ["low", "medium", "high", "auto"]}, "background": {"type": "string", "enum": ["auto", "opaque"]}, "output_format": {"type": "string", "enum": ["png", "jpeg", "webp"]}}, "required": ["prompt"], "additionalProperties": False}, ("image", "generation", "media", "artifact"), "user:media:generate", "medium", "metered_entitlement_and_quota", "engine/tools/media", 600, {"max_images": 1, "max_output_bytes": 20000000, "provider": "openai", "private_artifact_storage": True}, "idempotent_by_run_and_payload", "tool.media.image.generate", ("manus", "planning", "toolcall"), True),
    ToolDefinition("video_generate", "1.0.0", "Generate a video through the metered Runway Dev task API, recover the provider task from durable checkpoints, and persist the result privately.", {"type": "object", "properties": {"prompt": {"type": "string", "minLength": 1, "maxLength": 1000}, "duration": {"type": "integer", "minimum": 2, "maximum": 10}, "ratio": {"type": "string", "enum": ["1280:720", "720:1280"]}, "seed": {"type": "integer", "minimum": 0, "maximum": 4294967295}}, "required": ["prompt"], "additionalProperties": False}, ("video", "generation", "media", "artifact", "async_task"), "user:media:generate", "medium", "metered_entitlement_and_quota", "engine/tools/video", 600, {"max_videos": 1, "max_duration_seconds": 10, "max_output_bytes": 100000000, "provider": "runway", "durable_provider_task_checkpoint": True, "private_artifact_storage": True}, "durable_task_idempotency", "tool.media.video.generate", ("manus", "planning", "toolcall"), True),
    ToolDefinition("knowledge_ingest", "1.0.0", "Index owner-provided text into the private tenant knowledge base for semantic retrieval.", {"type": "object", "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 500}, "content": {"type": "string", "minLength": 1, "maxLength": 1000000}}, "required": ["title", "content"], "additionalProperties": False}, ("knowledge", "embedding", "rag", "storage"), "user:knowledge:write", "medium", "tenant_owner_scope", "apps/worker/knowledge", 180, {"max_chars": 1000000, "max_chunks": 500, "embedding_dimensions": 1536}, "idempotent_by_content_hash", "tool.knowledge.ingest"),
    ToolDefinition("knowledge_search", "1.0.0", "Search the current user's or workspace's indexed knowledge using semantic vector similarity.", {"type": "object", "properties": {"query": {"type": "string", "minLength": 2, "maxLength": 2000}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}, "document_ids": {"type": "array", "minItems": 1, "maxItems": 20, "items": {"type": "string", "format": "uuid"}}}, "required": ["query"], "additionalProperties": False}, ("knowledge", "embedding", "rag", "retrieval"), "user:knowledge:read", "low", "tenant_owner_scope", "apps/worker/knowledge", 60, {"max_results": 20, "embedding_dimensions": 1536}, "idempotent", "tool.knowledge.search"),
    ToolDefinition("google_search", "1.0.0", "Search public web sources through an approved search provider.", {"type": "object", "properties": {"query": {"type": "string", "minLength": 2, "maxLength": 1000}}, "required": ["query"], "additionalProperties": False}, ("search", "web"), "user:search", "medium", "provider_policy", "engine/tools/search_provider", 30, {"results": 10, "network": "provider_allowlist"}, "idempotent", "tool.web.search"),
    ToolDefinition("planning", "1.0.0", "Create and update a durable plan for the current agent run.", {"type": "object", "properties": {"command": {"type": "string", "enum": ["create", "get", "mark_step"]}, "title": {"type": "string", "maxLength": 500}, "steps": {"type": "array", "maxItems": 100, "items": {"type": "string", "maxLength": 10000}}, "step_index": {"type": "integer", "minimum": 0}, "status": {"type": "string"}, "notes": {"type": "string", "maxLength": 2000}}, "required": ["command"], "additionalProperties": False}, ("planning", "orchestration"), "run:plan", "low", "none", "engine/orchestration/durable_plan_store", 15, {"steps": 100, "step_text_chars": 10000}, "idempotent_by_run_and_step", "tool.plan.mutate", ("manus", "planning", "toolcall"), True),
    ToolDefinition("python_execute", "1.0.0", "Execute Python in a disposable isolated sandbox.", {"type": "object", "properties": {"code": {"type": "string", "maxLength": 50000}, "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 120}}, "required": ["code"], "additionalProperties": False}, ("python", "computation", "filesystem"), "workspace:execute", "critical", "explicit_approval", "apps/sandbox/python", 120, {"cpu": "1", "memory_mb": 512, "pids": 32, "network": "disabled", "filesystem": "ephemeral"}, "non_idempotent", "tool.python.execute"),
    ToolDefinition("run", "1.0.0", "Run an allowlisted tool with durable execution audit.", {"type": "object", "properties": {"tool_key": {"type": "string", "maxLength": 80}, "arguments": {"type": "object"}}, "required": ["tool_key", "arguments"], "additionalProperties": False}, ("tool", "orchestration"), "run:tool", "high", "tool_policy", "apps/worker", 120, {"concurrency": "quota_policy", "timeout": "tool_policy"}, "tool_defined", "tool.execution.dispatch", ("manus", "planning", "toolcall"), True),
    ToolDefinition("workspace_restore_version", "1.0.0", "Restore a prior immutable workspace file version as a new compare-and-swap version.", {"type": "object", "properties": {"path": {"type": "string", "maxLength": 512}, "version": {"type": "integer", "minimum": 1}}, "required": ["path", "version"], "additionalProperties": False}, ("filesystem", "versioning"), "workspace:file:restore", "high", "approval_for_overwrite", "apps/worker/workspace", 45, {"max_file_bytes": 2000000, "restore_mode": "append-new-version"}, "idempotent_with_version_fence", "tool.workspace.restore", ("manus", "planning", "toolcall"), True),
    ToolDefinition("workspace_read_file", "1.0.0", "Read an owner/member-scoped UTF-8 workspace file with SHA-256 integrity verification.", {"type": "object", "properties": {"path": {"type": "string", "minLength": 1, "maxLength": 512}}, "required": ["path"], "additionalProperties": False}, ("filesystem", "workspace", "read"), "workspace:file:read", "low", "workspace_member_scope", "engine/tools/workspace", 30, {"max_file_bytes": 2000000, "encoding": "utf-8", "integrity": "sha256"}, "idempotent", "tool.workspace.read", ("manus", "planning", "toolcall"), True),
    ToolDefinition("str_replace_editor", "1.0.0", "Edit files inside an isolated task workspace using version-fenced compare-and-swap.", {"type": "object", "properties": {"operation": {"type": "string", "enum": ["create", "edit", "delete", "rename", "restore_deleted"]}, "path": {"type": "string", "maxLength": 512}, "new_path": {"type": "string", "maxLength": 512}, "old_str": {"type": "string", "maxLength": 50000}, "new_str": {"type": "string", "maxLength": 50000}, "expected_version": {"type": "integer", "minimum": 0}}, "required": ["path"], "additionalProperties": False}, ("filesystem", "code"), "workspace:file:write", "high", "approval_for_overwrite", "apps/sandbox/workspace", 30, {"max_file_bytes": 2000000, "path": "workspace-root-only"}, "idempotent_with_content_hash", "tool.workspace.edit", ("manus", "planning", "toolcall"), True),
    ToolDefinition("terminate", "1.0.0", "End the current agent interaction with an explicit success or failure status.", {"type": "object", "properties": {"status": {"type": "string", "enum": ["success", "failure"]}}, "required": ["status"], "additionalProperties": False}, ("termination", "lifecycle"), "run:terminate", "low", "none", "engine/agents/durable_tool_runtime", 5, {"scope": "current-run-only"}, "idempotent", "tool.run.terminate", ("manus", "planning", "toolcall"), True),
)


def tool_catalog() -> list[dict[str, object]]:
    return [
        {
            "key": item.key,
            "version": item.version,
            "description": item.description,
            "input_schema": item.input_schema,
            "capability_tags": list(item.capability_tags),
            "permission_scope": item.permission_scope,
            "risk": item.risk,
            "approval_mode": item.approval_mode,
            "execution_environment": item.execution_environment,
            "timeout_seconds": item.timeout_seconds,
            "resource_limits": item.resource_limits,
            "idempotency": item.idempotency,
            "audit_category": item.audit_category,
            "available_by_default": list(item.available_by_default),
            "enabled_by_default": item.enabled_by_default,
        }
        for item in OPENMANUS_TOOL_CATALOG
    ]
