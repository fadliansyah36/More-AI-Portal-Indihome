# P1 Executable Payload Manual Review — Batch 05

Date: 2026-11-18
Branch: `main`
Pinned source: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
Scope: 7 Blender DCC source modules and 1 Maya animation module.
Method: immutable source retrieval and static inspection of imports, DCC API effects, file/process/network boundaries and CLI/output handling. No Blender/Maya process, scene, render, script, test, package installation or project file was executed.

## Per-file review and disposition

| # | Source path | Git blob SHA | Bytes | Raw SHA-256 | Finding | Disposition |
|---:|---|---|---:|---|---|---|
| 1 | `skills/dcc/blender/scenario-blender-lighting-rendering/scripts/bx_light.py` | `0fc51f7dda990dc2e4ec95943ec84590e02e1149` | 102909 | `6f6624765f2afdfebc0efc4b77313fee3cacef9e7d983bcb3a95c88c8fa2f8f2` | Blender lighting/compositor/render pipeline; reads EXR through OpenImageIO, writes PNG/EXR and legend files, mutates render/color/compositor state. | DEFER |
| 2 | `skills/dcc/blender/scenario-blender-previs-storyboard/scripts/bx_previs.py` | `462fb2eeaa7b07809e6cc9f41e4d5aa6e5854dfd` | 69531 | `8fdbcfb77f42bbfaac403bff5a163d0a7f741e2813c671172c5f068f607572ad` | Storyboard/animatic tooling; generates and saves multiple stills/contact sheets, creates temporary render scenes and Rigify proxies. | DEFER |
| 3 | `skills/dcc/blender/scenario-blender-retopology/scripts/bx_retopo.py` | `f7e6e92257107f939a9b1fe84c3cefbd8dd5f85a` | 128581 | `81bc2063c7c9ebe69c80b54041d1b70ce7c2fd47538a1d475cc0943f785f3266` | Large mesh/topology pipeline; voxel/quadriflow remesh, modifier application, UV/topology changes and optional rendered output. | DEFER |
| 4 | `skills/dcc/blender/scenario-blender-rigging/scripts/bx_rig.py` | `1f172e5091af838bb33a9573680479facc0ebe03` | 139639 | `33a0a60ca321245b9016938953a884b76f8ac78fd34f4d11d42a8135881749ce` | Rigify/metarig/weights/pose pipeline; saves a .blend copy and spawns Blender via fixed argv `subprocess.run` for dependency-cycle check, timeout 300s, static `--python-expr`. | DEFER |
| 5 | `skills/dcc/blender/scenario-blender-sculpting/scripts/bx_sculpt.py` | `9f52ea9692c52508c09e11a2c4f812199ee52c20` | 79076 | `3921f0a2fde493be94ae0c454d3e5cafc1433e0dc5be08adc6763d78a3d4f603` | Mesh-data sculpt/mask/remesh operations; mutates active Blender objects and may render review images. | DEFER |
| 6 | `skills/dcc/blender/scenario-blender-texturing-shading/scripts/bx_materials.py` | `674d16825dde88f6dea54133ad2b204c4429f64c` | 87244 | `15877d81bea8d2c95e1393b7c6ce8c96182fdb1a8d26dfa6bfbaf2d88886e72b` | PBR material/node graph builder; consumes texture paths, mutates materials/nodes, writes baked texture outputs and render QA assets. | DEFER |
| 7 | `skills/dcc/blender/scenario-blender-uv-baking/scripts/bx_uvbake.py` | `5067d81fdf19ccc6f41020e11fc18e22efada358` | 107561 | `fea0c2ebaf3a82897e28750afdea613d96949ca0dc018db8c3f88bb023a04451` | UV unwrap/pack, mesh modifier and bake pipeline; mutates scene and writes baked texture/render outputs. | DEFER |
| 8 | `skills/dcc/maya/scenario-maya-animation/scripts/mx_anim.py` | `1a2d341b3ec0f702c3a233969a01056f9c34d9d9` | 111834 | `8f9a8527cc4d558f29e0f968bb0ff6ae44a68652b0b51cb9a4ced897f263da1e` | Maya animation/keyframe analysis; reads caller-provided JSON plan and WAV audio, writes plots/gates JSON, and can invoke GUI playblast via sibling Maya toolkit. | DEFER |

All eight Git blob identities, byte sizes and SHA-256 values match the selected-payload audit ledger. Hashes are reproduced from committed evidence, not recalculated by executing the source.

## Security and architecture findings

- All eight are DCC-specific scene/model manipulation, not generic MoreAI API, customer UI or Agent Runtime modules.
- Blender modules perform expensive mesh remeshing, geometry, node, rig, animation and render operations. Require strict CPU/memory/time/frame/resolution quotas, non-root isolated Blender worker, per-run scratch workspace, canonical path allowlists, cancellation and process-tree termination.
- `bx_rig.cycle_check` starts Blender with `subprocess.run` using a fixed executable and argv list (no shell), a static Python expression and 300-second timeout. The saved `.blend` input remains untrusted and must be mounted read-only; the child process needs resource limits and output/log capture.
- `bx_light` opens EXR subimages via OpenImageIO; `bx_materials` and `bx_uvbake` consume texture paths and write baked outputs. Image/texture parsers require the same sandbox boundary as user-uploaded media.
- `bx_previs` writes per-shot stills/contact sheets and generates Rigify objects; `bx_retopo` and `bx_sculpt` mutate meshes and can consume substantial CPU/memory; these must never run in FastAPI request handlers.
- `mx_anim` reads plan JSON and WAV data and writes files under an output directory. It lazily calls Maya commands and sibling `mx_run`, `mx_review` and `mx_bridge` capabilities; those dependencies require their own license, code and security review before any adapter decision.
- Static pattern review found no external HTTP/network client, credential access, dynamic `exec/eval` or shell command. `bx_rig` has one fixed-argv Blender subprocess call. This is not a malware scan or runtime proof.
- All files remain DEFER pending DCC license/redistribution closure, isolated worker design, dependency provenance and source-wide security review. No code is approved for active import.

## Review coverage after this batch

- Entrypoints: 229/229.
- Executable source: **47/875** manually reviewed (39 prior + 8 in this batch); 828 remain.
- Configuration/schema: 13/69.
- Reference documents: 17/726.
- Selected payload SHA-256: 1,941/1,941 verified; 19 ARCHIVE_ONLY / 1,922 DEFER FINAL_HOLD.
- Full source-tree disposition: 3,919 rows = 111 COPY (pristine OpenManus archive only), 388 ARCHIVE_ONLY FINAL, 7 ARCHIVE_ONLY FINAL_BLOCKED, 2,454 DEFER FINAL_HOLD, 959 directory rows NOT_APPLICABLE.
- Exact OSV query coverage: 1,824 unique npm PURLs + 112 unique PyPI PURLs; 49 vulnerable coordinates and 247 advisory associations. See the P1 OSV reconciliation report and CSV risk registers.

P1 remains **IN_PROGRESS / NOT ACCEPTED**. No source execution, package installation, tests/builds, provider calls, Supabase writes/migrations, staging or deployment occurred.
