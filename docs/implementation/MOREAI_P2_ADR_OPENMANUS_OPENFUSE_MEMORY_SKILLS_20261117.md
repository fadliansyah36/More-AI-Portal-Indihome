# P2 Architecture Decision Record — OpenManus, OpenFuse, Memory & Skill Integration

Date: 2026-11-17  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Target branch: `main`  
Status: **DRAFT — NOT ACCEPTED; P1 source-governance closure and mandatory Phase 00–11 acceptance remain prerequisites.**  
Decision scope: integration architecture only. No product code, schema or UI changes are authorized by this draft.

## 1. Context and constraints

The product must integrate the existing Customer Dashboard with the pinned OpenManusWeb backend, OpenFuse browser/computer capabilities, unified memory and selected Visual/Scenario/Motion skills, using FastAPI and the canonical Supabase project.

Binding constraints from `AGENTS.md`:
- OpenManus remains the sole Agent Runtime and complete pinned OpenManusWeb source remains a pristine archival snapshot.
- FastAPI is the trusted business API. Browser Supabase access is Auth-only; all business data/actions go through typed FastAPI clients.
- Supabase PostgreSQL is canonical persistence; do not create a second database or duplicate registry.
- Existing Next.js Customer UI is protected. Add UI only for a required PRD workflow that is demonstrably absent.
- No additional PRD feature/domain implementation before mandatory Phase 00–11 pass, unless a written product-owner exception is approved.
- No fake data, demo success, mock provider, direct browser database CRUD, unreviewed provider calls, staging or deployment.
- User instruction for this continuation: no real testing and no staging. Therefore Phase 10 and Phase 11 cannot be accepted in this work session.

## 2. Evidence reviewed

### Main source tree and provenance
- OpenManusWeb pinned `dev_web_app@3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`, 111 files; repository source manifest reports 111/111 matching Git blob SHA in `vendor/openmanusweb/`.
- OpenFuse pinned `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`, 219 files.
- Visual Skills pinned `61a60d317f0fa0c3dc98902e58a7cb178838ae3f`, 60 files, 2 product `SKILL.md` entrypoints, CC BY 4.0 + attribution.
- Scenario Skills pinned `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`, 2,114 files; 172 product skill entrypoints + 7 internal maintainer entrypoints, 519 references, 898 scripts, 54 assets and 20 test/evidence paths in the prior source audit. Root MIT plus nested Apache 2.0 for internal skill-creator.
- Motion Skills root pinned `9b9ce041932da787cc856d4cdf23afb6cd13d4bf` is a catalogue, not an executable skill pack. Its 19 separately pinned child repositories contain 56 product skill entrypoints. Eighteen child packs expose MIT root licenses; `generative-illustration-skills` is missing a root license and is blocked.
- The 24 source trees are inventoried in the P1 recursive manifests. A 3,919-entry preliminary disposition register exists but is explicitly not final.
- Static CycloneDX 1.6 BOM currently inventories 2,024 distinct component records from upstream lockfiles/manifests and MoreAI manifests. Lockfile license metadata, complete dependency edges, 24 OpenManusWeb requirement resolutions, registry license evidence and vulnerability reconciliation remain incomplete.
- Raw SHA-256 evidence is currently computed for 34 files (including all 18 identical Motion pack root LICENSE files, root notices, selected lockfiles and selected skill entrypoints). It is not a full SHA-256 manifest for all selected skill source trees.

### Existing MoreAI implementation evidence
- Existing typed Customer API client: `lib/api/client.ts`; it obtains Supabase Auth session tokens and calls FastAPI. Browser business-data access must remain behind this client.
- Existing memory implementation: `engine/agents/memory_context.py`, `engine/agents/memory.py`, `apps/worker/app/memory_store.py`; existing memory coordinator composes Working, Conversation, Personal/Long-term, Episodic, Semantic and Procedural context.
- Existing skill implementation: `apps/api/app/routers/skills.py`, `apps/worker/app/skill_resolver.py`; pinned immutable source ingestion, SHA-256/Git blob verification, SBOM evidence, owner-scoped installation, permission snapshots and audit already exist.
- Existing browser/computer implementation: `apps/api/app/routers/browser_sessions.py`, `apps/api/app/routers/computer_actions.py`, browser supervisor/sandbox adapters, persistent browser sessions, action receipts, capacity leases, takeover grants and customer preview/takeover components.
- Existing Knowledge Library uses `knowledge_documents`, `knowledge_chunks` and pgvector. Existing conversation and Agent Run records provide durable run/step/event/checkpoint history.
- Existing UI components include Skills Library, Personal Memory settings, Knowledge Library, browser session preview and browser takeover. Do not add duplicate screens/components until an exact missing PRD behavior is proven.

