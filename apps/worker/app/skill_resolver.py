from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from app.client import WorkerRpcClient


MAX_SKILL_SOURCE_FILES = 64


# Keep this boundary aligned with DurableOpenManusRuntime.skill_permission_tools.
# Unknown permission labels must fail closed even if a privileged DB row is malformed.
ALLOWED_SKILL_PERMISSIONS = frozenset({
    "network.read", "search.web",
    "workspace.read", "workspace.write",
    "browser.navigate", "browser.download",
    "files.read", "files.write",
    "gmail.read", "calendar.read", "gmail.send", "calendar.write",
})


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
                "select": "id,version,content_sha256,source_path,source_blob_sha,manifest,requested_permissions,validation_report",
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
            if (
                not isinstance(requested, list)
                or not isinstance(granted, list)
                or any(not isinstance(value, str) or value not in ALLOWED_SKILL_PERMISSIONS for value in requested)
                or any(not isinstance(value, str) or value not in ALLOWED_SKILL_PERMISSIONS for value in granted)
                or len(requested) != len(set(requested))
                or len(granted) != len(set(granted))
                or not set(granted).issubset(set(requested))
            ):
                raise PermissionError("skill_permission_snapshot_invalid")
            files = await self.client.select("moreai_skill_source_files", {
                "skill_package_id": f"eq.{skill_id}", "owner_user_id": f"eq.{user_id}",
                "select": "relative_path,git_blob_sha,content_sha256,text_content,binary_content_base64,byte_size,media_type",
                "order": "relative_path.asc", "limit": str(MAX_SKILL_SOURCE_FILES),
            })
            if not files:
                raise PermissionError("skill_source_files_missing")

            # A published skill must resolve the complete file inventory that
            # passed static validation, not an arbitrary first page of files.
            validation_report = package.get("validation_report")
            validation_report = validation_report if isinstance(validation_report, dict) else {}
            source_inventory = validation_report.get("source_inventory")
            source_inventory = source_inventory if isinstance(source_inventory, dict) else {}
            sbom = source_inventory.get("sbom")
            sbom = sbom if isinstance(sbom, dict) else {}
            sbom_files = sbom.get("files")
            if not isinstance(sbom_files, list) or not 1 <= len(sbom_files) <= MAX_SKILL_SOURCE_FILES:
                raise PermissionError("skill_source_sbom_file_inventory_invalid")
            expected_sha_by_path: dict[str, str] = {}
            for item in sbom_files:
                if not isinstance(item, dict) or not isinstance(item.get("fileName"), str):
                    raise PermissionError("skill_source_sbom_file_entry_invalid")
                relative = item["fileName"].removeprefix("./")
                checksums = item.get("checksums") if isinstance(item.get("checksums"), list) else []
                sha256 = next(
                    (checksum.get("checksumValue") for checksum in checksums
                     if isinstance(checksum, dict) and checksum.get("algorithm") == "SHA256"),
                    None,
                )
                if (
                    not relative or not isinstance(sha256, str) or len(sha256) != 64
                    or any(character not in "0123456789abcdef" for character in sha256)
                    or relative in expected_sha_by_path
                ):
                    raise PermissionError("skill_source_sbom_file_entry_invalid")
                expected_sha_by_path[relative] = sha256
            actual_paths = {
                item.get("relative_path") for item in files
                if isinstance(item.get("relative_path"), str)
            }
            if len(files) != len(expected_sha_by_path) or actual_paths != set(expected_sha_by_path):
                raise PermissionError("skill_source_file_inventory_incomplete")

            total_bytes = 0
            root_verified = False
            for source_file in files:
                relative_path = source_file.get("relative_path")
                size = source_file.get("byte_size")
                if not isinstance(relative_path, str) or not isinstance(size, int) or size < 0 or size > 524288:
                    raise PermissionError("skill_source_file_metadata_invalid")
                total_bytes += size
                if total_bytes > 5 * 1024 * 1024:
                    raise PermissionError("skill_source_package_size_limit_exceeded")
                if isinstance(source_file.get("text_content"), str):
                    raw = source_file["text_content"].encode("utf-8")
                elif isinstance(source_file.get("binary_content_base64"), str):
                    try:
                        raw = base64.b64decode(source_file["binary_content_base64"], validate=True)
                    except Exception as exc:
                        raise PermissionError("skill_source_binary_encoding_invalid") from exc
                else:
                    raise PermissionError("skill_source_file_content_missing")
                content_sha = hashlib.sha256(raw).hexdigest()
                if len(raw) != size or content_sha != source_file.get("content_sha256"):
                    raise PermissionError("skill_source_sha256_mismatch")
                if expected_sha_by_path.get(relative_path) != content_sha:
                    raise PermissionError("skill_source_sbom_content_mismatch")
                git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                if git_blob != source_file.get("git_blob_sha"):
                    raise PermissionError("skill_source_git_blob_mismatch")
                if relative_path == package.get("source_path"):
                    root_verified = git_blob == package.get("source_blob_sha") and hashlib.sha256(raw).hexdigest() == package.get("content_sha256")
            if not root_verified:
                raise PermissionError("skill_source_root_provenance_mismatch")
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
            prior_resolution = await self.client.select("moreai_skill_execution_audit", {
                "skill_package_id": f"eq.{skill_id}",
                "skill_install_id": f"eq.{install['id']}",
                "owner_user_id": f"eq.{user_id}",
                "agent_run_id": f"eq.{run_id}",
                "event_type": "eq.resolved",
                "select": "id",
                "limit": "1",
            })
            if not prior_resolution:
                await self.client.insert("moreai_skill_execution_audit", {
                    "skill_package_id": str(skill_id), "skill_install_id": install["id"],
                    "owner_user_id": user_id, "agent_run_id": run_id,
                    "skill_version": package["version"],
                    "skill_content_sha256": package["content_sha256"],
                    "permission_snapshot": sorted(granted), "event_type": "resolved",
                    "event_detail": {"source_file_count": len(files), "instruction_file_count": len(instruction_files), "verified_total_bytes": total_bytes},
                })
            resolved.append({"snapshot": snapshot, "instructions": body, "install_id": install["id"]})
        return resolved


    async def record_executed(self, *, resolved_skills: list[dict[str, Any]], user_id: str, run_id: str) -> None:
        for item in resolved_skills:
            snapshot = item.get("snapshot") if isinstance(item.get("snapshot"), dict) else {}
            skill_id = snapshot.get("skill_id")
            if not isinstance(skill_id, str) or not isinstance(item.get("install_id"), str):
                raise ValueError("skill_execution_audit_identity_invalid")
            existing = await self.client.select("moreai_skill_execution_audit", {
                "skill_package_id": f"eq.{skill_id}",
                "skill_install_id": f"eq.{item['install_id']}",
                "owner_user_id": f"eq.{user_id}",
                "agent_run_id": f"eq.{run_id}",
                "event_type": "eq.executed",
                "select": "id",
                "limit": "1",
            })
            if existing:
                continue
            await self.client.insert("moreai_skill_execution_audit", {
                "skill_package_id": skill_id, "skill_install_id": item["install_id"],
                "owner_user_id": user_id, "agent_run_id": run_id,
                "skill_version": snapshot.get("version"),
                "skill_content_sha256": snapshot.get("content_sha256"),
                "permission_snapshot": snapshot.get("permissions") or [],
                "event_type": "executed",
                "event_detail": {"execution_outcome": "agent_run_succeeded"},
            })
