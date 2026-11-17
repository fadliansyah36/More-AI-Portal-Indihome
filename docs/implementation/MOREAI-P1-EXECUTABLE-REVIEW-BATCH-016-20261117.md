# P1 Executable Payload Review — Batch 016 (Ledger rows 322–522) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Ledger: `docs/implementation/p1-skill-payload-evidence/skill-payload-file-audit.csv`
Ledger blob SHA at review: `6661261f2cc6f87c326ae911c9551b5d5013c8a7`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope clarification

The requested contiguous ledger range 322–522 contains **201 executable-source entries** (inclusive), not 200. The authoritative ledger contains 875 executable-source entries. This batch covers exactly rows 322–522; the next contiguous range begins at row 523.

The review fetched source files from the pinned Scenario Skills commit and inspected them statically for process invocation, network/API calls, dynamic execution/import, filesystem/resource loading, engine services, persistence, remote/event boundaries, publishing operations, asset creation, and test-only fixtures. GitHub-returned blob SHAs were reconciled with the ledger entries during the review. This is source-integrity evidence only; it does not establish licensing, safety, dependency closure, or runtime correctness.

No source was executed/imported. No Roblox Studio, Lune, Unity Editor, Python tool adapter, browser, rendering, network provider, or customer runtime was launched. No tests, builds, staging, deployment, migrations, worker jobs, or Supabase operations were performed.

## Inventory and interim dispositions

| Ledger rows | Source area | Interim disposition |
|---|---|---|
| 322–331 | Roblox data and environment modules/adapters | DEFER |
| 332–341 | Roblox environment authoring and expert audit/spec/stats modules | DEFER |
| 342–348 | Roblox expert audit/check/environment/MCP/play/review/run adapters | DEFER |
| 349–366 | Roblox gameplay modules, client/server bootstrap, Lune audit and Python adapter | DEFER |
| 367–376 | Roblox Luau buffers, leak/probe/parallel modules and Python adapter | DEFER |
| 377–387 | Roblox monetization/catalog/entitlements/live config/purchases/telemetry and Python adapter | DEFER |
| 388–397 | Roblox networking/exploit guard/rate limit/suspicion and Python adapter | DEFER |
| 398–405 | Roblox performance profiling/audit/probe and Python adapter | DEFER |
| 406–423 | Roblox tooling, publish/cloud/place/version/restart/test scripts and fixtures | DEFER |
| 424–434 | Roblox UI audit/input/kit/layout/settings/style/templates and Python adapter | DEFER |
| 435–441 | Roblox VFX/audio audit, authoring/runtime modules and Python adapter | DEFER |
| 442–465 | Unity 2D authoring jobs, runtime components, Cinemachine integration and Python adapter | DEFER |
| 466–483 | Unity animation authoring/import/rigging/sampling/timeline/runtime and Python adapter | DEFER |
| 484–522 | Unity architecture/editor/runtime templates, persistence/input/event systems and test fixtures | DEFER |

**All 201 entries remain DEFER.** No final copy/adapt/archive-only/exclude decision is made in this batch. This review does not authorize importing any of these files into the MoreAI runtime or enabling a skill.

## Findings

### 1. Roblox environment and expert authoring (322–348)

- Environment modules such as `Looks.luau`, `MaterialKit.luau`, `Scatter.luau`, `TerrainKit.luau` and `WorldCheck.luau` create and inspect Roblox engine instances, materials, terrain and world state. Their semantics are Roblox DataModel-specific; do not port their object model directly into the MoreAI web/API runtime.
- `rbx_environment.py` uses process execution, Python import-path mutation, filesystem operations and compilation-related paths. Any future adapter requires a fixed executable allowlist, argument arrays without shell interpretation, minimal environment, process-tree timeout/cleanup, pinned tool versions and per-run workspace confinement.
- Expert Luau modules include `require`-based module composition and dynamic-code-related patterns (including loadstring indicators in audit logic). Treat module resolution as a fixed manifest graph; reject user-supplied module paths and dynamic source execution.
- `rbx_check.py`, `rbx_env.py`, `rbx_mcp.py`, `rbx_play.py`, `rbx_review.py` and `rbx_run.py` bridge local project files, processes and tooling. MCP transport is not itself an authorization boundary. Require typed operations, explicit capability grants, owner/run binding, audit receipts and isolated workers before considering any adaptation.
- These authoring/audit tools are not general-purpose customer skills without a product mapping and runtime compatibility decision.

