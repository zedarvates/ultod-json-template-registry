import unittest
from pathlib import Path

from scripts.migrate_cohort_two import build_migration


class CohortTwoMigrationTests(unittest.TestCase):
    def test_real_cohort_is_exhaustively_classified(self):
        plan = build_migration(Path("."))
        self.assertEqual(len(plan["results"]), 15)
        self.assertEqual(plan["counts"], {"legacy-only-authoritative": 2, "manual-review": 4, "migrated": 9})
        self.assertEqual(sum(plan["counts"].values()), 15)

    def test_authoritative_city_sources_are_not_superseded(self):
        plan = build_migration(Path("."))
        catalog = __import__("json").loads(plan["files"]["templates/catalog.json"])
        entries = {entry["file"]: entry for entry in catalog["entries"]}
        for source in (
            "templates/cities/template/v0.1.0/template.json",
            "templates/city-layouts/template/v0.1.0/template.json",
        ):
            self.assertNotIn("superseded_by", entries[source])
