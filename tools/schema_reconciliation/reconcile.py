from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from pglast.parser import parse_sql_json
from schema_graph import _normalize


VALID_CLASSES = {
    "MATCH", "MISSING", "UNEXPECTED", "DEFINITION_MISMATCH",
    "SECURITY_MISMATCH", "DEPENDENCY_MISMATCH", "NOT_VERIFIABLE",
}


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _observed_ast(item: dict[str, Any]) -> Any | None:
    direct = item.get("definition_ast")
    if isinstance(direct, dict):
        return _normalize(direct)
    sql = item.get("definition_sql")
    if not isinstance(sql, str) or not sql.strip():
        return None
    try:
        parsed = json.loads(parse_sql_json(sql))
    except Exception:
        return None
    statements = parsed.get("stmts", []) if isinstance(parsed, dict) else []
    if len(statements) != 1 or not isinstance(statements[0], dict):
        return None
    statement = statements[0].get("stmt")
    return _normalize(statement) if isinstance(statement, dict) else None

def _root_tag(value: Any) -> str | None:
    if isinstance(value, dict) and len(value) == 1:
        return next(iter(value))
    return None


def _candidate_matches_observed_reference(candidate: str, reference: str) -> bool:
    """Bind only identities proven equal by the source and observed catalog.

    PostgreSQL resolves unqualified names through search_path. Unless that
    search_path is captured as evidence, an unqualified AST reference cannot
    be assigned to an arbitrary schema-qualified pg_depend identity. Likewise,
    suffix matching can bind unrelated objects from different schemas.
    """
    value = candidate.strip()
    observed = reference.strip()
    if not value or not observed:
        return False

    if value.startswith("function:"):
        name = value[len("function:"):].strip()
        # pg_depend identities may append a rendered argument signature.
        # Compare the complete qualified function name, never only its leaf.
        observed_name = observed.split("(", 1)[0].strip()
        return bool(name) and observed_name == name

    if value.startswith("type:"):
        name = value[len("type:"):].strip()
        return bool(name) and observed == name

    # Relation and other catalog identities must be exact. A dotted suffix
    # can denote a different schema or a column, not the same relation.
    return observed == value


