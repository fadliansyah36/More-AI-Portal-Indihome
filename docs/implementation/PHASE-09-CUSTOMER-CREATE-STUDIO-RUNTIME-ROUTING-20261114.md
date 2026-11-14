# Phase 09 — Create Studio Runtime Routing Increment

Date: 2026-11-14  
Branch: `main`  
Implementation commit: `d741e657bae8cdd1bcb5525e00e01691ba24208f`

## Scope

Continue Customer Dashboard integration by making Create Studio handoffs select the actual OpenManus execution runtime instead of always relying on the default Manus agent. Existing screens, layout, styles, navigation and design tokens remain unchanged.

## Source findings

- The Customer Chat API accepts only the registered runtime keys `manus`, `planning`, and `toolcall`.
- The typed `customerApi.sendMessage` contract forwards the selected runtime key to FastAPI and uses an idempotency key.
- FastAPI validates the key and atomically enqueues the user message and durable Agent Run through the existing Supabase RPC.
- The Planning runtime persists a dependency-aware plan and executes steps through registered agent runtimes. It is the appropriate existing path for multi-step authoring tasks.
- Create Studio image generation has no verified media provider contract and remains unavailable. Video generation remains explicitly a text-only script/storyboard handoff; no rendered media is claimed.

## Implemented

- Added a runtime key to each Create Studio action.
- Routed document summarization, presentation planning and video storyboard tasks to the existing `planning` runtime.
- Routed straightforward text/document authoring and translation tasks to `manus`.
- Passed the selected runtime key through the existing `onNavigateToChat` handoff into Customer Chat, preserving the existing FastAPI enqueue and durable worker path.
- Corrected prompt handoff separators to actual newline characters, preserving task instruction and user prompt as separate readable sections.
- Left image generation fail-closed; no fake provider, media artifact or credit mutation was introduced.

## Files changed

- `components/views/create-view.tsx`

## Verification and deployment constraints

Per product-owner instruction, no tests, lint, typecheck, build, browser/API/worker runtime checks, provider calls, staging or deployment were run. This is a source-level implementation only. No Supabase migration or database mutation was performed.

## Remaining Phase 09 work

- Reconcile remaining Customer actions against real FastAPI contracts and backend capability registry.
- Complete safe manual retry/regenerate only after a durable retry contract is present; do not duplicate a prior message/run with a new client-side guess.
- Complete Customer Memory consent/review/correction/retention/deletion lifecycle.
- Continue full upstream backend capability parity and tool/LLM/provider routing reconciliation.
- Finish Customer integration before Phase 10. Phase 10 remains not accepted and Phase 11 remains blocked while verification/staging are disallowed.
