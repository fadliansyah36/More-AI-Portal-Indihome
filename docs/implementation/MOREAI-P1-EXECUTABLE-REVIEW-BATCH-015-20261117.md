# P1 Executable Payload Review — Batch 015 (Ledger rows 221–321) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope clarification

The requested ledger range 221–321 contains **101 entries**, not 200. This batch reviews exactly that contiguous range to avoid skipping or duplicating ledger rows. The next unreviewed range begins at row 322.

Coverage:
- Godot shaders and shader authoring tools (221–241)
- Godot UI tools (242–255)
- Godot VFX tools (256–272)
- Roblox animation tools (273–279)
- Roblox architecture and arena fixtures (280–311)
- Roblox asset and data helpers (312–321)

The files were fetched from the pinned Scenario Skills commit and inspected statically for subprocess/process invocation, network/API calls, dynamic execution/import, filesystem/resource loading, Roblox service access, remotes, persistence, and resource creation. SHA values returned for the fetched files were compared against the corresponding P1 ledger Git blob SHA values; all 101 matched.

No source was executed/imported. No Godot, Blender, Roblox Studio, Lune, browser, rendering or provider runtime was launched. No tests, builds, staging, deployment, migration, worker, or Supabase operation was performed.

## Inventory and interim dispositions

| Ledger rows | Source area | Interim disposition |
|---|---|---|
| 221–241 | Godot shader examples, GLSL/GDShader resources, shader compile/sweep/compute helpers, Python installer | DEFER |
| 242–255 | Godot UI builder, HUD/menu/safe-area, UI audit/capture/focus/layout/rebind/settings/theme, Python installer | DEFER |
| 256–272 | Godot VFX runtime, shaders, audit/build/capture/jobs/recipes/self-test, Python installer | DEFER |
| 273–279 | Roblox animation audit/clip/face/IK/rig and Blender/Lune animation adapters | DEFER |
| 280–311 | Roblox architecture audit/binder/loader, Lune adapters, Rojo build adapter, arena fixtures and client/server/shared services | DEFER |
| 312–321 | Roblox asset audit/mesh/payload/UGC checks, Blender/Rojo asset adapters, Roblox data audit/check/key queue/migration helpers | DEFER |

**All 101 entries remain DEFER.** No final copy/adapt/archive-only/exclude decision is made in this batch.

## Findings

### 1. Godot shader tools (221–241)

- Scene builders create and save scenes/materials from shader resources; examples accept paths such as shader and output paths in job arguments. Resolve all paths through a trusted per-run manifest and confine writes to the isolated project workspace.
- `compile_probe.gd` and `render_probe.gd` intentionally compile shader strings and attach shaders to rendered objects. The probe corpus includes invalid/edge shader cases. Keep this as isolated validation tooling, not a customer arbitrary-shader execution endpoint.
- `compute_texture.gd` creates RenderingDevice resources, dispatches compute shader work and captures GPU output. Cap texture dimensions, workgroup counts, GPU allocation, execution time and concurrent jobs; ensure all RIDs are released on success, error, cancellation and timeout.
- `shader_tools.gd` scans shader files, compiles files and sweeps parameter variants. It can discover shader files under a project root and supports caller-provided file/root arguments. Restrict traversal to an allowlisted workspace, cap file count/size, and do not include arbitrary addon directories by default.
- `gd_shaders.py` installs tools/resources into Godot projects and mutates Python `sys.path`. Pin the imported expert toolkit and constrain every copy/write to a job-owned project root.
- `water_lite.gdshader` and `water_stylized.gdshader` include a shared shader include file. Dependency closure and include path integrity must be verified before shipping; do not approve the shader files in isolation.
- Shader code is executable GPU logic. Review loops, texture sampling, storage buffers/images, render modes, includes and resource use. Never allow unreviewed customer-supplied shader source to execute in shared render infrastructure.

### 2. Godot UI tools (242–255)

