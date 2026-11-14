from __future__ import annotations

import hashlib
import json
from typing import Any

from app.client import WorkerRpcClient


class SupabaseSkillResolver:
    """Resolves only immutable, approved skill snapshots for a single durable Agent Run."""

    def __init__(self, client: WorkerRpcClient):
        self.client = client

    async def resolve(self, *, skill_ids: list[str], user_id: str, run_id: str) -> list[dict[str, Any]]:
        if not skill_ids:
            return []
        if len(skill_ids) > 10 or len(set(skill_ids)) != len(skill_ids):
            raise ValueError("skill_selection_invalid")
        resolved: list[dict[str, Any]] = []
        for skill_id in skill_ids:
            packages = await self.client.select("moreai_skill_packages", {
                "id": f"eq.{skill_id}", "owner_user_id": f"eq.{user_id}",
                "validation_status": "eq.validated", "license_status": "eq.approved",
                "publication_status": "eq.published",
                "select": "id,version,content_sha256,manifest,requested_permissions",
                "limit": "1",
            })
            if not packages:
                raise PermissionError("skill_not_published_or_approved")
            installs = await self.client.select("moreai_skill_installs", {
                "skill_package_id": f"eq.{skill_id}", "owner_user_id": f"eq.{user_id}",
                "status": "eq.installed", "execution_enabled": "eq.true",
                "permission_status": "eq.approved",
                "select": "id,granted_permissions",
                "limit": "1",
            })
            if not installs:
                raise PermissionError("skill_execution_permission_not_granted")
            package, install = packages[0], installs[0]
            requested = package.get("requested_permissions") or []
            granted = install.get("granted_permissions") or []
            if not isinstance(requested, list) or not isinstance(granted, list) or not set(granted).issubset(set(requested)):
                raise PermissionError("skill_permission_snapshot_invalid")
            files = await self.client.select("moreai_skill_source_files", {
                "skill_package_id": f"eq.{skill_id}", "owner_user_id": f"eq.{user_id}",
                "select": "relative_path,content_sha256,text_content,byte_size,media_type",
                "order": "relative_path.asc", "limit": "40",
            })
            if not files:
                raise PermissionError("skill_source_files_missing")
            instruction_files = [
                item for item in files
                if isinstance(item.get("text_content"), str)
                and str(item.get("relative_path", "")).lower().endswith((".md", ".txt"))
            ]
            if not instruction_files:
                raise PermissionError("skill_instruction_files_missing")
            body = "\n\n".join(
                f"### {item['relative_path']}\n{item['text_content'][:24000]}"
                for item in instruction_files
            )[:100000]
            snapshot = {
                "skill_id": str(skill_id), "version": package["version"],
                "content_sha256": package["content_sha256"],
                "permissions": sorted(granted),
            }
            await self.client.insert("moreai_skill_execution_audit", {
                "skill_package_id": str(skill_id), "skill_install_id": install["id"],
                "owner_user_id": user_id, "agent_run_id": run_id,
                "skill_version": package["version"],
                "skill_content_sha256": package["content_sha256"],
                "permission_snapshot": sorted(granted), "event_type": "resolved",
                "event_detail": {"source_file_count": len(files), "instruction_file_count": len(instruction_files)},
            })
            resolved.append({"snapshot": snapshot, "instructions": body})
        return resolved
