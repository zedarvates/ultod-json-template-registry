import unittest
from pathlib import Path

from scripts.migrate_cohort_one import build_migration


class CohortOneMigrationTests(unittest.TestCase):
    def test_real_cohort_is_exhaustively_classified(self):
        plan = build_migration(Path("."))
        self.assertEqual(len(plan["results"]), 26)
        self.assertEqual(plan["counts"], {"legacy-only-authoritative": 3, "manual-review": 1, "migrated": 22})
        self.assertEqual(sum(plan["counts"].values()), 26)

    def test_authoritative_achievement_sources_are_not_superseded(self):
        plan = build_migration(Path("."))
        catalog = __import__("json").loads(plan["files"]["templates/catalog.json"])
        entries = {entry["file"]: entry for entry in catalog["entries"]}
        source = "templates/achievements/combat/v0.1.0/template.json"
        self.assertNotIn("superseded_by", entries[source])
