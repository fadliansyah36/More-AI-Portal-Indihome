# P1 normalized pnpm dependency graph and exact-version registry license evidence

Date: 2026-11-17 | Branch: main

Method: immutable pinned lockfiles fetched read-only; structural graph extraction without dependency installation or source execution; exact package/version coordinates reconciled against the existing CycloneDX npm PURLs; 1,808 exact-version npm registry metadata requests completed with HTTP 200; registry license strings checked against the SPDX license identifier list. No tests, staging, provider activation, database writes, migrations or deployment.

## Pinned inputs
- OpenFuse `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`
- Scenario Skills `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`

## Normalized graph

| Source | Importers | Package keys | Snapshot keys | Integrity records | Dependency declarations |
|---|---:|---:|---:|---:|---:|
| OpenFuse | 3 | 1,452 | 1,454 | 1,452 | 3,464 |
| Scenario Skills | 1 | 466 | 466 | 466 | 644 |

OpenFuse dependency resolution: 2,650 exact, 809 peer-context-resolved, 5 npm alias-resolved, 0 unresolved after alias handling. Scenario: 610 exact, 34 peer-context-resolved, 0 unresolved. The export also retains transitive peer contexts (OpenFuse 324; Scenario 14), peer range constraints (390; 52), and optional peer metadata (124; 34). The CSV contains 4,302 OpenFuse rows and 744 Scenario rows across dependency, peer-constraint and peer-context relations.

The parser was corrected to distinguish real npm aliases such as `string-width-cjs -> string-width@4.2.3` from ordinary peer-context suffixes such as `1.70.1(peer@...)`. Five alias-style dependency declarations resolve to package entries.

## SBOM reconciliation
- Existing CycloneDX BOM: 1,995 components, 1,824 npm PURLs.
- Unique exact coordinates in the two pinned pnpm lockfiles: 1,808.
- Lockfile coordinates absent from the SBOM: 0.
- Additional SBOM npm coordinates not in these two lockfiles: 16; listed in `MOREAI_P1_SBOM_EXTRA_NPM_COORDINATES_20261117.csv` pending source attribution.

## Exact-version npm registry license metadata
- Exact package coordinates queried: 1,808; successful registry responses: 1,808.
- 1,797 records contained a license field; 11 returned no license field and remain `NOASSERTION`.
- 1,796 values contained only identifiers/operators present in the SPDX license identifier list; one value (`CC BY-SA 4.0`) is non-SPDX and remains manual-review-required.
- The 12 review-required records are listed in `MOREAI_P1_REGISTRY_LICENSE_REVIEW_REQUIRED_20261117.csv`.

Registry metadata is not legal approval. No npm tarballs were downloaded or unpacked; package LICENSE/NOTICE files, source headers, bundled fonts/media, vulnerability advisories and transitive content remain subject to review. No license was inferred from package names.

## Artifacts
- `MOREAI_P1_PNPM_PACKAGES_20261117.csv` — package mapping keys, exact coordinates, peer contexts and integrity presence.
- `MOREAI_P1_PNPM_EDGES_20261117.csv` — importer/snapshot dependency declarations, alias resolutions, peer constraints, optional peer metadata and transitive peer contexts.
- `MOREAI_P1_REGISTRY_LICENSE_REVIEW_REQUIRED_20261117.csv` — 11 NOASSERTION packages and one non-SPDX license string requiring evidence.
- `MOREAI_P1_SBOM_EXTRA_NPM_COORDINATES_20261117.csv` — 16 SBOM npm coordinates requiring source attribution.

## Remaining P1 gates
1. Inspect exact package tarballs and notices for all 11 NOASSERTION packages and the CC BY-SA 4.0 package; validate all other registry license expressions against authoritative artifact evidence.
2. Attribute the 16 extra SBOM coordinates to exact source manifests/lockfiles.
3. Review all selected skill references, scripts, engines, fonts, media, models and assets; registry metadata does not clear content rights.
4. Compute raw SHA-256 for every final selected skill payload file and finalize file-by-file copy/adapt/archive/exclude/defer decisions.
5. Keep `generative-illustration-skills` blocked until valid license or explicit permission is evidenced.
6. Close P1 only after content, asset, vulnerability and hash evidence is complete and dispositions are accepted; P2 ADR remains DRAFT until then.

**Status: P1 dependency graph and first-pass registry license metadata are materially advanced, but P1 is NOT CLOSED.** Phase 04–09 remain gated by AGENTS.md and P1/P2 acceptance. Phase 10–11 cannot be accepted under the no-real-testing/no-staging instruction.


## Motion talking-head nested lockfile source attribution — 2026-11-17

