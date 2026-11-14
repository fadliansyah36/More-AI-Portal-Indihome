# P1 Visual Skills Asset Rights & Scenario Recursive Inventory — 2026-11-14

## Pinned sources and method

- Visual Skills: `smixs/visual-skills@61a60d317f0fa0c3dc98902e58a7cb178838ae3f`.
- Scenario Skills: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`.
- Both Git recursive tree responses were complete (`truncated=false`). This report records exact tree-level evidence and source license text inspected; it does not claim every skill body/reference/script was read or every asset binary was independently verified.
- No source code/assets were copied into the MoreAI product in this increment.

## Visual Skills — exact inventory

Pinned recursive tree: 60 blobs, 676,353 bytes total. Asset directory contains 16 blobs:

| Asset path | Blob SHA | Bytes | Rights disposition |
|---|---|---:|---|
| `assets/dramaturgy-banner.ru.svg` | `684436c9b83692c91a18e509493b33c935d6c508` | 4,744 | CC BY 4.0 repository license is present; individual creator/provenance not independently evidenced — hold pending rights verification |
| `assets/dramaturgy-banner.svg` | `fd551ecb196897303e92cf06cf0121302b97900b` | 4,504 | CC BY 4.0 repository license is present; individual creator/provenance not independently evidenced — hold pending rights verification |
| `assets/hero.webp` | `a0f428d40903c954ed5394fd98c12a9b85fba23c` | 147,000 | CC BY 4.0 repository license is present; underlying image/model/stock provenance not independently evidenced — hold pending rights verification |
| `assets/logos/bytedance-color.svg` | `ded0e4de8e06d9d00ee80912d64310fcaa34c741` | 896 | Third-party mark; CC BY does not grant trademark rights — exclude/defer pending brand permission |
| `assets/logos/deepmind-color.svg` | `e185ae3a5e77c5e73d3c32dcc11f011ac97f82e0` | 763 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/kling-color.svg` | `e07fb600c7db3971a9a12fd6191c444d55c7475e` | 2,188 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/luma-color-dark.svg` | `fe7725bbfb7b9ef6a939ff23ad2061f41c8f0db2` | 1,765 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/luma-color.svg` | `9331c81c48b46909d41cc2d7bc0d4ac608f9ec74` | 1,762 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/nanobanana-color.svg` | `9990ab2938bd9450eb7cc36bbb167a962004cc36` | 1,323 | Third-party mark/product branding; trademark permission not evidenced — exclude/defer |
| `assets/logos/openai-dark.svg` | `a859049ade16939db83d5a234e65bdf11a4d02dd` | 1,625 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/openai.svg` | `8a274245edd215d520663eebe22935abfc48226d` | 1,625 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/pika-dark.svg` | `8bd195a53f494b8dbee3627b723f94c544a517f1` | 435 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/pika.svg` | `b66b281be43e417811be8392417c5003514898b1` | 435 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/runway-dark.svg` | `f34d52da266b1565c6ac340394ac4ababa9c05a3` | 690 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/runway.svg` | `d18abcf841256f804fe8ab88daa70bf0ffc2f732` | 690 | Third-party mark; trademark permission not evidenced — exclude/defer |
| `assets/logos/sora-color.svg` | `47135660498fceceef0af194fa201e213602bdcc` | 4,510 | Third-party mark/product branding; trademark permission not evidenced — exclude/defer |

### License and attribution evidence

- Root `LICENSE` is Creative Commons Attribution 4.0 International (CC BY 4.0).
- Root `NOTICE` names Serge Shima, supplies source/author URLs and requires attribution for use/copy/derivatives. Preserve author, source link, license link, and modification indication in any reuse.
- NOTICE states selected methods were adapted (rewritten, not copied) after studying `agentara/skills` under MIT, with specified reference topics. This is provenance context, not permission to copy that upstream source. Any independently sourced MIT material must retain its own notice.
- CC BY 4.0 does not license trademark rights. The 13 provider logo SVGs must not be treated as cleared merely because they sit in a CC BY repository. Use text-only provider labels or separately licensed/official brand assets only after permission and usage terms are documented.
- The two banners and hero image remain on hold until the author confirms that they are original/licensable and any embedded third-party material is cleared. Do not publish or redistribute them based only on the root license.

### Decision

**Visual Skills asset rights are NOT CLOSED.** Skill text may be evaluated for CC BY reuse with full attribution and change notices, but the 16 asset paths do not yet have a fully evidenced per-asset rights decision. The 13 third-party brand marks are explicitly deferred; three visual assets require creator/source confirmation.

## Scenario Skills — recursive tree reconciliation

Pinned recursive tree: 2,114 blobs, 62,154,351 bytes, `truncated=false`.

| Inventory dimension | Count |
|---|---:|
| All repository blob paths | 2,114 |
| Files under `skills/` | 1,664 |
| `SKILL.md` entrypoints found recursively | 172 |
| Reference files under `references/` | 519 |
| Script files under `scripts/` | 898 |
| Assets under `assets/` | 54 |
| Test files under `tests/` or `test/` within skills | 20 |
| Root/nested license files detected by filename | 2 |

The prior working target of **179 Scenario entrypoints** is reconciled by the pinned tree: **172 product skill entrypoints** under `skills/` plus **7 internal repository-maintenance/skill-authoring entrypoints** under `.agents/skills/`. Therefore the 179 aggregate includes 7 internal maintainer skills and must not be mistaken for 179 product-facing Scenario skills. The 7 internal entrypoints are archive-only; the 172 product skills remain in scope for capability review.

The repository tree also contains extensive non-Markdown assets (including Godot, Unity, Unreal, Roblox and DCC scripts/shaders/projects), sample media, PDFs, and nested skill materials. A filename-only license scan found root `LICENSE` and `.agents/skills/skill-creator/LICENSE.txt`; this does not prove that all binary/media/code assets are covered by those notices or that external dependencies embedded in examples have compatible licenses.

### Scenario review decision

**Scenario Skills are NOT CLOSED.** Tree enumeration is complete for the pinned commit. The 172 product entrypoint bodies and their 519 references, 898 scripts, 54 assets and 20 test files have not all received per-file content/provenance/license dispositions. The 7 internal maintainer entrypoints are archive-only. Do not copy wholesale or mark supporting files approved.

## P1 gate and next steps

- Visual Skills asset rights: OPEN.
- Scenario recursive content review: OPEN.
- Exact-version dependency licensing: unchanged; no package@version `NOASSERTION` coordinate is resolved by this report.
- OpenFuse complete path review: OPEN.
- Canonical manifest: do not remove `pending-content-review` without per-file evidence.
- P1 closure: NOT APPROVED.

Next: reconcile the historical 179 Scenario list to the pinned 172 entrypoints; then review each entrypoint and recursively follow its references/scripts/assets/tests/metadata and nested licenses, recording exact path, SHA, source/license evidence, destination/use decision and restrictions. Resolve Visual Skills' three image/banner provenance cases and obtain permission for provider marks or exclude them from reuse.