### 2. Roblox gameplay and Luau utilities (349–376)

- Gameplay modules implement vehicle behavior, hitboxes, NPC behavior/pooling/services, path guards, projectiles, state machines, and client/server bootstrapping. They mutate engine state and can create long-lived event/task lifecycles. Bound object counts, loops, event subscriptions, NPC/path complexity, task lifetime and cleanup.
- `GameplayServer.server.luau` and `GameplayClient.client.luau` encode Roblox's client/server split. Preserve the principle of server-authoritative validation if useful, but do not transplant Player/RemoteEvent semantics into FastAPI.
- `rbx_gameplay.py` and `rbx_luau.py` use subprocesses and/or Python import-path and filesystem operations. Require pinned Lune/toolchain binaries, no shell, fixed operation maps, bounded output, process timeouts and workspace confinement.
- Luau buffer codec, probe, leak and parallel modules are engine/runtime-specific. Review binary payload limits, buffer lengths, worker fan-out, memory lifetime and any dynamic environment manipulation before any reuse.
- `setfenv` appears in Luau audit-related code; verify exact execution path and prevent untrusted code from controlling global environments. Do not expose an arbitrary Luau execution facility to customer requests.

### 3. Roblox monetization and networking (377–397)

- Monetization modules model Roblox Catalog, entitlements, live configuration, purchase handling, odds, shop ranking and telemetry. They rely on Roblox platform identity, entitlement and purchase semantics; they are not a payment or wallet implementation for MoreAI.
- `LiveConfig.luau` and telemetry modules reference platform HTTP services. Apply explicit destination allowlists, response-size limits, timeouts, schema validation and secret isolation if any external integration is ever adapted.
- `rbx_monetization.py` and `rbx_net.py` include subprocess/import-path/filesystem integration. They must not run inside FastAPI request workers; use dedicated, isolated workers with fixed commands and bounded resources if justified.
- Networking modules provide remote event/function validation, rate limiting, suspicion scoring and movement checks. The general defensive ideas may inform API threat modeling, but Roblox remotes, player identity, and in-memory suspicion state do not replace FastAPI authorization, tenant isolation, durable rate limits or Supabase RLS.
- Static audit modules are not proof that a production service is secure. All trust decisions must be made server-side from authenticated context, not client-supplied ownership or identity.

### 4. Roblox performance and tooling/publishing (398–423)

- Profiling modules inspect heap, micro-performance, scripts and scenes. Profiling output may expose project structure or runtime data; scope collection to an authorized owner/run and bound output.
- `rbx_perf.py`, `rbx_tooling.py` and adjacent adapters use external processes, filesystem operations and path/import manipulation. Enforce pinned binaries, fixed arguments, no shell, timeout/process cleanup, output limits and workspace confinement.
- Tooling modules include ship checks, sync checks, test runners, cloud Luau, place merge/version, publish and restart-server operations. These are privileged project mutation/deployment actions. Do not expose them as ordinary skill tools or run them without a separate permission/approval boundary, explicit target project, immutable artifact provenance and an auditable action receipt.
- `check_key.luau`, `cloud_luau.luau`, `place_versions.luau`, `publish.luau` and `restart_servers.luau` include API-key/HTTP-related patterns. Never commit credentials, log tokens, accept arbitrary endpoints, or let customer prompts choose privileged publishing targets.
- Test and template files are fixtures, not MoreAI application tests and not evidence of test execution. They remain deferred.

### 5. Roblox UI and VFX/audio (424–441)

- UI modules build Roblox-specific HUD/menu/catalog components and settings/styles. They are not Next.js components and do not justify redesigning the existing MoreAI customer dashboard. Only product-required missing frontend components may be added using the existing PRD design tokens and CSS/font/button/color conventions.
- UI style/template code references fonts, images and token-like configuration. Any potential asset reuse requires a separate asset/font license and provenance review; no Roblox UI assets or fonts are approved by this batch.
- `rbx_ui.py` and `rbx_vfx_audio.py` use filesystem/import-path operations; the latter also uses subprocess/image/audio-related paths. Require bounded media dimensions/duration/codec, malware/content inspection, path confinement and isolated media workers.
- Audio/VFX modules create or replicate engine effects and sounds. Bound instance counts, sound duration, sample/resource size, replication fan-out and runtime lifetime. Treat media assets and serialized effect descriptions as untrusted input.

