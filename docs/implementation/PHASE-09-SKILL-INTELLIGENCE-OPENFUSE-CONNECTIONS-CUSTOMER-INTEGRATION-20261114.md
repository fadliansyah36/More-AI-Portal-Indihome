# MoreAI Phase 09 — Skill Intelligence, OpenManus and Connections Center Integration

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Status: **IMPLEMENTATION IN PROGRESS — SOURCE COMMITS ONLY; NOT RELEASE ACCEPTED**

## 1. Engineering constraints applied

- Followed `AGENTS.md`: existing Next.js customer shell remains canonical; no OpenManusWeb frontend was mounted and no second Agent Runtime was introduced.
- OpenManus remains the single Agent Runtime. OpenFuse integration is adapted into existing FastAPI and worker boundaries.
- Supabase remains the canonical database; FastAPI remains the trusted customer/backend boundary.
- Customer UI additions preserve the existing red actions, white/light-gray surfaces, navy/slate typography, rounded controls and spacing conventions.
- No staging, deployment, browser test, build, lint, typecheck, automated test, provider test operation or Supabase migration execution was performed.

## 2. Skill Intelligence Platform

### 2.1 Source ingestion and integrity

- Pinned-source ingestion now traverses the skill entrypoint's containing directory, nested directories and local references.
- It collects source-controlled manifests, scripts, license/NOTICE files, text documentation and binary assets within bounded limits.
- Git Blob SHA-1 uses the canonical Git blob preimage; SHA-256 is independently recomputed.
- The entrypoint hashes must match the immutable package provenance.
- Symlink/special file entries, path traversal, unpinned repositories/commits, oversized files/packages and duplicate ingestion are rejected.
- Source bytes and the registry validation report are persisted through one transactional Supabase RPC; source files are immutable per package.
- A source inventory detects SPDX/license files, SKILL.md/package manifests, npm/PyPI/Cargo/Go/Composer dependency declarations and exact-version pins.
- Exact-version package metadata is resolved only through fixed public registry hosts (npm, PyPI, crates.io). A version-specific SPDX 2.3 SBOM is emitted; unknown or free-form license declarations remain `NOASSERTION`, not guessed.
- Human license/asset-rights review remains mandatory. Registry metadata is not legal approval.

### 2.2 Customer Agent Studio → Chat → Agent Run

- Agent Studio loads the user's installed skills and only presents those with approved permissions and execution enabled.
- The customer selects up to 10 skill IDs; selected IDs flow through the existing app navigation state, Chat component and typed API client.
- FastAPI validates the request shape and sends skill IDs to the existing atomic chat enqueue RPC.
- The new Supabase RPC validates owner, installation, package validation, approved license, publication and permission state in the same transaction that inserts the message, attachments and durable Agent Run.
- Idempotency now binds the selected skill IDs as part of the run payload.

### 2.3 OpenManus resolver and audit

- Worker-side resolver is shared by Manus, ToolCall and the gated SWE runtime.
- It resolves only owner-scoped published, license-approved, validated and installed packages with approved permission and execution gates.
- Worker independently recomputes every stored file's Git Blob SHA-1 and SHA-256 before using skill instructions.
- Skill content is injected as explicitly untrusted reference context; it cannot override system policy or grant tools.
- Granted capability keys are translated into a per-run allowlist. Tool calls are independently checked before execution.
- Run snapshots are checkpointed; resolution and successful execution events are recorded in the skill audit ledger.
- Runtime remains disabled unless both `MOREAI_SKILL_RUNTIME_ENABLED=true` and `MOREAI_SKILL_RELEASE_GATE_PASSED=true` are explicitly configured and every package trust gate passes.

### 2.4 Reviewer UI and atomic audit

- Super Admin now includes an AI Skills Review tab.
- Reviewers can inspect source provenance, hashes, manifests, license evidence, dependency resolution and installation-specific permission requests.
- License/publication review and per-install permission decisions use transactional Supabase RPCs that commit the decision and audit record together.
- Permission review is scoped to one installation and grants only a subset of requested allowlisted permissions.
- Execution cannot be activated by the review UI alone; the independent server release gates remain required.

## 3. OpenFuse Connections Center

### 3.1 Google OAuth and credential lifecycle

- Added Authorization Code OAuth with PKCE S256, one-time hashed state, 10-minute expiry and callback URI matching.
- Scopes are explicitly selected and allowlisted for Gmail read/send and Calendar read/write.
- Google identity is verified before connection persistence.
- Access and refresh credentials are encrypted with AES-256-GCM and user-bound AAD. The encryption keyring supports versioned keys and lazy re-encryption on token access.
- Refresh-token preservation is handled when Google omits a new refresh token on reconnect.
- Disconnect revokes the Google token where possible, clears local ciphertext and records an audit event.
- No credential or provider secret is returned to the browser.

### 3.2 Gmail and Calendar operations

- Customer Connections Center lists connection status and granted scopes.
- Read-only Gmail metadata search and Calendar event listing are connected through FastAPI.
- Gmail send and Calendar event creation require explicit confirmation, owner-scoped OAuth scope and an Idempotency-Key.
- Side-effect receipts prevent accidental replay; ambiguous provider outcomes are marked unknown and are not automatically retried.
- OpenManus receives read-only `gmail_search` and `calendar_list_events` tools through a worker-to-FastAPI internal adapter. FastAPI binds the internal request to the actual running Agent Run owner before using credentials.
- Customer UI includes connection, Gmail read/send and Calendar read/create controls.

### 3.3 Required deployment configuration

