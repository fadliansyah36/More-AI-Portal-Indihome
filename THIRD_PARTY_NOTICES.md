# Third-party source notices and attribution

This file records source-level licenses and attribution for the upstream repositories used or adapted by MoreAI. It does not certify third-party dependency, model, font, media, trademark or dataset rights beyond the specific evidence listed here.

## OpenManusWeb

- Source: https://github.com/YunQiAI/OpenManusWeb
- Pinned source: `dev_web_app` @ `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`
- License: MIT
- Copyright: Copyright (c) 2025 manna_and_poem
- Treatment: pristine source snapshot under `vendor/openmanusweb/`; adapted runtime code remains separate in MoreAI production modules.
- Preserve the upstream LICENSE and copyright notice with any redistributed copy.

## OpenFuse

- Source: https://github.com/CopilotKit/openfuse
- Pinned source: `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`
- License: MIT
- Copyright: Copyright (c) 2026 OpenFuse contributors
- Treatment: browser/session/event concepts are adapted into MoreAI's existing FastAPI, worker and sandbox boundary. OpenFuse is not deployed as a second app or Agent Runtime.
- Preserve the upstream LICENSE and copyright notice with any redistributed copy.

## Visual Skills

- Source: https://github.com/smixs/visual-skills
- Pinned source: `61a60d317f0fa0c3dc98902e58a7cb178838ae3f`
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Attribution: Serge Shima, https://github.com/smixs/visual-skills
- Additional NOTICE: acknowledges agentara/skills methods studied and rewritten under MIT; preserve the upstream NOTICE and attribution.
- Selected entrypoints: `image/SKILL.md` and `video/SKILL.md`.
- Treatment: source instructions are loaded as owner-installed, immutable skill snapshots and adapted to MoreAI's real `image_generate` / `video_generate` tool schemas. They do not install providers or assert upstream model availability.
- Attribution must accompany redistributed or adapted material.

## Scenario Skills

- Source: https://github.com/scenario-labs/skills
- Pinned source: `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
- License: MIT, Copyright (c) 2026 Scenario Inc.
- Nested notice: `.agents/skills/skill-creator/LICENSE.txt` is Apache-2.0 and remains separately scoped; do not treat root MIT as overriding nested work.
- Copy Engine source workflows selected: `skills/scenario-brand-kit/SKILL.md`, `skills/scenario-ad-variants/SKILL.md` and `skills/scenario-text-overlay/SKILL.md`.
- Treatment: their brand-specification, controlled-variant and exact text-overlay specification principles are adapted into the original MoreAI Copy Engine adapter. Scenario text-overlay's `chevron`, `Pillow` and Chromium rendering dependencies are not imported; MoreAI returns a text-overlay specification only. No Scenario MCP, model endpoint, remote asset service or code from the Scenario runtime is imported.

## Motion Skills

- Aggregator: https://github.com/iart-ai/motion-skills
- Aggregator pin: `e8ba1f4eb2bcca3d1639d7545b9cd2bcfe4a3c6f` (master)
- Aggregator license: MIT, Copyright (c) 2026 iart.ai
- Skill payloads: the 18 child packs with root MIT notices at their individually pinned commits recorded in `docs/implementation/MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_20261117.csv` and `MOREAI_P1_MOTION_SKILLS_19_PACKS_MANIFEST_PART2_20261117.csv`.
- Excluded pack: `iart-ai/generative-illustration-skills` has no resolved root license in the captured source tree and remains blocked from import/adaptation.
- Treatment: curated motion skill instructions are resolved through the existing Skill Registry and translated to existing MoreAI media tools. Remotion, ffmpeg, fonts, codecs, MCP services, external model APIs and credentials are not implicitly provisioned.

## MoreAI Copy Engine

- Implementation: `engine/tools/copy_engine.py`
- Registry: `engine/tools/catalog.py`
- Runtime: `engine/agents/durable_tool_runtime.py`
- Source workflow attribution: Scenario Skills `scenario-brand-kit`, `scenario-ad-variants` and `scenario-text-overlay` (MIT, pinned commit above).
- Implementation status: original MoreAI adapter; invokes only the existing metered LLM gateway and is callable as `copy_engine_generate` through the canonical OpenManus tool loop.
- No Scenario MCP or external copywriting SaaS is called. User-provided facts are the only allowed factual basis for claims.

## Scope disclaimer

Repository-level licenses do not automatically clear every nested dependency, media asset, font, logo, model, trademark, copied snippet or external URL. Per-source SBOM, nested NOTICE and selected-file provenance registers remain authoritative for those narrower decisions. Unlicensed or unresolved source payloads must remain blocked.
