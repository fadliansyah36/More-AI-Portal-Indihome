# MOREAI Task 1 — Exact SQL Diff Batch Notes
Date: 2026-11-18
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main
Verified base HEAD at start: bd9608e2d7e1f1c02927fb1604817dc67d999d4f
Supabase project: uunfgimtokhucegqbpce (ACTIVE_HEALTHY, PostgreSQL 17.11)
Scope: read-only reconciliation. No migration apply, DDL, database write, staging, test deployment, or production deployment.

## Evidence sources
- AGENTS.md blob: ef31802dff84cf13739d2a1438bdf7a831a4792a
- Existing mismatch inventory: docs/implementation/MOREAI_SUPABASE_MIGRATION_SQL_MISMATCH_REVIEW_20261118.csv (blob b9fa9ba45e3e50a7ff236c7820312b8443b6bf2a)
- Existing corrected history report: docs/implementation/MOREAI_SUPABASE_MIGRATION_RECONCILIATION_REPORT_20261118.md (blob d5a0a046bbc4c762d2c0bf92e518ea3c00009839)
- Supabase live history read: supabase_migrations.schema_migrations, queried by the applied migration versions listed below.
- Repository migration SQL read from main by exact path; Git blob SHA values match the existing mismatch inventory.

## Exact-diff batch outcome
All 23 listed pairs were fetched from the live Supabase migration-history statements and current main-branch migration files. Raw content is different for every pair (the original inventory contains raw MD5s and Git blob SHAs). A line-oriented comparison was performed for all 23. The line comparator is diagnostic, not a SQL parser; a final semantic decision must be based on SQL tokens/statement structure and must account for quoted/dollar-quoted literals.

| Repo migration | Applied history version | Initial semantic disposition | Evidence / note |
|---|---|---|---|
| 20261111050000 moreai_tool_approval_lifecycle | 20261111061443 | UNKNOWN_REQUIRES_REVIEW | 58 history lines vs 117 repo lines; line layout and statement formatting differ substantially; full statement-level comparison still required. |
| 20261111103000 moreai_admin_partner_status_atomic_audit | 20261111083342 | UNKNOWN_REQUIRES_REVIEW | 55 history lines vs 106 repo lines; formatting and policy syntax differ in line representation; verify transaction/function body equivalence. |
| 20261111120000 moreai_explicit_server_only_rls_denials | 20261111112556 | FORMAT_ONLY | Differences are line wrapping of SELECT/FROM and format() arguments; same policy-name/table-name logic is visible in both. |
| 20261111180000 moreai_openmanus_approval_tool_keys | 20261111160343 | FORMAT_ONLY | Allowlist values and predicates match; line breaks and comments differ. |
| 20261112084047 moreai_auth_profile_provisioning_and_owner_update | 20261112084047 | FORMAT_ONLY | Same trigger, function, profile insert and own-profile policy logic; compact vs expanded formatting. |
| 20261113160000 moreai_customer_workspace_union_pagination | 20261113132826 | FORMAT_ONLY | Same workspace union/keyset pagination logic visible; comments and SELECT formatting differ. |
| 20261113170000 moreai_customer_workspace_file_lifecycle | 20261113133149 | FORMAT_ONLY | Expanded parameter/body formatting; continue token-level check of all function statements before final closure. |
| 20261113180000 moreai_customer_workspace_pagination_indexes | 20261113133346 | COMMENT_ONLY | Repository adds an explanatory comment and blank lines; SQL statements otherwise match. |
| 20261113190000 moreai_customer_workspace_restore_immutable_version | 20261113133453 | FORMAT_ONLY | Parameter and body formatting expanded; immutable version restore logic appears aligned. |
| 20261113200000 moreai_customer_workspace_delete_version_archive | 20261113133519 | FORMAT_ONLY | Comment and formatting changes; verify token equality in final review. |
| 20261113220000 moreai_worker_workspace_restore_immutable_version | 20261113133656 | FORMAT_ONLY | Parameter and body formatting expanded; verify token equality in final review. |
| 20261113230000 moreai_customer_workspace_restore_empty_file | 20261113133736 | FORMAT_ONLY | Comment and whitespace changes; comparison shows same predicates and operations. |
| 20261113240000 moreai_customer_learning_progress_pagination | 20261113134251 | FORMAT_ONLY | Function formatting expanded; query and owner scope appear unchanged. |
| 20261113250000 moreai_customer_knowledge_chunk_count | 20261113134544 | FORMAT_ONLY | Function formatting expanded; count and owner-check logic appear unchanged. |
| 20261114040000 moreai_customer_agent_configuration_capability_registry | 20261114034343 | UNKNOWN_REQUIRES_REVIEW | Grant syntax is consolidated in repo; full function body/privilege equivalence must be checked before final classification. |
| 20261115090000 moreai_agent_model_preferences | 20261115084819 | FUNCTION_OR_TRIGGER_CHANGE; EXECUTION_BEHAVIOR_CHANGE | Repo explicitly drops/recreates the configured chat enqueue function, adds p_attachment_ids, validates/deduplicates attachment IDs, checks attachment ownership/MIME/size/conversation, snapshots preferred model and attachment IDs, and persists attachment links. This is materially beyond the original history statement. Reconcile with intervening 20261115085314 attachment-compat history before final disposition. |
| 20261115110000 moreai_provider_configuration_and_route_types | 20261115092653 | FORMAT_ONLY (PROVISIONAL) | Route mutation and provider configuration function appear aligned; whitespace and formatting differ. Final token comparison remains required. |
| 20261115111000 moreai_provider_endpoint_allowlist | 20261115092950 | FUNCTION_OR_TRIGGER_CHANGE; EXECUTION_BEHAVIOR_CHANGE | Repo adds provider-specific host allowlist checks for OpenAI/Google adapter endpoints. This narrows accepted provider endpoints and is a behavior/security change; preserve as a substantive delta, not formatting. |
| 20261115130000 moreai_browser_action_receipts | 20261115095114 | FORMAT_ONLY | Only blank-line differences observed in line comparison. |
| 20261115131000 moreai_browser_action_receipt_action_types | 20261115095611 | COMMENT_ONLY | Repository adds an explanatory comment; SQL action-type constraint is unchanged. |
| 20261115132000 moreai_browser_session_close_requests | 20261115095839 | COMMENT_ONLY | Repository adds an explanatory comment; SQL status constraint is unchanged. |
| 20261115134000 moreai_browser_action_receipt_result_retention | 20261115100615 | FORMAT_ONLY | Function body and predicate are line-wrapped; same retention logic visible. |
| 20261115140000 moreai_computer_action_receipts | 20261115101318 | FORMAT_ONLY | Partial-index predicate and function formatting differ by line breaks only; same predicate and purge logic visible. |

