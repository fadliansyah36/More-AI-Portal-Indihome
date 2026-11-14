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


---

## 13. Fifth continuation increment — OpenFuse computer boundary and client transport review

**Date:** 2026-11-14. OpenFuse source pin remains `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`. Seven additional files were fetched in full and reviewed against the pinned blob identities:

| Path | Pinned blob SHA | Review |
|---|---|---|
| `.env.example` | `603e35542539cb7da5e36a0dfc605e0bdec84675` | Full static review |
| `.github/workflows/ci.yml` | `011d280c444e3604f2558c4f0a931fb41144b1d9` | Full static review; workflow commands were not run |
| `apps/computer/Dockerfile` | `4ef4cf8525201112601b7e597d29b6b21a6c7ae7` | Full static review |
| `apps/computer/files.py` | `270a5f1f3e3d521d5da67f156cb51fd87793de21` | Full static review |
| `apps/computer/smoke.test.ts` | `dc9201916123abfa7ee7910ba8274da123e9a262` | Full static review; test not executed |
| `apps/computer/e2b-desktop-smoke.test.ts` | `0de8cb8d090cb1678ad265e89d0cd7d0ff5433b9` | Full static review; test not executed |
| `apps/mobile/src/api.ts` | `6e57fadb47cb37c5740b22a30dcb260b0ba8ae80` | Full static review |

**Computer filesystem boundary:** the Docker image runs as UID 1000, keeps the workspace as its volume, and exposes a fixed stdin JSON file API. The Python bridge rejects traversal segments and symlinked path components, opens relative to directory descriptors, rejects non-regular files, applies bounded text/PDF sizes, validates PDF magic bytes, and atomically replaces files. These are useful local sandbox controls, not a substitute for MoreAI tenant-bound file authorization, malware scanning/quarantine, storage policy, or network egress controls.

**Runtime/configuration findings:**
- The environment template explicitly distinguishes Docker (default) from E2B Desktop and documents that E2B has internet access. MoreAI must treat the E2B network-enabled mode as a separate risk class; do not inherit Docker's network-deny assumptions.
- The E2B smoke fixture asserts that the desktop URL includes a VNC password query parameter and reuses the URL for the same process. This is test evidence, not proof of a production leak, but the credential-bearing URL must be treated as a secret: redact it from logs/telemetry, avoid analytics/referrer propagation, enforce short lifetime and tenant/session binding, and rotate/revoke on takeover or termination.
- The sample environment exposes server-only secret categories (OpenFuse access key, token encryption key, OAuth client secret, worker token, E2B key, provider keys). MoreAI must keep all such credentials in server-side secret management; none may enter public client configuration.
- CI declares installs, lint, typecheck, tests, builds and container checks. These workflow commands were only read as source; none was executed in this audit.
- The mobile API client accepts a bearer token in its constructor and attaches it to API calls. The inspected file does not establish secure token persistence or rotation; MoreAI must instead use Supabase Auth session semantics and FastAPI authorization, never a client-held OpenFuse shared access key.

**Disposition:** adapt only the fixed-file-bridge hardening concepts and bounded resource patterns where they fit MoreAI's existing sandbox. Exclude OpenFuse environment/auth/session configuration and standalone mobile API transport as product integration. E2B desktop remains deferred until MoreAI has explicit egress policy, secret isolation, approval, quota, audit and credential-bearing URL controls.

The pinned tree reconciliation remains **219 blobs total**. Seven paths in this increment were fetched and reviewed in full; the prior report's 25 reviewed OpenFuse paths therefore advances to **32 reviewed paths**, with **187 paths not yet fully reviewed**. This count is path-level evidence only; it does not close the full OpenFuse review or P1.

A further fetch of the large standalone mobile UI files (`agent-ui.tsx`, `agent-workspace.tsx`, and `chat.tsx`) was used only to identify likely integration surfaces; these files are **not counted as full semantic reviews**. They remain excluded from MoreAI UI adoption, and their detailed content review is still pending.

**No product code, dependency or Supabase changes were made.** No installs, script execution, tests, builds, lint, typechecks, staging, deployment, or database mutation were performed.


---

## 14. Sixth continuation increment — OpenFuse server and agent orchestration review

**Date:** 2026-11-14. Source pin: OpenFuse `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`. Ten additional server files were fetched in full and reviewed:

| Path | Pinned blob SHA |
|---|---|
| `apps/server/src/browser-console.ts` | `d88f46fba1d607792e7c26cecc69758cb420331d` |
| `apps/server/src/computer-tools.ts` | `99f8469cd06e8e60c1e90a83bb73cf2448a751cc` |
| `apps/server/src/demo/entry.ts` | `4f873b66ae174e05e0767b936a3fe997e020001e` |
| `apps/server/src/demo/jev-fixture.ts` | `c4234fc2326e35b0c102f6d048a894a7697e6cf9` |
| `apps/server/src/demo/model.ts` | `0f7ee424684f7998940476cfd76c19250e66f4bc` |
| `apps/server/src/engine/conversation.ts` | `df2b2bdd2b20b226155c888755f429991a308224` |
| `apps/server/src/engine/model.ts` | `8cffc66beaa2e17a099c244612b4a8115c43ca94` |
| `apps/server/src/engine/page-diff.ts` | `b516473295ac85bb87c827130c199147aaffdcbf` |
| `apps/server/src/engine/routes.ts` | `0d616aa9db5eb312a28911bba71f2c19f3f6e0ba` |
| `apps/server/src/engine/service.ts` | `54684937f82708ae16cadd074fdb505b3c947904` |

**Server and runtime findings:**
- `computer-tools.ts` defines materially different security contracts: Docker workspace has networking disabled and bounded command execution; E2B desktop explicitly has outbound networking and publicly reachable listening ports without application authentication. Do not merge these into one generic "computer" trust tier. MoreAI must enforce backend authorization, isolated tenant/session, egress policy, approval gates for external side effects, strict port exposure policy and bounded execution for each provider.
- Browser console is an HTML/JS client that fetches preview and posts interaction commands to its current URL. Its authenticated session and origin boundary must be preserved; do not expose this standalone console as a public MoreAI route without FastAPI authorization, short-lived session binding, CSP and origin controls.
- Conversation/model engine scopes operations using a server-derived `owner`, bounds some tool inputs, treats mail/page content as untrusted, and routes high-impact email send through prepare/approval. Adapt these patterns to MoreAI's verified Supabase Auth subject and policy checks; never accept owner/tenant identity from model arguments or client payloads.
- Agent routes expose task, goal, monitor, idea and memory operations. These are useful capability references, but MoreAI must map them into its existing customer dashboard and unified Agent Runtime rather than exposing an independent OpenFuse agent product surface.
- The engine service owns durable task orchestration, worker lifecycle, monitor activation and task/artifact state. It is a reference for state transitions and resumability, not a reason to create a second runtime or persistence engine. OpenManus remains MoreAI's sole planning/execution authority under the agreed architecture.
- OpenFuse server DB uses a generic owner/kind/id record API and imports PGlite for embedded mode. This is not the MoreAI canonical persistence layer. Do not adopt PGlite or OpenFuse's standalone DB schema as a second database; translate required durable state into FastAPI repositories and Supabase PostgreSQL with RLS and explicit tenant constraints.
- File service creates owner-scoped metadata and signed content URLs backed by local data directory. MoreAI must instead use Supabase Storage with private buckets, short-lived signed URLs, tenant-aware authorization, object lifecycle rules and metadata in PostgreSQL. Local disk paths and HMAC content URLs are not a substitute.
- Rate limiter uses an in-process Map store. It is a useful local algorithm reference but not a distributed production limiter across API instances; MoreAI needs shared/distributed enforcement at its trusted API boundary.
- Demo entry, fixtures and scripted demo model contain fixed local tokens, local-user identity, sample school-trip content and process spawning for a self-contained demo. These are explicitly demo-only and must be excluded from production and must not become seeded/customer data.
- The task model tool path explicitly uses bounded schemas and separate approval for prepared email sends. Preserve this human confirmation boundary for high-impact actions, and extend it to calendar writes, external submissions, uploads and purchases with idempotency and audit receipts.

**Integration disposition:** adapt the orchestration state-machine concepts, bounded tool schemas, per-owner service scoping and explicit action-approval pattern. Do not adopt OpenFuse PGlite/local-file persistence, demo identity/tokens, sample fixtures, standalone auth, or a parallel agent runtime. Map capabilities through FastAPI to Supabase; OpenManus remains the single runtime authority; OpenFuse is a capability extension only.

**Review count:** this increment adds 10 fully fetched server paths. The report now records **42 of 219 OpenFuse blobs reviewed in full**, leaving **177 blobs not yet fully reviewed**. This is still an open path-level audit; it is not P1 closure.

