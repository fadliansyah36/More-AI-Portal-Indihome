from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import schema_graph


class SemanticObjectGraphTests(unittest.TestCase):
    def test_rangevar_identity_supports_wrapped_and_raw_postgresql_nodes(self):
        self.assertEqual(
            schema_graph._rangevars({
                "relation": {"schemaname": "public", "relname": "profiles", "relpersistence": "p"}
            }),
            ["public.profiles"],
        )
        self.assertEqual(
            schema_graph._rangevars({
                "RangeVar": {"schemaname": "auth", "relname": "users", "relpersistence": "p"}
            }),
            ["auth.users"],
        )

    def test_grant_targets_keep_schema_and_function_signature_identity(self):
        schema = schema_graph._object_names(
            "GrantStmt",
            {"objtype": "OBJECT_SCHEMA", "objects": [{"String": {"sval": "public"}}]},
        )
        function = schema_graph._object_names(
            "GrantStmt",
            {
                "objtype": "OBJECT_FUNCTION",
                "objects": [{
                    "ObjectWithArgs": {
                        "objname": [{"String": {"sval": "public"}}, {"String": {"sval": "lookup_user"}}],
                        "objargs": [{"TypeName": {"names": [{"String": {"sval": "uuid"}}]}}],
                    }
                }],
            },
        )
        self.assertEqual(schema, ["public"])
        self.assertEqual(function, ["public.lookup_user(uuid)"])

    def test_create_table_emits_stable_column_and_constraint_events(self):
        payload = {
            "relation": {"schemaname": "public", "relname": "profiles", "relpersistence": "p"},
            "tableElts": [
                {"ColumnDef": {"colname": "id", "typeName": {"names": [{"String": {"sval": "uuid"}}]}}},
                {"Constraint": {"conname": "profiles_pk", "contype": "CONSTR_PRIMARY"}},
            ],
        }
        events = schema_graph._table_subobject_events(
            "CreateStmt", payload, migration_id="20261125000000",
            relative="fixture.sql", source_sha256="a" * 64, git_blob_sha1="b" * 40,
            statement_ordinal=1, parent_name="public.profiles", operation="CREATE",
        )
        self.assertEqual(
            {(item["object_class"], item["object_name"], item["operation"]) for item in events},
            {
                ("COLUMN", "public.profiles.id", "CREATE"),
                ("CONSTRAINT", "public.profiles.profiles_pk", "CREATE"),
            },
        )

    def test_column_reducer_folds_not_null_transition(self):
        history = [
            {
                "object_class": "COLUMN", "operation": "CREATE",
                "normalized_ast": {"ColumnDef": {"colname": "id", "is_not_null": False}},
            },
            {
                "object_class": "COLUMN", "operation": "ALTER",
                "normalized_ast": {"AlterTableCmd": {"subtype": "AT_SetNotNull"}},
            },
        ]
        status, definition, reduction = schema_graph._reduce_table_subobject_history(history)
        self.assertEqual(status, "REDUCED_TABLE_SUBOBJECT_DEFINITION")
        self.assertEqual(reduction, "TABLE_SUBOBJECT_EVENT_CHAIN_REDUCED")
        self.assertTrue(definition["ColumnDef"]["is_not_null"])

    def test_owner_changes_use_typed_object_identity_and_reduce_last_owner(self):
        payload = {
            "objectType": "OBJECT_TABLE",
            "object": {"RangeVar": {"schemaname": "public", "relname": "profiles", "relpersistence": "p"}},
            "newowner": {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "service_owner"}},
        }
        self.assertEqual(
            schema_graph._object_names("AlterOwnerStmt", payload),
            ["OBJECT_TABLE:public.profiles"],
        )
        status, definition, reduction = schema_graph._reduce_ownership_history([
            {"normalized_ast": {"AlterOwnerStmt": payload}},
        ])
        self.assertEqual(status, "REDUCED_OWNER_STATE")
        self.assertEqual(reduction, "OWNER_ROLE_REDUCED_FROM_AST")
        self.assertEqual(definition, {"Owner": {"role": "service_owner"}})

    def test_acl_reducer_folds_grant_option_revoke(self):
        base = {
            "objtype": "OBJECT_TABLE",
            "privileges": [{"AccessPriv": {"priv_name": "select"}}],
            "grantees": [{"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "authenticated"}}],
            "behavior": "DROP_RESTRICT",
        }
        history = [
            {"normalized_ast": {"GrantStmt": {**base, "is_grant": True, "grant_option": True}}},
            {"normalized_ast": {"GrantStmt": {**base, "is_grant": False, "grant_option": True}}},
        ]
        status, definition, reduction = schema_graph._reduce_acl_history(history)
        self.assertEqual(status, "REDUCED_PRIVILEGE_SET_GRANTOR_UNVERIFIED")
        self.assertEqual(reduction, status)
        grants = definition["EffectiveACL"]["grants"]
        self.assertEqual(len(grants), 1)
        self.assertEqual(grants[0]["grantee"], "authenticated")
        self.assertEqual(grants[0]["privilege"], "select")
        self.assertFalse(grants[0]["grant_option"])

    def test_acl_reducer_expands_all_table_privileges_for_grant_and_revoke(self):
        base = {
            "objtype": "OBJECT_TABLE",
            "grantees": [{"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "service_role"}}],
            "behavior": "DROP_RESTRICT",
        }
        history = [
            {"normalized_ast": {"GrantStmt": {**base, "is_grant": True}}},
            {"normalized_ast": {"GrantStmt": {**base, "is_grant": False}}},
        ]
        status, definition, _ = schema_graph._reduce_acl_history(history)
        self.assertEqual(status, "REDUCED_PRIVILEGE_SET_GRANTOR_UNVERIFIED")
        self.assertEqual(definition["EffectiveACL"]["grants"], [])
        grant_status, grant_definition, _ = schema_graph._reduce_acl_history([
            {"normalized_ast": {"GrantStmt": {**base, "is_grant": True, "grant_option": False}}},
        ])
        self.assertEqual(grant_status, "REDUCED_PRIVILEGE_SET_GRANTOR_UNVERIFIED")
        self.assertIn(
            "maintain",
            [item["privilege"] for item in grant_definition["EffectiveACL"]["grants"]],
        )

    def test_acl_reducer_removes_explicitly_revoked_privilege(self):
        base = {
            "objtype": "OBJECT_TABLE",
            "privileges": [{"AccessPriv": {"priv_name": "insert"}}],
            "grantees": [{"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "authenticated"}}],
            "behavior": "DROP_RESTRICT",
        }
        history = [
            {"normalized_ast": {"GrantStmt": {**base, "is_grant": True, "grant_option": False}}},
            {"normalized_ast": {"GrantStmt": {**base, "is_grant": False, "grant_option": False}}},
        ]
        status, definition, _ = schema_graph._reduce_acl_history(history)
        self.assertEqual(status, "REDUCED_PRIVILEGE_SET_GRANTOR_UNVERIFIED")
        self.assertEqual(definition["EffectiveACL"]["grants"], [])

    def test_drop_table_targets_preserve_each_qualified_identity(self):
        payload = {
            "removeType": "OBJECT_TABLE",
            "objects": [
                {"List": [{"String": {"sval": "public"}}, {"String": {"sval": "profiles"}}]},
                {"List": [{"String": {"sval": "billing"}}, {"String": {"sval": "invoices"}}]},
            ],
        }
        self.assertEqual(
            schema_graph._object_names("DropStmt", payload),
            ["public.profiles", "billing.invoices"],
        )
        self.assertEqual(
            schema_graph.DROP_OBJECT_CLASS[payload["removeType"]],
            "TABLE",
        )

    def test_drop_function_preserves_signature_and_class(self):
        payload = {
            "removeType": "OBJECT_FUNCTION",
            "objects": [{
                "ObjectWithArgs": {
                    "objname": [
                        {"String": {"sval": "public"}},
                        {"String": {"sval": "recalculate_invoice"}},
                    ],
                    "objargs": [{
                        "TypeName": {
                            "names": [{"String": {"sval": "uuid"}}],
                        },
                    }],
                },
            }],
        }
        self.assertEqual(
            schema_graph._object_names("DropStmt", payload),
            ["public.recalculate_invoice(uuid)"],
        )
        self.assertEqual(
            schema_graph.DROP_OBJECT_CLASS[payload["removeType"]],
            "FUNCTION",
        )

    def test_drop_targets_are_not_flattened_into_one_invalid_name(self):
        payload = {
            "removeType": "OBJECT_SEQUENCE",
            "objects": [
                {"List": [{"String": {"sval": "public"}}, {"String": {"sval": "invoice_id_seq"}}]},
                {"List": [{"String": {"sval": "public"}}, {"String": {"sval": "event_id_seq"}}]},
            ],
        }
        names = schema_graph._object_names("DropStmt", payload)
        self.assertEqual(len(names), 2)
        self.assertNotIn("public.invoice_id_seq.public.event_id_seq", names)


if __name__ == "__main__":
    unittest.main()
