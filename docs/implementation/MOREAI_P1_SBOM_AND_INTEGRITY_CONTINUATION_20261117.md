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