No application code or Supabase data/schema was changed. No builds, tests, installs, lint, typechecks, staging or deployment were run.


---

## 15. Seventh continuation increment — OpenFuse mobile app boundary and document rendering

**Date:** 2026-11-14. Source pin remains `CopilotKit/openfuse@7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`. Ten additional files were fetched in full and reviewed:

| Path | Pinned blob SHA |
|---|---|
| `apps/mobile/App.tsx` | `53e192a602f3541c1b3e913f595f00e1991772aa` |
| `apps/mobile/src/BrowserConsole.native.tsx` | `64e77489f65c95255745cbcaa4f359d6cc6336f1` |
| `apps/mobile/src/BrowserConsole.web.tsx` | `eb15e336900f156f47feeab4f179b59e5dd8efd7` |
| `apps/mobile/src/DateFields.native.tsx` | `32fb7ffc3ca6a2fd23c7484e78a5e2b228cf818b` |
| `apps/mobile/src/DateFields.web.tsx` | `db9e88afde19efef7596486defe2dddd5661d421` |
| `apps/mobile/src/DateTimeEditor.tsx` | `92e78ee7a0129b1d7f55fdfe474ba53c4e7d6e4c` |
| `apps/mobile/src/PdfReader.native.tsx` | `c5ead898a65b04c0483a0258ff16fb38699f87d6` |
| `apps/mobile/src/PdfReader.web.tsx` | `017fdf562c278f3a903e7832a0f23812f5160741` |
| `apps/mobile/src/api-response.ts` | `d6e8b017d2f70668f2833642e894268047032245` |
| `apps/mobile/src/assistant-markdown.ts` | `190f242e6f56eacb89c437950ad881300a8f92ab` |

**Findings and MoreAI disposition:**
- The mobile app obtains an OpenFuse standalone session through `createSession(key)`, retains its bearer token in component state, and passes it to CopilotKit runtime and a dedicated `FuseApi`. This is a standalone demo/application auth path, not MoreAI's identity model. Do not reuse it. MoreAI must use the authenticated Supabase user session and FastAPI authorization; any downstream service credential stays server-side.
- Native browser console uses React Native WebView to load a supplied URL; web browser console uses an iframe with optional sandbox flags. MoreAI must constrain session URLs to server-issued, short-lived, tenant-bound endpoints; enforce allowed origins, CSP, navigation restrictions and no credential-bearing URL leakage. Web sandbox flags need deliberate review; do not blindly enable same-origin plus scripts for untrusted content.
- Native PDF reader sends bearer authorization headers and disables cache; web PDF reader embeds a URL in an iframe and exposes print/download UI. MoreAI should use short-lived Supabase signed URLs or a FastAPI streaming endpoint with ownership/RLS checks, avoid long-lived bearer tokens in URL fragments, and apply download policy/audit.
- Date field/editor components are presentation utilities; they do not create a distinct backend capability. They are not candidates for direct UI transplantation because the MoreAI customer dashboard and design system remain canonical.
- Assistant markdown URL helper permits only HTTP(S) schemes. This is a useful baseline, but MoreAI additionally needs safe-link rendering, host/IP restrictions for server-side fetch tools, and untrusted-content treatment; client URL scheme validation alone does not prevent SSRF.
- API response helper is a parsing/normalization utility and does not establish auth or tenant security.

**Audit count correction:** a fresh set-based reconciliation of the previously named reviewed paths against the pinned 219-blob tree showed that the prior increment's stated 42/219 count had included ten paths that were not in the enumerated set. The reproducible count before this increment was **32**. This increment adds ten distinct fully reviewed paths, bringing the verified total to **42/219**, with **177 paths remaining**. This corrected count supersedes the earlier paragraph's count; the per-file list above is the evidence for the ten new paths.

No MoreAI application code, dependencies, or Supabase schema/data were changed. No install, build, test, lint, typecheck, staging or deployment was run.


---

## 16. Eighth continuation increment — OpenFuse agent UI state, approvals and browser tool presentation

