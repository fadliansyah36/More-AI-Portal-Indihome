# AI Skills and Copy Engine integration

## Curated source coverage and permission manifest

The selected source manifest contains **230 curated entrypoints**: 2 Visual Skills, 173 Scenario Skills and 55 licensed Motion Skills. The 19th Motion pack without a resolved license remains excluded. Exact source pins, paths and blob hashes are retained in `MOREAI_P1_SELECTED_SKILL_ENTRYPOINTS_20261117.csv`. The scoped tool permissions for every selected entrypoint are in `AI-SKILLS-REQUIRED-PERMISSIONS-MANIFEST-20261118.csv`.

- `media.generate` is required for Visual, Motion and Scenario native-media adapters; it maps only to the existing `image_generate` and `video_generate` tools.
- `content.generate` is required for Scenario brand-kit, ad-variants and text-overlay skills; it maps only to `copy_engine_generate`.
- API and worker both allowlist these permission names; the worker resolver fails closed if an adapter's required permission is not present in the install's granted-permission snapshot.

A read-only Supabase constraint inspection confirmed the skill package/install permission columns are JSON arrays with type-only checks, not a fixed database enum/check list. No schema migration is required for these new permission labels. No package import, install, permission grant or publication write was made.

## Canonical runtime path

`Agent Studio → FastAPI typed Agent Run API → existing Supabase Skill Registry/Resolver → OpenManus Durable Agent Runtime → policy-enforced tool registry`.

No second Agent Runtime or Skill Registry is introduced. Skill snapshots remain owner-scoped, immutable, versioned, hash-verified and permission checked. Worker-side repository/commit/path allowlists remain a second trust boundary. Skill content is untrusted procedural context; it cannot grant tools or override policy.

## Implemented capability adapters

| Source | Pinned source | Existing MoreAI capability | Integration behavior |
|---|---|---|---|
| Visual Skills image | `smixs/visual-skills@61a60d317f0fa0c3dc98902e58a7cb178838ae3f` | `image_generate` | Prompt authoring only; actual model/provider limits come from MoreAI tool schema |
| Visual Skills video | same | `video_generate` | Director/storyboard/prompt guidance; no upstream provider is claimed |
| Scenario brand kit | `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` | `copy_engine_generate` | Brand voice, message hierarchy and brand-aligned copy workflow |
| Scenario ad variants | same | `copy_engine_generate` | Controlled copy variants, fixed invariants and explicit variant deltas |
| Scenario text overlay | same | `copy_engine_generate` | Exact copy strings and a deterministic text-overlay payload specification; renderer is not imported |
| Motion Skills child packs | immutable child commits in P1 manifests | `video_generate`, `image_generate` | Creative production guidance only; missing renderers/providers fail closed |

The worker resolver now selects a dedicated Scenario copy adapter for `scenario-brand-kit` and `scenario-ad-variants`; all other Scenario skills retain the existing native-media adapter or explicit provider-capability denial. Visual and Motion adapters remain in the same resolver.

## Copy Engine contract

The canonical tool key is `copy_engine_generate`, version `1.0.0`. It is included in the existing tool catalog and registered by `DurableOpenManusRuntime`. The implementation calls the existing metered gateway using the configured chat routing policy and a deterministic run/payload request key.

Supported modes:
- `brand_voice`
- `campaign_concept`
- `ad_variant`
- `social_caption`
- `landing_page`
- `product_description`
- `email`
- `headline`
- `text_overlay`

Inputs include locale, audience, product and brand context, voice, channels, constraints, supplied source facts, forbidden claims and 1–5 variants. Output asks for a structured brand voice spec, core message, variant map, factual gaps and compliance notes. The tool explicitly prohibits fabricated prices, discounts, certifications, guarantees, performance results, testimonials and unsupported product claims. The `text_overlay` mode returns a structured payload specification only; it does not render or composite an image/video. Scenario text-overlay's `chevron`, Pillow and Chromium dependencies are intentionally not imported.

The tool uses no direct provider SDK, external SaaS or Scenario MCP. Usage remains on MoreAI's existing metered LLM gateway. No separate copywriting database, model, or agent is introduced.

## Activation and authorization

Source integration is committed. Database activation is intentionally not performed in this task: no package import, install, permission grant, publication or registry write was made to Supabase. Existing packages must be imported, validated, published and installed through the current FastAPI/Skill Registry workflow before a customer can select them. The tool itself remains subject to the existing per-run saved-agent tool allowlist and policy-enforced registry. Scenario copy skills (`scenario-brand-kit`, `scenario-ad-variants`, `scenario-text-overlay`) require the explicit skill permission `content.generate`; this permission is allowlisted by the API and worker, and maps only to `copy_engine_generate`. The resolver fails closed if the installation's granted permission snapshot does not include it. The two source mappings and their current activation state are in `AI-SKILLS-COPY-ENGINE-PERMISSION-MANIFEST-20261118.csv`.

## License and provenance

- Visual Skills: CC BY 4.0; preserve Serge Shima attribution and NOTICE.
- Scenario Skills: MIT; root license applies to the selected skill source; nested Apache-2.0 skill-creator remains separately scoped.
- Motion Skills: MIT at each pinned child pack; unlicensed generative-illustration pack remains blocked.
- The Copy Engine adapter is original MoreAI code. It adapts the workflow patterns of Scenario brand-kit/ad-variants and preserves source attribution in `THIRD_PARTY_NOTICES.md`.
- OpenManus/OpenFuse notices and source pins remain in the same third-party notice register.

## Database and deployment boundary

No Supabase write, migration apply, staging, runtime test or deployment was performed. No database activation is claimed. Existing Agent Studio UI was not redesigned.
