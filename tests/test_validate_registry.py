import json
import unittest

from scripts.validate_registry import validate_public_content


class PublicSafetyValidationTests(unittest.TestCase):
    def test_rejects_admin_debug_and_commercial_keys(self):
        document = {
            "admin_controls": {},
            "debug_mode": False,
            "shop_info": {"buy_price": 10},
        }

        violations = validate_public_content(document, json.dumps(document))

        self.assertEqual(violations, ["admin-control", "commercial"])

    def test_rejects_secret_values_internal_paths_and_rights_terms(self):
        document = {
            "api_key": "example-secret-value",
            "asset_path": "C:\\private\\model.glb",
            "inspiration": "Warcraft",
        }

        violations = validate_public_content(document, json.dumps(document))

        self.assertEqual(violations, ["internal", "rights", "secret"])

    def test_accepts_statless_original_identity(self):
        document = {
            "id": "original_spell_1234567890",
            "template_type": "spell",
            "version": "0.1.0",
            "dependencies": [],
        }

        self.assertEqual(validate_public_content(document, json.dumps(document)), [])


if __name__ == "__main__":
    unittest.main()