**Date:** 2026-11-14. Six additional source files were fetched in full at the pinned OpenFuse commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/mobile/src/assistant-response.tsx` | `9b89ffbbf74f4723e235d0c109bcb13454ef159e` |
| `apps/mobile/src/background-updates.tsx` | `76fb20cd8cdd1565548b6a90c1957152498b73b0` |
| `apps/mobile/src/browser-address.ts` | `5e02f43c9c634040ce37688e680a73ca989bc1fc` |
| `apps/mobile/src/browser-tool-card.tsx` | `c5e0f689fffb5f84839c2b12ccdb0a7707468ef9` |
| `apps/mobile/src/agent-ui.tsx` | `4939c12c7363f9562950336427d63b4b5eb18b0d` |
| `apps/mobile/src/agent-workspace.tsx` | `9ddf2a397b4b57dd44e6243cafcee51d16e41151` |

**Findings and MoreAI disposition:**
- Agent workspace UI reads a dedicated `/api/agent` API and keeps its own client-side cache/context. This is a useful reference for dashboard activity, task state and notifications, but MoreAI must bind those surfaces to the existing customer dashboard and OpenManus run/task model through FastAPI, not create a second Agent workspace API or runtime.
- Agent UI explicitly represents `waiting_approval` and `waiting_input` task states. Preserve this UX concept in MoreAI: show pending action, exact scope/target, impact, requester, expiry, approve/deny, and immutable audit receipt. Approval must be enforced server-side and bound to a single action payload/version, not merely a client button.
- Background update hook refreshes workspace data; adapt only the UX behavior if needed. Production update delivery should use authenticated FastAPI/Supabase Realtime channels with tenant filters, not trust client-side polling as an authorization boundary.
- Browser tool card retrieves a session by ID from the API and presents session status/control. MoreAI must authorize every session lookup/action against the verified user and tenant; unguessable IDs alone are not access control.
- Browser address helper accepts HTTP(S) addresses and normalizes host input. It is only client-side syntax validation. Server-side browser/navigation tools still require SSRF defenses, private/link-local IP rejection, DNS rebinding/redirect checks and egress policy.
- Assistant response renderer is a presentation utility. Do not port OpenFuse UI wholesale; align any missing MoreAI components with its Master PRD design tokens and existing frontend CSS/components.

Three additional guessed filenames in this batch (`approval-card.tsx`, `task-card.tsx`, `markdown.tsx`, `tool-card.tsx`) returned NOT_FOUND and were not counted or treated as source evidence.

**Reconciled path count:** the reproducible pinned-tree set is now **48/219 fully reviewed paths**, with **171 remaining**. This count is derived from the explicit reviewed-path set, not the previous narrative totals.

No MoreAI product code or Supabase was changed. No tests, builds, installs, lint, typechecks, staging or deployment were run.


---

## 17. OpenFuse external connection / plugin capability assessment

**Date:** 2026-11-14. This is an architecture/capability assessment from the pinned OpenFuse source and its feature/roadmap documents. It does not add to the 219-blob full-review counter because these paths were already included in prior file reviews.

**Additional pinned evidence inspected:**
- `README.md` — `1e07e33e37072b08b19ab2f5deddeed1cd709971`
- `docs/FEATURES.md` — `c44b5dca81e8970f7c93649282f9f55515636f60`
- `ROADMAP.md` — `83c9773347e743cf122e8c87b3fbcdbe3e9455ab`
- `docs/VERIFICATION.md` — `9453bf7a41af66b40c4a53c90abb494911213b96`
- `apps/server/src/google-auth.ts` — `ae56eb481b6cab1a52b3994d59090156ba97e193`
- `apps/server/src/engine/routes.ts` — `0d616aa9db5eb312a28911bba71f2c19f3f6e0ba`
- `apps/server/src/engine/service.ts` — `54684937f82708ae16cadd074fdb505b3c947904`

### What OpenFuse actually offers

1. **Google Workspace (Gmail + Google Calendar):** implemented OAuth adapter and capability surfaces are documented. OAuth uses state with a 10-minute expiry, PKCE S256, account/connection generation fencing, server-side encrypted tokens, token refresh, disconnect/revoke, and read/write scopes. The initial scopes include Gmail read, Calendar event read and calendar-list read; elevated write scopes include Gmail send and Calendar events write. Mail send and calendar mutations require a stored review/approval. The source describes reviewed event creation/update/deletion and Gmail drafts/attachments. However, the README explicitly says this is a single-owner deployment behind a shared access key, **not multi-tenant identity**, and live Google account acceptance remains pending in its verification/roadmap documents.
2. **Connector catalogue:** the feature inventory mentions a searchable capability/status catalogue, Google connection and browser worker. It is not evidence of a broad, production-ready third-party plugin marketplace or universal connector SDK.
3. **Google Drive / Docs:** explicitly listed as a planned extension, not currently implemented capability in the inspected feature inventory.
4. **Other providers:** Plaid, health, Instagram, WhatsApp and partner APIs are listed as planned/roadmap items, not available integrations to claim as implemented.
5. **Remotion:** no Remotion integration, package adapter, OAuth connector, render API or workflow capability was evidenced in the inspected OpenFuse feature/roadmap materials. Treat Remotion as a separate integration to design and implement in MoreAI, subject to its official API and licensing/terms. Do not describe it as an OpenFuse built-in plugin.
6. **Scheduling:** OpenFuse has durable task/goal/monitor concepts, recurring watches, pause/resume/retry/backoff and worker leases. The feature inventory still lists calendar-driven reminders and broader adaptive planning as remaining work. A recurring monitor/task is not the same as a user-facing calendar scheduler with timezone-aware recurrence, Google Calendar sync, webhook delivery, or a workflow automation designer.

### MoreAI integration direction — Muse-like connected assistant experience

Implement a first-party **Connections & Integrations** capability inside the existing MoreAI customer dashboard (do not transplant OpenFuse UI). It should expose:
- Discoverable connector catalogue with categories, search, capability descriptions, availability, scopes, connection status and admin policy.
- OAuth connect/disconnect/reconnect and consent-scope review for Google Workspace; per-user/per-tenant credentials with encryption-at-rest, KMS/envelope key rotation, refresh-token lifecycle, revocation, audit trail and least privilege.
- Google Calendar: list calendars/events, availability checks, create/update/delete events through explicit action proposals; timezone-aware recurrence and event version/ETag fencing. Gmail: search/read threads, draft and attachments, with separate approval before sending.
- Scheduling centre: one-time and recurring schedules, timezone, calendar source, trigger conditions, retry/backoff, pause/resume, run history, notifications and approval gates. Persist schedule definitions and run receipts in Supabase PostgreSQL; execute through FastAPI job/worker boundary while OpenManus remains the single planner/agent execution authority.
- Workflow automation: trigger → condition → OpenManus plan/task → authorized connector action → approval (where high impact) → result/audit. Use idempotency keys and explicit reconciliation for uncertain external writes.
- Remotion: dedicated provider adapter for rendering video programmatically (composition/template selection, input props/assets, render job submission, progress/webhook/polling, output artifact delivery, usage/quota). Store render jobs, ownership, provider IDs and artifacts in Supabase; credentials only server-side. Treat rendering as a capability invoked by OpenManus workflow, not another agent runtime.
- Future connectors should use a normalized connector contract (manifest/capabilities, OAuth/API-key auth strategy, scopes, input/output schemas, rate limits, webhook/event contract, retry policy, approval class, audit schema, tenant isolation). Provider-specific adapters live behind FastAPI. No connector receives arbitrary authority simply because it is installed.

### Security and architecture constraints
- Do not reuse OpenFuse shared `OPENFUSE_ACCESS_KEY` or single-owner identity model in MoreAI. Resolve tenant/user from verified Supabase Auth on the FastAPI server.
- Do not store provider tokens in browser/mobile state or expose them to OpenManus prompts. A tool receives a narrowly scoped server-side capability handle, never raw long-lived credentials.
- OAuth scopes are incremental and visible; separate read scopes from high-impact write scopes. Every send, calendar write/delete, external form submit, publish, or render spend must have policy evaluation, explicit confirmation as required, idempotency, audit receipt and spend/quotas.
- Keep OpenManus as the only agent/planning/runtime authority. OpenFuse browser/desktop execution is an isolated tool capability only, not an alternate autonomous runtime.
- Use Supabase PostgreSQL and private Supabase Storage as canonical MoreAI persistence. Exclude OpenFuse PGlite/local DB and local credential/file persistence as production source of truth.
- Do not claim live Google or Remotion connections are operational without user credentials and a permitted acceptance process. Per current user instruction, no live external account tests or staging are to be performed.

**Status:** this assessment is recorded for the MoreAI architecture backlog. It is not an implementation of the connection centre, Google Workspace, scheduling, or Remotion. No app code, dependency, or Supabase mutation was made.


---

## 18. Ninth continuation increment — OpenFuse chat, computer workspace and desktop surfaces

**Date:** 2026-11-14. Ten additional distinct files were fetched in full at the pinned source commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/mobile/src/chat.tsx` | `a95ad56bf9eb1dc19e0972619ae5daaa6493f31b` |
| `apps/mobile/src/computer-drafts.tsx` | `0deb0b7ce2692349ed452676a20c8c88c3f68cd5` |
| `apps/mobile/src/computer-status.ts` | `4d39a7e68cfd33fc6513a7e9e6511a490fe43105` |
| `apps/mobile/src/computer-workspace.tsx` | `19a9191cb5be7697216be33b053b15454580e6f3` |
| `apps/mobile/src/computer.tsx` | `285e0516b3ef27a7e4959ffe6337437f2a1e1bd7` |
| `apps/mobile/src/conversation-queue.ts` | `d3e940b68d6e39e93f06c50797c9aec1c150e848` |
| `apps/mobile/src/conversation-run.ts` | `4e1e5260e7b31bcab99b2125d499a6d9e4fb80bf` |
| `apps/mobile/src/date-time.ts` | `a1844f1eb9e94fe380abda1a17aa8534ca87b76e` |
| `apps/mobile/src/desktop-stream.tsx` | `4906d2552f0f883097b1cb1323341efbfdd8b705` |
| `apps/mobile/src/desktop-tool-card.tsx` | `cce31a1a60cc7e3010d0cf7222877533ce693acd` |

**Findings and MoreAI disposition:**
- Chat uses CopilotKit tool/render hooks and composes rich cards for browser, desktop, mail, search, tasks and artifacts. MoreAI should preserve this progressive rich-result concept while using its existing customer UI and OpenManus tool-call/event model. Tool outputs must remain data, not instructions or authorization.
- Conversation queue/run helpers handle queued turns, thread locking and replayed error events. These are UI/runtime coordination details; they do not replace server-side idempotency, durable run ownership, cancellation fencing or OpenManus run state.
- Computer workspace exposes terminal commands, files, uploads and a persistent computer snapshot through API routes. It is a privileged capability, not a general plugin. MoreAI must enforce tenant-scoped file ACLs, command allow/deny policy, isolated execution, output caps, approval tiers and audit receipts at FastAPI.
- Draft state intentionally remains in React memory rather than being persisted to disk. MoreAI should keep sensitive unsent drafts out of browser storage unless a separately designed encrypted draft persistence feature is approved.
- Desktop stream obtains a URL from the server and embeds/opens a VNC stream. The separate computer runtime has different network and isolation properties from the browser worker; do not conflate them. Treat stream URLs as bearer secrets: short TTL, tenant/session binding, redaction from logs/telemetry/referrers, and revocation.
- Desktop tool card can attach bearer authorization headers to screenshot requests and expose a start/takeover affordance. Every screenshot, stream and control action must re-check server-side ownership and session state.
- The small computer status and date-time helpers are presentation utilities only, not standalone backend capabilities.

**Count:** this increment adds ten distinct full-file reviews to the previously reconciled 48. OpenFuse content review is now **58/219**, with **161 remaining**. This is source inspection only; no test, build, install, lint, typecheck, staging, deployment or live external account operation was performed.


---

## 19. Tenth continuation increment — OpenFuse mail, calendar, thread and rich-result UI

