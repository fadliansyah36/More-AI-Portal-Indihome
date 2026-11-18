# Task 1 — Static expected schema baseline and object reconciliation

As-of: 2026-11-18 (UTC). Repository: `fadliansyah36/More-AI-Portal-Indihome`, branch `main`. Supabase project: `uunfgimtokhucegqbpce`. Supabase access used for this work is read-only.

## Baseline identity and trust boundary

**Baseline ID:** `MOREAI-STATIC-SCHEMA-LINEAGE-20261118`  
**Baseline type:** source-derived, migration-ordered, static expected-object event baseline.  
**Source trust:** Git blob identities and archived migration statement hashes are content-addressed evidence.  
**Execution trust:** UNVALIDATED. Offline replay and testing were explicitly waived by the user. This baseline is not a replayed PostgreSQL schema dump and does not certify deployed execution or exact live parity.

The baseline is deliberately not copied from the live Supabase snapshot. It is reconstructed from the ordered migration history, immutable historical SQL archive records, current migration sources and Git blob identities. The live catalog is held separately as the observed comparison side.

## Reproducible source set

| Evidence | Observed quantity | Interpretation |
|---|---:|---|
| Supabase migration history | 116 rows | History records, latest `20261116113852`; no native checksum/independent execution receipt |
| Active migration directory | 121 SQL files | 116 IDs have history records; 5 corrected browser sources are source-only and unapplied |
| Historical SQL archive | 34 JSON records | Archived source evidence; not execution receipts |
| Archived SQL sources | 8 files | 7 malformed/duplicate originals plus recovered applied Git source for `20261115084819`; blob hashes retained |
| DDL candidate extraction | 513 rows / 106 history versions | Regex/lexical candidate map; not PostgreSQL AST |
| Historical source for `20261115084819` | 619/619 ordered tokens match | Recovered from Git commit `cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31`; source identity recovered, execution still partial |
| Path-reference migrations | 3 | Exact current-main path and Git blob resolved; exact executed bytes unproven |

The active source inventory records each migration filename, Git blob SHA-1, size, history status and source status in `TASK1-MIGRATION-SOURCE-INVENTORY-20261118.csv`. The static object event baseline records each extracted DDL candidate, migration version, statement ordinal, object class, object/target name, expected effect, statement SHA-256, historical archive/source reference and observed reconciliation classification in `TASK1-STATIC-EXPECTED-OBJECT-BASELINE-20261118.csv`.

## Static expected-object event coverage

The 513 lexical DDL candidates are distributed as follows:

| Operation | Candidate events | Static object class |
|---|---:|---|
| CREATE TABLE | 99 | Table |
| ALTER TABLE | 81 | Table / column / constraint evolution |
| CREATE INDEX | 99 | Index |
| CREATE POLICY | 46 | RLS policy |
| CREATE FUNCTION | 165 | Function |
| DROP FUNCTION | 6 | Function removal/replacement |
| CREATE TRIGGER | 7 | Trigger |
| DROP TRIGGER | 6 | Trigger removal/replacement |
| CREATE EXTENSION | 2 | Extension |
| CREATE SCHEMA | 1 | Schema |
| CREATE VIEW | 1 | View |
| **Total** | **513** | **106 migration-history versions** |

These rows are migration events, not 513 unique final objects. Multiple events can mutate the same object over time. The event rows retain statement ordinal and SHA-256 so that each candidate can be traced back to the exact archived history statement. For a complete definition, follow `expected_definition_ref` to the archived JSON and selected statement; the event CSV is an index, not a replacement for the SQL source.

## Expected-versus-observed semantic reconciliation

Observed side is the read-only all-non-system-schema catalog snapshot in `TASK1-OBSERVED-CATALOG-FINGERPRINTS-20261118.csv`. Its all-schema inventory includes 27 schemas, 137 ordinary tables, 1 partitioned table, 4 views, 4 sequences, 396 indexes, 1,400 columns, 709 constraints, 328 functions, 19 non-internal triggers, 99 RLS policies, 123 RLS-enabled tables, 320 types, 7 extensions, 24 role memberships, 27 default ACL entries, 1,704 table-privilege rows, 702 routine-privilege rows and 5,456 non-internal dependency rows.

