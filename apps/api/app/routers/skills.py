from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/skills", tags=["customer-skills"])
PERMISSION_KEYS = {"network.read", "workspace.read", "workspace.write", "browser.navigate", "browser.download", "search.web", "files.read", "files.write", "calendar.read", "calendar.write", "gmail.read", "gmail.send"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]{1,119}$")


class SkillImportRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)
    source_repository: str = Field(min_length=3, max_length=255)
    source_ref: str = Field(min_length=1, max_length=160)
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_path: str = Field(min_length=1, max_length=512)
    source_blob_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    version: str = Field(min_length=1, max_length=80)
    license_id: str = Field(min_length=1, max_length=80)
    license_url: str | None = Field(default=None, max_length=512)
    license_evidence: str | None = Field(default=None, max_length=4000)
    manifest: dict[str, Any] = Field(default_factory=dict)
    requested_permissions: list[str] = Field(default_factory=list, max_length=32)


class SkillValidationResponse(BaseModel):
    skill_id: UUID
    validation_status: str
    license_status: str
    findings: list[str]


class SkillPermissionRequest(BaseModel):
    permissions: list[str] = Field(min_length=1, max_length=32)


@router.get("")
async def list_skills(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    owner = user["id"]
    packages = await repo.select("moreai_skill_packages", {
        "owner_user_id": f"eq.{owner}",
        "select": "id,slug,name,description,source_repository,source_ref,source_commit,source_path,source_blob_sha,content_sha256,version,license_id,license_url,license_status,manifest,requested_permissions,validation_status,validation_report,publication_status,created_at,updated_at",
        "order": "updated_at.desc,id.desc", "limit": "100",
    })
    installs = await repo.select("moreai_skill_installs", {
        "owner_user_id": f"eq.{owner}",
        "select": "id,skill_package_id,status,execution_enabled,permission_request,permission_status,created_at,updated_at",
        "order": "updated_at.desc", "limit": "100",
    })
    by_skill = {str(row["skill_package_id"]): row for row in installs}
    return {"items": [{**row, "installation": by_skill.get(str(row["id"]))} for row in packages], "count": len(packages)}


@router.post("", status_code=201)
async def import_skill(body: SkillImportRequest, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    if not SLUG.fullmatch(body.slug) or not SHA40.fullmatch(body.source_commit) or not SHA40.fullmatch(body.source_blob_sha) or not SHA64.fullmatch(body.content_sha256):
        raise HTTPException(422, "skill_provenance_format_invalid")
    if body.source_repository.count("/") != 1 or body.source_repository.startswith("/") or ".." in body.source_path.split("/"):
        raise HTTPException(422, "skill_source_reference_invalid")
    if any(permission not in PERMISSION_KEYS for permission in body.requested_permissions):
        raise HTTPException(422, "skill_permission_key_not_allowlisted")
    if len(set(body.requested_permissions)) != len(body.requested_permissions):
        raise HTTPException(422, "duplicate_skill_permissions")
    repo = repository(request)
    existing = await repo.select("moreai_skill_packages", {
        "owner_user_id": f"eq.{user['id']}", "source_repository": f"eq.{body.source_repository}",
        "source_commit": f"eq.{body.source_commit}", "source_path": f"eq.{body.source_path}",
        "select": "id", "limit": "1",
    })
    if existing:
        raise HTTPException(409, "skill_source_already_imported")
    # Import stores provenance and metadata only. It never downloads or executes upstream code.
    return await repo.insert("moreai_skill_packages", {
        **body.model_dump(),
        "owner_user_id": user["id"], "license_status": "unverified",
        "validation_status": "pending", "validation_report": {"findings": ["Source contents and nested files have not been fetched or scanned.", "License grant and attribution requirements require human review."]},
        "publication_status": "private",
    })


@router.post("/{skill_id}/validate", response_model=SkillValidationResponse)
async def validate_skill(skill_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    rows = await repo.select("moreai_skill_packages", {
        "id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id,slug,name,source_repository,source_commit,source_path,source_blob_sha,content_sha256,license_id,license_evidence,manifest,requested_permissions",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "skill_not_found")
    skill = rows[0]
    findings: list[str] = []
    files = await repo.select("moreai_skill_source_files", {
        "skill_package_id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "relative_path,git_blob_sha,content_sha256,byte_size,text_content,binary_content_base64",
        "limit": "40",
    })
    manifest = skill.get("manifest") if isinstance(skill.get("manifest"), dict) else {}
    if not manifest:
        findings.append("Skill manifest is missing; package is not executable.")
    if not files:
        findings.append("Pinned source files have not been ingested and integrity-verified.")
    if len(files) > 40 or sum(int(item.get("byte_size") or 0) for item in files) > 5 * 1024 * 1024:
        findings.append("Source package exceeds the file-count or expanded-size limit.")
    if files and not any(item.get("git_blob_sha") == skill.get("source_blob_sha") and item.get("content_sha256") == skill.get("content_sha256") for item in files):
        findings.append("Root entrypoint does not match the immutable provenance hashes.")
    for item in files:
        if not SHA40.fullmatch(str(item.get("git_blob_sha") or "")) or not SHA64.fullmatch(str(item.get("content_sha256") or "")):
            findings.append("One or more source file hashes are malformed.")
            break
    if not skill.get("license_evidence"):
        findings.append("License evidence is missing; legal approval is required.")
    if not skill.get("source_path") or ".." in str(skill["source_path"]).split("/"):
        findings.append("Unsafe source path.")
    if not skill.get("source_blob_sha") or not skill.get("content_sha256"):
        findings.append("Immutable source/content hashes are required.")
    if not isinstance(skill.get("requested_permissions"), list) or any(x not in PERMISSION_KEYS for x in skill["requested_permissions"]):
        findings.append("Requested permissions contain unsupported capabilities.")
    # Static metadata validation is not a malware scan, dependency audit or rights clearance.
    status = "review_required" if findings else "validated"
    license_status = "review_required" if findings else "unverified"
    await repo.update("moreai_skill_packages", {"id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}"}, {
        "validation_status": status, "license_status": license_status,
        "validation_report": {"findings": findings, "checked_at": datetime.now(timezone.utc).isoformat(), "scope": "metadata_only"},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"skill_id": skill_id, "validation_status": status, "license_status": license_status, "findings": findings}


@router.post("/{skill_id}/install", status_code=201)
async def install_skill(skill_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    packages = await repo.select("moreai_skill_packages", {
        "id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id,validation_status,publication_status", "limit": "1",
    })
    if not packages:
        raise HTTPException(404, "skill_not_found")
    if packages[0]["validation_status"] != "validated" or packages[0]["publication_status"] != "published":
        raise HTTPException(409, "skill_must_be_validated_and_published_before_install")
    existing = await repo.select("moreai_skill_installs", {
        "owner_user_id": f"eq.{user['id']}", "skill_package_id": f"eq.{skill_id}",
        "select": "id", "limit": "1",
    })
    if existing:
        raise HTTPException(409, "skill_already_installed")
    return await repo.insert("moreai_skill_installs", {
        "owner_user_id": user["id"], "skill_package_id": str(skill_id),
        "status": "installed", "execution_enabled": False, "permission_status": "not_requested",
    })


@router.post("/{skill_id}/permissions")
async def request_skill_permissions(skill_id: UUID, body: SkillPermissionRequest, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    if len(set(body.permissions)) != len(body.permissions) or any(key not in PERMISSION_KEYS for key in body.permissions):
        raise HTTPException(422, "skill_permission_key_not_allowlisted")
    repo = repository(request)
    rows = await repo.select("moreai_skill_installs", {
        "owner_user_id": f"eq.{user['id']}", "skill_package_id": f"eq.{skill_id}",
        "select": "id", "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "skill_installation_not_found")
    updated = await repo.update("moreai_skill_installs", {"id": f"eq.{rows[0]['id']}", "owner_user_id": f"eq.{user['id']}"}, {
        "permission_request": body.permissions, "permission_status": "pending_review",
        "execution_enabled": False, "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    if not updated:
        raise HTTPException(409, "skill_permission_request_conflict")
    return updated[0]


import base64
import hashlib
from urllib.parse import quote, unquote
from pathlib import PurePosixPath

PINNED_SKILL_SOURCES = {
    ("smixs", "visual-skills"): {"61a60d317f0fa0c3dc98902e58a7cb178838ae3f"},
    ("scenario-labs", "skills"): {"94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9"},
}
LOCAL_REFERENCE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)|^\s*[-*+]\s+.*?\]\(([^)]+)\)", re.MULTILINE)


def _safe_skill_path(value: str) -> str:
    decoded = unquote(value.split("#", 1)[0].split("?", 1)[0]).replace("\\", "/")
    path = PurePosixPath(decoded)
    if not decoded or decoded.startswith("/") or any(part in {"", ".", ".."} for part in decoded.split("/")):
        raise HTTPException(422, "skill_source_path_invalid")
    return str(path)


@router.post("/{skill_id}/ingest")
async def ingest_pinned_skill_source(skill_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    rows = await repo.select("moreai_skill_packages", {
        "id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id,source_repository,source_commit,source_path,source_blob_sha,content_sha256",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "skill_not_found")
    skill = rows[0]
    parts = str(skill["source_repository"]).split("/")
    if len(parts) != 2 or skill["source_commit"] not in PINNED_SKILL_SOURCES.get((parts[0], parts[1]), set()):
        raise HTTPException(403, "skill_source_repository_or_commit_not_pinned")
    root_path = _safe_skill_path(str(skill["source_path"]))
    queue = [root_path]
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    total_bytes = 0
    http = request.app.state.http
    while queue:
        relative = queue.pop(0)
        if relative in seen:
            continue
        seen.add(relative)
        if len(seen) > 40:
            raise HTTPException(413, "skill_source_file_count_limit_exceeded")
        url = f"https://api.github.com/repos/{parts[0]}/{parts[1]}/contents/{quote(relative, safe='/')}?ref={skill['source_commit']}"
        response = await http.get(url, headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}, timeout=15.0, follow_redirects=False)
        if response.status_code != 200:
            raise HTTPException(502, "skill_source_fetch_failed")
        item = response.json()
        if not isinstance(item, dict) or item.get("type") != "file" or item.get("encoding") != "base64":
            raise HTTPException(422, "skill_source_file_type_unsupported")
        encoded = item.get("content")
        if not isinstance(encoded, str):
            raise HTTPException(502, "skill_source_content_missing")
        try:
            content = base64.b64decode(encoded, validate=False)
        except Exception as exc:
            raise HTTPException(502, "skill_source_base64_invalid") from exc
        if len(content) > 524288:
            raise HTTPException(413, "skill_source_file_size_limit_exceeded")
        total_bytes += len(content)
        if total_bytes > 5 * 1024 * 1024:
            raise HTTPException(413, "skill_source_package_size_limit_exceeded")
        git_sha = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\\0" + content).hexdigest()
        sha_api = item.get("sha")
        if not isinstance(sha_api, str) or git_sha != sha_api:
            raise HTTPException(409, "skill_git_blob_hash_mismatch")
        digest = hashlib.sha256(content).hexdigest()
        if relative == root_path and (git_sha != skill["source_blob_sha"] or digest != skill["content_sha256"]):
            raise HTTPException(409, "skill_root_provenance_hash_mismatch")
        media_type = str(item.get("content_type") or "application/octet-stream")[:120]
        is_text = media_type.startswith("text/") or relative.lower().endswith((".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".js", ".ts", ".svg"))
        text_content = content.decode("utf-8", errors="strict") if is_text else None
        records.append({
            "skill_package_id": str(skill_id), "owner_user_id": user["id"],
            "relative_path": relative, "git_blob_sha": git_sha, "content_sha256": digest,
            "media_type": media_type, "byte_size": len(content),
            "text_content": text_content,
            "binary_content_base64": None if is_text else base64.b64encode(content).decode("ascii"),
        })
        if text_content:
            for match in LOCAL_REFERENCE.finditer(text_content):
                target = (match.group(1) or match.group(2) or "").strip()
                if not target or target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                    continue
                target = target.split("#", 1)[0].split("?", 1)[0]
                if not target:
                    continue
                base = PurePosixPath(relative).parent
                try:
                    resolved = _safe_skill_path(str(base / unquote(target)))
                except HTTPException:
                    continue
                if resolved not in seen and resolved not in queue:
                    queue.append(resolved)
    existing = await repo.select("moreai_skill_source_files", {
        "skill_package_id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}",
        "select": "id", "limit": "1",
    })
    if existing:
        raise HTTPException(409, "skill_source_already_ingested_immutable")
    for record in records:
        await repo.insert("moreai_skill_source_files", record)
    await repo.update("moreai_skill_packages", {
        "id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}",
    }, {
        "validation_status": "review_required",
        "validation_report": {
            "scope": "pinned_github_content_integrity",
            "file_count": len(records), "total_bytes": total_bytes,
            "files": [{"path": x["relative_path"], "git_blob_sha": x["git_blob_sha"], "sha256": x["content_sha256"], "bytes": x["byte_size"]} for x in records],
            "findings": ["File contents and local Markdown references were fetched at the pinned commit and Git blob SHA verified.", "License, nested dependency, script safety and asset rights still require separate review."],
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"skill_id": str(skill_id), "source_commit": skill["source_commit"], "file_count": len(records), "total_bytes": total_bytes, "integrity": "verified", "execution_enabled": False}
