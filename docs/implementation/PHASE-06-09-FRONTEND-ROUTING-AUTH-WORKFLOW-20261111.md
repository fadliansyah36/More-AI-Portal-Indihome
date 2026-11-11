# MoreAI Frontend Route, Authentication & Workflow Integration
Date: 2026-11-11
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main (direct commits only)

## Product-owner issue
The Workflow route returned to the home screen. The product owner also asked whether the existing frontend was connected to OpenManus and whether Login/Register were implemented. The prior state was incomplete: the app was primarily a single root client page with ephemeral tab state; direct deep-link routes were absent. Customer Chat was connected to Customer FastAPI endpoints, but this did not mean every UI screen was integrated. Customer Auth used Supabase Auth, while Partner Login still used fabricated credentials and a fake success message.

## Root cause and implementation

### Routing
- Added Next.js route entry points:
  - `/workflow` and `/workflow-progress`
  - `/login`
  - `/register`
  - `/partner/login`
- These route entry points forward to the existing root Next.js application with a selected view. They do not introduce an alternate frontend or change the UI hierarchy.
- Root navigation writes browser history and restores selected views from direct URL and back/forward navigation.
- Protected workspace screens require an existing Supabase Auth session; unauthenticated direct visits are sent to Login.
- Auth state changes are observed so a signed-out session returns to Login.

### Authentication
- Customer Login/Register continue to use Supabase Auth directly (the only allowed direct browser-to-Supabase operation).
- Password recovery now calls Supabase `resetPasswordForEmail`; the previous fabricated “email sent” toast was removed.
- Partner Login no longer uses seeded demo credentials or a fake success state. It signs in with Supabase Auth, then calls `GET /api/v1/partner/tenants`. A user is admitted to the Partner UI only when an active membership is returned.
- Partner applicant Auth metadata is not treated as authorization. A partner tenant, role or membership can only be granted by the server-side membership system.

### Existing UI → FastAPI → OpenManus
- Workflow progress reads actual persisted Customer Agent Runs through `GET /api/v1/customer/agent-runs`.
- Tasks view now lists actual agent-run records instead of seeded tasks; local-only task completion toggles were removed.
- Agent Studio reads enabled agents from `GET /api/v1/agents`; disabled/unavailable agent catalog states are explicit.
- Selecting an agent sends its supported key (Manus or Planning) into the Customer Chat request; the selected agent is no longer merely decorative.
- Home identity reads `GET /api/v1/me`; fabricated sample identity and “Partner ISP 100M” status badge were removed.
- Artifact-result view reads owner-scoped metadata from `GET /api/v1/artifacts`; Files view already used this API. No fake download success is displayed.

## Data flow
```
Browser UI
  ├─ Supabase Auth only: sign-in / sign-up / session / password recovery
  └─ typed lib/api/client.ts
       └─ FastAPI (Bearer JWT validation)
            ├─ Customer principal → owner-scoped conversations / agent_runs / artifacts
            ├─ Partner principal → active membership → tenant-scoped Partner endpoints
            └─ worker queue → OpenManus agent runtime → durable Supabase run/checkpoint/event state
```

## Files changed
- `app/page.tsx`
- `app/workflow/page.tsx`
- `app/workflow-progress/page.tsx`
- `app/login/page.tsx`
- `app/register/page.tsx`
- `app/partner/login/page.tsx`
- `components/views/auth-login-view.tsx`
- `components/views/partner-login-view.tsx`
- `components/views/workflow-progress-view.tsx`
- `components/views/tasks-view.tsx`
- `components/views/agent-studio-view.tsx`
- `components/views/chat-view.tsx`
- `components/views/home-view.tsx`
- `components/views/artifacts-result-view.tsx`
- `lib/api/client.ts`
- `docs/implementation/PHASE-TRACKER.md`
- `docs/implementation/openmanus-backend-capability-map.json`

## Explicitly not complete
- This increment does NOT complete Phase 04. Worker approval pause/resume and atomic consumption, sandbox supervisor dispatch, browser isolation/SSRF/DNS rebinding, isolated file execution and remaining upstream parity remain open.
- This increment does NOT complete Phases 06–08. Full domain API/OpenAPI contracts, durable worker concurrency/lease fencing and all upstream provider/tool/flow adapters remain open.
- This increment does NOT complete Phase 09. Wi-Fi, captive portal, vouchers, credits/ledger, analytics, education, notifications, profile mutations, all Partner operational screens and signed artifact downloads still need real backend endpoints and UI integration. No fabricated fallback data should be reintroduced.
- Partner venue application is not a self-service tenant-creation flow. Auth signup alone does not grant Partner membership; administrator-issued membership is still required.
- LLM execution remains subject to the existing provider/entitlement/worker feature gates.

## Verification and UI preservation
- Per explicit instruction, no tests, lint, typecheck, build, browser smoke, screenshot capture, SQL apply or runtime checks were run.
- No new verification pass is claimed. Existing historical CI runs predate this increment and do not validate these changes.
- UI changes were limited to replacing fabricated data/actions with API-backed states and adding route entry points; the existing screen layout was retained. Before/after screenshots are unavailable because the owner instructed to skip checks and capture.
- No deployment was performed.

## Phase status
- Phase 04: IN PROGRESS.
- Phase 06: IN PROGRESS.
- Phase 07: IN PROGRESS.
- Phase 08: IN PROGRESS.
- Phase 09: IN PROGRESS — workflow/auth/agent/artifact subset connected.
- Phase 10: BLOCKED (verification intentionally skipped and real provider E2E deferred).
- Phase 11: NOT STARTED.

## Next implementation sequence
1. Complete worker approval pause/resume + atomic consume.
2. Integrate sandbox supervisor and browser/file isolation; keep tools default-deny until actual enforcement is wired.
3. Complete upstream agent/flow/tool/API parity and update capability map.
4. Finish FastAPI/OpenAPI and durable worker contracts.
5. Connect each remaining existing UI screen to real endpoints and remove static/demo business data.
6. Phase 10 and 11 remain release gates and must not be marked complete without required evidence.
