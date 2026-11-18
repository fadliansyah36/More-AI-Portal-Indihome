# P1 Executable Payload Manual Review — Batch 03

Date: 2026-11-18
Branch: `main`
Pinned source: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
Scope: 8 executable-source files from Blender animation/blockout capability.
Method: immutable source retrieval and static inspection of imports, API calls, file/process/network boundaries and output behavior. No Blender process, Python script, render, test, package installation or project file was executed.

## Per-file review and disposition

| # | Source path | Git blob SHA | Bytes | Raw SHA-256 | Finding | Disposition |
|---:|---|---|---:|---|---|---|
| 1 | `skills/dcc/blender/scenario-blender-animation/scripts/bx_anim.py` | `9f0a3323facf18d66be00a909277e078f59fad6d` | 103252 | `7df38e0d5c3349fc66e228aa981c5da7bbeaed3af90586a235f1a5b7e742dfe2` | Blender animation API; writes generated image/legend outputs and invokes Blender render operators. No external network/process invocation observed in static pattern review. | DEFER |
| 2 | `skills/dcc/blender/scenario-blender-blockout/scripts/bx_blockout.py` | `981552ee4bba664ba01d41e852ac5741e6bbd93b` | 35735 | `fd5011762c6c58b51495a21522be6d572d47dd574510eedba47c0e1742a3e95a` | Blender scene builder/auditor; includes guarded scene mutation and save-copy helper writing a caller-selected folder. | DEFER |
| 3 | `skills/dcc/blender/scenario-blender-blockout/scripts/bx_kits.py` | `6f5f525f84120ad80856f7a66cbc74883033947a` | 66846 | `17cc4ea523106604c07327a291a921cdff2c20636896d2d8b84724fff7c9a992` | Blender mesh/material/figure/crowd/vehicle builders; mutates the active Blender DataModel. No standalone network/process entrypoint observed. | DEFER |
| 4 | `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex1_watchmaker.py` | `020f5b8178cf1c0ed3d51d9abb7cf38a27fccaec` | 8683 | `bfa426be719790c6d24e8247c68ac8ff470e6b1b2842c9f649d82b35fc67dab9` | Example scene generator for an interior/workshop; creates Blender geometry, materials, lighting and animation. | DEFER |
| 5 | `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex2_saltflat.py` | `86cf90a8c1e12be5ec44c4a2e792445797aed710` | 8899 | `69a612beaa14ba16c8e901df16b3a8db60460f657b2468f3d3e3973cffb94a08` | Example scene generator for a salt-flat/exterior sequence; Blender scene and animation mutation only. | DEFER |
| 6 | `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex3_bridge.py` | `389ec244ca9400e36d33c4f95b3d3f4f3d45f728` | 12567 | `dd8f51eb0ce18eae45d6287204cc9976801fbd90c9e5f80efdf06a2b866b55a9` | Example scene generator for a bridge/interior action sequence; creates objects, cameras, animation and audit outputs. | DEFER |
| 7 | `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex4_sky_islands.py` | `345a61b3050467460a734ff790ef7eeb4a6decad` | 13572 | `11552e6498ebd1f0b82b59bb1bf00e94602129e8ca6854e76daa24a3c76fa776` | Example scene generator for a multi-character/fantasy sequence; creates large object sets, animation and cameras. | DEFER |
| 8 | `skills/dcc/blender/scenario-blender-blockout/scripts/examples/ex_common.py` | `011de26be6541d0b925c4c7dc496a199b1433fa3` | 4319 | `cc252e8d63499dc5f13069ca6ff9f59b89a8971a0712429cc0e4f57ff5b91f8a` | Shared CLI setup; clears factory scene objects, writes stats/stills and saves a .blend file to caller-provided output directory; can invoke playblast helper. | DEFER |

All eight Git blob identities, byte sizes and SHA-256 values match the committed selected-payload evidence ledger. SHA-256 values are reproduced from that ledger; this batch did not recompute hashes by executing source code.

## Security and capability boundary

- The reviewed modules are Blender-hosted DCC tooling, not general-purpose FastAPI service modules.
- Their operations mutate an active scene, create large geometry/animation data, render stills/playblasts, create output directories, write stats/legend/image files and save Blender project files.
- The shared example setup accepts an output directory and saves generated assets there. A production adapter must canonicalize and confine that path to a per-run workspace; no host filesystem path may be customer-controlled.
- Rendering and scene construction need CPU/memory/time/output quotas, Blender version pinning, non-root isolated process/container, no ambient host credentials, no network by default, per-run scratch storage, cancellation/process-tree termination and artifact scanning.
- No literal credentials, external provider calls, subprocess invocation or dynamic-code execution were identified in the eight inspected source files. This is a static source observation, not malware clearance or a guarantee about Blender add-ons/runtime dependencies.
- The examples are instructional scene fixtures. They should not be installed as customer-callable tools. Keep them DEFER until the final disposition process explicitly chooses archive-only versus an isolated demo/test fixture boundary.
- No code is approved for COPY or ADAPT into active MoreAI runtime by this batch.

## Review coverage after this batch

- Entrypoints: 229/229 manually reviewed.
- Executable source: **31/875** manually reviewed (23 prior + 8 in this batch); 844 remain.
- Configuration/schema: 13/69 manually reviewed.
- Reference documents: 17/726 manually reviewed.
- Parser reference candidates: 148/148 path-triaged; this is not semantic review of all reference documents.
- Selected payload: 1,941/1,941 SHA-256 verified; current operational disposition 19 ARCHIVE_ONLY / 1,922 DEFER FINAL_HOLD.
- Full pinned source tree: 3,919 rows; current ledger 111 COPY (pristine OpenManus archival snapshot), 388 ARCHIVE_ONLY FINAL, 7 ARCHIVE_ONLY FINAL_BLOCKED, 2,454 DEFER FINAL_HOLD, 959 directory rows NOT_APPLICABLE.

P1 remains **IN_PROGRESS / NOT CLOSED**. The 31 reviewed executable files remain DEFER. Exact-version package license/artifact and vulnerability review, remaining executable/config/reference review, fonts/model/media provenance, full SBOM reconciliation and product-owner acceptance remain outstanding.

No source execution, package installation, tests, build, provider call, Supabase mutation/migration, staging or deployment occurred.
