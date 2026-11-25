from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any
from importlib.metadata import version as package_version

from pglast.parser import parse_sql_json


DDL_TAGS = {
    "CreateStmt": ("TABLE", "CREATE"),
    "AlterTableStmt": ("TABLE", "ALTER"),
    "IndexStmt": ("INDEX", "CREATE"),
    "CreateFunctionStmt": ("FUNCTION", "CREATE"),
    "AlterFunctionStmt": ("FUNCTION", "ALTER"),
    "CreateTrigStmt": ("TRIGGER", "CREATE"),
    "ViewStmt": ("VIEW", "CREATE"),
    "CreateSeqStmt": ("SEQUENCE", "CREATE"),
    "AlterSeqStmt": ("SEQUENCE", "ALTER"),
    "CreateEnumStmt": ("TYPE", "CREATE"),
    "CreateDomainStmt": ("DOMAIN", "CREATE"),
    "CompositeTypeStmt": ("TYPE", "CREATE"),
    "CreateRangeStmt": ("TYPE", "CREATE"),
    "CreateSchemaStmt": ("SCHEMA", "CREATE"),
    "CreatePolicyStmt": ("RLS_POLICY", "CREATE"),
    "AlterPolicyStmt": ("RLS_POLICY", "ALTER"),
    "GrantStmt": ("ACL", "GRANT_OR_REVOKE"),
    "GrantRoleStmt": ("ROLE_MEMBERSHIP", "GRANT_OR_REVOKE"),
    "AlterDefaultPrivilegesStmt": ("DEFAULT_ACL", "ALTER"),
    "AlterOwnerStmt": ("OWNERSHIP", "ALTER"),
    "CreateExtensionStmt": ("EXTENSION", "CREATE"),
    "CreateRoleStmt": ("ROLE", "CREATE"),
    "AlterRoleStmt": ("ROLE", "ALTER"),
    "DropStmt": ("OBJECT", "DROP"),
    "RenameStmt": ("OBJECT", "RENAME"),
    "CommentStmt": ("COMMENT", "COMMENT"),
    "CreateTableAsStmt": ("TABLE_OR_MATERIALIZED_VIEW", "CREATE"),
    "CreateForeignTableStmt": ("FOREIGN_TABLE", "CREATE"),
    "CreateForeignServerStmt": ("FOREIGN_SERVER", "CREATE"),
    "CreateUserMappingStmt": ("USER_MAPPING", "CREATE"),
    "AlterObjectSchemaStmt": ("OBJECT", "ALTER_SCHEMA"),
    "AlterTypeStmt": ("TYPE", "ALTER"),
    "AlterEnumStmt": ("TYPE", "ALTER"),
    "CreatePublicationStmt": ("PUBLICATION", "CREATE"),
    "AlterPublicationStmt": ("PUBLICATION", "ALTER"),
    "CreateSubscriptionStmt": ("SUBSCRIPTION", "CREATE"),
    "AlterSubscriptionStmt": ("SUBSCRIPTION", "ALTER"),
    "CreateCastStmt": ("CAST", "CREATE"),
    "CreateOpClassStmt": ("OPERATOR_CLASS", "CREATE"),
    "CreateOpFamilyStmt": ("OPERATOR_FAMILY", "CREATE"),
    "CreateConversionStmt": ("CONVERSION", "CREATE"),
    "CreateTransformStmt": ("TRANSFORM", "CREATE"),
    "CreateEventTrigStmt": ("TRIGGER", "CREATE"),
    "CreateCollationStmt": ("COLLATION", "CREATE"),
    "CreateStatisticsStmt": ("STATISTICS", "CREATE"),
    "CreateAccessMethodStmt": ("ACCESS_METHOD", "CREATE"),
    "CreateOperatorStmt": ("OPERATOR", "CREATE"),
    "AlterOperatorStmt": ("OPERATOR", "ALTER"),
    "CreateForeignDataWrapperStmt": ("FOREIGN_DATA_WRAPPER", "CREATE"),
    "AlterForeignDataWrapperStmt": ("FOREIGN_DATA_WRAPPER", "ALTER"),
    "AlterForeignServerStmt": ("FOREIGN_SERVER", "ALTER"),
    "AlterUserMappingStmt": ("USER_MAPPING", "ALTER"),
    "AlterExtensionStmt": ("EXTENSION", "ALTER"),
    "AlterDatabaseStmt": ("DATABASE", "ALTER"),
    "AlterSystemStmt": ("SYSTEM_SETTING", "ALTER"),
}

LOCATION_KEYS = {"location", "stmt_location", "stmt_len", "token_location"}


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize(item)
            for key, item in sorted(value.items())
            if key not in LOCATION_KEYS
        }
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _node_tag(value: Any) -> tuple[str | None, Any]:
    if isinstance(value, dict) and len(value) == 1:
        key = next(iter(value))
        if key and key[0].isupper() and isinstance(value[key], (dict, list, str, int, float, bool, type(None))):
            return key, value[key]
    return None, value


