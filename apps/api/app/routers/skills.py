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
    manifest = skill.get("manifest") if isinstance(skill.get("manifest"), dict) else {}
    if not manifest:
        findings.append("Skill manifest is missing; package is not executable.")
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
