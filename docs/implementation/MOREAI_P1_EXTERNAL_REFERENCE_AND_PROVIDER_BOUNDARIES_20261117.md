# P1 External References, Runtime Dependencies & Third-Party Boundaries — 2026-11-17

Status: **STATIC REFERENCE REVIEW; PROVIDER/ASSET APPROVAL NOT GRANTED**.

## External services and runtime assumptions

| Source | Observed external dependency/reference | What the source expects | MoreAI decision |
|---|---|---|---|
| Scenario Skills | Scenario MCP `https://mcp.scenario.com/mcp`, Scenario app/API, OAuth or API key | Image/video/audio/texture/skybox/3D generation and model workflows through Scenario account and MCP; some expert skills require installed Blender/Maya/Unreal/Unity/Godot/Roblox/ZBrush | Skill text may be reviewed/imported only through existing Skill Registry. No MCP connection, API key, OAuth grant, provider invocation or DCC execution is authorized by source inventory. Add provider adapters only after provider approval, credentials, pricing, quota, entitlement, safety and artifact contracts exist. |
| Motion Skills aggregator | iArt MCP `https://app.iart.ai/api/mcp`, iArt docs/pricing | Remote hosted service accepts prompts/files and returns rendered video/share URL; README describes beta and paid plans | External provider, not open-source runtime. Do not connect or send user data without explicit provider/product approval and a dedicated adapter, billing, privacy and security review. |
| Motion talking-head pack | `@fal-ai/client` and `@napi-rs/canvas` in `skills/talking-head` lockfile | Uses Fal.ai client for AI presenter/video generation and native canvas renderer | Do not treat MIT skill code as a Fal.ai license or provider entitlement. Credentials, model pricing, input policy, metering, artifact storage and user consent remain separate gates. |
| Visual Skills | References image/video model syntax and model-selection documentation; skill returns prompts | Prompt-authoring and film-direction knowledge, not a hosted image/video generator | Adapt as untrusted procedural guidance only. Generation must go through MoreAI's approved provider/model router and durable Agent Run path. |
| OpenFuse | Google OAuth / Gmail / Calendar integration code; browser/computer runtime services | OAuth state/PKCE, encrypted credentials, Gmail send and Calendar create/update/delete actions, isolated browser/computer workers | Adapt relevant connection/session/action semantics into FastAPI, Connections Center and worker. Require tenant-bound OAuth, least privilege, explicit confirmation for write actions, immutable action receipts and idempotency. Do not run OpenFuse as a second business runtime. |
| OpenManusWeb | Python agent tools, browser-use, Playwright, search and web dependencies | Full backend/agent runtime capabilities, including browser/network/file tools | Keep the complete pinned snapshot pristine; production adaptations remain in OpenManus/MoreAI worker behind SSRF, approval, sandbox, quota and audit controls. |

## Nested license evidence

- Scenario Skills root `LICENSE`: MIT, Scenario Inc. (2026).
- Scenario Skills nested `.agents/skills/skill-creator/LICENSE.txt`: Apache License 2.0. This belongs to an internal repository-maintenance/skill-authoring entrypoint, not one of the 172 product skill entrypoints. Keep that internal tree archive-only and preserve the Apache notice if retained/copied.
- Visual Skills root `LICENSE`: CC BY 4.0; root `NOTICE` requires Serge Shima attribution and describes methods adapted after studying `agentara/skills` (MIT). Existing asset-rights review already defers 13 third-party provider logo SVGs and holds three visual assets pending provenance.
- Eighteen Motion child packs expose identical MIT root license blob/content. The nineteenth, `generative-illustration-skills`, has no root license and remains blocked.
- OpenFuse and OpenManusWeb root licenses are MIT. Scenario root MIT does not erase the nested Apache scope.

## Attribution, marks and assets

- Do not bundle provider logos from Visual Skills as MoreAI provider marks. CC BY 4.0 does not grant trademark rights.
- Do not reuse demo media/showcases as customer-generated assets or training data without separate asset provenance and rights review.
- Skill source files are untrusted instructions. They cannot grant permissions, override the model router, invoke external providers directly, bypass confirmation, or authorize shell/DCC execution.
- Keep all external URLs, package references, model identifiers and provider-specific instructions in the package provenance record. Do not silently convert provider examples into active tools.

## Required before provider activation

1. Product-owner approval for each provider and data-processing purpose.
2. Legal/privacy review of terms, retention, region, content rights and subprocessor terms.
3. Server-only credential storage and rotation; no browser-side API keys.
4. FastAPI adapter with tenant identity, allowlisted capabilities, request idempotency, approval for high-impact actions, durable task receipts and safe error mapping.
5. Model/provider routing with versioned pricing, quotas, entitlements, credit reservation/settlement and usage records.
6. Private artifact persistence, MIME/content validation, malware scan where applicable, signed owner-scoped downloads and retention/deletion.
7. Worker isolation, resource limits, egress controls and operational readiness.
8. Phase 10 authenticated E2E and Phase 11 release acceptance before activation.

No external provider was connected or called. No credentials, OAuth grants, scripts, DCC applications, packages or runtime services were installed or executed.