- `build_g7.gd` builds a UI scene, loads scripts by path and writes project settings/directories. The script path and theme/font resources must be fixed by a trusted skill manifest, not supplied as arbitrary customer paths.
- `ui_audit.gd`, `ui_capture.gd`, `ui_focus.gd` and `ui_layout.gd` load/instantiate scenes and can load setup scripts from paths, mutate project settings for pseudolocalization, and capture UI at different sizes. Confine scene/script paths, restrict setup scripts to a fixed registry and bound resolution, capture count, memory and artifact size.
- `ui_rebind.gd` mutates Godot `InputMap` bindings and loads/saves configuration files. Restrict action names and event types; persist only in a per-run user data directory. Do not let customer input overwrite project-wide/shared input settings.
- `ui_settings.gd` persists settings to `user://settings.cfg`. Isolate the user data directory per tenant/run and validate types, keys and file size.
- `ui_theme.gd` loads font/theme resources and assigns them to generated themes. Only load approved font/theme resources; check licensing, font file size and resource compatibility.
- `ui_selftest.gd` recursively scans and loads GDScript files. It is test/inspection code and was not run; restrict scan root and file count if it is later used.
- `gd_ui.py` installs modules and changes Python import paths. Pin dependency locations and confine file operations to the job workspace.
- These are game UI authoring tools, not web frontend components. They do not authorize changing the existing MoreAI customer dashboard design system or importing Godot UI patterns into Next.js.

### 3. Godot VFX tools (256–272)

- Runtime VFX scripts and shader resources implement particle effects, projectile visuals, bursts, trails and screen/impact effects. Bound particle counts, lifetime, spawn rates, shader complexity, texture sizes and GPU/CPU budgets.
- `vfx_audit.gd`, `vfx_capture.gd`, `vfx_jobs.gd` and `vfx_recipes.gd` load and instantiate scenes, build resources and capture outputs. Scene paths, spawn scenes, recipe IDs, effect variants and output paths must be allowlisted and schema-validated.
- `vfx_build.gd` accepts a `shader_process` resource path for particle process material. Do not permit arbitrary shader paths or user-uploaded shader code; resolve only pinned approved shader resources.
- `vfx_selftest.gd` loads and exercises toolkit scripts/resources; it is not evidence of a test pass because it was not executed.
- `gd_vfx.py` installs scripts/shaders and processes image files using Python image tooling. Pin dependencies, bound image dimensions and output counts, and confine all writes to the run workspace.
- VFX workers should be isolated from API and should have GPU allocation and job concurrency controls.

### 4. Roblox animation tools (273–279)

- Luau animation modules create rigs, poses, keyframe sequences, curve animations and IK controls. These operations create/modify engine instances and can consume significant CPU/memory; cap bones, joints, keyframes, clip duration, sample rate and rig complexity.
- `AnimAudit.luau` audits deprecated APIs and architecture patterns. It is analysis logic and must not be mistaken for a runtime policy enforcement layer.
- `blender_roblox_anim.py` exports animation data from Blender and writes output files. Keep it in an isolated, version-pinned Blender worker; limit scene complexity, frame range, output bytes and filesystem access.
- `rbx_animation.py` launches external processes including Lune via subprocess, writes generated Luau/data and manipulates Python import paths. Use a fixed executable allowlist, no shell, argument arrays, minimal environment, timeout/process-tree cleanup and a pinned Lune runtime. Do not accept customer-controlled executable paths or command arguments.
- The animation pipeline bridges Blender samples to Roblox KeyframeSequence data. Validate all imported samples, numeric ranges, rig identifiers and serialized payload sizes.

### 5. Roblox architecture and arena fixtures (280–311)

- `ArchAudit.luau` statically analyzes Roblox project structure, `require()` resolution, service boundaries and DataStore/HTTP usage. Its findings are useful audit evidence, not proof that the audited project is safe.
- `Binder.luau` and `Loader.luau` manage lifecycle/binding and module loading. Enforce fixed module roots, dependency graph limits, cycle handling and deterministic cleanup.
- `lune_arch_audit.luau` and `lune_place_facts.luau` read and deserialize Roblox place files through Lune libraries. Treat place files as untrusted input; pin the Lune and Roblox serialization libraries, cap input size and graph depth, and isolate parsing.
- `rbx_architecture.py` invokes Rojo build/sourcemap and other subprocess commands, writes project artifacts and changes Python import paths. Use fixed binaries/arguments, no shell, timeouts, bounded output, pinned tool versions and workspace confinement.
- The arena fixture tree intentionally contains both correct and incorrect architecture patterns (cyclic requires, global registry, leaked connection/table, server-only module referenced from replicated code, GUI/service coupling, and client/server examples). These are audit fixtures and must not be treated as approved production patterns or copied wholesale into a product.
- Client/server separation is critical: never expose server-only services, secrets or privileged modules through replicated/client-visible module trees. Validate every client-to-server request on the server and derive identity/ownership from the authenticated Player rather than client-supplied fields.
- `MapService`, `RoundService`, `TeamService` and `WeaponService` mutate game state, create/destroy instances, spawn tasks and manage game flow. Apply server-authoritative validation, bounded loops, cancellation and deterministic cleanup.
- `RoundService` contains a persistent round loop; ensure shutdown and error states cannot leave orphaned loops or duplicate state transitions.
- `WeaponService` and other service methods must validate item identifiers, ownership, cooldowns and state transitions on the server. Never trust client-side UI state or prices/purchase claims.
- These are Roblox-specific modules and are not compatible with the MoreAI FastAPI/OpenManus runtime without an explicit adapter and product decision.

