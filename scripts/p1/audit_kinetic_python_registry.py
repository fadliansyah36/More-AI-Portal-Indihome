#!/usr/bin/env python3
"""Read-only PyPI registry metadata and locked-wheel hash audit for Kinetic Music Video.

No package is downloaded, installed, imported, or executed. Only PyPI JSON metadata is fetched.
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
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCKS = {
    "linux-x86_64": ROOT / "skills/scenario-kinetic-music-video/assets/python/linux-x86_64.txt",
    "macos-arm64": ROOT / "skills/scenario-kinetic-music-video/assets/python/macos-arm64.txt",
}
OUT = ROOT / "docs/implementation/p1-kinetic-python-registry-evidence"


def parse_lock(path: Path, platform: str) -> list[dict]:
    rows: list[dict] = []
    current: dict | None = None
    via_mode = False
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\\s\\\\;]+)\\s*\\\\?$", line)
        if match:
            current = {
                "name": match.group(1).lower().replace("_", "-"),
                "version": match.group(2),
                "platform": platform,
                "hashes": [],
                "via": [],
            }
            rows.append(current)
            via_mode = False
            continue
        if current is None:
            continue
        hash_match = re.search(r"--hash=sha256:([a-f0-9]{64})", line)
        if hash_match:
            current["hashes"].append(hash_match.group(1))
            via_mode = False
            continue
        if re.match(r"^\\s+# via\\s*$", line):
            via_mode = True
            continue
        via_match = re.match(r"^\\s+# via (.+)$", line)
        if via_match:
            current["via"].append(via_match.group(1).strip())
            via_mode = False
            continue
        continuation = re.match(r"^\\s+#\\s{2,}(.+)$", line)
        if continuation and via_mode:
            current["via"].append(continuation.group(1).strip())
            continue
        if line.strip() and not line.lstrip().startswith("#"):
            via_mode = False
    return rows


def fetch_metadata(name: str, version: str) -> tuple[dict | None, str]:
    encoded = urllib.parse.quote(name, safe="")
    url = f"https://pypi.org/pypi/{encoded}/{urllib.parse.quote(version, safe='')}/json"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MoreAI-P1-Static-Dependency-Audit/1.0", "Accept": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return json.loads(response.read().decode("utf-8")), "HTTP_200"
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None, "HTTP_404"
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                return None, f"HTTP_{exc.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == 3:
                return None, f"FETCH_ERROR:{type(exc).__name__}"
        time.sleep(1 + attempt * 2)
    return None, "FETCH_ERROR"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    packages: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"platforms": set(), "hashes": set(), "via": set(), "source_files": set()}
    )
    package_rows = []
    for platform, lock_path in LOCKS.items():
        if not lock_path.is_file():
            print(f"Missing lockfile: {lock_path}", file=sys.stderr)
            return 2
        for row in parse_lock(lock_path, platform):
            key = (row["name"], row["version"])
            record = packages[key]
            record["platforms"].add(platform)
            record["hashes"].update(row["hashes"])
            record["via"].update(row["via"])
            record["source_files"].add(lock_path.relative_to(ROOT).as_posix())

    args.output.mkdir(parents=True, exist_ok=True)
    fields = [
        "package", "version", "purl", "platforms", "license", "license_expression",
        "license_classifiers", "registry_status", "lock_hash_count", "registry_file_count",
        "matched_hash_count", "unmatched_hash_count", "hash_status", "project_urls",
        "requires_dist", "source_lockfiles", "dependency_via",
    ]
    summary = {
        "source": "Scenario Kinetic Music Video platform-specific uv lockfiles",
        "packages": len(packages),
        "platform_package_records": 0,
        "locked_sha256_hashes": 0,
        "registry_http_200": 0,
        "registry_failures": 0,
        "packages_with_license_field": 0,
        "packages_without_license_field": 0,
        "packages_with_all_locked_hashes_found": 0,
        "packages_with_unmatched_locked_hashes": 0,
        "packages_with_no_registry_release_files": 0,
        "notes": [
            "Read-only PyPI JSON metadata lookup; no distributions downloaded or installed.",
            "Registry metadata and hashes do not establish legal approval, source-header rights or vulnerability status.",
            "No vulnerability database was queried by this workflow.",
        ],
    }
    with (args.output / "pypi-package-registry-audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for (name, version), record in sorted(packages.items()):
            summary["platform_package_records"] += len(record["platforms"])
            locked_hashes = record["hashes"]
            summary["locked_sha256_hashes"] += len(locked_hashes)
            metadata, registry_status = fetch_metadata(name, version)
            info = (metadata or {}).get("info", {})
            release_files = (metadata or {}).get("urls", []) or []
            registry_hashes = {
                item.get("digests", {}).get("sha256")
                for item in release_files
                if item.get("digests", {}).get("sha256")
            }
            matched = locked_hashes & registry_hashes
            unmatched = locked_hashes - registry_hashes
            license_value = (info.get("license") or "").strip()
            license_expression = (info.get("license_expression") or "").strip()
            classifiers = [
                item for item in (info.get("classifiers") or [])
                if item.startswith("License ::")
            ]
            if registry_status == "HTTP_200":
                summary["registry_http_200"] += 1
            else:
                summary["registry_failures"] += 1
            if license_value or license_expression or classifiers:
                summary["packages_with_license_field"] += 1
                license_status = "REGISTRY_LICENSE_FIELD_PRESENT"
            else:
                summary["packages_without_license_field"] += 1
                license_status = "NOASSERTION"
            if not release_files:
                summary["packages_with_no_registry_release_files"] += 1
                hash_status = "NO_REGISTRY_RELEASE_FILES"
            elif locked_hashes and not unmatched:
                summary["packages_with_all_locked_hashes_found"] += 1
                hash_status = "ALL_LOCK_HASHES_MATCH_REGISTRY"
            elif matched:
                summary["packages_with_unmatched_locked_hashes"] += 1
                hash_status = "PARTIAL_LOCK_HASH_MATCH"
            else:
                summary["packages_with_unmatched_locked_hashes"] += 1
                hash_status = "NO_LOCK_HASH_MATCH"
            if registry_status != "HTTP_200":
                hash_status = "REGISTRY_LOOKUP_FAILED"
                license_status = "REGISTRY_LOOKUP_FAILED"
            writer.writerow({
                "package": name,
                "version": version,
                "purl": f"pkg:pypi/{name}@{version}",
                "platforms": ";".join(sorted(record["platforms"])),
                "license": license_value,
                "license_expression": license_expression,
                "license_classifiers": ";".join(classifiers),
                "registry_status": registry_status,
                "lock_hash_count": len(locked_hashes),
                "registry_file_count": len(release_files),
                "matched_hash_count": len(matched),
                "unmatched_hash_count": len(unmatched),
                "hash_status": hash_status,
                "project_urls": json.dumps(info.get("project_urls") or {}, sort_keys=True),
                "requires_dist": json.dumps(info.get("requires_dist") or [], sort_keys=True),
                "source_lockfiles": ";".join(sorted(record["source_files"])),
                "dependency_via": ";".join(sorted(record["via"])),
            })
            time.sleep(0.15)
    with (args.output / "pypi-package-registry-summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["registry_failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