def _walk(value: Any):
    if isinstance(value, dict):
        tag, payload = _node_tag(value)
        if tag:
            yield tag, payload
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _strings(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        if "String" in value and isinstance(value["String"], dict):
            sval = value["String"].get("sval")
            if isinstance(sval, str):
                found.append(sval)
        else:
            for item in value.values():
                found.extend(_strings(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_strings(item))
    return found


def _rangevars(value: Any) -> list[str]:
    result: list[str] = []
    for tag, payload in _walk(value):
        if tag == "RangeVar" and isinstance(payload, dict):
            schema = payload.get("schemaname")
            relation = payload.get("relname")
            if isinstance(relation, str):
                result.append(f"{schema}.{relation}" if isinstance(schema, str) and schema else relation)
    return list(dict.fromkeys(result))


def _first_rangevar(value: Any) -> str | None:
    values = _rangevars(value)
    return values[0] if values else None


def _qualified_identifier(names: list[str]) -> str:
    if len(names) == 1:
        return "public." + names[0]
    return ".".join(names)


def _object_names(tag: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if tag in {"IndexStmt", "CreateTrigStmt", "CreatePolicyStmt", "AlterPolicyStmt"}:
        relation = _first_rangevar(payload.get("relation"))
        field = {"IndexStmt": "idxname", "CreateTrigStmt": "trigname", "CreatePolicyStmt": "policy_name", "AlterPolicyStmt": "policy_name"}[tag]
        names = _strings(payload.get(field))
        if relation and names:
            return [f"{relation}.{'.'.join(names)}"]
        return names[:1]
    if tag in {"CreateFunctionStmt", "AlterFunctionStmt"}:
        names = _strings(payload.get("funcname") or payload.get("func"))
        if not names:
            return []
        if tag == "AlterFunctionStmt":
            return [_qualified_identifier(names) + "#signature-not-verifiable"]
        parameters = payload.get("parameters") or []
        argument_types: list[str] = []
        for node_tag, node_payload in _walk(parameters):
            if node_tag == "TypeName" and isinstance(node_payload, dict):
                type_names = _strings(node_payload.get("names"))
                if type_names:
                    argument_types.append(".".join(type_names))
        if not argument_types and parameters:
            return [_qualified_identifier(names) + "#signature-not-verifiable"]
        return [_qualified_identifier(names) + "(" + ", ".join(argument_types) + ")"]
    if tag in {"CreateEnumStmt", "CreateDomainStmt", "CompositeTypeStmt", "CreateRangeStmt", "AlterTypeStmt", "AlterEnumStmt"}:
        values = _strings(payload.get("typeName") or payload.get("typevar"))
        if values:
            return [_qualified_identifier(values)]
    if tag == "DropStmt":
        values = _strings(payload.get("objects"))
        return [".".join(values)] if values else []
    if tag in {"GrantStmt", "GrantRoleStmt", "AlterDefaultPrivilegesStmt"}:
        values = _strings(payload.get("objects"))
        return [".".join(values)] if values else [str(payload.get("objtype") or tag)]
    if tag == "CreateTableAsStmt":
        return _rangevars(payload.get("into") or payload)
    for key in ("relation", "view", "sequence", "typevar", "server", "publication"):
        if key in payload:
            ranges = _rangevars(payload[key])
            if ranges:
                return ranges
    for key in ("funcname", "func", "schemaname", "extname", "rolename", "role", "policy_name", "servername", "fdwname", "pubname", "subname", "amname", "opclassname", "opfamilyname", "conname", "collname", "trigname", "oprname", "defnames"):
        if key in payload:
            values = _strings(payload[key])
            if values:
                if key in {"schemaname", "extname", "rolename", "role", "servername", "fdwname", "pubname", "subname", "amname", "trigname"}:
                    return [".".join(values)]
                return [_qualified_identifier(values)]
    ranges = _rangevars(payload)
    return ranges[:1]
def _classify_statement(stmt: Any) -> tuple[str, Any] | None:
    tag, payload = _node_tag(stmt)
    if tag in DDL_TAGS:
        return tag, payload
    return None


def _dependency_candidates(value: Any, target: str | None) -> list[str]:
    candidates: list[str] = []
    for tag, payload in _walk(value):
        if tag == "RangeVar" and isinstance(payload, dict):
            schema, relation = payload.get("schemaname"), payload.get("relname")
            if isinstance(relation, str):
                candidates.append((str(schema) + "." if schema else "") + relation)
        elif tag == "FuncCall" and isinstance(payload, dict):
            names = _strings(payload.get("funcname"))
            if names:
                candidates.append("function:" + ".".join(names))
        elif tag == "TypeName" and isinstance(payload, dict):
            names = _strings(payload.get("names"))
            if names:
                candidates.append("type:" + ".".join(names))
    return [item for item in dict.fromkeys(candidates) if item != target]

def _procedural_body_status(tag: str, payload: Any) -> str:
    if tag != "CreateFunctionStmt" or not isinstance(payload, dict):
        return "NOT_APPLICABLE"
    options = payload.get("options") or []
    language = None
    body_present = False
    for option in options:
        if not isinstance(option, dict) or "DefElem" not in option:
            continue
        elem = option["DefElem"]
        if elem.get("defname") == "language":
            language = " ".join(_strings(elem.get("arg")))
        if elem.get("defname") in {"as", "sql_body"}:
            body_present = True
    if not body_present:
        return "BODY_NOT_FOUND_NOT_VERIFIABLE"
    if language and language.lower() == "sql":
        return "SQL_BODY_PRESENT_REQUIRES_SEPARATE_BODY_PARSE"
    return "PROCEDURAL_BODY_OPAQUE_NOT_VERIFIABLE"


def _git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def _migration_identity(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    match = re.match(r"^(\d{14})_", path.name)
    return match.group(1) if match else f"UNVERSIONED:{relative}"


def _table_subobject_events(tag: str, payload: Any, *, migration_id: str, relative: str, source_sha256: str, git_blob_sha1: str, statement_ordinal: int, parent_name: str | None, operation: str) -> list[dict[str, Any]]:
    """Emit identity-stable column/constraint events, including ALTER effects.

    PostgreSQL's AlterTableCmd subtype is the semantic authority for add/drop/
    alter operations. Unsupported subtypes are deliberately not guessed.
    """
    if tag not in {"CreateStmt", "AlterTableStmt"} or not isinstance(payload, dict) or not parent_name:
        return []
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def emit(object_class: str, object_name: str, event_operation: str, node_tag: str, node_payload: Any, status: str = "AST_PARSED") -> None:
        identity = (object_class, object_name, event_operation)
        if identity in seen:
            return
        seen.add(identity)
        normalized = _normalize({node_tag: node_payload})
        encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        output.append({
            "migration_id": migration_id, "source_kind": "ACTIVE_GIT_MIGRATION_FILE", "source_path": relative,
            "source_sha256": source_sha256, "git_blob_sha1": git_blob_sha1,
            "statement_ordinal": statement_ordinal, "ast_node_tag": node_tag,
            "object_class": object_class, "operation": event_operation,
            "object_name": object_name, "object_names": [object_name],
            "expected_effect": event_operation,
            "normalized_ast_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
            "normalized_ast": normalized, "dependency_candidates": [],
            "dependency_status": "NOT_APPLICABLE",
            "procedural_body_status": "NOT_APPLICABLE", "semantic_status": status,
        })

    if tag == "CreateStmt":
        for child_tag, child_payload in _walk(payload.get("tableElts")):
            if not isinstance(child_payload, dict):
                continue
            if child_tag == "ColumnDef":
                name = child_payload.get("colname")
                if isinstance(name, str) and name:
                    emit("COLUMN", parent_name + "." + name, "CREATE", child_tag, child_payload)
            elif child_tag == "Constraint":
                name = child_payload.get("conname")
                if not isinstance(name, str) or not name:
                    name = "unnamed:" + hashlib.sha256(json.dumps(_normalize(child_payload), sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:12]
                emit("CONSTRAINT", parent_name + "." + name, "CREATE", child_tag, child_payload)
        return output

    commands = payload.get("cmds") or []
    for command in commands:
        if not isinstance(command, dict) or not isinstance(command.get("AlterTableCmd"), dict):
            continue
        cmd = command["AlterTableCmd"]
        subtype = str(cmd.get("subtype") or "")
        definition = cmd.get("def")
        def_tag, def_payload = _node_tag(definition)
        name = cmd.get("name")
        if def_tag == "ColumnDef" and isinstance(def_payload, dict):
            name = def_payload.get("colname") or name
            event_operation = "CREATE" if subtype in {"AT_AddColumn", "AT_AddColumnRecurse"} else "ALTER"
            if subtype in {"AT_DropColumn", "AT_DropColumnRecurse"}:
                event_operation = "DROP"
            if isinstance(name, str) and name:
                emit("COLUMN", parent_name + "." + name, event_operation, def_tag, def_payload)
            continue
        if def_tag == "Constraint" and isinstance(def_payload, dict):
            name = def_payload.get("conname") or name
            event_operation = "CREATE" if subtype in {"AT_AddConstraint", "AT_AddConstraintRecurse"} else "ALTER"
            if isinstance(name, str) and name:
                emit("CONSTRAINT", parent_name + "." + name, event_operation, def_tag, def_payload)
            continue
        if subtype in {"AT_DropColumn", "AT_DropColumnRecurse"} and isinstance(name, str) and name:
            emit("COLUMN", parent_name + "." + name, "DROP", "AlterTableCmd", cmd)
        elif subtype in {"AT_DropConstraint"} and isinstance(name, str) and name:
            emit("CONSTRAINT", parent_name + "." + name, "DROP", "AlterTableCmd", cmd)
        elif subtype in {"AT_AlterColumnType", "AT_ColumnDefault", "AT_CookedColumnDefault", "AT_ColumnOnUpdate", "AT_ColumnNotNull", "AT_DropNotNull", "AT_SetNotNull", "AT_DropColumnDefault", "AT_SetStatistics", "AT_SetStorage", "AT_SetCompression", "AT_SetOptions", "AT_ResetOptions"} and isinstance(name, str) and name:
            emit("COLUMN", parent_name + "." + name, "ALTER", "AlterTableCmd", cmd)
        elif subtype in {"AT_RenameColumn", "AT_RenameConstraint"} and isinstance(name, str) and name:
            # Rename changes identity; preserve it as an explicit unbound event.
            object_class = "COLUMN" if subtype == "AT_RenameColumn" else "CONSTRAINT"
            emit(object_class, parent_name + "." + name, "RENAME", "AlterTableCmd", cmd, "RENAME_IDENTITY_REQUIRES_OLD_AND_NEW_NAME_BINDING")
    return output

def parse_source(path: Path, root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = path.read_bytes()
    source = raw.decode("utf-8")
    source_sha256 = hashlib.sha256(raw).hexdigest()
    git_blob_sha1 = _git_blob_sha1(raw)
    migration_id = _migration_identity(path, root)
    relative = path.relative_to(root).as_posix()
    try:
        parsed = json.loads(parse_sql_json(source))
    except Exception as exc:
        return [], {
            "migration_id": migration_id,
            "source_kind": "ACTIVE_GIT_MIGRATION_FILE",
            "source_path": relative,
            "source_sha256": source_sha256,
            "git_blob_sha1": git_blob_sha1,
            "byte_size": len(raw),
            "parse_status": "NOT_VERIFIABLE",
            "parse_error_type": type(exc).__name__,
            "parse_error": str(exc)[:500],
            "statement_count": 0,
            "ddl_event_count": 0,
        }

    statements = parsed.get("stmts", []) if isinstance(parsed, dict) else []
    events: list[dict[str, Any]] = []
    for ordinal, raw_stmt in enumerate(statements, start=1):
        stmt = raw_stmt.get("stmt") if isinstance(raw_stmt, dict) else None
        classified = _classify_statement(stmt)
        if not classified:
            continue
        tag, payload = classified
        object_class, operation = DDL_TAGS[tag]
        if tag == "CreateFunctionStmt" and isinstance(payload, dict) and payload.get("is_procedure"):
            object_class = "PROCEDURE"
        elif tag == "AlterFunctionStmt" and isinstance(payload, dict) and payload.get("objtype") in {"OBJECT_PROCEDURE", "PROCEDURE"}:
            object_class = "PROCEDURE"
        normalized = _normalize(stmt)
        ast_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        ast_sha256 = hashlib.sha256(ast_json.encode("utf-8")).hexdigest()
        names = _object_names(tag, payload)
        target = names[0] if names else None
        dependencies = _dependency_candidates(payload, target)
        event_status = "AST_PARSED"
        if not names:
            event_status = "NOT_VERIFIABLE"
        events.append({
            "migration_id": migration_id,
            "source_kind": "ACTIVE_GIT_MIGRATION_FILE",
            "source_path": relative,
            "source_sha256": source_sha256,
            "git_blob_sha1": git_blob_sha1,
            "statement_ordinal": ordinal,
            "ast_node_tag": tag,
            "object_class": object_class,
            "operation": operation,
            "object_name": target,
            "object_names": names,
            "expected_effect": operation,
            "normalized_ast_sha256": ast_sha256,
            "normalized_ast": normalized,
            "dependency_candidates": dependencies,
            "dependency_status": "AST_REFERENCE_CANDIDATES_NOT_FULL_SEMANTIC_BINDING",
            "procedural_body_status": _procedural_body_status(tag, payload),
            "semantic_status": event_status,
        })
        events.extend(_table_subobject_events(
            tag, payload, migration_id=migration_id, relative=relative,
            source_sha256=source_sha256, git_blob_sha1=git_blob_sha1,
            statement_ordinal=ordinal, parent_name=target, operation=operation,
        ))

    source_record = {
        "migration_id": migration_id,
        "source_path": relative,
        "source_sha256": source_sha256,
        "git_blob_sha1": git_blob_sha1,
        "byte_size": len(raw),
        "parse_status": "PARSED",
        "statement_count": len(statements),
        "ddl_event_count": len(events),
    }
    return events, source_record


def _history_payloads(history_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(history_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        migrations = payload.get("migrations") if isinstance(payload, dict) else None
        if isinstance(migrations, list):
            records.extend(item for item in migrations if isinstance(item, dict))
    return records


def _git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}" + chr(0)
    return hashlib.sha1(header.encode("ascii") + raw).hexdigest()


def _history_archive_payloads(history_archive_dir: Path | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if history_archive_dir is None or not history_archive_dir.is_dir():
        return records
    for path in sorted(history_archive_dir.glob("*.json"), key=lambda p: p.name):
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        source = payload.get("source") if isinstance(payload, dict) else None
        if not isinstance(source, dict) and isinstance(payload, dict) and isinstance(payload.get("version"), str):
            source = {"version": payload.get("version"), "name": payload.get("name")}
        if not isinstance(source, dict) or not isinstance(source.get("version"), str):
            continue
        statements = payload.get("statements")
        if not isinstance(statements, list):
            statements = [statements] if isinstance(statements, str) else []
        records.append({
            "version": source["version"], "name": source.get("name") or path.stem,
            "statements": statements, "_source_kind": "HISTORICAL_SQL_ARCHIVE_JSON",
            "_source_path": path.relative_to(history_archive_dir).as_posix(),
            "_git_blob_sha1": _git_blob_sha1(raw),
            "_archive_status": payload.get("archive_status") or (payload.get("archive_metadata") or {}).get("archive_status"),
            "_archive_provenance": payload.get("provenance") or payload.get("archive_metadata"),
            "_source_repository_path": ((payload.get("provenance") or payload.get("archive_metadata") or {}).get("source_repository_path")),
            "_source_repository_git_blob_sha": ((payload.get("provenance") or payload.get("archive_metadata") or {}).get("source_repository_git_blob_sha")),
        })
    return records


def parse_history_record(record: dict[str, Any], temp_root: Path, hash_manifest: dict[str, list[str]] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    version = str(record.get("version") or "UNKNOWN")
    name = str(record.get("name") or "unnamed")
    record_source_kind = str(record.get("_source_kind") or "SUPABASE_HISTORY_STATEMENT")
    record_source_path = record.get("_source_path")
    record_git_blob_sha1 = record.get("_git_blob_sha1")
    statements = record.get("statements")
    if not isinstance(statements, list):
        statements = [statements] if isinstance(statements, str) else []
    events: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    ordinal_offset = 0
    for statement_index, statement in enumerate(statements, start=1):
        if not isinstance(statement, str) or not statement.strip():
            continue
        source_bytes = statement.encode("utf-8")
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        expected_hashes = (hash_manifest or {}).get(version, [])
        expected_hash = expected_hashes[statement_index - 1] if statement_index - 1 < len(expected_hashes) else None
        if record_source_kind == "HISTORICAL_SQL_ARCHIVE_JSON":
            hash_status = "MATCH" if expected_hash == source_sha256 else ("ARCHIVE_TEXT_VARIANT" if expected_hash else "NOT_VERIFIABLE")
        else:
            hash_status = "MATCH" if expected_hash == source_sha256 else ("MISMATCH" if expected_hash else "NOT_VERIFIABLE")
        relative = (str(record_source_path) if record_source_path else "supabase_migrations.schema_migrations/" + version + "/" + name) + "#statement:" + str(statement_index)
        if re.match(r"^supabase/migrations/[A-Za-z0-9_./-]+\.sql$", statement.strip()):
            sources.append({
                "migration_id": version, "source_path": relative,
                "source_sha256": source_sha256, "git_blob_sha1": None,
                "byte_size": len(source_bytes), "parse_status": "NOT_VERIFIABLE",
                "source_kind": "HISTORY_PATH_REFERENCE", "history_reference": statement.strip(),
                "git_blob_sha1": record_git_blob_sha1,
                "history_statement_hash_status": hash_status, "history_statement_expected_sha256": expected_hash,
                "statement_count": 0, "ddl_event_count": 0,
            })
            continue
        safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", name)[:80]
        temp_path = temp_root / (version + "_" + safe_name + "_" + str(statement_index) + ".sql")
        temp_path.write_bytes(source_bytes)
        parsed_events, source_record = parse_source(temp_path, temp_root)
        parsed_count = source_record.get("statement_count", 0)
        for event in parsed_events:
            event["source_path"] = relative
            event["source_kind"] = record_source_kind
            event["git_blob_sha1"] = record_git_blob_sha1
            event["history_statement_index"] = statement_index
            event["history_statement_hash_status"] = hash_status
            event["history_statement_expected_sha256"] = expected_hash
            if hash_status == "MISMATCH":
                event["semantic_status"] = "NOT_VERIFIABLE"
            event["statement_ordinal"] = int(event.get("statement_ordinal", 0)) + ordinal_offset
            events.append(event)
        source_record["source_path"] = relative
        source_record["source_kind"] = record_source_kind
        source_record["git_blob_sha1"] = record_git_blob_sha1
        source_record["history_statement_index"] = statement_index
        source_record["history_statement_hash_status"] = hash_status
        source_record["history_statement_expected_sha256"] = expected_hash
        if record_source_kind == "HISTORICAL_SQL_ARCHIVE_JSON":
            source_record["archive_status"] = record.get("_archive_status")
            source_record["archive_provenance"] = record.get("_archive_provenance")
            source_record["source_repository_path"] = record.get("_source_repository_path")
            source_record["source_repository_git_blob_sha"] = record.get("_source_repository_git_blob_sha")
        sources.append(source_record)
        ordinal_offset += int(parsed_count or 0)
    return events, sources



def _reduce_table_subobject_history(history: list[dict[str, Any]]) -> tuple[str, Any | None, str]:
    """Fold only table-subobject changes whose final AST can be reconstructed safely."""
    object_class = history[-1].get("object_class") if history else None
    if object_class not in {"COLUMN", "CONSTRAINT"}:
        return "NOT_APPLICABLE", None, "NOT_APPLICABLE"
    current: dict[str, Any] | None = None
    saw_create = False
    for event in history:
        operation = event.get("operation")
        ast = event.get("normalized_ast") or {}
        node_tag, payload = _node_tag(ast)
        if operation == "DROP":
            current = None
            saw_create = False
            continue
        if operation == "CREATE":
            if object_class == "COLUMN" and node_tag == "ColumnDef" and isinstance(payload, dict):
                current = json.loads(json.dumps(payload))
                saw_create = True
                continue
            if object_class == "CONSTRAINT" and node_tag == "Constraint" and isinstance(payload, dict):
                current = json.loads(json.dumps(payload))
                saw_create = True
                continue
            return "NOT_VERIFIABLE", None, "CREATE_EVENT_SHAPE_UNSUPPORTED"
        if operation == "RENAME":
            return "NOT_VERIFIABLE", None, "RENAME_REQUIRES_IDENTITY_REBINDING"
        if operation == "ALTER" and object_class == "COLUMN":
            if not saw_create or current is None or node_tag != "AlterTableCmd" or not isinstance(payload, dict):
                return "NOT_VERIFIABLE", None, "ALTER_WITHOUT_REDUCIBLE_COLUMN_BASE"
            subtype = str(payload.get("subtype") or "")
            definition = payload.get("def")
            if subtype == "AT_AlterColumnType" and definition is not None:
                current["typeName"] = definition
            elif subtype == "AT_SetNotNull":
                current["is_not_null"] = True
            elif subtype == "AT_DropNotNull":
                current["is_not_null"] = False
            elif subtype == "AT_ColumnDefault" and definition is not None:
                current["raw_default"] = definition
            elif subtype == "AT_DropColumnDefault":
                current["raw_default"] = None
            else:
                return "NOT_VERIFIABLE", None, "ALTER_SUBTYPE_NOT_SUPPORTED_BY_COLUMN_REDUCER:" + subtype
            continue
        if operation == "ALTER" and object_class == "CONSTRAINT":
            return "NOT_VERIFIABLE", None, "CONSTRAINT_ALTER_REQUIRES_VALIDATION_STATE_REDUCER"
        return "NOT_VERIFIABLE", None, "EVENT_OPERATION_NOT_SUPPORTED"
    if current is None:
        return "DROPPED_IN_SOURCE_LINEAGE", None, "TABLE_SUBOBJECT_DROP_REDUCED"
    if not saw_create:
        return "NOT_VERIFIABLE", None, "TABLE_SUBOBJECT_CREATE_NOT_FOUND"
    return "REDUCED_TABLE_SUBOBJECT_DEFINITION", {("ColumnDef" if object_class == "COLUMN" else "Constraint"): current}, "TABLE_SUBOBJECT_EVENT_CHAIN_REDUCED"



def build_graph(root: Path, history_dir: Path | None = None, archive_dir: Path | None = None, history_hash_manifest_path: Path | None = None, history_archive_dir: Path | None = None) -> dict[str, Any]:
    files = sorted(root.rglob("*.sql"), key=lambda p: p.relative_to(root).as_posix())
    events: list[dict[str, Any]] = []
    archive_events: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for path in files:
        file_events, source_record = parse_source(path, root)
        source_record["source_kind"] = "ACTIVE_GIT_MIGRATION_FILE"
        events.extend(file_events)
        sources.append(source_record)
    archive_files = sorted(archive_dir.rglob("*.sql"), key=lambda p: p.relative_to(archive_dir).as_posix()) if archive_dir and archive_dir.is_dir() else []
    for path in archive_files:
        archive_file_events, archive_record = parse_source(path, archive_dir)
        archive_record["source_kind"] = "HISTORICAL_GIT_SOURCE_ARCHIVE"
        archive_record["source_path"] = path.relative_to(archive_dir).as_posix()
        for event in archive_file_events:
            event["source_kind"] = "HISTORICAL_GIT_SOURCE_ARCHIVE"
            event["source_path"] = path.relative_to(archive_dir).as_posix()
            event["historical_archive_only"] = True
        archive_events.extend(archive_file_events)
        sources.append(archive_record)
    history_snapshot_records = _history_payloads(history_dir) if history_dir and history_dir.is_dir() else []
    history_ids = {str(record.get("version")) for record in history_snapshot_records}
    events.extend(event for event in archive_events if str(event.get("migration_id")) in history_ids)
    history_archive_records = _history_archive_payloads(history_archive_dir)
    history_records = history_snapshot_records + history_archive_records
    hash_manifest: dict[str, list[str]] = {}
    if history_hash_manifest_path and history_hash_manifest_path.is_file():
        hash_payload = json.loads(history_hash_manifest_path.read_text(encoding="utf-8"))
        hash_manifest = {str(item.get("version")): list(item.get("statement_sha256") or []) for item in hash_payload.get("migrations", []) if isinstance(item, dict)}
    if history_records:
        with tempfile.TemporaryDirectory(prefix="moreai-migration-history-") as temp_dir:
            temp_root = Path(temp_dir)
            for record in history_records:
                history_events, history_sources = parse_history_record(record, temp_root, hash_manifest)
                events.extend(history_events)
                sources.extend(history_sources)

    merged_events: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    for event in events:
        identity = (event["migration_id"], event["statement_ordinal"], event["object_class"], str(event.get("object_name") or ""))
        existing = merged_events.get(identity)
        evidence = {
            "source_kind": event.get("source_kind"), "source_path": event.get("source_path"),
            "source_sha256": event.get("source_sha256"), "git_blob_sha1": event.get("git_blob_sha1"),
            "ast_sha256": event.get("normalized_ast_sha256"),
        }
        if existing is None:
            event["source_evidence"] = [evidence]
            merged_events[identity] = event
        else:
            existing.setdefault("source_evidence", []).append(evidence)
            if existing.get("normalized_ast_sha256") != event.get("normalized_ast_sha256"):
                existing["semantic_status"] = "NOT_VERIFIABLE"
                existing["source_conflict"] = True
                existing.setdefault("conflicting_ast_sha256", []).append(event.get("normalized_ast_sha256"))
    events = list(merged_events.values())

    object_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        name = event.get("object_name")
        if not isinstance(name, str) or not name:
            key = "NOT_VERIFIABLE:" + event["migration_id"] + ":" + str(event["statement_ordinal"])
        else:
            key = event["object_class"] + ":" + name
        object_events[key].append(event)

    objects = []
    for key, history in sorted(object_events.items()):
        history.sort(key=lambda item: (item["migration_id"], item["statement_ordinal"]))
        latest = history[-1]
        last_operation = latest["operation"]
        state = "NOT_VERIFIABLE"
        expected_definition = None
        reduction_status = "NOT_APPLICABLE"
        if latest.get("source_conflict"):
            state = "SOURCE_CONFLICT_NOT_VERIFIABLE"
        elif latest.get("procedural_body_status") not in {None, "NOT_APPLICABLE"}:
            state = "FUNCTION_BODY_NOT_VERIFIABLE"
        elif latest["semantic_status"] == "AST_PARSED" and last_operation == "CREATE":
            state = "CREATE_DEFINITION_AST_AVAILABLE"
            expected_definition = latest.get("normalized_ast")
        elif last_operation == "DROP":
            state = "DROPPED_IN_SOURCE_LINEAGE"
        elif latest["object_class"] in {"COLUMN", "CONSTRAINT"}:
            state, expected_definition, reduction_status = _reduce_table_subobject_history(history)
        elif last_operation in {"ALTER", "GRANT_OR_REVOKE", "RENAME", "ALTER_SCHEMA"}:
            state = "EVOLVED_STATE_REQUIRES_SEMANTIC_REDUCER"
        objects.append({
            "object_key": key, "object_class": latest["object_class"],
            "object_name": latest.get("object_name"), "event_count": len(history),
            "first_migration_id": history[0]["migration_id"],
            "last_migration_id": latest["migration_id"],
            "latest_operation": last_operation, "expected_state_status": state,
            "latest_ast_sha256": latest["normalized_ast_sha256"],
            "expected_definition": expected_definition,
            "semantic_reduction_status": reduction_status,
            "dependency_candidates": sorted({candidate for item in history for candidate in (item.get("dependency_candidates") or [])}),
            "dependency_candidate_count": len({candidate for item in history for candidate in (item.get("dependency_candidates") or [])}),
            "migration_lineage": [
                {
                    "migration_id": item["migration_id"], "source_path": item["source_path"],
                    "source_sha256": item["source_sha256"], "git_blob_sha1": item.get("git_blob_sha1"),
                    "statement_ordinal": item["statement_ordinal"], "operation": item["operation"],
                    "ast_sha256": item["normalized_ast_sha256"],
                    "source_evidence": item.get("source_evidence", []),
                } for item in history
            ],
        })

    parse_failures = [source for source in sources if source["parse_status"] != "PARSED"]
    active_sources = [source for source in sources if source.get("source_kind") == "ACTIVE_GIT_MIGRATION_FILE"]
    archive_sources = [source for source in sources if source.get("source_kind") == "HISTORICAL_GIT_SOURCE_ARCHIVE"]
    history_sources = [source for source in sources if source.get("source_kind") in {"SUPABASE_HISTORY_STATEMENT", "HISTORY_PATH_REFERENCE", "HISTORICAL_SQL_ARCHIVE_JSON"}]
    for source in sources:
        if source.get("source_kind") == "ACTIVE_GIT_MIGRATION_FILE":
            source["history_record_status"] = "HISTORY_RECORDED" if str(source.get("migration_id")) in history_ids else "HISTORY_ABSENT"
            source["execution_evidence_status"] = "HISTORY_RECORD_ONLY_NOT_EXECUTION_RECEIPT" if str(source.get("migration_id")) in history_ids else "SOURCE_ONLY_NOT_APPLIED"
        elif source.get("source_kind") in {"SUPABASE_HISTORY_STATEMENT", "HISTORY_PATH_REFERENCE"}:
            source["history_record_status"] = "HISTORY_RECORDED"
            source["execution_evidence_status"] = "HISTORY_RECORD_ONLY_NOT_EXECUTION_RECEIPT"
        elif source.get("source_kind") == "HISTORICAL_SQL_ARCHIVE_JSON":
            confirmed = str(source.get("migration_id")) in history_ids
            source["history_record_status"] = "HISTORY_RECORD_CONFIRMED" if confirmed else "ARCHIVE_ASSERTION_ONLY"
            source["execution_evidence_status"] = "HISTORY_RECORD_ONLY_NOT_EXECUTION_RECEIPT" if confirmed else "SOURCE_ARCHIVE_ONLY"
        elif source.get("source_kind") == "HISTORICAL_GIT_SOURCE_ARCHIVE":
            confirmed = str(source.get("migration_id")) in history_ids
            source["history_record_status"] = "HISTORY_RECORD_CONFIRMED" if confirmed else "HISTORICAL_SOURCE_NO_CURRENT_HISTORY_ROW_ASSERTION"
            source["execution_evidence_status"] = "HISTORY_RECORD_ONLY_NOT_EXECUTION_RECEIPT" if confirmed else "SOURCE_EXISTENCE_ONLY"
        else:
            source["history_record_status"] = "HISTORICAL_SOURCE_NO_CURRENT_HISTORY_ROW_ASSERTION"
            source["execution_evidence_status"] = "SOURCE_EXISTENCE_ONLY"
    return {
        "format": "moreai.postgresql.expected-object-graph.v1",
        "parser": {"name": "pglast", "version": package_version("pglast"), "postgresql_grammar": "pglast-bundled-server-parser", "authority": "PostgreSQL parser AST"},
        "execution_provenance_status": "EXECUTION_PROVENANCE_UNVERIFIABLE",
        "execution_provenance_reason": "Migration history rows and observed catalog are not independent exact-byte deployment receipts.",
        "source_root": str(root), "archive_source_file_count": len(archive_sources),
        "history_migration_record_count": len(history_snapshot_records),
        "history_archive_record_count": len(history_archive_records),
        "history_hash_manifest_migration_count": len(hash_manifest),
        "history_statement_hash_mismatch_count": sum(1 for source in history_sources if source.get("source_kind") in {"SUPABASE_HISTORY_STATEMENT", "HISTORY_PATH_REFERENCE"} and source.get("history_statement_hash_status") == "MISMATCH"),
        "history_statement_hash_not_verifiable_count": sum(1 for source in history_sources if source.get("source_kind") in {"SUPABASE_HISTORY_STATEMENT", "HISTORY_PATH_REFERENCE"} and source.get("history_statement_hash_status") == "NOT_VERIFIABLE"),
        "history_archive_statement_hash_variant_count": sum(1 for source in history_sources if source.get("source_kind") == "HISTORICAL_SQL_ARCHIVE_JSON" and source.get("history_statement_hash_status") == "ARCHIVE_TEXT_VARIANT"),
        "history_archive_statement_hash_not_verifiable_count": sum(1 for source in history_sources if source.get("source_kind") == "HISTORICAL_SQL_ARCHIVE_JSON" and source.get("history_statement_hash_status") == "NOT_VERIFIABLE"),
        "history_statement_source_count": len(history_sources),
        "active_migration_file_count": len(active_sources),
        "source_record_count": len(sources), "parsed_source_record_count": len(sources) - len(parse_failures),
        "parse_failure_count": len(parse_failures),
        "statement_count": sum(source["statement_count"] for source in sources),
        "ddl_event_count": len(events), "object_key_count": len(objects),
        "archive_ddl_event_count": len(archive_events),
        "sources": sources, "events": events, "historical_archive_events": archive_events, "objects": objects,
        "parse_failures": parse_failures,
        "limitations": [
            "AST parsing proves grammar recognition, not migration execution.",
            "ALTER event folding into complete final definitions is not inferred; affected objects remain NOT_VERIFIABLE until a supported reducer exists.",
            "Function bodies and dynamic SQL are not treated as outer SQL AST; procedural bodies are explicitly marked opaque.",
            "Dependency candidates are AST RangeVar references, not a complete PostgreSQL dependency resolver.",
            "ACL, ownership, extension, policy and role effects require catalog-specific semantic folding before global MATCH can be assigned.",
            "History path-reference statements have no SQL body and remain NOT_VERIFIABLE.",
        ],
    }

def main() -> int:
    cli = argparse.ArgumentParser(description="Build a PostgreSQL AST-backed static expected-object event graph.")
    cli.add_argument("--migrations-dir", required=True, type=Path)
    cli.add_argument("--history-dir", type=Path, default=None)
    cli.add_argument("--archive-dir", type=Path, default=None)
    cli.add_argument("--history-hash-manifest", type=Path, default=None)
    cli.add_argument("--history-archive-dir", type=Path, default=None)
    cli.add_argument("--output", required=True, type=Path)
    args = cli.parse_args()
    if not args.migrations_dir.is_dir():
        raise SystemExit("migration_directory_not_found")
    graph = build_graph(args.migrations_dir.resolve(), args.history_dir.resolve() if args.history_dir else None, args.archive_dir.resolve() if args.archive_dir else None, args.history_hash_manifest.resolve() if args.history_hash_manifest else None, args.history_archive_dir.resolve() if args.history_archive_dir else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "active_migration_file_count": graph["active_migration_file_count"],
        "history_migration_record_count": graph["history_migration_record_count"],
        "history_archive_record_count": graph["history_archive_record_count"],
        "history_hash_manifest_migration_count": graph["history_hash_manifest_migration_count"],
        "history_statement_hash_mismatch_count": graph["history_statement_hash_mismatch_count"],
        "history_statement_hash_not_verifiable_count": graph["history_statement_hash_not_verifiable_count"],
        "history_archive_statement_hash_variant_count": graph["history_archive_statement_hash_variant_count"],
        "history_archive_statement_hash_not_verifiable_count": graph["history_archive_statement_hash_not_verifiable_count"],
        "history_statement_source_count": graph["history_statement_source_count"],
        "archive_source_file_count": graph["archive_source_file_count"],
        "archive_ddl_event_count": graph["archive_ddl_event_count"],
        "source_record_count": graph["source_record_count"],
        "parsed_source_record_count": graph["parsed_source_record_count"],
        "parse_failure_count": graph["parse_failure_count"],
        "statement_count": graph["statement_count"],
        "ddl_event_count": graph["ddl_event_count"],
        "object_key_count": graph["object_key_count"],
        "output": str(args.output),
    }, separators=(",", ":")))
    return 0  # NOT_VERIFIABLE parse cases are emitted in the graph, not treated as execution failures.


if __name__ == "__main__":
    sys.exit(main())
