from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
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
        if key.endswith("Stmt") or key in {"RangeVar", "TypeName", "FuncCall", "Constraint"}:
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
        signature = hashlib.sha256(json.dumps(_normalize(parameters), sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
        return [f"{'.'.join(names)}#args:{signature}"]
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


def build_graph(root: Path) -> dict[str, Any]:
    files = sorted(root.rglob("*.sql"), key=lambda p: p.relative_to(root).as_posix())
    events: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for path in files:
        file_events, source_record = parse_source(path, root)
        events.extend(file_events)
        sources.append(source_record)

    object_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        name = event.get("object_name")
        if not isinstance(name, str) or not name:
            key = f"NOT_VERIFIABLE:{event['migration_id']}:{event['statement_ordinal']}"
        else:
            key = f"{event['object_class']}:{name}"
        object_events[key].append(event)

    objects = []
    for key, history in sorted(object_events.items()):
        history.sort(key=lambda item: (item["migration_id"], item["statement_ordinal"]))
        latest = history[-1]
        last_operation = latest["operation"]
        state = "NOT_VERIFIABLE"
        if latest["semantic_status"] == "AST_PARSED" and last_operation == "CREATE":
            state = "CREATE_DEFINITION_AST_AVAILABLE"
        elif last_operation == "DROP":
            state = "DROPPED_IN_SOURCE_LINEAGE"
        elif last_operation in {"ALTER", "GRANT_OR_REVOKE", "RENAME", "ALTER_SCHEMA"}:
            state = "EVOLVED_STATE_REQUIRES_SEMANTIC_REDUCER"
        objects.append({
            "object_key": key,
            "object_class": latest["object_class"],
            "object_name": latest.get("object_name"),
            "event_count": len(history),
            "first_migration_id": history[0]["migration_id"],
            "last_migration_id": latest["migration_id"],
            "latest_operation": last_operation,
            "expected_state_status": state,
            "latest_ast_sha256": latest["normalized_ast_sha256"],
            "expected_definition": latest["normalized_ast"] if state == "CREATE_DEFINITION_AST_AVAILABLE" else None,
            "migration_lineage": [
                {
                    "migration_id": item["migration_id"],
                    "source_path": item["source_path"],
                    "source_sha256": item["source_sha256"],
                    "git_blob_sha1": item["git_blob_sha1"],
                    "statement_ordinal": item["statement_ordinal"],
                    "operation": item["operation"],
                    "ast_sha256": item["normalized_ast_sha256"],
                }
                for item in history
            ],
        })

    parse_failures = [source for source in sources if source["parse_status"] != "PARSED"]
    return {
        "format": "moreai.postgresql.expected-object-graph.v1",
        "parser": {"name": "pglast", "postgresql_grammar": "pglast-bundled-server-parser", "authority": "PostgreSQL parser AST"},
        "source_root": str(root),
        "source_file_count": len(sources),
        "parsed_source_file_count": len(sources) - len(parse_failures),
        "parse_failure_count": len(parse_failures),
        "statement_count": sum(source["statement_count"] for source in sources),
        "ddl_event_count": len(events),
        "object_key_count": len(objects),
        "sources": sources,
        "events": events,
        "objects": objects,
        "limitations": [
            "AST parsing proves grammar recognition, not migration execution.",
            "ALTER event folding into complete final definitions is not inferred; affected objects remain NOT_VERIFIABLE until a supported reducer exists.",
            "Function bodies and dynamic SQL are not treated as outer SQL AST; procedural bodies are explicitly marked opaque.",
            "Dependency candidates are AST RangeVar references, not a complete PostgreSQL dependency resolver.",
            "ACL, ownership, extension, policy and role effects require catalog-specific semantic folding before global MATCH can be assigned.",
        ],
    }


def main() -> int:
    cli = argparse.ArgumentParser(description="Build a PostgreSQL AST-backed static expected-object event graph.")
    cli.add_argument("--migrations-dir", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    args = cli.parse_args()
    if not args.migrations_dir.is_dir():
        raise SystemExit("migration_directory_not_found")
    graph = build_graph(args.migrations_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_file_count": graph["source_file_count"],
        "parsed_source_file_count": graph["parsed_source_file_count"],
        "parse_failure_count": graph["parse_failure_count"],
        "statement_count": graph["statement_count"],
        "ddl_event_count": graph["ddl_event_count"],
        "object_key_count": graph["object_key_count"],
        "output": str(args.output),
    }, separators=(",", ":")))
    return 0 if graph["parse_failure_count"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
