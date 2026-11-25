# MoreAI live schema evidence snapshot — 2026-11-25

## Scope and method

Read-only inspection of Supabase project `uunfgimtokhucegqbpce` and the repository migration directory on branch `main`. No database mutation, migration apply, staging, provider call, test execution or deployment was performed.

Project metadata at inspection:
- Project status: `ACTIVE_HEALTHY`
- PostgreSQL engine: 17
- Reported database version: `17.11.0.011`
- Region: `ap-southeast-2`

## Migration history reconciliation

- Active repository SQL migration files: **121**
- Supabase migration-history rows: **116**
- Repository versions absent from Supabase migration history:
  - `20261116162500`
  - `20261116162600`
  - `20261116162700`
  - `20261116162800`
  - `20261116163000`
- Supabase migration-history versions without a matching active repository SQL filename: **0**

These five source-only versions are the corrected browser migration IDs from the 2026-11-18 source recovery. Their absence from the migration-history listing means they are not recorded as applied. Do not apply them as part of this evidence collection. The migration-history table is not an independent exact-byte deployment receipt; execution provenance remains unverified without matching statement/deployment evidence.

## Current observed catalog counts

The following counts are global across non-system namespaces (not restricted to `public`), and therefore include Supabase-managed application-adjacent schemas:

| Catalog surface | Observed count |
|---|---:|
| Relations (table/partition/view/materialized view/sequence/foreign table) | 146 |
| Functions/procedures | 332 |
| User-defined composite/domain/enum/range/multirange types | 157 |
| Non-internal triggers | 19 |
| RLS policies | 99 |
| Default ACL rows | 27 |
| Role membership rows | 24 |

ACL-bearing object counts:
- Relations with non-NULL `relacl`: 144
- Functions with non-NULL `proacl`: 312
- Types with non-NULL `typacl`: 0
- Schemas with non-NULL `nspacl`: 10

Typed `pg_depend` edge counts:
- Relation objects: 796
- Relation references: 2,949
- Function objects: 776
- Function references: 193
- Type objects: 356
- Type references: 409

RLS policy modes:
- Permissive: 62
- Restrictive: 37

Default ACL owner/schema/object-type rows include `postgres`, `supabase_admin`, and `supabase_auth_admin` across `public`, `storage`, `auth`, `graphql_public`, `extensions`, `graphql`, `realtime`, and `cron`. These rows must not be treated as MoreAI-owned policy without namespace/owner scope filtering.

## Reconciliation status

This is a fresh observed-catalog count snapshot, not a complete expected-versus-observed semantic reconciliation. Counts do not prove object-definition equivalence, effective privileges, dependency binding, migration execution, or RLS correctness. The full semantic comparison remains `NOT_VERIFIABLE` until:
1. The expected graph is regenerated from all current active migrations and the approved historical source set using the repository's pinned parser.
2. Full object definitions, ownership, ACL expansion/grantor chains, policies, triggers, constraints and typed dependency edges are captured with schema-qualified identities.
3. Expected source lineage is compared against observed catalog definitions without treating migration-history rows as execution receipts.
4. Supabase-managed namespaces are separated from MoreAI application-owned namespaces.

A subsequent aggregate catalog query joining multiple catalog families exhausted the database temporary-file quota and was discarded; no state change occurred. Do not use that failed query as evidence. Prefer bounded, per-catalog read-only queries.

## Source and evidence limitations

- No local reconciliation generator was executed in this workstream; test execution is prohibited by the active Master PRD Section 37.
- The five browser source corrections remain unapplied and must not be auto-applied.
- This snapshot does not advance Task 1 to READY_FOR_REVIEW or ACCEPTED.
