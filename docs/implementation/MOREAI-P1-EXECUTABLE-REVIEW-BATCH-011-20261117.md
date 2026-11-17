# P1 Executable Payload Review — Batch 011 (20 files) — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Target branch: `main`
Source repository: `scenario-labs/skills`
Pinned source commit: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Scope and review method

This batch covers the next 20 consecutive `executable-source` rows (ledger rows 51–70 in the executable-source ordering) after batch 010. All 20 files were fetched from the pinned commit. Static source inspection and targeted pattern scans covered process execution, network/socket use, dynamic code/import, filesystem access, Godot resource loading and DCC application boundaries.

No source was imported or executed. No Godot, ZBrush, Maya, Blender or other DCC/game-engine runtime was launched. No package was installed; no tests, builds, renders, workers, providers, staging, deployment, migration or Supabase operation was run.

## Reviewed files and interim decisions

| # | File | Bytes | Static observations | Interim disposition |
|---:|---|---:|---|---|
| 51 | `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_stroke.py` | 21,778 | Stroke-string and canvas/model coordinate helpers; convention JSON read/write; ZBrush-dependent play operation | DEFER |
| 52 | `skills/dcc/zbrush/scenario-zbrush-hard-surface/scripts/zb_hardsurface.py` | 108,695 | Hard-surface toolkit; imports expert scripts by manipulating `sys.path`; reads reference/config files; calls ZBrush toolkit | DEFER |
| 53 | `skills/dcc/zbrush/scenario-zbrush-paint-render/scripts/zb_paint.py` | 73,722 | Polypaint/mask/render pipeline; invokes external FFmpeg through `subprocess.run`; image reads/writes and generated outputs | DEFER / EXTERNAL PROCESS |
| 54 | `skills/dcc/zbrush/scenario-zbrush-pose-print/scripts/zb_pose.py` | 56,739 | ZBrush pose/document operations; filesystem outputs; expert module path manipulation; ZBrush-side execution | DEFER |
| 55 | `skills/dcc/zbrush/scenario-zbrush-pose-print/scripts/zb_print.py` | 67,138 | Agent-side mesh/print analysis and 3MF data generation; filesystem OBJ/mesh reads | DEFER |
| 56 | `skills/dcc/zbrush/scenario-zbrush-retopology-export/scripts/zb_retopology_export.py` | 145,630 | Retopology/export pipeline; filesystem reads/writes; `importlib.import_module` for expert modules; ZBrush calls | DEFER / DYNAMIC MODULE BOUNDARY |
| 57 | `skills/dcc/zbrush/scenario-zbrush-sculpting/scripts/zb_sculpt.py` | 98,344 | Agent-side stroke planning, NumPy/PIL image processing, calibration JSON and output files; mutates `sys.path` | DEFER |
| 58 | `skills/dcc/zbrush/scenario-zbrush-stylized/scripts/zb_stylized.py` | 80,333 | Stylized shape/hair operations; PIL image processing, output directories and dynamic expert module imports | DEFER / DYNAMIC MODULE BOUNDARY |
| 59 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/audit_2d.gd` | 4,737 | Godot scene audit; loads PackedScene resources and traverses directories | DEFER |
| 60 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/dual_grid.gd` | 2,615 | Godot @tool TileMap dual-grid editor/runtime helper | DEFER |
| 61 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/follow_camera_2d.gd` | 4,625 | Camera2D movement/follow behavior | DEFER |
| 62 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/parallax_tools.gd` | 1,606 | Parallax2D scene construction helper | DEFER |
| 63 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/pixel_light.gdshader` | 617 | Canvas-item pixel-snapped lighting shader | DEFER |
| 64 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/pixel_viewport.gd` | 2,732 | Control/SubViewport pixel-perfect presentation helper | DEFER |
| 65 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/platformer_body.gd` | 3,753 | CharacterBody2D platformer movement; preloads tuning resource | DEFER |
| 66 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/platformer_tuning.gd` | 2,681 | Resource containing platformer movement tuning values | DEFER |
| 67 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/sprite_frames_builder.gd` | 4,021 | Reads manifest via FileAccess; resolves/loads Resource paths; builds SpriteFrames | DEFER |
| 68 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/terrain_tools.gd` | 4,090 | TileMapLayer terrain construction and audit helper | DEFER |
| 69 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/tileset_builder.gd` | 8,019 | Builds TileSet from config/atlas; creates directories and loads texture resource | DEFER |
| 70 | `skills/game-engines/godot/scenario-godot-2d/scripts/agentkit/2d/topdown_body.gd` | 2,418 | CharacterBody2D top-down movement helper | DEFER |

## Findings and risk boundaries

### ZBrush payloads (8 files)

- `zb_paint.py` invokes FFmpeg via `subprocess.run` for media assembly. The executable path must be fixed by the worker image, arguments constructed from validated server-side values, and frame count/resolution/duration/output size bounded. Never pass user-controlled command fragments or arbitrary binary paths.
- `zb_retopology_export.py` and `zb_stylized.py` use dynamic expert-toolkit imports. Replace arbitrary module selection with a fixed server-side registry and pin the imported toolkit version. The dynamic import mechanism must not be reachable through customer payloads.
- Multiple files manipulate `sys.path`, read calibration/config/reference files, write artifacts and invoke ZBrush APIs. Keep the ZBrush-specific half in a separate licensed, digest-pinned, ephemeral worker. Agent-side pure-Python analysis must remain separate from application automation.
- `zb_stroke.py`, `zb_pose.py`, and other DCC tools can alter documents or issue drawing/pose operations. Run only on server-generated copies with explicit operation capabilities; never mutate a customer's original artifact implicitly.
- `zb_print.py` reads mesh data and constructs manufacturing-oriented reports/3MF content. Bound file size, vertex/face counts, parser memory and CPU; reject malformed or path-traversal inputs.
- No direct outbound HTTP client was demonstrated by the narrow scans. This is not a complete transitive dependency or egress audit.

### Godot 2D payloads (12 files)

- The Godot scripts inspected are primarily scene, camera, tilemap, shader, character movement and resource-construction helpers. The narrow scans did not demonstrate subprocess execution, network clients, dynamic code execution or dynamic imports in these 12 files.
- `audit_2d.gd` loads scene resources and traverses directories. Any future server-side use must constrain resource roots and reject arbitrary `res://` paths supplied by a customer.
- `sprite_frames_builder.gd` reads a manifest and loads resources. Treat manifest paths, frame dimensions/counts, FPS, loop settings and referenced resources as untrusted until schema-validated and confined to an approved project workspace.
- `tileset_builder.gd` creates output directories and loads texture resources from config. Validate config schema, texture ownership, resource path containment, atlas dimensions, tile counts and output paths.
- `dual_grid.gd` is marked `@tool`; editor-time scripts should not be loaded into a privileged server process or executed against a shared editor project.
- The remaining Godot files are largely runtime behavior components/shader code. They still require a Godot 4.7.2 compatibility/license/dependency review and resource limits before import into any skill execution environment.
- Static pattern scans do not establish absence of all unsafe behavior; complete content, referenced-scene, addon, dependency and engine API review remains open.

