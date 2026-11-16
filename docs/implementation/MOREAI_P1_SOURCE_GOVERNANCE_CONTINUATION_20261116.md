# MoreAI P1 Source Governance — Continuation 2026-11-16

Status: **IN PROGRESS — source pins and first-pass entrypoint/license review recorded; recursive inventory, dependency/SBOM, nested provenance and approval remain open.**

This document supplements Master PRD sections 35–37. It does not authorize mass import, package installation, script execution, provider calls, migrations, staging or deployment.

## Execution constraints

- Canonical repository: `fadliansyah36/More-AI-Portal-Indihome`, branch `main`.
- Current inspected main head: `106357690c457a8f43dd7df8e028794c40799c50`.
- Preserve existing Next.js customer UI. Add UI only for proven missing behavior and reuse existing tokens/components.
- OpenManus remains the sole Agent Runtime; FastAPI the trusted business API; Supabase the canonical persistence plane; existing durable worker/run lifecycle remains authoritative.
- No real tests, staging, deployment, provider calls, database mutations, or migration application in this continuation.

## Source pins and first-pass evidence

| Source | Immutable review pin | Evidence fetched | Initial decision |
|---|---|---|---|
| OpenManusWeb | `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` on `dev_web_app` (AGENTS.md) | Existing AGENTS source-copy claim: 111/111 Git blob matches in `vendor/openmanusweb/`; needs current manifest reconciliation | Keep pristine vendor snapshot; adapted code only in MoreAI workspaces |
| OpenFuse | `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc` | README, root MIT LICENSE, `docs/FEATURES.md`, `docs/COMPUTER.md` | Adapt capability contracts; exclude its Hono/PGlite/single-owner auth/independent task runtime/CopilotKit persistence |
| Visual Skills | `61a60d317f0fa0c3dc98902e58a7cb178838ae3f` | Root CC BY 4.0 LICENSE/NOTICE and `image/SKILL.md`, `video/SKILL.md` | Adapt as versioned procedural skills only; preserve attribution and modification notice |
| Scenario Skills | `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | README, root MIT LICENSE, AGENTS.md | Capability catalogue, not a single package; per-skill manifests/assets/dependencies still need audit |
| iart-ai Motion Skills | `9b9ce041932da787cc856d4cdf23afb6cd13d4bf` (`master`, reviewed commit 2026-11-13) | README and root MIT LICENSE | Add as a separate motion-graphics skill source; do not treat it as a media provider or runtime |

### Blob evidence recorded

| Source path | Git blob SHA |
|---|---|
| OpenFuse README.md | `1e07e33e37072b08b19ab2f5deddeed1cd709971` |
| OpenFuse LICENSE | `0e1238724a08528992a39ef43c63f899432a282c` |
| OpenFuse docs/FEATURES.md | `c44b5dca81e8970f7c93649282f9f55515636f60` |
| OpenFuse docs/COMPUTER.md | `ce1d49bf16fe42768936e8feeab4aea955bfaf58` |
| Visual Skills image/SKILL.md | `21f54f320d568d899642911e55e2e9d8b83e3d7e` |
| Visual Skills video/SKILL.md | `f764ae5e7c749aca504cbcf8618a88689611e325` |
| Visual Skills NOTICE | `ec40c203365e6b3747c2e711e77e8ab327f98e44` |
| Scenario Skills README.md | `9af17718eb780f5d012d915d5dac6e9dd3b7fe2f` |
| Scenario Skills AGENTS.md | `f3510c276606e7cd7dcb7f962bcf699f813f96ed` |
| Scenario Skills LICENSE | `05676553d9d10a0effff673b507b4fcfed652c17` |
| Motion Skills README.md | `3c2554af383b23c66625b81b9b3ad3c2d153d4db` |
| Motion Skills LICENSE | `a61b911146037f2ef312f67e9b45de6c99b7f870` |

These are sampled root/entrypoint records, **not** a complete per-file SHA-256 or recursive manifest.

## Additional source: iart-ai/motion-skills

The reviewed README describes 56 skills across 19 separately installable packs, covering:
- short-form TikTok/Reels/Shorts and text-message storytelling;
- YouTube, talking-head and b-roll workflows;
- ecommerce and ad-video production;
- data animation, explainers, maps and kinetic typography;
- web animation, WebGL, motion design and JavaScript canvas animation;
- Manim/math animation and generative illustration;
- lower-thirds and transparent overlays.

The repository README says visual-artifact skills include a deliver-and-verify loop (render frame, screenshot, inspect) and small helper scripts. This is source-reported behavior, not verified by MoreAI. The repository describes iArt remote MCP as a separate beta SaaS service requiring an iArt API key; this must not be enabled or called without explicit provider approval, credential handling, pricing/credit mapping, privacy review and a server-side adapter.

**Integration treatment:** import only selected skill packs after full file/reference/script/license review. Treat them as procedural content and renderer guidance. Map outputs to existing Create/Agent Run/artifact contracts. Remotion/Manim/JavaScript renderers, if selected, must run inside an isolated worker/sandbox with pinned dependencies, quotas, no host secrets and durable artifact receipts. Never install source scripts or run them on the FastAPI host. Preserve MIT notice for copied substantial portions. The root README alone does not establish the license/provenance of every linked external pack; each pack is a separate repository and requires its own pin and audit.

Source: https://github.com/iart-ai/motion-skills

## Source behavior and risk notes

### OpenFuse
- README identifies it as an alpha/self-hosting personal-agent application with its own server, task worker and browser worker.
- Its feature inventory distinguishes implemented capabilities from extensions and states the Linux computer is disabled until configured, single-owner, and has no network access.
- Its optional E2B desktop documents bearer-like stream URLs and owner/deployment sandbox assumptions. These are not acceptable as-is for MoreAI multi-tenant isolation.
- Reuse only bounded capability patterns: browser session, action review/receipts, durable task projection, PDF/CSV processing and connector lifecycle. Map all work to existing MoreAI Agent Runs, FastAPI, approvals, files and notification domains.

### Visual Skills
- Both image and video entrypoints mandate progressive reference loading; reading only SKILL.md is insufficient.
- Image skill requires model selection and model-specific references, then golden rules and task-shaped references.
- Video skill requires dramaturgy and universal rules, then model-specific and task-specific references, followed by dramaturgy/three-detail checks.
- The image skill writes prompts and does not generate images. Video skill is director/screenwriter/editor prompt methodology, not a generator.
- NOTICE credits Serge Shima and identifies third-party methods adapted from agentara/skills. Preserve applicable acknowledgements and inspect relevant source before reuse.

### Scenario Skills
- README distinguishes Scenario MCP skills from DCC/game-engine expert families (Blender, Maya, ZBrush, Unreal, Unity, Godot, Roblox).
- AGENTS.md requires unique skill names, directly linked supporting references, per-skill metadata/license and script test suites for shipped core scripts.
- Dynamic model discovery, runtime schema retrieval, exact-payload dry-run/cost, durable job wait and next-step/concurrency handling must be preserved.
- Skill instructions, manifests and provider outputs are untrusted content; none grants execution permission. MoreAI Tool Registry and policy engine remain authoritative.

## MoreAI implementation evidence rechecked

- `apps/api/README.md`: FastAPI is the only business-data and AI execution boundary; current documented conversation and Agent Run endpoints exist. Pinned Skill ingestion uses server-only GitHub token and does not publish/execute packages.
- `apps/worker/README.md`: durable Supabase run lifecycle, Manus/Planning, metered LLM routing and optional OpenFuse Browser adapter are documented. Browser capability remains conditional on a private persistent worker, token, egress attestation and authenticated boundary. Computer execution remains behind isolated supervisor/release gates.
- `lib/api/client.ts`: existing typed authenticated API client and stream contract should be extended, not duplicated.
- `docs/implementation/PHASE-TRACKER.md`: Phase 09 remains IN PROGRESS; Phase 10 is PARTIAL / NOT ACCEPTED; Phase 11 is BLOCKED. It also records unapplied migrations and unverified worker/provider/runtime integrations. The current task must not relabel these gates as complete.

## P1 closure work still required

1. Capture recursive Git trees for all five sources at immutable commits, including symlinks/submodules where present.
2. Record every file path, byte size, Git blob SHA, SHA-256, file type, license/attribution, dependency relationship, security classification and destination decision.
3. For Visual Skills, resolve every direct reference link recursively and capture all reference files and their hashes.
4. For Scenario Skills, enumerate every skill manifest and all nested references/scripts/assets/tests; record per-skill license and third-party material.
5. For Motion Skills, enumerate the root skill tree and all 19 linked pack repositories. Pin and audit each selected pack independently; do not assume root MIT applies to every separately hosted pack.
6. For OpenFuse, reconcile all application/package/server/browser/computer/worker/docs/test files and root/nested licenses. Include SECURITY.md, ROADMAP.md, Rich Threads, telemetry and OpenBot integration docs in parity inventory.
7. Produce dependency/SBOM and license/vulnerability reconciliation without installing dependencies.
8. Finalize copy/adapt/archive/exclude/defer decisions and obtain product-owner approval before mass import.

## Dependency and implementation gate

AGENTS.md mandatory Phase 00–11 remains controlling. Current evidence does not support closing Phase 04, 06, 07, 08, 09, 10 or 11. Therefore P1 source governance may proceed as documentation/inventory, while P2–P11 product implementation must be sequenced behind the mandatory gate or an explicit written exception. Do not duplicate Phase 09 Chat, Tasks, Workflow, Wallet, Files, Memory, artifacts, event stream or API client. Before new memory/skill/browser/computer/media schema or code, reconcile existing source and Supabase schema; do not apply migrations in the current no-database-mutation instruction.

## Execution record

- Inspected repository branch and latest commit metadata through GitHub connector; current main head observed: `106357690c457a8f43dd7df8e028794c40799c50`.
- Read AGENTS.md, Master PRD section 37, Phase Tracker, FastAPI README, Worker README and typed frontend API client.
- Read the pinned source files listed above.
- No source code copied, no package installed, no scripts executed, no tests/build/lint/typecheck run, no provider request, no Supabase mutation/migration, no staging and no deployment.
