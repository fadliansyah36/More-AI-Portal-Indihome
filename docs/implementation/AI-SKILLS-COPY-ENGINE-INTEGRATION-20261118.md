# AI Skills and Copy Engine integration

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

Inputs include locale, audience, product and brand context, voice, channels, constraints, supplied source facts, forbidden claims and 1–5 variants. Output asks for a structured brand voice spec, core message, variant map, factual gaps and compliance notes. The tool explicitly prohibits fabricated prices, discounts, certifications, guarantees, performance results, testimonials and unsupported product claims.

The tool uses no direct provider SDK, external SaaS or Scenario MCP. Usage remains on MoreAI's existing metered LLM gateway. No separate copywriting database, model, or agent is introduced.

## Activation and authorization

Source integration is committed. Database activation is intentionally not performed in this task: no package import, install, permission grant, publication or registry write was made to Supabase. Existing packages must be imported, validated, published and installed through the current FastAPI/Skill Registry workflow before a customer can select them. The tool itself remains subject to the existing per-run saved-agent tool allowlist and policy-enforced registry.

## License and provenance

- Visual Skills: CC BY 4.0; preserve Serge Shima attribution and NOTICE.
- Scenario Skills: MIT; root license applies to the selected skill source; nested Apache-2.0 skill-creator remains separately scoped.
- Motion Skills: MIT at each pinned child pack; unlicensed generative-illustration pack remains blocked.
- The Copy Engine adapter is original MoreAI code. It adapts the workflow patterns of Scenario brand-kit/ad-variants and preserves source attribution in `THIRD_PARTY_NOTICES.md`.
- OpenManus/OpenFuse notices and source pins remain in the same third-party notice register.

## Database and deployment boundary

No Supabase write, migration apply, staging, runtime test or deployment was performed. No database activation is claimed. Existing Agent Studio UI was not redesigned.
