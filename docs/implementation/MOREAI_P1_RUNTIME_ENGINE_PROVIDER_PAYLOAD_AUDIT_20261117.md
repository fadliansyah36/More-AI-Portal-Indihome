# P1 Continuation — Runtime, Engine, Provider and Skill Payload Audit

**Date:** 2026-11-17  
**Branch:** `main`  
**Status:** EVIDENCE ADDENDUM — P1 NOT CLOSED  
**Scope:** Read-only source inspection and integration-boundary clarification. No provider activation, dependency installation, code execution, tests, staging, database writes, migrations or deployment.

## 1. Governing interpretation

The user's instruction to bring over more than skill markdown is consistent with `AGENTS.md`. The required deliverable is not a collection of copied `SKILL.md` files. For every pinned source, the governance and implementation inventory must cover all repository-owned, relevant and legally reusable material:

- skill entrypoints and all referenced knowledge files;
- scripts, source modules, tests, fixtures and helper binaries/assets;
- model/provider adapters, SDK wrappers and API clients that are actually present in source;
- workflow definitions, orchestration, tool schemas and execution logic;
- package manifests, lockfiles, build configuration and runtime configuration templates;
- licenses, notices, provenance and third-party asset references.

The final integration still has to preserve the canonical MoreAI boundaries: OpenManus is the single agent runtime; OpenFuse is adapted into the existing FastAPI/worker/sandbox architecture, not deployed as a second runtime; Supabase remains the only canonical business database; the existing customer frontend remains the product UI and calls business services through the typed FastAPI client.

A source repository cannot supply implementation code for a remote service it merely calls. In those cases, MoreAI must implement a documented, secure provider adapter using the provider's published MCP/API contract. It must not claim to have copied the provider's private engine or backend.

## 2. New pinned-source evidence

### 2.1 OpenFuse

Pinned source: `CopilotKit/openfuse@7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`.

The root `package.json` identifies a private MIT-licensed ESM monorepo, Node `>=22`, pnpm `11.19.0`. It includes:

- a Hono/Node server entrypoint (`apps/server/src/index.ts`);
- a separate worker entrypoint (`apps/server/src/worker-entry.ts`);
- a browser worker (`apps/worker`) and computer execution area (`apps/computer`);
- MCP SDK, AG-UI, CopilotKit runtime, TanStack AI provider adapters, E2B desktop, PostgreSQL and Zod dependencies;
- a separate Expo/React Native mobile client (`apps/mobile`).

The root pnpm lockfile is a real transitive resolution graph, not just a list of direct dependencies. It records resolved package versions, peer contexts and integrity hashes. The workspace manifest explicitly includes `apps/mobile` and `apps/worker`; the server is the root package.

**Integration consequence:** OpenFuse must be audited and mapped by runtime boundary and capability, not copied wholesale into a running second Node service. Server/domain/orchestration/MCP/tool/browser/computer/worker logic that is relevant must be ported or adapted into the MoreAI FastAPI and worker boundaries. Mobile UI and any competing product frontend are retained only in the source snapshot/provenance archive, not mounted as the MoreAI customer frontend. E2B and any other external execution backend remain disabled until tenancy, secret handling, network policy, approvals, cost and durable lifecycle controls are explicitly integrated.

### 2.2 Scenario Skills

Pinned source: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`.

The pinned `AGENTS.md` states that core agent procedures use the Scenario MCP tools; it explicitly distinguishes scripts (where an official public SDK can be used where appropriate) from the steps the agent itself is taught to perform. It also defines sibling-skill loading, approval/budget rules, provenance and authoring constraints.

**Integration consequence:** importing only `SKILL.md` would be incomplete. The selected payload must include every referenced `references/`, `scripts/`, schemas, fixtures, family-level README, tests and other required files. The skill resolver must capture sibling-skill dependencies and the correct installation set. Scenario workflows/tools/API execution are remote provider capabilities, not server source contained in the skills repository. MoreAI therefore needs a provider adapter for the documented Scenario MCP/API contract, credential lifecycle and permission/budget policy. Do not copy an imagined Scenario server or activate calls during source governance.

The repo includes internal maintainer skills and third-party vendored authoring aids; these must remain separately classified from product-facing skills. Their nested licenses and source locks remain part of the file-level review.

### 2.3 Motion Skills

Pinned root: `iart-ai/motion-skills@9b9ce041932da787cc856d4cdf23afb6cd13d4bf`, with 19 independently pinned child packs in the existing P1 pack manifest.

The root README describes 56 installable skills across 19 packs. It says each skill can contain `SKILL.md`, `references/` and scripts for rendering/inspection. It documents an optional remote iArt MCP endpoint at `https://app.iart.ai/api/mcp`, authenticated by a user-created API key, and separately references a REST API/documentation. It identifies the talking-head pack as using an AI media pipeline and the current pinned source has a Node >=22 package manifest.

