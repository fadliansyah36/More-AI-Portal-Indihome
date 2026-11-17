# P1 Executable Payload Review — Batch 013 (50 files) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope

This batch covers the next 50 consecutive `executable-source` entries in the canonical P1 ledger, rows 121–170. The request described 200 files but explicitly identified ledger rows 121–170; this report follows that exact 50-row range. All files were fetched from the pinned source revision. Fetched Git blob SHA values match the corresponding ledger SHA for all 50 entries.

Static review focused on process execution, network/downloads, dynamic execution/import, filesystem and path operations, Godot resource loading, save/persistence behavior, and engine boundaries. This was not a full semantic, transitive dependency, license, or runtime audit.

No code was executed or imported. No Godot/FFmpeg runtime, test, build, render, worker, provider, staging, deployment, migration, or Supabase operation was run.

## Inventory and interim dispositions

| Ledger rows | Scope | Interim disposition |
|---|---|---|
| 121–125 | Godot architecture templates: inventory stack, base level, main game, persistence component, save service | DEFER |
| 126–133 | Godot audio helpers: audit, buses, meter, music builder, 3D occluder, SFX pool, tone generator, Python audio adapter | DEFER |
| 134–143 | Godot expert toolkit: audit/build/capture/job/profile helpers and Python environment/live/review/run/stat adapters | DEFER |
| 144–169 | Godot gameplay helpers: arena, AI brain, bullet pool, combat layers, crowd benchmark, dungeon generation, enemy management, hit logging/boxes, inventory, navigation, perception, quest rules, save I/O, state machine and states, voice pool | DEFER |
| 170 | Python gameplay installer/adapter `gd_gameplay.py` | DEFER |

**50/50 entries remain DEFER.** No ledger disposition was promoted to final.

## Findings

### 1. Architecture templates and persistence (121–125)

- The basic inventory, level and persistence components are small gameplay templates; they are not standalone deployable skills. Their dependencies, consuming scenes, registered classes and project settings still require review.
- `main_game.gd` loads a PackedScene from a path and schedules level loading with `call_deferred`. Scene paths must come from a trusted, owner-scoped project manifest, not arbitrary customer strings.
- `save_service.gd` creates directories and writes JSON save slots under `user://saves`. Its own comments warn that loading Godot resource files such as `.tres`/`.res` can execute embedded GDScript and that `str_to_var` or unchecked resource deserialization is unsafe for untrusted data. Preserve the safer data-only serialization boundary; validate schema, size, version, ownership and allowed value types. Do not deserialize customer-provided Godot resources or arbitrary Variants.

### 2. Audio helpers (126–133)

- `audio_buses.gd` loads and mutates audio bus layout configuration. Restrict layout paths and supported bus/effect types; reject unapproved custom resource/script references.
- `audio_meter.gd` can write WAV output; enforce output-root confinement, sample-rate/channel/frame limits, duration limits and artifact quotas.
- `music_builder.gd` loads audio streams from path-like clip specifications and assembles playback resources. Use a typed clip manifest, allowlisted resource paths and bounded clip count/duration; do not accept arbitrary filesystem paths.
- `gd_audio.py` invokes `ffprobe` with `subprocess.run`, reads WAV data, creates directories and installs helper scripts into a Godot project. Pin the executable and worker image, use argument arrays/no shell, impose timeout/output bounds, validate media files and isolate project writes. No arbitrary FFmpeg/ffprobe command fragments should be accepted.
- Audio generation/inspection must run in an isolated media/Godot worker, never in the FastAPI request process. Enforce CPU, memory, disk, duration and concurrency quotas.

### 3. Godot expert toolkit and adapters (134–143)

