# Task 1 — Duplicate SQL Decision Report
Date: 2026-11-18
All historical records and repository files are retained.

## Historical duplicate logical names

| Logical migration name | History versions | Raw SQL MD5 | Decision | Rationale |
|---|---|---|---|---|
| moreai_customer_learning_progress | 20261112044926; 20261113002555 | a14bb58a741ef8537711e22231fb3669 | CONFIRMED_DUPLICATE | Exact raw SQL content, 2,521 chars each |
| moreai_knowledge_rag_vector | 20261112060109; 20261113002601 | db8a7fadb77e6acfa075f2f175e40fac | CONFIRMED_DUPLICATE | Exact raw SQL content, 4,499 chars each |
| moreai_workspace_file_cas_versioning | 20261111140238; 20261111140255 | 1eaa6c05dbdc17ca0232536db4f3400e | CONFIRMED_DUPLICATE | Exact raw SQL content, 7,877 chars each |
| moreai_workspace_file_version_history | 20261112044816; 20261113002544 | distinct raw MD5s; normalized hash 13436a6452f6d1d5278a70cccdaa4435 | SEMANTICALLY_EQUIVALENT | Differences are whitespace/line wrapping; table, constraints, index, function and trigger behavior match in the reviewed SQL |
| moreai_workspace_restore_approval_key | 20261112044822; 20261113002550 | distinct raw MD5s; normalized hash 980d2670ce4d9c658c31dc51bf9e1fbc | SEMANTICALLY_EQUIVALENT | Comments/formatting differ; allowlist, validation, ownership, expiry and grants match |

Decision: retain all duplicate history rows. Do not delete, merge, rename or rewrite historical sources. The three exact duplicates are CONFIRMED_DUPLICATE at the statement-content level; the other two are SEMANTICALLY_EQUIVALENT historical variants.

## Repository duplicate source pair — model preferences

- `supabase/migrations/20261115090000_moreai_agent_model_preferences.sql`
- `supabase/migrations/20261115100000_moreai_agent_model_preferences_attachment_compat.sql`
- Both have Git blob SHA `86c53087c128b6a867bc462f4b3671ad716ea048` and 5,956 bytes.
- Their SQL MD5 `561ec2dfb21f2e7d74ad4a8ebf0ea4d5` exactly matches applied history `20261115085314_moreai_agent_model_preferences_attachment_compat`.
- The repository file named `20261115090000_moreai_agent_model_preferences.sql` is therefore a duplicate/misnamed alias of the later attachment-compat SQL, not the original applied `20261115084819_moreai_agent_model_preferences` migration. The original history statement (MD5 `9f5254d8a2749d42f512de381d22b68c`, 3,480 chars) adds `preferred_model_id` and its partial index and differs from the repo file.
- Decision: CONFIRMED_DUPLICATE for the two repository file contents; canonical source identity is the attachment-compat migration `20261115100000` / applied history `20261115085314`. Keep the duplicate `20261115090000` file untouched pending owner-approved disposition. The missing original source for history `20261115084819` remains a separate provenance blocker.

## Applied-content alias — durable run event outbox
- Repository-only `20261111110000_moreai_durable_run_event_outbox.sql` has exact SQL content matching applied history `20261111091531_moreai_durable_run_event_outbox_phase_07a` (historical source SHA-256 5a4da40e3a2c1c8a484e80a6dccb23c8a4000baad38422545deffdf82949a48e).
- Decision: DUPLICATE_OR_SUPERSEDED content alias; do not apply it again.


## Addendum — recovered historical source for 15084819 (2026-11-18)

The original 15084819 SQL source is now available in Git history at commit `cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31`, path `supabase/migrations/20261115090000_moreai_agent_model_preferences.sql`, blob `b7278df23425678a3009cb5c15f20e7c6cf53327`. Its 619 ordered SQL lexical tokens match history version 15084819. This does not change the duplicate decision for the current main files: current 15090000 and 15100000 remain identical attachment-compat aliases matching history 15085314. Preserve all representations; no cleanup is authorized.
