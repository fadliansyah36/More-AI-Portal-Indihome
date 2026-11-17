# P1 Executable Payload Manual Review — Batch 02

Date: 2026-11-17  
Branch: `main`  
Scope: 10 additional source files from pinned Scenario Skills and Motion Skills child repositories.  
Method: read-only source inspection at immutable commits; no code, test, renderer, engine, process, provider or installation was executed.

## Reviewed files and decisions

| # | Source file | Finding | Decision |
|---:|---|---|---|
| 1 | Scenario `skills/dcc/maya/scenario-maya-expert/scripts/mx_run.py` | Launches `mayapy` as a child process to execute caller-supplied Maya Python job files. The child process timeout and output protocol are useful reliability controls, but the job remains arbitrary code running with the local user's filesystem/process privileges. | **DEFER** — only in a disposable Maya worker with per-run filesystem, no host secrets/mounts, bounded process tree and strict job provenance. |
| 2 | Scenario `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_batch_job.py` | ZBrush-side batch recipe executed through the local ZBrush `-script` mode and operates on scene/mesh inputs. This is application automation code, not a server-safe business tool. | **DEFER** — isolate the ZBrush desktop/runtime and project assets per tenant; do not execute inside FastAPI/worker host. |
| 3 | Scenario `skills/game-engines/godot/scenario-godot-expert/scripts/gd_env.py` | Downloads large Godot export-template archives and GUT archives, writes to user-level caches/project paths and extracts ZIP entries. Godot template archive digest is checked against a release checksum file, but the checksum file is fetched from the same origin. The GUT digest is only enforced when the requested version exists in the local known-digest map; an unlisted version can be downloaded without a pinned digest. ZIP extraction paths are joined under the target without an explicit resolved-path containment check in the inspected extraction loop. | **DEFER** — pin versions and independent digests, enforce allowlisted origins and download-size limits, validate archive member paths against traversal, extract to quarantine, and run only in disposable project-scoped workers. |
| 4 | Scenario `skills/game-engines/roblox/scenario-roblox-tooling/scripts/template/tools/restart_servers.luau` | Calls Roblox Open Cloud `restartServers` and can terminate live game servers. It requires `ROBLOX_RESTART_LIVE=1` and `ROBLOX_API_KEY`; comments say the flag should be set only by an approved release job. This is a high-impact external production action. | **DEFER** — require explicit customer/admin approval, tenant-scoped secret reference, dry-run preview, environment/target confirmation, idempotency, rate limits and immutable action receipt. Never surface as an unapproved generic skill tool. |
| 5 | Scenario `skills/game-engines/unity/scenario-unity-pipeline-automation/scripts/AgentKit/PipelineCli/PipelineCliCommands.cs` | Exposes named Unity pipeline commands rather than a generic eval/run-command surface. This is a positive narrowing of the tool surface, but it still controls a local Unity project/editor pipeline. | **DEFER** — possible future adapter only after exact command schema, project ownership, editor process isolation and side-effect approval are enforced. |
| 6 | Scenario `skills/game-engines/unity/scenario-unity-pipeline-automation/scripts/AgentKit/Pipeline/PipelineBuild.cs` | Build-side pre-build gate can run content checks and mutate/create Unity build profiles/scenes and initiate player-build workflows. These are project/build side effects. | **DEFER** — isolated build worker, pinned Unity/editor/toolchain, project-root boundary, artifact scanning and approval for release-target builds. |
| 7 | Motion `skills/talking-head/scripts/render.mjs` | Runs ffmpeg/ffprobe against local generated media and writes final render/caption files. It assumes a trusted local output folder and process environment. | **DEFER** — adapt to a resource-limited renderer with run-scoped object storage, bounded output and process-tree cleanup. |
| 8 | Motion `skills/talking-head/scripts/prepare-person.mjs` | Uses ffmpeg/ffprobe to extract media metadata/frames and writes local preparation outputs. Input paths and media complexity are caller-controlled. | **DEFER** — require strict media MIME/size validation, isolated parsing, CPU/memory/time limits and private temporary storage. |
| 9 | Motion `skills/talking-head/scripts/talking-head.mjs` | CLI can trigger voice cloning, paid generation and recovery operations via the provider pipeline. A local dry-run mode does not implement MoreAI's credit reservation, user consent, approval, durable idempotency or billing receipt. | **DEFER** — route only through the MoreAI provider gateway and Agent Run lifecycle; require explicit voice/media consent and credit reservation before paid calls. |
| 10 | Motion `skills/talking-head-b-roll/scripts/render.mjs` | Local browser/Playwright + ffmpeg renderer opens project HTML and reads video/transcript files, then writes frame/render artifacts. It has local filesystem and process access and no tenant sandbox of its own. | **DEFER** — isolated browser/render worker, network disabled by default, bounded media/frame/size/runtime and artifact quarantine. |

## Security and architecture conclusions

- The Maya and ZBrush execution surfaces are privileged local application bridges; the Godot and Unity modules are local engine/project automation. None belongs in a shared FastAPI process.
- The Roblox server-restart tool is a production-impacting external action and must be approval-gated, not exposed as a normal autonomous tool.
- Godot archive installation requires stronger archive traversal checks and immutable artifact pinning before reuse. A release checksum downloaded from the same origin is integrity evidence but not independent publisher authenticity.
- Motion media tools need a single MoreAI renderer/provider adapter with cost reservation, consent, secret references, artifact retention and network egress enforcement. Do not copy local provider credentials into customer skill context.
- These are integration-boundary findings, not a claim that a confirmed exploit or malware sample was found.

## Review coverage

- Manual executable-source review: **23/875** (13 from Batch 01 + 10 from Batch 02).
- Remaining executable-source files: **852/875**.
- All 23 reviewed source files are **DEFER** pending isolated runtime/provider/action adapters.
- 69 configuration/schema files and 726 reference documents still require separate manual review.
- The 229/229 entrypoint sweep and 148/148 reference-candidate triage remain complete as separately documented.
- The 1,941-row operational disposition ledger remains 15 ARCHIVE_ONLY and 1,926 DEFER. This batch adds detailed review evidence for 10 of the already-DEFER executable rows; it does not authorize ingestion.

No tests, builds, package installs, scripts, engines, providers, Supabase operations, staging or deployment were run.

**P1 remains OPEN.**
