# P1 Recursive Inventory Continuation — 2026-11-17

Status: **RECURSIVE TREE INVENTORY CAPTURED; P1 NOT CLOSED**.

## Main source repositories

All five immutable recursive GitHub tree endpoints returned `truncated=false`. The complete tree-entry manifest is committed at [MOREAI_P1_RECURSIVE_SOURCE_TREE_MANIFEST_20261117.csv](./MOREAI_P1_RECURSIVE_SOURCE_TREE_MANIFEST_20261117.csv); the summary is [MOREAI_P1_RECURSIVE_SOURCE_TREE_INVENTORY_20261117.md](./MOREAI_P1_RECURSIVE_SOURCE_TREE_INVENTORY_20261117.md).

| Source | Pin | Files | Directories | Bytes |
|---|---|---:|---:|---:|
| OpenManusWeb | `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` | 111 | 20 | 1,201,688 |
| OpenFuse | `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc` | 219 | 32 | 4,345,760 |
| Visual Skills | `61a60d317f0fa0c3dc98902e58a7cb178838ae3f` | 60 | 8 | 676,353 |
| Scenario Skills | `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | 2,114 | 702 | 62,154,351 |
| Motion Skills root | `9b9ce041932da787cc856d4cdf23afb6cd13d4bf` | 10 | 2 | 5,174,361 |

## Motion Skills — all 19 independently pinned packs

The 19 pack repositories were resolved to current immutable HEAD commits and their recursive trees were captured. Every pack tree returned `truncated=false`. The complete tree manifests are split into [part 1](./MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_20261117.csv) and [part 2](./MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_PART2_20261117.csv).

| Pack | Commit | Files | Dirs | Bytes | Root license file |
|---|---|---:|---:|---:|---|
| tiktok-video-skills | `88e7152fc2710fa16852d013959cfd988a8adc8b` | 23 | 11 | 3,918,267 | LICENSE |
| text-message-video-skills | `10ae6bb32e89519c904b8f7950479ff655f839aa` | 14 | 5 | 3,654,036 | LICENSE |
| youtube-video-skills | `7838388571a3a6301bf5633e91941f9dfed0abfd` | 16 | 7 | 3,040,419 | LICENSE |
| ecommerce-video-skills | `a430fbbb7660783c421ad0a145bcc1c98d6f0b7b` | 23 | 9 | 4,128,429 | LICENSE |
| ad-video-skills | `cc8071678f4225ee7bdccc4506f2468722bb3515` | 21 | 9 | 5,697,402 | LICENSE |
| data-animation-skills | `6570c0c4fbc9daa8d7ac1f1163a890352344206b` | 21 | 9 | 6,896,473 | LICENSE |
| explainer-video-skills | `3c13a1bc360c08503f24f9c9a99fda6d3d35de56` | 28 | 13 | 3,516,553 | LICENSE |
| map-animation-skills | `c8ef8463f5a4a8aa35ff0c6c17f42e52bbf588a5` | 14 | 5 | 5,404,576 | LICENSE |
| web-animation-skills | `ed3a045192679b24d32090ee7a983871311ababd` | 42 | 23 | 5,951,023 | LICENSE |
| motion-design-skills | `b85e50c4cef5ff17aa2187a10d49d2dae9226c74` | 47 | 22 | 4,393,645 | LICENSE |
| kinetic-typography-skills | `2b79c81230c6647a344844f9ed53b6fa07f3f1f9` | 13 | 5 | 3,739,995 | LICENSE |
| freelance-motion-skills | `9f294eb6df73cde7e2dea235f42275df11a16466` | 36 | 13 | 3,795,102 | LICENSE |
| webgl-animation-skills | `0041933813688c357804f7b13dcb85095c5a3210` | 20 | 9 | 9,373,731 | LICENSE |
| manim-skills | `3e989cb044f6a6fed8c07b06dddade6e3463d7ac` | 15 | 5 | 2,700,402 | LICENSE |
| generative-illustration-skills | `e7d62437c875fc8ad5eff6e90fe0e25b30e43933` | 7 | 3 | 3,018,603 | NONE |
| javascript-animation-skills | `060f7467a6e5ae5b57c90c9cb1b3508c13b88e49` | 30 | 17 | 5,455,108 | LICENSE |
| lower-thirds-skills | `58d3623da95a2c97a4890a2d3f6d9d67e040b3d7` | 17 | 10 | 1,186,945 | LICENSE |
| b-roll-skills | `bcd56742a8a99edaa699a6f7bc5a45922a8ec567` | 21 | 8 | 3,182,408 | LICENSE |
| talking-head-skills | `eac1f6b01467f6f95d8ab7602310ba0ff67ed91b` | 38 | 12 | 6,943,742 | LICENSE |

Totals: **19 packs, 446 files, 195 directories, 85,996,859 bytes (~86.0 MB)**. Eighteen packs show a root `LICENSE` path. `generative-illustration-skills` has no root `LICENSE`, `LICENCE`, `COPYING` or `NOTICE` path in its captured tree and is blocked from reuse pending affirmative license evidence. Presence of a license filename in the other packs is not yet a completed license-text/third-party-content review.

## Integrity and legal status

- Every tree entry is recorded with path, Git object SHA, mode/type and byte size.
- **SHA-256 is not yet computed.** Git blob SHA is Git's object identifier (SHA-1 in these repositories), not SHA-256 of raw file content. The raw bytes were not available in this execution environment for a full local hashing pass. Do not fill the SHA-256 field by converting or relabeling Git blob SHA.
- Recursive path inventory is complete for the pinned trees; source-content retrieval, SHA-256, nested notices, dependency/SBOM, vulnerability/license reconciliation, external linked-reference expansion and file-by-file target decisions remain open.
- Motion packs are separately maintained repositories; root Motion Skills MIT does not automatically establish the terms of every linked pack. Pack-level license text and embedded assets/references must be reviewed individually.
- The 19-pack list is the upstream catalogue audit scope, not approval to import all packs. Select only capabilities justified by MoreAI PRD and map each file to a target module or archive/exclusion reason.

## Source-to-target direction (preliminary, not final ADR)

| Source family | Candidate MoreAI destination | Guardrail |
|---|---|---|
| OpenManusWeb backend/runtime | `vendor/openmanusweb` pristine snapshot; adapted code in `engine/`, `apps/api/`, `apps/worker/` | Complete upstream backend parity required; never mount upstream frontend as product UI |
| OpenFuse browser/computer/task patterns | Existing FastAPI routers, worker adapters, browser session/action receipts, workspace/sandbox contracts | No separate OpenFuse runtime; all capabilities remain fail-closed behind worker/security gates |
| Visual Skills | Existing Skill Registry source packages; prompt/reference retrieval services | Treat as untrusted procedural content; retain NOTICE/attribution; prompt guidance is not a media generator |
| Scenario Skills | Existing Skill Registry + Tool/Provider Resolver and durable Agent Run lifecycle | Provider schemas are dynamic; require policy/approval, entitlement, metering and artifact receipts |
| Motion Skills packs | Existing Skill Registry + worker-isolated Remotion/Manim/JS renderer adapters | Audit each pack independently; no host execution, no iArt MCP/API calls without provider approval |

This mapping is a starting hypothesis only; P2 ADR must reconcile every selected capability to actual MoreAI files, APIs, Supabase constraints/RLS and PRD behavior.

## Explicit remaining P1 closure gates

1. Retrieve raw file bytes and compute SHA-256 for all files selected for import and retained source snapshot; record size and Git blob SHA separately.
2. Parse all manifests/lockfiles without installing packages; generate CycloneDX/SPDX SBOM with exact versions, direct/transitive graph and source attribution. Reconcile all `NOASSERTION`/unknown licenses and package vulnerabilities using authoritative registries.
3. Read root and nested LICENSE/NOTICE files, including all 19 packs; inspect embedded media/fonts/assets and linked external references. Resolve the missing generative-illustration license.
4. Complete per-file source → target mapping with decisions `copy`, `adapt`, `archive-only`, `exclude`, or `defer`, each with rationale and owner.
5. Reconcile capability parity against actual MoreAI backend services and update P2 ADR only after evidence is sufficient.

## Execution constraints

Read-only source inspection and documentation writes only. No packages installed, no scripts executed, no product code imported, no tests/build/lint/typecheck, no Supabase writes/migrations, no staging and no deployment. Existing mandatory AGENTS.md Phase 00–11 gate remains controlling; Phase 04, 06–09 are still in progress, Phase 10 is not accepted, Phase 11 is blocked. This report does not close P1 or authorize P3–P11 feature implementation.


## Selected skill payload scope and file-level disposition — 2026-11-17

The eligible selected-entrypoint register contains 229 skills (2 Visual, 172 Scenario, 55 Motion). Joining those folders against the pinned recursive tree manifests yields 1,923 unique files / 26,586,168 bytes.

Payload classification: 229 skill entrypoints, 723 reference documents, 898 executable source files, 67 configuration/schema files, 4 fonts and 2 media/binary assets. The current file-level manifest is MOREAI_P1_SELECTED_SKILL_PAYLOAD_MANIFEST_20261117.csv. Proposed dispositions are adapt for 952 skill/reference documents and defer for 971 executable/config/binary files. Every row is preliminary, not legal or security approval.

Raw SHA-256 is verified for 25 root/nested license/notice paths only. Per-file raw SHA-256 for the 1,923 payload files is pending. scripts/p1/audit_skill_payloads.py provides binary-safe recursive retrieval, SHA-256, Git blob parity, size and reference audit; it has not been executed.