**Date:** 2026-11-14. Ten additional distinct files were fetched in full at pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/mobile/src/details.tsx` | `7046350953bc7739a55c4a7b03a228b7360bf5db` |
| `apps/mobile/src/jev-actions.ts` | `b52e6ca4a1b0393542f894eac9f91ef1eaba0b3b` |
| `apps/mobile/src/jev-tool-card.tsx` | `94563021a541eb838294790340fa8a624e89c848` |
| `apps/mobile/src/mail-tool-card.tsx` | `3e0ed193ff24f60c22cab632f9a704fce36b832b` |
| `apps/mobile/src/relative-date.ts` | `642c6d95889b0d1ca0dfd91f650e23b9e0d6198c` |
| `apps/mobile/src/screens.tsx` | `ea12faef13211657d8bd403db81a78886d70d12d` |
| `apps/mobile/src/search-tool-card.tsx` | `97aa69031cb5d04293342e092ea06c440ff38715` |
| `apps/mobile/src/thread-artifacts.tsx` | `9aa98c4bb3da4a9557865f9e24664192e42a5cc8` |
| `apps/mobile/src/threads.tsx` | `537522513e64b87896e6ed3e76cf57378c28766b` |
| `apps/mobile/src/ui.tsx` | `758a69f06a0d283a8041c28c8e36aaebc56434e7` |

**Findings and MoreAI disposition:**
- Details/screens assemble mail, calendar, files, browser, task and connection/app views. This is a single-owner OpenFuse information architecture; MoreAI must map the useful capabilities into existing dashboard navigation rather than transplant these screens.
- Mail detail fetches full threads and imports attachments through server APIs. MoreAI must preserve tenant ownership checks on thread IDs and attachment references, scan/quarantine uploads before RAG ingestion, and use private Storage with signed access.
- Calendar/event interaction cards and JEV choice/action helpers bind user confirmation to a specific panel, thread and selection. This is a useful stale-action defense pattern. MoreAI must additionally bind approval to a canonical action payload hash, connector account generation, event ETag/version, expiry and idempotency key on the server.
- Search result cards accept HTTP(S) source links and open them externally. This is display navigation only, not permission to fetch arbitrary URLs server-side; SSRF controls remain at FastAPI/tool boundary.
- Thread artifact cards explicitly hydrate task-linked artifacts by ID and do not store signed URLs in messages. Reuse this principle: persist durable artifact IDs/metadata, mint short-lived signed URLs on authorized access, and do not persist expiring URLs in chat history.
- Threads are backed by CopilotKit Intelligence thread persistence/replay, with the OpenFuse server provisioning a main thread. MoreAI should keep its canonical chat/run/message persistence in Supabase and connect UI through its FastAPI/OpenManus boundary, avoiding a second thread persistence service.
- Shared UI primitives and date format helpers are presentational. MoreAI's own component library and design tokens remain authoritative.

**Count:** ten more distinct full-file reviews; OpenFuse content review is now **68/219**, with **151 remaining**. No tests/build/install/lint/typecheck, staging, deployment, live mail send, calendar write or Supabase mutation was performed.


---

## 20. Eleventh continuation increment — OpenFuse server action, identity, storage and worker core

**Date:** 2026-11-14. Ten additional distinct files fetched in full at the pinned OpenFuse commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/server/src/actions.ts` | `e430a3d10b8e3be2e7c44122974520e0eb495572` |
| `apps/server/src/agent.ts` | `1d6bc4dfb87fae01c680be1add4840e54710a24b` |
| `apps/server/src/app.ts` | `811a5f520ca0b3b36f1b865460de85d0866e0050` |
| `apps/server/src/config.ts` | `34084326bf9846b688612cd61a8a6f51f6139700` |
| `apps/server/src/db.ts` | `e3103c9ee2ffd5413aabf32044c541d48ce9cc0b` |
| `apps/server/src/engine/tanstack-agent.ts` | `9ebf2bf85d18ddc73db507856f41f31e8ce145ac` |
| `apps/server/src/engine/worker.ts` | `b69fe63486dbdd3f8617aed59bbd1e48b92e344a` |
| `apps/server/src/errors.ts` | `63d6be2816a67e5fd553b4e5981b43b2cefe4006` |
| `apps/server/src/files.ts` | `14453455caa4a3425c255a21810710b2e4436e50` |
| `apps/server/src/jev/adapter.ts` | `1054914155bd4e91dc75d290d060adde89417dea` |

**Findings and MoreAI disposition:**
- Action proposals are owner-scoped, bind prepared provider actions to connection IDs and target event versions, and require review before execution. MoreAI should adopt the prepare → review → execute lifecycle with Supabase transaction/CAS semantics, action payload hash, ETag/version and idempotency. Ensure approval state and execution state cannot be forged by client input.
- OpenFuse agent runtime can select sample/model/AG-UI backends and resolves identity through its own auth helper. MoreAI must not add a second agent runtime: OpenManus is sole planner/executor, and FastAPI derives actor/tenant from verified Supabase Auth.
- Hono app composes auth, files, Google, workspace, browser, computer, agent and CopilotKit Intelligence. This confirms OpenFuse is a complete standalone app composition. MoreAI should adapt selected service/capability boundaries, not mount its app wholesale or duplicate the existing dashboard.
- Config includes model/provider credentials, Google OAuth, worker token, Docker/E2B desktop and storage settings. All secrets remain server-side. E2B and Docker are distinct execution trust classes and need separate policy.
- OpenFuse DB implements generic owner/kind/id records and imports PGlite. This is explicitly excluded as MoreAI persistence; use Supabase PostgreSQL, RLS, typed repositories and tenant-scoped transactions.
- TanStack agent adapter resolves provider/model combinations and defines state tools. Reuse only provider adapter design patterns where compatible with the MoreAI Model Router; do not let a UI-level agent SDK choose or own the canonical MoreAI model/runtime.
- Task worker supports scheduled task eligibility, leases, checkpoints, approval waits and cancellation/abort. This is useful execution-engine reference, but MoreAI schedule definitions, leases, run events and receipts must be persisted in Supabase and dispatched by the trusted FastAPI worker boundary. OpenManus remains execution authority.
- Files service creates owner-scoped metadata, deterministic operation IDs and signed content URLs over local filesystem storage. MoreAI should preserve deterministic idempotency and signed-access concepts but use private Supabase Storage, malware quarantine, RLS-backed metadata and tenant ACL checks.
- JEV adapter is a provider-mediated interaction selector/ranker. It is not a general plugin framework; if used, its output is untrusted suggestion data and must never override MoreAI authorization or action policy.

**Count:** ten more distinct full-file reviews; OpenFuse content review is now **78/219**, with **141 remaining**. No test/build/install/lint/typecheck, staging, deployment, live provider call or Supabase mutation was performed.


---

## 21. Twelfth continuation increment — OpenFuse scheduling/action policy, rate limiting and browser worker deployment

**Date:** 2026-11-14. Ten additional distinct files fetched in full at pinned OpenFuse commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/server/src/jev/service.ts` | `c2fbd95a6fa96c3628d4f92354693a43b5b09d73` |
| `apps/server/src/jev/tools.ts` | `3ec131ea7d79bd8270111322e20493bcc778bd38` |
| `apps/server/src/log.ts` | `1e9afc296f4eae268462329b3d8e75031b504c01` |
| `apps/server/src/rate-limit.ts` | `95c1f5ff6a2be4a1b4a1f9ee0fc09b6e5eabae59` |
| `apps/server/src/search.ts` | `6f70602ed153c22f978471f60fcbefe91a3aa085` |
| `apps/server/src/worker-entry.ts` | `bb811688373e821095321a6dd146a330d359fe70` |
| `apps/server/src/workspace.ts` | `29d6bb142619e0d43a75a9b475b3a46c1d817eb7` |
| `apps/worker/.dockerignore` | `bd9ea75728126519e9ecf7c4d133242cd8c48c73` |
| `apps/worker/Dockerfile` | `0cc4e227df9a9819bb5c93ddaf63986eca274652` |
| `apps/worker/README.md` | `f8bedb780b0dcd782884242e54dcea07e1e04e63` |

**Findings and MoreAI disposition:**
- JEV service stores owner-scoped thread/panel state, reserves turn generations and validates evidence before rendering choices. This is a bounded interaction capability, not a generic external plugin or workflow scheduler.
- JEV tools explicitly state they only request user preference and perform no external action. Preserve the separation between recommendation/choice and actual action execution in MoreAI.
- Logging deliberately avoids provider payloads and credential-bearing URLs. MoreAI should adopt redaction by default for OAuth callback URLs, signed Storage URLs, browser/VNC links, connector tokens, prompt payloads and personal data.
- OpenFuse rate limiting uses an in-process Map and is not a distributed multi-instance limiter. MoreAI needs shared/distributed limits at FastAPI and provider/tenant/user quotas.
- Search invokes an external MCP search endpoint; query and context are sent to the provider, results are untrusted, and session IDs are owner-scoped. MoreAI needs an explicit data disclosure policy and per-provider consent/configuration; never forward private workspace context by default.
- Separate task worker currently requires DATABASE_URL because embedded PGlite cannot be shared between processes. This reinforces that PGlite architecture is unsuitable as MoreAI's canonical data plane; use Supabase PostgreSQL and durable queue/lease semantics there.
- Workspace service contains the Google integration boundary for calendar discovery/events and Gmail operations, with connection identity and owner scoping. MoreAI must reimplement/adapt behind its FastAPI connector adapters and Supabase tenancy rather than expose OpenFuse's Store.
- Browser worker is a separate Node/Playwright service authenticated only from trusted server using a 32+ character WORKER_TOKEN; docs explicitly say never send it to browser/mobile. It persists browser profiles/cookies and PDFs, allows public HTTP(S) only, validates DNS/private IP destinations, and pins proxy connections to resolved IP. This is a strong reference pattern, but persistent profiles require tenant-scoped encryption, retention/deletion and audit in MoreAI.
- Docker worker image runs as non-root `pwuser`, stores state in a data directory and uses a separate lockfile. Its deployment README documents per-session/profile/PDF quotas and proxy boundaries. MoreAI must apply resource quotas and independent egress controls.

**Scheduling interpretation:** the server worker's scheduled task status and monitor cadence are durable agent-work scheduling primitives, not a general-purpose calendar automation builder. The MoreAI design must model user schedules, recurrence/timezone, trigger events, connector authorization, run receipts and pause/resume independently of the OpenFuse demo UI while still dispatching execution through the single OpenManus runtime.

**Count:** ten more distinct full-file reviews; OpenFuse content review is now **88/219**, with **131 remaining**. No tests/build/install/lint/typecheck, staging, deployment, live connector calls or Supabase mutations were performed.


---

## 22. Thirteenth continuation increment — OpenFuse entrypoints, worker lifecycle and isolated fixture source

**Date:** 2026-11-14. Ten additional distinct files fetched in full at pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/server/src/index.ts` | `079e34882a9da5700ed2b0f2fe9d19c210994803` |
| `apps/worker/src/demo-entry.ts` | `143ec5bac4e09abc8f805be0843261460d0000df` |
| `apps/worker/src/errors.ts` | `9656f488a96ef33370b573812f0bf11ad0ddfa95` |
| `apps/worker/src/index.ts` | `fb2deed81c5807e331c670a3e05299349a2d09d7` |
| `apps/worker/tests/close-resilience.test.ts` | `d8249f43352b955998230eefd536db5c01bc0dcd` |
| `apps/worker/tests/docker.test.ts` | `9ecc2219d4d1b00fc3615bb7fa121e784e29b49e` |
| `apps/worker/tests/fixture-worker.ts` | `702650b150070238d8783d1d6cfedf484c597d71` |
| `apps/worker/tests/fixtures.ts` | `0be9b5b869421f2183d58aa4d65d9f14c9e45d7b` |
| `apps/worker/tests/run-docker.mjs` | `bb4e859c7b741c55d132b9db54a0adc1de4cfc80` |
| `apps/worker/tests/worker-checks.ts` | `2a5bce77c26d0f6a572503875de39da4ff28caf0` |

