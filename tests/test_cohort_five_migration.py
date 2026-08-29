import unittest
from pathlib import Path
from scripts.migrate_cohort_five import build_migration


class CohortFiveMigrationTests(unittest.TestCase):
    def test_real_cohort_is_exhaustively_classified(self):
        plan=build_migration(Path(".")); self.assertEqual(len(plan["results"]),54); self.assertEqual(plan["counts"],{"manual-review":9,"migrated":45})

    def test_no_technical_identity_is_migrated(self):
        plan=build_migration(Path(".")); migrated=[r.slug for r in plan["results"] if r.disposition=="migrated"]; self.assertFalse(any("template" in slug or "example" in slug for slug in migrated))
