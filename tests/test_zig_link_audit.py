import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_zig_link_candidates import audit_links


class ZigLinkAuditTests(unittest.TestCase):
    def test_unique_id_match_is_relative_and_not_compatibility(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            registry, server = Path(a), Path(b)
            (registry / "templates").mkdir()
            (registry / "MIGRATION-V1.json").write_text(json.dumps({"results": [{
                "source_file": "templates/items/iron-ore/v0.1.0/template.json",
                "family": "items", "slug": "iron-ore", "disposition": "migrated",
                "target_file": "templates/items/iron-ore/v1.0.0/template.json",
            }]}), encoding="utf-8")
            (registry / "templates/catalog.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
            target = server / "nested/ore.json"
            target.parent.mkdir()
            target.write_text('{"id":"iron_ore"}', encoding="utf-8")
            report = audit_links(registry, server)
            self.assertEqual(report["results"][0]["disposition"], "unique-id")
            self.assertEqual(report["results"][0]["server_file"], "nested/ore.json")
            self.assertFalse(report["compatibility_claimed"])
            self.assertNotIn(str(server), json.dumps(report))
