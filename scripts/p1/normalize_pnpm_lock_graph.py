#!/usr/bin/env python3
"""Build a reproducible pnpm v9 dependency graph and exact-version npm license evidence.

This is an offline-safe audit utility: graph extraction reads pinned lockfiles only.
Registry metadata is fetched only when --registry-metadata is supplied. It never
installs packages, runs package scripts, or executes source from audited repos.
Requires Python 3.11+ and PyYAML (see scripts/p1/requirements.txt).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("Missing audit dependency PyYAML. Install scripts/p1/requirements.txt in an isolated audit environment.") from exc


def parse_package_key(key: str) -> tuple[str, str] | None:
    raw = key.lstrip("/")
    if raw.startswith("@"):
        slash = raw.find("/")
        split = raw.find("@", slash + 1) if slash >= 0 else -1
    else:
        split = raw.find("@")
    if split <= 0:
        return None
    name, version_context = raw[:split], raw[split + 1:]
    version = version_context.split("(", 1)[0]
    if not name or not version:
        return None
    return name, version


def dependency_version(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("version")
    if not isinstance(value, str) or not value:
        return None
    if value.startswith(("link:", "workspace:", "file:", "patch:", "catalog:")):
        return None
    if value.startswith("npm:"):
        # Alias coordinates are retained unresolved rather than guessed.
        return None
    return value.lstrip("/")


def load_lock(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("lockfileVersion") not in ("9.0", 9, 9.0):
        raise ValueError(f"{path}: expected pnpm lockfile v9")
    for section in ("importers", "packages", "snapshots"):
        if not isinstance(data.get(section), dict):
            raise ValueError(f"{path}: missing mapping section {section}")
    return data


def build_rows(lock: dict[str, Any], source: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    packages: dict[tuple[str, str], list[str]] = {}
    package_keys: set[str] = set()
    package_rows: list[dict[str, str]] = []
    for key, meta in lock["packages"].items():
        parsed = parse_package_key(str(key))
        if not parsed:
            package_rows.append({"source": source, "package_key": str(key), "name": "", "version": "", "integrity": "", "resolution": "UNPARSED_PACKAGE_KEY"})
            continue
        name, version = parsed
        package_keys.add(str(key).lstrip("/"))
        packages.setdefault((name, version), []).append(str(key))
        integrity = ""
        if isinstance(meta, dict):
            integrity = str(meta.get("resolution", {}).get("integrity", "")) if isinstance(meta.get("resolution"), dict) else ""
        package_rows.append({
            "source": source, "package_key": str(key), "name": name, "version": version,
            "integrity": integrity, "resolution": "EXACT_LOCK_COORDINATE" if integrity else "LOCKED_WITHOUT_INTEGRITY",
        })

    edges: list[dict[str, str]] = []
    def add_edge(parent_type: str, parent: str, dep_name: str, raw_value: Any, relation: str) -> None:
        resolved = dependency_version(raw_value)
        target_name = dep_name
        target_version = resolved
        is_alias = False
        alias_match = re.match(r"^(@[^/]+/[^@]+|[^@]+)@(.+)$", resolved) if resolved else None
        if alias_match:
            target_name, target_version = alias_match.group(1), alias_match.group(2)
            is_alias = target_name != dep_name
        exact_key = f"{target_name}@{target_version}" if target_version else ""
        if exact_key and exact_key in package_keys:
            matches = ["/" + exact_key]
        else:
            base_version = target_version.split("(", 1)[0] if target_version else ""
            matches = packages.get((target_name, base_version), []) if base_version else []
        state = ("RESOLVED_ALIAS" if is_alias else "RESOLVED_EXACT") if len(matches) == 1 else ("AMBIGUOUS_PEER_CONTEXT" if len(matches) > 1 else "UNRESOLVED_OR_NON_REGISTRY")
        edges.append({
            "source": source, "parent_type": parent_type, "parent": parent,
            "dependency_name": dep_name, "raw_resolution": json.dumps(raw_value, sort_keys=True),
            "resolved_package_key": matches[0] if len(matches) == 1 else "",
            "resolution_status": state, "candidate_count": str(len(matches)), "relation": relation,
        })

    for importer, data in lock["importers"].items():
        if not isinstance(data, dict):
            continue
        for group in ("dependencies", "devDependencies", "optionalDependencies"):
            for name, value in (data.get(group) or {}).items():
                add_edge("importer", str(importer), str(name), value, group)

    for package_key, data in lock["packages"].items():
        if not isinstance(data, dict):
            continue
        peer_meta = data.get("peerDependenciesMeta") or {}
        for name, version_range in (data.get("peerDependencies") or {}).items():
            optional = bool((peer_meta.get(name) or {}).get("optional", False))
            edges.append({
                "source": source, "parent_type": "package", "parent": str(package_key),
                "dependency_name": str(name), "raw_resolution": str(version_range),
                "resolved_package_key": "", "resolution_status": "OPTIONAL_PEER_CONSTRAINT" if optional else "PEER_RANGE_CONSTRAINT",
                "candidate_count": "0", "relation": "peerDependencies",
            })

    for snapshot_key, data in lock["snapshots"].items():
        if not isinstance(data, dict):
            continue
        for group in ("dependencies", "optionalDependencies"):
            for name, value in (data.get(group) or {}).items():
                add_edge("snapshot", str(snapshot_key), str(name), value, group)
        for name in data.get("transitivePeerDependencies") or []:
            edges.append({
                "source": source, "parent_type": "snapshot", "parent": str(snapshot_key),
                "dependency_name": str(name), "raw_resolution": "",
                "resolved_package_key": "", "resolution_status": "TRANSITIVE_PEER_CONTEXT",
                "candidate_count": "0", "relation": "transitivePeerDependencies",
            })
    return package_rows, edges


def registry_license(name: str, version: str, timeout: int) -> dict[str, str]:
    encoded = urllib.parse.quote(name, safe="@")
    url = f"https://registry.npmjs.org/{encoded}/{urllib.parse.quote(version, safe='')}"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.npm.install-v1+json", "User-Agent": "MoreAI-P1-License-Audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
            license_value = payload.get("license")
            if isinstance(license_value, dict):
                license_value = license_value.get("type")
            return {
                "registry_status": "FOUND",
                "registry_license": str(license_value or "NOASSERTION"),
                "registry_version": str(payload.get("version", "")),
                "registry_tarball": str((payload.get("dist") or {}).get("tarball", "")),
                "registry_url": url,
            }
    except urllib.error.HTTPError as exc:
        return {"registry_status": f"HTTP_{exc.code}", "registry_license": "NOASSERTION", "registry_version": "", "registry_tarball": "", "registry_url": url}
    except Exception as exc:
        return {"registry_status": f"ERROR_{type(exc).__name__}", "registry_license": "NOASSERTION", "registry_version": "", "registry_tarball": "", "registry_url": url}


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", required=True, metavar="NAME=LOCKFILE")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--registry-metadata", action="store_true", help="query npm registry exact package/version metadata")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--delay", type=float, default=0.15, help="seconds between registry requests")
    args = parser.parse_args()

    all_packages: list[dict[str, str]] = []
    all_edges: list[dict[str, str]] = []
    for source_arg in args.source:
        if "=" not in source_arg:
            parser.error("--source must be NAME=LOCKFILE")
        source, filename = source_arg.split("=", 1)
        package_rows, edges = build_rows(load_lock(Path(filename)), source)
        all_packages.extend(package_rows)
        all_edges.extend(edges)

    if args.registry_metadata:
        cache: dict[tuple[str, str], dict[str, str]] = {}
        for row in all_packages:
            if not row.get("name") or not row.get("version"):
                continue
            key = (row["name"], row["version"])
            if key not in cache:
                cache[key] = registry_license(*key, args.timeout)
                time.sleep(max(0.0, args.delay))
            row.update(cache[key])
            row["license_evidence"] = "REGISTRY_EXACT_VERSION" if cache[key]["registry_status"] == "FOUND" and cache[key]["registry_license"] != "NOASSERTION" else "NOASSERTION_REQUIRES_ARTIFACT_NOTICE_REVIEW"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "pnpm-packages.csv", all_packages)
    write_csv(args.out_dir / "pnpm-dependency-edges.csv", all_edges)
    summary = {
        "sources": sorted({row["source"] for row in all_packages}),
        "package_records": len(all_packages),
        "dependency_edges": len(all_edges),
        "resolved_exact_edges": sum(row["resolution_status"] == "RESOLVED_EXACT" for row in all_edges),
        "unresolved_or_non_registry_edges": sum(row["resolution_status"] == "UNRESOLVED_OR_NON_REGISTRY" for row in all_edges),
        "ambiguous_peer_context_edges": sum(row["resolution_status"] == "AMBIGUOUS_PEER_CONTEXT" for row in all_edges),
        "registry_metadata_requested": args.registry_metadata,
        "warning": "Graph edge statuses are conservative. Peer-context, aliases, workspace and non-registry protocols remain explicit; never infer licenses from package names.",
    }
    (args.out_dir / "pnpm-audit-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
