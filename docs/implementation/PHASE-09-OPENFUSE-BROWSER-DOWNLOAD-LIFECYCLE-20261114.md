# Phase 09 — OpenFuse Browser Download Lifecycle

Date: 2026-11-14  
Branch: main  
Baseline: c09aa56faf09af0ffb0a2918219ac7fbbfc177ee

## Source implementation
- Added Playwright download interception for downloads initiated during existing navigate/extract actions; maximum three downloads per action.
- Enforced a 10 MB per-file limit and a narrow MIME allowlist using file signatures/content, not extensions. Executables and unknown binary formats are rejected.
- ClamAV INSTREAM scanning is mandatory. Missing configuration, scanner unavailability, timeout, infected/unknown verdict, unsupported MIME, malformed content and size excess fail closed.
- Worker sends scanner-approved bytes to an internal FastAPI route protected by the worker token. API independently verifies owner/run association, status, filename, size, SHA-256, MIME/signature and text/JSON content.
- API persists files to the existing private `moreai-artifacts` bucket and creates owner/run-linked artifact metadata with SHA-256 and scan provenance. Failed metadata persistence compensates the Storage object.
- Existing customer Artifacts list and 60-second signed-download route provide Customer Files/Artifacts and Agent Run visibility. No new visual component was required.

## Changed files
- `apps/sandbox/app/browser_service.py`
- `apps/sandbox/app/browser_supervisor.py`
- `apps/api/app/routers/artifacts.py`
- `.env.example`

No migration was required: the existing artifact schema and private bucket already support owner, run, metadata, checksum and signed URLs.

## Limitations and security
- Browser tool currently supports navigate/extract only; this captures automatic downloads during those actions, not arbitrary click automation.
- ClamAV must be deployed/reachable and configured via `MOREAI_CLAMAV_HOST` and `MOREAI_CLAMAV_PORT`; until then all downloads are blocked.
- Scanner runtime, deployment network policy and production secrets were not configured.
- Download bytes are carried transiently through worker memory; persistent storage occurs only after a clean scan.
- Existing signed URLs remain 60 seconds and require authenticated owner lookup.

## Verification
Source-only implementation. No tests, lint, typecheck, build, browser/API/scanner probes, Supabase mutations, staging or deployment were run, per instruction. Runtime behavior and scanner availability are NOT VERIFIED. Phase 09 remains IN PROGRESS.


## Main-branch source review follow-up

- Download interception and FastAPI persistence were committed in `c91080104662ba27a23788dc4d43662f583d25b5`.
- Binary-signature escape correction was committed in `678ba70b6aba2cdadb85f1474b06e34154655875`.
- Browser context restore was explicitly wired to the persisted encrypted storage state in `1541dc1de186cc875b60f54b433a16fc386a7ec1`.
- Current source includes browser session restore and state save, ClamAV INSTREAM, internal worker-authenticated artifact persistence, and the existing customer artifact list/signed URL projection.
- This remains source review only. No test, build, lint, API call, scanner probe or deployment has been performed.
