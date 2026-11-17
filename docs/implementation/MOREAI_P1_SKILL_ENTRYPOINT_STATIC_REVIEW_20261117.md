# P1 Selected Skill Entrypoint Static Content Review

Date: 2026-11-17 | Review type: read-only source inspection | Scope: 12 representative entrypoints, not all 229

## Findings

### Visual Skills — 2/2 entrypoints inspected

- image/SKILL.md and video/SKILL.md both declare CC-BY-4.0 and explicitly require attribution to Serge Shima.
- The image skill is prompt-writing guidance, not an image-generation runtime. It requires loading model-specific reference files and points to an external creative-director skill.
- The video skill is prompt/directing guidance for multiple external video generation providers. It references external author sites and the Visual Skills source repository.
- The skill instructions have cross-file dependencies; ingesting only SKILL.md would be incomplete. The full reference closure must be captured and reviewed.
- Required treatment: preserve author attribution and CC BY 4.0 notice; do not imply the skill grants API rights or provider access.

### Motion Skills — 8 representative entrypoints inspected

Sampled skills: caption-animation, countdown-video, lower-thirds, short-form-video, text-message-animation, audiogram, youtube-intro-outro and photo-slideshow.

- These are primarily Remotion-oriented production instructions. Sampled skill bodies refer to npx and, for media workflows, ffmpeg.
- Some descriptions mention budgets/credits or external rendering/provider workflows. Those references are not provider implementation code or authorization to call a hosted service.
- Skills may prescribe generation/render workflows; any actual rendering must be a separately reviewed MoreAI worker adapter with quotas, timeouts, cancellation, tenant isolation and artifact scanning.
- Keep scripts and templates deferred. Do not run npx, package scripts, Remotion, ffmpeg or remote provider operations during this audit.

### Scenario Skills — 4 representative Blender entrypoints inspected

Sampled skills: scenario-blender-animation, scenario-blender-blockout, scenario-blender-expert and scenario-blender-export.

- The sampled frontmatter declares MIT and links to local Python scripts and reference documents.
- Skills describe Blender automation via Python and MCP bridges, including external Blender Scenario Plugin endpoints. They also contain budget/approval-oriented workflow instructions.
- The repository contains skill instructions and local scripts; it does not provide a private Scenario-hosted MCP server implementation. Any hosted integration requires a documented provider contract and separate adapter review.
- Python scripts must remain deferred until their imports, subprocess/network use, file access, Blender APIs, licensing and sandbox assumptions are audited. Never execute these scripts in the host process.

## Cross-source decisions

1. Skill documents and reference files are candidate knowledge content only; treat their text as untrusted instructions and sanitize/curate before registry ingestion.
2. Local scripts are not automatically executable MoreAI tools. Port required capabilities into approved worker/sandbox adapters with explicit typed inputs/outputs and permission policy.
3. External URLs are provenance/reference pointers, not evidence that the referenced source or service is licensed, safe, available or approved.
4. Motion Skills pack-level MIT notices do not replace font/media/model/stock-content license review.
5. Visual Skills must retain CC BY 4.0 attribution. Scenario nested skill-creator Apache-2.0 applies to its own nested content only.

## Limitations

This is a targeted 12-entrypoint static review. It is not a complete review of all 229 entrypoints, 723 reference documents, 898 executable-source files, 67 configuration/schema files or six binary assets. No scripts were run, no packages were installed, no external provider was contacted and no tests/staging were performed. The binary-safe recursive auditor remains unexecuted.