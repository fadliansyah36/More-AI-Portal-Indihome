# MoreAI — Customer Profile and Analytics API Integration
Date: 2026-11-11
Branch: main
Repository: fadliansyah36/More-AI-Portal-Indihome

## Scope and rationale
This increment binds existing Customer Profile/Settings and Analytics views to existing authenticated FastAPI contracts. UI layout and navigation were retained; only data sources and state handling were changed.

## Implemented
1. Profile identity
   - Loads `/api/v1/me` using the shared authenticated API client.
   - Displays profile display_name and authenticated account email instead of hardcoded demo identity.
2. Notification preferences
   - Loads `GET /api/v1/notifications/preferences`.
   - Persists in-app notification toggle using `PUT /api/v1/notifications/preferences`.
   - Shows API failure feedback and does not optimistically claim persistence.
3. Customer analytics
   - Loads authenticated usage records through `customerApi.usage(100)`.
   - Period filters calculate 7/30/365-day views from returned usage timestamps.
   - Activity count, token volume, successful usage count and recorded cost are derived from API records.
   - Removed the previously illustrative SVG trend chart because no historical aggregation contract exists yet; UI now states this limitation rather than displaying invented trends.

## Commits
- `57b1d4764f09e4e14c3a2fbba3805eea595fc078` — profile and notification preferences.
- `ee1298b4c97623397e95e6ba1f7a1e1c0020f937` — analytics API binding.
- `122b00c3825777d53be7ce24b88019f5b371a22e` — remove illustrative analytics chart.

## Verification boundary
No test, lint, typecheck, build, browser screenshot, API runtime call, migration, or deployment was run. These changes are source-level integration only and are not runtime accepted.

## Open integration work
- Customer Wi-Fi, connected devices, Captive Portal and voucher flows: backend contracts/gateway integration must be implemented before these screens can become real. Existing static device/network/voucher content must not be presented as live data.
- EduTech: course catalog, lesson progress and completion/certification APIs are not yet evidenced.
- Partner: wire existing screens to locations, networks, campaigns, members, access codes/redemptions and sessions. Backend CRUD coverage is partial; read/write permission matrices and ownership checks need complete review.
- Super Admin: existing APIs include overview, partner list/status, agent runs and audit, but the UI must be wired and each action checked against permission-specific dependencies.
- OpenManus and durable worker: complete all upstream capability parity, provider configuration/fallback, memory/RAG, Flow/server/session/tools and durable lifecycle. Current worker registry still gates several tools.
- Supabase: continue schema/RLS reconciliation for the missing product domains; do not create client-side direct business-data access or expose service-role credentials.

## Phase status
Phase 09 remains IN PROGRESS. This increment does not satisfy full integration or release acceptance.
