# P1 Manual Reference Triage — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Source basis: committed `p1-skill-payload-evidence/skill-reference-audit.csv` plus immutable source trees at their pinned commits.
Status: **REFERENCE TRIAGE COMPLETED FOR THE 148 PARSER CANDIDATES; FULL SKILL CONTENT / PER-FILE P1 REVIEW REMAINS OPEN.**

## Method and boundaries

- Re-read the current `AGENTS.md` before the review.
- Compared every parser candidate against the committed recursive source-tree manifest, preserving repository and commit scope.
- Manually inspected the affected Scenario/Motion reference documents, the relevant engine entrypoints, and both scaffold scripts.
- Verified all fragment targets against Markdown heading slugs.
- Read-only source inspection only. No shell command, script, package, build, test, provider, staging, deployment or Supabase operation was run.

## Reconciliation of the 148 parser candidates

The current committed reference CSV contains **148** rows marked `NOT_FOUND_IN_PINNED_TREE`. They are not 148 missing source files.

| Classification | Count | Review result |
|---|---:|---|
| Markdown heading fragments | 49 | **49/49 matched** to headings in the six source Markdown documents; false positives because fragments are not file paths |
| Existing directory targets | 78 | **78/78 resolved** to directory entries in the pinned recursive tree; parser expected file blobs |
| Contextual/runtime/generated references | 21 | Manually reviewed and classified below |
| **Total** | **148** | No unclassified candidate remains in this triage |

This count-based reconciliation supersedes the earlier shorthand “25 unresolved” for this exact committed CSV. The earlier number was a coarse residual estimate; it must not be repeated as the current exact row count.

## Contextual/runtime/generated references (21 rows)

| Reference(s) | Source context | Manual finding | Disposition |
|---|---|---|---|
| `value` | Unity architecture procedures | Code/data field token inside a sample, not a path | False-positive parser token; no source file required |
| `data:,` | Unity WebGL template HTML | Valid empty data URI, not a repository file | Runtime literal; no source file required |
| `./spec.js` | Kinetic Film engine `main.js` | Project-specific spec is supplied by the scaffold from the selected example | Generated project file; scaffold-dependent |
| Three `./blocks.js` imports | Kinetic Film example specs | Scaffold copies engine `blocks.js` into each new film project; example folder itself is not the final project root | Generated project layout; scaffold-dependent |
| `/engine/main.js` | Kinetic Music Video `index.html` | Root-relative URL for the scaffolded project server layout, not a repository-relative path | Runtime mount path; requires correct project serving root |
| `./timeline.js`, `../timeline.js` | Kinetic Music Video engine and HUD | `scaffold.sh` creates `engine/timeline.js` from `assets/timeline.template.js` | Generated project file; scaffold-dependent |
| `mraid.js` | Playable Ads network guide | Mobile ad network-provided MRAID runtime, not vendored source | External platform dependency; must be supplied by the target ad network and never fetched from an untrusted URL |
| Four `../../` links | TikTok skill README files | Navigation links to the repository root; root exists in the pinned tree | Valid directory navigation |
| `logo.png`, `dana.jpg` | YouTube intro/outro and testimonial examples | Illustrative assets referenced by example snippets; not mandatory source payloads | Optional example inputs; do not treat as verified production assets |
| `/about` | Web animation skill | Example application route, not a source file | App-specific route; adapt only if MoreAI has an approved matching route |
| `clip.mov`, `clip.webm` | After Effects export guide | Generic output filename/format examples | Generated user output; no source asset required |
| `lower-third-safari.mov`, `lower-third.webm` | Lower-thirds delivery guide | Output files produced by the documented render/encode workflow | Generated user output; no source asset required |

### Scaffold evidence

- Kinetic Film `SKILL.md` states `scripts/new_film.sh` scaffolds a film folder and copies the engine files; its script header explicitly says it creates the project engine and example `spec.js`. The script is inspected as text only and was not executed.
- Kinetic Music Video `SKILL.md` and `scripts/scaffold.sh` state that the engine is copied into the project and `engine/timeline.js` is created from `assets/timeline.template.js`. The script is inspected as text only and was not executed.
- Therefore the engine references above are scaffold-time generated dependencies, not proof that those files exist in the pristine source tree. Any MoreAI adapter must reproduce this layout explicitly and must not execute these upstream shell scripts directly on the host.

## Content review sample — selected skill entrypoints

A static content review was performed on 16 entrypoints (2 Visual Skills and 14 Scenario Skills from the beginning of the pinned entrypoint register). This is a sample only, not a full review of all 229.

