# Task 1 — Execution Continuation & Reference Skills Integration

Date: 2026-11-18
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Base commit: `9b5bf2ca8df7cc6c8e34c569f6857747dbca5e39`
Supabase project: `uunfgimtokhucegqbpce`

## Executive status

**Task 1 remains REVIEW_REQUIRED — not complete.** This continuation preserves the source-only browser migration recovery already committed and advances the evidence set. It does not relabel the observed production catalog as an expected schema, infer execution from migration-history rows, or claim that reference skill packages were imported into Supabase.

No production database write, DDL, migration apply, offline replay, staging, test, build, lint, typecheck, provider call, runtime activation, or deployment was performed.

## 1. Migration source and provenance decisions

### 1.1 Browser migrations — source correction committed

The five invalid 14-digit identifiers used hour values 25, 26, 27, 28 and 30. Their corrected active source paths and blob SHAs on the base commit are:

| Corrected active migration | Blob SHA |
|---|---|
| `20261116162500_moreai_browser_human_takeover_grants.sql` | `99162b991ec3c6982632e5873cd48b9942db54f2` |
| `20261116162600_moreai_browser_takeover_run_terminal_revocation.sql` | `67eff05afa814cdd836a168e1ce3355eebb87a77` |
| `20261116162700_moreai_browser_takeover_logout_revocation.sql` | `90e4e023020232dbf022fa1d52935c82ade83cd1` |
| `20261116162800_moreai_browser_takeover_command_queue.sql` | `eaa688946b91215fec04d8382e2eff3eb3ada3b8` |
| `20261116163000_moreai_browser_preview_requests.sql` | `38ef82a6eca59c29c220f671c6a21d90c9249e4c` |

Decisions already implemented in the base commit:

- Preserve the eight lifecycle events already supported by applied history/live CHECK constraints: `created`, `restored`, `state_saved`, `close_requested`, `closed`, `expired`, `profile_retention_eligible`, `profile_deleted`.
- Human takeover grants are short-lived and one-time; privileged RPCs are service-role-only and verify session ownership/status/expiry.
- Run terminal and logout revocation are separated; the FastAPI caller must bind the logout user ID to the authenticated principal.
- The command queue has one claim function, one finish function and one revoke trigger. Expired processing leases are terminally marked `worker_lease_expired_outcome_unknown`; uncertain browser input is not replayed automatically.
- Preview requests bind the requesting owner, browser session, run and PNG artifact owner/run association.
- All five original malformed source files are preserved byte-for-byte under `docs/implementation/migration-source-archive/`; their original Git blob SHAs are recorded in the prior recovery manifest.
- Two duplicate/misnamed aliases were moved out of the active migration directory and retained under the historical source archive: `20261115090000_moreai_agent_model_preferences.sql` and `20261111110000_moreai_durable_run_event_outbox.sql`.

The source/object dependency map is recorded in `TASK1-DEPENDENCY-MAPPING-20261118.csv`; the recorded-history DDL candidate map is `MOREAI-MIGRATION-TO-OBJECT-DDL-MAP-20261118.csv`. These are repository-source corrections only. None of the five corrected browser migrations was applied to Supabase.

### 1.2 Migration 20261115084819

The original source identity was recovered from historical Git commit `cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31`. At that commit, path `supabase/migrations/20261115090000_moreai_agent_model_preferences.sql` has 619/619 ordered SQL lexical tokens matching the history statement for `20261115084819`.

The current-main `15090000` file was a different duplicate alias of `15100000` / applied history `20261115085314`; it is archived and removed from the active migration directory. The original historical source remains preserved in Git history. This resolves source identity, not an independent execution receipt.

### 1.3 Duplicate/misnamed migration paths

- `20261111110000_moreai_durable_run_event_outbox.sql` was an exact content alias of applied history `20261111091531`; it is retained as an archived source artifact, not an active migration.
- `20261115090000_moreai_agent_model_preferences.sql` on current main was an exact duplicate alias of `20261115100000`; the separate original `20261115084819` source is recovered from its historical commit.
- Historical migration-history rows and archived statements were not deleted or rewritten.

### 1.4 Three migration-history path references — source identity resolved

The three history rows `20261111030000`, `20261111033000` and `20261111040000` store path references rather than SQL text. Each reference was read directly from `supabase_migrations.schema_migrations.statements` and resolved to the exact current-main file and Git blob:

