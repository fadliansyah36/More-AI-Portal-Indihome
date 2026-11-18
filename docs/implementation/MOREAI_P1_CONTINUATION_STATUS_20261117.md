# MoreAI P1 Continuation Status — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Execution policy: source review and documentation only; no new real tests, staging, deployment, runtime activation, package installation, provider call, Supabase mutation or migration apply.

## Governing documents and source alignment

- Root `AGENTS.md` was reread at the current main head before this continuation. Its mandatory order remains READ → UNDERSTAND → inspect upstream full tree → classify → pin → copy → reconcile → port/integrate → connect UI → migrate → test → security/UI review → report.
- The repository phase tracker currently records Phase 00 revalidated, Phase 01–03 complete, Phase 04 in progress, Phase 05 complete, Phase 06–09 in progress, Phase 10 partial/not accepted and Phase 11 blocked. Those are source/documentation statuses, not proof of live runtime acceptance.
- The Project Library search found `MoreAI_Master_PRD_v1.0_ID.md` (and a duplicate). The repository also contains `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md`. **No Master PRD v1.2 file was found** in the searched Project Library or the current repository tree. Do not silently treat v1.0 as v1.2; product owner should provide/identify the authoritative v1.2 artifact if a newer revision exists.
- PRD v1.0 design direction inspected: Playful Neo-Brutalist + Soft Pastel; warm off-white canvas, ink outlines, pastel accents, hard offset shadows, Plus Jakarta Sans / Inter / JetBrains Mono; no excessive gradients/glassmorphism. Existing Customer UI remains protected and must be reused rather than redesigned.
- PRD v1.0 Customer PWA scope inspected: Home/Workspace, Chat, Agents, Tools/Connectors, Tasks/Runs, Files/Artifacts, Memory, Credits/Wallet, Plans, Partner Wi-Fi Access, Notifications and Profile/Settings. This aligns with the existing typed FastAPI integration inventory; it does not authorize adding duplicate UI surfaces.

## P1 evidence now committed

1. GitHub Actions run `44005811297`, job `133780781223`, succeeded and committed:
   - `docs/implementation/p1-skill-payload-evidence/skill-payload-audit-summary.json`
   - `docs/implementation/p1-skill-payload-evidence/skill-payload-file-audit.csv`
   - `docs/implementation/p1-skill-payload-evidence/skill-reference-audit.csv`
2. Integrity summary: 229 selected entrypoints; 1,941 recursively discovered payload files; 1,941 SHA-256 computations; 1,941 byte-size matches; 1,941 Git blob SHA matches; zero fetch failures.
3. Manual reference triage: 148 parser candidates are partitioned into 49 heading fragments (49/49 match), 78 existing directory targets and 21 contextual/runtime/generated/example references. The 21 contextual references are described individually in `MOREAI_P1_MANUAL_REFERENCE_TRIAGE_20261117.md`. Kinetic Film and Kinetic Music Video scaffold dependencies were confirmed by static reading of their scripts; the scripts were not executed.
4. Binary/font review: 14 assets have verified SHA-256, size and Git blob identity. Ten media/binary assets are dispositioned ARCHIVE_ONLY (preview/test evidence/examples); four WOFF2 fonts remain DEFER pending internal metadata and reserved-name review. Their adjacent OFL 1.1 notices were read and must remain separate from Scenario root MIT. See `MOREAI_P1_BINARY_FONT_ASSET_REVIEW_20261117.md` and `MOREAI_P1_SELECTED_ASSET_DISPOSITION_20261117.csv`.
5. Skill entrypoint review sample: 24/229 (10.5%) have been read-only inspected. Blender/Maya shell or process instructions are not permitted from browser/API process and remain sandbox-only; credential keyword occurrences were contextual reference checklist text, not observed literal secret values. This is a sample, not full review.

## P1 dependency/license status

- Corrected CycloneDX BOM: 1,995 distinct source+PURL components; 1,989 NOASSERTION and 6 with declared license fields. The earlier 2,032 / 2,026-NOASSERTION draft count is superseded.
- OpenFuse exact package coordinates: 1,452/1,452; Scenario exact package coordinates: 466/466.
- 1,808 unique exact coordinates across those lockfiles were compared to the BOM; all are present. Dependency declarations resolve to exact, peer-context or npm-alias categories with zero unresolved declaration in the normalized graph.
- 1,797/1,808 exact-version npm registry responses contain a license field; 11 remain NOASSERTION; one raw value `CC BY-SA 4.0` requires manual SPDX/license review.
- 16 additional npm PURLs in the BOM are still not attributed to a pinned input manifest.
- Exact npm package tarball notices/source headers and vulnerability evidence are not complete. Registry metadata is not legal clearance.
- OpenManusWeb's 24 ranged/unpinned Python requirements and MoreAI's missing root lockfiles remain reproducibility gaps.
- Missing root license for `generative-illustration-skills` remains a hard block.

## Current P1 disposition gate

- The 3,919-entry upstream source-to-target register remains `PRELIMINARY_NOT_FINAL`.
- The 1,941-file selected payload register remains `PRELIMINARY_NOT_FINAL`, except the separately documented 14 asset decisions and contextual reference triage.
- Only 24/229 entrypoints have been content-reviewed; the remaining 205 entrypoints, 875 executable-source files and 69 configuration/schema files still require review.
- External references, third-party source headers, media/model/font provenance, 12 registry license records, 16 extra npm coordinates, package vulnerabilities and final per-file dispositions remain open.
- Therefore **P1 is NOT CLOSED and cannot yet be marked accepted**.

## P2 and Phase 04–09 gate