- No literal secret value was observed in the sample.
- Shell/process-oriented guidance was flagged in Blender export and hair workflows; those commands must remain unexecutable from the customer/browser process and require a reviewed sandbox/worker adapter.
- Credential/source references occur in content guidance; they are not credentials themselves. Any credential access must remain through server-side secret references and explicit consent.
- No dynamic-code pattern such as `eval()` or `new Function()` was identified in the reviewed sample.
- Keyword flags for URLs/network are not a vulnerability finding; the instructions and referenced destinations still need a full per-file review.

## Decisions from this triage

1. The 49 fragment and 78 directory rows can be marked `RESOLVED_CONTEXTUAL_REFERENCE` in the reference review ledger, while preserving the original machine CSV unchanged as raw audit evidence.
2. The 21 contextual rows are not copy approvals. Their row-level dispositions are: generated/scaffold dependency, external runtime, optional illustrative input, app route, or output example.
3. Kinetic Film and Kinetic Music Video remain **DEFER / ADAPT ONLY AFTER A REVIEWED SCAFFOLD ADAPTER**. Their upstream shell scripts are not approved for direct execution.
4. Playable Ads MRAID integration remains **DEFER** until an approved network adapter supplies the official SDK/runtime under an allowlisted origin.
5. This reference triage does not grant license clearance, security clearance, binary/font provenance, or final product-skill ingestion approval.

## Remaining P1 gates

- Review all 229 entrypoints, not just the 16-entrypoint sample.
- Review all 875 executable-source and 69 configuration/schema payload files for safety, provenance, license and target mapping.
- Inspect all 10 media/binary and 4 font assets, including embedded metadata and origin/license scope.
- Resolve the 16 extra npm PURLs pending source attribution, inspect package tarball notices for the 12 registry-license review records, reconcile vulnerability evidence, and resolve OpenManusWeb ranged Python dependencies.
- Replace the preliminary disposition of all 1,941 payload files with explicit final per-file decisions and evidence.
- Product-owner acceptance is still required before P1 closure and P2 ADR acceptance.

**Conclusion: the 148 parser reference candidates are triaged; P1 is not closed.**


## Entrypoint sample register — exact 16 reviewed

