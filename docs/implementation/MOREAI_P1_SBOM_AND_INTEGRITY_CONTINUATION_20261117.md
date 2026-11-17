# P1 SBOM & Integrity Continuation — 2026-11-17

Status: **STATIC BOM INVENTORY GENERATED; DEPENDENCY/LICENSE CLOSURE OPEN**.

## CycloneDX BOM

File: `MOREAI_P1_UPSTREAM_SBOM_20261117.cdx.json`  
Format: CycloneDX 1.6  
Components: **1,995 distinct source+PURL records after correcting 37 peer-dependency range declarations that had been incorrectly emitted as package components**.

| Input | Inventory records |
|---|---:|
| OpenFuse `pnpm-lock.yaml` | 1,524 |
| Scenario Skills `pnpm-lock.yaml` | 479 |
| Motion talking-head skill `pnpm-lock.yaml` | 16 |
| OpenFuse browser-worker `package-lock.json` | 6 |
| OpenManusWeb `requirements.txt` | 24 |
| MoreAI root `package.json` direct deps/devDeps | 23 |
| MoreAI FastAPI + worker `pyproject.toml` direct dependencies | 9 |
| Raw source records before source+PURL dedupe | 2,044 after excluding 37 peer-only declarations from package nodes |
| Final unique source+PURL records | **1,995** |

The BOM is a static package-component inventory. It does not yet contain a fully reconciled dependency edge graph, vulnerability results, package registry license evidence, or proof of installation. No dependency was installed and no build/script was executed.

## Explicit license status

- **1,989 components:** SPDX `NOASSERTION` because the corresponding manifest/lock entry did not declare a license.
- **6 components:** declared license fields were available from the OpenFuse worker npm package-lock.
- The historical P1 OpenFuse audit noted 1,793 `package@version` `NOASSERTION` coordinates. That earlier count has not yet been reconciled one-to-one against this expanded 2,032-record scope; do not treat the two counts as equivalent.
- Registry metadata/artifact review for exact versions, license expressions, notices and vulnerability advisories remains outstanding.

## Reproducibility gaps

- Main MoreAI root has `package.json` but no root npm/pnpm/yarn lockfile in the inspected tree.
- `apps/api/pyproject.toml` and `apps/worker/pyproject.toml` have no checked-in uv/Poetry lockfile.
- OpenManusWeb `requirements.txt` includes ranges and unpinned dependencies; 24 lines are represented as unresolved constraints, not falsely assigned resolved versions.
- The OpenFuse root and Scenario Skills have pnpm lockfiles; OpenFuse browser worker has an npm lockfile; Motion's talking-head renderer has a nested pnpm lockfile. The other 18 Motion packs do not expose lockfiles in their captured tree.

## Raw SHA-256

The separate `MOREAI_P1_RAW_SHA256_MANIFEST_20261117.csv` records 34 source file/repository rows. Exact GitHub blob JSON base64 bytes were decoded, hashed, and byte counts matched GitHub's blob sizes. It includes:
- OpenManusWeb/OpenFuse/Visual Skills/Scenario/Motion root licenses/notices;
- all 18 identical Motion child-pack MIT LICENSE files;
- dependency manifests/lockfiles used in this static BOM;
- both Visual Skills skill entrypoints and one Scenario skill entrypoint.

This is not yet a complete raw SHA-256 inventory for all 230 product skill entrypoints and all selected references/scripts/assets. The existing OpenManusWeb vendor manifest separately reports 111/111 source/destination Git blob SHA matches. The Skill Resolver independently verifies per-file SHA-256 and Git blob SHA before package validation/execution.

## Remaining P1 closure gates

1. Reconcile all exact package coordinates and dependency edges; resolve the 1,793 historical NOASSERTION baseline against this new BOM.
2. Resolve exact-version license/NOTICE metadata and vulnerabilities from authoritative package registries for all selected packages.
3. Add lockfiles for MoreAI direct dependencies only through an approved engineering phase; do not install dependencies or change versions as part of this audit.
4. Compute raw SHA-256 for every final selected skill file (entrypoint, references, required scripts/assets) before immutable ingestion.
5. Complete per-file content review and final copy/adapt/archive-only/exclude/defer evidence. Current 3,919-entry disposition register remains preliminary.
6. Keep the unlicensed `generative-illustration-skills` pack blocked.
7. Only then close P1 and accept the P2 ADR.

No code, UI, database, migration, provider credential, test, staging or deployment changes were made.

## Corrective exact lockfile/SBOM reconciliation — 2026-11-17

A static key-level comparison was rerun against the pinned OpenFuse and Scenario pnpm v9 `packages:` sections, excluding `peerDependencies` range declarations and comparing exact package-name/version coordinates against the CycloneDX component records. The previous SBOM generator had incorrectly parsed 37 scoped peer dependency range keys (25 OpenFuse + 12 Scenario) as components with malformed PURLs/names and no resolved version. Those are not package@version records and were removed from `components`; the peer-range declarations are retained as a metadata property requiring separate resolution/compatibility review.

| Source | Exact lockfile package coordinates | Corrected SBOM coordinates | Missing | Extra |
|---|---:|---:|---:|---:|
| OpenFuse pnpm | 1,452 | 1,452 | 0 | 0 |
| Scenario Skills pnpm | 466 | 466 | 0 | 0 |

Corrected CycloneDX component count: **1,995**; corrected `NOASSERTION`: **1,989**; declared-license components: **6**. This resolves the exact coordinate parity of those two pnpm package sections only. It does not complete dependency edges/snapshot graph, nested peer dependency resolution, other source manifests, exact-version registry licenses, vulnerability review, or P1 closure.

The correction is committed in `fec0c32dd1531eb0bc26785eeac25965d0611e7d`. No dependency installation, build, package script or test was run.