| History version | Stored path reference | Current-main Git blob SHA |
|---|---|---|
| 20261111030000 | supabase/migrations/20261111030000_moreai_enqueue_chat_run.sql | 5496f3f51100b843d9b5e96032e52cc10de482d3 |
| 20261111033000 | supabase/migrations/20261111033000_moreai_llm_reserve_with_entitlement_quota.sql | 9b4984abcd100c558a50e676f0f39a7296d49b66 |
| 20261111040000 | supabase/migrations/20261111040000_moreai_llm_quota_settlement_reconciliation.sql | 7bb174c960aeabba71c49a84e95f30a13552eece |

This resolves source-path identity and current source blob identity. It does **not** prove the exact bytes executed at deployment time: the history stores a path token, not a checksum or signed deployment receipt. The provenance CSV records these rows as `SOURCE_IDENTITY_PATH_RESOLVED;EXECUTION_UNPROVEN`.

### 1.5 Execution provenance rule

The live `supabase_migrations.schema_migrations` history currently has 116 rows, latest version `20261116113852`. The table has no native checksum column. The three records `20261111030000`, `20261111033000` and `20261111040000` store path references rather than SQL text in their statement values. Reconstructed MD5/SHA-256 values are evidence hashes of retrieved source/history content, not historical deployment checksums.

A history row proves that a migration record exists in the migration-history table. It does not independently prove successful execution, the exact deployed bytes, or the final object state. Observed object effects can support a mapping but are not a deployment receipt.
A read-only extraction now maps direct DDL candidates from the stored migration statements: `MOREAI-MIGRATION-TO-OBJECT-DDL-MAP-20261118.csv` contains 513 regex-extracted DDL candidate rows across 106 of 116 history versions. Each row records migration version/name, statement ordinal, operation, object/target object where captured, and SHA-256 of the exact history statement. Recognized operations include CREATE/ALTER TABLE, CREATE INDEX, CREATE POLICY, CREATE FUNCTION, CREATE TRIGGER, DROP FUNCTION/TRIGGER, CREATE EXTENSION/SCHEMA/VIEW. Ten history versions have no match in this limited pattern set; that does not imply they have no effects. The extractor is lexical/regex-based, not a PostgreSQL AST or replay, and does not resolve dynamic SQL, all ALTER subcommands, GRANT/REVOKE, rename semantics, or dependencies embedded inside function bodies. It is a useful migration-to-object candidate map, not a final object-evolution proof.


## 2. Read-only observed object inventory

A fresh read-only catalog query against project `uunfgimtokhucegqbpce` returned:

| Public-schema object class | Observed count |
|---|---:|
| Base tables | 94 |
| Views | 1 |
| Materialized views | 0 |
| Columns | 922 |
| Constraints | 562 |
| Indexes | 245 |
| Functions/procedures | 98 |
| Non-internal triggers | 5 |
| RLS policies | 95 |
| RLS-enabled base tables | 94 / 94 |
| FORCE RLS base tables | 0 |
| Table privilege rows | 1,318 |
| Sequences in public | 0 |
| pg_type rows in public | 190 |

The same read-only query observed 27 non-system schemas and seven installed extensions: `pg_cron 1.6.4`, `pg_stat_statements 1.11`, `pgcrypto 1.3`, `plpgsql 1.0`, `supabase_vault 0.3.1`, `uuid-ossp 1.1`, and `vector 0.8.2`.

The following reproducible MD5 fingerprints were computed from sorted public-schema catalog definitions (not security attestations):

- relations: `61446821f81408ff1580fb965b4c60e0`
- columns: `af3f6dca2b85d858b8853f8b744ee24b`
- constraints: `1461077f3ede3d4c386a77f4038125dd`
- indexes: `b8965b9082b89396b77d74794420f6a4`
- functions: `6523c48a123b997fbcd2847cc143691c`
- triggers: `eb2ae0d20f7d22486b69dd55cb2e1e81`
- RLS policies: `74762a7c84df6498207292292f8526e9`
- table privilege rows: `118bd81a46ccf08993601020462a83dc`

This inventory is an observed-state fingerprint. It is not an expected-state baseline.

### 2.1 Full non-system schema-family inventory