- P2 ADR `MOREAI_P2_ADR_OPENMANUS_OPENFUSE_MEMORY_SKILLS_20261117.md` remains DRAFT / NOT ACCEPTED.
- Do not accept the ADR until P1 has full content/license/security/dependency evidence and product-owner acceptance.
- Existing Phase 04–09 implementation remains in progress per `PHASE-TRACKER.md`; it is not being represented as newly completed by this P1 audit. Phase 04 sandbox/browser deployment acceptance and Phase 06/07/08 live runtime/provider gates remain outstanding; Phase 09 has source-level Customer Dashboard work but no complete real Customer→worker→provider→Supabase acceptance.
- No new Phase 04–09 product code or UI changes are authorized in this continuation while P1/P2 prerequisites remain unaccepted under `AGENTS.md`.
- Phase 10/11 cannot be accepted in this work session under the user's no-real-testing/no-staging instruction.

## Commit trace

This status document is updated incrementally on `main`. The authoritative commit history is the repository history for this path and the linked evidence documents; no hand-maintained commit list is included here to avoid stale or mismatched SHA references.

**Next work:** the 229/229 entrypoint sweep is complete. Continue the 875 executable-source and 69 configuration/schema reviews; inspect 726 reference documents and 14 media/font assets; attribute the 16 extra npm PURLs; review 12 package license records and vulnerability evidence; reconcile OpenManusWeb Python requirements; then finalize all 1,941 file dispositions. Only after those gates can P1 be presented for product-owner acceptance and P2 finalized.

## Review coverage update — 2026-11-17

The read-only manual entrypoint sample has advanced from 24 to **32/229 (14.0%)**. The additional eight Maya/ZBrush files were inspected. “Credential” and “verify token” keyword hits were contextualized as source-provenance checklist or version-token text, not literal secrets. ZBrush `-script` execution and other DCC shell/process instructions remain sandbox-only. This does not close the remaining 197 entrypoints or the executable/configuration review.


## Review coverage update — 2026-11-17 (continued)

The manual entrypoint sample now covers **40/229 (17.5%)**. The latest eight ZBrush/Godot entrypoints were read. The one credential keyword hit was a provenance checklist reference, not a literal secret. No dynamic-code pattern was identified in the 40-entrypoint sample. Remaining 189 entrypoints are not reviewed; no blanket safety clearance is implied.


## Review coverage update — 2026-11-17 (48/229)

The manual entrypoint sample now covers **48/229 (21.0%)**. Eight Godot entrypoints were reviewed. Password-related keyword hits were limited to documented release keystore environment-variable names and a warning not to store passwords in presets; no literal secret was observed. Shell/process guidance remains sandbox-only. Remaining 181 entrypoints and referenced payloads are still open.


## Review coverage update — 2026-11-17 (64/229)

Manual content review now covers **64/229 (27.9%)** entrypoints. Roblox API-key/token mentions were contextualized as documented prerequisites and CI security guidance; no literal secrets were observed. Godot/Roblox shell/process workflows remain sandbox-only. Remaining 165 entrypoints are not yet reviewed.


## Review coverage update — 2026-11-17 (72/229)

The manual entrypoint sample now covers **72/229 (31.4%)**. Eight additional Roblox/Unity entrypoints were inspected. Credential/token keyword hits were contextualized as provenance checklists, cancellation tokens or editor-license diagnostic wording; no literal secrets were observed. Remaining 157 entrypoints are not reviewed.


## Review coverage update — 2026-11-17 (80/229)

The manual entrypoint sample now covers **80/229 (34.9%)**. Unity VFX and Unreal animation credential keyword hits were source-provenance checklist text, not secrets. DCC/engine shell workflows remain sandbox-only. Remaining 149 entrypoints are not reviewed.


## Review coverage update — 2026-11-17 (88/229)

The manual entrypoint sample now covers **88/229 (38.4%)**. Eight Unreal skills were inspected; credential hits were provenance checklist wording only, not secrets. Remaining 141 entrypoints and referenced executable/configuration payloads are open.


## Review coverage update — 2026-11-17 (96/229)

The manual entrypoint sample now covers **96/229 (41.9%)**. The latest eight Scenario skills were inspected; admin-analytics credential/API-key mentions were documentation about access scope and usage metrics, not secret material. Remaining 133 entrypoints are open.


## Review coverage update — 2026-11-17 (104/229)

Manual entrypoint review now covers **104/229 (45.4%)**. A material external-credential boundary was identified in Scenario Blender: the skill describes a Scenario API key/secret and local Blender MCP bearer token. No literal credential value was present and no provider was activated. This skill remains DEFER pending server-side secret references, explicit consent and isolated execution. A separate skill mentions `pip install pillow numpy`; no install was run. Remaining 125 entrypoints are open.


## Review coverage update — 2026-11-17 (112/229)

Manual entrypoint review now covers **112/229 (48.9%)**. Eight additional provider/media-oriented Scenario skills were inspected. They reference external providers but no shell/process, dynamic-code or secret-keyword pattern was flagged; provider calls remain blocked pending server-side adapter, consent, metering and artifact governance. Remaining 117 entrypoints are open.


## Review coverage update — 2026-11-17 (120/229)

Manual entrypoint review now covers **120/229 (52.4%)**. Eight additional image/video-oriented Scenario skills were inspected; external provider calls remain gated, and Kinetic Film scaffold commands remain sandbox-only. Remaining 109 entrypoints are open.


## Review coverage update — 2026-11-17 (128/229)

