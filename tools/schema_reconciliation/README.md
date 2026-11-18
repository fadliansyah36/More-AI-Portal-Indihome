# MoreAI PostgreSQL AST schema graph

This is a static source-analysis utility. It does not connect to PostgreSQL, execute migrations, create a database, or write to Supabase.

## Parser

- Parser: `pglast`, using PostgreSQL's grammar parser and AST JSON representation.
- Pin: `pglast==7.23`.
- Sources: active Git migration files plus raw SQL statements preserved from the Supabase migration history.
- Output: source manifests, AST-normalized DDL events, per-object migration event history, nested column/constraint events and AST reference candidates.

## Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python schema_graph.py \
  --migrations-dir ../../supabase/migrations \
  --history-dir ../../docs/implementation/migration-history-sql-source-snapshot-20261118 \
  --archive-dir ../../docs/implementation/migration-source-archive \
  --history-hash-manifest ../../docs/implementation/migration-history-statement-hashes-20261118.json \
  --history-archive-dir ../../docs/implementation/migration-history-archive \
  --output ../../docs/implementation/generated/expected-object-graph.json
python reconcile.py \
  --expected ../../docs/implementation/generated/expected-object-graph.json \
  --observed ../../docs/implementation/observed-catalog-snapshot-20261118.json \
  --security ../../docs/implementation/observed-security-catalog-snapshot-20261118.json \
  --dependencies ../../docs/implementation/observed-dependency-graph-20261118.json \
  --output ../../docs/implementation/generated/semantic-reconciliation.json
```

The history input contains 116 raw migration-history rows captured with read-only SELECT in `docs/implementation/migration-history-sql-source-snapshot-20261118/`. The snapshots preserve statement text as returned by Supabase history. Their Git blob hashes identify the snapshot files; the parser computes SHA-256 for each individual SQL statement and compares it to the independent SHA-256 manifest captured directly from Supabase history with pgcrypto. Three path-reference rows are not SQL and remain `NOT_VERIFIABLE`.

Active Git files and history statements are cross-linked by migration ID and statement ordinal. Equal AST hashes retain both source evidence records. Different AST hashes are flagged as source conflicts rather than silently selecting one version. The graph also parses 34 recovered applied-history JSON archive records and the eight archived SQL sources (seven malformed/duplicate originals plus the recovered historical Git source for migration 20261115084819) as historical archive evidence without mixing those old IDs into the active expected-object timeline. The graph retains source existence and history-record evidence separately; it does not attest exact deployed bytes.

## Reconciliation

The reconciliation CLI merges the read-only observed object snapshot, expanded ACL/default-ACL/role-membership snapshot and dependency edge snapshot. It emits one row per expected/observed object with `MATCH`, `MISSING`, `UNEXPECTED`, `DEFINITION_MISMATCH`, `SECURITY_MISMATCH`, `DEPENDENCY_MISMATCH` or `NOT_VERIFIABLE`.

It only emits `MATCH` when normalized semantic definitions are supplied on both sides, or when an applied DROP event is confirmed absent. Unmatched observed objects remain `NOT_VERIFIABLE` because source coverage is not complete. Opaque function bodies, ACL identity expansion, unnamed constraints and dependency candidates are not promoted to verified matches.

## Coverage and limitations

- AST parsing proves grammar recognition, not migration execution.
- ALTER event folding into complete final definitions is not inferred; affected objects remain `NOT_VERIFIABLE` until a supported reducer exists.
- SQL/PLpgSQL function bodies and dynamic SQL are opaque in this version and explicitly marked `NOT_VERIFIABLE`.
- Dependency candidates are AST references, not a complete PostgreSQL dependency resolver; the observed dependency snapshot is separate evidence.
- ACL, ownership, extension, policy and role effects require catalog-specific semantic folding before global MATCH can be assigned.
- History path-reference statements have no SQL body and remain `NOT_VERIFIABLE`.
- No global no-drift conclusion is emitted.

The GitHub Actions workflow `.github/workflows/moreai-postgres-ast-reconstruction.yml` runs the parser against active sources and the preserved history snapshot, reconciles against the committed read-only catalog snapshots, and persists generated graph/reconciliation artifacts under `docs/implementation/generated/` when repository write permission permits.
