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

    def test_column_reducer_preserves_using_expression_for_type_change(self):
        using_expression = {
            "FuncCall": {
                "funcname": [{"String": {"sval": "public"}}, {"String": {"sval": "normalize_code"}}],
                "args": [{"ColumnRef": {"fields": [{"String": {"sval": "code"}}]}}],
            },
        }
        history = [
            {
                "object_class": "COLUMN", "operation": "CREATE",
                "normalized_ast": {"ColumnDef": {
                    "colname": "code",
                    "typeName": {"TypeName": {"names": [{"String": {"sval": "text"}}]}},
                }},
            },
            {
                "object_class": "COLUMN", "operation": "ALTER",
                "normalized_ast": {"AlterTableCmd": {
                    "subtype": "AT_AlterColumnType",
                    "name": "code",
                    "def": {"TypeName": {"names": [{"String": {"sval": "varchar"}}, {"String": {"sval": "64"}}]}},
                    "transform": using_expression,
                }},
            },
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(history)
        self.assertEqual(status, "REDUCED_TABLE_SUBOBJECT_DEFINITION")
        self.assertEqual(reason, "TABLE_SUBOBJECT_EVENT_CHAIN_REDUCED")
        self.assertEqual(definition["ColumnDef"]["type_change_using"], using_expression)
        self.assertEqual(
            definition["ColumnDef"]["typeName"],
            {"TypeName": {"names": [{"String": {"sval": "varchar"}}, {"String": {"sval": "64"}}]}},
        )

    def test_column_reducer_clears_stale_using_expression_on_later_plain_type_change(self):
        first_transform = {"A_Const": {"val": {"Integer": {"ival": 1}}}}
        history = [
            {"object_class": "COLUMN", "operation": "CREATE", "normalized_ast": {"ColumnDef": {"colname": "code"}}},
            {"object_class": "COLUMN", "operation": "ALTER", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_AlterColumnType",
                "name": "code",
                "def": {"TypeName": {"names": [{"String": {"sval": "integer"}}]}},
                "transform": first_transform,
            }}},
            {"object_class": "COLUMN", "operation": "ALTER", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_AlterColumnType",
                "def": {"TypeName": {"names": [{"String": {"sval": "bigint"}}]}},
                "transform": None,
            }}},
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(history)
        self.assertEqual(status, "REDUCED_TABLE_SUBOBJECT_DEFINITION")
        self.assertNotIn("type_change_using", definition["ColumnDef"])

    def test_column_reducer_rejects_alter_for_different_column_name(self):
        history = [
            {"object_class": "COLUMN", "operation": "CREATE", "normalized_ast": {"ColumnDef": {"colname": "status"}}},
            {"object_class": "COLUMN", "operation": "ALTER", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_SetNotNull",
                "name": "another_column",
            }}},
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "COLUMN_ALTER_TARGET_MISMATCH")

    def test_column_reducer_folds_not_null_transition(self):
        history = [
            {
                "object_class": "COLUMN", "operation": "CREATE",
                "normalized_ast": {"ColumnDef": {"colname": "id", "is_not_null": False}},
            },
            {
                "object_class": "COLUMN", "operation": "ALTER",
                "normalized_ast": {"AlterTableCmd": {"subtype": "AT_SetNotNull", "name": "id"}},
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

    def test_zero_argument_function_signature_is_preserved_for_drop_and_grant(self):
        object_with_args = {
            "ObjectWithArgs": {
                "objname": [
                    {"String": {"sval": "public"}},
                    {"String": {"sval": "refresh_cache"}},
                ],
                "objargs": [],
            },
        }
        self.assertEqual(
            schema_graph._object_names("DropStmt", {
                "removeType": "OBJECT_FUNCTION",
                "objects": [object_with_args],
            }),
            ["public.refresh_cache()"],
        )
        self.assertEqual(
            schema_graph._object_names("GrantStmt", {
                "objtype": "OBJECT_FUNCTION",
                "objects": [object_with_args],
            }),
            ["public.refresh_cache()"],
        )

    def test_drop_unqualified_relation_does_not_invent_public_schema(self):
        self.assertEqual(
            schema_graph._object_names("DropStmt", {
                "removeType": "OBJECT_TABLE",
                "objects": [{"List": [{"String": {"sval": "customer_events"}}]}],
            }),
            ["customer_events"],
        )

    def test_drop_schema_identity_is_not_schema_qualified(self):
        self.assertEqual(
            schema_graph._object_names("DropStmt", {
                "removeType": "OBJECT_SCHEMA",
                "objects": [{"List": [{"String": {"sval": "analytics"}}]}],
            }),
            ["analytics"],
        )

    def test_policy_reducer_applies_only_explicit_alter_clauses(self):
        table = {"RangeVar": {"schemaname": "public", "relname": "documents"}}
        create = {
            "policy_name": "documents_read",
            "table": table,
            "permissive": True,
            "cmd_name": "CMD_SELECT",
            "roles": [{"RoleSpec": {"roletype": "ROLESPEC_PUBLIC"}}],
            "qual": {"A_Expr": {"kind": "AEXPR_OP", "name": [{"String": {"sval": "="}}]}},
            "with_check": {"A_Expr": {"kind": "AEXPR_OP", "name": [{"String": {"sval": ">"}}]}},
        }
        alter = {
            "policy_name": "documents_read",
            "table": table,
            "roles": [{"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "authenticated"}}],
            "qual": {"A_Expr": {"kind": "AEXPR_OP", "name": [{"String": {"sval": "<>"}}]}},
            "with_check": None,
        }
        status, definition, reason = schema_graph._reduce_policy_history([
            {"operation": "CREATE", "normalized_ast": {"CreatePolicyStmt": create}},
            {"operation": "ALTER", "normalized_ast": {"AlterPolicyStmt": alter}},
        ])
        self.assertEqual(status, "REDUCED_POLICY_STATE")
        self.assertEqual(reason, "POLICY_CREATE_ALTER_CHAIN_REDUCED")
        reduced = definition["CreatePolicyStmt"]
        self.assertEqual(reduced["roles"], alter["roles"])
        self.assertEqual(reduced["qual"], alter["qual"])
        self.assertEqual(reduced["with_check"], create["with_check"])
        self.assertEqual(reduced["cmd_name"], "CMD_SELECT")
        self.assertTrue(reduced["permissive"])

    def test_policy_reducer_fails_closed_when_alter_changes_table_identity(self):
        create = {
            "policy_name": "documents_read",
            "table": {"RangeVar": {"schemaname": "public", "relname": "documents"}},
            "roles": [],
        }
        alter = {
            "policy_name": "documents_read",
            "table": {"RangeVar": {"schemaname": "private", "relname": "documents"}},
            "roles": [],
        }
        status, definition, reason = schema_graph._reduce_policy_history([
            {"operation": "CREATE", "normalized_ast": {"CreatePolicyStmt": create}},
            {"operation": "ALTER", "normalized_ast": {"AlterPolicyStmt": alter}},
        ])
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "POLICY_TABLE_IDENTITY_CHANGED")

    def test_policy_object_identity_uses_postgresql_table_field(self):
        payload = {
            "policy_name": "documents_read",
            "table": {"RangeVar": {"schemaname": "public", "relname": "documents"}},
            "roles": [],
        }
        self.assertEqual(
            schema_graph._object_names("CreatePolicyStmt", payload),
            ["public.documents.documents_read"],
        )
        self.assertEqual(
            schema_graph._object_names("AlterPolicyStmt", payload),
            ["public.documents.documents_read"],
        )

    def test_enum_reducer_folds_add_before_after_and_rename_value(self):
        create = {
            "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
            "vals": [{"String": {"sval": "queued"}}, {"String": {"sval": "running"}}, {"String": {"sval": "done"}}],
        }
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateEnumStmt": create}},
            {"operation": "ALTER", "normalized_ast": {"AlterEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
                "newVal": {"String": {"sval": "blocked"}},
                "newValNeighbor": {"String": {"sval": "running"}},
                "newValIsAfter": False,
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
                "newVal": {"String": {"sval": "paused"}},
                "newValNeighbor": {"String": {"sval": "running"}},
                "newValIsAfter": True,
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
                "oldVal": {"String": {"sval": "done"}},
                "newVal": {"String": {"sval": "completed"}},
            }}},
        ]
        status, definition, reason = schema_graph._reduce_enum_type_history(history)
        self.assertEqual(status, "REDUCED_ENUM_TYPE_STATE")
        self.assertEqual(reason, "ENUM_CREATE_ALTER_CHAIN_REDUCED")
        labels = [item["String"]["sval"] for item in definition["CreateEnumStmt"]["vals"]]
        self.assertEqual(labels, ["queued", "blocked", "running", "paused", "completed"])

    def test_enum_reducer_rejects_alter_for_different_type_identity(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
                "vals": [{"String": {"sval": "queued"}}],
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "other_state"}}],
                "newVal": {"String": {"sval": "blocked"}},
            }}},
        ]
        status, definition, reason = schema_graph._reduce_enum_type_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "ENUM_ALTER_TARGET_MISMATCH")

    def test_enum_reducer_fails_closed_when_alter_type_identity_is_missing(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
                "vals": [{"String": {"sval": "queued"}}],
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterEnumStmt": {
                "newVal": {"String": {"sval": "blocked"}},
            }}},
        ]
        status, definition, reason = schema_graph._reduce_enum_type_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "ENUM_ALTER_TYPE_IDENTITY_UNRESOLVED")

    def test_enum_reducer_fails_closed_when_add_value_neighbor_is_unknown(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
                "vals": [{"String": {"sval": "queued"}}],
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterEnumStmt": {
                "typeName": [{"String": {"sval": "public"}}, {"String": {"sval": "job_state"}}],
                "newVal": {"String": {"sval": "blocked"}},
                "newValNeighbor": {"String": {"sval": "missing"}},
                "newValIsAfter": True,
            }}},
        ]
        status, definition, reason = schema_graph._reduce_enum_type_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "ENUM_ADD_NEIGHBOR_NOT_FOUND")

    def test_alter_function_identity_matches_create_function_signature(self):
        function = {
            "ObjectWithArgs": {
                "objname": [
                    {"String": {"sval": "public"}},
                    {"String": {"sval": "calculate_total"}},
                ],
                "objargs": [{
                    "TypeName": {
                        "names": [{"String": {"sval": "numeric"}}],
                    },
                }],
            },
        }
        self.assertEqual(
            schema_graph._object_names("AlterFunctionStmt", {"func": function}),
            ["public.calculate_total(numeric)"],
        )


    def test_sequence_reducer_folds_explicit_create_and_alter_options(self):
        create = {
            "sequence": {"RangeVar": {"schemaname": "public", "relname": "invoice_seq"}},
            "options": [
                {"DefElem": {"defname": "increment", "arg": {"A_Const": {"val": {"Integer": {"ival": 1}}}}}},
                {"DefElem": {"defname": "cache", "arg": {"A_Const": {"val": {"Integer": {"ival": 1}}}}}},
            ],
        }
        alter = {
            "sequence": {"RangeVar": {"schemaname": "public", "relname": "invoice_seq"}},
            "options": [
                {"DefElem": {"defname": "increment", "arg": {"A_Const": {"val": {"Integer": {"ival": 5}}}}}},
                {"DefElem": {"defname": "cycle", "arg": {"A_Const": {"val": {"Boolean": {"boolval": True}}}}}},
            ],
        }
        status, definition, reason = schema_graph._reduce_sequence_history([
            {"operation": "CREATE", "normalized_ast": {"CreateSeqStmt": create}},
            {"operation": "ALTER", "normalized_ast": {"AlterSeqStmt": alter}},
        ])
        self.assertEqual(status, "REDUCED_SEQUENCE_EXPLICIT_OPTIONS_PARTIAL")
        self.assertEqual(reason, "SEQUENCE_CREATE_ALTER_EXPLICIT_OPTIONS_REDUCED")
        self.assertEqual(definition["SequenceOptions"]["explicit"], {
            "increment": 5, "cache": 1, "cycle": True,
        })
        self.assertEqual(definition["SequenceOptions"]["runtime_state"], "NOT_INCLUDED")

    def test_sequence_reducer_fails_closed_for_restart_runtime_state(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateSeqStmt": {
                "sequence": {"RangeVar": {"schemaname": "public", "relname": "invoice_seq"}},
                "options": [],
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterSeqStmt": {
                "sequence": {"RangeVar": {"schemaname": "public", "relname": "invoice_seq"}},
                "options": [{"DefElem": {"defname": "restart", "arg": {"A_Const": {"val": {"Integer": {"ival": 20}}}}}}],
            }}},
        ]
        status, definition, reason = schema_graph._reduce_sequence_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "SEQUENCE_OPTION_UNSUPPORTED:restart")

    def test_sequence_reducer_rejects_alter_for_different_sequence(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateSeqStmt": {
                "sequence": {"RangeVar": {"schemaname": "public", "relname": "invoice_seq"}},
                "options": [],
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterSeqStmt": {
                "sequence": {"RangeVar": {"schemaname": "public", "relname": "event_seq"}},
                "options": [],
            }}},
        ]
        status, definition, reason = schema_graph._reduce_sequence_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "SEQUENCE_ALTER_TARGET_MISMATCH")

    def test_sequence_reducer_fails_closed_when_alter_identity_is_missing(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateSeqStmt": {
                "sequence": {"RangeVar": {"schemaname": "public", "relname": "invoice_seq"}},
                "options": [],
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterSeqStmt": {"options": []}}},
        ]
        status, definition, reason = schema_graph._reduce_sequence_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "SEQUENCE_ALTER_IDENTITY_UNRESOLVED")

    def test_sequence_reducer_requires_source_create(self):
        status, definition, reason = schema_graph._reduce_sequence_history([
            {"operation": "ALTER", "normalized_ast": {"AlterSeqStmt": {"options": []}}},
        ])
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "SEQUENCE_ALTER_WITHOUT_SOURCE_CREATE")


    def test_column_reducer_folds_cooked_default_on_update_and_storage_options(self):
        base = {"colname": "status", "typeName": {"TypeName": {"names": [{"String": {"sval": "text"}}]}}}
        events = [
            {"operation": "CREATE", "object_class": "COLUMN", "normalized_ast": {"ColumnDef": base}},
            {"operation": "ALTER", "object_class": "COLUMN", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_CookedColumnDefault",
                "name": "status",
                "def": {"A_Const": {"val": {"String": {"sval": "draft"}}}},
            }}},
            {"operation": "ALTER", "object_class": "COLUMN", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_ColumnOnUpdate",
                "name": "status",
                "def": {"FuncCall": {"funcname": [{"String": {"sval": "now"}}]}},
            }}},
            {"operation": "ALTER", "object_class": "COLUMN", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_SetStorage",
                "name": "status",
                "def": {"String": {"sval": "EXTENDED"}},
            }}},
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(events)
        self.assertEqual(status, "REDUCED_TABLE_SUBOBJECT_DEFINITION")
        self.assertEqual(reason, "TABLE_SUBOBJECT_EVENT_CHAIN_REDUCED")
        column = definition["ColumnDef"]
        self.assertIn("cooked_default", column)
        self.assertIn("on_update", column)
        self.assertEqual(column["column_options"]["AT_SetStorage"], {"String": {"sval": "EXTENDED"}})

    def test_column_reducer_keeps_unknown_alter_subtype_unverifiable(self):
        events = [
            {"operation": "CREATE", "object_class": "COLUMN", "normalized_ast": {"ColumnDef": {"colname": "status"}}},
            {"operation": "ALTER", "object_class": "COLUMN", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_UnknownFutureSubtype", "name": "status",
            }}},
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(events)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "ALTER_SUBTYPE_NOT_SUPPORTED_BY_COLUMN_REDUCER:AT_UnknownFutureSubtype")


    def test_constraint_reducer_folds_explicit_deferrability_change(self):
        base = {
            "contype": "CONSTR_FOREIGN",
            "conname": "orders_customer_fk",
            "deferrable": False,
            "initdeferred": False,
            "skip_validation": True,
        }
        history = [
            {"operation": "CREATE", "object_class": "CONSTRAINT", "normalized_ast": {"Constraint": base}},
            {"operation": "ALTER", "object_class": "CONSTRAINT", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_AlterConstraint",
                "name": "orders_customer_fk",
                "deferrable": True,
                "initdeferred": True,
            }}},
            {"operation": "ALTER", "object_class": "CONSTRAINT", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_ValidateConstraint",
                "name": "orders_customer_fk",
            }}},
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(history)
        self.assertEqual(status, "REDUCED_TABLE_SUBOBJECT_DEFINITION")
        self.assertEqual(reason, "TABLE_SUBOBJECT_EVENT_CHAIN_REDUCED")
        constraint = definition["Constraint"]
        self.assertTrue(constraint["deferrable"])
        self.assertTrue(constraint["initdeferred"])
        self.assertFalse(constraint["skip_validation"])

    def test_constraint_reducer_rejects_alter_for_different_constraint_name(self):
        history = [
            {"operation": "CREATE", "object_class": "CONSTRAINT", "normalized_ast": {"Constraint": {
                "conname": "orders_customer_fk", "deferrable": False, "initdeferred": False,
            }}},
            {"operation": "ALTER", "object_class": "CONSTRAINT", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_AlterConstraint",
                "name": "another_constraint",
                "deferrable": True,
                "initdeferred": True,
            }}},
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "CONSTRAINT_ALTER_TARGET_MISMATCH")

    def test_constraint_reducer_fails_closed_for_implicit_deferrability_flags(self):
        history = [
            {"operation": "CREATE", "object_class": "CONSTRAINT", "normalized_ast": {"Constraint": {"conname": "orders_customer_fk"}}},
            {"operation": "ALTER", "object_class": "CONSTRAINT", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_AlterConstraint",
                "name": "orders_customer_fk",
                "deferrable": True,
            }}},
        ]
        status, definition, reason = schema_graph._reduce_table_subobject_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "CONSTRAINT_DEFERRABILITY_FLAGS_UNRESOLVED")


    def test_trigger_reducer_folds_named_enablement_modes(self):
        create = {
            "trigname": "audit_change",
            "relation": {"RangeVar": {"schemaname": "public", "relname": "profiles"}},
            "funcname": [{"String": {"sval": "audit_profile_change"}}],
        }
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateTrigStmt": create}},
            {"operation": "ALTER", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_DisableTrig", "name": "audit_change",
            }}},
            {"operation": "ALTER", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_EnableAlwaysTrig", "name": "audit_change",
            }}},
        ]
        status, definition, reason = schema_graph._reduce_trigger_history(history)
        self.assertEqual(status, "REDUCED_TRIGGER_STATE")
        self.assertEqual(reason, "TRIGGER_CREATE_ALTER_ENABLEMENT_REDUCED")
        self.assertEqual(definition["Trigger"]["enabled_mode"], "ALWAYS")
        self.assertIn("CreateTrigStmt", definition["Trigger"]["definition_ast"])

    def test_trigger_reducer_fails_closed_for_unnamed_or_unsupported_alter(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateTrigStmt": {"trigname": "audit_change"}}},
            {"operation": "ALTER", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_EnableTrigAll", "name": None,
            }}},
        ]
        status, definition, reason = schema_graph._reduce_trigger_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "TRIGGER_ALTER_SUBTYPE_UNSUPPORTED:AT_EnableTrigAll")


    def test_trigger_reducer_rejects_alter_for_different_trigger_name(self):
        history = [
            {"operation": "CREATE", "normalized_ast": {"CreateTrigStmt": {"trigname": "audit_change"}}},
            {"operation": "ALTER", "normalized_ast": {"AlterTableCmd": {
                "subtype": "AT_DisableTrig", "name": "other_trigger",
            }}},
        ]
        status, definition, reason = schema_graph._reduce_trigger_history(history)
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "TRIGGER_ALTER_TARGET_MISMATCH")

    def test_acl_reducer_does_not_claim_effective_acl_without_grantor(self):
        grant = {
            "objtype": "OBJECT_TABLE",
            "privileges": [{"AccessPriv": {"priv_name": "select"}}],
            "grantees": [{"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "analyst"}}],
            "is_grant": True,
            "grant_option": False,
            "behavior": "DROP_RESTRICT",
        }
        status, definition, reason = schema_graph._reduce_acl_history([
            {"operation": "GRANT_OR_REVOKE", "normalized_ast": {"GrantStmt": grant}},
        ])
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "ACL_GRANTOR_UNRESOLVED_EFFECTIVE_ACL_NOT_COMPARABLE")

    def test_acl_reducer_tracks_grant_option_revoke_for_explicit_grantor(self):
        grantor = {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "owner_role"}}
        grantee = {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "analyst"}}
        grant = {
            "objtype": "OBJECT_TABLE",
            "privileges": [{"AccessPriv": {"priv_name": "select"}}],
            "grantees": [grantee], "grantor": grantor,
            "is_grant": True, "grant_option": True, "behavior": "DROP_RESTRICT",
        }
        revoke_option = {
            "objtype": "OBJECT_TABLE",
            "privileges": [{"AccessPriv": {"priv_name": "select"}}],
            "grantees": [grantee], "grantor": grantor,
            "is_grant": False, "grant_option": True, "behavior": "DROP_RESTRICT",
        }
        status, definition, reason = schema_graph._reduce_acl_history([
            {"operation": "GRANT_OR_REVOKE", "normalized_ast": {"GrantStmt": grant}},
            {"operation": "GRANT_OR_REVOKE", "normalized_ast": {"GrantStmt": revoke_option}},
        ])
        self.assertEqual(status, "REDUCED_EXPLICIT_EFFECTIVE_ACL")
        self.assertEqual(reason, "ACL_EXPLICIT_GRANTOR_PRIVILEGE_SET_REDUCED")
        self.assertEqual(definition["EffectiveACL"]["grants"], [{
            "grantee": "analyst", "privilege": "select",
            "grantor": "owner_role", "grant_option": False,
        }])


    def test_role_membership_identity_pairs_each_member_with_granted_role(self):
        payload = {
            "granted_roles": [
                {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "analyst"}},
                {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "report_reader"}},
            ],
            "grantee_roles": [
                {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "alice"}},
                {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "bob"}},
            ],
        }
        self.assertEqual(
            schema_graph._object_names("GrantRoleStmt", payload),
            [
                "member:alice->role:analyst",
                "member:alice->role:report_reader",
                "member:bob->role:analyst",
                "member:bob->role:report_reader",
            ],
        )

    def test_role_membership_reducer_folds_explicit_grant_and_revoke(self):
        role = {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "analyst"}}
        member = {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "alice"}}
        grantor = {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "security_admin"}}
        grant = {
            "granted_roles": [role], "grantee_roles": [member], "grantor": grantor,
            "is_grant": True, "admin_opt": True, "inherit_opt": True,
            "set_opt": True, "behavior": "DROP_RESTRICT",
        }
        revoke = {**grant, "is_grant": False, "admin_opt": False, "inherit_opt": False, "set_opt": False}
        status, definition, reason = schema_graph._reduce_role_membership_history([
            {"object_name": "member:alice->role:analyst", "normalized_ast": {"GrantRoleStmt": grant}},
            {"object_name": "member:alice->role:analyst", "normalized_ast": {"GrantRoleStmt": revoke}},
        ])
        self.assertEqual(status, "REDUCED_EXPLICIT_ROLE_MEMBERSHIP")
        self.assertEqual(reason, "ROLE_MEMBERSHIP_EXPLICIT_GRANT_REVOKE_REDUCED")
        self.assertEqual(definition["RoleMembership"]["memberships"], [])

    def test_role_membership_reducer_fails_closed_when_role_options_are_implicit(self):
        payload = {
            "granted_roles": [{"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "analyst"}}],
            "grantee_roles": [{"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "alice"}}],
            "grantor": {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "security_admin"}},
            "is_grant": True, "admin_opt": False, "inherit_opt": None, "set_opt": None,
        }
        status, definition, reason = schema_graph._reduce_role_membership_history([
            {"object_name": "member:alice->role:analyst", "normalized_ast": {"GrantRoleStmt": payload}},
        ])
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "ROLE_MEMBERSHIP_OPTIONS_REQUIRE_ROLE_CATALOG")



    def test_default_acl_identity_is_scoped_by_owner_schema_and_object_type(self):
        payload = {
            "defaclrole": {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "app_owner"}},
            "defaclnamespace": [{"String": {"sval": "public"}}, {"String": {"sval": "reporting"}}],
            "action": {"GrantStmt": {"objtype": "OBJECT_TABLE"}},
        }
        self.assertEqual(
            schema_graph._object_names("AlterDefaultPrivilegesStmt", payload),
            [
                "role:app_owner|schema:public|object:OBJECT_TABLE",
                "role:app_owner|schema:reporting|object:OBJECT_TABLE",
            ],
        )

    def test_default_acl_reducer_folds_explicit_grant_and_revoke(self):
        owner = {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "app_owner"}}
        analyst = {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "analyst"}}
        action = {
            "objtype": "OBJECT_TABLE",
            "privileges": [{"AccessPriv": {"priv_name": "select"}}],
            "grantees": [analyst],
            "is_grant": True,
            "grant_option": True,
            "behavior": "DROP_RESTRICT",
        }
        defacl = {
            "defaclrole": owner,
            "defaclnamespace": [{"String": {"sval": "public"}}],
            "action": {"GrantStmt": action},
        }
        revoke = {
            **defacl,
            "action": {"GrantStmt": {**action, "is_grant": False, "grant_option": False}},
        }
        target = "role:app_owner|schema:public|object:OBJECT_TABLE"
        status, definition, reason = schema_graph._reduce_default_acl_history([
            {"object_name": target, "normalized_ast": {"AlterDefaultPrivilegesStmt": defacl}},
            {"object_name": target, "normalized_ast": {"AlterDefaultPrivilegesStmt": revoke}},
        ])
        self.assertEqual(status, "REDUCED_EXPLICIT_DEFAULT_ACL")
        self.assertEqual(reason, "DEFAULT_ACL_EXPLICIT_GRANT_REVOKE_REDUCED")
        self.assertEqual(definition["DefaultACL"], {
            "owner": "app_owner", "schema": "public", "object_type": "OBJECT_TABLE", "grants": [],
        })

    def test_default_acl_reducer_fails_closed_for_implicit_owner(self):
        payload = {
            "defaclnamespace": [{"String": {"sval": "public"}}],
            "action": {"GrantStmt": {
                "objtype": "OBJECT_TABLE", "grantees": [
                    {"RoleSpec": {"roletype": "ROLESPEC_CSTRING", "rolename": "analyst"}}
                ], "is_grant": True,
            }},
        }
        status, definition, reason = schema_graph._reduce_default_acl_history([
            {"object_name": "DEFAULT_ACL:IDENTITY_NOT_VERIFIABLE", "normalized_ast": {"AlterDefaultPrivilegesStmt": payload}},
        ])
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "DEFAULT_ACL_OWNER_ROLE_UNRESOLVED")



    def test_function_reducer_folds_scalar_alter_options_and_preserves_body(self):
        create = {
            "CreateFunctionStmt": {
                "options": [
                    {"DefElem": {"defname": "language", "arg": {"String": {"sval": "sql"}}}},
                    {"DefElem": {"defname": "volatility", "arg": {"String": {"sval": "VOLATILE"}}}},
                    {"DefElem": {"defname": "as", "arg": {"String": {"sval": "select 1"}}}},
                ],
            },
        }
        alter = {
            "AlterFunctionStmt": {
                "actions": [
                    {"DefElem": {"defname": "volatility", "arg": {"String": {"sval": "IMMUTABLE"}}}},
                    {"DefElem": {"defname": "strict", "arg": {"Boolean": {"boolval": True}}}},
                ],
            },
        }
        status, definition, reason = schema_graph._reduce_function_history([
            {"operation": "CREATE", "normalized_ast": create},
            {"operation": "ALTER", "normalized_ast": alter},
        ])
        self.assertEqual(status, "REDUCED_FUNCTION_SCALAR_OPTIONS_PARTIAL")
        self.assertEqual(reason, "FUNCTION_CREATE_ALTER_SCALAR_OPTIONS_REDUCED")
        self.assertEqual(definition["FunctionAttributes"], {"volatility": "IMMUTABLE", "strict": True})
        self.assertEqual(
            definition["CreateFunctionStmt"]["options"][2]["DefElem"]["arg"]["String"]["sval"],
            "select 1",
        )
        self.assertEqual(definition["body_semantics"], "OPAQUE_NOT_EXECUTED_OR_REPARSED")

    def test_function_reducer_fails_closed_for_configuration_options(self):
        create = {"CreateFunctionStmt": {"options": []}}
        alter = {"AlterFunctionStmt": {"actions": [
            {"DefElem": {"defname": "set", "arg": {"VariableSetStmt": {"name": "search_path"}}}},
        ]}}
        status, definition, reason = schema_graph._reduce_function_history([
            {"operation": "CREATE", "normalized_ast": create},
            {"operation": "ALTER", "normalized_ast": alter},
        ])
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "FUNCTION_OPTION_UNSUPPORTED:set")



    def test_domain_identity_uses_domainname_not_base_type(self):
        create = {
            "domainname": [{"String": {"sval": "email_address"}}],
            "typeName": {"TypeName": {"names": [{"String": {"sval": "text"}}]}},
        }
        alter = {"typeName": [{"String": {"sval": "email_address"}}]}
        self.assertEqual(schema_graph._object_names("CreateDomainStmt", create), ["public.email_address"])
        self.assertEqual(schema_graph._object_names("AlterDomainStmt", alter), ["public.email_address"])

    def test_domain_reducer_folds_validation_not_null_and_default(self):
        create = {"CreateDomainStmt": {
            "domainname": [{"String": {"sval": "email_address"}}],
            "typeName": {"TypeName": {"names": [{"String": {"sval": "text"}}]}},
            "constraints": [{"Constraint": {
                "conname": "email_address_check",
                "contype": "CONSTR_CHECK",
                "skip_validation": True,
            }}],
        }}
        def alter(subtype, definition=None):
            return {"AlterDomainStmt": {
                "typeName": [{"String": {"sval": "email_address"}}],
                "subtype": subtype,
                "def": definition,
            }}
        history = [
            {"operation": "CREATE", "normalized_ast": create},
            {"operation": "ALTER", "normalized_ast": alter("T_ValidateConstraint", {"String": {"sval": "email_address_check"}})},
            {"operation": "ALTER", "normalized_ast": alter("T_SetNotNull")},
            {"operation": "ALTER", "normalized_ast": alter("T_SetDefault", {"A_Const": {"val": {"String": {"sval": "unknown@example.test"}}}})},
        ]
        status, definition, reason = schema_graph._reduce_domain_history(history)
        self.assertEqual(status, "REDUCED_DOMAIN_EXPLICIT_STATE_PARTIAL")
        self.assertEqual(reason, "DOMAIN_CREATE_ALTER_EXPLICIT_STATE_REDUCED")
        constraint = definition["CreateDomainStmt"]["constraints"][0]["Constraint"]
        self.assertFalse(constraint["skip_validation"])
        self.assertTrue(definition["CreateDomainStmt"]["domain_not_null"])
        self.assertIsNotNone(definition["CreateDomainStmt"]["domain_default"])

    def test_domain_reducer_adds_and_drops_named_constraints(self):
        create = {"CreateDomainStmt": {
            "domainname": [{"String": {"sval": "positive_int"}}],
            "typeName": {"TypeName": {"names": [{"String": {"sval": "integer"}}]}},
            "constraints": [],
        }}
        alter_add = {"AlterDomainStmt": {
            "typeName": [{"String": {"sval": "positive_int"}}],
            "subtype": "T_AddConstraint",
            "def": {"Constraint": {"conname": "positive_int_check", "contype": "CONSTR_CHECK"}},
        }}
        alter_drop = {"AlterDomainStmt": {
            "typeName": [{"String": {"sval": "positive_int"}}],
            "subtype": "T_DropConstraint",
            "def": {"String": {"sval": "positive_int_check"}},
        }}
        status, definition, _ = schema_graph._reduce_domain_history([
            {"operation": "CREATE", "normalized_ast": create},
            {"operation": "ALTER", "normalized_ast": alter_add},
            {"operation": "ALTER", "normalized_ast": alter_drop},
        ])
        self.assertEqual(status, "REDUCED_DOMAIN_EXPLICIT_STATE_PARTIAL")
        self.assertEqual(definition["CreateDomainStmt"]["constraints"], [])

    def test_domain_reducer_rejects_alter_for_different_domain(self):
        create = {"CreateDomainStmt": {
            "domainname": [{"String": {"sval": "first_domain"}}],
            "typeName": {"TypeName": {"names": [{"String": {"sval": "text"}}]}},
            "constraints": [],
        }}
        alter = {"AlterDomainStmt": {
            "typeName": [{"String": {"sval": "other_domain"}}],
            "subtype": "T_SetNotNull",
        }}
        status, definition, reason = schema_graph._reduce_domain_history([
            {"operation": "CREATE", "normalized_ast": create},
            {"operation": "ALTER", "normalized_ast": alter},
        ])
        self.assertEqual(status, "NOT_VERIFIABLE")
        self.assertIsNone(definition)
        self.assertEqual(reason, "DOMAIN_ALTER_TARGET_MISMATCH")


if __name__ == "__main__":
    unittest.main()
