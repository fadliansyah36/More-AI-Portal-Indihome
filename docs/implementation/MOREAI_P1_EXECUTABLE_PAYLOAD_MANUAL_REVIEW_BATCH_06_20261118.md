# P1 Executable Payload Manual Review — Batch 06

Date: 2026-11-18
Branch: `main`
Pinned source: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
Scope: 8 Maya DCC source modules covering deformation, audit/review/validation, FX, groom, lighting and look development.
Method: immutable source static inspection, including file/process/network/dynamic execution boundaries and author-declared Maya runtime verification state. No Maya/MayaPy/Arnold/MtoA process, script, render, test, package installation or scene was executed.

## Per-file review and disposition

| # | Source path | Git blob SHA | Bytes | Raw SHA-256 | Finding | Disposition |
|---:|---|---|---:|---|---|---|
| 1 | `skills/dcc/maya/scenario-maya-deformation/scripts/mx_skin.py` | `5fafd032b5d0e9ac4d47b1b2fffceee2c2a4f53a` | 115009 | `ce0857f97b7e0ac78b226c3cfb961fa18624b3f431cf921df69403e8497d0546` | SkinCluster weight/deformation operations through Maya cmds/OpenMaya; reads spec JSON and writes result JSON; mutates skin/mesh weights. | DEFER |
| 2 | `skills/dcc/maya/scenario-maya-expert/scripts/mx_audit.py` | `4b515a0ba2f882a94bf2557d4c2401ba309c20b5` | 43612 | `072e56a81f57d831695f1652912cf083fc1126d7b1b4a34195d900a024db7f0d` | Mesh audit/scene extraction using Maya cmds/OpenMaya; writes JSON. Source header says Maya 2027 extraction has not been run/verified. | DEFER |
| 3 | `skills/dcc/maya/scenario-maya-expert/scripts/mx_review.py` | `37e1a8b30431828d2c2acc1549a8912a65e1e652` | 63769 | `aa5526841111bd2e2bc101093037a4a4b1a50abeddd4dbc487a51beed9eafd60` | Renders model review/contact sheets, reads/writes PNG and invokes `imconvert` and `ffmpeg` via argv-based subprocess calls; uses MEL Arnold render. Header says Maya/Arnold calls unverified. | DEFER |
| 4 | `skills/dcc/maya/scenario-maya-expert/scripts/mx_validate.py` | `b29571e508a6287823802b9ed5b2d656fed058a9` | 42079 | `1dfca96851a21c0084a64376de79552579c156d63ac01320d93ccedb82fe16e3` | Scene validator with optional safe fixes; writes JSON and invokes MEL cleanup command. Header says Maya 2027 runtime has not been run. | DEFER |
| 5 | `skills/dcc/maya/scenario-maya-fx/scripts/mx_fx.py` | `194fc4ca507c2ce207e6fadd09765cfd48a28dbc` | 103486 | `a5dc0c08def8c6a6f7038ae4ce4c6262036fafe86d6d51b770a911cf3bda3974` | Nucleus/nCloth/Bifrost/MASH/cache operations; MEL command construction, plugin loading, file/cache mutation and writes Python code into a MASH Python node after syntax compilation. Header says Maya 2027 API paths are unverified. | DEFER |
| 6 | `skills/dcc/maya/scenario-maya-groom/scripts/mx_groom.py` | `34edadef87bd9fe29342370f8091905aa1d5fa47` | 169006 | `1aa5ecdc92e434f793c7539199fa185be0cfa5f8d1f51b21a19be2edcb8ab146` | XGen Interactive Groom and plugin/scene/file operations. Reads menu callback strings, executes them through `mel.eval` or Python `exec`; loads and replays stored MEL recipes and captures command history to disk. | DEFER — HIGH RISK |
| 7 | `skills/dcc/maya/scenario-maya-lighting-rendering/scripts/mx_light.py` | `386c7e462c1e0e54eeac92f8aabb3f05dfd5a706` | 196902 | `0055719dbfe58812a3a40439a2d5e9842f25323c7ece9b656a45d6b9226c1afa` | Arnold lighting/render/EXR pipeline; reads/writes image and scene files, builds and executes Arnold `kick` subprocess commands, loads MtoA plugin. Header says Maya/MtoA integration not yet run. | DEFER |
| 8 | `skills/dcc/maya/scenario-maya-lookdev/scripts/mx_shade.py` | `d61194736e3022c30551d2e5d572023676f460c3` | 128158 | `380df284a4cd61cb747e4bef5b0f588a961cd3bccc56e5d56e4b90ba8345992a` | Texture/color-space/material graph and Arnold look-dev operations; reads/writes texture/image/JSON files, invokes MEL Arnold render. Header says Maya 2027/MtoA behavior unverified. | DEFER |

