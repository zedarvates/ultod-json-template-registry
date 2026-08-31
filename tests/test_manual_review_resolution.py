import unittest
from pathlib import Path

from scripts.audit_manual_review_resolution import audit_resolutions
from scripts.resolve_manual_reviews import build


class ManualReviewResolutionTests(unittest.TestCase):
    def test_resolution_builder_closes_all_manual_reviews(self):
        plan = build(Path("."))
        self.assertEqual(len(plan["resolutions"]), 61)
        self.assertTrue(all(
            item["resolution_disposition"] == "legacy-only-authoritative"
            for item in plan["resolutions"]
        ))
        self.assertTrue(all(item["strict_target_file"] is None for item in plan["resolutions"]))

    def test_resolution_audit_has_no_gap_or_duplicate(self):
        result = audit_resolutions(Path("."))
        self.assertEqual(result["manual_reviews"], 61)
        self.assertEqual(result["resolved"], 61)
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["duplicates"], [])
        self.assertEqual(result["extraneous"], [])