Manual entrypoint review now covers **128/229 (55.9%)**. Kinetic Music Video scaffold remains sandbox-only; image/video/3D provider skills require approved adapters, consent, metering and artifact governance. Remaining 101 entrypoints are open.


## Review coverage update — 2026-11-17 (136/229)

Manual entrypoint review now covers **136/229 (59.4%)**. Motion Loops and Playable Ads require Node/ffmpeg/Playwright or Python dependency installation per their instructions; no installation or command was run. Both remain DEFER pending dependency/license and isolated-renderer review. Remaining 93 entrypoints are open.


## Review coverage update — 2026-11-17 (144/229)

Manual entrypoint review now covers **144/229 (62.9%)**. Scenario Report explicitly prohibits placing API keys, tokens or signed asset-download URLs in reports; signed URLs must remain ephemeral and redacted. Remaining 85 entrypoints are open.


## Review coverage update — 2026-11-17 (152/229)

Manual entrypoint review now covers **152/229 (66.4%)**. Eight additional Seedance/Seedream/3D and media workflow skills were reviewed; provider calls remain gated. Remaining 77 entrypoints are open.


## Review coverage update — 2026-11-17 (160/229)

Manual entrypoint review now covers **160/229 (69.9%)**. Scenario Team Admin is deferred because it can change team membership/roles, project state, spend caps and API-key policy; it requires consent, approval, secret-vault and audit controls. Text Overlay dependency installation was not run. Remaining 69 entrypoints are open.


## Review coverage update — 2026-11-17 (168/229)

Manual entrypoint review now covers **168/229 (73.4%)**. Eight video/UGC skills were inspected; no shell/process, credential-keyword, install or dynamic-code pattern was flagged. Provider execution remains gated. Remaining 61 entrypoints are open.


## Review coverage update — 2026-11-17 (176/229)

Manual entrypoint review now covers **176/229 (76.9%)**. Scenario's general skill explicitly forbids agents from collecting/echoing API secrets; Motion caption token references are media timing structures, not credentials. Motion shell workflows remain isolated-worker-only. Remaining 53 entrypoints are open.


## Review coverage update — 2026-11-17 (184/229)

Manual entrypoint review now covers **184/229 (80.3%)**. Eight Motion Skills command-driven renderer workflows were inspected; they remain isolated-worker-only. Remaining 45 entrypoints are open.


## Review coverage update — 2026-11-17 (192/229)

Manual entrypoint review now covers **192/229 (83.8%)**. Eight additional Motion Skills renderer workflows were inspected; they remain isolated-worker-only and external resources require allowlist/provenance review. Remaining 37 entrypoints are open.


## Review coverage update — 2026-11-17 (200/229)

Manual entrypoint review now covers **200/229 (87.3%)**. Eight additional Motion renderer skills were inspected; local command workflows remain isolated-worker-only. Remaining 29 entrypoints are open.


## Review coverage update — 2026-11-17 (208/229)

Manual entrypoint review now covers **208/229 (90.8%)**. Eight additional web animation/motion-design skills were reviewed; renderer/build command guidance remains isolated-worker-only. Remaining 21 entrypoints are open.


## Review coverage update — 2026-11-17 (224/229)

Manual entrypoint review now covers **224/229 (97.8%)**. Manim requires Python package installation, ffmpeg and LaTeX; WebGL/Manim render workflows remain DEFER pending isolated renderer and dependency governance. Remaining five entrypoints are open.


## Review coverage update — 2026-11-17 (229/229 entrypoints)

The selected-skill entrypoint sweep is now **COMPLETE: 229/229**. The final five Motion entrypoints were reviewed. The static scan did not flag `eval()`, `new Function()`, `exec()` or `compile()` patterns in the entrypoint Markdown; this is not a malware scan or security certification. Referenced executable source, config/schema, docs, assets, fonts and final per-file disposition remain open. P1 remains NOT CLOSED.


## P1 manual payload review continuation — 2026-11-17

- Selected skill entrypoints: **229/229 manually reviewed** (complete; static entrypoint review is not code execution or security certification).
- Ambiguous reference parser candidates: **148/148 manually triaged** in `MOREAI_P1_MANUAL_REFERENCE_TRIAGE_20261117.md`: 49 heading fragments, 78 valid directory targets and 21 contextual/runtime/generated references. This supersedes the earlier coarse estimate of 25 unresolved candidates for the committed CSV.
- Executable payload source: first manual batch **13/875** reviewed and recorded in `MOREAI_P1_EXECUTABLE_PAYLOAD_MANUAL_REVIEW_BATCH_01_20261117.md`; all 13 are DEFER because of local arbitrary-code IPC, workstation process control, provider upload/download and renderer isolation requirements. Remaining 862 executable files remain DEFER pending individual review.
- Per-file selected-payload operational register: `MOREAI_P1_SELECTED_PAYLOAD_FINAL_OPERATIONAL_DISPOSITION_20261117.csv` contains all **1,941/1,941** selected payload paths. Current conservative decisions: **15 ARCHIVE_ONLY** (10 media/binary and 5 test/example fixtures) and **1,926 DEFER** (including all not-yet-cleared entrypoints, references, executable code, configuration/schema and fonts). This is a final operational hold register, not approval to ingest or execute; no file has been promoted to COPY/ADAPT.
- Exact npm source attribution: all 16 extra PURLs are now mapped 16/16 to the pinned Motion talking-head nested pnpm lockfile. Their package artifact/license and vulnerability review remains open.
- Binary/font review: 10 media/binary assets ARCHIVE_ONLY; 4 OFL font assets DEFER pending internal metadata and embedding/redistribution review.

