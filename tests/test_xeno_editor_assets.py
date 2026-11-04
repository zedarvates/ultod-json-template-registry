import hashlib
import json
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


class XenoEditorAssetTests(unittest.TestCase):
    def test_catalogued_asset_hashes_and_review_status(self):
        catalog = json.loads((ROOT / "templates/catalog.json").read_text(encoding="utf-8"))
        entries = [e for e in catalog["entries"] if e.get("family") == "xeno-editor"]
        self.assertTrue(entries, "expected at least one Xeno editor entry")
        for entry in entries:
            spec = json.loads((ROOT / entry["file"]).read_text(encoding="utf-8"))["spec"]
            assets = {}
            for name in ("genome", "source_recipe", "preview"):
                path = PurePosixPath(spec[name + "_file"])
                self.assertEqual(path.parts[:2], ("assets", "xeno-editor"))
                self.assertNotIn("..", path.parts)
                data = (ROOT / path).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), spec[name + "_sha256"])
                assets[name] = data
            genome = json.loads(assets["genome"])
            json.loads(assets["source_recipe"])
            self.assertTrue(genome["review_only"])
            self.assertFalse(genome["server_authoritative"])
            self.assertEqual(genome["bestiary_provenance"]["recipe_sha256"], spec["source_recipe_sha256"])
            self.assertTrue(assets["preview"].startswith(b"\x89PNG\r\n\x1a\n"))


if __name__ == "__main__":
    unittest.main()