## Duplicate SQL decision evidence
The five duplicate logical names in migration history were queried directly.

Three pairs have exact raw SQL equality:
- moreai_customer_learning_progress: versions 20261112044926 and 20261113002555; raw MD5 a14bb58a741ef8537711e22231fb3669; 2,521 chars each.
- moreai_knowledge_rag_vector: versions 20261112060109 and 20261113002601; raw MD5 db8a7fadb77e6acfa075f2f175e40fac; 4,499 chars each.
- moreai_workspace_file_cas_versioning: versions 20261111140238 and 20261111140255; raw MD5 1eaa6c05dbdc17ca0232536db4f3400e; 7,877 chars each.
Decision: CONFIRMED_DUPLICATE for each pair at the statement-content level. Retain both history records; do not delete or rewrite history.

Two pairs have different raw SQL but matching whitespace/comment-stripped hashes and were inspected:
- moreai_workspace_file_version_history: 20261112044816 (MD5 b0c9a73a0af4fd2366fe1cf20663f3f2, 2,538 chars) vs 20261113002544 (MD5 6f8955dd0ff761755808ba674306815f, 2,583 chars); normalized hash 13436a6452f6d1d5278a70cccdaa4435. The only visible deltas are blank lines and splitting a compound IF predicate across lines.
- moreai_workspace_restore_approval_key: 20261112044822 (MD5 459595e444f54d49ddb04866519869d5, 2,319 chars) vs 20261113002550 (MD5 256543cfe7c00e50d7c1cafd52b0920c, 2,501 chars); normalized hash 980d2670ce4d9c658c31dc51bf9e1fbc. The second adds comments and line wrapping; the allowlist, request validation, owner check, expiry update, selection and grants are unchanged.
Decision: SEMANTICALLY_EQUIVALENT (based on inspected SQL text and normalized equality). Retain both history records as historical variants; no canonical migration is deleted.

## Live schema inventory snapshot
Read-only catalog query returned:
- relations (tables/partitions/views/materialized views/foreign tables): 142
- functions: 332
- non-internal triggers: 19
- policies: 99
- extensions: 7
- enum/composite/domain types: 157

This is an inventory count only. It does not establish schema parity. Full definition-level comparison of columns, constraints, indexes, functions, triggers, RLS policies/grants, extensions, views/materialized views and enum/custom types remains outstanding.

## Task 1 blockers / remaining work
1. Finalize SQL token/statement-level comparison and impact assessment for all 23 pairs, especially the first two, 20261114040000, 20261115090000 and 20261115111000.
2. Reconcile 20261115090000 against intervening applied history 20261115085314 (attachment compatibility) and any exact deployed source evidence.
3. Complete full definition-level schema drift inspection; the counts above are not a schema drift report.
4. Complete five unapplied migration decisions with exact dependency, object-existence and owner-intent evidence. Do not apply them.
5. Verify all evidence references and produce the final Task 1 report only after these items close.

Task 1 status: IN_PROGRESS / REVIEW_REQUIRED. Not READY_FOR_REVIEW.
Task 2: NOT_STARTED (must not begin until Task 1 acceptance criteria are met).
P1 acceptance: BLOCKED.
P2 ADR: BLOCKED pending P1 acceptance.
Phase 04–09: NOT_STARTED under this execution gate.
