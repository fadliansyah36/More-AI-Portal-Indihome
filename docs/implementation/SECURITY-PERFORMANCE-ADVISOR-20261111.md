# MoreAI — Security & Performance Advisor Review
Date: 2026-11-11
Project: `uunfgimtokhucegqbpce` (MoreAIdb)
Repository target: `main`

## Scope
Read-only review of the canonical Supabase Security and Performance Advisors after the explicit server-only RLS policy remediation. No staging, runtime test, provider call, production data write, or schema mutation was performed in this review.

## Security result
The Security Advisor currently returns one finding:
- `auth_leaked_password_protection` — WARN, externally facing. Supabase Auth leaked-password protection is disabled. Enable it in Supabase Dashboard → Authentication → Security and password settings (exact labels may vary), then refresh the Security Advisor.

This setting is Auth project configuration, not a Postgres policy or SQL migration. The connected Supabase tools available in this session expose project/schema/advisor operations but no Auth password-security configuration setter. It was therefore not changed, and must not be reported as resolved.

## Performance result
The Performance Advisor currently returns:
- `unindexed_foreign_keys`: 53 findings.
- `unused_index`: 34 findings.

The advisor output included examples across `admin_audit_logs`, `agent_runs`, `agent_tool_approvals`, `artifacts`, `conversation_messages`, `credit_reservations`, `llm_request_records`, `network_sessions`, `partner_access_codes`, `notifications`, and other platform tables.

### Remediation decision
No indexes were added or removed in this review. The unindexed-FK findings must be reconciled against the complete index catalog, column order, partial predicates, uniqueness, and existing composite indexes before DDL. The unused-index signal is workload-statistical and can be misleading after low-traffic or recently reset statistics; dropping indexes without workload evidence could regress production. Treat both sets as a prioritized review queue, not as permission for blind mass DDL.

Recommended next pass:
1. Export the complete 53 FK findings and compare each FK column tuple with existing valid indexes (leftmost-prefix coverage).
2. Draft additive `CREATE INDEX CONCURRENTLY` operations only for genuinely uncovered FK tuples; apply through an operationally safe migration procedure compatible with Supabase migration constraints.
3. Correlate the 34 unused-index findings with index size, table write volume, query plans and a representative observation window before considering any removal. Do not drop indexes as part of this integration increment.
4. Re-run advisors after approved index changes.

## Integration status
The repository's Phase 04, 06, 07, 08 and 09 remain in progress. The existing approval pause/decision/consume path and durable worker event publisher are present in source, but this review does not establish runtime operation or end-to-end acceptance. Browser execution remains default-deny until the actual network isolation boundary is deployed and verified. Existing MoreAI UI remains the product frontend; no UI files were changed.

## Execution constraints
- Work target remains `main`; no branch created.
- No staging or real-world tests, no provider calls, no production data writes, no migration, no build/lint/typecheck, and no deployment were run.
- Advisor responses are read-only findings, not proof of workload performance or phase completion.

## Next implementation order
1. Phase 04: complete upstream Flow/server/session parity and close isolated SWE/browser supervisor gaps; keep unsafe tools disabled until deployment and security gates.
2. Phase 07: finish durable pause/resume, event retry/recovery and cancellation lifecycle.
3. Phase 08: close provider/tool/memory/RAG/structured call and per-tool metering parity.
4. Phase 06: finish remaining Customer, Partner, Super Admin, Wi-Fi/captive portal/voucher/credit/ledger/entitlement/analytics contracts.
5. Phase 09: wire existing UI screens through typed FastAPI clients without replacing the MoreAI UI.
6. Auth configuration: enable leaked-password protection in Supabase Dashboard; reconcile advisor FK/index findings before any DDL.
