# P1 Executable Payload Review — Batch 012 (50 files) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Target branch: `main`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope and method

Reviewed the next 50 consecutive `executable-source` entries from the canonical P1 ledger: executable-source ordering rows 71–120, immediately following batch 011. Every source file was fetched from the pinned Scenario Skills commit. The fetched Git blob SHA matched the ledger SHA for all 50 files.

Static inspection covered process invocation, network/socket patterns, dynamic code/import, filesystem operations, Godot resource loading, project path handling, and engine/runtime boundaries. This is a targeted static review, not a complete semantic, transitive dependency, license or runtime audit.

No source was imported or executed. No Godot, ZBrush, Maya, Blender or other runtime was launched. No package installation, tests, builds, renders, workers, providers, staging, deployment, migration or Supabase operation was performed.

## File inventory and interim disposition

| Ledger row | File(s) | Interim disposition |
|---:|---|---|
| 71 | `skills/game-engines/godot/scenario-godot-2d/scripts/gd_2d.py` | DEFER |
| 72–87 | `scenario-godot-3d-world/scripts/agentkit/world/{post_import_prop, runtime/cell_streamer, runtime/third_person_controller, world_audit, world_blockout, world_common, world_import, world_kit, world_mesh, world_player, world_project, world_scatter, world_stream, world_terrain, world_terrain3d}.gd`; plus `scenario-godot-3d-world/scripts/gd_world.py` | DEFER |
| 88–101 | `scenario-godot-animation/scripts/agentkit/animation/{anim_audit, anim_capture, anim_cutscene, anim_ik, anim_import, anim_motion, anim_rig, anim_setup, anim_tree, anim_tween, cutscene_director, foot_placer, locomotion_state, pose_persist}.gd` | DEFER |
| 102 | `skills/game-engines/godot/scenario-godot-animation/scripts/gd_anim.py` | DEFER |
| 103–109 | `scenario-godot-architecture/scripts/agentkit/architecture/{arch_audit, bench, build_catalog, pack_probe, scaffold, setup_input, validate_data}.gd` | DEFER |
| 110 | `skills/game-engines/godot/scenario-godot-architecture/scripts/gd_architecture.py` | DEFER / EXTERNAL PROCESS |
| 111–120 | `scenario-godot-architecture/scripts/templates/core/{combat/damage_info, combat/health_component, combat/hitbox_3d, combat/hurtbox_3d, data/item_catalog, data/item_definition, events/events, input/input_actions, input/input_remap, inventory/inventory}.gd` | DEFER |

All 50 ledger rows remain **DEFER**. No row is promoted to a final disposition.

## Findings

### 1. Godot 2D and 3D world tools

- `gd_2d.py` installs a toolkit into a Godot project and modifies Python `sys.path`; it also creates directories and handles image files. Keep project roots explicit and confined; pin imported expert toolkit modules.
- The 3D world helpers use `load`, `ResourceLoader`, `FileAccess`, `DirAccess`, `ProjectSettings.globalize_path`, and user-supplied job arguments for scene/resource/output paths. These APIs can instantiate scenes, import assets, create directories and write generated scenes/data.
- `world_blockout.gd`, `world_import.gd`, `world_kit.gd`, `world_mesh.gd`, `world_player.gd`, `world_scatter.gd`, `world_stream.gd`, `world_terrain.gd`, and `world_terrain3d.gd` are project-mutating build helpers. Treat job arguments and resource paths as untrusted. A string beginning with `res://` is not itself a security boundary.
- `world_project.gd` traverses project directories, reads source files and reloads scripts. Restrict traversal to a per-run project root and exclude symlinks, hidden/system paths and oversized trees.
- `cell_streamer.gd` uses threaded resource loading and instantiates PackedScenes. Bound concurrent requests, scene count, resource size and memory; cancellation must stop pending work and clean up references.
- `gd_world.py` invokes `cp -c` using `subprocess.run` for APFS clone behavior and manipulates project paths/directories. This introduces an OS-specific external-process boundary. Use a fixed executable/argument vector, no shell, validated source/destination roots, quotas and process timeouts; provide a safe copy fallback only if explicitly designed and reviewed.
- `post_import_prop.gd` reads a JSON manifest and performs post-import configuration. Validate schema, referenced files, resource ownership and allowed import settings before loading.
- Godot engine scripts must remain in an isolated, version-pinned Godot worker; they must not execute inside FastAPI or a shared API process.