P1 remains **OPEN**. Remaining work includes the 862 executable sources, 69 configuration/schema files, 726 reference documents, exact npm tarball/license evidence for unresolved packages (including the Motion 16), vulnerability review, Python requirements provenance/version reconciliation, and product-owner acceptance. P2 remains draft; Phase 04–09 remain gated by AGENTS.md. No tests, builds, installs, provider calls, Supabase reads/writes, staging or deployment were performed.


## Executable-source manual review update — Batch 02

The manual executable-source review has advanced to **23/875**. Batch 02 inspected ten additional engine, desktop automation and motion files. All ten remain DEFER: Maya mayapy job runner, ZBrush batch job, Godot archive installer, Roblox live-server restart tool, Unity pipeline CLI/build hooks, and Motion talking-head/b-roll render/prepare/paid-generation commands. Specific risks and controls are recorded in `MOREAI_P1_EXECUTABLE_PAYLOAD_MANUAL_REVIEW_BATCH_02_20261117.md`.

The per-file operational disposition ledger was refreshed with the 10 new review-evidence references; its 1,941 rows remain 15 ARCHIVE_ONLY and 1,926 DEFER. No source is enabled for execution. Remaining executable source: **852/875**; configuration/schema: 69; reference docs: 726. P1 remains OPEN.


## Complete source-tree disposition ledger — 2026-11-17

The broader pinned source inventory now has a complete operational decision row for every path: `MOREAI_P1_FULL_SOURCE_TREE_OPERATIONAL_DISPOSITION_20261117.csv` — 3,919 unique repository/commit/path rows, 2,960 file blobs and 959 directory records. Decisions: 111 COPY (pristine OpenManusWeb archival snapshot only), 391 ARCHIVE_ONLY (tests/evidence/non-runtime assets and unlicensed Motion pack), 2,458 DEFER, 959 directory rows NOT_APPLICABLE. No unreviewed file is promoted to runtime.

This resolves the missing/empty earlier CSV register issue, but it does not mean all 2,458 DEFER files have been manually reviewed. Selected payload manual executable review remains 23/875; 852 executable files, 69 config/schema files and 726 reference documents still require review. P1 remains OPEN.


## Configuration and nested dependency review update — 2026-11-17

Manual configuration review now covers **13/69** config/schema payload files. Four reviewed templates/examples are ARCHIVE_ONLY (Roblox live publish workflow, Roblox test CI workflow, Godot project CI workflow and Patina example config); nine reviewed package/manifest/intake files remain DEFER pending exact dependency, license, sandbox and input-validation gates. See `MOREAI_P1_CONFIGURATION_PAYLOAD_MANUAL_REVIEW_BATCH_01_20261117.md`.

Two nested Scenario npm lockfiles and a nested Python requirements file were discovered in the selected payload scope but were not part of the earlier top-level SBOM graph. They are now recorded in `MOREAI_P1_NESTED_LOCKFILE_AND_REQUIREMENTS_SUPPLEMENT_20261117.csv` and `MOREAI_P1_NESTED_LOCKFILE_DEPENDENCY_EDGES_20261117.csv`: six unique npm coordinates (Playwright/Core, opentype.js, string.prototype.codepointat, tiny-inflate, three) and two exact Python pins (numpy 2.5.4, opencv-python-headless 5.0.0.93). These coordinates still require de-duplication against the CycloneDX BOM and exact-version registry/artifact license and vulnerability review. The previous 1,995-component count is corrected for its earlier input scope, but must not be represented as complete for every nested selected skill manifest until this supplement is reconciled.

Disposition ledger correction: selected payload register now contains **19 ARCHIVE_ONLY / 1,922 DEFER**; full 3,919-row source ledger now contains **111 COPY / 395 ARCHIVE_ONLY / 2,454 DEFER / 959 directory NOT_APPLICABLE**. COPY remains limited to the pristine OpenManusWeb archival snapshot. P1 remains OPEN.


## Reference document review update — Batch 01

A separate manual content review now covers **8/726 reference documents**: three Visual Skills video-provider references (Kling, Seedance 2.5, Veo), two Maya reliability/source references, Godot procedures, Roblox procedures and the Motion talking-head workflow. All eight remain DEFER due to CC BY attribution, unstable third-party provider details, workstation-bound MCP/project actions, and/or voice/media privacy and deletion requirements. See `MOREAI_P1_REFERENCE_DOCUMENT_MANUAL_REVIEW_BATCH_01_20261117.md`. The 148/148 parser-reference-candidate triage remains a separate path-resolution result and is not counted as review of the 726 document contents.

Current selected-payload manual review coverage: entrypoints **229/229**; reference docs **8/726**; executable source **23/875**; configuration/schema **13/69**; fonts **4/4 notices inspected, binary metadata pending**; media/binary assets **10/10 classified ARCHIVE_ONLY**; parser reference candidates **148/148 triaged**. Per-file operational disposition remains 19 ARCHIVE_ONLY / 1,922 DEFER in the 1,941-row selected payload register. P1 remains OPEN; no file has been promoted to active runtime.


## Reference review Batch 02 and model-lock audit — 2026-11-17

Cumulative manual reference/maintainer content review is now **17/726** (8 unique documents in Batch 01 + 9 new unique documents in Batch 02; the repeated Veo reference is not double-counted). The second batch covers Maya 2027 traps, Godot/Roblox source catalogues, Kinetic Film/Music Video/Playable Ads maintainer notes, GPT Image/Nano Banana model guidance, Seedance and Visual Skills animatic keyframes. All remain DEFER. See `MOREAI_P1_REFERENCE_DOCUMENT_MANUAL_REVIEW_BATCH_02_20261117.md`.

