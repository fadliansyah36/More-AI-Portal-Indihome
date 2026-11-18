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


def _object_names(tag: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if tag in {"IndexStmt", "CreateTrigStmt", "CreatePolicyStmt"}:
        relation = _first_rangevar(payload.get("relation"))
        field = {"IndexStmt": "idxname", "CreateTrigStmt": "trigname", "CreatePolicyStmt": "policy_name"}[tag]
        names = _strings(payload.get(field))
        if relation and names:
            return [f"{relation}.{'.'.join(names)}"]
        return names[:1]
    if tag == "CreateFunctionStmt":
        names = _strings(payload.get("funcname"))
        if not names:
            return []
        parameters = payload.get("parameters") or []
        argument_types: list[str] = []
        for node_tag, node_payload in _walk(parameters):
            if node_tag == "TypeName" and isinstance(node_payload, dict):
                type_names = _strings(node_payload.get("names"))
                if type_names:
                    argument_types.append(".".join(type_names))
        if not argument_types and parameters:
            return [".".join(names) + "#signature-not-verifiable"]
        return [".".join(names) + "(" + ",".join(argument_types) + ")"]
    if tag in {"CreateEnumStmt", "CreateDomainStmt", "CompositeTypeStmt", "CreateRangeStmt", "AlterTypeStmt", "AlterEnumStmt"}:
        values = _strings(payload.get("typeName") or payload.get("typevar"))
        if values:
            return [".".join(values)]
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
    for key in ("funcname", "schemaname", "extname", "rolename"):
        if key in payload:
            values = _strings(payload[key])
            if values:
                return [".".join(values)]
    ranges = _rangevars(payload)
    return ranges[:1]
def _classify_statement(stmt: Any) -> tuple[str, Any] | None:
    tag, payload = _node_tag(stmt)
    if tag in DDL_TAGS:
        return tag, payload
    return None


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
    if tag not in {"CreateStmt", "AlterTableStmt"} or not isinstance(payload, dict) or not parent_name:
        return []
    roots = payload.get("tableElts") if tag == "CreateStmt" else payload.get("cmds")
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for child_tag, child_payload in _walk(roots):
        if not isinstance(child_payload, dict):
            continue
        if child_tag == "ColumnDef":
            name = child_payload.get("colname")
            if not isinstance(name, str) or not name:
                continue
            object_class, object_name = "COLUMN", parent_name + "." + name
        elif child_tag == "Constraint":
            name = child_payload.get("conname")
            if not isinstance(name, str) or not name:
                name = "unnamed:" + hashlib.sha256(json.dumps(_normalize(child_payload), sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:12]
            object_class, object_name = "CONSTRAINT", parent_name + "." + name
        else:
            continue
        identity = (object_class, object_name)
        if identity in seen:
            continue
        seen.add(identity)
        normalized = _normalize({child_tag: child_payload})
        encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        output.append({
            "migration_id": migration_id, "source_kind": "ACTIVE_GIT_MIGRATION_FILE", "source_path": relative,
            "source_sha256": source_sha256, "git_blob_sha1": git_blob_sha1,
            "statement_ordinal": statement_ordinal, "ast_node_tag": child_tag,
            "object_class": object_class, "operation": operation,
            "object_name": object_name, "object_names": [object_name],
            "expected_effect": operation,
            "normalized_ast_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
            "normalized_ast": normalized, "dependency_candidates": [],
            "dependency_status": "NOT_APPLICABLE",
            "procedural_body_status": "NOT_APPLICABLE", "semantic_status": "AST_PARSED",
        })
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
        normalized = _normalize(stmt)
        ast_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        ast_sha256 = hashlib.sha256(ast_json.encode("utf-8")).hexdigest()
        names = _object_names(tag, payload)
        target = names[0] if names else None
        all_refs = _rangevars(payload)
        dependencies = [name for name in all_refs if name != target]
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


def parse_history_record(record: dict[str, Any], temp_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    version = str(record.get("version") or "UNKNOWN")
    name = str(record.get("name") or "unnamed")
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
        relative = "supabase_migrations.schema_migrations/" + version + "/" + name + "#statement:" + str(statement_index)
        if re.match(r"^supabase/migrations/[A-Za-z0-9_./-]+\\.sql$", statement.strip()):
            sources.append({
                "migration_id": version, "source_path": relative,
                "source_sha256": source_sha256, "git_blob_sha1": None,
                "byte_size": len(source_bytes), "parse_status": "NOT_VERIFIABLE",
                "source_kind": "HISTORY_PATH_REFERENCE", "history_reference": statement.strip(),
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
            event["source_kind"] = "SUPABASE_HISTORY_STATEMENT"
            event["git_blob_sha1"] = None
            event["history_statement_index"] = statement_index
            event["statement_ordinal"] = int(event.get("statement_ordinal", 0)) + ordinal_offset
            events.append(event)
        source_record["source_path"] = relative
        source_record["source_kind"] = "SUPABASE_HISTORY_STATEMENT"
        source_record["git_blob_sha1"] = None
        source_record["history_statement_index"] = statement_index
        sources.append(source_record)
        ordinal_offset += int(parsed_count or 0)
    return events, sources


def build_graph(root: Path, history_dir: Path | None = None) -> dict[str, Any]:
    files = sorted(root.rglob("*.sql"), key=lambda p: p.relative_to(root).as_posix())
    events: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for path in files:
        file_events, source_record = parse_source(path, root)
        source_record["source_kind"] = "ACTIVE_GIT_MIGRATION_FILE"
        events.extend(file_events)
        sources.append(source_record)
    history_records = _history_payloads(history_dir) if history_dir and history_dir.is_dir() else []
    if history_records:
        with tempfile.TemporaryDirectory(prefix="moreai-migration-history-") as temp_dir:
            temp_root = Path(temp_dir)
            for record in history_records:
                history_events, history_sources = parse_history_record(record, temp_root)
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
        if latest.get("source_conflict"):
            state = "SOURCE_CONFLICT_NOT_VERIFIABLE"
        elif latest["semantic_status"] == "AST_PARSED" and last_operation == "CREATE":
            state = "CREATE_DEFINITION_AST_AVAILABLE"
        elif last_operation == "DROP":
            state = "DROPPED_IN_SOURCE_LINEAGE"
        elif last_operation in {"ALTER", "GRANT_OR_REVOKE", "RENAME", "ALTER_SCHEMA"}:
            state = "EVOLVED_STATE_REQUIRES_SEMANTIC_REDUCER"
        objects.append({
            "object_key": key, "object_class": latest["object_class"],
            "object_name": latest.get("object_name"), "event_count": len(history),
            "first_migration_id": history[0]["migration_id"],
            "last_migration_id": latest["migration_id"],
            "latest_operation": last_operation, "expected_state_status": state,
            "latest_ast_sha256": latest["normalized_ast_sha256"],
            "expected_definition": latest.get("normalized_ast") if state == "CREATE_DEFINITION_AST_AVAILABLE" else None,
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
    history_sources = [source for source in sources if source.get("source_kind") != "ACTIVE_GIT_MIGRATION_FILE"]
    return {
        "format": "moreai.postgresql.expected-object-graph.v1",
        "parser": {"name": "pglast", "postgresql_grammar": "pglast-bundled-server-parser", "authority": "PostgreSQL parser AST"},
        "source_root": str(root), "history_source_count": len(history_sources),
        "active_migration_file_count": len(active_sources),
        "source_record_count": len(sources), "parsed_source_record_count": len(sources) - len(parse_failures),
        "parse_failure_count": len(parse_failures),
        "statement_count": sum(source["statement_count"] for source in sources),
        "ddl_event_count": len(events), "object_key_count": len(objects),
        "sources": sources, "events": events, "objects": objects,
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
    cli.add_argument("--output", required=True, type=Path)
    args = cli.parse_args()
    if not args.migrations_dir.is_dir():
        raise SystemExit("migration_directory_not_found")
    graph = build_graph(args.migrations_dir.resolve(), args.history_dir.resolve() if args.history_dir else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "active_migration_file_count": graph["active_migration_file_count"],
        "history_source_count": graph["history_source_count"],
        "source_record_count": graph["source_record_count"],
        "parsed_source_file_count": graph["parsed_source_file_count"],
        "parse_failure_count": graph["parse_failure_count"],
        "statement_count": graph["statement_count"],
        "ddl_event_count": graph["ddl_event_count"],
        "object_key_count": graph["object_key_count"],
        "output": str(args.output),
    }, separators=(",", ":")))
    return 0  # NOT_VERIFIABLE parse cases are emitted in the graph, not treated as execution failures.


if __name__ == "__main__":
    sys.exit(main())
