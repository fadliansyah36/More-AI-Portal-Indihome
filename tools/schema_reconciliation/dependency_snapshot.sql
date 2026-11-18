-- Read-only PostgreSQL dependency edge snapshot.
WITH edges AS (
  SELECT
    d.deptype,
    d.classid::regclass::text AS dependent_catalog_class,
    d.objid,
    d.objsubid,
    d.refclassid::regclass::text AS referenced_catalog_class,
    d.refobjid,
    d.refobjsubid,
    dep.type AS dependent_type,
    dep.schema AS dependent_schema,
    dep.name AS dependent_name,
    dep.identity AS dependent_identity,
    ref.type AS referenced_type,
    ref.schema AS referenced_schema,
    ref.name AS referenced_name,
    ref.identity AS referenced_identity,
    pg_describe_object(d.classid,d.objid,d.objsubid) AS dependent_description,
    pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid) AS referenced_description
  FROM pg_depend d
  CROSS JOIN LATERAL pg_identify_object(d.classid,d.objid,d.objsubid) dep
  CROSS JOIN LATERAL pg_identify_object(d.refclassid,d.refobjid,d.refobjsubid) ref
  WHERE d.deptype NOT IN ('i','e')
    AND (
      (dep.schema IS NOT NULL AND dep.schema !~ '^pg_' AND dep.schema <> 'information_schema')
      OR (ref.schema IS NOT NULL AND ref.schema !~ '^pg_' AND ref.schema <> 'information_schema')
    )
)
SELECT jsonb_build_object(
  'format','moreai.postgresql.observed-dependency-graph.v1',
  'snapshot_id',to_char(clock_timestamp() AT TIME ZONE 'UTC','YYYYMMDD"T"HH24MISS"Z"'),
  'database_version',current_setting('server_version'),
  'edge_count',(SELECT count(*) FROM edges),
  'edges',(SELECT coalesce(jsonb_agg(jsonb_build_object(
    'dependency_type',deptype,
    'dependent_catalog_class',dependent_catalog_class,
    'dependent_type',dependent_type,
    'dependent_schema',dependent_schema,
    'dependent_name',dependent_name,
    'dependent_identity',dependent_identity,
    'dependent_description',dependent_description,
    'referenced_catalog_class',referenced_catalog_class,
    'referenced_type',referenced_type,
    'referenced_schema',referenced_schema,
    'referenced_name',referenced_name,
    'referenced_identity',referenced_identity,
    'referenced_description',referenced_description
  ) ORDER BY dependent_schema,dependent_identity,referenced_schema,referenced_identity),'[]'::jsonb) FROM edges)
) AS observed_dependency_graph;
