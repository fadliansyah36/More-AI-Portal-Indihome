-- Read-only observed catalog export for MoreAI semantic reconciliation.
-- Execute only as SELECT against project uunfgimtokhucegqbpce.
WITH
schemas AS (
  SELECT jsonb_build_object(
    'object_key', 'SCHEMA:' || n.nspname,
    'object_class', 'SCHEMA',
    'name', n.nspname,
    'definition', jsonb_build_object('owner', pg_get_userbyid(n.nspowner)),
    'security_fingerprint', md5(jsonb_build_object('owner', pg_get_userbyid(n.nspowner), 'acl', coalesce(n.nspacl::text, 'NULL'))::text)
  ) AS item
  FROM pg_namespace n
  WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
),
relations AS (
  SELECT jsonb_build_object(
    'object_key',
      CASE WHEN c.relkind = 'f' THEN 'FOREIGN_TABLE:' WHEN c.relkind IN ('v','m') THEN 'VIEW:' ELSE 'TABLE:' END || n.nspname || '.' || c.relname,
    'object_class',
      CASE WHEN c.relkind = 'f' THEN 'FOREIGN_TABLE' WHEN c.relkind IN ('v','m') THEN 'VIEW' ELSE 'TABLE' END,
    'name', n.nspname || '.' || c.relname,
    'definition', jsonb_build_object(
      'relkind', c.relkind,
      'persistence', c.relpersistence,
      'owner', pg_get_userbyid(c.relowner),
      'row_security', c.relrowsecurity,
      'force_row_security', c.relforcerowsecurity,
      'partitioned', c.relispartition
    ),
    'security_fingerprint', md5(jsonb_build_object(
      'owner', pg_get_userbyid(c.relowner),
      'row_security', c.relrowsecurity,
      'force_row_security', c.relforcerowsecurity,
      'acl', coalesce(c.relacl::text, 'NULL')
    )::text),
    'definition_sql', CASE
      WHEN c.relkind = 'v' THEN format('CREATE VIEW %I.%I AS %s', n.nspname, c.relname, pg_get_viewdef(c.oid, true))
      WHEN c.relkind = 'm' THEN format('CREATE MATERIALIZED VIEW %I.%I AS %s', n.nspname, c.relname, pg_get_viewdef(c.oid, true))
      ELSE NULL
    END
  ) AS item
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
    AND c.relkind IN ('r','p','v','m','f')
),
columns AS (
  SELECT jsonb_build_object(
    'object_key', 'COLUMN:' || table_schema || '.' || table_name || '.' || column_name,
    'object_class', 'COLUMN',
    'name', table_schema || '.' || table_name || '.' || column_name,
    'definition', jsonb_build_object(
      'ordinal_position', ordinal_position,
      'data_type', data_type,
      'udt_schema', udt_schema,
      'udt_name', udt_name,
      'is_nullable', is_nullable,
      'column_default', column_default,
      'character_maximum_length', character_maximum_length,
      'numeric_precision', numeric_precision,
      'numeric_scale', numeric_scale,
      'identity_generation', identity_generation,
      'is_generated', is_generated,
      'generation_expression', generation_expression
    )
  ) AS item
  FROM information_schema.columns
  WHERE table_schema !~ '^pg_' AND table_schema <> 'information_schema'
),
constraints AS (
  SELECT jsonb_build_object(
    'object_key', 'CONSTRAINT:' || n.nspname || '.' || coalesce(t.relname, typ.typname) || '.' || con.conname,
    'object_class', 'CONSTRAINT',
    'name', n.nspname || '.' || coalesce(t.relname, typ.typname) || '.' || con.conname,
    'definition', jsonb_build_object(
      'constraint_type', con.contype,
      'definition', pg_get_constraintdef(con.oid, true),
      'validated', con.convalidated,
      'deferrable', con.condeferrable,
      'initially_deferred', con.condeferred,
      'domain', con.contypid <> 0
    ),
    'dependency_fingerprint', md5(con.conrelid::text || ':' || con.confrelid::text || ':' || con.conindid::text || ':' || con.contypid::text)
  ) AS item
  FROM pg_constraint con
  LEFT JOIN pg_class t ON t.oid = con.conrelid
  LEFT JOIN pg_type typ ON typ.oid = con.contypid
  JOIN pg_namespace n ON n.oid = coalesce(t.relnamespace, typ.typnamespace)
  WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
),
indexes AS (
  SELECT jsonb_build_object(
    'object_key', 'INDEX:' || n.nspname || '.' || t.relname || '.' || i.relname,
    'object_class', 'INDEX',
    'name', n.nspname || '.' || t.relname || '.' || i.relname,
    'definition_sql', pg_get_indexdef(i.oid),
    'definition', jsonb_build_object(
      'valid', x.indisvalid,
      'ready', x.indisready,
      'unique', x.indisunique,
      'primary', x.indisprimary,
      'replica_identity', x.indisreplident,
      'nulls_not_distinct', x.indnullsnotdistinct
    ),
    'dependency_fingerprint', md5(x.indrelid::text || ':' || x.indexrelid::text)
  ) AS item
  FROM pg_index x
  JOIN pg_class i ON i.oid = x.indexrelid
  JOIN pg_class t ON t.oid = x.indrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
  WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
),
routines AS (
  SELECT jsonb_build_object(
    'object_key', (CASE WHEN p.prokind = 'p' THEN 'PROCEDURE:' ELSE 'FUNCTION:' END)
      || n.nspname || '.' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')',
    'object_class', CASE WHEN p.prokind = 'p' THEN 'PROCEDURE' ELSE 'FUNCTION' END,
    'name', n.nspname || '.' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')',
    'definition_sql', pg_get_functiondef(p.oid),
    'definition', jsonb_build_object(
      'result_type', pg_get_function_result(p.oid),
      'language', l.lanname,
      'volatility', p.provolatile,
      'strict', p.proisstrict,
      'security_definer', p.prosecdef,
      'leakproof', p.proleakproof,
      'parallel', p.proparallel,
      'owner', pg_get_userbyid(p.proowner),
      'configuration', p.proconfig
    ),
    'security_fingerprint', md5(jsonb_build_object(
      'security_definer', p.prosecdef,
      'owner', pg_get_userbyid(p.proowner),
      'acl', coalesce(p.proacl::text, 'NULL'),
      'configuration', p.proconfig
    )::text)
  ) AS item
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
  JOIN pg_language l ON l.oid = p.prolang
  WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
    AND p.prokind IN ('f','p')
),
triggers AS (
  SELECT jsonb_build_object(
    'object_key', 'TRIGGER:' || n.nspname || '.' || t.relname || '.' || g.tgname,
    'object_class', 'TRIGGER',
    'name', n.nspname || '.' || t.relname || '.' || g.tgname,
    'definition_sql', pg_get_triggerdef(g.oid, true),
    'definition', jsonb_build_object(
      'enabled', g.tgenabled,
      'internal', g.tgisinternal,
      'constraint_trigger', g.tgconstraint <> 0,
      'function', g.tgfoid::regprocedure::text
    )
  ) AS item
  FROM pg_trigger g
  JOIN pg_class t ON t.oid = g.tgrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
  WHERE NOT g.tgisinternal AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
),
policies AS (
  SELECT jsonb_build_object(
    'object_key', 'RLS_POLICY:' || schemaname || '.' || tablename || '.' || policyname,
    'object_class', 'RLS_POLICY',
    'name', schemaname || '.' || tablename || '.' || policyname,
    'definition', jsonb_build_object(
      'permissive', permissive,
      'roles', roles,
      'command', cmd,
      'using', qual,
      'with_check', with_check
    ),
    'security_fingerprint', md5(jsonb_build_object(
      'permissive', permissive, 'roles', roles, 'command', cmd,
      'using', qual, 'with_check', with_check
    )::text)
  ) AS item
  FROM pg_policies
  WHERE schemaname !~ '^pg_' AND schemaname <> 'information_schema'
),
sequences AS (
  SELECT jsonb_build_object(
    'object_key', 'SEQUENCE:' || n.nspname || '.' || c.relname,
    'object_class', 'SEQUENCE',
    'name', n.nspname || '.' || c.relname,
    'definition', jsonb_build_object(
      'owner', pg_get_userbyid(c.relowner),
      'start_value', s.seqstart, 'increment_by', s.seqincrement,
      'minimum_value', s.seqmin, 'maximum_value', s.seqmax,
      'cache_size', s.seqcache, 'cycle', s.seqcycle,
      'acl', coalesce(c.relacl::text, 'NULL')
    ),
    'security_fingerprint', md5(coalesce(c.relacl::text, 'NULL') || ':' || pg_get_userbyid(c.relowner))
  ) AS item
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  JOIN pg_sequence s ON s.seqrelid = c.oid
  WHERE c.relkind = 'S' AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
),
types AS (
  SELECT jsonb_build_object(
    'object_key', (CASE WHEN t.typtype = 'd' THEN 'DOMAIN:' ELSE 'TYPE:' END) || n.nspname || '.' || t.typname,
    'object_class', CASE WHEN t.typtype = 'd' THEN 'DOMAIN' ELSE 'TYPE' END,
    'name', n.nspname || '.' || t.typname,
    'definition', jsonb_build_object(
      'owner', pg_get_userbyid(t.typowner),
      'type_kind', t.typtype,
      'category', t.typcategory,
      'base_type', CASE WHEN t.typbasetype <> 0 THEN t.typbasetype::regtype::text ELSE NULL END,
      'not_null', t.typnotnull,
      'default', t.typdefault,
      'enum_labels', (SELECT jsonb_agg(e.enumlabel ORDER BY e.enumsortorder) FROM pg_enum e WHERE e.enumtypid = t.oid)
    )
  ) AS item
  FROM pg_type t
  JOIN pg_namespace n ON n.oid = t.typnamespace
  WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
    AND t.typtype IN ('e','d','c','r','b')
    AND t.typname NOT LIKE '\_%'
),
extensions AS (
  SELECT jsonb_build_object(
    'object_key', 'EXTENSION:' || e.extname,
    'object_class', 'EXTENSION',
    'name', e.extname,
    'definition', jsonb_build_object('version', e.extversion, 'schema', n.nspname, 'owner', pg_get_userbyid(e.extowner))
  ) AS item
  FROM pg_extension e
  JOIN pg_namespace n ON n.oid = e.extnamespace
),
acl_entries AS (
  SELECT jsonb_build_object(
    'object_key', 'ACL:' || n.nspname || '.' || c.relname || ':' || x.grantee || ':' || x.privilege_type,
    'object_class', 'ACL',
    'name', n.nspname || '.' || c.relname,
    'definition', jsonb_build_object('grantee', x.grantee, 'grantor', x.grantor, 'privilege', x.privilege_type, 'grantable', x.is_grantable),
    'security_fingerprint', md5(x.grantee || ':' || x.grantor || ':' || x.privilege_type || ':' || x.is_grantable)
  ) AS item
  FROM information_schema.table_privileges x
  JOIN pg_class c ON c.relname = x.table_name
  JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = x.table_schema
  WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
),
dependency_count AS (
  SELECT count(*)::integer AS count FROM pg_depend d WHERE d.deptype <> 'i' AND d.deptype <> 'e'
)