The Kinetic Music Video README exposed two previously uncounted platform Python wheel locks. Static parsing (no install) recorded Linux x86_64 100 package records, macOS arm64 83 records, 104 unique exact package@version coordinates, 3,660 SHA-256 wheel hash entries and 306 dependency edges. The locks use binary-only wheel/hash pins; the Linux lock includes CUDA/NVIDIA/Triton packages, versions diverge by platform, and no Linux ARM64 lock exists. Upstream notes also identify Demucs checkpoint verification by short hash prefix followed by unpickling and unverified Hugging Face model content. See `MOREAI_P1_KINETIC_MUSIC_VIDEO_PYTHON_LOCK_PACKAGES_20261117.csv`, `MOREAI_P1_KINETIC_MUSIC_VIDEO_PYTHON_LOCK_EDGES_20261117.csv` and Batch 02 reference review.

These 104 PyPI coordinates require source+PURL deduplication against the CycloneDX BOM, exact-version registry license/vulnerability review and model provenance. They are not assumed to be 104 net-new components. The previous 1,995-component BOM count remains incomplete for all selected skill payloads until this nested platform lock scope is reconciled. P1 remains OPEN.


## Fresh repository + Supabase audit — 2026-11-18 (superseding stale counts)

Audit baseline at start of this continuation: `main@151da0a0133684bd38518c5f2f40f27bc08aa65a`. Root `AGENTS.md`, the current Master PRD document, phase tracker, P1 evidence and P2 ADR were reread before any source review.

### Governing-document correction

- The repository file name is `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md`, but its document header explicitly states **Version 1.2**. The earlier sentence in this report claiming that no Master PRD v1.2 exists is incorrect and is superseded.
- The document header is Version 1.2 / 11 November 2026 / Draft. Its opening narrative still mentions the former Playful Neo-Brutalist / Soft Pastel visual direction. Root `AGENTS.md` is the current implementation authority for the protected frontend and explicitly supersedes that older palette with clean white/light cool-gray surfaces, MoreAI/IndiHome red actions, deep navy typography and restrained category accents. Existing UI remains frozen; do not apply a visual redesign or global token migration.
- The current tree contains 780 tracked blobs at the audit baseline. Phase 00 has historical CI/browser evidence in the tracker; this continuation did not rerun those checks. Phase 10/11 remain blocked/not accepted under the current no-testing/no-staging instruction.

### Current Supabase read-only snapshot

Project ref: `uunfgimtokhucegqbpce`.

- 94 public base tables; RLS enabled on all 94.
- 95 public RLS policies; zero RLS-enabled public tables without a policy.
- 116 rows in `supabase_migrations.schema_migrations`; latest version `20261116113852` (`moreai_skill_ingestion_pending_until_validation`).
- Installed extensions include `vector 0.8.2`, `pgcrypto 1.3`, `supabase_vault 0.3.1`, `pg_cron 1.6.4`, and `uuid-ossp 1.1`.
- At query time, row counts were zero in `agent_runs`, `outbox_events`, `llm_providers`, `llm_models`, `llm_routing_policies`, `moreai_worker_capability_snapshots`, `moreai_browser_sessions`, `moreai_connections`, `moreai_skill_packages`, `moreai_skill_source_files`, `moreai_customer_memories`, `moreai_customer_memory_preferences`, `knowledge_documents` and `knowledge_chunks`. This is a data/configuration snapshot only; it does not prove that a worker process is absent, but it provides no persisted evidence of configured providers, healthy worker capability, active browser sessions, imported skills, memory or knowledge content.
- Supabase Security Advisor: one WARN — leaked password protection disabled. It was not changed.
- Performance Advisor: 94 unindexed foreign-key findings and 80 unused-index findings (INFO). No index changes were made; workload/EXPLAIN evidence is required before tuning.
- No schema, migration history, data, Auth settings, storage policy or runtime configuration was modified.

### P1 evidence reconciliation

The authoritative current selected-payload audit summary JSON reports:
- 229/229 selected skill entrypoints.
- 1,941/1,941 payload files with raw SHA-256 verified, Git blob SHA match, byte-size match and zero fetch failures.
- Content-kind inventory: 229 entrypoints, 726 reference documents, 875 executable-source files, 69 configuration/schema files, 23 other files, 10 media/binary assets, 4 font assets and 5 test/example fixtures.
- Static pattern scan: filesystem mutation 171, remote tool/MCP 29, process spawn 155, dynamic code 65, credential/environment references 86, network I/O 59 and package-install patterns 22. These are review flags, not confirmed vulnerabilities.

Do not confuse the two hash artifacts: `p1-skill-payload-evidence/skill-payload-file-audit.csv` contains the 1,941 selected-payload SHA-256 evidence rows; `MOREAI_P1_RAW_SHA256_MANIFEST_20261117.csv` is a separate 34-row supplemental manifest for selected root notices, dependency files and samples.