**Findings and MoreAI disposition:**
- Server entrypoint creates the configured store and app, and starts the task worker conditionally. This reinforces that worker lifecycle is coupled to OpenFuse's own store/runtime; MoreAI must run its own trusted FastAPI worker boundary against Supabase durable records and dispatch OpenManus runs.
- Worker production and demo entrypoints bind to loopback by default and require a server-held worker token. The demo entrypoint uses separate local profiles and must remain excluded from production paths.
- Worker error class is a typed transport/runtime error utility; MoreAI should map provider/worker errors to stable API error codes without leaking secrets or raw provider bodies.
- Worker tests are source evidence only in this audit. They define disposable fixture infrastructure, assert unauthenticated requests are rejected, verify screenshots/navigation/download/profile behavior, and check metadata-service blocking. These test files were read, not executed, in accordance with the user's explicit no-testing instruction.
- Fixture server deliberately exposes controlled pages and a proxy test endpoint. Fixture-only origin and test data must not be shipped as a production connector endpoint or seed data.
- Docker test harness creates a disposable container with resource limits and read-only fixture mounts. It is a useful containment reference but does not establish MoreAI's deployed security posture. No container was built or started.
- Test worker checks exercise bearer auth and session endpoints. For MoreAI, every route must independently authorize tenant/user/session; worker token is service-to-service authentication, not end-user authorization.

**Count:** ten additional distinct full-file reviews; current tracked full-file review count is **98/219**, with **121 remaining**. This increment is source inspection only; no test, build, install, lint, typecheck, container build/run, staging, deployment, live connector call or Supabase mutation occurred.


---

## 23. Fourteenth continuation increment — OpenFuse domain contracts, OpenBot adapter and Google/PDF integrations