A second read-only catalog query covered all 27 non-system schemas (not just `public`). The observed counts are:

| Object class | Observed count |
|---|---:|
| Non-system schemas | 27 |
| Ordinary tables | 137 |
| Partitioned tables | 1 |
| Views | 4 |
| Materialized views | 0 |
| Sequences | 4 |
| Indexes | 396 (394 ordinary + 2 partitioned indexes) |
| Columns | 1,400 |
| Constraints | 709 |
| Functions/procedures | 328 (all 328 are functions) |
| Non-internal triggers | 19 |
| RLS policies | 99 |
| RLS-enabled base/partitioned tables | 123 |
| FORCE RLS tables | 0 |
| Table privilege rows | 1,704 |
| Routine privilege rows | 702 |
| pg_type rows | 320 |
| Enum labels | 47 |
| Domain constraints | 2 |
| Role memberships | 24 |
| Default ACL entries | 27 |
| Non-internal dependency rows | 5,456 |
| Extensions | 7 |

The seven extensions and versions are: `pg_cron 1.6.4`, `pg_stat_statements 1.11`, `pgcrypto 1.3`, `plpgsql 1.0`, `supabase_vault 0.3.1`, `uuid-ossp 1.1`, and `vector 0.8.2`.

Sorted catalog-definition fingerprints for the all-schema snapshot (MD5, reproducibility identifiers only):

| Catalog set | Fingerprint |
|---|---|
| Schemas, owners and schema ACLs | `29a2265ac033284b723736ff4a269455` |
| Relations, owners, RLS flags and relation ACLs | `533553c7d6f2bc8621b14513432e8954` |
| Columns | `3269c99076916dcddd6b88be2ba22fe6` |
| Constraints | `fb7c57f52c22d49090f95bd6f7193cf0` |
| Index definitions | `b01daea35818f1a0fd70eb555378e2e5` |
| Routine definitions, owners, security-definer flags and ACLs | `c098e21fd78656a9bb0715c0d61caad7` |
| Trigger definitions | `d533ce13d2b715c843fe61a624b9f08d` |
| RLS policy definitions | `c842208fffb2720bb24daad8589a5530` |
| Type metadata | `08b0b3c4938e385f73fa0da35a9bf3ee` |
| Relation/object dependency catalog rows | `a56fbd3c9c1be0cde66b2ac5126c23a3` |
| View definitions | `e74a710960c3998bc2470325b0b79ffd` |
| Sequence definitions and parameters | `673086bafa9ebbdc1ec8417860603c72` |
| Default ACL entries | `648953781337e0e07d2f743aa8a67da2` |
| Role memberships | `fc3d7ebff9ed4734e923337d3f2addad` |

The all-schema inventory is also exported to `TASK1-OBSERVED-CATALOG-FINGERPRINTS-20261118.csv`. These hashes fingerprint the observed catalog only. They do not establish expected definitions, prove historical migration execution, or certify that the current state is correct.
 The public table privilege view does not replace schema, sequence, function ACL, role membership, ownership and default-privilege reconciliation. The 190 `pg_type` rows include PostgreSQL-generated relation row types and must not be interpreted as 190 independently authored domain types.

## 3. Trusted expected schema baseline — status and concrete boundary

The evidence set now includes:

- 116 applied-history rows, ordered by migration version.
- 32 historical SQL statements recovered into immutable JSON archive records, with per-statement SHA-256.
- Current migration-source inventory and the corrected 116-row history reconciliation.
- 85-file migration-directory inventory from the prior reconciliation; current source-only browser path corrections and duplicate-alias archive decisions are recorded separately.
- 23 source/history mismatch classifications: 22 are formatting/comment or semantically equivalent after token/statement comparison; the 15084819 source identity is recovered from Git history.
- Live catalog definitions and the observed object fingerprints above.
- The Master PRD v1.2 Draft and repository engineering instructions.

**A source-traceable static expected-object event baseline has now been created** at `TASK1-STATIC-EXPECTED-SCHEMA-BASELINE-20261118.md` and `TASK1-STATIC-EXPECTED-OBJECT-BASELINE-20261118.csv`. It is derived from 513 DDL candidates across 106 history versions and references archived SQL statement hashes, migration source paths and Git blob identities. It is trusted as a reproducible source-lineage index, but is explicitly **EXECUTION_UNVALIDATED**: it is not a replayed schema dump and does not independently attest live deployment. The PRD is not DDL-complete; the live catalog remains the observed side only. Migration history has no native checksum and includes three path-reference statements.