All eight Git blob identities, byte sizes and SHA-256 values match the selected-payload audit ledger. Hashes are reproduced from committed evidence; no source was executed.

## Security findings

### High-risk dynamic execution — `mx_groom.py`

- `_menu_build()` obtains a Maya menu `postMenuCommand` string and attempts `mel.eval(pmc)`, then Python `exec(pmc, {"cmds": cmds, "mel": mel})` as fallback.
- `run_recipe()` loads a MEL string from a recipe JSON file, substitutes tokens, then calls `mel.eval(code)`.
- `capture_start()/capture_stop()` write Maya command history to a caller-provided log path; recipes may therefore be derived from GUI commands and later replayed.
- This is intentional desktop automation, but it is an arbitrary-code execution boundary. Recipe JSON, menu callback strings, token values and the Maya session must never be customer-controlled or exposed as an ordinary Agent tool. Any future adapter requires signed/allowlisted recipes, a fixed command schema, approval, audit receipt, disposable per-tenant Maya process and no ambient credentials.

### Other process and script execution

- `mx_review.py` launches `imconvert` and `ffmpeg` using argv lists (no shell); output/input paths and binary discovery must be constrained to an isolated worker.
- `mx_light.py` launches Arnold `kick` via `subprocess.run`; command construction, MTOA binary discovery, render environment and .ass input/output must be pinned and sandboxed.
- `mx_fx.py` stores Python code in a MASH Python node after `compile(..., "exec")`; compilation is a syntax check, but the node may execute the code in Maya. Treat all script-node content as executable and block arbitrary user code.
- `mx_validate.py` runs a MEL cleanup command; `mx_shade.py` and `mx_review.py` call Arnold render commands through MEL.
- No outbound HTTP client or explicit credential access was identified in these eight files. Process and dynamic execution signals are local DCC boundaries, not proof of external network use.

### Runtime and product fit

- Several headers explicitly say Maya 2027 / Arnold / MtoA integration has not been run or verified; only pure-Python portions or fake-Maya tests are described in source comments. The user's current prohibition on real-world testing means these runtime claims cannot be accepted now.
- Maya/Arnold/XGen/MASH require licensed, version-pinned DCC runtimes, plugins and GPU/CPU resources. They cannot be imported into FastAPI or an ordinary OpenManus tool process.
- These files are not MoreAI customer dashboard components and have no direct capability parity with customer workflows. If a future media/3D capability is justified, it needs a dedicated isolated Maya worker and product-owner/legal/security approval.

All eight remain DEFER. The high-risk `mx_groom.py` dynamic execution boundary is explicitly blocked from import/activation pending a redesigned allowlisted adapter.

## Review coverage after this batch

- Entrypoints: 229/229.
- Executable source: **55/875** manually reviewed (47 prior + 8 in this batch); 820 remain.
- Configuration/schema: 13/69.
- Reference documents: 17/726.
- Selected payload SHA-256: 1,941/1,941 verified; 19 ARCHIVE_ONLY / 1,922 DEFER FINAL_HOLD.
- Exact OSV query coverage: 1,824 unique npm PURLs + 112 unique PyPI PURLs; 49 vulnerable coordinates and 247 advisory associations.

P1 remains **IN_PROGRESS / NOT ACCEPTED**. No Maya/DCC execution, package install, tests/builds, provider calls, Supabase writes/migrations, staging or deployment occurred.