| Object category | Static expected-source coverage | Observed catalog evidence | Reconciliation result |
|---|---|---|---|
| Schemas | 1 CREATE SCHEMA candidate | 27 schemas, owner/ACL fingerprint | NOT_VERIFIABLE globally; candidate lineage only |
| Tables | 99 CREATE + 81 ALTER candidates | 138 ordinary/partitioned tables | NOT_VERIFIABLE per object; aggregate count is not a semantic match |
| Columns | Embedded in CREATE TABLE / ALTER TABLE statements | 1,400 columns with type/nullability/default/ordinal fingerprint | NOT_VERIFIABLE globally; no AST-normalized all-object expected column graph |
| PK/FK/UNIQUE/CHECK constraints | Embedded in table DDL and ALTER TABLE candidates | 709 constraint definitions fingerprinted | NOT_VERIFIABLE globally; no complete semantic expected constraint graph |
| Indexes | 99 CREATE INDEX candidates | 396 index definitions fingerprinted | NOT_VERIFIABLE globally; source events do not represent all platform/internal indexes |
| Sequences | Implicit defaults/serial/identity may occur in table DDL; no dedicated sequence extractor | 4 sequences with parameters/owner/ACL fingerprint | NOT_VERIFIABLE |
| Functions/procedures | 165 CREATE + 6 DROP FUNCTION candidates | 328 routines; all inspected entries are functions | NOT_VERIFIABLE globally; overload identity, body normalization and platform routines need separate provenance |
| Triggers | 7 CREATE + 6 DROP TRIGGER candidates | 19 non-internal trigger definitions | NOT_VERIFIABLE globally |
| Views | 1 CREATE VIEW candidate | 4 views | NOT_VERIFIABLE globally |
| RLS policies | 46 CREATE POLICY candidates; DROP/ALTER policy coverage is incomplete | 99 policy definitions fingerprinted | NOT_VERIFIABLE globally |
| ACL / grants / ownership | GRANT/REVOKE/ALTER OWNER are not comprehensively extracted by the current DDL candidate parser | schema/relation/routine ACLs, owners, role membership and default ACLs inventoried | NOT_VERIFIABLE |
| Extensions | 2 CREATE EXTENSION candidates | 7 extension names/versions/schemas | NOT_VERIFIABLE globally |
| Types/domains/enums | Implicit/custom type definitions in SQL are not comprehensively extracted | 320 pg_type rows; 47 enum labels; 2 domain constraints | NOT_VERIFIABLE |
| Dependencies | Direct references in DDL and routine bodies are not fully resolved by regex extraction | 5,456 non-internal pg_depend rows | NOT_VERIFIABLE globally |

**No category is declared globally MATCH.** This is intentional: a count or fingerprint on the observed side is not equivalent to a source-derived expected definition. The static baseline is source-traceable; full semantic expected-vs-observed parity remains NOT_VERIFIABLE without AST-level reconstruction or replay. No database write or schema change was performed.

## Explicit, evidence-backed classifications

- **Expected difference / unapplied source:** corrected browser migrations `20261116162500` through `20261116163000` are absent from migration history. Their new tables, functions, triggers, policies and indexes are source-only expectations, not defects in the live catalog.
- **Browser lifecycle CHECK:** applied history through `20261116083458` supports the eight-value lifecycle CHECK. Later corrected browser sources extend it while preserving the existing eight values. Those later definitions are unapplied; do not claim their additional event values exist in production.
- **Malformed legacy IDs:** `20261116250000`, `20261116260000`, `20261116270000`, `20261116280000`, `20261116300000` are retained as historical source identities only. Corrected active paths are `20261116162500`, `20261116162600`, `20261116162700`, `20261116162800`, `20261116163000`.
- **Duplicate/misnamed paths:** the historical `20261111110000` outbox alias and current-main `20261115090000` model-preferences alias were archived and removed from active migration paths; historical source bytes remain preserved.
- **20261115084819:** original source recovered at historical commit `cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31`; current-main alias is not treated as its source.
- **Three path references:** `20261111030000`, `20261111033000`, `20261111040000` resolve to exact current-main SQL paths and Git blob SHA-1 values. The history values are path references, not SQL checksums.

## Execution provenance vocabulary

- `SOURCE_EXISTS`: source file/blob exists and hash is recorded.
- `HISTORY_RECORDED`: migration version exists in Supabase migration history.
- `SOURCE_IDENTITY_RECOVERED`: historical source mapped to the history statement (including token-match evidence where recorded).
- `OBSERVED_EFFECT_SUPPORTED`: compatible live catalog object evidence exists; not an exact execution receipt.
- `UNAPPLIED_SOURCE_ONLY`: source exists but no history record and no applied claim is made.
- `EXECUTION_UNPROVEN`: no signed receipt/native checksum independently ties deployed bytes to the source.
- `NOT_VERIFIABLE`: insufficient evidence for semantic object parity.

A migration history row is not an execution receipt. A current catalog object is not proof that a particular migration created it. Source hash, history record and observed effect remain separate evidence dimensions.

## Scope and release decision

- Supabase: read-only only; no migration apply, DDL, data write or Auth setting change.
- Local replay/testing: waived by user; no replay or test is claimed.
- Staging/deployment: not performed.
- Static schema baseline: **CREATED — SOURCE-TRACEABLE / EXECUTION-UNVALIDATED**.
- Global object parity: **NOT_VERIFIABLE** for categories above.
- Task 1: **REVIEW_REQUIRED / NOT COMPLETE** until per-object semantic expected definitions and live comparison can be completed with evidence beyond lexical DDL extraction and aggregate fingerprints.