Accordingly, the deterministic migration-lineage/source baseline is now committed. A full normalized expected-object graph and global semantic expected-vs-observed result still cannot be certified without either:
1. an immutable, known-good, schema-only dump with environment identity, capture time and hash; or
2. explicit permission to replay the complete pinned lineage offline in an isolated disposable database. The user has now explicitly chosen to skip this replay; this option is waived for the current continuation.

The user has explicitly waived offline replay and testing for this continuation. No known-good schema-only dump has been supplied. Therefore the expected schema can proceed only as a static source-derived reconstruction; it must remain marked UNVALIDATED and must not be presented as a replay-verified baseline. This is a documented scope decision, not permission to substitute the live snapshot or guess missing object definitions.

## 4. Object-level reconciliation result

Observed public object classes and definitions were read for relations, columns, constraints, indexes, functions, triggers, views, RLS policies, table privileges, extensions, types and relation dependencies. Existing scoped comparison still has 7 MATCH, 3 EXPECTED_DIFFERENCE (unapplied browser objects) and 2 NOT_VERIFIABLE results.

**Global object-level reconciliation is not closed.** Static source analysis may continue, but a complete expected-vs-observed object-by-object comparison for every schema, object owner, schema/table/sequence/function ACL, default privilege, role membership, type definition, extension dependency and cross-object dependency cannot be truthfully claimed without a trusted expected baseline. Offline replay/testing is waived by the user for this continuation. No live object was changed to force a false match.

## 5. Reference AI Skills — source and integration status

### 5.1 Source governance and pins

The current FastAPI Skill Registry source already contains pinned-source support for:

- Visual Skills: `smixs/visual-skills@61a60d317f0fa0c3dc98902e58a7cb178838ae3f` — two entrypoints, CC BY 4.0. Root LICENSE and NOTICE are present. Attribution/change notices are required. Third-party provider logos and three image/banner assets remain excluded/held pending rights evidence.
- Scenario Skills: `scenario-labs/skills@94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9` — 172 product-facing `skills/*/SKILL.md` entrypoints; root MIT. Seven internal maintainer/skill-authoring entrypoints are archive-only. Per-file nested license, asset and dependency review remains incomplete.
- Motion Skills: the supplied `iart-ai/motion-skills` repository is an index, not an executable package. The API pins 19 linked pack repositories and 56 `skills/*/SKILL.md` entrypoints. Eighteen pack roots have MIT licenses; `generative-illustration-skills` has no root license and remains blocked as NOASSERTION. Exact pack pins and counts are in `REFERENCE-SKILLS-CURATION-AND-INTEGRATION-20261118.csv`.

The catalog's current source inventory is 230 product entrypoints (2 Visual + 172 Scenario + 56 Motion). The aggregator repository itself is not admitted as a skill package because it contains no `skills/*/SKILL.md` entrypoints.

### 5.2 Existing implementation verified in source

The following source integration is already implemented in `main`; it was verified by reading the exact source files, not by running the application:

1. `apps/api/app/routers/skills.py` exposes the pinned catalog, source registration/import, recursive bounded source ingestion and validation/SBOM review. Source import does not execute upstream code. License/publication remains unverified/private until privileged review.
2. The catalog only returns allowlisted pinned repository entrypoints; Visual paths are restricted to `image/SKILL.md` and `video/SKILL.md`, Scenario/Motion paths to their `skills/*/SKILL.md` subtrees.
3. `components/views/agent-studio-view.tsx` selects only installed, approved skill packages (maximum 10).
4. `apps/api/app/routers/conversations.py` accepts `skill_ids` and passes them through the existing durable enqueue RPC.
5. `engine/agents/durable_tool_runtime.py` resolves skills for the Agent Run through the existing `SupabaseSkillResolver`.
6. `apps/worker/app/skill_resolver.py` enforces owner-scoped package/install status, validation, license approval, publication, exact granted-permission subset, immutable source inventory, SHA-256 and Git blob SHA-1 checks, and per-run resolution/execution audit events.
7. The resolver is injected into the existing OpenManus durable runtime. No second Agent Runtime, Skill database, or browser-side Supabase access was added.
8. A source-aware MoreAI adapter was implemented in `apps/worker/app/skill_resolver.py` (commit `dd3f9ba170568182674c54e75140d452e09bc88a`). It adds an explicit native-tool contract to Visual/Scenario/Motion skill context, blocks Scenario 3D/Mesh/Blender-only entrypoints while no native 3D provider exists, and records the selected adapter in the immutable per-run snapshot/audit event. It does not add provider tools or activate packages.