SELECT jsonb_build_object(
  'format', 'moreai.postgresql.observed-catalog.v1',
  'applied_migration_ids', (SELECT coalesce(jsonb_agg(version ORDER BY version), '[]'::jsonb) FROM supabase_migrations.schema_migrations),
  'snapshot_id', to_char(clock_timestamp() AT TIME ZONE 'UTC', 'YYYYMMDD"T"HH24MISS"Z"'),
  'database_version', current_setting('server_version'),
  'expected_source_coverage_complete', false,
  'objects', (
    SELECT coalesce(jsonb_agg(item), '[]'::jsonb)
    FROM (
      SELECT item FROM schemas UNION ALL
      SELECT item FROM relations UNION ALL
      SELECT item FROM columns UNION ALL
      SELECT item FROM constraints UNION ALL
      SELECT item FROM indexes UNION ALL
      SELECT item FROM routines UNION ALL
      SELECT item FROM triggers UNION ALL
      SELECT item FROM policies UNION ALL
      SELECT item FROM sequences UNION ALL
      SELECT item FROM types UNION ALL
      SELECT item FROM extensions UNION ALL
      SELECT item FROM acl_entries
    ) all_objects
  ),
  'dependency_count', (SELECT count FROM dependency_count)
) AS observed_catalog;