- `agent_audit.gd` inspects project settings, export presets, scripts and resources. Treat project content as untrusted and bound traversal, file size and report output.
- `agent_build.gd` creates directories and writes project scenes/configuration. Confine writes to a per-run workspace and prevent edits to shared templates or host paths.
- `agent_capture.gd` loads and instantiates project scenes to capture screenshots/sequences. Scene instantiation is active resource processing; use allowlisted scenes and resource limits.
- `agent_job.gd` resolves/loads a script path and dispatches methods, creates directories and loads scenes. This is a sensitive execution boundary: do not expose arbitrary script path, method name or script source from customer input. Use a fixed operation registry, typed schemas and explicit capabilities.
- `gd_env.py` invokes Godot subprocesses, downloads tools/assets through `urllib.request.urlopen`, writes files, clones directories using `cp -cR`, and changes Python import paths. Network downloads require pinned URLs/digests, HTTPS host allowlists, redirect validation, byte/time limits, safe temporary files and signature/hash checks. Do not allow user-controlled download URLs. The clone operation is OS-specific and must be constrained to workspace-owned paths.
- `gd_live.py` starts subprocesses and launches configured processes; its setup notes include external toolchain installation/build requirements. Treat command/args configuration as privileged operator configuration, never tenant-provided values. No persistent shared live process or editor session should cross tenant boundaries.
- `gd_review.py` invokes external image/video tooling through subprocess and reads image files. Bound input image dimensions/count and output paths; use fixed tool arguments and timeouts.
- `gd_run.py` invokes system commands/process inspection and launches Godot jobs. This is a high-impact execution adapter. Keep it inside an ephemeral sandbox with strict command allowlists, fixed Godot binary, no shell, minimal environment, process-tree termination, no host mounts and default-deny egress. Never expose arbitrary command or script execution to the public API.
- `gd_stat.py` parses engine output/logs. Treat logs as untrusted and cap size/line count; escape output rendered in UI.
- These helpers are development/engine tooling and must not become a general-purpose customer shell or remote execution surface.

### 4. Gameplay helpers and adapter (144–170)

- Most gameplay GDScript files are in-engine logic for combat, inventory, navigation, perception, quests, AI states and audio voice pools. They rely on Godot classes/resources and cross-file preload dependencies; review dependency closure and engine version compatibility before packaging.
- `crowd_bench.gd` is a benchmark that instantiates gameplay components and may scale entity counts. It requires strict maximum entity counts, bounded frames/time, memory ceilings and explicit non-production capability.
- `dungeon_gen.gd` generates level structures; constrain dimensions, room/cell counts, recursion/iteration, collision and output resource size to prevent resource exhaustion.
- `save_io.gd` persists resources and includes a checked resource-loading approach with an allowlist of save classes. Preserve and strengthen this allowlist. Never load arbitrary resource/script paths from player shares or mod folders; use data-only schemas wherever possible.
- `gd_gameplay.py` installs GDScript helpers into a project, creates directories and modifies `sys.path`; it delegates operations to expert toolkit modules. Resolve dependencies from pinned internal packages and a fixed allowlist; prohibit user-supplied module paths and ensure all copied files stay within the run workspace.
- Combat, AI and navigation scripts can create large numbers of entities or expensive physics/path queries. Use per-operation ceilings, frame/time limits and deterministic cleanup.
- Gameplay scripts are not independent Agent Skills by themselves. Their scene, project, class registration, addon and asset dependencies must be mapped before import.

## Required controls before any adoption

1. Do not execute Godot, Python adapter scripts, FFmpeg/ffprobe or shell commands inside FastAPI. Use isolated, ephemeral, non-root worker images pinned by digest.
2. Replace any general-purpose script/method/command execution interface with a fixed operation registry and typed Pydantic input schemas. Customer inputs must not select executable binaries, script paths, dynamic imports, command lines or arbitrary methods.
3. Enforce owner- and run-scoped workspace roots. Canonicalize paths; reject traversal, symlink escapes, absolute host paths, shared template writes and paths outside allowed input/output directories.
4. Apply default-deny egress. Download only from operator-configured host allowlists with pinned content digests, redirect controls, TLS verification, time/size limits and malware/content inspection.
5. Use media/engine-specific CPU, memory, PID, disk, duration, output-size, entity-count and concurrency limits. Kill process trees on cancellation/timeout and clean ephemeral data.
6. Treat Godot scenes/resources/scripts as active content. Only load approved, pinned resource manifests; do not deserialize untrusted `.tres`/`.res` or arbitrary Variant data.
7. Keep save state tenant-isolated and data-only where possible. Bind every artifact to authenticated owner, Agent Run, skill version, approval/consent and audit receipt.
8. Preserve durable lifecycle semantics: idempotency, lease fencing, heartbeat, cancellation, retry policy, checkpoint recovery, cleanup and owner-checked artifact download.
9. Hash integrity does not establish license rights, attribution completeness, dependency safety or runtime correctness. Those gates remain open.

## Integrity and disposition

- Reviewed ledger rows: **121–170 (50 files)**.
- Fetched Git blob SHA matches ledger: **50 / 50**.
- Interim dispositions: **50 DEFER; 0 final approvals**.
- No source execution or runtime verification performed.

Cumulative manually reviewed executable-source payloads in batches 001–013: **170 / 875 (19.43%)**. P1 remains OPEN. Continue with the next 50 consecutive executable-source rows (171–220). After all 875 executable files, proceed to configuration/schema, references/dependencies, assets/fonts and SBOM audits, then determine final per-file dispositions from the complete evidence.
