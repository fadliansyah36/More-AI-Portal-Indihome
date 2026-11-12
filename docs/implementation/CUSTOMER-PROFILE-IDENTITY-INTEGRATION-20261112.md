# Customer Profile Identity and Greeting Integration — 2026-11-12

## Scope
Direct implementation on \`main\`, limited to the existing Customer identity/profile integration. No redesign, deployment, staging, real tests, migration or production mutation.

## Root cause found in source
1. \`components/views/profile-settings-view.tsx\` loaded the authenticated profile and notification preferences inside one \`Promise.all\`. A failure in the unrelated notification-preferences request rejected the entire operation, so the Profile screen showed a profile-load error even when the profile endpoint itself could succeed.
2. \`components/views/home-view.tsx\` replaced the greeting identity with the generic \`Pengguna MoreAI\` whenever the profile request failed. It did not use the registered \`full_name\` already submitted to Supabase Auth during registration.
3. \`apps/api/app/dependencies.py\` validated the Supabase Auth user but discarded the safe registered-name fields from \`user_metadata\`; consequently the identity endpoint had no Auth-metadata fallback when a profile row had an empty display_name.

## Changes
- \`apps/api/app/dependencies.py\`: derive a normalized display_name from Supabase Auth \`user_metadata.full_name\` or \`name\`; return only that scalar with id/email (never expose raw metadata).
- \`lib/api/client.ts\`: type the identity response's optional \`display_name\`.
- \`components/views/profile-settings-view.tsx\`: load profile identity independently from notification preferences. Notification-preference failure no longer masks a successful profile response. Prefer profile.display_name, then Auth registered display_name; show an explicit unset state rather than a fake user identity.
- \`components/views/home-view.tsx\`: use the shared typed \`profileApi.get()\`, prefer the Supabase-provisioned profile name, then Auth metadata name, then email local-part; preserve the existing supplied identity on a transient request error instead of resetting to a generic label.

## Commits
- API authenticated identity: \`3ea69daed8caf10322482042d9cd928de9a1a31f\`
- Profile resource isolation: \`b9ebfd71456359e5d25532c6d58ff4f07039ccaa\`
- Typed API identity contract: \`27966787443cd4ec2e1de4ab6e95ed40a627bc7c\`
- Customer greeting identity: \`f18280ac70b57e9a730ea51f0446bef9bf5dd33f\`

## Verification boundary
No test, lint, typecheck, build, API request, browser session, provider call, database mutation, staging or deployment was run, as explicitly instructed. The source-level coupling and missing metadata fallback are corrected; production Profile availability remains unverified and may still depend on API origin/CORS/runtime configuration.

## Remaining work
- Phase 08: complete upstream provider/model capability mapping, tool adapter parity, agent registry parity, file/PDF/URL ingestion and retrieval citations.
- Phase 06: finish versioned FastAPI schemas, auth/tenant enforcement, consistent errors, pagination/idempotency/correlation and OpenAPI contract coverage.
- Phase 09: reconcile every existing Customer screen against the real API and remove any remaining demo/fallback paths without changing visual UI.
- Phase 04/07 dependencies remain in progress; do not claim overall backend integration complete.
