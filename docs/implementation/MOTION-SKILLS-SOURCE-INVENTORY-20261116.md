# Motion Skills — source inventory and registry integration

Date: 2026-11-16  
Target branch: `main`  
Scope: source pinning, repository governance and customer Skill Registry discovery; no upstream source files are copied into the MoreAI vendor tree in this increment.

## Source structure finding

The supplied `iart-ai/motion-skills` repository is an index/curation repository, not the location of all 56 `SKILL.md` entrypoints. Its pinned `master` commit is `9b9ce041932da787cc856d4cdf23afb6cd13d4bf`; the recursive tree contains 12 tracked blobs, including README, MIT license, showcases and verification-tool documentation. Its README lists 19 independently maintained skill-pack repositories. Each pack must be pinned and governed separately; the aggregator README is not treated as an executable skill.

## Pinned skill-pack repositories

All 19 linked pack repositories were inspected on `main`. Their commit IDs equal the inspected tree IDs in this inventory. The recursive trees are complete (not truncated) and contain 56 `skills/*/SKILL.md` entrypoints in total.

| Pack repository | Pinned commit | Skill entrypoints | Root license |
|---|---|---:|---|
| `iart-ai/tiktok-video-skills` | `88e7152fc2710fa16852d013959cfd988a8adc8b` | 4 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/text-message-video-skills` | `10ae6bb32e89519c904b8f7950479ff655f839aa` | 1 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/youtube-video-skills` | `7838388571a3a6301bf5633e91941f9dfed0abfd` | 2 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/ecommerce-video-skills` | `a430fbbb7660783c421ad0a145bcc1c98d6f0b7b` | 3 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/ad-video-skills` | `cc8071678f4225ee7bdccc4506f2468722bb3515` | 3 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/data-animation-skills` | `6570c0c4fbc9daa8d7ac1f1163a890352344206b` | 3 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/explainer-video-skills` | `3c13a1bc360c08503f24f9c9a99fda6d3d35de56` | 5 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/map-animation-skills` | `c8ef8463f5a4a8aa35ff0c6c17f42e52bbf588a5` | 1 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/web-animation-skills` | `ed3a045192679b24d32090ee7a983871311ababd` | 9 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/motion-design-skills` | `b85e50c4cef5ff17aa2187a10d49d2dae9226c74` | 9 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/kinetic-typography-skills` | `2b79c81230c6647a344844f9ed53b6fa07f3f1f9` | 1 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/freelance-motion-skills` | `9f294eb6df73cde7e2dea235f42275df11a16466` | 5 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/webgl-animation-skills` | `0041933813688c357804f7b13dcb85095c5a3210` | 3 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/manim-skills` | `3e989cb044f6a6fed8c07b06dddade6e3463d7ac` | 1 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/generative-illustration-skills` | `e7d62437c875fc8ad5eff6e90fe0e25b30e43933` | 1 | Missing — NOASSERTION / blocked |
| `iart-ai/javascript-animation-skills` | `060f7467a6e5ae5b57c90c9cb1b3508c13b88e49` | 2 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/lower-thirds-skills` | `58d3623da95a2c97a4890a2d3f6d9d67e040b3d7` | 1 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/b-roll-skills` | `bcd56742a8a99edaa699a6f7bc5a45922a8ec567` | 1 | MIT — Copyright (c) 2026 iart.ai |
| `iart-ai/talking-head-skills` | `eac1f6b01467f6f95d8ab7602310ba0ff67ed91b` | 1 | MIT — Copyright (c) 2026 iart.ai |

The 18 pack repositories with a root LICENSE were inspected and identify MIT. `generative-illustration-skills` has no root LICENSE in the pinned tree and is intentionally recorded as `NOASSERTION`; it must remain unapproved and non-executable until the rights evidence is resolved. MIT at repository level is not blanket approval for nested third-party assets, scripts, generated media, model references or dependencies.

## Registry implementation

- Added all 19 pinned pack repositories to the server-side source allowlist used by the existing Skill Registry catalog and import endpoints.
- Customer catalog discovery now enumerates only `skills/*/SKILL.md` from the pinned Motion pack repositories; it does not treat aggregator README text, showcase media or shell verification scripts as skills.
- Import accepts only pinned `iart-ai/*` repositories and entrypoints under `skills/` ending in `SKILL.md`.
- Existing recursive ingestion remains bounded (40 files, 512 KiB per file, 5 MiB per skill), verifies Git blob SHA-1 and SHA-256, stores immutable source records through the existing transactional Supabase RPC, and does not grant execution permission.
- The existing OpenManus resolver, approval workflow, license/dependency evidence and fail-closed publication gates remain authoritative. No second runtime or database was introduced.

## Not yet complete

1. Full 56-skill recursive ingestion has not been executed; catalog availability does not mean packages have been imported.
2. Dependency graph parsing, SBOM closure, vulnerability scanning, nested license/asset provenance and human review remain required before publication.
3. Motion video generation providers, worker adapters, model pricing, quota/credit settlement and private artifact storage must be independently configured and verified. Skill content alone does not render or export a video.
4. The aggregator's verification scripts require local tools such as Playwright/Chromium and ffmpeg/ffprobe. They remain unexecuted and are not enabled as privileged MoreAI tools.
5. No tests, lint, typecheck, build, browser/API/worker runtime, provider calls, staging, migration apply or deployment were run, per product-owner instruction.

## Governance

- Source is fetched only from immutable commit pins through HTTPS GitHub API with redirects disabled.
- Source paths are restricted to the pack's `skills/` subtree and `SKILL.md` entrypoints.
- Source import does not grant permissions, publish a package or activate runtime execution.
- Copyright and license evidence must remain attached to each imported package.
- No secrets, generated runtime state or external provider credentials are copied.

## Next phase

Continue Phase 09 customer Skill Registry closure: finish the 56-entry catalog review, recursively ingest selected approved packages, complete dependency/license/asset evidence, then wire media skill selection through Agent Studio → Chat enqueue → durable OpenManus Agent Run → provider routing/metering → private artifact projection. Keep image/video generation unavailable until real provider, worker and billing readiness gates pass.
