# P1 Reference Document Manual Review — Batch 01

Date: 2026-11-17  
Branch: `main`  
Scope: 8 reference documents from pinned Visual Skills, Scenario Skills and Motion Skills repositories.  
Method: read-only full-text inspection at immutable source commits, with focused checks for provenance, third-party sources, provider/API claims, credentials, local execution assumptions and privacy. No referenced provider or application was called.

## Reviewed references

| # | Source document | Findings | Decision |
|---:|---|---|---|
| 1 | Visual Skills `video/references/kling.md` | Provider-specific Kling workflow and upload/reference-image guidance. Document explicitly identifies author Serge Shima, CC BY 4.0 and upstream source in its footer. It is a prompt/workflow reference, not an authenticated API contract. | **DEFER** — adapt only with CC BY 4.0 attribution, preserved author/source credit and independent current provider schema review. |
| 2 | Visual Skills `video/references/seedance-25.md` | Contains provider-specific Seedance 2.5 guidance and mentions Blender/Maya plugins uploading blockout videos to Jimeng. Document identifies Serge Shima and CC BY 4.0. Some claims are based on provider/practitioner observations and may change. | **DEFER** — retain attribution; do not turn upload instructions into an enabled provider action without user consent, destination allowlist, data handling and current API verification. |
| 3 | Visual Skills `video/references/veo.md` | Google Veo prompt/reference-image guidance; author/source footer identifies CC BY 4.0. The document is descriptive prompting guidance, not Google API authorization or an API contract. | **DEFER** — attribution plus separate official API/terms/security review required before any provider adapter. |
| 4 | Scenario `skills/dcc/maya/scenario-maya-expert/references/cmds-reliability.md` | Describes Maya Python/OpenMaya operations and explicitly says code is not yet run in Maya; some steps are marked `[verify]`. References third-party Maya MCP implementations and GUI/local scene assumptions. | **DEFER** — useful domain reference only; do not infer execution safety from procedural guidance. Cross-check commands against supported Maya versions in an isolated desktop worker. |
| 5 | Scenario `skills/dcc/maya/scenario-maya-expert/references/sources.md` | Source catalogue includes Autodesk documentation, third-party videos and public Maya MCP bridges. It explicitly labels some contributor credentials as unverified and contains external source references. | **DEFER** — preserve source attribution and the unverified labels; do not repeat credential claims as fact or copy third-party bridge implementations without their own license/security review. |
| 6 | Scenario `skills/game-engines/godot/scenario-godot-expert/references/procedures.md` | Describes local Godot 4.7.2 procedures and claims upstream live/offline tests on a specific macOS machine. Includes local MCP/editor operations, plugin installation, project mutation and export workflows. | **DEFER** — upstream test claims are not MoreAI verification; no MCP/project actions in shared workers. Revalidate in a future isolated Godot worker only if product scope requires it. |
| 7 | Scenario `skills/game-engines/roblox/scenario-roblox-expert/references/procedures.md` | Describes local Roblox Studio MCP, raw Luau execution and author-reported live/offline test runs. The guide requires a local signed-in Studio instance and has project/game mutation surfaces. | **DEFER** — treat as workstation instructions, not a hosted API contract. Raw Luau and Studio control require per-tenant isolation, approval and external-action receipts. |
| 8 | Motion `skills/talking-head/references/workflow.md` | Workflow covers user photos/voice/video, optional voice cloning, FAL/ElevenLabs provider use and local-only paths. It explicitly warns private outputs include input text, synthesized audio, downloaded footage, voice IDs and provider asset URLs; local deletion does not delete provider-side voice/uploads. | **DEFER** — requires explicit voice/likeness consent, data-retention disclosure, provider-side deletion flow, server-only secret references, credit reservation and isolated media processing. No cloning/upload/provider calls are authorized by this review. |

## Cross-cutting conclusions

- Visual Skills reference documents carry CC BY 4.0 attribution requirements; retain the named author and exact source reference when adapting.
- Provider/model names and workflow details in reference documents are not stable API contracts. Recheck official provider docs and product terms before building adapters.
- Maya, Godot and Roblox procedures assume local desktop/editor state. Their test claims are upstream author evidence only and do not prove a MoreAI sandbox or worker integration.
- Motion talking-head materials can contain sensitive personal likeness/voice and provider-side artifacts. User consent, deletion and retention controls are mandatory before enabling any voice/media workflow.
- No external source was contacted, no media was uploaded, and no provider credentials were read.

## Coverage and disposition

- Manual reference documents reviewed in this batch: **8/726**.
- Remaining reference documents: **718/726**.
- All 8 reviewed documents remain **DEFER** pending rights/attribution, provider contract, privacy or isolated execution gates.
- The separate 148/148 parser-candidate triage remains complete; that triage resolves reference-path semantics, not the content of all 726 documents.

No scripts, tests, builds, installs, providers, Supabase operations, staging or deployments were run.

**P1 remains OPEN.**