### 5.3 Compatibility curation and execution gates

- Visual `image` and `video` skills are prompt-authoring workflows. Their instructions reference model names and model-specific reference files that are not all MoreAI provider contracts. Their portable prompt-design methods can be adapted to existing MoreAI image/video adapters; the upstream text must not be treated as permission to call unsupported models.
- Scenario image/video/storyboard/consistency entrypoints explicitly require Scenario MCP tools (`recommend`, `model_schema_get`, `model_run`, `jobs_wait`, asset tools). MoreAI does not expose a Scenario MCP runtime. These workflows must be adapted to the existing MoreAI OpenAI image and Runway video adapters; they cannot be executed unchanged.
- Scenario 3D entrypoints depend on Scenario 3D model services and are deferred; do not advertise them as executable in the current MoreAI runtime.
- Motion packs are discoverable through the same pinned registry. Their instructions do not provision video providers, ffmpeg/ffprobe, Remotion, model pricing, billing, or rendering infrastructure. These dependencies remain separate release gates.
- Skills remain untrusted instruction context. They cannot grant tools or override system policy. Runtime execution requires per-owner import, complete ingestion, source integrity, dependency/license/asset review, publication, installation, permission grant and the existing worker release flags.

### 5.4 Native source adapters implemented

`apps/worker/app/skill_resolver.py` now derives the source adapter from immutable `source_repository` and `source_path` fields after verifying every stored file and root hash:

- Visual Skills: prompt-authoring-only adapter; maps to MoreAI `image_generate` or `video_generate` only when the respective tool is actually registered.
- Scenario Skills: explicitly rejects Scenario MCP tool names and translates supported creative workflows to the native MoreAI image/video tool boundary. Scenario 3D, 3D-world, Blender, Meshy, Rodin, SPARC3D and Patina-retexture entrypoints fail closed with `skill_provider_capability_unavailable` until a native 3D/mesh adapter exists.
- Motion Skills: adds a production-workflow guard; does not assume Remotion, ffmpeg/ffprobe, fonts, codecs, render workers, external model APIs or credentials are provisioned.
- Adapter identity is attached to the per-run skill snapshot and resolution audit detail. No new tools, provider credentials, database tables or Agent Runtime were introduced.

Worker trust-boundary corrections (commits `0a4f99a906b227d71ea59d0055e1173d5fe11816` and `1f096d231292bf83ca84192c2352409e0fda5bfd`): the resolver now invokes `_validate_pinned_source_identity` for each owner-scoped package before loading stored files. The validator requires an exact allowlisted repository and commit and rejects unknown repositories, unpinned commits, unsupported entrypoint paths, and the unlicensed Motion pack. A privileged or malformed registry row therefore cannot widen the API import allowlist. These changes are source-only and were not runtime-tested in this run.

This is a source-level adaptation and security boundary. It is not runtime acceptance; no packages were imported or executed in this continuation.

### 5.5 What has not been executed

The customer Skill Registry package count was previously observed as zero in the read-only Supabase snapshot. Because this task forbids production writes, no package was inserted, ingested, installed, published, permission-granted or activated in the connected project during this continuation. No skills were represented by fake seed data. The source-level integration is real; actual tenant package activation remains intentionally off.

## 6. Remaining blockers

1. Trusted expected schema object baseline: no immutable known-good schema-only dump is available; offline isolated replay/testing has been explicitly waived by the user. Static reconstruction remains unvalidated.
2. Full expected-vs-observed object comparison: every schema/object and ACL/owner/dependency class against that trusted baseline.
3. Native execution receipts or independently verifiable deployment artifacts for historical migration execution; the history table alone is insufficient.
4. The three path-reference rows are now mapped to exact current-main paths and Git blob SHAs; byte-for-byte execution remains unproven because history has no native checksum or independent deployment receipt.
5. Reference skills require actual per-user import/ingestion and privileged review before execution. The user explicitly prohibited production writes in this run; this is not performed.
6. Scenario/Motion provider and tool contracts need explicit MoreAI adapters before model-specific workflows can execute; no Scenario MCP or parallel runtime is introduced.

