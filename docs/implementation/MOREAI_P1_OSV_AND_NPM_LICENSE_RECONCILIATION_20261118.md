# MoreAI P1 — Exact-Version OSV and npm License Reconciliation (2026-11-18)

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Pinned SBOM: `docs/implementation/MOREAI_P1_UPSTREAM_SBOM_20261117.cdx.json`
Advisory source: OSV.dev query_batch, source databases recorded per advisory
Registry source: npm registry exact-version package metadata
License artifact source: exact-version package files served by unpkg CDN

## 1. Exact-version vulnerability query coverage

Read-only OSV.dev queries were run against all exact package URLs in the current 1,995-component CycloneDX input and the additional pinned Python lock supplements.

| Ecosystem/scope | Exact coordinates queried | Vulnerable coordinates | Advisory associations |
|---|---:|---:|---:|
| Unique exact npm PURLs queried | 1,824 | 40 | 134 |
| Scenario Kinetic Music Video platform Python locks | 104 | 6 | 87 |
| Scenario Kinetic Film pinned Python requirements | 2 | 0 | 0 |
| MoreAI API/Worker direct Python pins | 6 | 3 | 26 |
| **Total exact coordinates queried** | **1,936** | **49** | **247** |

- The 1,824 unique exact npm PURLs were queried in batches of up to 100. 1,784 returned no matching advisory; 40 returned `vulnerable=true`. The BOM contains 1,940 exact npm component rows plus 23 unversioned MoreAI root dependencies; 116 exact component rows are repeated PURLs across source/component contexts.
- The 104 unique Python package@version coordinates from Linux x86_64 and macOS arm64 uv lock files were queried. Six returned vulnerable; 98 returned no matching advisory.
- `numpy==2.5.4` and `opencv-python-headless==5.0.0.93` from Kinetic Film's nested requirements file were queried separately; both returned no matching advisory.
- The 32 Python component rows in the original BOM comprise 8 exact direct-pin rows (6 unique PURLs) and 24 ranged/unpinned OpenManusWeb constraints. The 6 unique direct pins from MoreAI API/Worker were queried separately: python-multipart@0.0.20, cryptography@44.0.2 and pytest@8.3.5 are vulnerable; fastapi@0.115.12, httpx@0.28.1 and uvicorn@0.34.0 returned no matching advisory. OpenManusWeb's 24 ranged/unpinned requirements remain unresolved and are not included in the 1,936 exact-version count.
- The two machine-readable risk registers are:
  - `MOREAI_P1_OSV_NPM_VULNERABLE_COORDINATES_20261118.csv` — 40 exact npm PURLs and all 134 advisory associations.
  - `MOREAI_P1_OSV_PYPI_VULNERABLE_COORDINATES_20261118.csv` — 6 exact PyPI PURLs and all 87 advisory associations.
- A vulnerable query result means OSV's affected-version ranges match the exact package coordinate. It does not establish that the vulnerable code path is reachable in MoreAI or that any upstream skill has been imported into production.

## 2. Confirmed Python advisory detail samples

The following OSV records were opened to inspect exact affected ranges and fixed versions:

