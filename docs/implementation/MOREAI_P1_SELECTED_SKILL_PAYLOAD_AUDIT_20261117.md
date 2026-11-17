# P1 Selected Skill Payload Scope and Evidence Update

Date: 2026-11-17 | Branch: main | Status: **AUDIT SCOPE MAPPED — P1 NOT CLOSED**

## Selected entrypoint and payload inventory

The pinned manifests and selected-entrypoint register were joined by immutable repository, commit and path. The resulting payload manifest contains **229 eligible skill entrypoints and 1,923 unique files (26,586,168 bytes / 26.6 MB)** under their selected skill folders.

| Source | Entry points | Payload files |
|---|---:|---:|
| Visual Skills | 2 | 37 |
| Scenario Skills | 172 | 1,657 |
| Motion Skills | 55 | 229 |
| **Total** | **229** | **1,923** |

## Content-type inventory

| Kind | Files | Proposed disposition |
|---|---:|---|
| Skill entrypoints (SKILL.md) | 229 | adapt after safety, provenance and attribution review |
| Reference documents | 723 | adapt after citation/content/prompt-safety review |
| Executable source (Python, JS/TS, C#, GDScript, Luau, shaders, Swift, HTML templates, etc.) | 898 | defer pending security, relevance, sandbox and architecture review |
| Configuration/schema | 67 | defer pending dependency, secret, schema and runtime review |
| Media/binary assets | 2 | defer pending raw-byte, provenance, license and malware review |
| Fonts | 4 | defer pending redistribution and embedding-rights review |
| **Total** | **1,923** | **952 proposed adapt / 971 defer** |

The 898 executable files are not approved for execution or direct production import. They must be reviewed as source and, if justified by the PRD, adapted behind the MoreAI sandbox/worker boundary. No source script was executed.

## File-level provenance and decisions

MOREAI_P1_SELECTED_SKILL_PAYLOAD_MANIFEST_20261117.csv records each selected payload file's source, repository, immutable commit, owning skill entrypoint, path, Git blob SHA, expected byte size, content kind, proposed disposition and reason.

Every row is PRELIMINARY_NOT_FINAL. Git blob SHA is not SHA-256. The sha256 column remains empty until raw bytes are fetched and hashed. The register does not imply license or security approval.

## Binary-safe recursive audit utility

scripts/p1/audit_skill_payloads.py was added. It uses Python standard library only and fetches raw bytes from pinned GitHub commits, computes SHA-256 and Git blob SHA-1 separately, checks raw byte size and Git blob parity, follows local markdown/HTML/script references against the pinned source tree, records external and unresolved references, and assigns conservative preliminary dispositions.

The utility never installs dependencies, executes source, invokes providers or writes to Supabase. **The utility has not been executed.** The no-real-testing/no-staging instruction remains in force. A read-only audit run is separate from test/build/staging, but it is not completed evidence until output files are committed and reviewed.

## License and notice raw-hash evidence

A binary-safe UTF-8 hash pass was completed for all **25 root/nested license and notice paths** found across the pinned upstream source trees. They resolve to seven unique Git blob objects; all 25 paths have raw byte size and SHA-256 evidence in MOREAI_P1_LICENSE_NOTICE_SHA256_20261117.csv.

| Observed notice class | Paths |
|---|---:|
| MIT | 22 |
| CC BY 4.0 | 1 |
| Visual Skills attribution NOTICE | 1 |
| Apache-2.0 nested Scenario skill-creator | 1 |
| **Total** | **25** |

All 18 eligible Motion pack root LICENSE files have the same Git blob SHA and SHA-256 content. The generative-illustration-skills pack has no root license and remains blocked; its content is not part of the eligible selected register.

These hashes prove the identity of the notice bytes at the pinned revisions; they do not prove every file in a repository is covered by that notice. Per-skill third-party content, fonts, images, models, sample assets and dependency license scope still require review.

## Remaining P1 gates

1. Run the read-only payload audit utility against the committed pinned manifests and selected entrypoint register; commit its per-file SHA-256, Git blob parity, reference closure and failure outputs.
2. Manually review all 898 executable-source candidates and 67 config/schema files; map only relevant and safe capabilities to MoreAI worker/engine modules.
3. Review 723 reference documents for external citations, copied third-party material, prompt-injection content and attribution requirements.
4. Review the 6 binary assets (4 fonts, 2 media/image assets) for raw-byte hash, origin, license and malware status.
5. Resolve all external/unresolved references and identify any required sibling skill outside the selected folders.
6. Inspect exact npm tarballs/notices for 11 NOASSERTION packages and one non-SPDX registry license string; attribute the 16 additional SBOM coordinates.
7. Finalize each selected file's copy/adapt/archive-only/exclude/defer decision; the current 1,923-row register is preliminary.
8. Keep Scenario/Motion remote providers and execution services disabled until separate adapters, credentials, customer consent, tenancy, budgets, approvals and threat-model controls are accepted.

## Gate decision

**P1 remains OPEN.** Graph extraction and first-pass npm metadata are complete; 25 license/notice path hashes are verified; selected skill payload scope is now enumerated. The 1,923-file raw SHA-256 and content/reference audit has not yet been executed. P2 ADR remains draft/unaccepted. Phase 04–09 must not be represented as complete or advanced past the mandatory gate until P1 and P2 are accepted. Phase 10–11 remain unavailable under the user's no-real-testing/no-staging instruction.