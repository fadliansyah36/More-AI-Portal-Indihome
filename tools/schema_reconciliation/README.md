# MoreAI PostgreSQL AST schema graph

This is a static source-analysis utility. It does not connect to PostgreSQL, execute migrations, create a database, or write to Supabase.

## Parser

- Parser: `pglast`, using PostgreSQL's grammar parser and AST JSON representation.
- Pin: `pglast==7.10`.
- Source inputs: active migration SQL files; preserve and separately parse historical SQL source files when available.
- Output: migration source manifest, AST-normalized DDL events, per-object migration event history and AST reference candidates.

## Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python schema_graph.py --migrations-dir ../../supabase/migrations --history-dir ../../docs/implementation/migration-history-sql-source-snapshot-20261118 --output ../../docs/implementation/generated/expected-object-graph.json
```

The `--history-dir` input contains 116 raw migration-history rows captured with a read-only SELECT in `docs/implementation/migration-history-sql-source-snapshot-20261118/`. These snapshots preserve the SQL statement text exactly as returned by Supabase history. Git blob hashes identify the snapshot JSON files; the parser computes SHA-256 for each individual statement. Three path-reference rows are not SQL and remain `NOT_VERIFIABLE`. Active Git migration files and history statements are cross-linked by migration ID/statement ordinal; differing AST hashes are flagged as source conflicts rather than silently selected.\n\nThe reconciliation CLI consumes an expected graph and a read-only catalog JSON. It emits one row per expected/observed object with MATCH, MISSING, UNEXPECTED, DEFINITION_MISMATCH, SECURITY_MISMATCH, DEPENDENCY_MISMATCH or NOT_VERIFIABLE. It only emits MATCH when normalized semantic definitions are supplied on both sides. For incomplete source coverage, unmatched observed objects remain NOT_VERIFIABLE rather than UNEXPECTED.\n\nThe generated JSON contains exact source SHA-256, Git blob SHA-1, migration ID, statement ordinal, AST node type, normalized AST hash and event lineage. The parser marks objects whose last event is ALTER/GRANT/RENAME as requiring a semantic reducer. Function/procedural bodies are marked opaque unless a dedicated body parser is added. It does not turn syntax recognition into execution proof.

## Classification contract

- `AST_PARSED`: statement was accepted by PostgreSQL grammar parser.
- `NOT_VERIFIABLE`: parse failure, object identity unavailable, dynamic/procedural body opaque, or final state cannot be reconstructed without a reducer.
- `EXECUTION_PROVENANCE_UNVERIFIABLE`: source and history may exist, but exact deployed bytes or execution receipt cannot be proven.

No schema object is globally MATCH solely because its AST parsed.