Current disposition evidence:
- Selected payload ledger: 1,941 rows = 19 ARCHIVE_ONLY / 1,922 DEFER (FINAL_HOLD). No selected payload is approved COPY/ADAPT.
- Full pinned source-tree ledger: 3,919 rows = 111 COPY (only pristine OpenManusWeb archival snapshot), 388 ARCHIVE_ONLY FINAL, 7 ARCHIVE_ONLY FINAL_BLOCKED, 2,454 DEFER FINAL_HOLD, and 959 directory records NOT_APPLICABLE.
- The full source-tree ledger's 7 FINAL_BLOCKED archive-only records include source/license blockers; these are not approved for import. In particular, the Motion `generative-illustration-skills` child pack still lacks a root license and remains blocked.
- Entrypoint content review 229/229; executable-source review 31/875 after Batch 03; configuration/schema review 13/69; reference-document review 17/726. The 148 parser reference candidates are path-triaged, not equivalent to semantic review of all 726 references.
- Fonts: 4/4 OFL notices inspected, binary metadata/provenance still pending. Media/binary assets: 10 ARCHIVE_ONLY.
- Exact-version npm registry metadata: 1,808 exact coordinates; 1,797 license fields, 11 missing fields, one non-SPDX `CC BY-SA 4.0` string. Package tarball NOTICE/source-header review and vulnerability reconciliation remain incomplete.
- The prior 1,995-component CycloneDX BOM is not a complete all-selected-payload SBOM: two nested Scenario npm lockfiles, a Python requirements file and two platform-specific Kinetic Music Video Python locks were discovered and must be reconciled. The platform locks contain 104 unique Python package@version coordinates, 3,660 wheel SHA-256 entries and 306 dependency edges; they are not assumed net-new components until deduplicated. OpenManusWeb also has 24 ranged/unpinned Python requirements.
- P1 executable manual review Batch 03 added 8 Blender source files; all remain DEFER due Blender scene mutation, render and caller-selected filesystem output boundaries. The per-file selected-payload ledger now links those 8 rows to the Batch 03 report.
- Vulnerability/CVE evidence across the complete resolved dependency graph has not been reconciled. Registry license metadata alone is not a vulnerability scan.

### P2 and phase gate

- P2 ADR remains DRAFT / NOT ACCEPTED. No product-owner acceptance evidence exists.
- Phase 04, 06, 07, 08 and 09 remain IN_PROGRESS / REVIEW_REQUIRED; Phase 05 remains COMPLETE at the documented schema-reconciliation scope, but this read-only snapshot does not certify end-to-end runtime behavior.
- Phase 04–09 product implementation remains gated by AGENTS.md's P1/ADR prerequisites unless a written product-owner exception is recorded. This continuation therefore advances P1 governance rather than bypassing the acceptance gate.
- Phase 10 remains BLOCKED / NOT ACCEPTED; Phase 11 remains BLOCKED / NOT ACCEPTED. No real tests, builds, staging, production deployment, provider calls, worker activation or Supabase writes/migrations were performed.

P1 remains **IN_PROGRESS / NOT ACCEPTED**. P2 remains **DRAFT / NOT ACCEPTED**.


## Executable source review continuation — Batches 03 and 04 (2026-11-18)

- Batch 03 reviewed 8 Blender animation/blockout files. All remain DEFER due Blender scene mutation, render and caller-selected output filesystem boundaries. Report: `MOREAI_P1_EXECUTABLE_PAYLOAD_MANUAL_REVIEW_BATCH_03_20261118.md`; commit `1f50d71024785299a46db7185be4adffd96d356a`.
- Batch 04 reviewed 8 Blender audit/GUI/review/export/geometry-node/Grease Pencil/hair/hard-surface files. `bx_export.py` launches a fixed-argv Blender subprocess with timeout but imports caller-selected model files and performs batch export; other tools mutate a Blender scene, invoke GUI/render operators or write outputs. All remain DEFER. Report: `MOREAI_P1_EXECUTABLE_PAYLOAD_MANUAL_REVIEW_BATCH_04_20261118.md`; commit `35a854d6598457b82ee4fac72f8a7bcba6fec473`.
- The selected-payload operational disposition CSV now links all 16 Batch 03/04 source paths to their detailed review reports. Each row retains DEFER / FINAL_HOLD; no COPY/ADAPT approval was made. CSV evidence update commit: `4adc5b40b4283fd4499abd9360f8a9945d70678c`.
- Cumulative executable-source manual review is now **39/875**; 836 remain. Entrypoints 229/229, configuration/schema 13/69 and references 17/726 remain the current review counts. Selected payload SHA-256 remains 1,941/1,941 verified.
- These reports are static source reviews. No Blender, Python source, subprocess, render, package installation, test/build, provider, Supabase mutation, staging or deployment was executed.
- P1 remains IN_PROGRESS / NOT ACCEPTED; P2 remains DRAFT / NOT ACCEPTED. Phase 04–09 remain gated and Phase 10/11 remain BLOCKED / NOT ACCEPTED.


## Exact-version OSV and npm license evidence — 2026-11-18