| Package@version | Advisory | Severity | Affected range / fixed version | Impact summary |
|---|---|---|---|---|
| `certifi@2026.7.22` | [GHSA-6q48-6c7w-9gw2](https://osv.dev/vulnerability/GHSA-6q48-6c7w-9gw2) / PYSEC-2026-4320 | CRITICAL | Before 2026.10.18; safe release 2026.10.19+ | Certifi bundled compromised emSign roots; an on-path attacker could impersonate TLS endpoints for clients trusting the bundle |
| `pillow@12.3.0` | [GHSA-22hg-r758-rrw9](https://osv.dev/vulnerability/GHSA-22hg-r758-rrw9) | HIGH | 7.2.0 through before 13.0.0 | Crafted MIC/TIFF input can cause an infinite loop at 100% CPU when optional `olefile` is installed and frame count is read |
| `filelock@4.2.0` | [GHSA-2g95-wg33-c5x2](https://osv.dev/vulnerability/GHSA-2g95-wg33-c5x2) | MODERATE | 4.1.0 through before 4.2.1 | Soft lock/lease race when another local user can manipulate files in a shared lock directory |
| `protobuf@4.25.9` | [GHSA-7gcm-g887-7qv7](https://osv.dev/vulnerability/GHSA-7gcm-g887-7qv7) / PYSEC-2026-1805 | HIGH | Before 5.29.6 for the 4.x range | Deeply nested `Any` JSON can bypass recursion accounting and exhaust the Python recursion stack |
| `setuptools@81.0.0` | [GHSA-h35f-9h28-mq5c](https://osv.dev/vulnerability/GHSA-h35f-9h28-mq5c) | MODERATE | Before 83.0.0 | Unicode normalization collision can bypass `MANIFEST.in` exclusions on macOS APFS/HFS+ source-distribution builds |
| `torch@2.11.0` | [GHSA-rrmf-rvhw-rf47](https://osv.dev/vulnerability/GHSA-rrmf-rvhw-rf47) / CVE-2025-3000 | LOW (OSV database severity) | Before 2.13.0 | Local PyTorch JIT script memory-corruption advisory |

The Python risk register records all 87 advisory associations, but only the representative records above have been individually opened and range-reviewed in this batch. Remaining records need full advisory-level severity, fixed-version, alias and reachability triage. The 62 Pillow advisory associations must not be treated as 62 independent vulnerabilities without alias/CVE deduplication.

## 3. npm vulnerable coordinate highlights

The npm register records 40 affected exact PURLs. Notable affected package/version groups include:

- `@azure/msal-node@5.1.5` — [GHSA-xcx6-jx8p-x3h5](https://osv.dev/vulnerability/GHSA-xcx6-jx8p-x3h5), CVE-2026-109461; advisory states the auth-code flow may disclose parameters to an attacker-controlled endpoint and patched release starts at 7.1.0.
- `@modelcontextprotocol/sdk@1.30.0` — six advisory associations.
- `node-forge@1.4.0` — 21 advisory associations.
- `undici@5.29.0`, `6.28.1`, `7.29.1`, `8.10.2` — 37 advisory associations across four exact versions.
- `dompurify@3.4.15` — five advisory associations.
- `hono@4.13.13` — five advisory associations.
- `fast-uri@3.1.7` and `3.1.8` — nine advisory associations.
- `body-parser`, `brace-expansion`, `minimatch`, `picomatch`, `postcss`, `zod`, `follow-redirects`, `glob` and other packages are listed in the complete CSV.

Severity, fixed versions, aliases and reachability for the 134 npm advisory associations have not all been individually triaged. All 40 coordinates are marked `BLOCK_IMPORT_UNTIL_TRIAGE`; no dependency version was changed and no package was installed.

## 4. Exact-version npm license file reconciliation

The 12 exact package versions previously in the registry-license review queue were inspected against their published package file manifests and LICENSE text via the exact-version unpkg CDN paths.

| Package group | Exact versions | Resolved license evidence |
|---|---:|---|
| `@ag-ui/client/core/encoder/mcp-apps-middleware/mcp-middleware/proto` | 6 | MIT |
| `base-64@0.1.0` | 1 | MIT (`LICENSE-MIT.txt`) |
| `khroma@2.1.0` | 1 | MIT (`license`) |
| `limiter@1.1.5` | 1 | MIT (`LICENSE.txt`) |
| `qrcode-terminal@0.11.0` | 1 | Apache-2.0 |
| `requireg@0.2.2` | 1 | ISC |
| `@cspell/dict-en-common-misspellings@2.2.5` | 1 | CC BY-SA 4.0; mapped to SPDX `CC-BY-SA-4.0` |

Evidence is stored in `MOREAI_P1_NPM_TARBALL_LICENSE_EVIDENCE_20261118.csv` with npm registry SHA-512 tarball integrity strings, exact license file URLs, and the SHA-256 file-integrity values advertised in the package CDN's `?meta` manifest. No separate NOTICE path appeared in the file manifests for these 12 versions.

Important limits:
- npm registry metadata had no `license` field for 11 of the 12; the exact package license text is now located, but the registry field remains null.
- The package tarball SHA-512 values are registry-advertised integrity values and were not independently recomputed from downloaded tarball bytes in this no-install/no-execution audit.
- The file-level SHA-256 values are CDN manifest integrity values, not independently recomputed local hashes.
- The CC-BY-SA dictionary's attribution/share-alike implications require explicit legal/product review before copying or distributing its contents.
- Other package source headers, nested third-party assets and all selected npm package notices across the 1,963 component rows are not thereby cleared.

The 12-row source queue was updated; it now links to the license evidence CSV. This resolves the missing LICENSE-file evidence for those 12 coordinates, not the complete license reconciliation for all selected dependencies.

## 5. Attribution and audit method

- OSV.dev query results and source advisory records must retain OSV.dev attribution. The records returned in this batch identify GitHub Advisory Database as the source database and `CC-BY-4.0` as the source licence; attribution and source URLs are preserved here and in the CSV risk registers.
- npm metadata was obtained for exact package versions from the npm registry. Published file contents were read from exact-version unpkg CDN URLs. No package tarballs were installed or executed.
- All source repositories and lockfiles remain pinned to the commits already recorded in the P1 source manifest. No upstream source commit was changed.

## 6. Gate status and required next work

- Exact npm OSV query coverage: **1,824/1,824 unique exact PURLs** (1,940 exact component rows; 23 unversioned root dependency rows unresolved).
- Exact Python OSV query coverage: **112/112 unique exact PURLs**.
- Vulnerable exact coordinates: **49** (40 npm + 9 PyPI), with **247 advisory associations**.
- The 12 previously missing npm license-file records now have exact-version license text evidence; CC-BY-SA obligations remain a legal review item.
- Advisory-level triage, alias/CVE deduplication, severity/fixed-version analysis for all npm/PyPI records, and code-path reachability remain open.
- Full SBOM is still incomplete because 32 original PyPI constraints and 24 OpenManusWeb ranged/unpinned requirements are unresolved, additional package sources must be reconciled, and source/tarball/NOTICE coverage is not complete.
- Do not import, publish, or activate any dependency/skill package on the strength of this scan alone.
- P1 remains **IN_PROGRESS / NOT ACCEPTED**. P2 ADR remains **DRAFT / NOT ACCEPTED**. Phase 04–09 remain gated; Phase 10/11 remain BLOCKED / NOT ACCEPTED.

No dependency versions, package manifests, lockfiles, application source, database schema or runtime configuration were modified. No installs, tests, builds, provider activation, Supabase writes/migrations, staging or deployment were performed.


## Correction addendum — exact PURL deduplication and direct API/Worker Python dependencies (2026-11-18)

A second structural reconciliation of the CycloneDX component properties found that the npm component row count and unique exact PURL count must be distinguished:
- 1,963 npm component rows total.
- 1,940 exact-version npm component rows, but only **1,824 unique exact PURLs** after deduplicating repeated coordinates across source/component contexts.
- 23 MoreAI frontend root `package.json` rows have no lockfile and remain `UNRESOLVED_NO_LOCKFILE`; they are not exact versions and were not OSV queried.
- Therefore exact npm OSV coverage is **1,824/1,824 unique exact PURLs**, not 1,963. This correction supersedes the earlier count wording above.

The 32 PyPI component rows comprise 24 unpinned/ranged OpenManusWeb constraints and eight exact direct-pin rows representing six unique MoreAI API/Worker PURLs. Those six were queried separately:
- Vulnerable: `python-multipart@0.0.20` (14 advisory associations; representative [GHSA-5rvq-cxj2-64vf](https://osv.dev/vulnerability/GHSA-5rvq-cxj2-64vf), HIGH, fixed 0.0.30), `cryptography@44.0.2` (10 associations; representative [GHSA-537c-gmf6-5ccf](https://osv.dev/vulnerability/GHSA-537c-gmf6-5ccf), HIGH, fixed 48.0.1 for PyPI wheels), and `pytest@8.3.5` (2 associations; representative [GHSA-6w46-j5rx-g56g](https://osv.dev/vulnerability/GHSA-6w46-j5rx-g56g), MODERATE, fixed 9.0.3).
- No matching OSV advisory: `fastapi@0.115.12`, `httpx@0.28.1`, `uvicorn@0.34.0`.
- The PyPI risk register now includes these three direct dependency findings.

Corrected total exact-version query coverage is **1,936 unique PURLs** (1,824 npm + 112 PyPI), with **49 vulnerable coordinates** (40 npm + 9 PyPI) and **247 advisory associations**. The 23 unversioned npm root rows and 24 ranged Python constraints remain unresolved. This count still does not include unresolved/transitive dependencies from manifests without lockfiles or packages outside the current BOM inputs.
