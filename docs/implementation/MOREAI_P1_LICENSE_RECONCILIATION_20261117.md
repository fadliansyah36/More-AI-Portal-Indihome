# MoreAI P1 License Reconciliation — 2026-11-17

Status: **PARTIAL CONTENT REVIEW; NOT A LEGAL APPROVAL OR P1 CLOSURE**.

## Confirmed pinned root notices

| Source | Pinned revision | Observed license / notice | Required treatment |
|---|---|---|---|
| OpenManusWeb | `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` | MIT, copyright 2025 manna_and_poem | Preserve copyright + MIT text in pristine vendor snapshot and substantial copied portions |
| OpenFuse | `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc` | MIT, copyright 2026 OpenFuse contributors | Preserve notice and inspect nested assets/dependencies |
| Visual Skills | `61a60d317f0fa0c3dc98902e58a7cb178838ae3f` | NOTICE declares CC BY 4.0, copyright 2026 Serge Shima; credits agentara/skills methods adapted/re-written under MIT | Attribution is mandatory; preserve author/source attribution and third-party acknowledgment. Verify the referenced LICENSE file and every referenced external work before copying |
| Scenario Skills | `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | Root MIT, copyright 2026 Scenario Inc. | Preserve MIT notice; inspect per-skill nested notices and third-party assets |
| Motion Skills root | `9b9ce041932da787cc856d4cdf23afb6cd13d4bf` | MIT, copyright 2026 iart.ai | Applies to the root repository only; do not infer it covers separately hosted packs |

## Motion Skills 19-pack license pass

At the pinned commits listed in the recursive manifests, raw root `LICENSE` content was retrieved for 18 packs. All 18 returned the MIT License with copyright 2026 iart.ai. The one exception is `generative-illustration-skills`: its recursive tree contains 7 files and 3 directories but no root `LICENSE`, `LICENCE`, `COPYING` or `NOTICE` file. It remains **BLOCKED / DO NOT COPY OR ADAPT** until a valid license or explicit permission is obtained.

| Pack | Observed root license |
|---|---|
| tiktok-video-skills | MIT — iart.ai (2026) |
| text-message-video-skills | MIT — iart.ai (2026) |
| youtube-video-skills | MIT — iart.ai (2026) |
| ecommerce-video-skills | MIT — iart.ai (2026) |
| ad-video-skills | MIT — iart.ai (2026) |
| data-animation-skills | MIT — iart.ai (2026) |
| explainer-video-skills | MIT — iart.ai (2026) |
| map-animation-skills | MIT — iart.ai (2026) |
| web-animation-skills | MIT — iart.ai (2026) |
| motion-design-skills | MIT — iart.ai (2026) |
| kinetic-typography-skills | MIT — iart.ai (2026) |
| freelance-motion-skills | MIT — iart.ai (2026) |
| webgl-animation-skills | MIT — iart.ai (2026) |
| manim-skills | MIT — iart.ai (2026) |
| javascript-animation-skills | MIT — iart.ai (2026) |
| lower-thirds-skills | MIT — iart.ai (2026) |
| b-roll-skills | MIT — iart.ai (2026) |
| talking-head-skills | MIT — iart.ai (2026) |
| generative-illustration-skills | **No root license found — blocked** |

## Important limits

1. This is a review of root license/notice files only. It does not yet reconcile nested LICENSE/NOTICE files, fonts, stock imagery, video/audio assets, code snippets, external references or per-file copyright provenance.
2. Visual Skills NOTICE states CC BY 4.0 and requires attribution to Serge Shima; it also credits methods studied from `agentara/skills` (MIT). Do not flatten these into a single generic MIT label.
3. Scenario Skills tree contains at least one nested `.agents/skills/skill-creator/LICENSE.txt`; its scope and corresponding content need a dedicated attribution review. A nested license can govern only the nested work, not the entire parent repository.
4. Motion Skills README mentions the iArt remote MCP beta service. This is an external hosted provider, not licensed source code. No iArt API/MCP connection, key, provider call, subscription or user data transfer is approved by this inventory.
5. A license file being present does not establish dependency license compatibility or vulnerability status.

## Remaining P1 legal/SBOM/integrity work

- Inspect all nested license and attribution files in all 24 source trees.
- Inspect third-party content declarations and references recursively, including Visual Skills references and Scenario/Motion per-skill resources.
- Parse dependency manifests and lockfiles without installing packages; create exact-version SBOM and reconcile transitive license expressions, `NOASSERTION` and known vulnerabilities.
- Retrieve raw bytes and calculate SHA-256 for each selected source file. Keep Git blob SHA and SHA-256 in separate columns.
- Finalize copy/adapt/archive-only/exclude/defer decisions per file and selected capability.

No code was imported or executed. No tests, builds, migrations, Supabase writes, staging or deployment were performed.