### 6. Unity 2D, animation and architecture templates (442–522)

- Unity authoring jobs use `AssetDatabase`, `System.IO`, project asset paths, scene/resource loading and editor APIs. They mutate a Unity project and must not run in the API process. Any future support requires a dedicated, immutable-image Unity worker, per-run project copy, path confinement, resource quotas and cleanup.
- Unity 2D jobs build/import atlases, sprites, levels, cameras, lights, physics and tilemaps. Validate image dimensions, texture memory, sprite/atlas counts, project path boundaries and asset import settings.
- Cinemachine integration and animation jobs rely on optional Unity packages and APIs; `Type.GetType`/reflection patterns occur. Pin Unity/editor/package versions and resolve only a fixed allowlisted package set; do not allow user-supplied type names or arbitrary reflection dispatch.
- Animation authoring/import/rigging/sampling/timeline modules create and mutate controllers, clips, rigs, keyframes and project assets. Bound bones, clips, frame ranges, sample rates, keyframe counts, texture sizes and total import bytes. Review package install/update behavior and imported asset provenance.
- Unity runtime templates include health, inventory, save, input, event-channel, service and composition-root examples. These are product/game runtime patterns, not a replacement for MoreAI's FastAPI/Supabase data layer.
- `SaveData.cs`, `SaveService.cs`, `BindingStore.cs`, `RuntimeSet.cs`, and `GameRoot.cs` contain serialization or local persistence patterns. Do not transplant local save files or Unity PlayerPrefs as a second database; any transferable data model must be redesigned around existing Supabase tables, tenant ownership, RLS and server-side FastAPI contracts.
- Event channels and async helpers may provide conceptual patterns, but require explicit lifecycle disposal, cancellation, bounded concurrency and error propagation before any adaptation.
- Rows 515–522 are Unity test fixture sources. They were only read as source; no tests were run. Their presence does not waive the user's no-testing instruction.

## MoreAI architecture and adoption constraints

1. OpenManus remains the single Agent Runtime. OpenFuse is adapted as an internal FastAPI capability layer, not deployed as a second application/runtime.
2. The Memory Coordinator remains the single coordinator over the existing Working, Conversation, Long-term, Episodic, Semantic and Procedural memory lifecycle. Do not introduce another database or transplant Roblox/Unity local persistence.
3. Keep Supabase as the canonical database and FastAPI as the trusted business API. Customer frontend actions must use typed FastAPI contracts; browser Supabase usage is limited to the approved Auth flow.
4. Do not expose arbitrary code execution, dynamic module loading, shell commands, executable paths, project paths, network URLs, publish/restart operations, or tool arguments directly to customer prompts.
5. If an engine/media skill is approved later, run it in an isolated ephemeral non-root worker with immutable toolchain image, per-run workspace, egress allowlist, CPU/memory/time/output quotas, cancellation, lease fencing, artifact ownership checks and audit receipts.
6. Keep customer UI changes additive and minimal. Preserve existing layout, navigation, typography, colors, buttons and user journeys; add only missing components required by the PRD and existing design tokens.
7. Hash agreement establishes source identity only. It does not establish copyright/license compatibility, attribution, SBOM completeness, dependency safety, data rights, runtime correctness or production readiness.
8. All skill registration and activation remains blocked until P1 legal/security/provenance and dependency reviews reach final approved dispositions.

## Status

- Ledger rows reviewed in this batch: **322–522 (201 files)**.
- Interim disposition: **201 DEFER; 0 final approvals**.
- No source execution, tests, builds, staging or deployment performed.
- Next contiguous executable-source range: **523–572 (50 files)**.
- After all 875 executable-source files are reviewed, continue with configuration/schema, references/dependencies, assets/fonts and SBOM audits before final per-file dispositions.
- P1 remains **OPEN**. Phase 04–09 integration completion and Phase 10/11 release acceptance must not be claimed on the basis of this source audit.