## Required adaptation boundary

- Keep all 20 payloads disabled pending full content, dependency, license and runtime review.
- Separate DCC application automation (ZBrush) from game-engine project generation (Godot); do not execute either inside FastAPI.
- Pin distinct worker images/engine versions and dependencies; use non-root ephemeral workers, no host mounts/secrets, default-deny egress, CPU/RAM/PID/disk/time quotas and forced process-tree termination.
- Use fixed registries for modules, operations and external binaries. Reject arbitrary code, module names, executable paths and command fragments.
- Accept only schema-validated manifests/configs with bounded files, resources, dimensions, frames, mesh complexity and output quotas.
- Resolve all project/resource paths server-side within the per-run workspace; enforce canonical path containment, symlink-safe operations and cleanup.
- Bind every job/artifact to authenticated owner, Agent Run and approved skill version; preserve durable cancellation, timeout, lease fencing, audit receipts and owner-checked artifact downloads through existing FastAPI/Supabase architecture.
- Quarantine and validate generated images, videos, meshes, scenes and archives before publication.

## Integrity and disposition

The audit ledger reports expected file sizes and Git blob SHA values for these 20 rows as verified. The fetched content SHA values were consistent with the ledger's recorded Git blob identifiers where inspected. This is source integrity evidence only; it is not a license grant, complete security review, runtime compatibility proof or production approval.

**Batch 011: 20 additional executable payloads reviewed statically; all 20 remain DEFER.** No preliminary ledger row was promoted to final disposition.

Cumulative manually reviewed executable payloads in batches 001–011: **70 / 875 (8.00%)**. P1 remains OPEN. Continue with the next 20 executable-source ledger rows, then complete the remaining configuration/schema, references/dependencies, assets/fonts and SBOM work before final per-file disposition.