### Canonical Supabase schema evidence
Project ref: `uunfgimtokhucegqbpce`. Read-only inspection found canonical tables including:
- Runs: `agent_runs`, `agent_run_steps`, `agent_run_events`, `agent_run_checkpoints`, `tool_executions`.
- Memory/knowledge: `conversations`, `conversation_messages`, `moreai_customer_memories`, `moreai_customer_memory_preferences`, `knowledge_documents`, `knowledge_chunks`.
- Skills: `moreai_skill_packages`, `moreai_skill_installs`, `moreai_skill_source_files`, `moreai_skill_execution_audit`, `moreai_skill_registry_audit`.
- Browser/computer: `moreai_browser_sessions`, `moreai_browser_session_events`, `moreai_browser_action_receipts`, `moreai_browser_capacity_leases`, `moreai_computer_action_receipts`.
- Approvals/notifications: `agent_tool_approvals`, `agent_run_approval_pauses`, `notifications`, `notification_preferences`, `outbox_events`.
- Wallet/entitlements: `wallet_accounts`, `credit_ledger`, `credit_reservations`, `quota_policies`, `quota_usage`, `user_entitlements`.
No new database, vector store, skill registry or run ledger is justified by current evidence.

## 3. Decisions proposed

### ADR-01 — One Agent Runtime: OpenManus

**Decision:** OpenManus is the only agent execution runtime. MoreAI keeps the complete pinned upstream source under `vendor/openmanusweb/`; production adaptations live in `engine/`, `apps/api/`, `apps/worker/` and `apps/sandbox/`.

**Consequences:**
- No OpenFuse Agent Runtime, Hono server or PGlite database is deployed as a second canonical runtime.
- Preserve upstream backend parity by capability/module, not by copying only selected files.
- Adapt upstream server/session/stream behavior into FastAPI and durable worker contracts.
- Keep upstream user-facing UI only in the archival snapshot; MoreAI's existing Customer UI remains authoritative.

### ADR-02 — OpenFuse as an internal capability adapter

**Decision:** Port browser, computer, download, OAuth/session and action-receipt patterns from OpenFuse into the existing MoreAI FastAPI/worker/sandbox boundary.

**Required flow:**
`Customer UI → typed API client → FastAPI auth/tenant/approval → durable Agent Run → worker → isolated Browser/Computer Supervisor → Supabase session/action receipts/artifacts → event/status projection → existing Customer UI`.

**Security constraints:**
- Browser contexts and computer workspaces are owner/tenant/run scoped.
- SSRF/private-IP/DNS-rebinding/redirect protections are enforced at network egress, not only by URL parsing.
- Downloads are size/MIME/content validated, quarantined/scanned and persisted privately.
- OAuth uses tenant-bound PKCE/state, encrypted credentials, least-privilege scopes and revocation.
- Gmail send, Calendar mutations, computer commands and other high-impact actions require explicit user approval, immutable receipt and idempotency/unknown-outcome handling.
- Docker and E2B/network-enabled runners are not equivalent; each needs a separate threat model and egress policy.
- No browser/computer capability is active until deployed supervisor readiness and security acceptance are evidenced.

### ADR-03 — One Memory Coordinator, six logical memory types

**Decision:** Keep the existing Memory Context Coordinator and canonical persistence. Do not create six new tables or a second memory database.

| Logical memory | Canonical source | Rules |
|---|---|---|
| Working | current Agent Run input/context, steps, checkpoints and tool observations | bounded to active run; no implicit long-term persistence |
| Conversation | `conversations` and `conversation_messages` | owner/workspace scoped; durable transcript and run replay |
| Long-term / Personal | `moreai_customer_memories` and `moreai_customer_memory_preferences` | explicit consent, owner scope, retention and deletion |
| Episodic | bounded episode metadata on `conversation_messages`, linked to run/citations/skill snapshots | consent-gated, untrusted recall, explicit expiry/deletion |
| Semantic | `knowledge_documents`, `knowledge_chunks`, pgvector and citation provenance | owner/tenant/document authorization; deletion and re-index lifecycle |
| Procedural | approved immutable Skill package/version and workflow definitions | instructions are untrusted context; never grant permissions |

**RLS note:** prior read-only policy inspection found owner-scoped authenticated ALL policies on the two personal-memory tables, while AGENTS.md prohibits browser business-data CRUD. This is an architectural hardening item: inspect all frontend callsites and keep all memory operations on FastAPI. Do not apply RLS changes until policy/grant/function/storage dependencies and existing service paths are reconciled in Phase 05.

### ADR-04 — One Skill Registry and immutable resolver

**Decision:** Reuse existing `moreai_skill_*` tables and `SupabaseSkillResolver`. Do not create a second Skill Registry or direct skill execution path.

**Import/publication sequence:**
1. Source repository + immutable commit allowlist.
2. Recursive source inventory; selected `SKILL.md`, references and required files only.
3. Git blob SHA + raw SHA-256 + file-size/path validation.
4. Dependency graph/SBOM and exact-version license/NOTICE/asset provenance.
5. Static security validation and external provider reference scan.
6. Reviewer decision and publication evidence.
7. Owner install and explicit permission grant, separate from publication.
8. Immutable run snapshot and runtime tool allowlist/approval.
9. Execution audit, durable Agent Run lifecycle and artifact receipts.