**Integration consequence:** the payload audit must include each selected pack's source, references, scripts, tests, manifests, lockfiles, render engines and media-processing dependencies. A pack that teaches Remotion/Manim/HTML/Canvas rendering can be integrated only with its actual required source/runtime dependencies and sandbox constraints, not by copying markdown alone. A pack that delegates generation to iArt or another remote media provider requires a MoreAI provider adapter and explicit customer credential/consent, pricing/credit metering, job lifecycle, artifact storage, webhook/polling, timeout/cancellation and data-retention controls. The remote iArt service implementation is not present in the skill repo and cannot be copied from it.

The `generative-illustration-skills` child pack remains blocked from reuse under the existing license finding. Its files cannot be mass-imported merely because the root Motion Skills repo is MIT.

### 2.4 Visual Skills

Pinned source: `smixs/visual-skills@61a60d317f0fa0c3dc98902e58a7cb178838ae3f`.

The pinned README identifies two product skills (`image` and `video`) and describes a layered prompt pipeline: dramaturgy, universal rules, model-specific references, task modules, and mandatory output audits. It explicitly states CC BY 4.0 and requires attribution to Serge Shima for copies and derivatives. It also credits third-party model logos from lobe-icons (MIT), while the existing audit has already deferred provider logo SVGs and held other assets pending provenance.

**Integration consequence:** a complete reusable payload is the two skill trees plus all referenced model/task references and required assets, not just their entrypoint markdown. Attribution and asset-level licensing must travel with every copied or adapted derivative. Model references describe external model capabilities and prompt formats; they do not include the underlying model inference engine. MoreAI must route generation through its own approved LLM/media gateway and provider adapters.

## 3. Complete payload policy by source class

| Source class | Required treatment |
|---|---|
| OpenManusWeb | Preserve the complete pinned repository snapshot in `vendor/openmanusweb`; separately port every backend/runtime capability into production modules and track parity. |
| OpenFuse | Preserve pinned source and lockfiles; port relevant server, worker, orchestration, MCP, tool, browser and computer logic into FastAPI/worker/sandbox. Do not run a second runtime or import its mobile frontend as product UI. |
| Scenario Skills | Preserve each selected full skill folder, references, scripts, tests and dependency metadata. Implement a Scenario MCP/API adapter; remote provider internals are out of scope unless separately published as source. |
| Motion Skills | Preserve selected pack payloads including render scripts/engines/configs/dependencies. Integrate local rendering engines where present; implement guarded adapters for remote iArt/media services. |
| Visual Skills | Preserve both complete skill trees and required references; apply CC BY 4.0 attribution and independently govern all assets/logos. |
| All sources | Keep source pin, source path, destination path, Git blob SHA, raw SHA-256, size, license/NOTICE, dependencies, references, disposition and integration target in the evidence register. |

## 4. Dependency and provider boundary findings

1. OpenFuse's pinned lockfile contains the transitive Node dependency graph, including workspace importer contexts and package integrity values. The previous SBOM's PURL inventory must be reconciled against this lockfile and the exact importers before it can be called complete.
2. MoreAI root `package.json` has version ranges for many dependencies, while the repository has no root lockfile in the prior audit. `apps/api/pyproject.toml` and `apps/worker/pyproject.toml` declare direct Python dependencies but no checked-in Python lockfile was found in the prior audit.
3. OpenManusWeb's pinned `requirements.txt` includes unpinned/ranged requirements. They cannot be treated as reproducible exact versions until a lock/resolution is generated in an approved environment. No package installation is authorized in this task.
4. Scenario and iArt MCP endpoints are external services. Their credentials must be stored server-side and never copied into source, browser bundles, docs or generated manifests.
5. Third-party image/video model providers, logos, SDKs, CLIs, ffmpeg/Remotion/Manim and application bridges each require independent license, dependency, network, security and cost review. Presence in a skill reference is not proof that the dependency is vendored or licensed for redistribution.
6. Provider adapters must use the shared MoreAI gateway/connection registry, not introduce per-skill secret stores, independent billing or an alternate orchestration runtime.

## 5. Required next P1 work (still open)