### 2. Godot animation tools

- Animation helpers load and instantiate project scenes from job-provided paths, inspect imported animation resources, create/modify rigs and scenes, and write generated artifacts.
- `anim_import.gd` reads import configuration and creates output directories; constrain source assets, importer options, subresource overrides and output paths to the authorized run workspace.
- `anim_rig.gd` creates directories and writes scene/GLB outputs. Enforce file size, bone count, animation count, hierarchy depth, duration, sample rate, texture limits and artifact quotas.
- `anim_cutscene.gd`, `anim_ik.gd`, `anim_motion.gd`, `anim_setup.gd` and `anim_tree.gd` load/instantiate scene paths derived from job arguments. Use fixed operation IDs and typed schemas rather than arbitrary script paths or unconstrained scene references.
- `gd_anim.py` installs animation scripts into a Godot project and manipulates `sys.path`. Resolve imported module paths from a pinned internal registry; do not allow customer-provided module names or paths.
- The remaining animation components are scene/animation logic. Absence of a suspicious pattern in a narrow scan is not a security or runtime approval.

### 3. Godot architecture and template scripts

- `arch_audit.gd`, `build_catalog.gd`, `pack_probe.gd`, `scaffold.gd`, `setup_input.gd` and `validate_data.gd` traverse directories, load scripts/resources, inspect project structure or create/update project configuration. Restrict all roots and outputs to a per-run workspace and validate every resource class and path.
- `gd_architecture.py` invokes Godot through `subprocess.run` and manipulates project files/directories. Treat it as a separate worker adapter: fixed Godot binary, argument allowlist, no shell, bounded logs/output, environment allowlist, process timeout/tree kill, no host mounts/secrets and default-deny egress.
- The combat, data, events and input template scripts (rows 111–120) are reusable Godot gameplay components. `input_remap.gd` persists runtime bindings to `user://input_bindings.json`; this is application-local persistence, not suitable for cross-customer shared storage. If persisted in a hosted worker, use an isolated per-run user data directory and never reuse it across tenants.
- Template scripts are not independently deployable skills: review their consuming scenes, project settings, addons, class registrations, licenses and dependency chain before bundling.

## Security and architecture requirements

1. Keep Godot execution out of FastAPI. Dispatch only typed, authorized jobs through the existing durable Agent Run/worker lifecycle.
2. Use separate digest-pinned Godot worker images for 2D, 3D world, animation and architecture operations where dependency sets differ. Do not install Godot or DCC dependencies in the API image.
3. Run non-root, ephemeral workers with no host filesystem mounts, no inherited secrets, default-deny network egress, CPU/RAM/PID/disk/time limits, bounded concurrency and forced process-tree termination.
4. Reject arbitrary script paths, source code, command strings, executable paths and dynamic module names from customer inputs. Expose a narrow operation registry with strict Pydantic schemas and per-skill capability permissions.
5. Canonicalize and confine all project/resource/input/output paths to the owner- and run-scoped workspace. Prevent traversal, symlink escapes, absolute-path injection and writes to shared templates.
6. Validate GLB/GLTF, textures, images, scene resources, manifests and generated archives before import. Bound geometry, hierarchy, animation duration, frames, dimensions, resource counts and total output size.
7. Bind every operation and artifact to authenticated owner, Agent Run, pinned skill version, consent/approval and audit receipt. Preserve cancellation, timeout, lease fencing, cleanup and owner-checked downloads through FastAPI/Supabase.
8. Treat source hashes as integrity evidence only. License, NOTICE, attribution, dependency and provenance gates remain separate.

## Integrity and disposition

- Ledger SHA matched fetched Git blob SHA: **50 / 50**.
- Reviewed executable-source rows: **71–120**.
- Interim disposition: **50 DEFER; 0 final approvals**.
- This batch adds source-level risk evidence; it does not approve importing, enabling, executing or publishing any of these skills.

Cumulative manually reviewed executable-source payloads in batches 001–012: **120 / 875 (13.71%)**. P1 remains OPEN. Continue with the next 50 consecutive executable-source rows (121–170). Once all 875 executable payloads are reviewed, proceed to configuration/schema, references/dependencies, assets/fonts and SBOM audits. Final per-file decisions must wait until all relevant evidence is available.
