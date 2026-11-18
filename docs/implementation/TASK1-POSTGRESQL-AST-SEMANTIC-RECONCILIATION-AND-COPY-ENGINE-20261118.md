# Task 1 — PostgreSQL AST, semantic reconciliation and Copy Engine implementation

Date: 2026-11-18  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Supabase: `uunfgimtokhucegqbpce`

## Implementation delivered

### PostgreSQL parser and expected-object graph

- Added a pinned `pglast==7.10` parser package under `tools/schema_reconciliation/`. It uses PostgreSQL grammar/AST JSON, not regex, as the parser authority.
- AST inputs are: 121 active migration SQL files; 116 exact migration-history rows captured through read-only SELECT; and 8 archived SQL sources parsed as archive evidence (7 malformed/duplicate originals plus the recovered applied Git source for 20261115084819).
- Raw history statement text is preserved in 15 JSON batches under `migration-history-sql-source-snapshot-20261118/`; each batch is Git-blob-addressed.
- Added `migration-history-statement-hashes-20261118.json`: 116 migration records, 116 statement hashes, 113 SQL statement records and 3 path-reference records. SHA-256 values were computed read-only in PostgreSQL using pgcrypto. The AST parser independently recomputes statement hashes and compares them to this manifest.
- AST event graph includes migration/source identity, source SHA-256, Git blob SHA-1 where a Git file exists, statement ordinal, AST node tag, object class/name, normalized AST hash, dependency candidates and per-object migration lineage.
- Table CREATE/ALTER AST is expanded into nested column and constraint events. Index, function/procedure, trigger, view, sequence, type/domain, schema, RLS policy, extension, role, grant/ACL, ownership and other supported DDL tags are recognized.
- Active source and history AST variants are cross-linked by migration ID/statement ordinal. Identical ASTs retain both source records; conflicting ASTs become NOT_VERIFIABLE.
- The seven malformed/duplicate archived SQL originals are parsed into a separate historical archive event list; they are not mixed into the active expected-state timeline.
- Procedural SQL bodies, dynamic SQL, unsupported statements, ambiguous object identities and path references are explicitly marked NOT_VERIFIABLE. Function bodies are not falsely represented as parsed outer DDL semantics.

### Read-only observed catalog evidence

The observed side is stored separately from the expected graph:

- `observed-catalog-snapshot-20261118.json`: 4,980 objects across schemas, relations, columns, constraints, indexes, routines, triggers, policies, sequences, types, extensions and table ACL rows. It includes 116 applied migration IDs and a total non-internal dependency count of 5,456.
- `observed-security-catalog-snapshot-20261118.json`: 4,159 expanded ACL entries, 312 default ACL entries, 24 role memberships, 702 routine privilege rows and 30 role definitions.
- `observed-dependency-graph-20261118.json`: 3,905 dependency edges whose dependent or referenced object is in a non-system schema.

The snapshots are SELECT-only evidence; they do not modify Supabase. Routine bodies and definitions are preserved as catalog text where available. Tables, columns, constraints, policies, ownership, ACLs and generated types without a comparable source AST remain NOT_VERIFIABLE until category-specific semantic reducers are implemented.

### Semantic reconciliation engine

- Added `reconcile.py`, which joins expected object keys to observed catalog keys, parses observed definition SQL back into PostgreSQL AST where possible, compares AST roots and normalized ASTs, and emits the requested classification vocabulary.
- Supported classifications: MATCH, MISSING, UNEXPECTED, DEFINITION_MISMATCH, SECURITY_MISMATCH, DEPENDENCY_MISMATCH and NOT_VERIFIABLE.
- It will not classify unmatched observed objects as UNEXPECTED while expected-source coverage is incomplete.
- It will not classify a missing object from an unapplied source as live drift.
- It will not classify ACL, ownership, role membership or unnamed generated constraints as missing when source identity cannot be normalized.
- Dependency candidates and observed dependency edges are attached to each object as evidence, but are not reported as semantically matched until full dependency binding is available.
- The reconciliation output is explicitly not allowed to make a global no-drift claim while any object remains unverified.

### Execution provenance

- Migration history SQL statement hashes are now recorded independently from Git source blob hashes.
- History row presence remains distinct from exact source existence, source identity and observed catalog effect.
- The five corrected browser migration files remain unapplied. Their malformed originals remain preserved in the historical archive.
- Migration `20261115084819` retains the recovered Git commit/token-match evidence; no deployed-byte receipt is inferred.
- Three path-reference history records remain path-reference evidence and do not prove the exact deployed SQL bytes.
- Global execution provenance status remains `EXECUTION_PROVENANCE_UNVERIFIABLE`: no native deployed checksum or independent deployment receipt exists.

### AI Skills and Copy Engine

- Added the original MoreAI `copy_engine_generate` tool to the existing tool catalog and registered it in the canonical `DurableOpenManusRuntime`. It calls the existing metered LLM gateway; it is not a second runtime or external copy SaaS.
- Modes: brand voice, campaign concept, ad variant, social caption, landing page, product description, email, headline and text overlay specification.
- The engine enforces source-fact-only claims and rejects fabricated prices, discounts, guarantees, certifications, performance results, testimonials and unsupported product claims.
- Text-overlay mode emits an exact copy/design specification only. It does not render or composite media; Scenario's chevron/Pillow/Chromium renderer dependencies were not imported.
- Scenario `scenario-brand-kit`, `scenario-ad-variants` and `scenario-text-overlay` route through the Copy Engine adapter and require `content.generate`.
- Visual Skills, generic Scenario media skills and curated Motion Skills route through the existing MoreAI media tools and require `media.generate`.
- API and worker allowlists include the two permission keys. The worker resolver fails closed if the selected skill's adapter-required permission is not present in the install's granted-permission snapshot.
- Curated permission manifest covers 230 selected entrypoints: 2 Visual Skills, 173 Scenario Skills and 55 licensed Motion Skills. The unresolved-license Motion pack remains excluded.
- Supabase skill package/install permission values are JSON arrays rather than a fixed enum/check list. No schema migration is needed for the new permission labels.
- No package import, publication, installation or permission grant was written to Supabase. Database activation remains pending the existing Skill Registry owner-authorized workflow.

## Runtime execution status and remaining limits

A GitHub Actions workflow `.github/workflows/moreai-postgres-ast-reconstruction.yml` is configured to parse active/history/archive SQL, compare history statement hashes, reconcile against the committed read-only catalog snapshots, and persist generated graph/reconciliation JSON under `docs/implementation/generated/` when repository write permission permits.

**The AST parser and reconciliation implementation are committed, but a successful workflow run and generated output artifact have not yet been independently verified in this session. Therefore no number of successfully parsed DDL statements or final semantic classification totals is claimed.** This is not a test result and no runtime test suite was run.

Outstanding semantic work:
1. Implement and execute table/column/constraint ALTER reducers for the full migration timeline.
2. Normalize ACL, owner, RLS policy and role membership semantics against source AST grants and catalog ACLs.
3. Bind expected dependency candidates to `pg_depend` identities and classify dependency parity.
4. Verify the generated AST graph and reconciliation artifact from the GitHub Actions run.
5. Exact deployed-byte provenance remains unavailable without a deployment receipt/native checksum; retain `EXECUTION_PROVENANCE_UNVERIFIABLE`.

## Safety boundary

No Supabase write, DDL, migration apply, staging, test suite, production deployment or UI redesign was performed. All Supabase access used for this work was read-only.
