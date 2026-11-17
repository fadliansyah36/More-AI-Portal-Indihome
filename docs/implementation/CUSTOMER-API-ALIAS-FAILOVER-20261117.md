# Customer API Alias Failover — 2026-11-17

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Parent baseline: `835afbc1f937b3ceb5309593e256bbd044f09a5b`
Implementation commit: recorded by Git history after this report is committed.

## Scope
Correct the existing typed frontend API transport's safe-read fallback between the two verified Vercel aliases for the same FastAPI project.

## Evidence and change
- Frontend production configuration is documented as using `https://more-ai-api-more-ai.vercel.app`.
- The API project also has the alias `https://more-ai-api.vercel.app`.
- Before this change, `fetchMoreAiApi` retried GET/HEAD only when the configured base URL was exactly the secondary alias. The canonical configured alias therefore had no fallback path.
- The fallback constant was changed to the secondary alias.
- Safe GET/HEAD transport failures now select the other alias based on the configured base URL.
- Only a transport-level `TypeError` triggers fallback. HTTP responses, authentication failures and business errors are not retried.
- POST/PATCH/PUT/DELETE are never replayed to another origin, avoiding duplicate mutations.
- Existing Supabase browser access remains limited to Auth session retrieval/refresh. No business-data access path changed.

## Files changed
- `lib/api/client.ts`

## UI and architecture preservation
- No UI component, route, CSS, typography, token, navigation or design-system file changed.
- FastAPI remains the business API boundary.
- Supabase remains canonical persistence.
- No alternate backend or database was introduced.

## Verification and deployment
- Per owner instruction, no tests, lint, typecheck, build, browser/API probe, worker execution, staging, migration, provider call or deployment was run.
- This commit is a source-level API transport correction only. It does not prove that either alias currently responds successfully or that Customer API runtime is healthy.
- Production deployment was not triggered.

## Remaining blockers
- Full per-action Customer frontend ↔ FastAPI contract reconciliation remains open.
- OpenManus backend parity and Phase 04 security gates remain open.
- Durable worker lifecycle acceptance remains open.
- Provider/model/tool/orchestration readiness remains open.
- Six-type Memory and Skill Registry/source governance remain in progress; source presence is not runtime acceptance.
- Phase 10 and Phase 11 remain NOT ACCEPTED because real verification is prohibited.

## Next
Continue the Customer API action-to-route reconciliation and resolve any contract mismatches in source. Then continue Phase 04/05/06/07/08 dependencies and complete Phase 09 source integration. Do not claim phase completion or deploy without the required evidence and release gates.