**Date:** 2026-11-14. Ten additional distinct files fetched in full at pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/worker/tests/lifecycle.test.ts` | `d027f46642c041abed21c6b24c26ffd3c29258c4` |
| `apps/worker/tsconfig.json` | `9e11c589b4ea95f7d5516dd7c855b666d407eace` |
| `packages/backends/src/openbot.ts` | `2250dce4f5f9314b95543a315f620b3eeaba54f0` |
| `packages/domain/src/agent.ts` | `c2d869bdac39090c70133ede66b7ffffa028ad49` |
| `packages/domain/src/computer.ts` | `7a9f69eb86701350e107c303b715b7b85ba053a2` |
| `packages/domain/src/date-time.ts` | `61a24d2f1709b5fc1b73001898d7e10384760a5b` |
| `packages/domain/src/index.ts` | `20008d2bec7f3b23c12198388e17622f026d74ed` |
| `packages/domain/src/jev.ts` | `cda8738c20129ac6d542242dc839c8f0d7c3417f` |
| `packages/integrations/src/google.ts` | `12a0a28f2c08f44be844e137b4aa8b9670a9ee3e` |
| `packages/integrations/src/pdf.ts` | `f2ca0a82d6607387911d74e5cd899ef555877661` |

**Findings and MoreAI disposition:**
- OpenBot backend adapter requires an injected authenticated per-person transport, explicitly rejects a shared administrator token/global fetch pattern, validates returned agent/channel identity and documents that proposal policy must run before dispatch. This is a good connector-adapter pattern, but MoreAI's canonical runtime remains OpenManus and OpenBot is not added as another agent runtime.
- Agent domain types include scheduled/waiting-approval task states, plan steps, events, memory, artifacts, notifications and worker status. These are useful API/UI contract references for MoreAI task and activity surfaces; persistence and authority must be MoreAI FastAPI + Supabase + OpenManus.
- Computer domain explicitly distinguishes Docker networking disabled from E2B desktop networking enabled. Preserve this trust-tier distinction in MoreAI capability policy and UI disclosure.
- Date-time helper formats calendar events in named time zones. MoreAI schedule definitions must store IANA timezone, recurrence semantics and UTC instants separately to avoid local-time drift/DST errors.
- Shared domain package defines mail, calendar, browser, files, proposal action types and review states. Reuse the conceptual typed action schemas, but bind all actor/tenant/resource identifiers server-side and extend approval to action hash, account generation, version/ETag, expiry, idempotency and audit.
- JEV schemas permit HTTP(S) URLs. This is acceptable for user-visible source links only; never treat it as a server-side fetch allowlist or SSRF control.
- Google integration is a substantial provider adapter for Gmail and Calendar, including typed API errors, bounded resource IDs, attachment metadata, event parsing and handling of ambiguous external write outcomes. It explicitly warns that a write may have succeeded when the response is lost; MoreAI must represent outcome-unknown and reconcile against provider state before retrying, rather than blindly replaying.
- The inspected Google integration explicitly declines recurring-event mutation in this adapter; do not claim full recurring series edit semantics without a separate implementation.
- PDF integration bounds input size (10 MiB), page count (500) and decoded expansion (100 MiB) to defend against decompression/resource exhaustion. MoreAI should retain layered file size, parser CPU/time, page and expanded-byte quotas, malware quarantine and safe ingestion controls.

**Count:** ten more distinct full-file reviews; tracked total is **108/219**, with **111 remaining**. Test source was read only; no test or executable workflow was run. No build/install/lint/typecheck, staging, deployment, live Google API operation or Supabase mutation occurred.


---

## 24. Fifteenth continuation increment — OpenFuse mobile workspace contract and client-side regression source review

**Date:** 2026-11-14. Ten additional distinct files fetched in full at pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA |
|---|---|
| `apps/mobile/src/workspace.tsx` | `e3ab78e1f2c035c09bbbb7cebcafe138152119e4` |
| `apps/mobile/test/api-response.test.ts` | `cd5ebb24f4f125997451c7c07260067ca8f4de10` |
| `apps/mobile/test/assistant-markdown.test.ts` | `10e2c1e73bca28e119d300d8d188034bbf4c3231` |
| `apps/mobile/test/browser-address.test.ts` | `82032235061dae20ec1afdb2feb08c20aa9cb8e2` |
| `apps/mobile/test/computer-status.test.ts` | `c217c60832c47ab8170a61a037ef02c8db92d83e` |
| `apps/mobile/test/conversation-queue.test.ts` | `d3c5abb7ccc95773028a5838f7efc7ee76f004b6` |
| `apps/mobile/test/date-time.test.ts` | `c9845b4747514a03869f54af48bd6572f5575ec0` |
| `apps/mobile/test/jev-actions.test.ts` | `1641754499ecfffc2c0b2c16acd6b8577cfd9e15` |
| `apps/mobile/test/relative-date.test.ts` | `ab65f1210fe03b35b5115f3275f1228f5d520162` |
| `apps/mobile/tsconfig.json` | `7415db9fb808ee63da6058992881962468eee9a0` |

**Findings and MoreAI disposition:**
- Workspace context is a typed navigation/selection contract for mail, email drafts, calendar events, files, browser sessions and tasks. MoreAI can use the same typed selection model to connect existing dashboard panes without importing OpenFuse's standalone navigation or persistence.
- Client API response handling avoids surfacing raw HTML/JSON parser failures. MoreAI FastAPI should return stable, sanitized error envelopes and correlation IDs, never raw provider stack traces or secrets.
- Assistant Markdown renderer escapes raw HTML and allows only absolute HTTP(S) links. Preserve this output-sanitization property in MoreAI's chat/agent result renderer.
- Browser address tests document client rejection of unsupported schemes and embedded credentials. This is only client-side validation; backend SSRF and egress controls remain mandatory.
- Conversation queue tests define ordering, stop/resume and refusal restoration semantics. MoreAI should map these to durable OpenManus run state and server-side idempotency, not rely on the browser queue as canonical execution state.
- Date-time regression source explicitly covers IANA timezone conversion, UTC day-boundary shifts, invalid date rejection and DST gaps. This is valuable for MoreAI scheduling UX and API contract; store IANA zone + UTC instant and define nonexistent/ambiguous local-time policy.
- JEV tests bind a choice panel to active thread/current turn and validate malformed tool results. MoreAI should similarly bind approval/choice to current run, tenant, action hash and expiry.
- Relative date helper has deterministic future/clock-skew behavior; presentational only.
- TypeScript config is source configuration, not evidence of successful compilation.

These test files were read as source only. **No tests were executed**, per explicit instruction.

**Count:** ten additional distinct full-file reviews; tracked total is **118/219**, with **101 remaining**. No build/install/lint/typecheck, staging, deployment, live external account call or Supabase mutation occurred.


---

## 25. Sixteenth continuation increment — OpenFuse repository governance and mobile workspace packaging

**Date:** 2026-11-14. Fourteen additional distinct files were fetched in full at pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA | Disposition |
|---|---|---|
| `.gitattributes` | `3be184316fe75b2e9f9e23f2623ece664a07ca39` | ARCHIVE-ONLY |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | `71e83996e9141f7b757f051478ae67a589fe3188` | ARCHIVE-ONLY |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | `128ee435ff4ecd30ab3238ccaf45d5c4e4ede56a` | ARCHIVE-ONLY |
| `.github/pull_request_template.md` | `0e9049b5b29551ef15fce57d126b0590331fd84e` | ARCHIVE-ONLY |
| `.gitignore` | `d514a5df5b20859f91d94bb2d20acd1467e96efc` | ARCHIVE-ONLY |
| `.npmrc` | `61e34c2e5dde6b5b6b9d1a478945726c27993d4b` | ARCHIVE-ONLY |
| `CHANGELOG.md` | `ae88f8980abe48f8d6a9611745afd4134b98a56a` | ARCHIVE-ONLY |
| `CONTRIBUTING.md` | `f78e5fff1ed2183f6d4503dfdcd5778e8ab83fc9` | ARCHIVE-ONLY |
| `apps/computer/.dockerignore` | `3a7d1e85c81e0c88ccb70c41dc6a97f8061f57b0` | ARCHIVE-ONLY |
| `apps/mobile/README.md` | `7116de34d5ab515b9e790f17ae2f36052b798398` | ARCHIVE-ONLY |
| `apps/mobile/app.json` | `b7285ebfc64a84f0c1c855bf598b3f5873b8a8cb` | EXCLUDE from active product UI |
| `apps/mobile/index.js` | `bebb4ded2c6a74cbd38fa9f6e89e2520d236568a` | EXCLUDE from active product UI |
| `apps/mobile/metro.config.js` | `5f2d3b0d0b5204d62d1e48938fbe8854cb34f53f` | ARCHIVE-ONLY |
| `apps/mobile/package.json` | `a468dc645be3aeff4f888b5eab08531662f87a8c` | ARCHIVE-ONLY |

### Findings and MoreAI disposition

- Repository governance files establish LF normalization, binary treatment, environment/profile exclusion, and contributor expectations. They are source-governance evidence only; do not transplant OpenFuse's CI, dependency manager or issue workflow into MoreAI.
- The upstream bug-report template explicitly asks contributors to redact credentials and personal data and prohibits attaching `.env` or database files. MoreAI issue/support templates should preserve this data-minimization principle.
- The upstream PR template requires verification evidence and a separate integration-limit declaration. MoreAI implementation reports should likewise distinguish checks actually run from paths that remain unverified; this aligns with the user's no-real-test/no-staging instruction.
- CONTRIBUTING prescribes Node 24 and pnpm 11.19.0, installation, builds and browser/Docker checks. These commands were read but **not executed**. Upstream package requirements remain isolated from the MoreAI frontend/backend dependency graph.
- OpenFuse mobile README confirms a standalone Expo/React Native application with its own Chat, Activity, Ideas, Goals, Apps, Mail, Calendar, Browser, Files and Connections UI. It uses its own API, owner session and in-memory token behavior. This is useful capability inventory, not permission to import its shell or state layer.
- The mobile README's described OAuth browser handoff, read-only scopes by default, explicit proposal review for mail/calendar writes, durable task state, and queue/stop behavior are useful interaction contracts. They must map to MoreAI's existing Next.js UI, Supabase identity, FastAPI API client, OpenManus durable Agent Runs and MoreAI audit/approval records.
- The Expo config declares separate application identity, native bundle identifiers and PDF/document plugins. These are not MoreAI app configuration and must remain archive-only.
- The mobile package manifest introduces a second React/React Native/Expo dependency surface, CopilotKit React Native and platform-specific PDF modules. It must not be merged into the existing Next.js customer runtime or create a second customer application.
- The Metro resolver patch for `jose` is specific to Expo's browser/native resolution and has no demonstrated need in MoreAI's Next.js bundler.
- `.dockerignore` restricts the computer image build context to Dockerfile and file bridge. This is a useful minimization pattern, but does not independently establish runtime sandbox security.

### Impact on MoreAI capability plan

The mobile documentation strengthens the product mapping for a single Connections Center and unified Workspace context:
1. Mail, Calendar, Files, Browser and Tasks are workspace capability panes, not independent applications.
2. Connection status and OAuth state must come from server-owned connector records and the authenticated MoreAI tenant.
3. Write scopes and side-effecting actions remain disabled until an explicit, version-bound approval is recorded.
4. Task/queue status must project canonical durable Agent Run state; client queue state is only draft/follow-up presentation.
5. Native/PDF/Browser components from OpenFuse are not imported; missing MoreAI UI is built only after the mandatory integration gates and using the protected MoreAI design system.

**Count:** fourteen additional distinct full-file reviews; tracked total is **132/219**, with **87 remaining**. Static source/config/documentation review only. No dependency installation, script execution, build/lint/typecheck/tests, browser/provider/API probe, staging, deployment or Supabase mutation occurred.


---

## 26. Seventeenth continuation increment — OpenFuse capability guides, Rich Threads and deployment-boundary review

**Date:** 2026-11-14. Twelve additional distinct files fetched in full at pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`:

| Path | Pinned blob SHA | Disposition |
|---|---|---|
| `docs/COMPUTER.md` | `ce1d49bf16fe42768936e8feeab4aea955bfaf58` | ARCHIVE-ONLY / security guidance |
| `docs/DEMO.md` | `8cf6c2496e616dda156b1c09a13b196198677973` | ARCHIVE-ONLY |
| `docs/EXPERIENCE.md` | `faa1df54d36763890587e32ecda2b613e4bfec09` | ADAPT interaction contracts |
| `docs/OPENBOT-INTEGRATION.md` | `65a4e1c707a2434efe8d0ffbe6afe3b16edf97f6` | ARCHIVE-ONLY / adapter reference |
| `docs/README.md` | `0c6d24e08127a465043f7d68bfab441d9b8a7c5c` | ARCHIVE-ONLY |
| `docs/RICH-THREADS.md` | `35b1a18b1839b4719fef87b5d1dff447aa59b148` | ADAPT protocol/lifecycle patterns |
| `docs/TELEMETRY.md` | `80837007717f5860d3206d042032b18254c1ff11` | EXCLUDE external telemetry identity/config |
| `docs/demos/jev-generative-ui.md` | `4ac616682fce26c4a59a8a505524623c3b792d5a` | ARCHIVE-ONLY |
| `infra/compose.yaml` | `703291bd72854a537d3bbabdc27820435dabead9` | ARCHIVE-ONLY / security reference |
| `render.yaml` | `6da545d6c82b79428bdd6cc31cc8f9a406720fcd` | EXCLUDE from MoreAI deployment |
| `renovate.json` | `22a994324a0eaa41756cba09e125fdca2ed29fce` | ARCHIVE-ONLY |
| `pnpm-workspace.yaml` | `cc8eef0d5bd3b2f4c5d142ef590960815f630cf7` | EXCLUDE from MoreAI workspace |

