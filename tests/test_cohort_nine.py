import unittest
from pathlib import Path

from scripts.migrate_cohort_nine import build


class CohortNineTests(unittest.TestCase):
    def test_all_sources_are_exhaustively_classified_without_targets(self):
        plan = build(Path("."))
        self.assertEqual(len(plan["results"]), 44)
        self.assertEqual(plan["counts"], {
            "legacy-only-authoritative": 40,
            "legacy-only-narrative": 4,
        })
        self.assertTrue(all(result["target_file"] is None for result in plan["results"]))

    def test_rts_never_claims_strict_compatibility(self):
        plan = build(Path("."))
        rts = [result for result in plan["results"] if result["family"] == "rts"]
        self.assertEqual(len(rts), 13)
        self.assertTrue(all(result["disposition"] == "legacy-only-authoritative" for result in rts))
