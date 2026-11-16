#!/usr/bin/env bash
set -Eeuo pipefail

# Provision only on the authorized, persistent Linux host. This script starts
# the pinned OpenFuse/ClamAV Compose stack; it does not create credentials.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

[[ "$EUID" -eq 0 ]] || fail "Run as root on the authorized Docker host."
command -v docker >/dev/null 2>&1 || fail "Docker Engine is not installed."
command -v findmnt >/dev/null 2>&1 || fail "findmnt is required."
command -v lsblk >/dev/null 2>&1 || fail "lsblk is required."
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required."

: "${MOREAI_OPENFUSE_BASE_IMAGE:?Set a digest-pinned Playwright base image}"
: "${MOREAI_CLAMAV_IMAGE:?Set a digest-pinned ClamAV image}"
: "${MOREAI_BROWSER_PROFILE_VOLUME:?Set the dedicated encrypted Docker data-root mount path}"
: "${MOREAI_BROWSER_SERVICE_TOKEN:?Set the OpenFuse worker token}"
: "${MOREAI_BROWSER_PROXY_TOKEN:?Set the private egress proxy token}"
: "${MOREAI_BROWSER_ALLOWED_DOMAINS:?Set exact public domain allowlist}"

is_digest_pinned() {
  [[ "$1" =~ @sha256:[a-f0-9]{64}$ ]]
}
is_digest_pinned "$MOREAI_OPENFUSE_BASE_IMAGE" || fail "MOREAI_OPENFUSE_BASE_IMAGE must end with @sha256:<64 lowercase hex characters>."
is_digest_pinned "$MOREAI_CLAMAV_IMAGE" || fail "MOREAI_CLAMAV_IMAGE must end with @sha256:<64 lowercase hex characters>."

(( ${#MOREAI_BROWSER_SERVICE_TOKEN} >= 32 )) || fail "MOREAI_BROWSER_SERVICE_TOKEN must contain at least 32 characters."
(( ${#MOREAI_BROWSER_PROXY_TOKEN} >= 32 )) || fail "MOREAI_BROWSER_PROXY_TOKEN must contain at least 32 characters."

# Do not accept wildcards, URLs, paths, IP literals or empty entries in this
# browser egress allowlist. The egress proxy separately validates resolved IPs.
IFS=',' read -r -a allowed_domains <<< "$MOREAI_BROWSER_ALLOWED_DOMAINS"
(( ${#allowed_domains[@]} > 0 )) || fail "The domain allowlist is empty."
for domain in "${allowed_domains[@]}"; do
  [[ "$domain" =~ ^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)+$ ]] \
    || fail "Allowlist entries must be exact DNS names without wildcard or URL syntax."
done

[[ -d "$MOREAI_BROWSER_PROFILE_VOLUME" ]] || fail "The encrypted Docker data-root mount path must already exist."
mountpoint -q "$MOREAI_BROWSER_PROFILE_VOLUME" || fail "MOREAI_BROWSER_PROFILE_VOLUME must be an active filesystem mountpoint."
docker_root="$(docker info --format '{{.DockerRootDir}}')"
[[ -n "$docker_root" && -d "$docker_root" ]] || fail "Docker data-root could not be resolved."
profile_source="$(findmnt -n -o SOURCE -T "$MOREAI_BROWSER_PROFILE_VOLUME" | head -n 1)"
docker_source="$(findmnt -n -o SOURCE -T "$docker_root" | head -n 1)"
[[ -n "$profile_source" && "$profile_source" == "$docker_source" ]] \
  || fail "The supplied encrypted mountpoint must be the filesystem backing DockerRootDir and its persistent named volumes."
lsblk -s -n -o TYPE "$docker_source" | grep -qx 'crypt' \
  || fail "DockerRootDir is not backed by a LUKS/dm-crypt device; refusing to store browser profiles or ClamAV signatures."

# Compose named volumes are persistent under DockerRootDir. The host encryption
# check above therefore protects both openfuse_browser_profiles and clamav_db.
docker compose --project-directory "$ROOT_DIR" \
  -f "$ROOT_DIR/apps/sandbox/compose.browser.yml" \
  up -d --build --scale browser-supervisor=1

printf '\nOpenFuse/ClamAV Compose services were requested on this encrypted host.\n'
printf 'Next: attach the persistent MoreAI worker with the worker-browser overlay:\n'
printf '  docker compose --project-directory %q -f docker-compose.runtime.yml -f apps/sandbox/compose.worker-browser.yml --profile worker up -d worker\n' "$ROOT_DIR"
printf 'Keep exactly one browser-supervisor replica until shared profile storage and sticky routing are designed.\n'
