import unittest

from scripts.template_contract import (
    compute_spec_checksum,
    decode_json_bytes,
    parse_strict_template_path,
    validate_document_limits,
    validate_envelope_identity,
    validate_schema_identity,
)


class TemplateContractPrimitiveTests(unittest.TestCase):
    def test_spec_checksum_is_stable_across_key_order(self):
        left = {"tags": ["forest"], "category": "animal"}
        right = {"category": "animal", "tags": ["forest"]}
        self.assertEqual(compute_spec_checksum(left), compute_spec_checksum(right))
        self.assertRegex(compute_spec_checksum(left), r"^sha256:[0-9a-f]{64}$")

    def test_strict_json_rejects_duplicate_keys_and_non_finite_numbers(self):
        for content in (b'{"id":"a","id":"b"}', b'{"value":NaN}', b'{"value":Infinity}'):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    decode_json_bytes(content)

    def test_document_limits_reject_excessive_depth_and_file_size(self):
        nested = {}
        cursor = nested
        for _ in range(33):
            cursor["child"] = {}
            cursor = cursor["child"]
        errors = validate_document_limits(nested, content_size=262145)
        self.assertIn("document exceeds 262144 bytes", errors)
        self.assertTrue(any("nesting exceeds 32 levels" in error for error in errors))

    def test_strict_path_extracts_family_slug_and_version(self):
        parsed = parse_strict_template_path(
            "templates/monsters/forest-wolf/v1.2.3/template.json"
        )
        self.assertEqual(parsed.family, "monsters")
        self.assertEqual(parsed.slug, "forest-wolf")
        self.assertEqual(parsed.version, "1.2.3")

    def test_identity_rejects_path_document_disagreement(self):
        document = {
            "id": "monsters:wrong-wolf",
            "slug": "forest-wolf",
            "family": "monsters",
            "version": "1.2.3",
        }
        self.assertEqual(
            validate_envelope_identity(
                "templates/monsters/forest-wolf/v1.2.3/template.json", document
            ),
            ["id must equal monsters:forest-wolf"],
        )

    def test_strict_path_rejects_unversioned_or_nested_layouts(self):
        for path in (
            "templates/monsters/forest-wolf/template.json",
            "templates/generated-content/quests/example/v1.0.0/template.json",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    parse_strict_template_path(path)

    def test_schema_id_must_match_family_and_version_path(self):
        errors = validate_schema_identity(
            "templates/schemas/monsters/v1.2.3/schema.json",
            {"$id": "https://ultimateodycer.com/schemas/items/1.2.3"},
        )
        self.assertEqual(
            errors,
            ["$id must equal https://ultimateodycer.com/schemas/monsters/1.2.3"],
        )


if __name__ == "__main__":
    unittest.main()
