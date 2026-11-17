# P1 Binary & Font Asset Review — 2026-11-17

Status: **HASH / FILE-SCOPE VERIFIED; VISUAL, METADATA AND FINAL LICENSE ACCEPTANCE PARTIAL.**

Source: `docs/implementation/p1-skill-payload-evidence/skill-payload-file-audit.csv`
Pinned source: Scenario Skills `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
All listed raw SHA-256 values, expected byte sizes and Git blob SHA-1 values match the pinned source in the committed audit CSV.

## Asset inventory

| File | Bytes | SHA-256 | Review / disposition |
|---|---:|---|---|
| `skills/game-engines/unity/scenario-unity-web/scripts/WebRuntime/WebGLTemplates/AgentWeb/thumbnail.png` | 1,068 | `534e8493f0f207a0e4eb216cea42b588ad576da0bf08fb544c83ee3e26d27940` | Template preview thumbnail; archive-only, not a runtime asset |
| `skills/scenario-kinetic-film/assets/examples/tour/logo.svg` | 486 | `c134c3271d2ac20a84ae934620883906462f66f30257bc98fdd352e8bc28a7ed` | Source says placeholder mark and “Replace with your logo”; archive-only |
| `tests/scenario-admin-analytics/evidence/screenshots/dashboard-overview.png` | 113,901 | `7623a48db089b1a2bd03e32174bf475d915b368858e7fa633877d535486f2c0e` | Test/evidence screenshot; archive-only |
| `tests/scenario-admin-analytics/evidence/screenshots/dashboard-filtered.png` | 229,282 | `a8b160fd076c5ede63f7219b684891b9f7e0d2e181fadf94ee47d17755182151` | Test/evidence screenshot; archive-only |
| `tests/scenario-admin-analytics/evidence/screenshots/dashboard-mobile.png` | 55,883 | `6aa814092a12eede4520fe4b80ba549c88342b2840397031d2d9fc35d354646d` | Test/evidence screenshot; archive-only |
| `tests/scenario-admin-analytics/evidence/example/report.pdf` | 7,687 | `31725864a13b3ce6157c74d0348c5340b047ece0a02cb8fe508284741219c58d` | Test/evidence report; archive-only |
| `tests/scenario-admin-analytics/evidence/screenshots/report-page-1.png` | 90,525 | `b1b70338e877e042f2cf069be52725cfc8dca7ec57a4b9dc9c6cb82cd3518b28` | Test/evidence screenshot; archive-only |
| `tests/scenario-admin-analytics/evidence/screenshots/report-page-2.png` | 146,522 | `e80e894652a69b81099faf2ff00209023dead63180ad1a33fd6d744f3799420f` | Test/evidence screenshot; archive-only |
| `tests/scenario-admin-analytics/evidence/screenshots/report-page-3.png` | 83,767 | `fa7c5e169efcf4e9b6072daab63b787a3adaacabd8d0c3e295db80273a892985` | Test/evidence screenshot; archive-only |
| `tests/scenario-admin-analytics/evidence/screenshots/report-page-4.png` | 79,350 | `6d672d2a02eaff68b02ab784f1103a310ca53df0904d0041f43d1350d54483f3` | Test/evidence screenshot; archive-only |
| `skills/scenario-playable-ads/assets/fonts/fredoka/Fredoka-Bold.woff2` | 14,844 | `be5bf1116137720ddd047885c22d7542c9ee861b2d1e466f8737b849508cbad5` | SIL OFL 1.1 file present; defer final use pending font metadata / reserved-name review |
| `skills/scenario-playable-ads/assets/fonts/lilita-one/LilitaOne-Regular.woff2` | 10,672 | `d2575d4fa3632580aafcbcdf6978b3b57e144b90cf5bd9c2c98194f28b869704` | SIL OFL 1.1 file present; Lilita One reserved font name stated; defer final use pending metadata review |
| `skills/scenario-playable-ads/assets/fonts/orbitron/Orbitron-ExtraBold.woff2` | 6,716 | `90423db4185eeab03301ed16d0f0f30557540ff89b0b0c8562515db7024186d3` | SIL OFL 1.1 file present; defer final use pending font metadata review |
| `skills/scenario-playable-ads/assets/fonts/rajdhani/Rajdhani-Bold.woff2` | 20,888 | `ca0b50f1e654049f21b45e2605fd6a412f2b8fa061c129a029d241b5e275c605` | SIL OFL 1.1 file present; defer final use pending font metadata review |

## Font notice inspection

Four adjacent `OFL.txt` files were read from the same pinned Scenario commit:

- Fredoka: copyright 2016 The Fredoka Project Authors; SIL Open Font License 1.1.
- Lilita One: copyright 2011 Juan Montoreano; SIL Open Font License 1.1; Reserved Font Name “Lilita One”.
- Orbitron: copyright 2018 The Orbitron Project Authors; SIL Open Font License 1.1.
- Rajdhani: copyright 2014 Indian Type Foundry; SIL Open Font License 1.1.

The license texts establish the declared font license and attribution scope, not an independent verification of the WOFF2 internal metadata or all font build provenance. Preserve each font's own OFL notice; do not collapse these fonts under the Scenario root MIT notice.

## Review limitations

- The binary payloads were hash-verified by the committed workflow, but the PNG/PDF pixel/page content and WOFF2 internal metadata were not successfully rendered/extracted in this review.
- The logo SVG source was read as text and explicitly identifies itself as a placeholder.
- Test screenshots and the sample report are evidence fixtures, not product assets; they must not be promoted to runtime UI or seeded into production.
- No file was executed, installed, embedded, rendered by an app, or uploaded to Supabase.

## Decision

- 10 media/binary rows: `ARCHIVE_ONLY` (examples, preview or test/evidence fixtures).
- 4 font rows: `DEFER` until internal metadata, exact notice scope and intended redistribution/embedding treatment are recorded. Their OFL notices are present and must be preserved.
- All 14 remain excluded from production skill installation at this point.

**This asset review does not close P1.**