- OSV.dev exact-PURL query coverage: **1,824/1,824 unique exact npm PURLs** and **112/112 unique exact PyPI PURLs** (104 from Kinetic Music Video platform locks + 2 Kinetic Film exact requirements + 6 MoreAI API/Worker direct pins). Total 1,936 unique exact coordinates queried.
- OSV returned **40 vulnerable npm coordinates / 134 advisory associations** and **9 vulnerable Python coordinates / 113 advisory associations**. Total: **49 exact vulnerable coordinates / 247 advisory associations**. The full exact package/PURL/advisory IDs are persisted in `MOREAI_P1_OSV_NPM_VULNERABLE_COORDINATES_20261118.csv` and `MOREAI_P1_OSV_PYPI_VULNERABLE_COORDINATES_20261118.csv`.
- Representative Python advisories were opened and range-reviewed: certifi 2026.7.22 (CRITICAL, safe 2026.10.19+), Pillow 12.3.0 (HIGH for GHSA-22hg; fixed 13.0.0), filelock 4.2.0 (MODERATE for GHSA-2g95; fixed 4.2.1), protobuf 4.25.9 (HIGH; fixed 5.29.6), setuptools 81.0.0 (MODERATE; fixed 83.0.0), torch 2.11.0 (LOW; fixed 2.13.0). Other advisory associations still require individual severity, fixed-version, alias and reachability review.
- Notable npm findings include `@azure/msal-node@5.1.5`, `@modelcontextprotocol/sdk@1.30.0`, `node-forge@1.4.0`, multiple `undici` versions, `dompurify@3.4.15`, `hono@4.13.13`, and multiple parser/URL/glob packages. Full list is in the npm risk register.
- Exact-version npm package LICENSE file text was located for all 12 prior registry-license review entries: six AG-UI packages MIT; base-64 MIT; khroma MIT; limiter MIT; qrcode-terminal Apache-2.0; requireg ISC; cspell common misspellings CC-BY-SA-4.0. Evidence includes exact package URLs, tarball registry SHA-512 integrity, and CDN-advertised LICENSE-file SHA-256. The 11 missing registry license fields remain null but have package-file evidence; the CC BY-SA entry needs attribution/share-alike review. Tarball bytes were not independently downloaded/rehashed, and other NOTICE/source-header coverage remains incomplete.
- Full reconciliation report: `MOREAI_P1_OSV_AND_NPM_LICENSE_RECONCILIATION_20261118.md`.
- OSV attribution from OSV.dev and GitHub Advisory Database (CC-BY-4.0) is retained in the report. Vulnerable coordinates remain `BLOCK_IMPORT_UNTIL_TRIAGE`; no dependency versions or package manifests were changed.
- The 32 unresolved/ranged PyPI BOM entries and 24 ranged/unpinned OpenManusWeb requirements remain outside exact-version query coverage. The SBOM and full vulnerability/license gates remain incomplete.
- P1 remains IN_PROGRESS / NOT ACCEPTED; P2 remains DRAFT / NOT ACCEPTED. Phase 04–09 remain gated; Phase 10/11 remain BLOCKED / NOT ACCEPTED. No packages were installed, no tests/builds/provider calls/database writes/migrations/staging/deployment were run.


## Correction — unique PURL counts and MoreAI direct Python pins (2026-11-18)

A follow-up parse of CycloneDX component properties corrected the OSV coverage denominator:
- npm: 1,963 component rows = 1,940 exact-version rows and 23 unversioned MoreAI root `package.json` ranges. After PURL deduplication there are **1,824 unique exact npm PURLs**; all 1,824 were queried. The 116-row difference between exact component rows and unique PURLs is repeated PURL identity across component/source contexts, not missing query coverage.
- PyPI: 32 BOM component rows = 24 ranged/unpinned OpenManusWeb rows plus 8 direct-pin rows representing 6 unique MoreAI API/Worker PURLs. Those six direct pins were queried in addition to 104 Kinetic Music Video and 2 Kinetic Film exact pins, giving **112 unique exact PyPI PURLs queried**.
- Three MoreAI direct Python dependencies returned vulnerable: `python-multipart@0.0.20` (14 advisory associations; HIGH representative advisory, fixed 0.0.30), `cryptography@44.0.2` (10 associations; HIGH representative advisory, fixed 48.0.1 for PyPI wheels), and `pytest@8.3.5` (2 associations; MODERATE representative advisory, fixed 9.0.3). `fastapi@0.115.12`, `httpx@0.28.1` and `uvicorn@0.34.0` returned no matching advisory.
- Corrected total: **1,936 unique exact PURLs queried** (1,824 npm + 112 PyPI), **49 vulnerable coordinates** (40 npm + 9 PyPI), **247 advisory associations**. This supersedes the prior 2,069/46/221 figures in the preceding addendum.
- The Python vulnerable-coordinate register now includes the three direct dependency records. The full report's correction addendum documents the denominator and package details.
- 23 npm root dependencies and 24 Python requirements remain unpinned/unresolved and outside exact-version query coverage. No dependency versions were changed; P1 remains IN_PROGRESS / NOT ACCEPTED.


## Executable source review — Batch 05 (2026-11-18)

- Reviewed 8 additional pinned Scenario Skills source files: seven Blender modules (lighting/rendering, previs/storyboard, retopology, rigging, sculpting, materials/shading, UV/baking) and one Maya animation module.
- Static findings: Blender render/scene mutation and image parsing, large mesh/UV operations, a fixed-argv Blender subprocess in `bx_rig.cycle_check` (300s timeout), and Maya plan/audio file processing plus sibling GUI/toolkit dependencies. All 8 remain DEFER pending isolated DCC worker architecture, full source/dependency/license review and output-path confinement.
- Report: `MOREAI_P1_EXECUTABLE_PAYLOAD_MANUAL_REVIEW_BATCH_05_20261118.md`, commit `04ca37af78654e220f78fa6aba7bc6362cf7183b`.
- The selected-payload per-file operational disposition CSV now links these 8 paths to Batch 05; evidence update commit `1f6037e615bb785ba2e4c3419b205b24911f38d7`.
- Executable-source manual review is now **47/875**; 828 remain. All eight rows retain DEFER / FINAL_HOLD.
- P1 remains IN_PROGRESS / NOT ACCEPTED; P2 remains DRAFT / NOT ACCEPTED. No source execution, DCC application, test/build, provider call, database write/migration, staging or deployment occurred.


## Executable source review — Batch 06 and consolidated risk register (2026-11-18)

