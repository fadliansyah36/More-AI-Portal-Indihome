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
python schema_graph.py --migrations-dir ../../supabase/migrations --output ../../docs/implementation/generated/expected-object-graph.json
```

The generated JSON contains exact source SHA-256, Git blob SHA-1, migration ID, statement ordinal, AST node type, normalized AST hash and event lineage. The parser marks objects whose last event is ALTER/GRANT/RENAME as requiring a semantic reducer. Function/procedural bodies are marked opaque unless a dedicated body parser is added. It does not turn syntax recognition into execution proof.

## Classification contract

- `AST_PARSED`: statement was accepted by PostgreSQL grammar parser.
- `NOT_VERIFIABLE`: parse failure, object identity unavailable, dynamic/procedural body opaque, or final state cannot be reconstructed without a reducer.
- `EXECUTION_PROVENANCE_UNVERIFIABLE`: source and history may exist, but exact deployed bytes or execution receipt cannot be proven.

No schema object is globally MATCH solely because its AST parsed.
