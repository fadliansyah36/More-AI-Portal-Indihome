# Phase 09D — Browser session lifecycle and customer dashboard continuation

Date: 2026-11-16  
Branch: `main`

## Implemented in this increment

- `apps/api/app/routers/browser_sessions.py`: TTL/idle expiry is durably queued as `close_requested`; acquire-time expiry now also queues physical cleanup instead of prematurely marking the database row expired and leaving a possible OpenFuse profile behind.
- `apps/worker/app/main.py`: existing close reconciliation loop polls expiry work and then consumes eligible close requests. The worker asks the isolated OpenFuse supervisor to close the browser session and acknowledges completion through FastAPI.
- `supabase/migrations/20261116100000_moreai_browser_session_close_event_constraint.sql`: allows the durable `close_requested` event in the session event constraint.
- `components/views/code-view.tsx`: added a compact Browser Sessions & Activity panel using existing FastAPI customer API methods. It displays active/close-requested sessions, origin host, created/last-used/expiry timestamps, customer close action, and recent Browser action receipts. It reuses existing Tailwind classes, typography, border, red action and status conventions; no global style/token changes.
- Existing typed client methods in `lib/api/client.ts` are reused; no browser-to-Supabase data access was added.

## UI change gate

Baseline route/component: existing Code Assistant & Sandbox screen, `components/views/code-view.tsx`. The exact missing behavior was customer visibility and control of persistent OpenFuse sessions and browser action receipts. The smallest addition is one panel in the existing screen. No existing navigation, page hierarchy, layout shell, typography system or global styling was changed. Before/after screenshots were not captured because the user prohibited real testing/staging and no browser runtime was used.

## Lifecycle data flow

Customer UI → typed `customerApi` → FastAPI customer browser-session endpoints → canonical Supabase metadata/receipts. Worker-only expiry/close endpoints require the internal worker token. Worker → isolated OpenFuse supervisor → FastAPI close acknowledgement. Customer close requests remain durable until the supervisor reports physical close.

## Skills Governance status

The existing pinned-source inventory already captures nested license/NOTICE files, dependency manifests, exact versions where parsable, registry license metadata, SPDX 2.3 package/file records and SHA-256 checksums. Unresolved versions/licenses, unsupported registry metadata and binary asset rights remain review findings; publication remains blocked unless the existing review RPC prerequisites are satisfied. No blanket approval or automatic license compatibility claim was added in this increment.

## Not completed / external blockers

- OpenFuse browser profile persistence and state export/import contract is not established by the current supervisor adapter. The API's encrypted storage-state field must not be represented as a working restore mechanism until the isolated service exposes a verified compatible contract.
- Key rotation, orphaned profile deletion, malware scanning and download import remain open.
- Persistent worker/browser service configuration, private egress proxy and secret readiness remain operational prerequisites.
- No evidence of actual worker heartbeat, OpenFuse session closure or production data persistence is claimed.
- Skill dependency resolution is currently bounded and does not prove complete transitive closure, vulnerability status, legal compatibility or asset/trademark rights.

## Verification policy

Per product-owner instruction, no tests, lint, type checks, builds, browser/API/worker/Docker runtime calls, provider calls, staging or deployment were performed. This is a source-change report only.

## Next implementation work

1. Establish the exact pinned OpenFuse storage-state/profile lifecycle contract and wire encrypted save/restore only against supported endpoints.
2. Implement orphaned profile reconciliation with durable ownership mapping and safe deletion acknowledgement.
3. Extend customer session UI to show closed/expired historical sessions and event timeline when the API projection supports them.
4. Complete skill dependency lockfile parsers and reviewer-supplied license/asset evidence before publication.
5. Continue mapping remaining customer dashboard routes to existing FastAPI contracts and add only missing UI integration seams.
