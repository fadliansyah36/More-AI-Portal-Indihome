# P1 — External Source Governance & Capability Inventory

**Status:** IN PROGRESS — immutable pins and initial capability mapping recorded; recursive inventory and per-file/dependency audit remain open.  
**Branch:** main · **Review date:** 2026-11-14  
**Restrictions:** No tests/build/lint/typecheck, browser/API/provider probes, staging, Supabase mutation/migration apply, deployment, package installation or source import.

## 1. Controlling MoreAI rules reviewed

Reviewed root AGENTS.md. Mandatory rules:
- OpenManusWeb is the authoritative backend source. Complete pristine source copy and backend parity are mandatory; selective inspiration cannot replace this.
- Existing Next.js customer UI is protected. Only the smallest genuinely missing integration UI may be added, following PRD section 16 and reference images.
- Browser uses Supabase Auth only; business data/actions flow through typed frontend API client → FastAPI → server-side Supabase.
- OpenManus remains the sole Agent runtime; current durable worker and Supabase run lifecycle remain canonical.
- No post-integration product domain implementation before mandatory Phase 00–11 gates pass, absent written product-owner exception.
- No fake integration/completion claims; implementation report and next phase are required.

Existing OpenManus source manifest inspected: `YunQiAI/OpenManusWeb`, branch `dev_web_app`, commit `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`, tree `41258ca11d4299beab17e4172fbcf8303eac1a6b`, 111 tracked files, 111 matching destination blob SHAs, zero mismatches/exclusions. This remains the mandatory backend authority.

## 2. Immutable external source pins