## 7. Task status and next work

- Browser migration source correction and alias archival: **SOURCE IMPLEMENTED**.
- 15084819 historical source identity: **RECOVERED**.
- Migration history/source archive and mismatch mapping: **EVIDENCE RECOVERED; execution provenance PARTIAL**.
- Read-only observed catalog inventory: **CAPTURED**.
- Trusted expected schema baseline: **STATIC RECONSTRUCTION ONLY / UNVALIDATED — OFFLINE REPLAY AND TESTING WAIVED BY USER**.
- Full object-level reconciliation: **PARTIAL — 513 DDL candidate events mapped; global semantic parity NOT_VERIFIABLE; scoped comparisons retained**.
- Visual/Scenario/Motion source catalog and unified registry/resolver path: **IMPLEMENTED IN SOURCE**.
- Reference skill tenant import, publication and runtime activation: **NOT EXECUTED — production writes prohibited**.

**Overall Task 1: REVIEW_REQUIRED / NOT COMPLETE.** Do not advance Phase 05 or claim global schema parity. Continue with static source-derived object lineage, identify every deterministically provable expected definition, classify unresolved objects/ACLs/dependencies as NOT_VERIFIABLE, and complete the migration execution provenance map where evidence exists. Do not claim replay validation or global schema parity. Reference skills can be imported and reviewed only in an explicitly authorized non-production or production write context; do not activate unsupported Scenario/Motion providers.


## 8. Static schema reconstruction continuation — 2026-11-18

- Read and followed root `AGENTS.md`; Master PRD file path `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md` declares Version 1.2 Draft. Existing PRD and phase tracker remain the product authority; no UI or runtime source was modified for this schema task.
- Committed `TASK1-STATIC-EXPECTED-SCHEMA-BASELINE-20261118.md` and `TASK1-STATIC-EXPECTED-OBJECT-BASELINE-20261118.csv`. The event baseline contains 513 lexical DDL candidates across 106 of 116 applied history versions, classified into schema/table/table evolution/index/RLS/function/trigger/view/extension classes. Each row retains migration version, statement ordinal, SHA-256, historical source reference, current source path/blob where available, expected effect and observed status.
- Committed `TASK1-MIGRATION-SOURCE-INVENTORY-20261118.csv`: 121 active SQL source files, 34 historical JSON archive records and 7 preserved malformed/duplicate original SQL source files. 116 active migration IDs have history records; five corrected browser migrations are source-only/unapplied. Each row records Git blob SHA-1, size and provenance classification.
- Current read-only all-schema observed snapshot is linked from `TASK1-OBSERVED-CATALOG-FINGERPRINTS-20261118.csv`: 27 schemas, 138 ordinary/partitioned tables, 1,400 columns, 709 constraints, 396 indexes, 328 functions, 19 triggers, 99 policies, 4 sequences, 320 pg_type rows, 7 extensions, 24 role memberships, 27 default ACL entries and 5,456 dependency rows.
- Object-category semantic reconciliation is documented in the static baseline report. Scoped verified matches remain limited to the 12-row register (7 MATCH, 3 EXPECTED_DIFFERENCE, 2 NOT_VERIFIABLE); all unscoped/global object categories remain NOT_VERIFIABLE. The 513 DDL rows are migration events, not unique final object definitions, and regex extraction is not a PostgreSQL AST.
- Corrected the stale browser CHECK analysis and malformed `20261116280000` report to reflect implemented source corrections and the new active path `20261116162800`. Original malformed bytes remain archived; five corrected browser sources remain unapplied. The live eight-value CHECK is preserved and no live DB mutation occurred.
- No tests, replay, migration apply, production write, staging or deployment were run, consistent with the user's explicit waiver and scope.

**Task 1 status: IMPLEMENTATION EVIDENCE EXPANDED / REVIEW_REQUIRED / NOT COMPLETE.** Static source baseline and migration inventory are committed; global expected-vs-observed semantic parity and exact historical execution receipts remain NOT_VERIFIABLE.