- Reviewed 8 additional Maya DCC files covering deformation, mesh audit/review/validation, FX, groom, lighting and look development. All remain DEFER.
- **High-risk finding:** `scenario-maya-groom/scripts/mx_groom.py` evaluates Maya menu callback strings using `mel.eval` and Python `exec`; it also loads/replays MEL recipes from JSON. `scenario-maya-fx/scripts/mx_fx.py` writes Python code into MASH Python nodes. These are explicit dynamic execution boundaries and must not be exposed as ordinary customer-callable skills.
- Other reviewed modules invoke Arnold `kick`, `imconvert`, `ffmpeg`, and write/render files. They require isolated, non-root, resource-limited DCC workers with fixed binaries, path confinement, process-tree cancellation, approval and audit.
- Several Maya source headers state that Maya 2027 / Arnold / MtoA API calls are not yet run or verified. Under the current no-real-world-testing restriction, these remain unaccepted.
- Batch report: `MOREAI_P1_EXECUTABLE_PAYLOAD_MANUAL_REVIEW_BATCH_06_20261118.md`, commit `ad790422781bd41e700e11521ba8aff67a0e54cd`. Per-file ledger evidence update commit: `0dc8230a39ebd4a25805a8f8ea7d87b6f99811e7`.
- Executable-source manual review is now **55/875**; 820 remain. The 8 rows link to Batch 06 and retain DEFER / FINAL_HOLD.
- Consolidated 12-item security risk register created at `MOREAI_P1_SECURITY_RISK_REGISTER_20261118.csv`, commit `2522c153d677349d80cc9948bdfad7edd2ae86f3`. It covers dynamic code execution, DCC subprocesses, untrusted asset parsers, vulnerable npm/Python coordinates, unpinned dependencies, Supabase Auth warning, index tuning and license/provenance gaps.
- P1 remains IN_PROGRESS / NOT ACCEPTED; P2 remains DRAFT / NOT ACCEPTED. No Maya/DCC execution, tests/builds, provider calls, Supabase writes/migrations, staging or deployment occurred.


## Supabase migration parity finding — 2026-11-18

A read-only comparison between current `main` and `supabase_migrations.schema_migrations` found a material migration-history drift:
- Supabase applied history: **116 rows**; current `supabase/migrations`: **85 SQL files**.
- **7** exact version+name matches.
- **72** current repo files share a logical name with applied history but have a different version; these map to **77 applied rows** because five logical migration names are duplicated in history.
- **32** applied migration names have no current source file.
- **6** current repo migration files are not present in applied history by name.
- Five duplicate applied logical names: workspace CAS versioning, workspace file version history, workspace restore approval key, customer learning progress and Knowledge RAG vector.
- `schema_migrations` has `version`, `statements`, `name`, `created_by`, `idempotency_key`, `rollback`; no checksum column. Therefore same-name migration files cannot be assumed byte/SQL-equivalent without comparing statement arrays.
- Matrix: `MOREAI_SUPABASE_MIGRATION_PARITY_20261118.csv` (116 applied + 6 repo-only rows); report: `MOREAI_SUPABASE_MIGRATION_PARITY_AUDIT_20261118.md`.
- Phase 05 is now **REVIEW_REQUIRED**, not COMPLETE, until statement-level reconciliation, missing historical source recovery and repo-only migration intent review are complete. No db push, repair, migration or DB write was executed.
- Do not run `supabase db push` or apply the six repo-only files before the migration baseline is reconciled and product-owner approval is recorded.


### Migration history recovery evidence

The 32 applied migration history rows whose names have no current repo source each contain one stored SQL statement in `schema_migrations.statements`; their `rollback` arrays are NULL. This provides potential read-only recovery evidence, but the statements have not been exported or replayed. The migration table has no checksum column. Any recovery must inspect for embedded credentials/environment-specific values, compare against surviving source/commits, calculate hashes and store recovered SQL outside `supabase/migrations/` as archive-only evidence. Do not replay these statements.


## Executable source review — Batch 07 (2026-11-18)

- Reviewed 8 additional Maya/ZBrush DCC files: Maya modeling, pipeline scripting, retopology/UV, rigging, ZBrush GoZ automation, plugin operations, character/creature tooling and OBJ audit.
- Key security boundary: `mx_run.py` launches mayapy and executes a job file with Python `runpy`. Scene script nodes are disabled by default, but any customer-controlled job path would still be arbitrary code execution. Job files must be server-generated, signed/allowlisted, and workspace-confined.
- `mx_pipeline.py` uses per-scene mayapy process isolation/timeouts but accepts job/scene/output/plugin/env/script-node controls; these require fixed schemas and server-side allowlists. ZBrush GoZ modifies shared user preferences and launches the desktop app; it is not multi-tenant API safe.
- ZBrush plugin and character modules explicitly state live ZBrush operations have not been run; several plugin paths are tagged [verify]. OBJ audit lacks explicit input-size/mesh complexity limits. All remain DEFER.
- Report: `MOREAI_P1_EXECUTABLE_PAYLOAD_MANUAL_REVIEW_BATCH_07_20261118.md`, commit `52311f9f55938d779c9b6834a89f3be545036324`. Per-file ledger update commit `c7d2f4a065caeb3e0552f502da226e300b7dff7f`.
- Executable-source manual review is now **63/875**; 812 remain. Eight rows are linked to Batch 07 and remain DEFER / FINAL_HOLD.
- P1 remains IN_PROGRESS / NOT ACCEPTED; P2 remains DRAFT / NOT ACCEPTED. Phase 05 remains REVIEW_REQUIRED due migration parity; Phase 04 and 06–09 remain gated; Phase 10/11 BLOCKED / NOT ACCEPTED.
- No Maya/ZBrush runtime, tests/builds, provider calls, Supabase writes/migrations, staging or deployment occurred.
