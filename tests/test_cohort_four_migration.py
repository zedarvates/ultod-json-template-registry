import unittest
from pathlib import Path

from scripts.migrate_cohort_four import build_migration


class CohortFourMigrationTests(unittest.TestCase):
    def test_real_cohort_is_exhaustively_classified(self):
        plan = build_migration(Path("."))
        self.assertEqual(len(plan["results"]), 108)
        self.assertEqual(plan["counts"], {"legacy-only-authoritative": 4, "manual-review": 2, "migrated": 102})

    def test_no_technical_identity_is_migrated(self):
        plan = build_migration(Path("."))
        migrated = [result.slug for result in plan["results"] if result.disposition == "migrated"]
        self.assertFalse(any("template" in slug for slug in migrated))
