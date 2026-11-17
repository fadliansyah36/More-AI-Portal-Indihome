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

## Recursive license/NOTICE filename re-scan — 2026-11-17 continuation

A second path-level scan was performed against the captured recursive tree manifests (the five primary trees plus both 19-pack Motion child manifests). The filename patterns included `LICENSE`, `LICENCE`, `COPYING`, `NOTICE`, `COPYRIGHT` and common extension variants. Every returned license-like file was fetched by immutable Git blob SHA and its content inspected.

### Primary source trees

| Repository | Path | Git blob SHA | Content-level finding |
|---|---|---|---|
| OpenManusWeb | `LICENSE` | `db2216e1a5bfd392213f57a257930e9b2dcca684` | MIT, copyright 2025 manna_and_poem |
| OpenFuse | `LICENSE` | `0e1238724a08528992a39ef43c63f899432a282c` | MIT, copyright 2026 OpenFuse contributors |
| Visual Skills | `LICENSE` | `da6ab6cc8f333d7e89a99812866df8f24374d47c` | CC BY 4.0 full license text |
| Visual Skills | `NOTICE` | `ec40c203365e6b3747c2e711e77e8ab327f98e44` | Serge Shima attribution + agentara/skills method acknowledgment |
| Scenario Skills | `LICENSE` | `05676553d9d10a0effff673b507b4fcfed652c17` | MIT, copyright 2026 Scenario Inc. |
| Scenario Skills | `.agents/skills/skill-creator/LICENSE.txt` | `4f881c52d1f72f4cfb720e339e2d35c3058d01a9` | Apache License 2.0; scoped to nested internal skill-creator tree |
| Motion Skills root | `LICENSE` | `a61b911146037f2ef312f67e9b45de6c99b7f870` | MIT, copyright 2026 iart.ai |

### Motion child packs

The two child-pack manifests were re-parsed for every license-like path. Exactly 18 of 19 child repositories contain a root `LICENSE`; all 18 point to the same Git blob SHA `a61b911146037f2ef312f67e9b45de6c99b7f870` (1,064 bytes), whose content is MIT, copyright 2026 iart.ai. The missing-license pack is `generative-illustration-skills`; it remains blocked. The 18 repository-specific source commit/path records and identical raw SHA-256 are already listed in `MOREAI_P1_RAW_SHA256_MANIFEST_20261117.csv`.

### Scope and limitations

- This re-scan establishes the set of license-like filenames present in the captured recursive source trees; it does not establish that every code/media/font/model asset is original or covered by the root license.
- A path scan cannot discover license text embedded in source headers, package metadata, copied snippets, binary/media metadata, external downloads or links. Those require file-content and asset provenance review.
- Scenario's nested Apache-2.0 notice must remain separately attributed; root MIT is not a blanket override.
- Visual Skills CC BY 4.0 and NOTICE requirements remain mandatory for any adapted material; the 13 deferred provider-logo assets and three pending-provenance visuals remain excluded from approval.
- No file has been promoted from preliminary disposition to final approval by this scan. P1 remains open.

## Exact-version npm registry metadata pass — 2026-11-17

The two pinned pnpm lockfiles contain 1,808 unique exact package coordinates. Exact-version npm registry metadata was retrieved for all 1,808; all requests returned HTTP 200. 1,797 returned a non-empty license field. Eleven returned no license field and remain NOASSERTION; one additional raw license string, `CC BY-SA 4.0`, is not an SPDX identifier/expression and remains manual-review-required.

See `MOREAI_P1_REGISTRY_LICENSE_REVIEW_REQUIRED_20261117.csv` for the 12 records requiring further evidence and `MOREAI_P1_NORMALIZED_PNPM_GRAPH_AND_REGISTRY_LICENSES_20261117.md` for aggregate distributions.

Registry metadata does not prove the package tarball's actual license notices, source-header rights, bundled media/font rights, or vulnerability posture. No package tarball was unpacked and no legal clearance is claimed. P1 remains OPEN.


## Raw SHA-256 of root and nested source notices — 2026-11-17

A raw-byte hash pass has now been completed for all 25 root/nested license and notice paths in the pinned upstream trees. The paths resolve to seven unique Git blob objects; each row records raw byte size, Git blob SHA and raw SHA-256 in MOREAI_P1_LICENSE_NOTICE_SHA256_20261117.csv.

Observed scope: 22 MIT notice paths (including the 18 eligible Motion pack LICENSE files), one Visual Skills CC BY 4.0 LICENSE, one Visual Skills attribution NOTICE, and one nested Scenario skill-creator Apache-2.0 LICENSE.txt. All 25 hash rows are marked verified.

The 229 selected skill entrypoints map to 1,923 files. Raw SHA-256 for those payload files remains pending; the separate license-notice hash pass must not be misrepresented as payload-wide hash coverage. The recursive binary-safe auditor is committed but has not been run.
