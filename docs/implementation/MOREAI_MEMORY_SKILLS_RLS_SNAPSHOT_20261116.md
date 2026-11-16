# MoreAI Memory / Skills / Worker RLS Snapshot — 2026-11-16

Read-only Supabase catalog query for project `uunfgimtokhucegqbpce`. No row data was read and no database state was changed.

## Observed policies

| Table | Observed policy | Roles | Command | Predicate |
|---|---|---|---|---|
| `moreai_customer_memories` | `moreai_customer_memories_owner_all` | authenticated | ALL | `user_id = auth.uid()` in USING and WITH CHECK |
| `moreai_customer_memory_preferences` | `moreai_customer_memory_preferences_owner_all` | authenticated | ALL | `user_id = auth.uid()` in USING and WITH CHECK |
| `moreai_skill_packages` | `moreai_skill_packages_server_only` | anon, authenticated | ALL | false |
| `moreai_skill_installs` | `moreai_skill_installs_server_only` | anon, authenticated | ALL | false |
| `moreai_skill_source_files` | `moreai_skill_source_files_server_only` | anon, authenticated | ALL | false |
| `moreai_browser_sessions` | `moreai_deny_client_moreai_browser_sessions` | anon, authenticated | ALL | false |
| `moreai_browser_action_receipts` | `moreai_deny_client_moreai_browser_action_receipts` | anon, authenticated | ALL | false |
| `moreai_computer_action_receipts` | `moreai_deny_client_moreai_computer_action_receipts` | anon, authenticated | ALL | false |
| `knowledge_documents` | `knowledge_documents_server_only` | anon, authenticated | ALL | false |
| `knowledge_chunks` | `knowledge_chunks_server_only` | anon, authenticated | ALL | false |
| `agent_runs` | `agent_runs_deny_client_access` | anon, authenticated | ALL | false |
| `agent_run_events` | `agent_run_events_deny_client_access` | anon, authenticated | ALL | false |
| `notifications` | `notifications_server_only` | anon, authenticated | ALL | false |

## Architecture implications

1. The live catalog currently allows authenticated owner-scoped direct SQL access to customer memory tables under RLS. This is not evidence that the browser actually uses direct CRUD. However, AGENTS.md requires browser business data/actions to go through FastAPI and Supabase Auth to be the only direct browser Supabase capability. P3 must inspect and remove any browser-side memory data access path in source; do not weaken RLS to accomplish this.
2. Skills, skill source files, knowledge/RAG, browser sessions, browser/computer receipts, Agent Runs/events and notifications are server-only for anon/authenticated at the policy layer. Customer UI must consume their owner-scoped FastAPI projections.
3. The listed owner memory policies include both USING and WITH CHECK predicates. Preserve owner binding and consent checks in API/service logic as well as database defense in depth.
4. This query inspected `pg_policies` only. It does not establish grants, function EXECUTE exposure, SECURITY DEFINER safety, Storage policies, or absence of other policies on unlisted tables. Those remain in the full security audit.

## P3/P4 follow-up before code changes

- Inspect memory service/router and frontend call sites to establish the actual path used by Customer Memory UI and OpenManus context assembly.
- Map existing `source_type`, `scope`, `expires_at`, and source metadata into the six PRD memory types without conflating personal memory, conversation memory, RAG knowledge or procedural skills.
- Confirm consent withdrawal/clear behavior, retention, deletion propagation, retrieval authorization and source provenance.
- Inspect skill registry import/review/publish/install/execution code against the existing server-only policies. Imported skill text and referenced files remain untrusted data; only the MoreAI permission resolver can grant capabilities.
- Do not create new tables or migrations until source/service/RPC/index/RLS reconciliation proves a missing contract. No migration is applied in the current workstream.