| Source | Entrypoint | Static review note |
|---|---|---|
| Visual Skills | `image/SKILL.md` | Prompt/workflow guidance; external reference URLs present |
| Visual Skills | `video/SKILL.md` | Prompt/workflow guidance; external reference URLs present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-animation/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-blockout/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-expert/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-export/SKILL.md` | Contains explicit `blender -b ... -P bx_export.py` command guidance; sandbox-only |
| Scenario Skills | `skills/dcc/blender/scenario-blender-geometry-nodes/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-grease-pencil/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-hair/SKILL.md` | Python/script workflow guidance; sandbox-only |
| Scenario Skills | `skills/dcc/blender/scenario-blender-hard-surface/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-lighting-rendering/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-previs-storyboard/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-retopology/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-rigging/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-sculpting/SKILL.md` | Blender workflow; external references present |
| Scenario Skills | `skills/dcc/blender/scenario-blender-texturing-shading/SKILL.md` | Mentions credential provenance in a reference checklist; no literal credential value observed; credential handling remains server-side and consent-gated |

The static scan's URL/network keyword hits are not automatically findings of unsafe behavior; they include ordinary upstream documentation and source links. The two shell/process-oriented Blender workflows are not approved for direct customer/browser execution. The entrypoint sample remains 16/229, so no blanket safety approval is inferred.


## Entrypoint review expansion — 24/229

The read-only content review has expanded from 16 to **24 of 229** selected entrypoints. The next eight reviewed files are:

- `skills/dcc/blender/scenario-blender-uv-baking/SKILL.md`
- `skills/dcc/maya/scenario-maya-animation/SKILL.md`
- `skills/dcc/maya/scenario-maya-deformation/SKILL.md`
- `skills/dcc/maya/scenario-maya-expert/SKILL.md`
- `skills/dcc/maya/scenario-maya-fx/SKILL.md`
- `skills/dcc/maya/scenario-maya-groom/SKILL.md`
- `skills/dcc/maya/scenario-maya-lighting-rendering/SKILL.md`
- `skills/dcc/maya/scenario-maya-lookdev/SKILL.md`

Static keyword flags were manually contextualized for Maya animation and FX: the term “credential” appears in a reference checklist requiring source/credential/URL provenance, not as a literal secret or credential value. Shell/process flags in Maya deformation/expert/lighting/lookdev require sandbox-only review; they are not evidence of malicious behavior. The scan did not identify `eval()` or `new Function()` patterns in this 24-entrypoint sample. All DCC command/script guidance remains unavailable to the customer/browser process until the isolated worker boundary is approved and enforced.

**Review coverage: 24/229 entrypoints (10.5%).** Remaining 205 entrypoints and all referenced executable/configuration files still require review; no blanket safety or license approval is inferred.


## Entrypoint review expansion — 32/229

The content review has expanded to **32/229** entrypoints. The eight additional files are:

- `skills/dcc/maya/scenario-maya-modeling/SKILL.md`
- `skills/dcc/maya/scenario-maya-pipeline-scripting/SKILL.md`
- `skills/dcc/maya/scenario-maya-retopology-uv/SKILL.md`
- `skills/dcc/maya/scenario-maya-rigging/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-automation/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-character-creature/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-expert/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-hard-surface/SKILL.md`

Manual contextualization: “verify token” in a version identifier is not a credential; “credential” in a source-provenance checklist is a documentation requirement, not a secret value. ZBrush automation includes a `ZBrush -script` process path and remains sandbox-only. Shell/process keyword flags in DCC instructions are expected tool-operation guidance, not evidence of malicious code. No `eval()` or `new Function()` pattern was found in this 32-entrypoint sample.

**Review coverage: 32/229 entrypoints (14.0%).** Remaining 197 entrypoints and all referenced scripts/configuration continue to require review. No safety approval is inferred for the unreviewed content.


## Entrypoint review expansion — 40/229

The read-only entrypoint sample has advanced to **40/229**. The additional eight reviewed files are:

- `skills/dcc/zbrush/scenario-zbrush-paint-render/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-pose-print/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-retopology-export/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-sculpting/SKILL.md`
- `skills/dcc/zbrush/scenario-zbrush-stylized/SKILL.md`
- `skills/game-engines/godot/scenario-godot-2d/SKILL.md`
- `skills/game-engines/godot/scenario-godot-3d-world/SKILL.md`
- `skills/game-engines/godot/scenario-godot-animation/SKILL.md`

The single credential keyword hit in ZBrush retopology/export is a source provenance checklist (“source with credential, URL and best…”), not a literal credential value. No dynamic-code pattern was found in this 40-entrypoint sample. The remaining 189 entrypoints and all executable/configuration references still require review.


## Entrypoint review expansion — 48/229

The sample now covers **48/229** entrypoints. Eight additional Godot skills were reviewed:

- `skills/game-engines/godot/scenario-godot-architecture/SKILL.md`
- `skills/game-engines/godot/scenario-godot-audio/SKILL.md`
- `skills/game-engines/godot/scenario-godot-expert/SKILL.md`
- `skills/game-engines/godot/scenario-godot-gameplay/SKILL.md`
- `skills/game-engines/godot/scenario-godot-multiplayer/SKILL.md`
- `skills/game-engines/godot/scenario-godot-performance-export/SKILL.md`
- `skills/game-engines/godot/scenario-godot-pipeline-automation/SKILL.md`
- `skills/game-engines/godot/scenario-godot-rendering-lighting/SKILL.md`

Manual contextualization: “password” hits are names of environment variables for release keystore configuration and documentation explicitly says not to put passwords in presets; no literal secret value was observed. Shell/process guidance remains sandbox-only. No dynamic-code pattern was found in the 48-entrypoint sample. Remaining 181 entrypoints are unreviewed.


## Entrypoint review expansion — 64/229

The read-only entrypoint review has expanded from 48 to **64/229 (27.9%)**. The latest 16 entries cover Godot and Roblox skill families. Secret/token keyword hits were contextualized as Roblox Open Cloud API-key prerequisites, token-bucket terminology and security guidance about passing secrets via CI environment variables; no literal key or secret value was observed. Shell/process guidance in Godot/Roblox tooling remains sandbox-only. No `eval()` or `new Function()` pattern was found in the 64-entrypoint sample. Remaining 165 entrypoints are unreviewed.


## Entrypoint review expansion — 72/229

The manual sample now covers **72/229** entrypoints, including eight Roblox/Unity skills:

- `skills/game-engines/roblox/scenario-roblox-vfx-audio/SKILL.md`
- `skills/game-engines/unity/scenario-unity-2d/SKILL.md`
- `skills/game-engines/unity/scenario-unity-animation/SKILL.md`
- `skills/game-engines/unity/scenario-unity-architecture/SKILL.md`
- `skills/game-engines/unity/scenario-unity-expert/SKILL.md`
- `skills/game-engines/unity/scenario-unity-gameplay/SKILL.md`
- `skills/game-engines/unity/scenario-unity-mobile/SKILL.md`
- `skills/game-engines/unity/scenario-unity-performance/SKILL.md`

Manual contextualization: “credential” appears in source provenance checklists; “token” appears as Unity cancellation-token/programming terminology or in an editor-license diagnostic phrase. No literal credential value was observed. Unity command/script guidance remains sandbox-only. No dynamic-code pattern was found in the 72-entrypoint sample. Remaining 157 entrypoints are unreviewed.


## Entrypoint review expansion — 80/229

The entrypoint review sample now covers **80/229 (34.9%)**. The eight additional files span Unity pipeline/rendering/shaders/UI/VFX/web/world-building and Unreal animation. Credential keyword hits are provenance checklists in the Unity VFX and Unreal animation references, not credential values. Shell/process guidance remains sandbox-only; no dynamic-code pattern was identified in the 80-entrypoint sample. Remaining 149 entrypoints are unreviewed.


## Entrypoint review expansion — 88/229

The manual sample now covers **88/229 (38.4%)**, adding eight Unreal Engine skills (cinematics, expert, gameplay, lighting/rendering, materials, performance, pipeline automation and VFX). All credential keyword hits are source-provenance checklists; no credential value was observed. Shell/process workflows remain sandbox-only. No dynamic-code pattern was identified in the 88-entrypoint sample. Remaining 141 entrypoints are unreviewed.


## Entrypoint review expansion — 96/229

The manual sample now covers **96/229 (41.9%)**. The latest eight files include Unreal world-building and Scenario 3D/world, Ace-Step, ad variants, admin analytics, asset analysis and audio. The admin-analytics credential/API-key terms describe which projects a credential can access and a usage metric; no secret value or credential material was observed. No shell/process or dynamic-code pattern was flagged in these eight files. Remaining 133 entrypoints are unreviewed.


## Entrypoint review expansion — 104/229

The manual entrypoint sample now covers **104/229 (45.4%)**. Eight additional Scenario skills include Blender 2D/Blender, Brand Kit, Caption Studio, ChatGPT Pet Create/Update, Comic Creator and Consistency.

Important finding: `skills/scenario-blender/SKILL.md` documents a Scenario API key/secret and a local Blender MCP bearer token. The text instructs that the MCP token is distinct from the API key, held in memory, passed through `SCENARIO_BLENDER_TOKEN`, and not pasted into snippets; it also warns that a `--token` process argument exposes the token. No actual credential value was present and no credential/provider was activated. This skill is **DEFER** until MoreAI implements a reviewed server-side secret reference, customer consent, local/private MCP boundary and isolated tool execution; do not copy secrets into browser config or logs.

`scenario-chatgpt-pet-create` mentions `pip install pillow numpy`; this is installation guidance only. No packages were installed. It remains subject to dependency pinning, license and isolated worker review. No dynamic-code pattern was found in this 104-entrypoint sample. Remaining 125 entrypoints are unreviewed.


## Entrypoint review expansion — 112/229

The manual sample now covers **112/229 (48.9%)**. The eight additional Scenario skills cover ElevenLabs, fan-cam, format conversion, game assets, game UA ads, Gemini image/omni and GPT Image. The static scan found external-provider/network references but no shell/process, dynamic-code or secret-keyword pattern in these eight files. These capabilities still require approved server-side provider adapters, explicit credentials/consent, metering and artifact lifecycle; skill text alone does not activate them. Remaining 117 entrypoints are unreviewed.


## Entrypoint review expansion — 120/229

The sample now covers **120/229 (52.4%)**. Eight more Scenario skills cover Grok Imagine image/video, identity library, Ideogram, image editing/image, inspiration and Kinetic Film. External provider references in the image/video skills remain gated on server-side credential, consent, metering and artifact controls. Kinetic Film's shell scaffold is a project-generation dependency already documented in the reference triage; it is not approved for direct host execution. No literal secret or dynamic-code pattern was found in this eight-file batch. Remaining 109 entrypoints are unreviewed.


## Entrypoint review expansion — 128/229

The manual sample now covers **128/229 (55.9%)**. Eight additional Scenario skills cover Kinetic Music Video, Kling, Luma image/video, MAI image, Meshy, MiniMax music and MiniMax video. Kinetic Music Video shell scaffolding is a generated project layout and remains blocked from direct host execution; see the scaffold evidence above. The provider-specific skills require approved server-side adapters, consent, usage metering, safe artifact persistence and data-retention review. No secret or dynamic-code pattern was found in this batch. Remaining 101 entrypoints are unreviewed.


## Entrypoint review expansion — 136/229

The manual sample now covers **136/229 (59.4%)**. Eight additional skills cover model comparison/training, moderation, motion loops, multi-reference, orbit views, patina retexture and playable ads.

Important dependency gate: `scenario-motion-loops` documents Node/ffmpeg/Playwright requirements and `npm install playwright` / browser installation commands; `scenario-playable-ads` documents Python packages, Playwright Chromium and ffmpeg installation. These are instructions only; no package/browser installation or command was run. Both skills remain **DEFER** until exact-version dependency/licensing review, isolated renderer worker, artifact scanning and egress policy are accepted. Playable Ads additionally depends on a network-provided MRAID runtime as recorded in the reference triage. Remaining 93 entrypoints are unreviewed.