A package remains pending/review-required or blocked until all evidence is complete. Unknown license, unverified binary asset, unsupported external service or unsafe script means defer/exclude, never silently approve.

### ADR-05 — Provider capabilities remain separate from skill content

**Decision:** Scenario MCP, iArt MCP and Fal.ai are external providers, not bundled capabilities of the open-source skill repositories. No credentials or API calls are assumed. Skills must invoke only MoreAI's approved provider adapters through Model/Tool Resolver and FastAPI/worker contracts.

**Activation prerequisites:** provider-owner approval, privacy/legal terms, server-only credentials, capability allowlist, pricing version, entitlement/quota/credit reservation and settlement, durable job idempotency, artifact storage, retention/deletion and worker security gate.

### ADR-06 — Preserve the existing Customer UI; add only missing components

**Decision:** Reuse the existing Skills Library, Personal Memory settings, Knowledge Library, Browser Preview/Takeover and existing Agent Run/Workflow/Tasks projections. Add no new UI in this ADR.

If a later PRD trace proves a required workflow has no UI, add the smallest component using the existing MoreAI light surface, red brand actions, navy typography, established CSS/Tailwind classes, buttons, fonts, loading/progress/empty/error states and responsive conventions. No global restyling or new design system.

### ADR-07 — Supabase remains the only canonical application database

**Decision:** Keep PostgreSQL/Auth/Storage/Realtime/pgvector and existing tables. No PGlite, local in-memory Map, second vector database or external provider database becomes product source of truth.

Every server query/mutation remains explicit owner/workspace/partner scoped. All new schema changes, if eventually justified, are forward-only, idempotent, reviewed migrations with RLS and rollback/mitigation notes.

## 4. Capability-to-phase traceability

| Capability | Existing evidence | Mandatory phase owner | Remaining gap |
|---|---|---|---|
| OpenManus full parity | pristine vendor snapshot + capability map | 03/04/08 | capability map still contains PARTIAL entries; complete backend behavior and parity evidence |
| OpenFuse browser/computer | FastAPI routers, worker adapters, sandbox supervisor, session/receipt/lease tables | 04/06/07/08/09 | full source path review, deployed supervisor readiness, network and download security acceptance, UI action coverage |
| Memory six types | coordinator, stores, consent/retention, pgvector and existing tables | 04/05/07/08/09 | full lifecycle source review, consent/deletion, citations, orphan storage cleanup and RLS/browser boundary proof |
| Skills | registry, ingestion, resolver, permission/audit tables and UI | 01/04/05/06/08/09 | complete selected-file SHA/SBOM/license/security evidence, import selected packages, provider contracts, runtime acceptance |
| Customer dashboard | typed API client and existing UI views | 06/09 | close every screen/action against real FastAPI contracts; remove any remaining mock/fallback behavior |
| E2E/release | historical CI evidence only | 10/11 | user explicitly prohibits tests/staging in this continuation; cannot accept phases 10/11 |

## 5. Rejected alternatives

- **Run OpenFuse as a separate product runtime:** rejected; duplicates runtime, data store and auth boundary.
- **Create a new memory database or six tables:** rejected; existing schema and coordinator already cover the six logical types.
- **Create a second skill registry:** rejected; existing registry supports pinned provenance, validation, permission and audit.
- **Allow skill instructions to call external MCP/provider directly:** rejected; bypasses tenant, entitlement, metering, approvals and artifact policy.
- **Replace existing Customer UI with OpenFuse/OpenManus UI:** rejected by UI freeze and product design authority.
- **Bulk import every skill and enable execution by default:** rejected; asset rights, license, dependencies, scripts, provider and permissions remain per-package gates.
- **Add direct Supabase business CRUD in React:** rejected by AGENTS.md.

## 6. Acceptance criteria for this ADR

This draft can be accepted only after:
1. P1 closes recursive content review, all nested licenses/NOTICE/asset provenance, exact dependency/SBOM license reconciliation, raw SHA-256 for every selected file and final file-by-file disposition.
2. Phase 04/06/07/08 capability parity and security contracts are reconciled against current source and schema.
3. Phase 05 confirms all RLS policies, grants, RPCs, triggers and Storage boundaries for selected flows.
4. Phase 09 customer action inventory proves every existing screen action has a real typed FastAPI contract or an explicitly unavailable state with no fabricated success.
5. Product owner accepts this ADR or records specific exceptions.

## 7. Implementation boundary and next action

No code, UI, migration, data or provider change is authorized by this draft. No tests, build, lint, typecheck, staging, deployment or live provider calls were performed.

**Next action:** continue P1 closure, then finalize and accept P2 ADR. Afterward, complete mandatory Phase 04/05/06/07/08/09 in dependency order; Phase 09 must close before Phase 10. Phase 10/11 remain unaccepted until their required verification is explicitly authorized and evidenced.
