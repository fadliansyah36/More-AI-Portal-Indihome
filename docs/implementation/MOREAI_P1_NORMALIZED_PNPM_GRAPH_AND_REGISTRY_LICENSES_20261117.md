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
