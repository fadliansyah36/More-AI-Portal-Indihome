# P1 Executable Payload Manual Review — Batch 04

Date: 2026-11-18
Branch: `main`
Pinned source: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
Scope: 8 Blender expert/export/geometry-node/Grease Pencil/hair/hard-surface executable source files.
Method: immutable-source static inspection of entrypoints, imports, process/file/network boundaries, Blender operator effects and output paths. No Blender process, script, render, test, external command, package installation or project file was executed.

## Per-file review and disposition

| # | Source path | Git blob SHA | Bytes | Raw SHA-256 | Finding | Disposition |
|---:|---|---|---:|---|---|---|
| 1 | `skills/dcc/blender/scenario-blender-expert/scripts/bx_audit.py` | `ad9325f3b03b5cd04eb3762878446bd42709ad8c` | 31886 | `35d86b16dae8bfff583e22d852631888f938ac695f15afe25690e256fa13f9db` | Imports arbitrary user-supplied model formats into a factory-reset Blender scene; optional JSON report path writes to caller-specified filesystem path. Untrusted file parser boundary requires isolation. | DEFER |
| 2 | `skills/dcc/blender/scenario-blender-expert/scripts/bx_gui.py` | `6c1d98166adce8442ed45557becd5be1352849a2` | 8951 | `d5c020f27d2714f7f773da30cfa190017be453a621bb45f1eccececa3a33d60c` | Drives real GUI paint/sculpt brushes, viewport redraw and screenshot operations in an already-open Blender desktop session. Not headless or tenant-isolated. | DEFER |
| 3 | `skills/dcc/blender/scenario-blender-expert/scripts/bx_review.py` | `0b7cbe320ef6a9bdc1fb220ebd9933cd68f786bd` | 15644 | `5b274739b2a8ed26b3fe144e0d6ed15e51aee8e52b2852b51d5f6f464e939106` | Creates temporary render scenes, writes contact sheets/legends and renders images/video to caller-selected paths. Requires bounded render resources and per-run output confinement. | DEFER |
| 4 | `skills/dcc/blender/scenario-blender-export/scripts/bx_export.py` | `1f303a91e5ed4a2ba98f7361eb0e8b36f09dafdb` | 36318 | `0f9ed709d91b4122424bb9fae54c6432ca30f9e12691caf0c59a472cdb03cc40` | Export/round-trip/batch CLI launches the Blender binary via argv-based `subprocess.run` with timeout, but accepts source/destination directories, imports every matching model file and writes exports/reports. Fixed argv is safer than shell interpolation but not tenant isolation. | DEFER |
| 5 | `skills/dcc/blender/scenario-blender-geometry-nodes/scripts/bx_gn.py` | `108e25a60216461be14f3f2b17c481b049311363` | 57043 | `b325317f54e1e944f33f1af91e141c20bd5ebe7d3a3c487738fa70fd725639e0` | Builds/mutates Geometry Nodes, simulation caches and renders snapshot/legend files in the active Blender scene. | DEFER |
| 6 | `skills/dcc/blender/scenario-blender-grease-pencil/scripts/bx_gp.py` | `2f45637521d148300cb8dc2f1cf300dab8be7649` | 47192 | `60333346c7ab8c894870d00e6fac692496f9a76ff89595b585a41a22a055e07c` | Creates/mutates Grease Pencil drawing data, line-art bake and render outputs; GUI operators are also used for editing actions. | DEFER |
| 7 | `skills/dcc/blender/scenario-blender-hair/scripts/bx_hair.py` | `2a9ade25985c5981887f36a78637a68a16c300cf` | 55125 | `903ab71cc8ad4a45b90fa1c639f981a6c9ddbc29c91627296675e5d203e22512` | Builds hair curves/node groups, applies modifiers and renders review assets into an output directory. CPU/render cost and path confinement required. | DEFER |
| 8 | `skills/dcc/blender/scenario-blender-hard-surface/scripts/bx_hardsurface.py` | `a5837ecbece3efc7073f233a241db398e870081b` | 69529 | `a7eb60b356c16609573ea8bb0005cd1278e908dcd7593eb7ff1f749ceb7b9999` | Geometry/mesh editing, bevel/boolean/shading QA and render operations mutate the active Blender scene. | DEFER |

All eight Git blob identities, byte sizes and raw SHA-256 values match the selected-payload audit ledger. The hashes are reproduced from committed evidence; this review did not execute the source to calculate them.

## Security and architecture findings

- `bx_export.py` is the highest-risk file in this batch because it starts a second Blender process. Its subprocess call uses a fixed executable and argv list with a timeout, not shell interpolation; however, a batch request can cause many arbitrary model files from a caller-provided directory to be imported and exported. Treat every model parser and Blender child process as untrusted workload.
- `bx_audit.py` uses Blender import operators for GLB/GLTF/FBX/OBJ/STL/PLY/USD variants. File-format parsing must happen in a disposable, non-root, resource-limited process with a read-only input mount and no host secrets/network.
- `bx_gui.py` requires a real interactive desktop session and changes brush state/viewport; it is not suitable for shared API/worker execution.
- `bx_review.py`, `bx_gn.py` and `bx_hair.py` create/render files, images, animation or simulation state. Enforce output path canonicalization, per-run quotas, render frame/resolution limits, cancellation and artifact scanning.
- `bx_gp.py` and `bx_hardsurface.py` are local scene-mutating DCC operations. They are not FastAPI route logic or direct customer-callable tools.
- No actual external network client or credential flow was identified in the inspected code. Blender node/socket names triggered superficial keyword matches only; they are not network sockets.
- No dynamic `exec/eval/compile` pattern was identified in these eight files. This is not a malware scan or a guarantee about Blender binary/add-ons/importer dependencies.
- All eight remain DEFER pending a dedicated, isolated Blender adapter and exact dependency/license/vulnerability review. No active MoreAI runtime import is approved.

## Review coverage after this batch

- Entrypoints: 229/229.
- Executable source: **39/875** manually reviewed (31 prior + 8 in this batch); 836 remain.
- Configuration/schema: 13/69.
- Reference documents: 17/726.
- Parser reference candidates: 148/148 path-triaged; not equivalent to full content review.
- Selected payload SHA-256: 1,941/1,941 verified; operational disposition 19 ARCHIVE_ONLY / 1,922 DEFER FINAL_HOLD.
- Full source-tree disposition: 3,919 rows = 111 COPY (pristine OpenManus archival snapshot only), 388 ARCHIVE_ONLY FINAL, 7 ARCHIVE_ONLY FINAL_BLOCKED, 2,454 DEFER FINAL_HOLD, 959 directory rows NOT_APPLICABLE.

P1 remains **IN_PROGRESS / NOT ACCEPTED**. No source execution, package installation, tests, builds, provider calls, Supabase writes/migrations, staging or deployment occurred.
