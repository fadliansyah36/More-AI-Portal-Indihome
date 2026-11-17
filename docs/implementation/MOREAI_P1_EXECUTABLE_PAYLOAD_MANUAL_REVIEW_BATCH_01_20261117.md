# P1 Executable Payload Manual Review — Batch 01

Date: 2026-11-17  
Branch: `main`  
Scope: 13 source files from the pinned Scenario Skills and Motion Skills payloads.  
Method: read-only inspection of source text from immutable commits, including imports, process/network/file boundaries, credential flow, and execution entrypoints. No source code or scripts were executed.

## Reviewed files and dispositions

| # | Source file | Review finding | Decision |
|---:|---|---|---|
| 1 | Scenario `skills/dcc/maya/scenario-maya-expert/scripts/mx_bridge_server.py` | Opens a loopback command port and reads job files, then executes submitted Python with `exec(compile(...))` on Maya's main thread. Its own header explicitly says there is no authentication and any local process can send Python. Loopback binding does not isolate mutually untrusted local processes. | **DEFER** — do not expose in a hosted/multi-tenant MoreAI worker. Requires an isolated per-run desktop/GUI agent, authenticated IPC, owner-scoped job directory, strict protocol and process boundary. |
| 2 | Scenario `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_plugins/zb_bridge_server.py` | Listens on `127.0.0.1`, accepts JSON containing code and executes it using `exec(compile(...))`; no authentication is described in the server protocol. Main-thread mode is experimental. | **DEFER** — same local-process trust issue as Maya bridge; no customer/browser access or shared worker deployment. |
| 3 | Scenario `skills/dcc/roblox/scenario-roblox-expert/scripts/rbx_mcp.py` | Starts the local Roblox Studio MCP binary as a subprocess and drives an already signed-in Studio session. This is a workstation-bound privileged control channel, not a headless multi-tenant service. | **DEFER** — only reconsider with a dedicated per-customer isolated Studio worker, explicit session binding/consent and audited tool allowlist. |
| 4 | Scenario `skills/game-engines/roblox/scenario-roblox-expert/scripts/rbx_run.py` | Invokes Roblox Studio's RunScript task against a local place file and runs a supplied Luau chunk. | **DEFER** — arbitrary project-code execution must remain in an isolated disposable runner with strict file/network/resource controls. |
| 5 | Scenario `skills/game-engines/godot/scenario-godot-expert/scripts/gd_run.py` | Uses argv-based subprocess calls (not shell interpolation), timeout and process locks, which are positive local safeguards. However, it discovers host processes, writes locks/logs under the local user's cache, launches Godot project scripts and exports, and accepts project/script arguments. It assumes a trusted local workstation and does not establish a tenant-isolated sandbox. | **DEFER** — port only behind a disposable sandbox/microVM, non-root identity, read-only base, no host mounts/secrets, network disabled by default, strict project-root allowlist, resource limits and process-tree cleanup. |
| 6 | Scenario `skills/game-engines/godot/scenario-godot-pipeline-automation/scripts/gd_pipeline.py` | Installs files/plugins into caller-selected projects, downloads gdUnit4 archives and verifies a pinned digest, launches Godot through `gd_run`, checks URLs, and exposes an MCP stdio helper accepting a command array. Digest verification is useful but does not replace origin/egress and tenant isolation. | **DEFER** — external archive fetches need allowlisted origins, pinned artifact metadata and quarantine; arbitrary MCP command launch and project writes require sandbox policy. |
| 7 | Scenario `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_batch.py` | Orchestrates local GUI ZBrush, subprocess launch/restart, desktop capture and file-based batch recipes. It is designed for an interactive workstation. | **DEFER** — requires isolated desktop worker, fixed executable allowlist, bounded jobs, scoped file access and auditable restart/cancellation. |
| 8 | Motion `skills/talking-head/scripts/providers.mjs` | Reads FAL and ElevenLabs credentials from environment, uploads voice/media inputs to external providers, and downloads a supplied HTTPS URL. HTTPS-only validation is insufficient: no destination host allowlist, redirect revalidation, IP-range/SSRF guard, content-length/MIME cap or quarantine is visible in this adapter. | **DEFER** — rewrite as a server-side provider adapter using secret references, user consent, cost reservation, strict provider-origin allowlist, redirect/DNS egress checks, download size/MIME validation and private artifact quarantine. |
| 9 | Motion `skills/talking-head/scripts/pipeline.mjs` | Maintains local run state and writes media/request/response artifacts, uploads image/audio files through provider adapter, downloads generated video and invokes ffmpeg via argv. It assumes trusted local paths and a local renderer environment. | **DEFER** — adapt only after run-scoped storage, artifact scanning, idempotent paid-provider calls, secret redaction and isolated renderer controls. |
| 10 | Motion `skills/lower-thirds/scripts/render.mjs` | Opens caller-supplied HTML through Playwright `file://`, writes frame files and invokes ffmpeg/ffprobe. It has local filesystem/browser and process access; no multi-tenant sandbox is established by the script itself. | **DEFER** — renderer must run in disposable sandbox with read-only input mount, isolated browser profile, blocked network by default, bounded frames/resolution/runtime/output and cleanup. |
| 11 | Motion `skills/talking-head-b-roll/scripts/transcribe.mjs` | Reads local video/audio, invokes ffprobe/ffmpeg and optional Whisper process, and may upload media to ElevenLabs using an environment API key. Temporary files are local. | **DEFER** — media processing and external upload need consent, scoped credentials, isolated worker, file-type/size validation, retention policy and artifact cleanup. |
| 12 | Motion `skills/soundtrack/scripts/sync-check.mjs` | Invokes ffprobe/ffmpeg against caller-supplied media and captures raw video/audio buffers with large maximum buffers. This can consume substantial memory/CPU on untrusted inputs. | **DEFER** — require media parser isolation, input limits, timeouts, memory/CPU quotas and bounded output. |
| 13 | Scenario `skills/dcc/maya/scenario-maya-expert/scripts/mx_bridge.py` | Client connects to the local Maya command port/Unix socket and submits job IDs; it inherits the server's unauthenticated local IPC trust model. | **DEFER** — no use until the server protocol is replaced by authenticated, owner-scoped IPC. |

