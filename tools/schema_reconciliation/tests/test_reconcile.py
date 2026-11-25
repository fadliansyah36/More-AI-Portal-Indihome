from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reconcile


class DependencyBindingTests(unittest.TestCase):
    def test_binds_ast_table_and_function_candidates_to_observed_pg_depend(self):
        expected = {
            "object_class": "VIEW",
            "object_name": "public.learning_path_progress_summary",
            "dependency_candidates": ["public.learning_lessons", "function:count", "function:sum"],
        }
        edges = {
            "public.learning_path_progress_summary": [
                {"dependent_identity": "public.learning_path_progress_summary", "referenced_identity": "public.learning_lessons"},
                {"dependent_identity": "public.learning_path_progress_summary", "referenced_identity": "pg_catalog.count(any)"},
                {"dependent_identity": "public.learning_path_progress_summary", "referenced_identity": "pg_catalog.sum(any)"},
            ],
        }
        evidence = reconcile._dependency_binding_evidence(expected, edges)
        self.assertEqual(evidence["bound_candidate_count"], 3)
        self.assertEqual(evidence["unbound_candidates"], [])
        self.assertEqual(evidence["comparison_status"], "ALL_AST_CANDIDATES_FOUND_IN_OBSERVED_PG_DEPEND_EDGES")

    def test_keeps_partial_dependency_bindings_explicit(self):
        expected = {
            "object_class": "TABLE",
            "object_name": "public.example",
            "dependency_candidates": ["public.parent", "type:custom_type"],
        }
        edges = {
            "public.example": [
                {"dependent_identity": "public.example", "referenced_identity": "public.parent.id"},
            ],
        }
        evidence = reconcile._dependency_binding_evidence(expected, edges)
        self.assertEqual(evidence["bound_candidate_count"], 1)
        self.assertEqual(evidence["unbound_candidates"], ["type:custom_type"])
        self.assertEqual(evidence["comparison_status"], "PARTIAL_AST_CANDIDATES_FOUND_IN_OBSERVED_PG_DEPEND_EDGES")

    def test_does_not_claim_exact_binding_for_unsupported_dependent_identity(self):
        expected = {
            "object_class": "TRIGGER",
            "object_name": "public.example.trigger_example",
            "dependency_candidates": ["public.example"],
        }
        evidence = reconcile._dependency_binding_evidence(expected, {})
        self.assertEqual(evidence["comparison_status"], "DEPENDENT_IDENTITY_CLASS_NOT_SUPPORTED_FOR_EXACT_BINDING")


if __name__ == "__main__":
    unittest.main()
