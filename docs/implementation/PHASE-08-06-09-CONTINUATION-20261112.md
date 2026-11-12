# Phase 08 / 06 / 09 Continuation — 2026-11-12

## Scope
Direct-main implementation increment for provider capability matching, durable RAG citation propagation, FastAPI profile error contracts, and Customer Chat / Wallet binding. Existing UI layout and visual tokens are preserved; the Wallet screen's fabricated transaction records and fabricated balance/token conversion are removed.

## Baseline and target
- Baseline: current `main` immediately before this increment (repository state fetched from the canonical GitHub connector).
- Target commits:
  - `681617addb946c585bc22a5fb2c72f45e306069c` — requested model capability filtering reaches candidate resolution.
  - `5967ab698eae58de768f38b03dcc285bcfbaab48` — OpenManus tool route requires tool-call capability and final output includes durable retrieval citations.
  - `34bf606ba6bbf3661529e5a33ce6658ed1ae6d36` — RAG retrieval preserves chunk identifiers and metadata.
  - `78699331b0b440f436a64242ca11f87859bd1818` — Customer Chat displays returned knowledge citations.
  - `e59680dfc2ead0d860d7b41df3794395eec15362` — canonical provider/model capability aliases.
  - `c7df5ee843709e4091c38a5c063b10969f67917e` — Customer Wallet uses authenticated wallet and ledger API data instead of local fabricated entries.
  - `bb25ef3e4110c5c860bee72d63fb0a98361a19b2` — ledger direction derives from entry type and amount.
  - `98c100f55ee54f90c40c4a60906c1af96b658c1a` — profile API errors use the common structured FastAPI error envelope.
  - `a5066ee6d7da66bf238620ce451d2e32c59fb9e2` — frontend API client parses structured detail, error code and correlation ID.

## Implementation details

### Phase 08 — LLM / RAG
- `MeteredGateway.complete` now accepts `required_capabilities` and forwards them into both candidate and single-route resolution.
- `DurableOpenManusRuntime` requests the canonical `tool_calling` capability when it supplies function tools. This prevents a text-only model from being selected for a tool-enabled ReAct turn.
- `ModelRouter` normalizes known provider/model capability aliases (for example tools/function_calling/tool_calls → tool_calling; vision/image_understanding → image_input; json_schema → structured_output) before subset matching.
- RAG tool observations preserve `chunk_id`, `document_id`, title, similarity and safe metadata. Durable run final output includes de-duplicated citation records reconstructed from settled `knowledge_search` checkpoints, so citation metadata survives worker restart/replay.
- Manus system instructions now require exact source markers from retrieved chunk IDs and prohibit invented source markers.

### Phase 06 — FastAPI / client contract
- Profile GET/PATCH upstream failures, invalid response shapes, invalid display names/avatar paths and missing profile rows now raise structured HTTP errors handled by the common error envelope.
- The shared browser API client understands both legacy string details and structured FastAPI details, preserving error code and correlation ID on the thrown error.

### Phase 09 — Customer Dashboard
- Customer Chat accepts citation metadata from the completed durable run and shows the source title and stable chunk marker without changing the message layout.
- Customer Wallet no longer renders hardcoded sample transactions, a made-up balance, or an invented token conversion. It loads wallet accounts and immutable ledger entries from the existing authenticated Customer API, retains the existing filter UI, and shows explicit loading/error/empty states.

## Supabase
- No database schema, migration, policy, storage bucket or production data was changed in this increment.
- Existing knowledge RAG RPC output already exposes `chunk_id`, `document_id`, `title`, `content`, `similarity`, and `metadata`; the worker adapter now retains those citation fields rather than discarding them.

## UI preservation
- No layout, color, typography, spacing, navigation, or screen hierarchy redesign.
- `components/views/chat-view.tsx`: additive source list for citations only.
- `components/views/token-ledger-view.tsx`: same screen structure; data source changed from fabricated local records to live API contract.

## Tests / runtime / security
- Per owner instruction: no tests, lint, typecheck, build, API requests, browser automation, provider calls, database writes, migrations, staging or deployment were run.
- Static source inspection only. This report does not claim runtime acceptance or production behavior.
- Agent execution remains fail-closed; no worker activation or deployment was attempted.
- Security boundaries remain server-side: provider secrets and service-role credentials are not added to browser code; RAG citations contain only source identifiers/title/similarity, not vectors or private tool arguments.

## Remaining blockers — not phase complete
- Phase 08: full upstream agent/flow parity and explicit registry coverage beyond currently registered `manus` and `planning`; full tool adapter parity; provider-specific capability matrix and production route configuration; durable file/PDF extraction and ingestion; embedding lifecycle/retry/recovery; richer source/page/offset citation attribution; end-to-end citation validation.
- Phase 06: complete route-by-route OpenAPI schema/error/pagination/idempotency coverage; consistent principal and authorization dependencies across every customer/partner/admin route; exhaustive tenant isolation review and OpenAPI compatibility evidence.
- Phase 09: full screen-to-contract reconciliation remains outstanding. Wallet and Chat citations were improved, but every existing Customer page/action (including Wi-Fi/network, captive portal, account upgrade/benefits, device/session, remaining analytics, profile/security, file upload, knowledge file ingest, and other feature screens) still needs individual real API binding or explicit unavailable-state treatment. No mock data may remain in production UI.
- Phases 04, 07, 08, 06 and 09 remain IN PROGRESS; Phase 10 remains NOT ACCEPTED and Phase 11 remains BLOCKED.

## Next dependency-ordered work
1. Phase 08: implement durable file upload + safe PDF/text extraction and resumable ingestion using the existing private Storage / worker / knowledge schema; complete source metadata and citation rendering; reconcile every upstream agent, flow and tool capability against the capability map.
2. Phase 06: finish shared Pydantic response/error contracts, authorization dependency coverage, tenant/workspace membership checks, cursor pagination and idempotency across all mutation endpoints; publish generated OpenAPI contract artifacts.
3. Phase 09: audit every Customer route and bind each existing screen/action to the real FastAPI contract; remove remaining fabricated content and unsupported success interactions while preserving visuals.
4. Only after explicit authorization, perform integration verification and release gates. No deployment before Phase 11.
