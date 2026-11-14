# P1 Continuation — Content-Level Audit & File Parity

**Date:** 2026-11-14  
**Repository:** `fadliansyah36/More-AI-Portal-Indihome`  
**Branch:** `main`  
**Reviewed main HEAD:** `cc74a6a00269c13d3e42ce7dd1ccbf3665fdbaff`  
**Status:** CONTINUATION IN PROGRESS — recursive tree parity is established; content/dependency/security sign-off is not complete.  
**Execution constraints:** no package installation, no upstream script execution, no build/lint/typecheck/tests, no browser/API/provider probes, no staging, no Supabase mutation/migration apply, no deployment.

## 1. Decision summary

This increment reviewed the pinned recursive source trees, selected implementation files, skill entrypoints and governing documents. It advances the content-level audit but does **not** close P1. The current evidence is insufficient to assert a final legal/security disposition for every external file or a complete transitive dependency SBOM.

No external source code or skills were imported into MoreAI in this increment. This is deliberate: the audit found architecture conflicts that make wholesale import unsafe and contrary to `AGENTS.md`.

### Immutable source pins and tree parity

| Source | Pinned commit | Files | Directories | Bytes | Tree |
|---|---|---:|---:|---:|---|
| CopilotKit/OpenFuse | `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc` | 219 | 32 | 4,345,760 | complete; `truncated=false` |
| smixs/visual-skills | `61a60d317f0fa0c3dc98902e58a7cb178838ae3f` | 60 | 8 | 676,353 | complete; `truncated=false` |
| scenario-labs/skills | `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | 2,114 | 702 | 62,154,351 | complete; `truncated=false` |
| **Total** | | **2,393** | **742** | **67,176,464** | **all complete** |

The companion `external-source-file-inventory.json` contains the path, size and Git blob SHA-1 for every tracked file. Git blob SHA-1 is not a raw-file SHA-256. No SHA-256 is claimed. The existing first-pass category totals are metadata classifications, not final content decisions: 5 governance/license, 38 governance docs, 788 documentation/skill knowledge, 150 build/config/scripts, 685 implementation candidates, 248 assets/domain resources, 437 tests/evidence and 42 other/manual-review.

## 2. OpenFuse content audit

### 2.1 Recursive structure inspected

- `apps/computer/`: 5 files — Docker boundary, file bridge and smoke evidence.
- `apps/mobile/`: 54 files — full standalone React Native/web UI, browser/computer console, chat, threads, queue, PDF reader and presentation cards.
- `apps/server/`: 36 files — Hono server, local auth, database/store, agent and task engine, browser/computer services, Google integration, PDF/files, workspace and finance.
- `apps/worker/`: 22 files — separate browser worker, network/proxy/downloads, Docker and lifecycle evidence.
- `packages/domain/`: 5 files — task/agent/computer domain types.
- `packages/integrations/`: 3 files — Google, PDF and vault adapters.
- `packages/backends/`: 1 file — OpenBot backend adapter.
- Root includes package/workspace manifests and lockfile, infra, patches, docs, tests and deployment configuration.

### 2.2 Content findings from manifests and implementation samples

The root package manifest declares Node >=22 and pnpm 11.19.0. Direct dependencies include Hono, PGlite, `pg`, CopilotKit runtime/AG-UI, MCP SDK, TanStack AI provider packages, E2B desktop, pdf-lib and Zod. Workspace packages are only mobile and worker. The package graph therefore describes a separate TypeScript application/server architecture, not a drop-in library for the MoreAI FastAPI/OpenManus backend.

Reviewed implementation samples:
- `apps/server/src/auth.ts`: live mode uses one configured access key and creates a local owner identity (`local-user`); this is not MoreAI Supabase Auth, customer identity, tenant membership or RLS authorization.
- `apps/server/src/db.ts`: record store is backed by PGlite or PostgreSQL abstraction with owner/kind/id records. PGlite/local record persistence is a competing persistence model; the generic store contract is not a MoreAI data migration.
- `apps/server/src/engine/worker.ts` and `packages/domain/src/agent.ts`: standalone task worker, leases, task status, plan/evidence/checkpoints/events. These concepts map to MoreAI's existing durable Agent Runs/Steps/Events/Checkpoints and worker, but importing the task engine would create a second execution authority.
- `apps/server/src/browser.ts`: browser sessions and worker HTTP bridge. Useful capability patterns, but must be reimplemented/adapted through MoreAI's isolated sandbox/browser boundary, ownership, SSRF/egress policy, lease and durable run receipts.
- `apps/server/src/computer.ts`: command execution, workspace files, Docker/E2B desktop backends and resource caps. Not safe to expose as a normal API tool; MoreAI sandbox remains the required execution boundary.
- `packages/integrations/src/pdf.ts`: bounded PDF parsing/field handling patterns can inform the existing Files/Artifacts pipeline; retain file-size/page/decompression safeguards and existing owner/tenant controls.
- README distinguishes current alpha features from roadmap. OpenFuse describes itself as a standalone app with its own server, task worker and browser worker; roadmap items must not be represented as implemented.

### 2.3 OpenFuse disposition

| File family | MoreAI owner | Decision |
|---|---|---|
| Chat/AG-UI stream and rich cards | Existing Chat + typed client + FastAPI/OpenManus event projection | **ADAPT PATTERNS**; do not import mobile UI |
| Follow-up queue and retained draft | Existing conversation/message lifecycle | **MAP/ADAPT** only if absent in current canonical lifecycle |
| Agent/task plans, steps, lease, retry, cancel, events | Existing Agent Run/Step/Event/Checkpoint + worker | **ADAPT DATA/EVENT SEMANTICS**; exclude second task worker |
| Browser profiles/session/takeover | Existing tool registry + isolated sandbox/browser + Files/Artifacts | **DEFER/BLOCKED** until tenant isolation, egress/SSRF, session lease, approval and receipt controls exist |
| Computer/terminal/workspace | Existing sandbox | **DEFER/BLOCKED**; no host mounts/secrets, non-root and network-deny-by-default required |
| Action approval/receipts | Existing approval/audit lifecycle | **ADAPT** to exact tenant/user/run/step/action hash and idempotency |
| PDF/CSV/files | Existing Files/Analyse/Artifacts | **ADAPT SELECTED LOGIC** after security and ownership review |
| Goals/monitoring/ideas/notifications | Existing Workflow scheduler + durable Agent Runs + notifications | **ADAPT CONCEPTS**; scheduler only enqueues canonical Agent Runs |
| Hono API, PGlite store, OpenFuse local auth, standalone worker | FastAPI + Supabase + OpenManus + MoreAI worker | **EXCLUDE** as competing architecture |
| OpenFuse React Native app/screens | Existing Next.js Customer UI | **ARCHIVE-ONLY**; do not mount or redesign |

OpenFuse root MIT notice must be preserved for any substantial copied portions. SECURITY.md's one-owner/shared-access-key deployment model is not accepted as MoreAI multi-tenant authentication. No implementation import is approved by this audit.

## 3. Visual Skills content and attribution audit

### 3.1 Complete tree contents

The 60-file tree consists of:
- `image/SKILL.md` and 23 image references;
- `video/SKILL.md` and 12 video references;
- 3 root license/notice/readme files;
- 2 plugin manifests;
- 16 image assets/logos plus 2 dramaturgy banners and a hero asset.

The image entrypoint explicitly says it writes prompts and does not generate images. It mandates reading model selection, a selected model reference, golden rules, task-specific references and creative direction in sequence. The video entrypoint requires dramaturgy and universal rules before choosing the model-specific reference, with task-shaped references such as storyboard, cinematography and genre.

Content samples reviewed: image skill entrypoint and model-routing reference; video skill's director workflow and dramaturgy reference; root NOTICE. The remaining individual references/assets/plugin manifests have not all received semantic, embedded-source and third-party asset review.

### 3.2 Attribution and disposition

- Root license: CC BY 4.0.
- Required attribution: **Serge Shima — https://github.com/smixs/visual-skills** (NOTICE also supplies author contact/site references).
- NOTICE identifies methods adapted/re-written after study of `agentara/skills` under MIT; retain that acknowledgement where relevant.
- Any adapted material must identify modifications and preserve attribution. Do not represent upstream material as original MoreAI-authored content.
- Skill procedures are eligible to be transformed into MoreAI-owned, attributed knowledge records after all linked references and third-party source/asset review. They are not executable provider adapters and do not grant tool permissions.

**Decision:** candidate for selective inclusion in the existing Skill Registry and Create prompt/workflow guidance; **no wholesale copy and no production import approval yet**.

## 4. Scenario Skills family audit

### 4.1 Recursive family distribution

The 2,114-file tree includes 172 skill entrypoint links in the earlier repository listing, a large expert-tools surface and supporting references/scripts/assets/tests. Major groups include:
- Scenario MCP core and general creative skills: image, video, audio, textures, skyboxes, 3D, editing, consistency, asset analysis, model training and moderation.
- Provider/model-specific families: GPT Image, Gemini, Seedream, Reve, Ideogram, Grok Imagine, Kling, Veo, Seedance, Runway, Luma, Wan, Vidu, Minimax, Meshy, Rodin and Sparc3D.
- Workflow/governance: workflows, workflow authoring, task tracking, reporting, quality gate, team/admin analytics and moderation.
- DCC/game-engine expert families: Blender, Maya, ZBrush, Unreal, Unity, Godot and Roblox, with scripts, references, templates, tests and family READMEs.
- Repository-level scripts, tests, lockfiles, plugin metadata, CI and maintainer/agent instructions.

### 4.2 Content samples and mandatory integration pattern

Reviewed the Scenario AGENTS.md, root README, core Scenario skill, image/video/3D/workflow skill entrypoints and one provider-specific image skill. Their operational contract is materially important:
1. discover a currently available model/tool dynamically;
2. fetch the exact input schema before invocation;
3. validate inputs and dry-run cost;
4. execute an idempotent job;
5. wait/monitor using returned job identifiers;
6. review and persist resulting artifacts;
7. settle credits using MoreAI's canonical wallet/ledger/usage accounting.

Provider/model names and parameter schemas are dynamic and must not be hardcoded from static skill text. The repo's own AGENTS.md requires public-source grounding, unique skill names, direct one-level links for supporting files, per-skill metadata, and tests for shipped scripts. Its DCC/game-engine skills require locally installed applications and authorized execution channels.

### 4.3 Scenario disposition by family

| Family | MoreAI owner | Decision |
|---|---|---|
| General image/video/audio/texture/skybox/3D guidance | Existing Skill Registry + Create | **SELECTIVE KNOWLEDGE ADAPTATION** after content and attribution review |
| Provider/model-specific generation | Existing provider adapter + model router + Create | **SCHEMA-DRIVEN ADAPTER ONLY**; discover and fetch schema at runtime; no hardcoded model IDs |
| Image/video/3D generation jobs | Existing durable Agent Run/Step/Events + Files/Artifacts + wallet/ledger | **MAP TO EXISTING LIFECYCLE**; no second job store or credit ledger |
| Scenario saved workflow graph | Existing MoreAI Workflow + OpenManus orchestration | **ADAPT AS PROVIDER CAPABILITY ONLY**; do not replace MoreAI workflow authority |
| Team/admin/analytics/moderation/task tracking | Existing MoreAI admin/control plane, entitlements, audit and Agent Runs | **SELECTIVE REVIEW**; no external identity or admin authority |
| Blender/Maya/ZBrush/Unreal/Unity/Godot/Roblox expert tools | Optional Skill Registry knowledge | **DEFER** unless a supported local execution agent and explicit user authorization exist |
| Scripts, templates, binary assets, generated manifests, CI and tests | None by default | **ARCHIVE/REVIEW**; no import or execution without file-level provenance and dependency approval |

Scenario root license is MIT. The skill-creator subdirectory contains an additional LICENSE.txt and must be preserved if that material is ever adapted. Each imported skill's metadata and linked support files need per-skill review; root MIT alone is not sufficient to clear all embedded third-party assets/tutorial content.

## 5. Dependency graph and SBOM status

### OpenFuse
Direct dependencies were read from the pinned root package manifest and workspace config. Lockfile is inventoried. No package installation or lockfile resolution was performed. A transitive dependency/license SBOM is **not complete**. Architecture conflicts identified: Hono server, PGlite/standalone store, local owner/session auth, CopilotKit Intelligence persistence, independent worker and React Native shell.

### Visual Skills
No package manager dependency graph is declared in the pinned root tree. Plugin manifests and external references still require provenance review; this is a content/attribution surface rather than a runtime package dependency graph.

### Scenario Skills
Root package and lockfiles, plugin manifests, scripts and tests are inventoried. No install, package resolution, script execution or test execution occurred. Transitive dependency/license SBOM is **not complete**. The large expert-tool scripts have external runtime dependencies (DCC/game-engine applications and APIs) and are not deployable as ordinary MoreAI web/API modules.

## 6. Canonical MoreAI capability ownership — no duplicate engines

| Capability | Canonical owner | Non-negotiable boundary |
|---|---|---|
| Agent reasoning/planning/tool selection | OpenManus in `engine/` | Sole agent execution authority |
| Customer business API | `apps/api` FastAPI | Web → typed API client → FastAPI |
| Durable execution | `apps/worker` + existing Agent Run lifecycle | Queue/outbox, leases, checkpoints, retry/cancel/recovery |
| LLM/provider/model selection | Existing gateway/router/provider adapters | Server-side secrets, policy, entitlement, usage and cost |
| Browser/computer execution | Existing sandbox/tool registry | Isolated, tenant-bound, fail-closed until security boundary exists |
| Memory | Existing memory service/store + Supabase | One coordinator/store; explicit consent, provenance, scope, sensitivity and lifecycle |
| Skills | Existing Skill Registry/Resolver | Versioned, attributed, reviewed knowledge; skills cannot grant permissions |
| Create and visual/media generation | Existing Create + provider adapter | Discovery/schema/dry-run/job/artifact/settlement |
| Workflow | Existing MoreAI Workflow + OpenManus orchestration | Provider graphs cannot become a second orchestrator |
| Files and artifacts | Existing Files/Artifacts + Supabase Storage | Owner/tenant checks and server-side access |
| Wallet/credits | Existing wallet, quota, immutable ledger | No provider-side or skill-side balance authority |
| Customer UI | Existing Next.js dashboard | Protected visual surface; minimal integration seams only |

## 7. Per-file parity and final disposition policy

The recursive inventory is complete for path/size/blob identity. The existing JSON's `preliminary_disposition` values remain explicitly preliminary. This audit establishes these disposition rules:
- **COPY / ARCHIVE-ONLY:** license notices, provenance metadata and source snapshot material needed for reproducibility; no execution.
- **ADAPT:** isolated concepts/algorithms only after file-content review, dependency/license review and mapping to an existing MoreAI owner.
- **EXCLUDE:** competing UI shell, identity/auth, persistence, task/agent engine, wallet/ledger or workflow authority.
- **DEFER:** browser/computer/DCC/provider functionality until its MoreAI security, runtime and provider contracts are in place.
- **MANUAL REVIEW:** opaque assets, generated files, external tutorial-derived content, unknown licenses, lockfile/transitive dependencies and scripts.

**P1 final file-level sign-off is not yet justified.** In particular, not every one of the 685 preliminary implementation candidates, 248 assets/resources and 437 tests/evidence files has had individual content and provenance review; nested third-party notices and dependency license resolution remain open. It would be inaccurate to label the 2,393 files as fully content-audited or to close P1 from tree metadata alone.

## 8. Remaining P1 closure gates

1. Complete file-content review for all OpenFuse app/package implementation candidates, especially OAuth/Google, mail/calendar, finance, vault, network proxy, downloads, workspace and server actions; document security findings per file.
2. Inspect every Visual Skills reference, image/logo asset and plugin manifest; resolve third-party provenance and attribution.
3. Review Scenario skills by family and every skill's linked references/scripts/assets/tests/metadata; resolve embedded source and dependency license notices.
4. Produce a reproducible transitive dependency SBOM from pinned lockfiles without installing/executing packages; record package/version/license/source and unresolved licenses.
5. Replace preliminary manifest classifications with evidence-backed per-file `copy`, `adapt`, `archive-only`, `exclude` or `defer` decisions and explicit review status.
6. Map accepted capabilities to exact MoreAI source modules, existing schema/RLS and customer UI integration points; retain fail-closed states where security/runtime prerequisites are absent.
7. Update the official phase tracker only after evidence. P1 closes only when all above are signed off.

## 9. Return to mandatory Phase 00–11

P1 is a source-governance prerequisite, not a replacement for mandatory phases 00–11. Current known dependency state remains:
- 00 baseline/UI freeze: recorded complete.
- 01 source pin/provenance: pin/tree evidence exists; governance sign-off remains open.
- 02 workspace foundation: recorded complete.
- 03 complete pristine OpenManus source copy: recorded complete by prior manifest; no change here.
- 04 backend integration/security: in progress.
- 05 Supabase schema reconciliation: tracker recorded complete; no database changes here.
- 06 FastAPI/OpenAPI: in progress.
- 07 durable worker lifecycle: in progress.
- 08 LLM/tools/orchestration: in progress.
- 09 existing Customer Dashboard integration: in progress and dependent on backend/API/worker contracts.
- 10 end-to-end verification: not accepted under the current no-real-testing instruction.
- 11 release gate: blocked until required verification evidence exists.

**Next dependency-ordered phase after this P1 increment:** continue P1 closure (per-file content, dependency SBOM and final disposition). Once P1 is signed off, resume the earliest incomplete mandatory dependency: **Phase 04 — Full Backend Integration & Security Hardening**, then Phase 06/07/08 as their dependency graph requires, and Phase 09 customer-dashboard integration after those contracts are ready. Do not skip to product feature expansion. Phase 10/11 remain explicitly unaccepted while real verification is disallowed.


---

## 10. Second content-audit increment — deeper file and lockfile evidence

**Audit increment date:** 2026-11-14  
**Reviewed external source pins unchanged.** This section adds file-level evidence and corrects the distinction between a complete recursive inventory and a fully signed-off disposition manifest.

### 10.1 OpenFuse — additional files and dependency graph evidence

Additional pinned files read:
- root `package.json` (blob `1c2b85d7257886d8c8df99cc8a043c5b5ab58411`);
- root `pnpm-lock.yaml` (blob `1f64461ae3c5e6c69b5c8c04826fe7bdbac1f016`);
- `SECURITY.md` (blob `bcdfc706eac000d6d91747f902670eb49bbae95f`);
- implementation samples recorded in Section 2: auth, store, browser, computer, worker, domain, PDF.

Lockfile evidence:
- pnpm lockfile v9, 516,017 bytes;
- 3 workspace importers: root, `apps/mobile`, `apps/worker`;
- approximately 2,341 package/snapshot entries (counted from lockfile package-key records);
- 1,452 integrity records;
- one patched dependency declaration (`metro@0.83.3`) and one override (`image-size@2.0.4`).

The lockfile records resolved versions and integrity but does **not** provide a complete license attribution for each resolved package. A license-aware SBOM still requires package metadata/license resolution against the pinned package artifacts. No install or package execution was performed.

**Additional security decision from SECURITY.md:** OpenFuse's supported deployment is one owner per deployment; shared access key is not multi-tenant identity. Its browser worker is explicitly not a full hostile-tenant security boundary. E2B desktop mode enables outbound internet, passwordless sudo inside the VM, publicly reachable forwarded VM ports, and a VNC URL whose effective password is short; the policy itself warns that prompt-injected computer/browser actions can exfiltrate data. These are concrete reasons to exclude OpenFuse auth/persistence and defer direct browser/computer backend reuse. A MoreAI implementation must independently enforce tenant identity, isolated execution, egress policy, secret isolation, authenticated session transport, explicit human approval, action receipts and durable recovery.

OpenFuse source family counts from the pinned recursive tree:
- `apps/server`: 36 files;
- `apps/worker`: 22 files;
- `apps/computer`: 5 files;
- `apps/mobile`: 54 files;
- `packages/domain`: 5 files;
- `packages/integrations`: 3 files;
- `packages/backends`: 1 file;
- remaining root/governance/docs/tests/config: 93 files.
- 75 files classified as test/test-support paths by path convention; 140 source/script-like paths by extension/path convention; 4 image/PDF assets. These are inventory classifiers, not a claim that every file's semantic content was individually reviewed.

### 10.2 Visual Skills — content structure and attribution evidence

The pinned tree has exactly:
- 2 skill entrypoints: `image/SKILL.md`, `video/SKILL.md`;
- 24 image-family files and 13 video-family files (37 total, including their reference materials);
- 16 visual assets under `assets/`;
- root `LICENSE`, `NOTICE`, English and Russian README files, and two plugin metadata files.

Additional files read: root `NOTICE`, `video/SKILL.md`, and `image/references/golden-rules.md`, alongside the previously read image entrypoint and model reference. The image entrypoint expressly requires model-specific reference reading and states it produces prompts rather than generating images. The video entrypoint routes through dramaturgy/universal rules and task-specific storyboard/cinematography references.

**Attribution decision remains mandatory:** CC BY 4.0, attribution to Serge Shima and source URL, plus modification notice for adapted content. NOTICE also acknowledges methods studied/adapted from `agentara/skills` under MIT. Logo artwork and all 16 assets remain separate provenance/brand/trademark review items; their presence in the repository does not grant MoreAI an unrestricted right to redistribute brand marks.

The two skill entrypoints are candidates for a curated, attributed knowledge adaptation. No asset/logo is approved for direct customer-facing redistribution by this increment. All 37 family files and 16 assets have path-level inventory coverage, but not every reference and asset has individual semantic/provenance sign-off; P1 therefore remains open.

### 10.3 Scenario Skills — family, script, asset and dependency evidence

Pinned recursive-tree counts:
- 179 `SKILL.md` entrypoints across Scenario and supporting agent skills;
- 1,664 files beneath `skills/`;
- 1,147 script/source-like paths by extension/path classifier;
- 92 image/video/font/PDF and other asset-like paths;
- 372 test/test-support paths by path classifier;
- 318 paths beneath `tests/` (the broader 372 classifier also includes tests/fixtures outside that directory).
- 2,114 total files and 702 directories; `truncated=false`.

Additional pinned files read:
- root `package.json` (blob `3d3b31e566918356ed2bf7ee0d88d87a04c5c330`);
- root `pnpm-lock.yaml` (blob `a9bfa48bafc6cbd1b4c4652972ae6eeeaa27e098`);
- root `AGENTS.md` and README;
- `.agents/skills/skill-creator/LICENSE.txt` (blob `4f881c52d1f72f4cfb720e339e2d35c3058d01a9`);
- `skills/scenario-image/SKILL.md`, `skills/scenario-video/SKILL.md`, `skills/scenario-3d/SKILL.md`, `skills/scenario-workflows/SKILL.md`, `skills/scenario-gpt-image/SKILL.md`.

Lockfile evidence:
- pnpm lockfile v9, 130,017 bytes;
- one root workspace importer;
- approximately 693 package/snapshot entries;
- 466 integrity records.
- package manifest is a private skill repository, pnpm 11.21.0, Node >=22.18.0. Its validation/test scripts invoke repository-maintenance, Python lint and skill script suites; these were not run. The lockfile supplies versions/integrity, not full per-package license decisions.

License finding: root Scenario Skills license is MIT. The nested `.agents/skills/skill-creator/LICENSE.txt` is Apache License 2.0 and must be preserved for any material derived from that subtree. Each skill may link supporting material, scripts, model/provider docs, examples and assets; the root MIT license alone is not a blanket provenance clearance for third-party embedded content.

The entrypoint count and tree family inventory are complete. However, every one of 179 skill entrypoints and its transitive references/scripts/assets has not yet been individually fetched and semantically reviewed in this increment. Therefore this is family-level evidence, not final per-file legal/security sign-off.

### 10.4 Updated exact file disposition examples

| Source path / family | Disposition | Evidence / reason | MoreAI owner |
|---|---|---|---|
| OpenFuse `apps/server/src/auth.ts` | **EXCLUDE** | Local single-owner/shared access-key session model | Supabase Auth + FastAPI authz |
| OpenFuse `apps/server/src/db.ts` | **EXCLUDE** | PGlite/generic record store competes with canonical persistence | Supabase repositories |
| OpenFuse `apps/server/src/engine/worker.ts` | **ADAPT** | Lease/checkpoint/event patterns only; do not import task worker | MoreAI worker + Agent Run lifecycle |
| OpenFuse `apps/server/src/browser.ts` | **DEFER** | Browser worker bridge needs MoreAI tenant/egress/session controls | Existing sandbox + tool registry |
| OpenFuse `apps/server/src/computer.ts` | **DEFER** | Docker/E2B computer service has explicit single-owner and egress limitations | Existing isolated sandbox |
| OpenFuse `packages/integrations/src/pdf.ts` | **ADAPT** | Bounded PDF processing patterns, subject to Files pipeline ownership | Files/Artifacts |
| OpenFuse `apps/mobile/**` | **ARCHIVE-ONLY** | Competing standalone UI; customer UI is protected | Existing Next.js dashboard |
| Visual `image/SKILL.md`, `video/SKILL.md` | **ADAPT** | Prompt/storyboard knowledge with attribution and linked-reference review | Skill Registry + Create |
| Visual `assets/**` | **DEFER** | Brand/logo and embedded asset provenance review outstanding | Not approved for customer UI |
| Scenario `skills/scenario-image/**`, `scenario-video/**`, `scenario-3d/**` | **ADAPT** | Knowledge and dynamic schema-driven capability guidance only | Skill Registry + Create + provider router |
| Scenario provider-specific skills | **DEFER** | Model/tool schema must be discovered live; provider availability/entitlement cannot be assumed | Provider adapters/model router |
| Scenario `skills/dcc/**`, `skills/game-engines/**` | **DEFER** | Scripts depend on local DCC/game-engine runtime and execution authorization | Optional isolated execution agent |
| Scenario `tests/**`, root CI/scripts | **ARCHIVE-ONLY** | Upstream verification evidence/tooling, not MoreAI runtime code; do not execute | Source governance archive |
| Scenario root `LICENSE` | **COPY** | Preserve MIT notice for adapted/reproduced portions | Source governance |
| Scenario skill-creator `LICENSE.txt` | **COPY** if subtree reused; otherwise **ARCHIVE-ONLY** | Nested Apache-2.0 terms apply independently | Source governance |

These are exact reviewed-file decisions and family-level rules, **not** a complete 2,393-row final manifest. Unreviewed files remain **MANUAL REVIEW** and are not silently treated as approved.

### 10.5 SBOM and P1 closure status

| Gate | Current evidence | Status |
|---|---|---|
| Recursive path parity | All three pinned trees complete, no truncation | **GREEN** |
| OpenFuse direct manifest + lockfile inventory | Manifest and 516 KB lockfile read; 3 importers, ~2,341 entries | **PARTIAL** |
| Scenario direct manifest + lockfile inventory | Manifest and 130 KB lockfile read; 1 importer, ~693 entries | **PARTIAL** |
| Per-package resolved license SBOM | Lockfiles do not establish license metadata; package metadata/license scan not completed | **OPEN** |
| OpenFuse source semantics/security | High-risk auth/store/worker/browser/computer/PDF samples reviewed; full apps/packages file review incomplete | **PARTIAL** |
| Visual references and attribution | Entrypoints, selected references, NOTICE and 16 asset inventory reviewed; every reference/asset not individually signed off | **PARTIAL** |
| Scenario family inventory | 179 entrypoints, 1,664 skill files, 1,147 scripts, 92 assets, 372 test-like paths inventoried | **GREEN for inventory only** |
| Scenario per-entrypoint and linked-file content review | Only representative core/provider family samples reviewed; all 179 not individually signed off | **OPEN** |
| Final decision manifest for all source files | Exact examples and family rules added; full per-file disposition rows still outstanding | **OPEN** |
| P1 closure | All gates above not green | **NOT CLOSED** |

**Important no-test compliance:** No dependencies were installed, no upstream script was executed, no tests/build/lint/typecheck were run, and no staging, API/provider/browser probing, Supabase migration or deployment was performed. Lockfile inspection is static metadata analysis only.

### 10.6 Next bounded P1 work

1. Produce a reproducible package/license SBOM for the exact OpenFuse and Scenario lockfile snapshots, including unresolved license/unknown-package entries; do not install or execute packages.
2. Continue OpenFuse per-file semantic review of server actions, OAuth/Google, finance, vault, downloads/proxy/network, worker, computer and integrations; record exact path and disposition.
3. Complete Visual Skills reference and asset provenance review; keep all unverified brand marks deferred.
4. Review Scenario's 179 entrypoints in family batches, then resolve each linked reference/script/asset/test/metadata path to an exact disposition.
5. Generate a final machine-readable per-file decision manifest for all 2,393 source paths, with review status distinct from disposition; only mark reviewed when content/provenance evidence exists.
6. Close P1 only when unresolved license, provenance, security and disposition rows are zero or explicitly accepted by project governance.

**Phase sequence remains unchanged:** P1 is not complete. On closure, return to the earliest incomplete mandatory phase in `AGENTS.md`: Phase 04, then 06/07/08 and Phase 09 according to dependencies. Phase 10/11 remain unaccepted under the no-real-testing constraint.


---

## 11. Third content-audit increment — OAuth, finance, vault, worker, visual references and Scenario skill families

**Audit date:** 2026-11-14  
**Source pins unchanged.** This increment adds deeper source evidence, a machine-readable per-file handling manifest, and a lockfile-derived SPDX package inventory.

### 11.1 OpenFuse — requested security and capability families

#### Google OAuth and vault

Additional exact source review:
- `apps/server/src/google-auth.ts` (blob `ae56eb481b6cab1a52b3994d59090156ba97e193`);
- `packages/integrations/src/vault.ts` (blob `d36efce472df11916f23cd325084918c38439c78`);
- `packages/integrations/src/google.ts` (blob `12a0a28f2c08f44be844e137b4aa8b9670a9ee3e`);
- `apps/server/src/app.ts` (pinned app assembly).

Observed controls:
- OAuth uses a cryptographically random state and PKCE verifier/challenge (S256); state expires after 10 minutes and is consumed on callback.
- A generation token and compare-and-swap protect connect/disconnect races. Access/refresh credentials are encrypted in a versioned AES-256-GCM envelope with 32-byte base64 key validation and authenticated additional data.
- Refresh is serialized per owner/connection in-process; disconnect first invalidates the generation and then requests Google token revocation.
- Gmail/Calendar scopes are read-only by default; send/write scopes are added only when the caller explicitly requests write access.
- Action proposals bind the owner, Google connection, target and target version into a SHA-256 hash, expire after 30 minutes, require an approve/deny decision and support idempotency.

**Disposition:** ADAPT the OAuth PKCE, credential-envelope, scope-minimization, connection-generation and approval-hash patterns. Do not reuse the OpenFuse `Store`, session/auth owner model or its system-wide OAuth state persistence. MoreAI must bind every credential and callback to Supabase Auth user + tenant authorization, use its server-side credential vault, persist immutable approval/audit receipts, and avoid exposing provider tokens to the browser. Google provider logic is not a substitute for MoreAI's provider router.

#### Finance

Reviewed `apps/server/src/engine/finance.ts` (blob `ff92e07452f1bce22fab99da12c32da4c4afae02`). It is a bounded CSV spending analyzer:
- 500 KB input cap and 5,000-row cap;
- validates date, description, amount and category columns; rejects duplicate required headers, malformed rows and unsafe numeric ranges;
- positive amounts represent expenses and negative amounts income; it explicitly does not infer currency conversion.

It is **not** an open-banking connector, account balance provider, payment rail or ledger. **Disposition: ADAPT parser/normalization logic only** into MoreAI Files/Analyse, with source currency and import provenance explicit. Do not map this feature to wallet balance, payment execution or immutable credit ledger.

#### Worker, network/proxy and downloads

Reviewed `apps/worker/src/network.ts`, `proxy.ts`, `browser.ts`, `downloads.ts`, `server.ts`, `index.ts`, worker README and worker package manifest:
- Worker API requires a shared bearer token of at least 32 characters (except process health); documented deployment binds to loopback. App server is responsible for authentication and owner identity.
- Browser sessions are UUID-keyed, with a maximum of 3 active sessions, 20 persisted profiles and 30-minute idle close. Profiles/cookies/PDFs persist in a local Docker volume.
- URL validation allows only HTTP(S) on ports 80/443, rejects credentials/private/reserved destinations, resolves DNS and rejects if any answer is non-public. Proxy connects to the validated IP rather than resolving again, mitigating DNS rebinding at application level.
- Browser read returns visible page text; it accepts no user script/selector/evaluation input. Playwright service workers and WebSockets are disabled.
- PDF downloads are capped at 10 MiB each and 20 per session; actual stream bytes and PDF signature are checked; interrupted/failed outcomes are journaled and recoverable. The latest 100 failures are retained.
- Worker is a separate Node/Playwright service and its local profile volume contains sensitive login cookies/downloads. Its worker bearer token is a service-to-service secret, not a per-user session authorization contract.

**Security limitations from the upstream worker README:** this is application-level egress control, not a kernel firewall or proof against a Chromium exploit. Playwright's default Chromium launch disables Chromium's internal sandbox. The documented container does run as `pwuser`, without Docker socket, app/provider secrets or Linux capabilities, with read-only root filesystem and memory/process limits. The persistent profile volume must receive the same access control as user documents.

**Disposition:** ADAPT URL/SSRF validation, exact-IP proxy, bounded download and failure-journal patterns. DEFER direct worker runtime integration until MoreAI supplies a dedicated isolated browser service, kernel/network egress policy, per-tenant session binding, secure cookie vault, lease/quota, approval, audit receipt and lifecycle recovery. The OpenFuse service token must remain server-only. Browser/computer execution cannot be activated from the Customer Dashboard merely by importing this worker.

#### Computer and E2B desktop

Reviewed `apps/server/src/computer-backend.ts`, `computer.ts`, `computer-e2b-desktop.ts`, `computer-routes.ts` and `computer-tools.ts`.
- Docker backend explicitly checks a single-owner container and volume; non-root UID 1000, read-only rootfs, no privileged mode, drop all capabilities, no-new-privileges, no host binds/devices/port mappings, private IPC, resource caps and `NetworkMode=none`.
- E2B desktop is a distinct provider with outbound network enabled; its own agent instructions warn that listening ports are publicly reachable without app authentication and prohibit sending/submitting/signing in/buying/uploading without explicit user request.
- Computer operations have per-operation IDs, receipts, output/disk caps, and no automatic retry after an uncertain timeout/interruption.
- Computer HTTP routes are owner-scoped by the OpenFuse app middleware, but this does not make the standalone OpenFuse auth identity suitable for MoreAI.

**Disposition:** Docker isolation checks and operation receipts are ADAPTABLE patterns; the computer service itself is DEFERRED pending MoreAI sandbox integration. E2B outbound-network desktop is not approved for unrestricted autonomous actions. Human takeover must bind to the same durable run/session and an explicit approval receipt.

### 11.2 Visual Skills — all Markdown and vector assets reviewed

Pinned content review now covers all 39 Markdown files in the Visual Skills repository:
- 2 entrypoints (`image/SKILL.md`, `video/SKILL.md`);
- image model routing, golden rules, prompt framework, creative direction, character consistency, de-slop, editing, dimensional/structural control, text rendering, slides, storyboards, multi-panel and seven industry pattern libraries;
- video dramaturgy, universal rules, role modes, keyframes, camera/light/sound vocabulary, montage/genres, race/speed, continuity fixes and model-family references.

All 15 SVG files were read as text and inspected for external references, embedded images, remote-use elements and comments. The SVGs contain only the SVG namespace reference; no embedded raster data or external `use` references were found. This is a static SVG inspection, not a trademark or visual-asset legal clearance. The binary `assets/hero.webp` was inventoried but not visually inspected and remains DEFER.

**Attribution finding:** the exact NOTICE states copyright © 2026 Serge Shima, CC BY 4.0, and requires credit to Serge Shima plus the source repository. It separately acknowledges methods adapted/re-written after studying `agentara/skills` under MIT in named reference files. CC BY 4.0 does not grant trademark rights, so all 13 provider-logo variants remain DEFER for customer-facing use pending provider-brand permission/brand-guideline review. The two dramaturgy banners can be considered for attributed adaptation only after their embedded visual authorship is confirmed; hero binary remains held.

**Product mapping:** the image and video entrypoints are knowledge for Skill Registry/Create prompt planning, not model execution adapters. Their model names, quality/size claims, token limits and provider availability are time-sensitive content and must be treated as editorial hints, not authoritative live capabilities. MoreAI must use its own model router/provider schema discovery before execution. Skills cannot grant tool permission or bypass entitlements.

### 11.3 Scenario Skills — 179 entrypoints and family mapping

All 179 `SKILL.md` entrypoints were fetched and reviewed at entrypoint level:
- 172 product skill entrypoints under `skills/`;
- 7 internal repository-maintenance/skill-authoring entrypoints under `.agents/skills/`, disposition ARCHIVE-ONLY.

Scenario recursive tree:
- 2,114 files total; 1,664 beneath `skills/`;
- 179 skill entrypoints;
- 1,147 script/source-like files by extension/path inventory classifier;
- 92 asset-like files;
- 372 test/test-support-like paths (318 under `tests/`);
- 702 directories; `truncated=false`.

Major DCC/game-engine content families:
- DCC: Blender 98 files / 15 skill entrypoints; Maya 81 / 11; ZBrush 72 / 9.
- Game engines: Godot 307 files / 14 entrypoints; Roblox 292 / 14; Unity 388 / 14; Unreal 79 / 10.
- Remaining Scenario creative/provider/workflow/operations skills: 85 entrypoints.

#### Family decisions

| Family | File / entrypoint evidence | MoreAI owner | Decision |
|---|---:|---|---|
| General image/video/audio/3D, texture, skybox, sprites, storyboard, ad/creative | Skill entrypoints and references | Skill Registry + Create + provider router | **ADAPT KNOWLEDGE**; keep model schema dynamic |
| Provider-specific image/video/audio/3D | Model-family skill entrypoints | Provider adapters + Model Router | **ADAPT GUIDANCE ONLY**; discover model and schema live; no hardcoded model id or price |
| Scenario workflows and authoring | `scenario-workflows`, `scenario-workflow-authoring` | Existing MoreAI Workflow + OpenManus orchestration | **ADAPT CONTRACT PATTERNS**; no external workflow graph as second orchestration authority |
| Task tracking, admin, analytics, moderation, quality gates | Relevant operations skills | Existing Agent Runs, admin/control plane, audit and moderation | **SELECTIVE KNOWLEDGE ADAPTATION**; no external identity/admin authority |
| Blender/Maya/ZBrush | 35 skill entrypoints across three DCCs plus scripts/references/assets | Optional isolated DCC execution agent | **DEFER EXECUTION**; knowledge can be selectively adapted, scripts require licensed installed software, sandbox and explicit authorization |
| Godot/Roblox/Unity/Unreal | 52 skill entrypoints across four game engines plus source/assets/templates | Optional isolated game-engine execution agent | **DEFER EXECUTION**; do not import toolchains or scripts into FastAPI/Customer runtime |
| Repository maintainer/skill creator tools | 7 `.agents/skills` entrypoints | Source governance archive | **ARCHIVE-ONLY** |

The core Scenario skill prescribes: resolve team/project scope; discover/recommend model; fetch the exact schema; check plan/entitlement; dry-run cost; run idempotently; wait on returned job IDs; inspect/download artifacts; and account for credit usage. Provider-specific skills emphasize that schemas and limits vary per model and must be re-fetched. This maps to MoreAI's provider adapter → Model Router → durable Agent Run/Step/Events → Files/Artifacts → Wallet/ledger. The external Scenario workflow graph remains a provider feature, not a replacement for MoreAI's canonical workflow engine.

Nested licensing: Scenario root MIT license; `.agents/skills/skill-creator/LICENSE.txt` is Apache-2.0. Root MIT cannot be used to erase that nested license. Skill frontmatter and supporting source/assets must retain their own notices/provenance.

**Review boundary:** all 179 entrypoints have entrypoint-level content review, but not every linked `references/`, `scripts/`, `assets/`, `tests/`, plugin metadata and nested dependency has been individually read and signed off. A skill entrypoint's MIT field does not establish license clearance for every embedded third-party asset or external tutorial. All unreviewed supporting files remain held.

### 11.4 Per-file handling manifest — all 2,393 source paths now have explicit conservative decisions

Updated `docs/implementation/external-source-file-inventory.json` to schema 1.1. Every row now includes:
- `decision`: one of `copy`, `adapt`, `archive-only`, `exclude`, `defer`;
- `decision_basis` and `decision_owner`;
- `review_status` distinct from the decision.

Current counts:

| Decision | Files |
|---|---:|
| defer | 1,515 |
| archive-only | 487 |
| adapt | 330 |
| exclude | 56 |
| copy | 5 |
| **Total** | **2,393** |

Review status:
- 258 files have recorded content/static review evidence (25 OpenFuse files, 39 Visual Skills Markdown, 15 Visual Skills SVG, and 179 Scenario entrypoints);
- 2,135 files remain `pending-content-review`.

A decision of ADAPT means an adaptation path is selected, not that source copying/execution is approved. A DEFER decision is a deliberate hold. Pending rows are not import-approved. This is a complete per-path **handling decision manifest**, not a claim that every source file passed legal/security review.

### 11.5 Dependency SBOM and exact-version license status

Created `docs/implementation/sbom/P1-EXTERNAL-NPM-DEPENDENCIES.spdx.json` (SPDX 2.3):
- OpenFuse root pnpm v9 lockfile: 1,452 package rows;
- Scenario Skills pnpm v9 lockfile: 466 package rows;
- total: 1,918 lockfile package rows, representing 1,808 unique package@version coordinates across both repositories;
- exact pinned lockfile blobs: OpenFuse `1f64461ae3c5e6c69b5c8c04826fe7bdbac1f016`, Scenario `a9bfa48bafc6cbd1b4c4652972ae6eeeaa27e098`.

Also inspected the independent OpenFuse browser-worker npm `package-lock.json` (blob `37c93ea2a3410032df594b2893e1a015b2342749`, lockfile v3). Its six package entries expose exact pinned versions and license values, including Playwright/Playwright Core Apache-2.0, TypeScript Apache-2.0, and `@types/node`, `fsevents`, `undici-types` MIT.

Read-only npm package registry metadata was collected for 37 direct dependency coordinates. Nine current registry latest versions exactly matched their lockfile pins (8 MIT, 1 ISC). The other 28 records expose only the package's current latest-version license and are **not** treated as evidence for the older pinned versions. Combining exact-version matches with the independent worker package-lock resolved license metadata establishes 15 unique package@version coordinates (16 SBOM rows due to repository duplicates). Current SPDX counts:
- 11 rows MIT;
- 3 rows Apache-2.0;
- 2 rows ISC;
- 1,902 rows remain `NOASSERTION`.

The SBOM is therefore a valid lockfile-derived package inventory, but **not yet a license-complete SBOM**. pnpm lockfiles do not include license fields; package metadata from the latest tag cannot be projected backward onto older versions. Remaining 1,793 unique coordinates still need exact-version license resolution. No package was installed and no dependency code was executed.

Created `docs/implementation/sbom/P1-DIRECT-DEPENDENCY-LICENSE-OBSERVATIONS-20261114.json` with source URLs, registry latest version, observed license, pinned version, exact-match flag and limitations for the 37 direct dependencies.

### 11.6 Updated P1 gate

| Gate | Evidence | Status |
|---|---|---|
| Recursive source-tree parity | 2,393 paths across 3 pinned sources; all trees complete | **GREEN** |
| Per-file conservative handling decision | Every 2,393 rows has one of five decisions, owner and rationale | **GREEN for decision coverage** |
| Per-file content/provenance review | 258 reviewed; 2,135 pending | **OPEN** |
| OpenFuse requested high-risk family samples | OAuth/Google, finance, vault, worker, network/proxy, downloads and computer source read | **PARTIAL**; remaining server/package files need review |
| Visual Skills Markdown/SVG | 39 Markdown and 15 SVG reviewed | **PARTIAL**; binary hero, provider brand rights and embedded asset provenance open |
| Scenario skill entrypoints | 179 entrypoints reviewed; family routing mapped | **GREEN for entrypoints only** |
| Scenario linked references/scripts/assets/tests/metadata | 1,935 files under Scenario remain outside the entrypoint-level review boundary | **OPEN** |
| Lockfile SBOM | 1,918 package rows; 1,808 unique coordinates | **GREEN for lockfile inventory** |
| Exact-version package license resolution | 15 unique package@version coordinates resolved; 1,793 unique coordinates still NOASSERTION | **OPEN** |
| P1 closure | Content, provenance and exact-license gates not all closed | **NOT CLOSED** |

**No-test compliance:** no dependency installation, script execution, build, lint, typecheck, tests, browser/API/provider probing, staging, Supabase mutation/migration or deployment was performed. This work is static source and metadata review only.

### 11.7 Next bounded P1 work

1. Resolve exact-version licenses for the remaining 1,793 unique package@version coordinates; use immutable version metadata/artifacts and retain unknowns rather than inheriting latest package licenses.
2. Review the remaining OpenFuse server/package files by source path, including finance/workspace integration, vault/Google API error paths, auth middleware, browser API routes, Docker/E2B lifecycle and dependency/license notices.
3. Review Visual Skills binary hero asset and source/provenance of every provider logo/banner; determine whether any third-party assets are bundled or referenced. Keep brand marks deferred until cleared.
4. For Scenario, traverse all entrypoint-linked files and resolve every script, reference, asset, test, plugin manifest and nested license to a per-file review status; prioritize general image/video/audio/3D provider skills and workflows, then DCC/game-engine scripts.
5. Reconcile the final manifest so no row remains pending-content-review; retain explicit `defer` for items not approved for MoreAI.
6. Only then close P1 and resume the earliest incomplete mandatory phase under `AGENTS.md`: Phase 04, then 06/07/08 and Phase 09 according to dependency order.

**P1 remains open.** The next implementation work remains source governance and dependency/license resolution, not importing unreviewed engines or skipping to Phase 09.

---

## 12. Fourth continuation increment — deeper OpenFuse runtime evidence and rights reconciliation

**Date:** 2026-11-14. Source pins unchanged. Companion evidence documents:
- `docs/implementation/P1-OPENFUSE-RUNTIME-BROWSER-OAUTH-REVIEW-20261114.md`
- `docs/implementation/P1-VISUAL-SKILLS-ASSET-RIGHTS-AND-SCENARIO-INVENTORY-20261114.md`

### 12.1 OpenFuse runtime/browser/OAuth

A further ten complete source files were fetched and reviewed: `computer-backend.ts`, `computer-e2b-desktop.ts`, `computer.ts`, server `browser.ts`, `google-auth.ts`, worker `browser.ts`, `downloads.ts`, `network.ts`, `proxy.ts`, and integrations `vault.ts`. Their pinned blob SHAs and dispositions are recorded in the companion addendum.

Key security distinction: Docker computer isolation is configured with network disabled, non-root execution, read-only rootfs, dropped capabilities, no host binds/devices/ports and resource caps. E2B desktop is explicitly network-enabled and must be governed separately. Browser DNS validation and IP-pinned proxy patterns are useful defense-in-depth but do not replace network-layer egress controls. OAuth send-mail/calendar writes are high-impact actions and require explicit MoreAI confirmation, scoped credentials, version checks, idempotency and immutable receipts. OpenFuse owner Store/session/lease state is not MoreAI's canonical Supabase identity or durable run store.

The pinned OpenFuse tree has 219 blob paths. This increment does not claim all 219 are reviewed; remaining routes, packages, support files, tests, configs and notices remain in the path-by-path audit.

### 12.2 Visual Skills asset rights

The pinned Visual Skills tree contains 60 blobs and 16 files under `assets/`: 13 third-party provider/product logo variants, two dramaturgy banners and one hero WebP. Root LICENSE is CC BY 4.0 and NOTICE requires attribution to Serge Shima and the source repository, and describes specific third-party methods as rewritten/adapted from an MIT-licensed source. CC BY does not grant trademark rights. The 13 logo marks are deferred pending provider permission/brand-guideline review; banners and hero remain held until original authorship and embedded material provenance are confirmed. Therefore Visual Skills asset rights are **OPEN**, even though the prior content audit reviewed the 39 Markdown and 15 SVG text files.

### 12.3 Scenario entrypoint count reconciliation

The pinned Scenario recursive tree contains 2,114 blobs and is not truncated. The 179 entrypoint aggregate reconciles to 172 product `SKILL.md` files beneath `skills/` plus 7 internal maintainer/skill-authoring entrypoints beneath `.agents/skills/`. The seven internal entrypoints are archive-only, not product skills. Within `skills/`, tree counts include 519 reference paths, 898 script paths, 54 asset paths and 20 test paths. Tree enumeration does not equal per-file content review; linked supporting files and nested licensing remain open.

### 12.4 P1 gate remains open

- OpenFuse full-tree review: OPEN (selected high-risk paths now have detailed static review).
- Exact-version package license resolution: OPEN (1,793 unique package@version coordinates remain `NOASSERTION`).
- Visual Skills asset rights: OPEN (13 marks deferred; three non-logo assets await provenance confirmation).
- Scenario supporting-file content/provenance review: OPEN.
- Final manifest: OPEN; 2,135 paths remain `pending-content-review` per the prior manifest snapshot. No pending state is cleared by this increment without per-file evidence.
- P1 closure: NOT APPROVED.

No source code/assets were copied into product runtime. No dependency installation, script execution, build, lint, typecheck, tests, staging, database mutation/migration or deployment was performed. This remains static review and documentation only.