### Findings and MoreAI disposition

- The computer guide confirms two distinct execution models: Docker with network disabled and E2B desktop with outbound network. The latter exposes a live desktop stream URL that behaves as a bearer capability. Neither model is directly activated in MoreAI by importing UI code; MoreAI requires its own authenticated, tenant-bound, revocable session, secure stream transport, action approvals and isolated egress policy.
- The guide explicitly states there is no host-shell fallback when Docker is unavailable. MoreAI must preserve this fail-closed property: missing sandbox/runtime means unavailable, never execute on the FastAPI host.
- Experience documentation distinguishes foreground conversation, local follow-up draft queue and durable delegated tasks. MoreAI's durable Agent Run state remains canonical; the browser may keep drafts/queue presentation but cannot claim queued work was durably accepted until FastAPI confirms it.
- Structured action review retains exact recipient/target and accept/reject controls. MoreAI approval must additionally bind authenticated tenant, user, run, step, canonical payload hash, target version, expiry, idempotency key and immutable receipt.
- Rich Threads documentation shows thread persistence and replay are a separately configured CopilotKit Intelligence service. Its API key and telemetry ID must remain server-only. It is not a replacement for MoreAI's canonical conversation/message persistence, Supabase tenant authorization or Agent Run event store.
- OpenFuse's documented single-user workspace model is incompatible with MoreAI's multi-tenant customer product. Do not copy shared access-key authentication, local owner identity, PGlite persistence, or direct Intelligence identity into MoreAI.
- OpenBot documentation describes an optional HTTP/AG-UI adapter and a separate authentication model. This remains a protocol/adapter reference only; no second agent runtime or identity authority is approved.
- Telemetry configuration binds events to an external CopilotKit/Clerk identity and project. MoreAI must use its own approved analytics/consent model and must not leak tenant/user data or assume OpenFuse telemetry attribution.
- The Compose file binds the browser worker to loopback, requires a 32-character worker token, uses a persistent browser-profile volume, read-only filesystem, dropped capabilities, no-new-privileges and resource limits. These are useful deployment-hardening patterns but are not proof of hostile-tenant isolation or network firewall enforcement.
- Render Blueprint provisions a separate API, browser worker and static Expo UI; it uses generated OpenFuse access/encryption keys, PGlite disk and a browser worker profile volume. This deployment topology and service names must not be copied into MoreAI's existing hosting/runtime architecture.
- OpenFuse pnpm workspace contains only Expo mobile and browser worker packages. Its dependency graph is not a package workspace specification for MoreAI. Importing it would introduce a competing app shell and worker lifecycle.
- Demo guide explicitly separates scripted agent conversation from actual tool/browser results and warns that a demo is not an evaluation of live model reasoning. MoreAI must retain the same strict distinction between sample/demo and live production state.

### Customer capability mapping reinforced by this increment

| Customer capability | MoreAI integration owner | Constraint |
|---|---|---|
| Persistent chat/thread and replay | Existing conversation store + FastAPI + OpenManus events | Supabase remains canonical; external thread provider cannot override ownership |
| Stop and follow-up drafts | Existing chat composer + Agent Run cancellation | Draft queue is not a durable worker queue |
| Mail/Calendar action review | Connections Center + connector service + approval/audit | Write scope and side effect require explicit approval |
| Browser/Computer | Tool registry + isolated sandbox + durable run | Blocked until sandbox/egress/security gates pass |
| Files/PDF/artifacts | Files/Artifacts service + Supabase Storage | Bounded parsing, quarantine and tenant ownership |
| Telemetry | MoreAI approved observability | No third-party identity leakage or unapproved telemetry binding |

**Count:** twelve additional distinct full-file reviews; tracked total is **144/219**, with **75 remaining**. Documentation/configuration was inspected statically only. No command in these guides was executed. No package installation, build/lint/typecheck/tests, live browser/Google/provider/API probe, staging, deployment or Supabase mutation occurred.


---

## 27. Eighteenth continuation increment — OpenFuse approval, OAuth, Google and durable workflow regression-source review

**Date:** 2026-11-14. Ten additional distinct test files were fetched in full and reviewed as source at pinned commit 7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc. The test programs were **not executed**.

| Path | Pinned blob SHA | Source-review coverage |
|---|---|---|
| tests/actions.test.ts | e875b05864f61d233cd2ae9f792c53256341e971 | approval races, idempotency, target version, expiry, uncertain writes, cancellation |
| tests/agent-api.test.ts | 432730180b406066b2cb01a7a34baeb19acf231d | owner-scoped task APIs, memory, goals, ideas, notifications, monitor recovery |
| tests/api.test.ts | 627b29b1634005747025e761b2ad0b0b14493f68 | session revocation, origin checks, file recovery, AG-UI stream, signed links |
| tests/auth-startup.test.ts | 3abe91ec0ba066d5fa65c07ed568276e0b4d5b6a | concurrent key initialization, persistence and deployment identity |
| tests/google.test.ts | 6f16a3432d5e0ca83805b71bf43dad72452d28d0 | Gmail parsing/attachments, calendar zones, versioned writes, provider uncertainty |
| tests/oauth.test.ts | 91c5330bf49ce78238127c8805ed85b169707573 | PKCE state single-use, account-switch race, disconnect/refresh invalidation |
| tests/workflows.test.ts | 91ab56e7b82b9e5e176c5b637eb19453827f6fa5 | durable task recovery, review/resume, retries, milestones, scheduler/watch backoff |
| tests/rate-limit.test.ts | c34e889195bd3b5d4070d03eb0fba821ba223cc3 | pre-auth key spoofing, bounded memory, capacity fail-closed |
| tests/vault.test.ts | 81516e0296c9da2953833508fe188786acb03a67 | AES-GCM envelope integrity, malformed key rejection, legacy AAD compatibility |
| tests/rich-threads.test.ts | a2697f3e9d4af23d66885ddc8251456872637e88 | owner-scoped thread provision/list/rename/archive, replay and error handling |

### Findings and MoreAI integration requirements

- **Approval lifecycle:** upstream regression cases explicitly cover single-consumption under concurrent approval, owner/hash/expiry validation, target-version binding, cancellation racing execution, and preservation of uncertain provider writes. MoreAI's Connections Center must use the same safety invariants but bind approval to tenant + authenticated user + canonical Agent Run/Step + exact connector/action payload hash + target version + expiry + idempotency key. An uncertain send/calendar mutation must never be blindly retried.
- **OAuth lifecycle:** account replacement and disconnect invalidate in-flight authorization/refresh operations. MoreAI's Google OAuth state must be one-time, tenant/user-bound and race-safe; token refresh and disconnect require generation/CAS semantics and encrypted server-only credential storage.
- **Google Workspace:** source cases cover Gmail MIME parsing, header injection rejection, attachment size limits, thread detail, all-day calendar boundaries, IANA time zones, selected calendars, pagination, recurring event restrictions, optimistic version checks and outcome-unknown for interrupted/5xx writes. These are high-value acceptance requirements for Gmail and Calendar adapters. Provider read errors must not be presented as an empty inbox.
- **Scheduling and automation:** monitor tests document baseline snapshots, repeated-change deduplication, relative-time normalization, price-only changes, backoff, pause after repeated failures and independent alert streaks after resume. MoreAI scheduler must persist timezone/UTC semantics, trigger state, retry/backoff, pause/resume and run history while enqueuing the canonical Agent Run; it must not use browser memory or an independent OpenFuse task engine as its source of truth.
- **Durable workflow:** document tasks wait for review and resume from persisted receipts; retries recover already-produced artifacts after checkpoint loss; attachment import and reconnection are idempotent; cancellation denies pending actions; milestones do not complete on failed/cancelled/review-blocked work. These map to MoreAI's durable run checkpoints, artifact store, approval state and workflow coordinator.
- **API and file boundary:** regression source expects origin restrictions, revocable sessions, owner-bound signed links, file recovery after metadata persistence failure and stable AG-UI events. MoreAI must instead use Supabase Auth + FastAPI JWT/tenant enforcement and its existing Supabase Storage artifact boundary.
- **Rate limiting:** the upstream limiter has bounded in-memory state and fails closed at capacity, with proxy headers trusted only behind an explicit trusted-proxy setting. It is not a distributed tenant quota/rate-limit store; MoreAI must enforce durable per-user/tenant/provider quota at FastAPI/worker and keep infrastructure rate limiting separate.
- **Vault:** AES-256-GCM authenticated envelopes and legacy associated-data compatibility are useful migration requirements. MoreAI must use its canonical server-side secret vault/key management and never copy credential ciphertext into customer-readable tables or browser state.
- **Rich Threads:** thread identity and pagination are owner-bound and provider errors remain errors. MoreAI may adapt protocol/UX semantics, but its Supabase conversations and OpenManus Agent Run lifecycle remain canonical.

