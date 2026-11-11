# MoreAI — Vercel Production Routing Fix

Date: 2026-11-11  
Vercel team: More AI (`team_wHMjZ5NapyaF8aYYVs4UUY36`)  
Vercel project: `more-ai-portal-indihome` (`prj_2ge37Xd5uBSUGhn3wPsaHfFcW1UV`)  
Git source: `fadliansyah36/More-AI-Portal-Indihome`, branch `main`  
Final deployed commit: `3219109f047f1a58a411970fc1c6071b06debb03`  
Deployment: `dpl_37tWK4zTmehTz8FZmQLwicmir6K8`  
Production URL: https://more-ai-portal-indihome.vercel.app

## What was found

- Vercel project binding was approved and is now accessible under the More AI team.
- Latest pre-fix production deployment was READY at commit `825b3bb99abed63551a815ea213fc07ee334785b`.
- Production runtime error query for the previous deployment showed no runtime errors in the preceding seven days.
- Vercel project had no environment variables configured. The browser Supabase client requires `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`; without them, its initialization threw. The route resolver defaulted to Splash, but the initialization catch forced every route to the Customer Login tab. This explains why the root/entry flow could skip Splash when Auth configuration was missing.
- Project used Node.js `26.x`. Vercel build logs showed an `EBADENGINE` warning for `superstatic@10.0.0`, which supports Node 20, 22 or 24 only.

## Changes applied

1. Vercel Node.js runtime changed to `24.x`.
2. Added browser-safe Supabase environment variables to Production, Preview and Development:
   - `NEXT_PUBLIC_SUPABASE_URL=https://uunfgimtokhucegqbpce.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (Supabase publishable key; no service-role secret exposed)
3. Updated `app/page.tsx` so Auth initialization/session errors preserve public Splash and Onboarding routes. Protected Customer routes still resolve to Customer Login, and protected Partner routes still resolve to Partner Login.
4. No visual components, styles, screen layouts, colors, or typography were changed.

## Deployment history

- Commit `7b781e0b5959647c208a9686d7e19a265801c795` — first fallback implementation. Its production build failed because the inserted path-normalization regex was malformed. This failed deployment was not promoted.
- Commit `3219109f047f1a58a411970fc1c6071b06debb03` — corrected path normalization using a slash-ending check and string slice. Vercel Production deployment `dpl_37tWK4zTmehTz8FZmQLwicmir6K8` reached READY.
- Successful Vercel build: Next.js 15.5.29; TypeScript validation passed; 17/17 static pages generated; all serverless functions created; build completed in approximately two minutes.
- Build lint step is configured to skip linting in `next.config.ts`; no claim of lint pass is made.

## Route verification

Vercel HTTP fetch returned status 200 for each direct URL:

- `/`
- `/splash`
- `/onboarding`
- `/customer/login`
- `/customer/register`
- `/partner/login`
- `/workflow`

The production build route table includes all seven paths, plus `/customer`, `/partner` and `/workflow-progress`. The production deployment aliases include `more-ai-portal-indihome.vercel.app`, `more-ai-portal-indihome-more-ai.vercel.app`, and the main-branch alias.

These checks establish successful build and HTTP route reachability. They are not a browser-driven interactive E2E test; client-side navigation, Auth sign-in, and post-login workflow rendering still need an authenticated browser session.

## Remaining deployment blocker: FastAPI origin

- Vercel currently has only the two Supabase browser Auth environment variables above.
- `NEXT_PUBLIC_MOREAI_API_URL`, `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` and `NEXT_PUBLIC_MOREAI_PARTNER_API_URL` are not configured.
- The current Vercel Next.js build route table contains `/api/gemini/chat`, but it does not contain the FastAPI `/api/v1/*` domain routes.
- Therefore the public UI and route shells are deployed, but Customer/Partner data calls and Workflow run/approval loading cannot be considered production-connected until a reachable FastAPI deployment origin is supplied and configured. Do not point these variables to the Next.js host or invent an API hostname.
- Server-only FastAPI environment variables and durable worker hosting are separate from the public web project and must not be placed in browser variables.

## Runtime / security notes

- Vercel runtime error scan for the latest deployment's project, last one hour: no runtime errors found.
- The project has SSO protection enabled for deployments except custom domains. Production aliases were checked and assigned without alias error.
- No service-role key or LLM provider secret was added to the frontend project.
- No authenticated browser E2E, signup/login, customer workflow, partner membership, API connectivity, worker execution, or LLM call was performed.