### 6. Roblox asset and data helpers (312–321)

- `AssetAudit.luau` analyzes asset structure; `MeshBuild.luau` creates mesh/accessory instances; `Payload.luau` structures payload data; `UGCCheck.luau` invokes Roblox AvatarCreationService validation. UGC validation requires the correct Roblox server/playtest data model and cannot be treated as a static or offline guarantee.
- `blender_roblox_prep.py` performs mesh/scene preparation and writes exported assets. Enforce polygon/vertex/material/texture limits, Blender version pinning, output path confinement and worker resource quotas.
- `rbx_assets.py` invokes external processes (including process inspection and tool execution), writes artifacts and changes import paths. Fixed toolchain allowlists, no shell, process timeouts, minimal environment and per-run workspace are mandatory.
- `DataAudit.luau` inspects use of DataStore, MemoryStore, MessagingService, HTTP and teleport APIs. It is a static architecture analyzer; it does not prove the actual runtime policies, quotas or authorization are correct.
- `DataCheck.luau` evaluates whether values can be serialized for DataStore and highlights serialization edge cases. Preserve finite-number validation, schema validation and strict payload limits. Do not assume arbitrary JSON encoding is lossless for NaN/Infinity or all engine-specific values.
- `KeyQueue.luau` serializes DataStore calls per key with bounded retries/backoff. Its retry semantics need idempotent update functions and explicit handling of throttling, cancellation, lease loss and duplicate requests before use.
- `Migrate.luau` performs versioned schema migration of saved tables. Migrations must be deterministic, forward-compatible where required, all-or-nothing and protected against partial writes. Never run these Roblox DataStore migrations against MoreAI Supabase; they are platform-specific examples.

## Adoption/security requirements

1. Do not execute Godot, Blender, Lune, Rojo, native tools or Roblox-specific jobs inside FastAPI. Use dedicated ephemeral, non-root workers pinned by immutable image digests.
2. Do not expose arbitrary shader source, script path, module name, method, executable, shell command, remote URL or dynamic `require` to customer inputs. Use fixed operation registries and typed schemas.
3. Validate all paths and keep filesystem reads/writes inside owner/run-scoped workspaces; reject traversal, symlink escapes, absolute host paths and shared template mutation.
4. Treat shader, scene, place, GLB, native extension and animation inputs as hostile. Apply parser limits, geometry/frame/texture/graph bounds and isolated processing.
5. For networked game templates, enforce server-authoritative state, authenticated peer identity, remote rate/payload limits, ownership validation and strict client/server module separation.
6. Pin toolchains/dependencies and maintain provenance. Hash match does not establish license rights, dependency safety, attribution completeness or runtime correctness.
7. Bind outputs to authenticated owner, Agent Run, pinned skill version, permission/approval and audit receipt. Preserve idempotency, lease fencing, cancellation, timeout, cleanup and owner-checked artifact download.
8. Keep Roblox DataStore/MessagingService/MemoryStore semantics distinct from MoreAI Supabase. Do not create a parallel DB or transplant Roblox persistence code into the customer platform.

## Status

- Ledger rows reviewed: **221–321 (101 files)**.
- Fetched Git blob SHA matched ledger: **101 / 101**.
- Interim disposition: **101 DEFER; 0 final approvals**.
- Cumulative manually reviewed executable-source payloads, batches 001–015: **321 / 875 (36.69%)**.
- P1 remains **OPEN**. Next contiguous range: **322–371 (50 files)**. After all 875 executable files are reviewed, continue with configuration/schema, references/dependencies, assets/fonts and SBOM audits before final per-file dispositions.
