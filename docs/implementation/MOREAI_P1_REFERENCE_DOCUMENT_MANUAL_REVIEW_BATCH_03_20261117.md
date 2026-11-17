# P1 Reference Document Manual Review — Batch 03

Date: 2026-11-17  
Branch: `main`  
Scope: 6 additional references from Scenario Skills and Visual Skills.  
Method: read-only content review at immutable pinned commits. No training run, model upload, media upload, provider call, external tool invocation or dataset mutation was performed.

## Reviewed references

| # | Document | Findings | Decision |
|---:|---|---|---|
| 1 | Scenario Model Training `references/base-model-selection.md` | Describes base model selection, image/video/voice dataset shape, cost/performance trade-offs and server-returned model types. It explicitly cautions not to assert model IDs from the cheat sheet and to use the live `recommend_training` response. | **DEFER** — preserve dynamic model selection; do not hardcode model IDs or treat the guide as a provider contract. Any training route needs a typed MoreAI adapter, live quote, user budget and approval. |
| 2 | Scenario Model Training `references/dataset-curation.md` | Describes uploading personal/product/character images, captions, dataset review, `upload_images`, `asset_analyze`, `update_image` and `delete_image` actions. It recommends checking dimensions/duplicates before upload and treats captions as training data. | **DEFER** — require rights to all images, consent for identifiable people, explicit dataset purpose, private storage, data retention/deletion, upload limits and immutable cost reservation before any external training upload. |
| 3 | Scenario Model Training `references/video-lora.md` | Describes video LoRA training, upload of clips/reference assets, dataset pairing and a dry-run quote before start. It explicitly states real-person likeness needs consent and cites the MiniMax H3 license as forbidding imitation of real people and use of outputs to train other AI models. | **DEFER / LICENSE BLOCK** — independently verify the cited model license and provider terms; enforce likeness/voice consent, dataset rights, per-run budget approval and provider-side deletion. No training job may be started from this reference alone. |
| 4 | Scenario Kinetic Music Video `references/audio_editing.md` | Describes local editing of approved audio, upload/reuse of source assets, provider model runs, dry-run quote, launch, download and deterministic local audio cuts. It explicitly warns not to invent unsupported join APIs and to retain source/master/candidate separation. | **DEFER** — useful workflow pattern, but audio uploads and paid model runs require user authorization, exact schema validation, credit reservation, immutable job receipts and artifact provenance. |
| 5 | Scenario Playable Ads `references/make-them-install.md` | Creative/UX guidance for playable-ad conversion, pacing, CTA, sound and end-card behavior. No provider credentials or executable command surface was found in the reviewed content. | **DEFER** — content-only reference; adapt only where PRD requires and retain source/license attribution. |
| 6 | Visual Skills `image/references/models.md` | Compares Nano Banana and GPT Image 2.5 model families and prompt structure; footer identifies Serge Shima, CC BY 4.0 and source repo. This is a prompt-writing reference, not a live model catalogue or API contract. | **DEFER** — preserve CC BY attribution and validate model IDs/availability/terms against current official provider documentation before mapping to the MoreAI model router. |

## Cross-cutting findings

- Training workflows can transfer user photos, likeness, voice, video and captions to external model providers. Consent, ownership, retention and provider-side deletion are first-class requirements, not optional UI copy.
- A dry-run quote is not authorization to start. MoreAI must reserve credits/quotas, capture explicit approval, then start through the durable Agent Run lifecycle with idempotency and a provider receipt.
- Model-specific license restrictions must be reviewed per selected base model and version; root skill-repository MIT licensing does not override the model/provider license.
- References that caution against hardcoded model IDs align with MoreAI's model-router architecture: only server-returned, currently authorized models should be selectable.
- No model, asset, audio, video, user data or credential was sent to an external provider.

## Coverage and disposition

- Manual reference documents reviewed in this batch: **6/726**.
- Cumulative manual reference content review: **23/726**.
- Remaining reference documents: **703/726**.
- All six remain DEFER pending capability mapping, license/provider terms and consent/data lifecycle controls.

No tests, builds, package installs, model downloads, training jobs, provider calls, Supabase operations, staging or deployment were performed.

**P1 remains OPEN.**