- Expand the content-level review from path-level preliminary classification to every candidate file in each selected skill/engine payload.
- Record all nested LICENSE/NOTICE/COPYING files and SPDX/license expressions, including vendored skills, sample assets, logos, fonts, model marks and referenced repositories.
- Extract each skill's reference graph (links and local relative paths), script imports, subprocess calls, environment variables, network endpoints, MCP tool names, SDKs, runtime requirements and output formats.
- Build the complete dependency graph from lockfile importers and Python requirement sources. Reconcile all previous `NOASSERTION` package coordinates with authoritative package registry metadata and exact versions. Keep unknowns explicitly unresolved; do not infer licenses from package names.
- Compute raw SHA-256 and byte size for every file selected for copy/adaptation, not only the previous 34-file sample. Retain upstream Git blob SHA as a separate field.
- Replace preliminary dispositions with final decisions: copy, adapt, archive-only, exclude or defer, each with file-level evidence and rationale.
- Only after the above evidence is complete can P1 be submitted for closure and the P2 ADR finalized/accepted.

## 6. Explicit non-goals and safety holds

- No Scenario, iArt, Fal.ai, E2B, model-provider or other external service connection or request was made.
- No credentials, OAuth grants, paid generation, API keys or customer data were accessed.
- No skill was activated, installed into production, or exposed to customers.
- No package install, script execution, build, lint, typecheck or test was run.
- No Supabase write, migration, policy change or storage mutation was made.
- No staging, production deployment or frontend redesign was performed.

## 7. Phase position

P1 Source Governance remains **IN PROGRESS**. This addendum is evidence, not closure. P2 ADR remains **DRAFT / NOT ACCEPTED**. Mandatory Phase 04, 06, 07, 08 and 09 remain in progress; Phase 09 must be completed before Phase 10. Because the user prohibits real testing and staging, Phase 10 and Phase 11 cannot be marked accepted or passed on this work.

**Next action:** finish the complete file-level payload/reference/license/dependency/hash evidence, then close P1 and accept P2 before continuing the mandatory integration phases.

## Selected skill entrypoint scope confirmation — 2026-11-17

A selected-entrypoint register was generated from the pinned recursive source manifests: `MOREAI_P1_SELECTED_SKILL_ENTRYPOINTS_20261117.csv`.

| Source | Product skill entrypoints |
|---|---:|
| Visual Skills | 2 |
| Scenario Skills | 172 |
| Motion Skills | 55 eligible |
| Motion Skills blocked pack | 1 (`generative-illustration-skills`) |
| Total eligible entrypoints | **229** |

The 55 Motion entries exclude the unlicensed generative-illustration pack. The register records exact source repository, commit, path, Git blob SHA and expected byte size. This is an entrypoint inventory, not a content-level audit of every referenced file. Complete recursive references/scripts/assets review and raw SHA-256 of every selected payload file remain open.

The pinned dependency graph and first-pass npm registry license metadata are documented in `MOREAI_P1_NORMALIZED_PNPM_GRAPH_AND_REGISTRY_LICENSES_20261117.md`. These findings do not authorize importing any skill or activating remote providers.


## Selected skill payload closure — 2026-11-17

The selected entrypoint register covers 229 eligible skills: 2 Visual Skills, 172 Scenario Skills and 55 Motion Skills. Their folders contain 1,923 unique files totaling 26,586,168 bytes. The row-level file inventory is MOREAI_P1_SELECTED_SKILL_PAYLOAD_MANIFEST_20261117.csv.

Content-type counts: 229 SKILL.md entrypoints; 723 reference documents; 898 executable-source files; 67 configuration/schema files; 4 fonts; and 2 media/binary assets. Current proposed decisions are 952 adapt (entrypoints and reference docs) and 971 defer (executable source, configuration and binary assets). All rows remain PRELIMINARY_NOT_FINAL.

A binary-safe recursive auditor has been added at scripts/p1/audit_skill_payloads.py. It computes SHA-256, Git blob SHA-1 and byte-size parity from exact pinned raw bytes; it follows local Markdown/HTML/script references and records external/unresolved links. The tool has not been run. No source code was executed.

Root/nested license and notice path hashing is a completed, separate evidence pass: 25 paths, seven unique Git blob objects, 25 SHA-256 rows, 22 MIT, one CC BY 4.0, one attribution NOTICE and one nested Apache-2.0. See MOREAI_P1_LICENSE_NOTICE_SHA256_20261117.csv. This does not establish that every payload file is covered by those notices.
