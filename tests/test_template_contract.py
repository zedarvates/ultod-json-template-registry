import json
import tempfile
import unittest
from pathlib import Path

from scripts.template_contract import (
    compute_spec_checksum,
    decode_json_bytes,
    parse_strict_template_path,
    validate_document_limits,
    validate_envelope_identity,
    validate_schema_references,
    validate_schema_identity,
    validate_with_schema,
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


def strict_document(spec):
    return {
        "$schema": "../../../schemas/monsters/v1.0.0/schema.json",
        "contract_version": "1.0.0",
        "id": "monsters:forest-wolf",
        "slug": "forest-wolf",
        "family": "monsters",
        "version": "1.0.0",
        "authority": "declarative",
        "intended_consumers": [],
        "compatibility": [],
        "dependencies": [],
        "spec_checksum": compute_spec_checksum(spec),
        "spec": spec,
    }


class SchemaStoreTests(unittest.TestCase):
    def test_family_schema_refines_and_closes_spec(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            common = root / "templates/schemas/template-contract/v1.0.0/schema.json"
            family = root / "templates/schemas/monsters/v1.0.0/schema.json"
            common.parent.mkdir(parents=True)
            family.parent.mkdir(parents=True)
            common.write_text(
                Path("templates/schemas/template-contract/v1.0.0/schema.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            family.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://ultimateodycer.com/schemas/monsters/1.0.0",
                        "allOf": [
                            {
                                "$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"
                            },
                            {
                                "properties": {
                                    "spec": {
                                        "type": "object",
                                        "required": ["category"],
                                        "properties": {"category": {"type": "string"}},
                                        "additionalProperties": False,
                                    }
                                }
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            document = strict_document(spec={"category": "animal", "runtime_hp": 100})
            errors = validate_with_schema(
                root, "templates/schemas/monsters/v1.0.0/schema.json", document
            )
            self.assertTrue(any("runtime_hp" in error for error in errors))

    def test_common_schema_rejects_unknown_root_field(self):
        document = strict_document(spec={"category": "animal"})
        document["unexpected"] = True
        errors = validate_with_schema(
            Path("."),
            "templates/schemas/template-contract/v1.0.0/schema.json",
            document,
        )
        self.assertTrue(any("unexpected" in error for error in errors))

    def test_schema_reference_must_resolve_from_local_store(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            schema = root / "templates/schemas/monsters/v1.0.0/schema.json"
            schema.parent.mkdir(parents=True)
            schema.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://ultimateodycer.com/schemas/monsters/1.0.0",
                        "$ref": "https://ultimateodycer.com/schemas/missing/1.0.0",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                validate_schema_references(
                    root, "templates/schemas/monsters/v1.0.0/schema.json"
                ),
                [
                    "unresolved local schema reference: "
                    "https://ultimateodycer.com/schemas/missing/1.0.0"
                ],
            )


if __name__ == "__main__":
    unittest.main()