| Repository | Pinned commit | Root license | Initial inventory evidence |
|---|---|---|---|
| [CopilotKit/OpenFuse](https://github.com/CopilotKit/openfuse) | `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc` (Nov 13, 2026) | MIT, Copyright 2026 OpenFuse contributors | Root dirs .github, apps, assets, docs, infra, packages, patches, tests; 53 test files enumerated; app/package recursive inventory remains open |
| [smixs/visual-skills](https://github.com/smixs/visual-skills) | `61a60d317f0fa0c3dc98902e58a7cb178838ae3f` | CC BY 4.0; NOTICE Copyright 2026 Serge Shima + third-party acknowledgement | Two entrypoints image/SKILL.md and video/SKILL.md; 8 references and 2 assets surfaced; full nested tree remains open |
| [scenario-labs/skills](https://github.com/scenario-labs/skills) | `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | MIT, Copyright 2026 Scenario Inc. | Pinned root listing returned 172 SKILL.md links and 210 visible file links; nested asset/script/reference/test inventory remains open |

Pins are immutable for this review. Do not follow latest/main or install latest without a new review and pin.

## 3. License, attribution and source constraints

### OpenFuse
- Root LICENSE is MIT. Preserve notice for copied substantial portions.
- SECURITY.md says one owner per deployment and shared access key; not multi-tenant account authentication.
- README/docs distinguish implemented alpha features from planned roadmap extensions. Never present roadmap items as shipped.
- No source import approved; nested asset and dependency license audit remains open.

### Visual Skills
- Root LICENSE is CC BY 4.0.
- NOTICE requires attribution: **Serge Shima — https://github.com/smixs/visual-skills** and records methods adapted from agentara/skills under MIT. Preserve acknowledgement where applicable and mark modifications.
- image/SKILL.md and video/SKILL.md are intentionally thin routers; linked references are part of their functional content.
- Image skill writes prompts and does not generate images. Its mandatory loading order is models.md → one selected model reference → golden-rules.md → task-specific references → creative-direction.md → prompt-framework.md when needed.
- Video skill covers director/screenwriter/editor workflow and requires dramaturgy, universal rules, selected model references and task-shaped references.
- No import approved until all linked references and NOTICE dependencies are inventoried.

### Scenario Skills
- Root LICENSE is MIT. Root AGENTS.md is a strict skill authoring/public-content contract.
- Unique skill names; manifest `name`, `description`, `license`; supporting files linked directly one level deep; core scripts have root tests; expert tools test per family.
- Tool/model claims must be grounded in current MCP docs. Dynamic model discovery; schema before execution; dry-run exact payload; jobs_wait for pending jobs. No hardcoded generative model IDs.
- DCC/game-engine expert skills require their local applications and authorized execution channels.
- Per-skill license metadata, nested assets, external-source provenance and dependency licenses remain to be audited.

## 4. Initial source inventory

### OpenFuse
Visible root dirs: `.github/`, `apps/`, `assets/`, `docs/`, `infra/`, `packages/`, `patches/`, `tests/`. Root files surfaced include .env.example, .gitattributes, .gitignore, .npmrc, CHANGELOG, CONTRIBUTING, LICENSE, README, ROADMAP, SECURITY, biome.json, package.json, pnpm-lock.yaml, pnpm-workspace.yaml, render.yaml, renovate.json, tsconfig files. Docs surfaced: FEATURES, VERIFICATION, DEMO, COMPUTER, RICH-THREADS, TELEMETRY, OPENBOT-INTEGRATION. Tests listing returned 53 files covering actions, API/agent, auth, browser, computer, conversations, finance, Google, jobs/monitoring, PDF, persistence, rich threads, search, telemetry, vault and workflows. `infra/compose.yaml` surfaced. This is not a complete recursive tree; apps/packages subtrees remain unresolved.

### Visual Skills
Primary skill files: `image/SKILL.md`, `video/SKILL.md`. Root files include LICENSE, NOTICE, README.md, README.ru.md, .gitignore. Assets surfaced: `assets/hero.webp`, `assets/dramaturgy-banner.svg`. References surfaced: video dramaturgy, Seedance, Kling, Veo, universal rules, Seedance 2.5; image Nano Banana and GPT Image. Other files linked by SKILL.md remain to be enumerated.

### Scenario Skills
README groups core MCP skills, creative/content production, image/video/audio/3D model families, consistency/training, workflow/governance, and expert families for ZBrush, Blender, Maya, Unreal, Unity, Godot and Roblox. Root listing returned 172 SKILL.md links and 210 visible file links; exact full nested file count is not established. Root governance/build files include AGENTS.md, LICENSE, README, INSTALL, SECURITY, CONTRIBUTING, package/lockfiles, skills-lock, skills.sh index, scripts and tests.

## 5. MoreAI integration seams inspected

### Frontend — `lib/api/client.ts`
- Supabase browser client is used for Auth session retrieval/refresh/sign-out.
- Business API calls use `NEXT_PUBLIC_MOREAI_API_URL` with optional customer/partner origins.
- Typed JSON calls, raw customer fetch for binary/streaming and stream event/reconnect/replay contract exist.
- This is the canonical frontend integration seam; do not add another client or direct browser business-data access.

### FastAPI — `apps/api/README.md`
- FastAPI is the only business-data and AI execution boundary.
- Documented endpoints cover conversations, messages, agent runs, cancellation, events and streams.
- Supabase business data is accessed server-side with authenticated user/ownership scope.
- Documentation evidence only; no runtime endpoint invoked.

### Worker — `apps/worker/README.md`
- Durable Supabase claim/heartbeat/checkpoint/finish/cancel lifecycle.
- Durable planning steps and checkpoint manifest.
- Manus text runtime and Planning runtime through metered LLM gateway.
- DB-driven model routing, request idempotency, credit reservation, provider usage and settlement.
- Worker registers Manus and Planning only.
- SWE, Bash, Python, browser, process and workspace editing are explicitly blocked pending isolated sandbox deployment/review.
- Worker activation is fail-closed pending provider routes/secrets/wallet/credit conversion/quota/entitlement/health validation.

These findings are source/document inspection, not live service verification.

## 6. Source-to-MoreAI capability parity matrix

| External capability | MoreAI canonical owner | Status | Decision |
|---|---|---|---|
| OpenFuse chat, AG-UI projection, inline cards | Existing Chat + client.ts + FastAPI + OpenManus | PARTIAL | Extend event mapping/follow-up queue only where missing; no CopilotKit persistence/runtime |
| Follow-up queue, retained draft, side threads | Existing conversation lifecycle | PARTIAL/UNKNOWN | Inspect current lifecycle; no new thread store |
| Task plans, checkpoints, leases, retry/cancel | Existing Agent Runs/Steps/Events/Checkpoints + worker | EXISTS/PARTIAL | Extend only missing fields/events; no parallel task engine |
| Browser profiles/session/Take Control/download | Existing tool registry + isolated worker/sandbox + Files/Artifacts | MISSING/BLOCKED | Implement only within MoreAI tenant security boundary |
| Linux terminal/workspace/desktop | Existing sandbox boundary | MISSING/BLOCKED | Keep fail-closed; non-root, no network by default, no host mounts/secrets |
| Action review/receipts | Existing approvals/audit | PARTIAL | Bind to exact action/user/tenant/run/step/hash/idempotency |
| Goals/recurring monitoring/Ideas | Existing workflow scheduler + durable runs + notifications | PARTIAL/UNKNOWN | Scheduler only enqueues Agent Runs; evidence-backed suggestions |
| PDF forms/CSV analysis | Existing Files/Analyse/Artifacts | PARTIAL/UNKNOWN | Preserve originals; do not conflate analysis and wallet/ledger |
| Visual image/video skills | Skill Registry + Create | NOT IMPORTED | Import only after all linked references and attribution review |
| Scenario MCP core | Private Tool/Provider adapter + OpenManus | NOT CONNECTED/EVIDENCED | No browser MCP or provider secrets; use existing run/ledger |
| Scenario image/video/audio/3D | Create + provider adapter + artifacts + credits | NOT INTEGRATED | Discover → schema → validate/dry-run → idempotent run → wait → artifact → settle |
| Scenario saved workflows | Existing MoreAI Workflow/Agent Run | ADAPT ONLY | Scenario graph is a provider capability, not canonical orchestration |
| Scenario DCC/game-engine expert tools | Optional skill knowledge + authorized local execution | NOT IMPORTED | Require local app and explicit permission |
| OpenFuse Hono/PGlite/shared-key auth/Intelligence persistence | None | EXCLUDE | Conflicts with FastAPI/Supabase/multi-tenant identity |
| OpenFuse independent task/agent engine | None | EXCLUDE | OpenManus is sole runtime |
| Scenario workflow replacing MoreAI workflow | None | EXCLUDE | MoreAI remains orchestration authority |

## 7. Import eligibility

**No mass import approved.**
- OpenFuse: adopt selected patterns only; code import requires complete nested inventory, dependency/license review and module security assessment.
- Visual Skills: likely eligible for attributed procedural content after all references and NOTICE dependencies are closed.
- Scenario: selective import by MoreAI capability; do not wholesale import all 172 surfaced skills. Expert DCC/game-engine skills are optional and require local execution infrastructure.
- Do not run upstream scripts, install packages or connect provider credentials during this governance phase.

## 8. P1 closure checklist

1. Full recursive OpenFuse tree: apps, packages, assets, docs, patches, tests; every file path, byte size, blob identity and SHA-256.
2. Full recursive Visual Skills image/video references, assets, plugin manifests and linked sources.
3. Full recursive Scenario tree: 172 surfaced entrypoints, references, scripts, assets, tests, family READMEs, plugin/agent metadata and lockfiles.
4. Per-file provenance/license/attribution matrix and dependency SBOM; flag third-party assets/model docs/tutorial-derived content separately.
5. Inspect exact upstream implementation/security for browser, computer, worker, server, OAuth, PDF, finance, goals, notifications, MCP, model execution and DCC bridges.
6. Inspect MoreAI routes/hooks/API routers/worker adapters/migrations/RLS/UI components; replace PARTIAL/UNKNOWN with file-level evidence.
7. Resolve official Phase tracker and Phase 09 continuation report. Do not change phase status without evidence.
8. Final sign-off classifies every source file: copy, adapt, archive-only, exclude or defer. No mass copy before closure.

## 9. Current boundary and next phase

P1 is **not complete**. This report records immutable pins, root license findings, initial inventory, inspected MoreAI seams and initial parity. Recursive inventories, nested licensing, SBOM and file-level mapping remain blockers.

Primary product integration remains Phase 09: connect existing customer dashboard behavior to FastAPI/OpenManus/worker/Supabase. Do not create duplicate Chat, Tasks, Workflow, Agent Studio, Create, Research/Analyse, Files, Wallet, API client, run lifecycle, notifications or memory.

**Next:** P1 continuation — close recursive inventories, nested license/dependency review and file-by-file mapping. Then return to the mandatory AGENTS.md Phase 00–11 dependency gates; do not skip or reorder them.