def _dependency_binding_evidence(expected_item: dict[str, Any], dependency_map: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    object_class = expected_item.get("object_class")
    object_name = expected_item.get("object_name")
    candidates = expected_item.get("dependency_candidates") or []
    if not isinstance(candidates, list):
        candidates = []
    if not candidates:
        return {
            "expected_ast_candidates": [],
            "observed_catalog_edges": [],
            "comparison_status": "NO_AST_DEPENDENCY_CANDIDATES",
            "bound_candidate_count": 0,
            "unbound_candidates": [],
        }
    if object_class not in {"TABLE", "VIEW", "INDEX", "FUNCTION", "COLUMN"} or not isinstance(object_name, str):
        return {
            "expected_ast_candidates": candidates,
            "observed_catalog_edges": [],
            "comparison_status": "DEPENDENT_IDENTITY_CLASS_NOT_SUPPORTED_FOR_EXACT_BINDING",
            "bound_candidate_count": 0,
            "unbound_candidates": candidates,
        }
    edges = dependency_map.get(object_name, [])
    references = [
        str(edge.get("referenced_identity"))
        for edge in edges
        if isinstance(edge, dict) and isinstance(edge.get("referenced_identity"), str)
    ]
    bound = [
        candidate for candidate in candidates
        if any(_candidate_matches_observed_reference(str(candidate), reference) for reference in references)
    ]
    unbound = [candidate for candidate in candidates if candidate not in bound]
    status = (
        "ALL_AST_CANDIDATES_FOUND_IN_OBSERVED_PG_DEPEND_EDGES"
        if not unbound else
        "PARTIAL_AST_CANDIDATES_FOUND_IN_OBSERVED_PG_DEPEND_EDGES"
        if bound else
        "NO_AST_CANDIDATE_BOUND_TO_OBSERVED_PG_DEPEND_EDGES"
    )
    return {
        "expected_ast_candidates": candidates,
        "observed_catalog_edges": edges,
        "comparison_status": status,
        "bound_candidate_count": len(bound),
        "unbound_candidates": unbound,
        "observed_referenced_identities": sorted(set(references)),
    }

def reconcile(expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    expected_objects = expected.get("objects")
    observed_objects = observed.get("objects")
    if not isinstance(expected_objects, list) or not isinstance(observed_objects, list):
        raise ValueError("expected_and_observed_objects_must_be_arrays")

    expected_by_key = {
        item.get("object_key"): item
        for item in expected_objects
        if isinstance(item, dict) and isinstance(item.get("object_key"), str)
    }
    observed_by_key = {
        item.get("object_key"): item
        for item in observed_objects
        if isinstance(item, dict) and isinstance(item.get("object_key"), str)
    }
    applied = set(observed.get("applied_migration_ids") or [])
    complete_expected = observed.get("expected_source_coverage_complete") is True
    rows: list[dict[str, Any]] = []
    dependency_map: dict[str, list[dict[str, Any]]] = {}
    for edge in observed.get("dependency_edges") or []:
        if isinstance(edge, dict) and isinstance(edge.get("dependent_identity"), str):
            dependency_map.setdefault(edge["dependent_identity"], []).append(edge)

    for key, expected_item in sorted(expected_by_key.items()):
        observed_item = observed_by_key.get(key)
        lineage = expected_item.get("migration_lineage") or []
        latest_migration = expected_item.get("last_migration_id")
        latest_operation = expected_item.get("latest_operation")
        all_events_applied = bool(lineage) and all(
            isinstance(event, dict) and event.get("migration_id") in applied
            for event in lineage
        )

        if latest_operation == "DROP":
            if latest_migration in applied and all_events_applied:
                classification = "UNEXPECTED" if observed_item else "MATCH"
                reason = "Applied source lineage drops the object; observed presence is unexpected." if observed_item else "Applied source lineage drops the object and it is absent from the observed catalog."
            else:
                classification = "NOT_VERIFIABLE"
                reason = "The DROP source event is not proven applied; live presence or absence is not classified as drift."
        elif not observed_item:
            if expected_item.get("expected_state_status") == "SOURCE_CONFLICT_NOT_VERIFIABLE" or expected_item.get("object_class") in {"ACL", "DEFAULT_ACL", "ROLE_MEMBERSHIP", "OWNERSHIP", "OBJECT", "COMMENT", "ROLE"} or "unnamed:" in str(expected_item.get("object_name") or "") or ("signature-not-verifiable" in str(expected_item.get("object_name") or "")):
                classification = "NOT_VERIFIABLE"
                reason = "The source AST does not provide a normalized identity compatible with the observed catalog representation or has conflicting provenance."
            elif latest_migration in applied and all_events_applied:
                classification = "MISSING"
                reason = "Source lineage is recorded as applied but the object key is absent from the observed catalog."
            else:
                classification = "NOT_VERIFIABLE"
                reason = "The latest source event is not proven applied; absence is not classified as live drift."
        else:
            expected_definition = expected_item.get("expected_definition")
            observed_definition = observed_item.get("definition") or _observed_ast(observed_item)
            expected_security = expected_item.get("security_fingerprint")
            observed_security = observed_item.get("security_fingerprint")
            expected_dependencies = expected_item.get("dependency_fingerprint")
            observed_dependencies = observed_item.get("dependency_fingerprint")

            if expected_security is not None and observed_security is not None and expected_security != observed_security:
                classification = "SECURITY_MISMATCH"
                reason = "Expected and observed security fingerprints differ."
            elif expected_dependencies is not None and observed_dependencies is not None and expected_dependencies != observed_dependencies:
                classification = "DEPENDENCY_MISMATCH"
                reason = "Expected and observed dependency fingerprints differ."
            elif expected_definition is not None and observed_definition is not None:
                if _root_tag(expected_definition) != _root_tag(observed_definition):
                    classification = "NOT_VERIFIABLE"
                    reason = "Expected and observed definitions use different AST roots; object-specific normalization is required."
                elif canonical_hash(expected_definition) == canonical_hash(observed_definition):
                    classification = "MATCH"
                    reason = "Normalized PostgreSQL AST definitions are identical."
                else:
                    classification = "DEFINITION_MISMATCH"
                    reason = "Normalized PostgreSQL AST definitions differ."
            else:
                classification = "NOT_VERIFIABLE"
                reason = (
                    "Object is present on both sides, but one or both sides lack a complete "
                    "normalized definition/security/dependency fingerprint."
                )

        rows.append({
            "object_key": key,
            "object_class": expected_item.get("object_class"),
            "classification": classification,
            "latest_migration_id": latest_migration,
            "latest_operation": latest_operation,
            "observed_present": observed_item is not None,
            "reason": reason,
            "expected_evidence": {
                "event_count": expected_item.get("event_count"),
                "latest_ast_sha256": expected_item.get("latest_ast_sha256"),
                "migration_lineage": lineage,
            },
            "observed_evidence": observed_item,
            "dependency_evidence": _dependency_binding_evidence(expected_item, dependency_map),
        })

    for key, observed_item in sorted(observed_by_key.items()):
        if key in expected_by_key:
            continue
        classification = "UNEXPECTED" if complete_expected else "NOT_VERIFIABLE"
        rows.append({
            "object_key": key,
            "object_class": observed_item.get("object_class"),
            "classification": classification,
            "latest_migration_id": None,
            "latest_operation": None,
            "observed_present": True,
            "reason": (
                "Observed object is outside a declared complete expected-source scope."
                if complete_expected else
                "No source object is mapped, but expected-source coverage is incomplete; platform or historical origin cannot be excluded."
            ),
            "expected_evidence": None,
            "observed_evidence": observed_item,
        })

    counts = {name: 0 for name in sorted(VALID_CLASSES)}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    return {
        "format": "moreai.postgresql.semantic-reconciliation.v1",
        "expected_graph_format": expected.get("format"),
        "observed_snapshot_id": observed.get("snapshot_id"),
        "security_snapshot_id": observed.get("security_snapshot_id"),
        "dependency_snapshot_id": observed.get("dependency_snapshot_id"),
        "dependency_edge_count": len(observed.get("dependency_edges") or []),
        "routine_privilege_row_count": len(observed.get("routine_privilege_rows") or []),
        "comparison_mode": "read_only_object_level",
        "expected_source_coverage_complete": complete_expected,
        "object_count": len(rows),
        "classification_counts": counts,
        "objects": rows,
        "global_no_drift_claim": False,
        "limitations": [
            "The comparator only emits MATCH when normalized expected and observed definitions are both supplied.",
            "AST parsing alone is not a final schema definition for ALTER/GRANT/RENAME event chains.",
            "Objects whose source event is not proven applied are not treated as live MISSING drift.",
            "Observed objects outside incomplete source coverage are NOT_VERIFIABLE, not automatically UNEXPECTED.",
            "No classification is an execution receipt; exact deployed bytes require independent deployment evidence.",
        ],
    }


def main() -> int:
    cli = argparse.ArgumentParser(description="Compare source-derived expected objects to a read-only catalog snapshot.")
    cli.add_argument("--expected", required=True, type=Path)
    cli.add_argument("--observed", required=True, type=Path)
    cli.add_argument("--security", type=Path, default=None)
    cli.add_argument("--dependencies", type=Path, default=None)
    cli.add_argument("--output", required=True, type=Path)
    args = cli.parse_args()
    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    observed = json.loads(args.observed.read_text(encoding="utf-8"))
    if args.security is not None:
        security = json.loads(args.security.read_text(encoding="utf-8"))
        observed["security_snapshot_id"] = security.get("snapshot_id")
        base_objects = [item for item in observed.get("objects", []) if isinstance(item, dict) and item.get("object_class") != "ACL"]
        observed["objects"] = base_objects + list(security.get("acl_objects") or []) + list(security.get("default_acl_objects") or []) + list(security.get("role_memberships") or []) + list(security.get("roles") or [])
        observed["routine_privilege_rows"] = security.get("routine_privileges") or []
    if args.dependencies is not None:
        dependencies = json.loads(args.dependencies.read_text(encoding="utf-8"))
        observed["dependency_snapshot_id"] = dependencies.get("snapshot_id")
        observed["dependency_edges"] = dependencies.get("edges") or []
    result = reconcile(expected, observed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "object_count": result["object_count"],
        "classification_counts": result["classification_counts"],
        "global_no_drift_claim": False,
        "output": str(args.output),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
