from __future__ import annotations

import re
import asyncio
import json
import tomllib
from pathlib import PurePosixPath
from urllib.parse import quote
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


def _source_review_inventory(files: list[dict[str, Any]]) -> dict[str, Any]:
    license_files: list[dict[str, Any]] = []
    dependency_files: list[str] = []
    dependency_file_evidence: list[dict[str, Any]] = []
    manifest_files: list[str] = []
    dependencies: list[dict[str, Any]] = []
    dependency_edges: list[dict[str, str]] = []
    npm_declared: dict[str, set[str]] = {}
    npm_locked: dict[str, set[str]] = {}

    def add_dependency(ecosystem: str, name: Any, version: Any, path: str, *, status: str, integrity: Any = None) -> None:
        if not isinstance(name, str) or not name.strip() or not isinstance(version, str) or not version.strip():
            return
        dependencies.append({
            "ecosystem": ecosystem, "name": name.strip(),
            "exact_version": version.strip(), "source_manifest": path,
            "status": status, "integrity": integrity if isinstance(integrity, str) else None,
        })

    for item in files:
        path = str(item.get("relative_path") or "")
        name = PurePosixPath(path).name.lower()
        text = item.get("text_content")
        if name in {"skill.md", "skill.yaml", "skill.yml", "skill.json", "manifest.json", "package.json", "pyproject.toml"}:
            manifest_files.append(path)
        if name in {"package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "requirements.txt", "requirements.lock", "pyproject.toml", "poetry.lock", "uv.lock", "pipfile", "pipfile.lock", "cargo.toml", "cargo.lock", "go.mod", "go.sum", "composer.json", "composer.lock", "gemfile", "gemfile.lock"}:
            dependency_file_evidence.append({
                "path": path,
                "sha256": item.get("content_sha256"),
                "git_blob_sha": item.get("git_blob_sha"),
                "byte_size": item.get("byte_size"),
                "role": "lockfile" if name.endswith((".lock", "-lock.json", ".sum")) or name in {"pnpm-lock.yaml", "yarn.lock", "go.sum"} else "manifest_or_constraints",
            })
        if name.startswith(("license", "licence", "copying", "notice", "third_party")):
            license_files.append({
                "path": path, "sha256": item.get("content_sha256"),
                "bytes": item.get("byte_size"),
            })
        if not isinstance(text, str):
            continue
        if name in {"package.json", "package-lock.json", "npm-shrinkwrap.json"}:
            dependency_files.append(path)
            try:
                parsed = json.loads(text)
                if not isinstance(parsed, dict):
                    raise ValueError("manifest_root_not_object")
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "npm", "status": "parse_error"})
                continue
            if name == "package.json":
                declared: set[str] = set()
                for group in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                    values = parsed.get(group) or {}
                    if not isinstance(values, dict):
                        dependencies.append({"manifest": path, "ecosystem": "npm", "status": "invalid_dependency_group"})
                        continue
                    for package, spec in values.items():
                        if isinstance(package, str):
                            declared.add(package)
                        dependencies.append({
                            "ecosystem": "npm", "name": package, "requested": spec,
                            "exact_version": None, "source_manifest": path,
                            "status": "manifest_declared_requires_lockfile",
                        })
                npm_declared[path] = declared
            else:
                locked: set[str] = set()
                package_entries = parsed.get("packages")
                if isinstance(package_entries, dict):
                    for package_path, details in package_entries.items():
                        if not package_path or not isinstance(details, dict):
                            continue
                        marker = "node_modules/"
                        if marker not in package_path:
                            continue
                        package_name = package_path.rsplit(marker, 1)[-1]
                        if package_name.startswith("@") and "/" not in package_name:
                            continue
                        version = details.get("version")
                        if isinstance(version, str):
                            locked.add(package_name)
                            add_dependency("npm", package_name, version, path, status="lockfile_pinned", integrity=details.get("integrity"))
                            for group in ("dependencies", "optionalDependencies", "peerDependencies"):
                                declared_edges = details.get(group)
                                if isinstance(declared_edges, dict):
                                    dependency_edges.extend({
                                        "ecosystem": "npm", "from": package_name,
                                        "from_locator": package_path,
                                        "from_version": version, "to": dep,
                                        "requested": str(requested_spec),
                                        "kind": group, "source_manifest": path,
                                    } for dep, requested_spec in declared_edges.items() if isinstance(dep, str))
                # npm lockfile v1 stores transitive entries recursively under dependencies.
                def visit_v1(entries: Any) -> None:
                    if not isinstance(entries, dict):
                        return
                    for package_name, details in entries.items():
                        if not isinstance(details, dict):
                            continue
                        version = details.get("version")
                        if isinstance(version, str):
                            locked.add(package_name)
                            add_dependency("npm", package_name, version, path, status="lockfile_pinned", integrity=details.get("integrity"))
                            declared_edges = details.get("requires")
                            if isinstance(declared_edges, dict):
                                dependency_edges.extend({
                                    "ecosystem": "npm", "from": package_name,
                                    "from_version": version, "to": dep,
                                    "requested": str(requested_spec), "kind": "requires",
                                    "source_manifest": path,
                                } for dep, requested_spec in declared_edges.items() if isinstance(dep, str))
                        visit_v1(details.get("dependencies"))
                visit_v1(parsed.get("dependencies"))
                npm_locked[path] = locked
        elif name == "requirements.txt":
            dependency_files.append(path)
            for line in text.splitlines():
                raw = line.split("#", 1)[0].strip()
                if not raw:
                    continue
                if raw.startswith(("-r ", "--", "git+", "http:", "https:")):
                    dependencies.append({"manifest": path, "ecosystem": "pypi", "requested": raw, "status": "external_or_nested_requirement_requires_review"})
                    continue
                match = re.match(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)(?:\s*;.*)?$", raw)
                dependencies.append({
                    "ecosystem": "pypi",
                    "name": match.group(1) if match else re.split(r"[<>=!~;\s]", raw, maxsplit=1)[0],
                    "requested": raw, "exact_version": None, "source_manifest": path,
                    "status": "manifest_declared_requires_lockfile",
                })
        elif name == "pyproject.toml":
            dependency_files.append(path)
            try:
                parsed = tomllib.loads(text)
                declared = parsed.get("project", {}).get("dependencies", [])
                poetry = parsed.get("tool", {}).get("poetry", {})
                declared = list(declared) if isinstance(declared, list) else []
                poetry_deps = poetry.get("dependencies", {}) if isinstance(poetry, dict) else {}
                if isinstance(poetry_deps, dict):
                    declared.extend(f"{key}{value}" for key, value in poetry_deps.items() if key.lower() != "python")
                for raw in declared:
                    name_match = re.match(r"^([A-Za-z0-9_.-]+)", str(raw))
                    dependencies.append({
                        "ecosystem": "pypi", "name": name_match.group(1) if name_match else str(raw),
                        "requested": raw, "exact_version": None, "source_manifest": path,
                        "status": "manifest_declared_requires_lockfile",
                    })
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "pypi", "status": "parse_error"})
        elif name in {"poetry.lock", "uv.lock"}:
            dependency_files.append(path)
            try:
                parsed = tomllib.loads(text)
                entries = parsed.get("package", []) if name == "poetry.lock" else parsed.get("package", [])
                if not isinstance(entries, list):
                    raise ValueError("lockfile_package_list_missing")
                for package in entries:
                    if isinstance(package, dict):
                        source = package.get("source")
                        if isinstance(source, dict) and any(source.get(key) for key in ("url", "reference", "type")):
                            dependencies.append({
                                "ecosystem": "pypi", "name": package.get("name"),
                                "exact_version": package.get("version"), "source_manifest": path,
                                "status": "non_registry_source_requires_provenance",
                                "source_type": source.get("type"), "source_url": source.get("url"),
                                "source_reference": source.get("reference"),
                            })
                        else:
                            package_name = package.get("name")
                            package_version = package.get("version")
                            add_dependency("pypi", package_name, package_version, path, status="lockfile_pinned")
                        package_name = package.get("name")
                        package_dependencies = package.get("dependencies")
                        if isinstance(package_dependencies, dict):
                            dependency_edges.extend({
                                "ecosystem": "pypi", "from": str(package_name),
                                "to": str(dep_name), "kind": "dependency",
                                "requested": str(dep_spec),
                            } for dep_name, dep_spec in package_dependencies.items())
                        elif isinstance(package_dependencies, list):
                            for dependency in package_dependencies:
                                if isinstance(dependency, dict) and isinstance(dependency.get("name"), str):
                                    dependency_edges.append({
                                        "ecosystem": "pypi", "from": str(package_name),
                                        "to": dependency["name"], "kind": "dependency",
                                        "requested": str(dependency.get("specifier") or dependency.get("version") or ""),
                                    })
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "pypi", "status": "parse_error"})
        elif name == "pipfile.lock":
            dependency_files.append(path)
            try:
                parsed = json.loads(text)
                for group in ("default", "develop"):
                    for package, details in (parsed.get(group) or {}).items():
                        if isinstance(details, dict):
                            version = details.get("version")
                            if isinstance(version, str) and version.startswith("=="):
                                add_dependency("pypi", package, version[2:], path, status="lockfile_pinned", integrity=";".join(details.get("hashes") or []))
                            else:
                                dependencies.append({"manifest": path, "ecosystem": "pypi", "name": package, "status": "lockfile_version_missing"})
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "pypi", "status": "parse_error"})
        elif name == "cargo.lock":
            dependency_files.append(path)
            try:
                parsed = tomllib.loads(text)
                for package in parsed.get("package", []):
                    add_dependency("cargo", package.get("name"), package.get("version"), path, status="lockfile_pinned")
                    for dependency in package.get("dependencies", []) if isinstance(package.get("dependencies"), list) else []:
                        if isinstance(dependency, str):
                            # Cargo lock entries encode name, version and source in a
                            # single string; retain all three rather than collapsing
                            # distinct versions or registry/git sources by name.
                            parts = dependency.split(" ")
                            dependency_edges.append({
                                "ecosystem": "cargo",
                                "from": str(package.get("name")),
                                "from_version": str(package.get("version") or ""),
                                "from_source": str(package.get("source") or ""),
                                "to": parts[0],
                                "to_version": parts[1] if len(parts) > 1 else "",
                                "to_source": " ".join(parts[2:]) if len(parts) > 2 else "",
                                "kind": "dependency", "source_manifest": path,
                            })
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "cargo", "status": "parse_error"})
        elif name == "composer.lock":
            dependency_files.append(path)
            try:
                parsed = json.loads(text)
                composer_packages: dict[str, list[dict[str, Any]]] = {}
                composer_edges: list[dict[str, Any]] = []
                for package in (parsed.get("packages", []) or []) + (parsed.get("packages-dev", []) or []):
                    if not isinstance(package, dict):
                        continue
                    package_name = package.get("name")
                    package_version = str(package.get("version") or "")
                    source = package.get("source") if isinstance(package.get("source"), dict) else {}
                    dist = package.get("dist") if isinstance(package.get("dist"), dict) else {}
                    locator = {
                        "name": package_name, "version": package_version,
                        "source_type": source.get("type"), "source_url": source.get("url"),
                        "source_reference": source.get("reference"),
                        "dist_type": dist.get("type"), "dist_url": dist.get("url"),
                        "dist_reference": dist.get("reference"),
                    }
                    if isinstance(package_name, str):
                        composer_packages.setdefault(package_name, []).append(locator)
                    add_dependency("composer", package_name, package_version, path, status="lockfile_pinned",
                                   integrity=dist.get("shasum") or dist.get("reference"))
                    for group in ("require", "require-dev"):
                        required = package.get(group)
                        if isinstance(required, dict):
                            for dep, constraint in required.items():
                                if not isinstance(dep, str) or dep.lower().startswith(("php", "ext-", "lib-")):
                                    continue
                                composer_edges.append({
                                    "ecosystem":"composer", "from":str(package_name),
                                    "from_version":package_version,
                                    "from_source_reference":str(source.get("reference") or ""),
                                    "from_dist_reference":str(dist.get("reference") or ""),
                                    "to":dep, "requested":str(constraint),
                                    "kind":group, "source_manifest":path,
                                })
                for edge in composer_edges:
                    candidates = composer_packages.get(edge["to"], [])
                    if len(candidates) == 1:
                        edge["to_version"] = candidates[0]["version"]
                        edge["to_source_reference"] = candidates[0]["source_reference"]
                        edge["to_dist_reference"] = candidates[0]["dist_reference"]
                        edge["resolution_status"] = "unique_locked_package_instance"
                    else:
                        edge["resolution_status"] = "ambiguous_or_unresolved_package_instance"
                    dependency_edges.append(edge)
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "composer", "status": "parse_error"})
        elif name == "pnpm-lock.yaml":
            dependency_files.append(path)
            # Parse pnpm v6/v9 package/snapshot blocks and importer descriptors
            # without guessing package identity from a bare name.
            try:
                section = ""
                current_locator = None
                current_name = None
                current_version = None
                current_integrity = None
                current_edge_group = None
                package_nodes: dict[str, dict[str, Any]] = {}
                pending_edges: list[dict[str, Any]] = []
                def flush_pnpm_node() -> None:
                    nonlocal current_locator, current_name, current_version, current_integrity, current_edge_group
                    if current_locator and current_name and current_version:
                        prior = package_nodes.get(current_locator, {})
                        package_nodes[current_locator] = {
                            "name": current_name, "version": current_version,
                            "integrity": current_integrity or prior.get("integrity"),
                        }
                    current_edge_group = None
                def parse_pnpm_locator(raw_key: str) -> tuple[str | None, str | None]:
                    original = raw_key.strip().strip("'").strip('"')
                    key = original.lstrip("/")
                    if original.startswith("/") and "@" not in key and "/" in key:
                        package_name, ver = key.rsplit("/", 1)
                        version_match = re.match(r"^([^(/]+)", ver)
                        return package_name, version_match.group(1) if version_match else None
                    if key.startswith("@") and "/" in key:
                        scope, tail = key.split("/", 1)
                        if "@" not in tail:
                            return None, None
                        pkg, ver = tail.split("@", 1)
                        package_name = scope + "/" + pkg
                    else:
                        if "@" not in key:
                            return None, None
                        package_name, ver = key.rsplit("@", 1)
                    version_match = re.match(r"^([^(/]+)", ver)
                    return package_name, version_match.group(1) if version_match else None
                for line in text.splitlines():
                    top = re.match(r"^(importers|packages|snapshots):\s*$", line)
                    if top:
                        flush_pnpm_node()
                        section = top.group(1)
                        current_locator = current_name = current_version = current_integrity = None
                        current_edge_group = None
                        continue
                    if section == "importers":
                        # Importer dependency descriptors resolve to exact package locators.
                        importer_match = re.match(r"^\s{4}([^:]+):\s*$", line)
                        if importer_match and importer_match.group(1) in {"dependencies", "devDependencies", "optionalDependencies"}:
                            current_edge_group = importer_match.group(1)
                            continue
                        dep_match = re.match(r"^\s{6}(['\"]?[^:'\"]+['\"]?):\s*$", line)
                        if dep_match and current_edge_group:
                            pending_edges.append({"ecosystem":"npm","from":"<workspace-importer>","to_descriptor":dep_match.group(1).strip("'\""),"kind":current_edge_group,"source_manifest":path})
                        resolved_match = re.match(r"^\s{8}version:\s*['\"]?([^'\"]+)", line)
                        if resolved_match and pending_edges and pending_edges[-1].get("to_locator") is None:
                            pending_edges[-1]["resolved_reference"] = resolved_match.group(1)
                        continue
                    if section not in {"packages", "snapshots"}:
                        continue
                    node_match = re.match(r"^\s{2}(['\"]?[^:'\"]+['\"]?):\s*$", line)
                    if node_match:
                        flush_pnpm_node()
                        current_locator = node_match.group(1).strip("'\"")
                        current_name, current_version = parse_pnpm_locator(current_locator)
                        current_integrity = None
                        current_edge_group = None
                        continue
                    if not current_locator:
                        continue
                    integrity_match = re.search(r"\bintegrity:\s*['\"]?([^\s,'\"]+)", line)
                    if integrity_match:
                        current_integrity = integrity_match.group(1)
                    edge_group_match = re.match(r"^\s{4}(dependencies|optionalDependencies|peerDependencies):\s*$", line)
                    if edge_group_match:
                        current_edge_group = edge_group_match.group(1)
                        continue
                    edge_match = re.match(r"^\s{6}(['\"]?[^:'\"]+['\"]?):\s*['\"]?([^'\"]+)['\"]?\s*$", line)
                    if edge_match and current_edge_group and current_name:
                        target_name = edge_match.group(1).strip("'\"")
                        requested = edge_match.group(2).strip()
                        pending_edges.append({
                            "ecosystem":"npm", "from":current_name,
                            "from_locator":current_locator, "from_version":current_version,
                            "to":target_name, "requested":requested,
                            "kind":current_edge_group, "source_manifest":path,
                        })
                flush_pnpm_node()
                locator_by_name_version = {
                    (node["name"], node["version"]): locator
                    for locator, node in package_nodes.items()
                }
                for locator, node in package_nodes.items():
                    add_dependency("npm", node["name"], node["version"], path,
                                   status="lockfile_pinned" if node["integrity"] else "lockfile_pinned_integrity_missing",
                                   integrity=node["integrity"])
                for edge in pending_edges:
                    resolved_ref = edge.get("resolved_reference") or edge.get("requested")
                    target_name = edge.get("to")
                    if not target_name:
                        descriptor = str(edge.get("to_descriptor") or "")
                        target_name = descriptor.rsplit("@", 1)[0] if descriptor.startswith("@") else descriptor.split("@", 1)[0]
                    candidates = [key for key in locator_by_name_version if key[0] == target_name]
                    if isinstance(resolved_ref, str):
                        version_hint = re.match(r"^([^(/]+)", resolved_ref.lstrip("/"))
                        if version_hint:
                            exact = [key for key in candidates if key[1] == version_hint.group(1)]
                            candidates = exact or candidates
                    if len(candidates) == 1:
                        edge["to_locator"] = locator_by_name_version[candidates[0]]
                        edge["to_version"] = candidates[0][1]
                    else:
                        edge["resolution_status"] = "ambiguous_or_unresolved_package_instance"
                    dependency_edges.append(edge)
                if not package_nodes:
                    dependencies.append({"manifest":path,"ecosystem":"npm","status":"pnpm_lockfile_no_package_entries"})
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "npm", "status": "parse_error"})
        elif name == "yarn.lock":
            dependency_files.append(path)
            try:
                descriptors: list[str] = []
                current_version = None
                current_integrity = None
                current_resolution = None
                current_name = None
                current_dependencies: list[tuple[str, str, str]] = []
                yarn_nodes: dict[tuple[str, str], dict[str, Any]] = {}
                yarn_edges: list[dict[str, Any]] = []
                dependency_section = False
                def yarn_descriptor_name(value: str) -> str | None:
                    descriptor = value.strip().strip('"').strip("'")
                    # Yarn classic: name@range; Berry: name@npm:range.
                    if descriptor.startswith("@"):
                        slash = descriptor.find("/")
                        at = descriptor.find("@", slash + 1)
                    else:
                        at = descriptor.find("@")
                    return descriptor[:at] if at > 0 else None
                def flush_yarn() -> None:
                    nonlocal descriptors, current_version, current_integrity, current_resolution, current_name, current_dependencies
                    if current_version and descriptors:
                        for descriptor in descriptors:
                            package_name = yarn_descriptor_name(descriptor)
                            if not package_name:
                                continue
                            locator = current_resolution or descriptor
                            node_key = (package_name, current_version)
                            yarn_nodes[node_key] = {
                                "locator": locator, "integrity": current_integrity,
                            }
                            add_dependency("npm", package_name, current_version, path,
                                           status="lockfile_pinned" if current_integrity else "lockfile_pinned_integrity_missing",
                                           integrity=current_integrity)
                            for dep_name, requested, kind in current_dependencies:
                                yarn_edges.append({
                                    "ecosystem":"npm", "from":package_name,
                                    "from_locator":locator, "from_version":current_version,
                                    "to":dep_name, "requested":requested,
                                    "kind":kind, "source_manifest":path,
                                })
                    descriptors = []
                    current_version = current_integrity = current_resolution = current_name = None
                    current_dependencies = []
                for line in text.splitlines():
                    if line and not line[0].isspace() and line.rstrip().endswith(":"):
                        flush_yarn()
                        header = line.rstrip()[:-1]
                        descriptors = [part.strip().strip('"').strip("'") for part in header.split(",")]
                        dependency_section = False
                        continue
                    version_match = re.match(r"^\s+version\s+['\"]?([^\s'\"]+)", line)
                    if version_match:
                        current_version = version_match.group(1)
                        continue
                    resolution_match = re.match(r"^\s+resolution:\s*['\"]?([^'\"]+)", line)
                    if resolution_match:
                        current_resolution = resolution_match.group(1)
                        continue
                    integrity_match = re.match(r"^\s+integrity\s+(.+)$", line)
                    if integrity_match:
                        current_integrity = integrity_match.group(1).strip().strip('"')
                        continue
                    if re.match(r"^\s{2}dependencies:\s*$", line):
                        dependency_section = True
                        continue
                    if dependency_section:
                        dependency_match = re.match(r"^\s{4}(['\"]?[^:'\"]+['\"]?):\s*['\"]?([^'\"]+)['\"]?\s*$", line)
                        if dependency_match:
                            current_dependencies.append((
                                dependency_match.group(1).strip("'\""),
                                dependency_match.group(2).strip(), "dependency",
                            ))
                            continue
                        if line and not line.startswith("    "):
                            dependency_section = False
                flush_yarn()
                for edge in yarn_edges:
                    candidates = [node for (pkg, _), node in yarn_nodes.items() if pkg == edge["to"]]
                    if len(candidates) == 1:
                        edge["to_locator"] = candidates[0]["locator"]
                    else:
                        edge["resolution_status"] = "ambiguous_or_unresolved_package_instance"
                    dependency_edges.append(edge)
                if not yarn_nodes:
                    dependencies.append({"manifest":path,"ecosystem":"npm","status":"yarn_lockfile_no_package_entries"})
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "npm", "status": "parse_error"})
        elif name in {"gemfile", "gemfile.lock"}:
            dependency_files.append(path)
            if name == "gemfile":
                dependencies.append({"manifest": path, "ecosystem": "rubygems", "status": "manifest_declared_requires_lockfile"})
                continue
            try:
                in_specs = False
                current_gem: str | None = None
                for line in text.splitlines():
                    if line.strip() == "specs:":
                        in_specs = True
                        current_gem = None
                        continue
                    if in_specs and line and not line.startswith("    ") and not line.startswith("  "):
                        in_specs = False
                        current_gem = None
                    if not in_specs:
                        continue
                    # Gemfile.lock encodes resolved gem dependencies as nested
                    # rows below each four-space package declaration.
                    package_match = re.match(r"^    ([A-Za-z0-9_.-]+) \(([^)]+)\)(?: .*)?$", line)
                    if package_match:
                        current_gem = package_match.group(1)
                        add_dependency("rubygems", current_gem, package_match.group(2), path, status="lockfile_pinned")
                        continue
                    edge_match = re.match(r"^      ([A-Za-z0-9_.-]+)(?: \(([^)]+)\))?", line)
                    if current_gem and edge_match:
                        requested = edge_match.group(2) or ""
                        dependency_edges.append({
                            "ecosystem": "rubygems", "from": current_gem,
                            "to": edge_match.group(1), "kind": "runtime_dependency",
                            "requested": requested,
                            "resolved_exact_version": requested[2:].strip() if requested.startswith("= ") else None,
                            "source_manifest": path,
                        })
                if not any(item.get("source_manifest") == path for item in dependencies):
                    dependencies.append({"manifest": path, "ecosystem": "rubygems", "status": "gemfile_lock_no_specs"})
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "rubygems", "status": "parse_error"})
        elif name == "go.mod":
            dependency_files.append(path)
            try:
                in_require = False
                for line in text.splitlines():
                    stripped = line.strip()
                    if re.match(r"^(replace|exclude|retract|toolchain|godebug)\b", stripped):
                        dependencies.append({
                            "manifest": path, "ecosystem": "go",
                            "status": "go_mod_directive_requires_module_graph_resolution",
                            "directive": stripped.split(maxsplit=1)[0],
                            "detail": stripped[:500],
                        })
                    if stripped.startswith("require ("):
                        in_require = True
                        continue
                    if in_require and stripped == ")":
                        in_require = False
                        continue
                    if stripped.startswith("require "):
                        stripped = stripped[len("require "):]
                    elif not in_require:
                        continue
                    match = re.match(r"^([^\s]+)\s+(v[0-9][^\s]+)", stripped)
                    if match:
                        dependencies.append({"ecosystem": "go", "name": match.group(1), "requested": match.group(2),
                                             "exact_version": None, "source_manifest": path,
                                             "status": "manifest_declared_requires_lockfile"})
            except Exception:
                dependencies.append({"manifest": path, "ecosystem": "go", "status": "parse_error"})
        elif name == "go.sum":
            dependency_files.append(path)
            for line in text.splitlines():
                fields = line.split()
                if len(fields) == 3 and not fields[1].endswith("/go.mod"):
                    add_dependency("go", fields[0], fields[1], path, status="lockfile_pinned", integrity=fields[2])

    for manifest_path, declared in npm_declared.items():
        lock_candidates = [
            candidate for candidate in npm_locked
            if PurePosixPath(candidate).parent == PurePosixPath(manifest_path).parent
        ]
        if not lock_candidates:
            dependencies.append({
                "manifest": manifest_path, "ecosystem": "npm",
                "status": "npm_lockfile_missing", "unresolved_direct_dependencies": sorted(declared),
            })
            continue
        locked = set().union(*(npm_locked[candidate] for candidate in lock_candidates))
        missing = sorted(declared - locked)
        if missing:
            dependencies.append({
                "manifest": manifest_path, "ecosystem": "npm",
                "status": "npm_lockfile_incomplete", "unresolved_direct_dependencies": missing,
            })

    # Match direct declarations to the same ecosystem's resolved lock entries.
    # A semver-looking manifest string alone is never treated as a reproducible pin.
    locked_versions: dict[tuple[str, str], list[str]] = {}
    for item in dependencies:
        ecosystem, package_name, version = item.get("ecosystem"), item.get("name"), item.get("exact_version")
        if item.get("status") == "lockfile_pinned" and isinstance(package_name, str) and isinstance(version, str):
            normalized = re.sub(r"[-_.]+", "-", package_name).lower()
            locked_versions.setdefault((str(ecosystem), normalized), []).append(version)
    for item in dependencies:
        if item.get("status") != "manifest_declared_requires_lockfile":
            continue
        ecosystem, package_name = item.get("ecosystem"), item.get("name")
        normalized = re.sub(r"[-_.]+", "-", package_name).lower() if isinstance(package_name, str) else ""
        matches = locked_versions.get((str(ecosystem), normalized), [])
        if matches and len(set(matches)) == 1:
            item["exact_version"] = matches[0]
            item["status"] = "locked_declaration_matched"
        else:
            item["status"] = "lockfile_declaration_unresolved"
    exact = sum(1 for item in dependencies if item.get("exact_version"))
    resolved_statuses = {"lockfile_pinned", "locked_declaration_matched"}
    unresolved = sum(1 for item in dependencies if not item.get("exact_version") or item.get("status") not in resolved_statuses)
    return {
        "license_files": license_files,
        "manifest_files": sorted(set(manifest_files)),
        "dependency_manifests": sorted(set(dependency_files)),
        "dependency_file_evidence": sorted(dependency_file_evidence, key=lambda item: item["path"]),
        "dependency_files_sha256_complete": bool(dependency_file_evidence) and all(SHA64.fullmatch(str(item.get("sha256") or "")) for item in dependency_file_evidence),
        "dependencies": dependencies,
        "dependency_edges": dependency_edges,
        "dependency_edge_count": len(dependency_edges),
        "dependency_count": len(dependencies),
        "exact_version_count": exact,
        "unresolved_dependency_count": unresolved,
        "dependency_lockfiles_present": any(PurePosixPath(path).name.lower() in {"package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "requirements.lock", "poetry.lock", "uv.lock", "pipfile.lock", "cargo.lock", "composer.lock"} for path in dependency_files),
        "license_evidence_status": "source_license_files_present" if license_files else "source_license_files_missing",
        "notice_files_present": any(PurePosixPath(item["path"]).name.lower().startswith("notice") for item in license_files),
        "warning": "Dependency edges are extracted only where the source lockfile encodes them. Missing edges, unsupported lockfile syntax, and unresolved package identity remain review findings; package inventory alone is not a complete build graph.",
    }


SPDX_COMMON_IDS = {
    "MIT","Apache-2.0","BSD-2-Clause","BSD-3-Clause","ISC","MPL-2.0",
    "LGPL-2.1-only","LGPL-3.0-only","GPL-2.0-only","GPL-3.0-only",
    "AGPL-3.0-only","CC-BY-4.0","CC0-1.0","Unlicense","Zlib","0BSD",
    "Artistic-2.0","BSL-1.0","EPL-2.0","OFL-1.1","PostgreSQL",
}


def _spdx_expression(value: Any) -> str:
    if not isinstance(value, str):
        return "NOASSERTION"
    raw = value.strip()
    if raw in SPDX_COMMON_IDS:
        return raw
    parts = re.split(r"\s+(AND|OR)\s+", raw)
    if len(parts) >= 3 and len(parts) % 2 == 1:
        ids = parts[::2]
        operators = parts[1::2]
        if all(item in SPDX_COMMON_IDS for item in ids) and all(op in {"AND","OR"} for op in operators):
            return raw
    return "NOASSERTION"


async def _resolve_exact_dependency_licenses(http: Any, dependencies: list[dict[str, Any]]) -> dict[str, Any]:
    semaphore = asyncio.Semaphore(8)
    async def resolve(item: dict[str, Any]) -> dict[str, Any]:
        ecosystem = item.get("ecosystem")
        name = item.get("name")
        version = item.get("exact_version")
        if not isinstance(name, str) or not isinstance(version, str):
            return {**item, "registry_metadata_status": "not_exactly_pinned", "license_declared": "NOASSERTION"}
        if ecosystem == "npm":
            url = "https://registry.npmjs.org/" + quote(name, safe="@") + "/" + quote(version, safe="")
        elif ecosystem == "pypi":
            url = "https://pypi.org/pypi/" + quote(name, safe="") + "/" + quote(version, safe="") + "/json"
        elif ecosystem == "cargo":
            url = "https://crates.io/api/v1/crates/" + quote(name, safe="") + "/" + quote(version, safe="")
        else:
            return {**item, "registry_metadata_status": "registry_not_supported", "license_declared": "NOASSERTION"}
        async with semaphore:
            try:
                response = await http.get(url, headers={"Accept":"application/json","User-Agent":"MoreAI-Skill-SBOM/1.0"}, timeout=12.0, follow_redirects=False)
                if response.status_code != 200:
                    return {**item, "registry_metadata_status": "not_found_or_unavailable", "license_declared": "NOASSERTION"}
                payload = response.json()
                license_value = None
                if ecosystem == "npm":
                    license_value = payload.get("license")
                    if isinstance(license_value, dict):
                        license_value = license_value.get("type")
                elif ecosystem == "pypi":
                    info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
                    license_value = info.get("license")
                    if not license_value:
                        classifiers = info.get("classifiers") or []
                        license_value = "; ".join(value.split("::")[-1].strip() for value in classifiers if "License ::" in value) or None
                elif ecosystem == "cargo":
                    version_data = payload.get("version") if isinstance(payload.get("version"), dict) else {}
                    license_value = version_data.get("license")
                return {
                    **item, "registry_metadata_status": "resolved",
                    "license_declared": _spdx_expression(license_value),
                    "license_declared_raw": str(license_value)[:240] if license_value else None,
                    "registry_metadata_url": url,
                }
            except Exception:
                return {**item, "registry_metadata_status": "fetch_failed", "license_declared": "NOASSERTION"}
    bounded = dependencies[:100]
    resolved = await asyncio.gather(*(resolve(item) for item in bounded))
    if len(dependencies) > len(bounded):
        resolved.extend({**item, "registry_metadata_status":"resolution_limit_exceeded","license_declared":"NOASSERTION"} for item in dependencies[len(bounded):])
    exact = [item for item in resolved if item.get("exact_version")]
    return {
        "packages": resolved,
        "exact_version_count": len(exact),
        "registry_metadata_resolved_count": sum(1 for item in exact if item.get("registry_metadata_status") == "resolved"),
        "license_assertion_count": sum(1 for item in exact if item.get("license_declared") != "NOASSERTION"),
        "unresolved_count": sum(1 for item in resolved if item.get("registry_metadata_status") != "resolved"),
        "note": "Registry metadata is version-specific evidence only. It does not prove license compatibility, source provenance, transitive completeness or asset rights; human review remains mandatory.",
    }


def _spdx_skill_sbom(
    skill: dict[str, Any], packages: list[dict[str, Any]], files: list[dict[str, Any]],
) -> dict[str, Any]:
    spdx_packages = []
    relationships = []
    for index, item in enumerate(packages, start=1):
        name = str(item.get("name") or "unknown")
        version = str(item.get("exact_version") or item.get("requested") or "UNKNOWN")
        package_id = f"SPDXRef-Dependency-{index}"
        spdx_packages.append({
            "name": name, "SPDXID": package_id,
            "versionInfo": version,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": str(item.get("license_declared") or "NOASSERTION"),
            "copyrightText": "NOASSERTION",
            "externalRefs": [],
            "comment": f"{item.get('ecosystem')} · {item.get('registry_metadata_status')} · {item.get('source_manifest')}",
        })
        relationships.append({"spdxElementId":"SPDXRef-DOCUMENT","relationshipType":"DESCRIBES","relatedSpdxElement":package_id})
    spdx_files = []
    for index, item in enumerate(files, start=1):
        path = str(item.get("relative_path") or "")
        digest = str(item.get("content_sha256") or "")
        if not path or not re.fullmatch(r"[0-9a-f]{64}", digest):
            continue
        file_id = f"SPDXRef-File-{index}"
        spdx_files.append({
            "fileName": "./" + path,
            "SPDXID": file_id,
            "checksums": [{"algorithm":"SHA256","checksumValue":digest}],
            "licenseConcluded": "NOASSERTION",
            "licenseInfoInFiles": ["NOASSERTION"],
            "licenseComments": "File-level license and asset rights require explicit review.",
            "copyrightText": "NOASSERTION",
            "fileTypes": ["SOURCE"] if str(item.get("media_type") or "").startswith(("text/","application/json","application/javascript")) else ["BINARY"],
        })
        relationships.append({"spdxElementId":"SPDXRef-DOCUMENT","relationshipType":"DESCRIBES","relatedSpdxElement":file_id})
    return {
        "spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT", "name": f"MoreAI Skill {skill.get('slug','unknown')} SBOM",
        "documentNamespace": f"https://moreai.invalid/sbom/skills/{skill.get('id','unknown')}/{skill.get('content_sha256','unknown')}",
        "creationInfo": {"creators":["Tool: MoreAI-Skill-Registry"],"created":datetime.now(timezone.utc).isoformat()},
        "packages": spdx_packages, "files": spdx_files, "relationships": relationships,
        "comment": "Inventory is bounded to ingested pinned source files and discovered dependency manifests; it is not a complete build attestation or legal opinion.",
    }


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
    source_inventory = _source_review_inventory(files)
    registry_inventory = await _resolve_exact_dependency_licenses(request.app.state.http, source_inventory["dependencies"])
    sbom = _spdx_skill_sbom(skill, registry_inventory["packages"], files)
    source_inventory["registry_resolution"] = {
        "exact_version_count": registry_inventory["exact_version_count"],
        "registry_metadata_resolved_count": registry_inventory["registry_metadata_resolved_count"],
        "license_assertion_count": registry_inventory["license_assertion_count"],
        "unresolved_count": registry_inventory["unresolved_count"],
        "note": registry_inventory["note"],
    }
    source_inventory["sbom"] = sbom
    source_inventory["dependencies"] = registry_inventory["packages"]
    manifest = skill.get("manifest") if isinstance(skill.get("manifest"), dict) else {}
    if not manifest or not source_inventory["manifest_files"]:
        findings.append("A source-controlled SKILL.md or package manifest is required; user-entered metadata alone is not a skill manifest.")
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
    if not skill.get("license_evidence") or not source_inventory["license_files"]:
        findings.append("Repository LICENSE/NOTICE evidence is incomplete; legal approval is required.")
    if source_inventory.get("unresolved_dependency_count", 0):
        findings.append("Dependency inventory is incomplete: direct declarations are not matched to exact lockfile entries, or a lockfile parser/source is unsupported.")
    if registry_inventory["unresolved_count"]:
        findings.append("One or more exact dependency versions lack authoritative registry metadata; SPDX licenseDeclared remains NOASSERTION.")
    if any(item.get("license_declared") == "NOASSERTION" for item in registry_inventory["packages"]):
        findings.append("One or more dependency license declarations are unknown or not a recognized SPDX expression.")
    if any(item.get("registry_metadata_status") == "range_or_unpinned" for item in registry_inventory["packages"]):
        findings.append("One or more dependencies are not pinned to an exact version; a reproducible dependency lock is required.")
    if any(item.get("ecosystem") == "npm" and item.get("status") == "lockfile_pinned" and not item.get("integrity") for item in registry_inventory["packages"]):
        findings.append("One or more npm lockfile entries omit package integrity hashes; provenance evidence is incomplete.")
    if any(item.get("binary_content_base64") for item in files):
        findings.append("Binary assets are inventoried by SHA-256, but provenance, redistribution rights and asset-specific licenses require reviewer evidence.")

    if not skill.get("source_path") or ".." in str(skill["source_path"]).split("/"):
        findings.append("Unsafe source path.")
    if not skill.get("source_blob_sha") or not skill.get("content_sha256"):
        findings.append("Immutable source/content hashes are required.")
    if not isinstance(skill.get("requested_permissions"), list) or any(x not in PERMISSION_KEYS for x in skill["requested_permissions"]):
        findings.append("Requested permissions contain unsupported capabilities.")
    # Static source inventory is not malware scanning, registry license reconciliation or rights clearance.
    status = "review_required" if findings else "validated"
    license_status = "review_required" if findings else "unverified"
    await repo.update("moreai_skill_packages", {"id": f"eq.{skill_id}", "owner_user_id": f"eq.{user['id']}"}, {
        "validation_status": status, "license_status": license_status,
        "validation_report": {"findings": findings, "checked_at": datetime.now(timezone.utc).isoformat(), "scope": "pinned_source_static_inventory", "source_inventory": source_inventory},
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


@router.post("/{skill_id}/permissions/revoke")
async def revoke_skill_permissions(
    skill_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Let an installation owner close its own execution gate immediately."""
    repo = repository(request)
    rows = await repo.select("moreai_skill_installs", {
        "owner_user_id": f"eq.{user['id']}", "skill_package_id": f"eq.{skill_id}",
        "select": "id,permission_status", "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "skill_installation_not_found")
    updated = await repo.update("moreai_skill_installs", {
        "id": f"eq.{rows[0]['id']}", "owner_user_id": f"eq.{user['id']}",
    }, {
        "execution_enabled": False,
        "permission_status": "revoked",
        "permission_request": [],
        "granted_permissions": [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    if not updated:
        raise HTTPException(409, "skill_permission_revocation_conflict")
    return updated[0]


import base64
import hashlib
import mimetypes
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


PINNED_SKILL_LICENSES = {
    ("smixs", "visual-skills"): {
        "license_id": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "license_evidence": "Pinned repository root LICENSE and NOTICE are present. Individual asset, creator and trademark rights remain unverified; human review is required.",
    },
    ("scenario-labs", "skills"): {
        "license_id": "MIT",
        "license_url": "https://github.com/scenario-labs/skills/blob/94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9/LICENSE",
        "license_evidence": "Pinned repository root LICENSE is present. Nested licenses, assets, scripts and transitive dependencies remain unverified; human review is required.",
    },
}


class PinnedSkillCatalogImportRequest(BaseModel):
    source_repository: str = Field(min_length=3, max_length=255)
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_path: str = Field(min_length=1, max_length=512)


@router.get("/catalog")
async def list_pinned_skill_catalog(
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    http = request.app.state.http
    repo = repository(request)
    imported = await repo.select("moreai_skill_packages", {
        "owner_user_id": f"eq.{user['id']}",
        "select": "source_repository,source_commit,source_path",
        "limit": "500",
    })
    imported_keys = {
        (str(item.get("source_repository")), str(item.get("source_commit")), str(item.get("source_path")))
        for item in imported
    }
    items: list[dict[str, Any]] = []
    for (source_owner, source_repo), commits in PINNED_SKILL_SOURCES.items():
        commit = sorted(commits)[0]
        url = f"https://api.github.com/repos/{source_owner}/{source_repo}/git/trees/{commit}?recursive=1"
        response = await http.get(
            url,
            headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
            timeout=20.0,
            follow_redirects=False,
        )
        if response.status_code != 200:
            raise HTTPException(502, "pinned_skill_catalog_source_unavailable")
        payload = response.json()
        if not isinstance(payload, dict):
            raise HTTPException(502, "pinned_skill_catalog_payload_invalid")
        tree = payload.get("tree")
        if not isinstance(tree, list) or payload.get("truncated") is True:
            raise HTTPException(502, "pinned_skill_catalog_tree_incomplete")
        license_info = PINNED_SKILL_LICENSES[(source_owner, source_repo)]
        for node in tree:
            path = node.get("path") if isinstance(node, dict) else None
            blob_sha = node.get("sha") if isinstance(node, dict) else None
            if (
                not isinstance(path, str) or not path.lower().endswith("/skill.md")
                or node.get("type") != "blob" or node.get("mode") == "120000"
            ):
                continue
            if source_repo == "visual-skills" and path not in {"image/SKILL.md", "video/SKILL.md"}:
                continue
            if source_repo == "skills" and not path.startswith("skills/"):
                continue
            if not isinstance(blob_sha, str) or not SHA40.fullmatch(blob_sha):
                continue
            parent = str(PurePosixPath(path).parent)
            catalog_slug = re.sub(r"[^a-z0-9._-]+", "-", f"{source_repo}-{parent}".lower().replace("/", "-")).strip("-")[:120]
            leaf = PurePosixPath(path).parent.name
            items.append({
                "slug": catalog_slug,
                "name": leaf.replace("-", " ").replace("_", " ").title(),
                "description": "Pinned upstream skill entrypoint; source review and publication approval are required.",
                "source_repository": f"{source_owner}/{source_repo}",
                "source_ref": f"pinned:{commit[:12]}",
                "source_commit": commit,
                "source_path": path,
                "source_blob_sha": blob_sha,
                "version": f"pinned-{commit[:12]}",
                "license_id": license_info["license_id"],
                "license_url": license_info["license_url"],
                "imported": (f"{source_owner}/{source_repo}", commit, path) in imported_keys,
            })
    items.sort(key=lambda item: (item["source_repository"], item["source_path"]))
    return {"items": items, "count": len(items), "source_status": "pinned_tree_inventory_only"}


@router.post("/catalog/import", status_code=201)
async def import_pinned_skill_from_catalog(
    body: PinnedSkillCatalogImportRequest,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    parts = body.source_repository.split("/")
    if len(parts) != 2 or body.source_commit not in PINNED_SKILL_SOURCES.get((parts[0], parts[1]), set()):
        raise HTTPException(403, "skill_source_repository_or_commit_not_pinned")
    source_path = _safe_skill_path(body.source_path)
    if parts[1] == "visual-skills" and source_path not in {"image/SKILL.md", "video/SKILL.md"}:
        raise HTTPException(403, "visual_skill_entrypoint_not_allowlisted")
    if parts[1] == "skills" and not (source_path.startswith("skills/") and source_path.endswith("/SKILL.md")):
        raise HTTPException(403, "scenario_skill_entrypoint_not_allowlisted")

    repo = repository(request)
    existing = await repo.select("moreai_skill_packages", {
        "owner_user_id": f"eq.{user['id']}",
        "source_repository": f"eq.{body.source_repository}",
        "source_commit": f"eq.{body.source_commit}",
        "source_path": f"eq.{source_path}",
        "select": "id",
        "limit": "1",
    })
    if existing:
        raise HTTPException(409, "skill_source_already_imported")

    url = (
        f"https://api.github.com/repos/{parts[0]}/{parts[1]}/contents/"
        f"{quote(source_path, safe='/')}?ref={body.source_commit}"
    )
    response = await request.app.state.http.get(
        url,
        headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        timeout=15.0,
        follow_redirects=False,
    )
    if response.status_code != 200:
        raise HTTPException(502, "pinned_skill_entrypoint_fetch_failed")
    item = response.json()
    if not isinstance(item, dict) or item.get("type") != "file" or item.get("encoding") != "base64":
        raise HTTPException(502, "pinned_skill_entrypoint_payload_invalid")
    try:
        raw = base64.b64decode("".join(str(item.get("content") or "").split()), validate=True)
        text_content = raw.decode("utf-8", errors="strict")
    except Exception as exc:
        raise HTTPException(502, "pinned_skill_entrypoint_content_invalid") from exc
    git_blob_sha = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if item.get("sha") != git_blob_sha:
        raise HTTPException(409, "pinned_skill_entrypoint_blob_hash_mismatch")

    frontmatter = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text_content, re.DOTALL)
    metadata_text = frontmatter.group(1) if frontmatter else ""
    name_match = re.search(r"(?m)^name:\s*[\"']?([^\"'\n]+)", metadata_text)
    description_match = re.search(r"(?m)^description:\s*[\"']?([^\"'\n]+)", metadata_text)
    parent = str(PurePosixPath(source_path).parent)
    slug = re.sub(r"[^a-z0-9._-]+", "-", f"{parts[1]}-{parent}".lower().replace("/", "-")).strip("-")[:120]
    license_info = PINNED_SKILL_LICENSES[(parts[0], parts[1])]
    name = name_match.group(1).strip() if name_match else PurePosixPath(source_path).parent.name.replace("-", " ").title()
    description = description_match.group(1).strip() if description_match else "Pinned upstream skill; human source and license review required."
    row = {
        "owner_user_id": user["id"], "slug": slug, "name": name[:160],
        "description": description[:2000], "source_repository": body.source_repository,
        "source_ref": f"pinned:{body.source_commit[:12]}", "source_commit": body.source_commit,
        "source_path": source_path, "source_blob_sha": git_blob_sha,
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "version": f"pinned-{body.source_commit[:12]}",
        "license_id": license_info["license_id"], "license_url": license_info["license_url"],
        "license_evidence": license_info["license_evidence"],
        "manifest": {
            "name": name, "version": f"pinned-{body.source_commit[:12]}",
            "source_catalog": "pinned_visual_scenario_skills",
            "source_entrypoint": source_path, "source_review_required": True,
        },
        "requested_permissions": [], "license_status": "unverified",
        "validation_status": "pending",
        "validation_report": {"findings": [
            "Only the pinned SKILL.md entrypoint was fetched; recursive references, scripts, assets and dependency manifests are not yet ingested.",
            "Repository-level license metadata is not an approval. Nested license, attribution, asset and trademark rights require human review.",
            "No permissions were requested or granted; publication and execution remain disabled.",
        ]},
        "publication_status": "private",
    }
    return await repo.insert("moreai_skill_packages", row)


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
    source_root = str(PurePosixPath(root_path).parent)
    queue = [root_path] + ([source_root] if source_root != "." else [])
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    total_bytes = 0
    http = request.app.state.http
    # Repository-level LICENSE/NOTICE files govern many nested skill directories.
    root_listing_url = f"https://api.github.com/repos/{parts[0]}/{parts[1]}/contents?ref={skill['source_commit']}"
    root_listing = await http.get(root_listing_url, headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}, timeout=15.0, follow_redirects=False)
    if root_listing.status_code != 200:
        raise HTTPException(502, "skill_repository_root_listing_failed")
    root_items = root_listing.json()
    if not isinstance(root_items, list):
        raise HTTPException(502, "skill_repository_root_listing_invalid")
    for root_item in root_items:
        if not isinstance(root_item, dict) or root_item.get("type") != "file":
            continue
        root_name = str(root_item.get("name") or "").lower()
        if root_name.startswith(("license","licence","copying","notice","third_party")):
            root_file = _safe_skill_path(str(root_item.get("path") or ""))
            if root_file not in queue:
                queue.append(root_file)
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
        if isinstance(item, list):
            # Directory traversal captures nested scripts, manifests, licenses,
            # NOTICE files and referenced assets at the same immutable commit.
            for child in item:
                if not isinstance(child, dict) or child.get("type") not in {"file", "dir"}:
                    raise HTTPException(422, "skill_source_symlink_or_special_file_rejected")
                child_path = _safe_skill_path(str(child.get("path") or ""))
                if child_path not in seen and child_path not in queue:
                    queue.append(child_path)
            continue
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
        git_sha = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        sha_api = item.get("sha")
        if not isinstance(sha_api, str) or git_sha != sha_api:
            raise HTTPException(409, "skill_git_blob_hash_mismatch")
        digest = hashlib.sha256(content).hexdigest()
        if relative == root_path and (git_sha != skill["source_blob_sha"] or digest != skill["content_sha256"]):
            raise HTTPException(409, "skill_root_provenance_hash_mismatch")
        media_type = str(item.get("content_type") or mimetypes.guess_type(relative)[0] or "application/octet-stream")[:120]
        source_name = PurePosixPath(relative).name.lower()
        is_text = media_type.startswith("text/") or source_name.startswith(("license", "licence", "copying", "notice", "readme", "third_party")) or relative.lower().endswith((".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".js", ".ts", ".svg", ".lock", ".mod"))
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
    validation_report = {
        "scope": "pinned_github_content_integrity",
        "file_count": len(records), "total_bytes": total_bytes,
        "files": [{"path": x["relative_path"], "git_blob_sha": x["git_blob_sha"], "sha256": x["content_sha256"], "bytes": x["byte_size"]} for x in records],
        "findings": [
            "Files, nested directories, local references, manifests, scripts, licenses, NOTICE files and assets under the skill source directory were fetched at the pinned commit and Git blob SHA verified.",
            "Dependency resolution, script safety and asset rights still require separate review.",
        ],
    }
    try:
        stored = await repo.rpc("moreai_ingest_skill_source", {
            "p_skill_id": str(skill_id),
            "p_owner_user_id": str(user["id"]),
            "p_files": records,
            "p_validation_report": validation_report,
        })
    except Exception as exc:
        raise HTTPException(409, "skill_source_atomic_persistence_failed") from exc
    if not isinstance(stored, dict) or stored.get("integrity") != "verified":
        raise HTTPException(409, "skill_source_atomic_persistence_failed")
    return {"skill_id": str(skill_id), "source_commit": skill["source_commit"], "file_count": len(records), "total_bytes": total_bytes, "integrity": "verified", "execution_enabled": False}
