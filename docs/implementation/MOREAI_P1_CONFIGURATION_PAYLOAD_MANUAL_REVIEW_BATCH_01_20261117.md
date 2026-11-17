# P1 Configuration & Dependency Payload Manual Review — Batch 01

Date: 2026-11-17  
Branch: `main`  
Scope: 12 configuration, package-manifest, lockfile, CI workflow and example-data files from pinned Scenario Skills / Motion Skills trees.  
Method: read-only inspection of exact source content at pinned commits. No package installation, workflow execution, build, CI, test, provider call or project mutation.

## Reviewed configuration files

| # | File | Review finding | Decision |
|---:|---|---|---|
| 1 | Scenario `skills/scenario-kinetic-film/assets/npm/package.json` | Declares a private local project with exact direct dependency `playwright@1.64.1`. | **DEFER** — renderer dependency only; no installation until isolated renderer and license/artifact review. |
| 2 | Scenario `skills/scenario-kinetic-film/assets/npm/package-lock.json` | npm lockfile v3 pins Playwright and Playwright Core 1.64.1, with integrity values and declared Apache-2.0 fields. This is exact lock metadata, not package-tarball or NOTICE verification. | **DEFER** — retain as dependency evidence; no install/activation. |
| 3 | Scenario `skills/scenario-kinetic-music-video/assets/npm/package.json` | Private local project declares `opentype.js@1.3.4`, `playwright@1.64.1` and `three@0.187.0`. | **DEFER** — local browser/render dependency; isolate before any use. |
| 4 | Scenario `skills/scenario-kinetic-music-video/assets/npm/package-lock.json` | npm lockfile v3 records six unique package coordinates across this and the companion film lockfile: Playwright/Core (Apache-2.0), opentype.js, string.prototype.codepointat, tiny-inflate and three (declared MIT). Integrity values are present. Lock metadata is not legal approval. | **DEFER** — exact package/artifact license and vulnerability review still required. |
| 5 | Scenario `skills/scenario-kinetic-film/assets/requirements.txt` | Pins `numpy==2.5.4` and `opencv-python-headless==5.0.0.93`, but has no hashes or resolver lock. The skill scaffold installs these into a local virtual environment. | **DEFER** — no pip install; add exact Python artifact hashes/licenses and dependency graph before reuse. |
| 6 | Scenario Roblox template `.github/workflows/publish.yml` | This is a production publishing workflow: uses protected production environment and `ROBLOX_PUBLISH_API_KEY`, downloads Rokit from a release URL, runs `rokit install --no-trust-check` and `wally install`, builds/merges places, publishes live, and can restart live servers. | **ARCHIVE_ONLY** — never import as a MoreAI workflow or execute from a customer skill. Any future Roblox publishing needs a separately designed approval-gated external action with dedicated customer credentials and immutable receipt. |
| 7 | Scenario Roblox template `.github/workflows/ci.yml` | CI downloads toolchain binaries and LuaU definitions, runs `rokit install --no-trust-check`, `wally install`, lint/type analysis/tests and a test-universe upload/execution using `ROBLOX_TEST_API_KEY`. | **ARCHIVE_ONLY** — upstream CI template only; do not run or transplant into MoreAI CI. |
| 8 | Scenario Godot `scripts/ci/godot-ci.yml` | CI template downloads Godot and export templates, checks SHA-512 against the release checksum file, runs project import/test/export, and uploads build/log artifacts. It is a game-project workflow, not a MoreAI backend workflow. | **ARCHIVE_ONLY** — retain only as source reference; do not attach to MoreAI CI or execute. |
| 9 | Motion `skills/talking-head/package.json` | Private Node >=22 package pins `@fal-ai/client@1.10.1` and `@napi-rs/canvas@1.0.13`. | **DEFER** — provider/media dependency; keep server-side and isolated, with package/artifact license and vulnerability review. |
| 10 | Motion `skills/talking-head/pnpm-lock.yaml` | Exact nested lockfile is source-attributed separately; records 16 package keys, integrity values and 13 explicit snapshot keys. | **DEFER** — dependency provenance is recorded, but registry license/tarball and native binary provenance review remains open. |
| 11 | Scenario Playable Ads `assets/template/assets/manifest.json` | Declarative asset-processing manifest for images, audio and font inputs with dimensions, crop/mask, quality, trim and bitrate fields. It names local project asset paths and contains no provider credential. | **DEFER** — validate paths, file types, dimensions, decode limits and output budgets before renderer ingestion. |
| 12 | Scenario Playable Ads `assets/template/intake/intake.json` | Template intake metadata includes user-provided recording/screenshots/logo, store links, ad networks and Scenario team/project/asset identifiers. Values are placeholders, not credentials. | **DEFER** — treat all user file paths and external store URLs as untrusted input; enforce upload validation and provider authorization. |
| 13 | Scenario Patina `references/example-config.json` | Example render configuration with relative Blender project paths, output path, dimensions, FPS, worker count and camera transforms. | **ARCHIVE_ONLY** — sample config only; do not treat it as a production MoreAI renderer profile. |

## Dependency scope correction

The selected-payload inventory contains two nested Scenario npm lockfiles and one pinned Python requirements file that were not included in the previously documented top-level lockfile graph. They are now separately registered in:
- `MOREAI_P1_NESTED_LOCKFILE_AND_REQUIREMENTS_SUPPLEMENT_20261117.csv`
- `MOREAI_P1_NESTED_LOCKFILE_DEPENDENCY_EDGES_20261117.csv`

Exact source-level findings:
- Kinetic Film npm: `playwright@1.64.1`, `playwright-core@1.64.1`.
- Kinetic Music Video npm: `opentype.js@1.3.4`, `playwright@1.64.1`, `playwright-core@1.64.1`, `string.prototype.codepointat@0.2.1`, `tiny-inflate@1.0.3`, `three@0.187.0`.
- Kinetic Film Python requirements: `numpy==2.5.4`, `opencv-python-headless==5.0.0.93` (exact pins, no hashes/lock).
- The six unique npm coordinates must be deduplicated against the existing CycloneDX BOM before updating the component count. The two Python coordinates are also pending BOM/source/license reconciliation.

## Review coverage

- Configuration/schema files manually reviewed in this batch: 13/69 (including package manifests/lockfiles and CI workflows).
- Remaining configuration/schema files: 56/69.
- Executable source manual review: 23/875 (separate reports).
- Reference documents: 726 remain outside full manual content review.
- Every reviewed config remains DEFER or ARCHIVE_ONLY; none is activated.

No package install, CI workflow, source script, engine, test, provider, Supabase operation, staging or deployment was run.

**P1 remains OPEN.**


## Count correction
The scope/table contains **13 files**, not 12: 4 npm manifest/lock files, 1 Python requirements file, 3 CI/release workflow files, 2 Motion talking-head manifest/lock files, 2 Playable Ads JSON configs and 1 Patina example config. Of these, 4 are ARCHIVE_ONLY (two Roblox workflow templates, one Godot workflow template and one illustrative Patina config) and 9 remain DEFER. The operational ledgers were updated to reflect these decisions.