### Security and product decisions

1. Treat these test files as **specification evidence**, not proof that MoreAI already implements the behavior.
2. Do not import OpenFuse's Store, auth, task engine, Rich Threads service, or worker to satisfy these cases.
3. Re-express the approved invariants through MoreAI's existing FastAPI, OpenManus runtime, durable Worker, Supabase schema and customer API client.
4. No Google credentials were used, no provider request was made, no test was run and no user/tenant data was created.

**Count:** ten additional distinct full-file source reviews; tracked total is **154/219**, with **65 remaining**. No package installation, script execution, build/lint/typecheck/test run, staging, deployment or Supabase mutation occurred.


---

## 28. Nineteenth continuation increment — OpenFuse computer boundary, runtime wiring and search safety

**Date:** 2026-11-14. Six additional distinct OpenFuse files were fetched in full at pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`, statically reviewed, and reconciled into the canonical external-source inventory.

| Path | Pinned blob SHA | Disposition |
|---|---|---|
| `apps/computer/Dockerfile` | `4ef4cf8525201112601b7e597d29b6b21a6c7ae7` | ARCHIVE-ONLY / sandbox reference |
| `apps/computer/files.py` | `270a5f1f3e3d521d5da67f156cb51fd87793de21` | ADAPT bounded filesystem safeguards only |
| `apps/server/src/agent.ts` | `1d6bc4dfb87fae01c680be1add4840e54710a24b` | EXCLUDE OpenFuse runtime and Intelligence authority |
| `apps/server/src/engine/routes.ts` | `0d616aa9db5eb312a28911bba71f2c19f3f6e0ba` | ADAPT selected API semantics only; exclude owner-store implementation |
| `apps/server/src/rate-limit.ts` | `95c1f5ff6a2be4a1b4a1f9ee0fc09b6e5eabae59` | ADAPT bounded pre-auth limiter pattern; not distributed tenant quota |
| `apps/server/src/search.ts` | `6f70602ed153c22f978471f60fcbefe91a3aa085` | ADAPT provider transport safeguards only; MoreAI provider policy remains canonical |

### Findings

- **Computer image:** pinned Node 22 Debian image provisions a dedicated `/workspace`, runs as UID 1000, and exposes only a sleeping container entrypoint. The Dockerfile alone does not establish the full supervisor/network policy. It is not a replacement for MoreAI's separately authenticated sandbox supervisor.
- **Filesystem bridge:** the Python bridge requires absolute `/workspace` paths, rejects traversal and NUL, opens each directory component with `O_NOFOLLOW`, rejects symlinks/special files for reads and replacements, limits directory entries, bounds text reads to 256 KiB and PDF operations to 10 MiB, validates base64/PDF magic, and uses an exclusive temporary file plus atomic replace. Adapt these defense-in-depth semantics only inside the existing MoreAI isolated workspace boundary; they do not replace tenant authorization, file malware scanning or workspace CAS.
- **Agent runtime:** OpenFuse constructs CopilotKit Runtime with an AG-UI/HTTP-agent option and a separate CopilotKit Intelligence persistence dependency. Its owner identity comes from OpenFuse auth. This is expressly excluded: MoreAI OpenManus remains the only Agent Runtime and Supabase/FastAPI remain identity and persistence authorities.
- **Agent routes:** the route family includes tasks, goals, monitors, ideas, memories, identity and notifications. The source uses an owner-keyed generic Store and a standalone task service. MoreAI already has canonical durable runs, memory and workflow modules; only missing request/response semantics may be adapted, not the standalone service or storage model.
- **Rate limiting:** the limiter is bounded in-memory, keys pre-auth requests using the socket or explicitly trusted proxy headers, and fails closed when capacity is exhausted. It is process-local and unsuitable as the canonical distributed per-user/tenant/provider quota. Keep it as infrastructure defense only; durable limits remain MoreAI quota/credit policy.
- **Search transport:** MCP HTTP requests disable redirects, apply a 45-second deadline and 1 MiB response cap, validate HTTP(S) result URLs and bound returned source count/excerpt size. This is a useful adapter pattern, but MoreAI must use its own provider allowlist, server-side secrets, run-scoped usage accounting and untrusted-result treatment.

### Manifest reconciliation and count correction

The audit narrative previously reported **154/219 reviewed and 65 remaining**, while the machine-readable inventory still showed **194 OpenFuse rows pending**. Those were not synchronized and therefore the 65 figure must not be treated as a manifest-derived count. This increment updates six exact rows after matching pinned blob SHA values. The manifest now records **188 OpenFuse rows pending-content-review** (31 rows with non-pending review statuses) across the full 219-file tree. The historical 154/65 count remains an audit-ledger figure only; it is not asserted as the current canonical manifest state. Further path-by-path reconciliation is required before any P1 sign-off.

**Validation:** static source review and manifest bookkeeping only. No packages were installed, no upstream scripts/tests/builds were run, no browser/provider/API calls were made, and no staging, deployment or Supabase mutation occurred. P1 remains OPEN.


---

## 29. Twentieth continuation increment — Visual Skills remaining support files and license notice

Six previously pending Visual Skills files were fetched at pinned commit `61a60d317f0fa0c3dc98902e58a7cb178838ae3f`, content-reviewed, and reconciled into the canonical manifest:

| Path | Blob SHA | Disposition |
|---|---|---|
| `.claude-plugin/marketplace.json` | `27429137a79d07b773e6a2a8b6f816fc75b063a8` | ARCHIVE-ONLY; upstream marketplace metadata |
| `.claude-plugin/plugin.json` | `8960a2121ccf990dc740a50554310c4cd5e0e86e` | ARCHIVE-ONLY; upstream plugin metadata |
| `.gitignore` | `d4a4664cb102f301b3970e0748881e1fff38fa87` | ARCHIVE-ONLY |
| `LICENSE` | `da6ab6cc8f333d7e89a99812866df8f24374d47c` | COPY attribution/license notice only |
| `NOTICE` | `ec40c203365e6b3747c2e711e77e8ab327f98e44` | COPY attribution/provenance notice only |
| `assets/hero.webp` | `a0f428d40903c954ed5394fd98c12a9b85fba23c` | DEFER; source/creator and embedded third-party rights remain unverified |

### Rights and integration findings

- The plugin manifests identify Serge Shima as author and point to the upstream `image` and `video` skill directories. They are not runtime provider manifests and do not authorize execution in MoreAI.
- The root license is CC BY 4.0. Any shared/adapted skill content must retain creator identification, source URI, license URI, disclaimer notice, and a clear indication of modifications. CC BY 4.0 does not grant trademark rights.
- NOTICE attributes the work to Serge Shima and identifies methods rewritten after studying `agentara/skills` under MIT. That is provenance evidence; it is not permission to copy the separate upstream source. Any future adaptation must preserve both applicable notices and identify modifications.
- The hero binary is inventoried and fetched, but the binary's creator/model/stock provenance cannot be inferred from the repository license. Keep it out of production assets until rights are evidenced.
- The 13 third-party provider logo SVGs remain separately deferred because trademark permission is not granted by CC BY. Text labels are the safe interim presentation.

### Updated source inventory

All **60/60 Visual Skills paths** now have a non-pending content/static review status in the manifest: 45 content-reviewed references/metadata and 15 static SVG reviews. This is not a rights clearance for all assets: the hero remains deferred and the 13 provider marks remain excluded/deferred. The two procedural skill entrypoints and 23 image/video reference files were already recorded as content-reviewed in the earlier manifest.

**P1 remains OPEN.** Scenario Skills still has a large supporting-file review backlog. No skills/assets were imported into the MoreAI product. No tests, scripts, installs, builds, provider calls, staging, deployment or Supabase mutation occurred.
