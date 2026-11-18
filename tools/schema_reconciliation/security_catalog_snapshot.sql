-- Read-only security catalog supplement. No data or schema writes.
WITH acl_rows AS (
  SELECT jsonb_build_object(
    'object_key','ACL:SCHEMA:'||n.nspname||':'||CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type,
    'object_class','ACL','name','SCHEMA:'||n.nspname,
    'definition',jsonb_build_object('grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,'grantor',pg_get_userbyid(a.grantor),'privilege',a.privilege_type,'grantable',a.is_grantable)
  ) item
  FROM pg_namespace n CROSS JOIN LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a
  WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'
  UNION ALL
  SELECT jsonb_build_object(
    'object_key','ACL:RELATION:'||n.nspname||'.'||c.relname||':'||CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type,
    'object_class','ACL','name','RELATION:'||n.nspname||'.'||c.relname,
    'definition',jsonb_build_object('grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,'grantor',pg_get_userbyid(a.grantor),'privilege',a.privilege_type,'grantable',a.is_grantable)
  )
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault(CASE WHEN c.relkind='S' THEN 'S'::"char" ELSE 'r'::"char" END,c.relowner))) a
  WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema' AND c.relkind IN ('r','p','v','m','S','f')
  UNION ALL
  SELECT jsonb_build_object(
    'object_key','ACL:ROUTINE:'||n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||'):'||CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type,
    'object_class','ACL','name','ROUTINE:'||n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')',
    'definition',jsonb_build_object('grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,'grantor',pg_get_userbyid(a.grantor),'privilege',a.privilege_type,'grantable',a.is_grantable)
  )
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
  WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema' AND p.prokind IN ('f','p')
  UNION ALL
  SELECT jsonb_build_object(
    'object_key','ACL:TYPE:'||n.nspname||'.'||t.typname||':'||CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type,
    'object_class','ACL','name','TYPE:'||n.nspname||'.'||t.typname,
    'definition',jsonb_build_object('grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,'grantor',pg_get_userbyid(a.grantor),'privilege',a.privilege_type,'grantable',a.is_grantable)
  )
  FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
  CROSS JOIN LATERAL aclexplode(coalesce(t.typacl,acldefault('T',t.typowner))) a
  WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'
),
default_acl AS (
  SELECT jsonb_build_object(
    'object_key','DEFAULT_ACL:'||pg_get_userbyid(d.defaclrole)||':'||coalesce(ns.nspname,'ALL_SCHEMAS')||':'||d.defaclobjtype::text||':'||CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type,
    'object_class','DEFAULT_ACL',
    'definition',jsonb_build_object('owner_role',pg_get_userbyid(d.defaclrole),'schema',ns.nspname,'object_type',d.defaclobjtype::text,'grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,'grantor',pg_get_userbyid(a.grantor),'privilege',a.privilege_type,'grantable',a.is_grantable)
  ) item
  FROM pg_default_acl d LEFT JOIN pg_namespace ns ON ns.oid=d.defaclnamespace
  CROSS JOIN LATERAL aclexplode(d.defaclacl) a
),
memberships AS (
  SELECT jsonb_build_object(
    'object_key','ROLE_MEMBERSHIP:'||granted.rolname||':'||member.rolname,
    'object_class','ROLE_MEMBERSHIP',
    'definition',jsonb_build_object('granted_role',granted.rolname,'member_role',member.rolname,'grantor',pg_get_userbyid(m.grantor),'admin_option',m.admin_option,'inherit_option',m.inherit_option,'set_option',m.set_option)
  ) item
  FROM pg_auth_members m JOIN pg_roles granted ON granted.oid=m.roleid JOIN pg_roles member ON member.oid=m.member
)
SELECT jsonb_build_object(
  'format','moreai.postgresql.observed-security-catalog.v1',
  'snapshot_id',to_char(clock_timestamp() AT TIME ZONE 'UTC','YYYYMMDD"T"HH24MISS"Z"'),
  'database_version',current_setting('server_version'),
  'acl_objects',(SELECT coalesce(jsonb_agg(item),'[]'::jsonb) FROM acl_rows),
  'default_acl_objects',(SELECT coalesce(jsonb_agg(item),'[]'::jsonb) FROM default_acl),
  'role_memberships',(SELECT coalesce(jsonb_agg(item),'[]'::jsonb) FROM memberships),
  'routine_privileges',(SELECT coalesce(jsonb_agg(jsonb_build_object('schema',specific_schema,'specific_name',specific_name,'grantee',grantee,'grantor',grantor,'privilege',privilege_type,'grantable',is_grantable)),'[]'::jsonb) FROM information_schema.routine_privileges WHERE specific_schema !~ '^pg_' AND specific_schema<>'information_schema'),
  'roles',(SELECT coalesce(jsonb_agg(jsonb_build_object('object_key','ROLE:'||rolname,'object_class','ROLE','name',rolname,'definition',jsonb_build_object('superuser',rolsuper,'inherit',rolinherit,'create_role',rolcreaterole,'create_db',rolcreatedb,'can_login',rolcanlogin,'replication',rolreplication,'bypass_rls',rolbypassrls,'connection_limit',rolconnlimit)) ORDER BY rolname),'[]'::jsonb) FROM pg_roles)
) AS observed_security_catalog;
