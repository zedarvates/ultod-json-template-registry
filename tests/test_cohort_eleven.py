import unittest
from pathlib import Path

from scripts.audit_migration_coverage import audit_coverage
from scripts.migrate_cohort_eleven import build


class CohortElevenTests(unittest.TestCase):
    def test_final_bulk_is_exhaustively_authoritative(self):
        plan = build(Path("."))
        self.assertEqual(len(plan["results"]), 1169)
        self.assertEqual(plan["counts"], {"legacy-only-authoritative": 1169})
        self.assertTrue(all(result["target_file"] is None for result in plan["results"]))

    def test_every_legacy_source_has_exactly_one_disposition(self):
        coverage = audit_coverage(Path("."))
        self.assertEqual(coverage["legacy_sources"], 4047)
        self.assertEqual(coverage["classified_sources"], 4047)
        self.assertEqual(coverage["missing"], [])
        self.assertEqual(coverage["duplicates"], {})
        self.assertEqual(coverage["extraneous"], [])