## Cross-cutting findings

- These are **deployment-boundary findings**, not claims that malware or a remotely exploitable vulnerability was confirmed.
- Loopback-only sockets are not sufficient authentication between untrusted local processes.
- DCC/game-engine skills (Maya, ZBrush, Roblox Studio, Godot) are workstation/desktop automation capabilities, not safe direct tools inside a shared API process.
- Motion render/transcribe/provider flows are local media pipelines with paid third-party calls. They must be adapted to MoreAI's durable Agent Run, approval, credit reservation, server-side secret and artifact lifecycle.
- Provider download URLs must not be accepted solely because their scheme is HTTPS. Apply the Phase 04 SSRF/egress policy to redirects and resolved addresses.
- All 13 reviewed source files remain **DEFER**. No code was copied into the active runtime or executed.

## Review coverage

- Manual entrypoint review: 229/229 complete (separate report).
- Manual executable-source review in this batch: 13/875.
- Remaining executable-source files: 862/875.
- Configuration/schema files: 0/69 manually reviewed in this batch.
- Reference-document manual triage: all 148 parser candidates classified in the separate reference-triage report; that is not a full semantic review of all 726 documents.
- Binary/font review: 10 media/binary files classified ARCHIVE_ONLY; 4 font files DEFER pending WOFF2 metadata/provenance review.

## Next review batch

Continue through the remaining executable payloads by capability risk: process/IPC/MCP, network/provider clients, filesystem/archive extraction, package installation, project mutation, then pure runtime/example source. Review configuration/schema files and all 726 references separately. Keep every unreviewed executable/config file DEFER; do not promote by file extension or keyword scan.

**Status: P1 remains OPEN.** This batch is static manual review only; no tests, builds, package installs, source execution, staging, deployment, Supabase reads/writes or migrations.
