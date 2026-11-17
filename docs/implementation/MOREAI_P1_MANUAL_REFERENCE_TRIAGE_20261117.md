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
