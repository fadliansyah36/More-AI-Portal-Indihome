# MoreAI Customer Authentication Hardening
Date: 2026-11-12
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Implemented
- Registration now collects full name, email and password only; phone/WhatsApp is removed from the signup payload and user metadata.
- Login now accepts email only and uses Supabase Auth password sign-in. The former email-or-phone fallback has been removed.
- Email is trimmed and normalized to lowercase; email and full name are validated before submission.
- Registration enforces a 12–128 character password with lowercase, uppercase, numeric and symbol characters. Password values are never logged.
- Duplicate submissions are blocked while a request is in progress. Auth errors are normalized to safe Indonesian messages; rate-limit errors are surfaced without leaking provider internals.
- Signup enters the success path only when Supabase returns an active session. A null session is explicitly treated as an Auth configuration blocker.
- Next.js and FastAPI responses receive baseline security headers. FastAPI mutation routes reject untrusted Origin values and cross-site Fetch Metadata requests. CORS remains a separate allowlist gate with credentials disabled.
- A database trigger provisions one profiles row transactionally after each Auth user is created. It sanitizes untrusted full-name metadata, uses a fixed search path, resides in non-exposed auth_private, and revokes direct function execution.
- profiles_update_own permits authenticated users to update only their own row using both USING and WITH CHECK.
- Existing Auth users are backfilled without overwriting existing profile data.

## Canonical Supabase change and verification
Project: uunfgimtokhucegqbpce (MoreAIdb).
Applied migration: 20261112084047_moreai_auth_profile_provisioning_and_owner_update.
Verified live: auth.users trigger exists; trigger function is in auth_private and SECURITY DEFINER with empty search_path; profile owner UPDATE policy exists; existing users are backfilled with ON CONFLICT DO NOTHING.

## Required Supabase Dashboard setting — not changeable with the connected database tool
1. Open Supabase Dashboard for project uunfgimtokhucegqbpce.
2. Go to Authentication > Sign In / Providers > Email.
3. Turn Confirm email OFF and save.
4. Keep email/password sign-in enabled.
When Confirm Email is disabled, Supabase Auth implicitly confirms new email addresses and returns both user and session from signup. This is a project-level Auth configuration, not a PostgreSQL setting. Connected Supabase tools do not expose the Auth provider configuration/Management API, so this setting has not been changed here.

## Security coverage and boundaries
- SQL injection: database access remains behind parameterized PostgREST/API operations; never concatenate raw user values into SQL. RLS is defense in depth.
- CSRF/XSRF: app API uses explicit Bearer Authorization headers, strict CORS allowlists, Origin checks and Fetch Metadata checks for state-changing routes. This does not replace XSS prevention.
- XSS: baseline no-sniff/frame/referrer/permissions/HSTS headers are added. A strict nonce-based CSP needs a separate audit of inline scripts/styles and third-party integrations before enforcement.
- Rate limiting: Supabase Auth native rate limits remain authoritative for direct sign-up/sign-in. Configure project Auth limits and CAPTCHA/Turnstile in Supabase Auth settings; an in-browser timer is not a security boundary.
- Password protection: application complexity checks are added. Supabase Security Advisor reports Leaked Password Protection is disabled; enable it in Authentication > Attack Protection > Leaked Password Protection.
- Prompt injection is not an authentication attack. Treat user/agent/web/document content as untrusted instructions and enforce tool/network authorization server-side.
- URL validation and SSRF are handled at the backend/browser egress boundary; auth form validation does not provide SSRF protection.
- Sessions: keep short-lived access tokens, refresh-token rotation and server-side authorization checks. Never trust user_metadata for roles or permissions.

## Verification status
- Live migration apply successful; trigger metadata query successful; migration version 20261112084047 present.
- Frontend CI/build and browser login/register E2E pending latest commit.
- Real signup/login smoke test pending because Confirm Email must first be disabled in the Supabase Dashboard. No production user account was created as part of this change.

## Next
After the dashboard toggle is saved, run one controlled registration and login E2E test, verify profile creation, then enable leaked-password protection and configure Auth rate limits/CAPTCHA. Keep the existing customer UI layout and styling unchanged apart from removing the phone field.