from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reconcile import _candidate_matches_observed_reference


class DependencyIdentityBindingTests(unittest.TestCase):
    def test_qualified_function_identity_accepts_catalog_signature(self) -> None:
        self.assertTrue(
            _candidate_matches_observed_reference(
                "function:public.calculate_total",
                "public.calculate_total(numeric, integer)",
            )
        )

    def test_unqualified_function_does_not_guess_search_path(self) -> None:
        self.assertFalse(
            _candidate_matches_observed_reference(
                "function:calculate_total",
                "public.calculate_total(numeric)",
            )
        )

    def test_function_leaf_name_does_not_cross_schema_boundary(self) -> None:
        self.assertFalse(
            _candidate_matches_observed_reference(
                "function:billing.calculate_total",
                "public.calculate_total(numeric)",
            )
        )

    def test_type_identity_requires_exact_qualification(self) -> None:
        self.assertTrue(
            _candidate_matches_observed_reference(
                "type:billing.invoice_state",
                "billing.invoice_state",
            )
        )
        self.assertFalse(
            _candidate_matches_observed_reference(
                "type:invoice_state",
                "billing.invoice_state",
            )
        )

    def test_relation_identity_does_not_match_column_or_schema_suffix(self) -> None:
        self.assertFalse(
            _candidate_matches_observed_reference(
                "public.invoices",
                "public.invoices.invoice_id",
            )
        )
        self.assertFalse(
            _candidate_matches_observed_reference(
                "invoices",
                "public.invoices",
            )
        )

    def test_exact_relation_identity_matches(self) -> None:
        self.assertTrue(
            _candidate_matches_observed_reference(
                "public.invoices",
                "public.invoices",
            )
        )


if __name__ == "__main__":
    unittest.main()
