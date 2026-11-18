# P1 Executable Payload Manual Review — Batch 07

Date: 2026-11-18
Branch: `main`
Pinned source: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
Scope: 4 Maya DCC source modules and 4 ZBrush source modules.
Method: immutable-source static inspection of DCC operations, child-process/job runner, MEL and plugin boundaries, local filesystem and source-declared runtime verification. No Maya, mayapy, ZBrush, GoZ, plugin, render, script, package installation or scene was executed.

## Per-file review and disposition

| # | Source path | Git blob SHA | Bytes | Raw SHA-256 | Finding | Disposition |
|---:|---|---|---:|---|---|---|
| 1 | `skills/dcc/maya/scenario-maya-modeling/scripts/mx_modeling.py` | `8e17b983c93131ed93c14f3e6cef8914dcee89c2` | 82559 | `efb87ad722c5dd9c59ffa9b00dcdf002fb93737bdde45ab544ecd86bccba0ebf` | Maya modeling/mesh/curve/transform operations, plugin and scene mutation; output reports and project assets are written locally. | DEFER |
| 2 | `skills/dcc/maya/scenario-maya-pipeline-scripting/scripts/mx_pipeline.py` | `2dd0f9a687170091fc5cc1ee8cc9c6d4c33bf11e` | 118323 | `38ffab582f349d60062c317fabce9a4300cc10ff6868ad5d5e27499ea52cf468` | Batch pipeline delegates to `mx_run.run_subprocess` per scene (default 900s timeout; process isolation; script nodes off by default), writes JSON/CSV reports, and executes generated FBX MEL option commands. | DEFER |
| 3 | `skills/dcc/maya/scenario-maya-retopology-uv/scripts/mx_retopology_uv.py` | `8d2491bb2d4a5b98504016390c2f806c1a3dd44d` | 151741 | `8a22fcb25d1a86bd401a52a4c8fa5daad01dfe707541e6cb339abcadac77fce1` | Maya topology/UV analysis and deformation-ready gate; computes mesh reports and optionally creates/render poses through sibling Maya review module. | DEFER |
| 4 | `skills/dcc/maya/scenario-maya-rigging/scripts/mx_rig.py` | `fddfae914b778236fc3652bb4ae373dc0da86163` | 126334 | `188cb42089c3c625bd4cab023cc09cb6f9bcec795767f095f88ae4a29aa41c41` | Rig/IK/skeleton/weight and pose operations through Maya cmds/MEL; writes JSON report; some solver MEL names are marked [verify]. | DEFER |
| 5 | `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_goz.py` | `87cfaecd316943e2570c33f1ed870a074e9827d9` | 18844 | `3a6a7cae7e56cdabcc2a68214af1e277a0d33ef2bd5e039cc1c6ff8072059365` | Parses/writes binary GoZ files, edits global ZBrush GoZ preference/object-list files with backups, and starts macOS ZBrush via fixed argv `open -a` (60s timeout). | DEFER |
| 6 | `skills/dcc/zbrush/scenario-zbrush-automation/scripts/zb_plugin_ops.py` | `bbb5945a05d3aba6e8051a96b10b5d7c0a2dd7a0` | 30311 | `4fe0d1356d137cd9075a4904ef939563373adeb60e08870ebe6838539edfd497` | Automates ZBrush plugin palettes (UV Master, Decimation Master, Multi Map Exporter), SubTool loops and map exports; many command paths are explicitly [verify]. Header says NOT YET RUN IN ZBRUSH. | DEFER |
| 7 | `skills/dcc/zbrush/scenario-zbrush-character-creature/scripts/zb_character.py` | `0394480a3fe520721a3d240b2432bedc4f4c8cd8` | 112551 | `d55f234097cdbb68e32ef117e43e696fa17464af621c820b26a8c00931427ca4` | Pure Python mesh/stroke planning plus ZBrush-side layer/mask/FiberMesh/curve operations and agent-side OBJ/alpha image processing; imports sibling ZBrush toolkits. Header says ZBrush layer 2 has not run. | DEFER |
| 8 | `skills/dcc/zbrush/scenario-zbrush-expert/scripts/zb_audit.py` | `6aa30d9f940a7397e7d03de4cb858374cdc209d3` | 17846 | `8b2dcfee22e40aff7a873b3dcc31193f74137fd072a027cfd340bb3590b0fc2e` | Agent-side OBJ parser and mesh audit via NumPy; reads caller-supplied OBJ without explicit size/vertex/face limits and writes optional JSON output. | DEFER |

All eight Git blob identities, byte sizes and SHA-256 values match the selected-payload audit ledger. Hashes are reproduced from committed evidence, not recalculated by running source.

## Security findings

- `mx_run.py` is a general Maya job runner: it launches a mayapy subprocess and executes a job script using Python `runpy`. It explicitly disables scene script nodes by default (good defense), but a customer-controlled `job_path` or `job_args` would still be arbitrary code execution. Only signed/allowlisted job modules may be passed; no user file path may become a job script.
- `mx_pipeline.py` uses process isolation and timeouts, but its batch API accepts scene paths, output directory, job path, plugins, environment and script-node toggle. These must be server-generated/allowlisted, path-confined and tenant-scoped. The FBX exporter uses MEL for generated option commands; do not allow raw MEL or unchecked string overrides.
- `zb_goz.py` uses fixed argv and a timeout (no shell), but mutates shared user-level ZBrush preference and object-list files. It is not safe in a multi-tenant API/worker environment and can overwrite global settings, even though it makes backups.
- `zb_plugin_ops.py` and `zb_character.py` automate ZBrush plugin UI paths that the source labels [verify]. Both declare that live ZBrush operations have not been run. They must remain inactive until supported ZBrush version/plugin verification is authorized.
- `zb_audit.py` parses untrusted OBJ files directly and has no explicit input-size/vertex/face quotas. Add bounded parsing and run in an isolated worker if ever adopted.
- No outbound HTTP client, credential handling or Python `exec/eval` was found in this batch. MEL evaluation in Maya is used for fixed commands; it must not become a raw user-provided command channel.
- No source is approved for COPY/ADAPT into the MoreAI API process, OpenManus runtime or customer-callable tools. DCC operations need dedicated licensed, version-pinned, isolated workers with quotas, no ambient secrets, no default network and complete artifact provenance.

## Review coverage after this batch

- Entrypoints: 229/229.
- Executable source: **63/875** manually reviewed (55 prior + 8 in this batch); 812 remain.
- Configuration/schema: 13/69.
- Reference documents: 17/726.
- Selected payload SHA-256: 1,941/1,941 verified; 19 ARCHIVE_ONLY / 1,922 DEFER FINAL_HOLD.
- Exact OSV query coverage: 1,824 unique npm PURLs + 112 unique PyPI PURLs; 49 vulnerable coordinates and 247 advisory associations.
- Migration parity: 116 applied history rows vs 85 repo migration files; Phase 05 REVIEW_REQUIRED.

P1 remains **IN_PROGRESS / NOT ACCEPTED**. No DCC runtime, subprocess, tests/builds, provider calls, Supabase writes/migrations, staging or deployment occurred.