## Pinned pnpm graph and registry-license reconciliation — 2026-11-17

This addendum supersedes the earlier statement that the dependency graph and all exact-version registry metadata were still wholly unexamined. The graph has now been structurally extracted from both pinned pnpm v9 lockfiles and exported to `MOREAI_P1_PNPM_EDGES_20261117.csv`.

| Source | Importers | Package keys | Snapshot keys | Integrity records | Dependency declarations |
|---|---:|---:|---:|---:|---:|
| OpenFuse | 3 | 1,452 | 1,454 | 1,452 | 3,464 |
| Scenario Skills | 1 | 466 | 466 | 466 | 644 |

OpenFuse dependency declarations resolve as 2,650 exact, 809 peer-context and 5 npm aliases; Scenario resolves as 610 exact and 34 peer-context. No dependency declaration remains unresolved after the alias correction. Peer constraints, optional peer metadata and transitive peer-context declarations are separately retained in the edge export.

Across the two lockfiles, 1,808 unique exact package coordinates were compared to the existing CycloneDX BOM. All 1,808 are present; 16 other npm PURLs in the BOM originate outside these two lockfiles and are listed in `MOREAI_P1_SBOM_EXTRA_NPM_COORDINATES_20261117.csv` pending source attribution.

Exact-version npm registry metadata was queried for all 1,808 coordinates; all returned HTTP 200. 1,797 package records contained a license field, while 11 did not and remain NOASSERTION. A token-level check against the SPDX license identifier list found one non-SPDX raw string, `CC BY-SA 4.0`, requiring manual evidence review. The 11 missing and one non-SPDX package are listed in `MOREAI_P1_REGISTRY_LICENSE_REVIEW_REQUIRED_20261117.csv`.

These registry values are not legal approval. Package tarballs were not downloaded/unpacked; artifact notices, source headers, vulnerability advisories and bundled assets remain open. P1 remains OPEN.


## Consolidated count reconciliation — 2026-11-17

The current corrected CycloneDX inventory is **1,995 distinct source+PURL component records**, not the earlier 2,032 / 2,026-NOASSERTION figures repeated in a draft ADR and earlier expanded-BOM notes. The 2,032 figure is superseded by the corrected generator output after removing 37 peer-dependency range declarations that had been incorrectly emitted as package components. Current corrected license summary: **1,989 NOASSERTION + 6 components with declared license fields**. Do not combine historical counts across generator revisions.

The exact lockfile package coordinate comparison is closed for the two pinned pnpm package sections: OpenFuse 1,452/1,452 and Scenario 466/466, with no missing/extra coordinates. The structurally extracted dependency declaration graph reports 3,464 OpenFuse and 644 Scenario declarations; after alias correction, all declarations are classified as exact, peer-context or npm alias, with no unresolved declaration. Across both lockfiles there are 1,808 unique exact coordinates, all present in the corrected BOM; 16 other npm PURLs remain pending attribution to their non-pnpm source manifests.

Registry metadata was retrieved for all 1,808 exact npm coordinates (HTTP 200): 1,797 have a license field; 11 do not; one additional raw value `CC BY-SA 4.0` is not an SPDX expression and needs manual review. This is metadata evidence only, not legal clearance or package-tarball verification. Vulnerability advisories, package archive notices, source headers, bundled assets and the 24 ranged OpenManusWeb Python requirements remain unresolved. P1 remains OPEN.


## Additional npm PURL attribution correction — 2026-11-17

The 16 extra npm PURLs previously marked pending attribution are now proven to originate from the pinned Motion Skills talking-head nested pnpm lockfile: `iart-ai/talking-head-skills@eac1f6b01467f6f95d8ab7602310ba0ff67ed91b/skills/talking-head/pnpm-lock.yaml`. A direct exact-coordinate comparison confirms 16/16 matches, zero missing and zero extras. See `MOREAI_P1_SBOM_EXTRA_NPM_COORDINATES_20261117.csv`, `MOREAI_P1_MOTION_TALKING_HEAD_PNPM_PACKAGES_20261117.csv` and `MOREAI_P1_MOTION_TALKING_HEAD_PNPM_EDGES_20261117.csv`.

The nested lockfile recount is 1 importer, 16 package keys, 16 integrity records and 13 explicit snapshot keys (the earlier 18-snapshot count is superseded). Its graph export has 16 edges. Source attribution is closed; license/tarball/vulnerability review of these 16 exact packages remains open. The corrected CycloneDX total remains 1,995 components.


## Nested selected-skill dependency source correction — 2026-11-17

The selected payload inventory includes two Scenario nested npm lockfiles (`scenario-kinetic-film/assets/npm/package-lock.json` and `scenario-kinetic-music-video/assets/npm/package-lock.json`) plus `scenario-kinetic-film/assets/requirements.txt`. These were not included in the previous 1,995-component CycloneDX input summary. A supplementary exact package/edge register now exists: `MOREAI_P1_NESTED_LOCKFILE_AND_REQUIREMENTS_SUPPLEMENT_20261117.csv` and `MOREAI_P1_NESTED_LOCKFILE_DEPENDENCY_EDGES_20261117.csv`.

The supplement records six unique npm coordinates (Playwright/Core, opentype.js, string.prototype.codepointat, tiny-inflate, three) and two pinned PyPI requirements (numpy 2.5.4 and opencv-python-headless 5.0.0.93). The npm lockfiles declare licenses and integrity hashes; the Python requirements do not include artifact hashes. These must be deduplicated against the current CycloneDX components, added where absent, and receive exact-version registry/artifact license and vulnerability review. Therefore **1,995 is the corrected count for the previous BOM inputs, not yet the complete selected-skill dependency BOM**. P1 remains OPEN.
