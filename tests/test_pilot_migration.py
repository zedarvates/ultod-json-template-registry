import unittest
from pathlib import Path

from scripts.migrate_pilot_families import build_migration


class PilotMigrationTests(unittest.TestCase):
    def test_real_registry_is_exhaustively_classified(self):
        plan = build_migration(Path("."), ("classes", "races", "items", "spells", "monsters"))
        self.assertEqual(len(plan["results"]), 2327)
        self.assertEqual(plan["counts"].get("manual-review"), 14)
        self.assertEqual(sum(plan["counts"].values()), 2327)
