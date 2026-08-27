import unittest
from pathlib import Path

from scripts.migrate_cohort_three import build_migration


class CohortThreeMigrationTests(unittest.TestCase):
    def test_real_cohort_is_exhaustively_classified(self):
        plan = build_migration(Path("."))
        self.assertEqual(len(plan["results"]), 200)
        self.assertEqual(plan["counts"], {"legacy-only-authoritative": 4, "manual-review": 31, "migrated": 165})
        self.assertEqual(sum(plan["counts"].values()), 200)

    def test_no_technical_identity_is_migrated(self):
        plan = build_migration(Path("."))
        migrated = [result.slug for result in plan["results"] if result.disposition == "migrated"]
        self.assertFalse(any(slug.startswith("uo-") or "template" in slug for slug in migrated))