The 16 additional npm coordinates previously listed as unattributed are now reconciled exactly to the pinned Motion Skills child repository `iart-ai/talking-head-skills@eac1f6b01467f6f95d8ab7602310ba0ff67ed91b`, lockfile `skills/talking-head/pnpm-lock.yaml`. A direct key-level comparison found **16/16 exact package coordinates**, with no missing or extra coordinate. The source attribution is recorded in `MOREAI_P1_SBOM_EXTRA_NPM_COORDINATES_20261117.csv` and the exact package register is `MOREAI_P1_MOTION_TALKING_HEAD_PNPM_PACKAGES_20261117.csv`.

The pinned nested lockfile contains one importer, two direct dependencies (`@fal-ai/client@1.10.1`, `@napi-rs/canvas@1.0.13`), 16 package-section keys, 16 integrity records and 13 explicit snapshot-section keys. The normalized 16-row edge register is `MOREAI_P1_MOTION_TALKING_HEAD_PNPM_EDGES_20261117.csv`: two importer edges, three transitive dependencies of the Fal client, and eleven platform-specific optional native canvas dependencies. The earlier inventory note stating 18 snapshot keys is superseded by this direct recount of the pinned lockfile.

This closes source attribution for the 16 extra npm PURLs; it does **not** close exact-version license metadata, package tarball NOTICE/source-header review, native binary provenance, vulnerability review or SBOM legal acceptance. These 16 packages remain pending registry/artifact license review and no dependency was installed.


## Newly discovered nested Scenario dependency manifests — 2026-11-17

A recursive selected-payload manifest scan identified two additional nested npm lockfiles and one nested Python requirements file under Scenario Kinetic Film / Kinetic Music Video. They were not inputs to the previously normalized OpenFuse/Scenario root pnpm graph or the Motion talking-head graph. Exact source records and dependency edges are now captured in `MOREAI_P1_NESTED_LOCKFILE_AND_REQUIREMENTS_SUPPLEMENT_20261117.csv` and `MOREAI_P1_NESTED_LOCKFILE_DEPENDENCY_EDGES_20261117.csv`.

The two npm lockfiles contribute six unique exact npm coordinates: `playwright@1.64.1`, `playwright-core@1.64.1`, `opentype.js@1.3.4`, `string.prototype.codepointat@0.2.1`, `tiny-inflate@1.0.3`, and `three@0.187.0`. Their package-lock entries include integrity values and declared license fields (Apache-2.0 for Playwright/Core; MIT for the remaining four). The lockfile metadata is not package tarball/NOTICE legal approval.

The Kinetic Film Python requirements file pins `numpy==2.5.4` and `opencv-python-headless==5.0.0.93` but has no hash lock or resolved transitive graph. No pip/npm install was performed. The six npm PURLs and two PyPI PURLs must be deduplicated against the current CycloneDX BOM before its final component count is stated. The current 1,995 count remains valid only for its previously documented input set and is not a complete all-selected-payload SBOM yet. P1 remains OPEN.


## Kinetic Music Video platform Python lock graph — 2026-11-17

The selected payload's maintainer reference revealed two additional uv-generated Python lock files, omitted from the earlier SBOM input inventory:
- `skills/scenario-kinetic-music-video/assets/python/linux-x86_64.txt`: 100 exact package records.
- `skills/scenario-kinetic-music-video/assets/python/macos-arm64.txt`: 83 exact package records.

A read-only parse generated 104 unique package@version coordinates across both platforms, 3,660 SHA-256 wheel hash entries and 306 dependency edges (reconstructed from the `# via` reverse dependency comments and direct requirements). Machine-readable evidence: `MOREAI_P1_KINETIC_MUSIC_VIDEO_PYTHON_LOCK_PACKAGES_20261117.csv` and `MOREAI_P1_KINETIC_MUSIC_VIDEO_PYTHON_LOCK_EDGES_20261117.csv`.

The locks use exact versions, binary-only wheel resolution and per-artifact SHA-256 hashes. They do not contain SPDX license fields, so registry/artifact license evidence remains NOASSERTION pending review. Platform divergence includes `av` 18.1.0 vs 15.1.0, `onnxruntime` 1.31.0 vs 1.23.2, and Linux-only CUDA/NVIDIA/Triton packages. No Linux ARM64 lock is present. The maintainer notes that Demucs downloads a checkpoint checked only against a short hash prefix before unpickling, and Whisper model content verification is not confirmed; these model artifacts remain blocked until full content hashes/signatures and safe serialization are established.

The 104 coordinates must be deduplicated against the CycloneDX BOM; they are not assumed to be 104 net-new components. The previous 1,995-component count is not a complete selected-skill BOM. No package or model was downloaded or installed by this audit. P1 remains OPEN.