Server-side environment values that must be configured before the integration can be used:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI`
- `MOREAI_CUSTOMER_APP_URL`
- `MOREAI_CONNECTIONS_ENCRYPTION_KEYS` and `MOREAI_CONNECTIONS_ACTIVE_KEY_VERSION`
- `MOREAI_WORKER_INTERNAL_TOKEN`
- `MOREAI_INTERNAL_API_URL`

The encryption keyring must be backed by a managed secret/KMS process in production. Retain old key versions until all stored credentials have been re-encrypted. The environment template documents the names; no secrets were added.

## 4. Main files changed

### Skills
- `apps/api/app/routers/skills.py`
- `apps/api/app/routers/admin.py`
- `apps/api/app/routers/conversations.py`
- `apps/worker/app/skill_resolver.py`
- `apps/worker/app/registry_factory.py`
- `engine/agents/durable_tool_runtime.py`
- `supabase/migrations/20261114102000_moreai_skill_source_files_and_audit.sql`
- `supabase/migrations/20261114103000_moreai_skill_aware_chat_enqueue.sql`
- `supabase/migrations/20261114104000_moreai_skill_atomic_ingestion_and_registry_audit.sql`
- `supabase/migrations/20261114105000_moreai_skill_package_review_rpc.sql`
- `components/views/skills-library-view.tsx`
- `components/views/agent-studio-view.tsx`
- `components/views/super-admin-view.tsx`
- `app/page.tsx`
- `lib/api/client.ts`

### Connections / OpenFuse adaptation
- `apps/api/app/routers/connections.py`
- `apps/api/app/main.py`
- `apps/worker/app/connection_tools.py`
- `apps/worker/app/registry_factory.py`
- `engine/tools/catalog.py`
- `engine/agents/durable_tool_runtime.py`
- `supabase/migrations/20261114106000_moreai_google_connections_center.sql`
- `supabase/migrations/20261114107000_moreai_connection_action_receipts.sql`
- `components/views/connections-center-view.tsx`
- `components/navigation/app-navbar.tsx`
- `types/moreai.ts`
- `lib/api/client.ts`
- `.env.example`
- `apps/api/requirements.txt`
- `apps/api/pyproject.toml`

## 5. Remaining blockers / work not claimed complete

1. Supabase migrations are committed but have not been applied. Until applied, the new API/RPC/table paths are not live.
2. Google OAuth client registration, redirect URI allowlisting, secrets and worker internal token must be configured in deployment.
3. Platform RBAC must grant `skills.registry.review` to the intended authorized platform reviewer role. The existing authorization layer enforces this permission; no broad admin bypass was added. The exact role/permission provisioning schema was not altered without an authoritative schema migration.
4. KMS/HSM envelope encryption and automated key rotation remain an infrastructure task; current API supports versioned AES-GCM keyring and lazy re-encryption.
5. Gmail send and Calendar create have explicit confirmation and idempotent receipts, but ambiguous external outcomes still require manual provider-side reconciliation.
6. Scenario Skills crawler is bounded to 40 files / 5 MiB per skill. It does not yet guarantee complete traversal of every external reference or repository-wide dependency tree.
7. NPM/PyPI/Cargo registry metadata is version-specific; Go/Composer/Pnpm/Yarn parsing and registry license resolution are partial. Exact transitive SBOM closure and vulnerability/license compatibility review remain open.
8. OpenFuse's full 219-path source inventory is not closed. Browser session lifecycle, download receipts, E2B/Docker execution parity, OAuth providers beyond Google, and all remaining worker/server routes still require file-by-file parity and security review.
9. Full customer dashboard route-by-route integration is not complete. Remaining screens and actions must be reconciled against the Master PRD and current API contract; no claim is made that every demo/simulated action has been removed.
10. The platform release gate remains closed; no runtime acceptance is claimed.

## 6. Current next phase

**Phase 09 continuation — Customer Dashboard API Completion & OpenFuse Capability Parity.**

Dependency order:
1. Apply the committed Supabase migrations in the canonical project when authorized.
2. Provision the narrowly scoped reviewer permission and server-side OAuth/internal worker secrets.
3. Finish remaining OpenFuse browser/download/worker capabilities and action receipts.
4. Audit each customer screen against its typed FastAPI endpoint; replace remaining simulated actions and remove unsupported controls without redesigning the protected UI.
5. Complete source-to-runtime evidence and release checks only when the owner authorizes tests/staging.

## 7. Validation boundary

This report documents committed source changes only. No build, test, lint, typecheck, browser session, live OAuth consent, Gmail/Calendar provider action, staging, deployment or Supabase mutation was performed.


## 8. Additional implementation after the first report revision

- OpenManus now has Gmail send and Calendar create tools in addition to read-only search/list tools.
- Both write tools are classified as critical/high-risk in the canonical tool policy and require the existing durable run-scoped approval gate before the adapter is invoked.
- Worker-to-FastAPI write requests are bound to an authenticated internal token and a currently running Agent Run owned by the same user.
- Write operations use deterministic run-and-payload idempotency keys and the shared connection action receipt ledger. Ambiguous provider outcomes are marked unknown and are not retried automatically.
- Skill permissions `gmail.send` and `calendar.write` map to those approval-gated tools; granting a skill permission does not bypass the approval gate.
- The Super Admin reviewer can now inspect actual source-controlled LICENSE/NOTICE/manifest contents, in addition to hashes and dependency metadata.
- Pinned source ingestion now includes repository-level LICENSE/NOTICE/COPYING files so skills that inherit repository licensing can be reviewed.
- Worker independently verifies the canonical Git Blob preimage and every source file's SHA-256 before injecting instructions.
- Skill instructions are appended as an untrusted user-context message, not concatenated into the system prompt.

These additions are committed on `main`. They do not change the validation boundary in Section 7: no live OAuth consent, provider action, migration application, tests, staging or deployment was performed.
