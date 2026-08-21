import unittest

from scripts.validate_registry import validate_public_content, validate_public_path


class PublicRegistryPolicyTests(unittest.TestCase):
    def test_rejects_hash_placeholder_directory(self):
        violations = validate_public_path(
            "templates/monsters/original-aberration-1234567890/v0.1.0/template.json"
        )
        self.assertEqual(violations, ["hash-placeholder-name"])

    def test_rejects_privileged_and_commercial_fields(self):
        document = {
            "id": "sample",
            "admin_controls": {},
            "shop_info": {"buy_price": 10},
        }
        self.assertEqual(
            validate_public_content(document),
            ["admin-control", "commercial"],
        )

    def test_accepts_semantic_sanitized_template(self):
        document = {
            "id": "aberration_creature_0001",
            "base_stats": {"health": 100},
            "loot_table": {},
        }
        self.assertEqual(validate_public_content(document), [])
        self.assertEqual(
            validate_public_path(
                "templates/monsters/aberration-creature-0001/v0.1.0/template.json"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
