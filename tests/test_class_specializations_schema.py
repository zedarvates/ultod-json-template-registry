import json
import unittest
from pathlib import Path

from jsonschema import Draft7Validator


class ClassSpecializationsSchemaTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.old = json.loads((self.root / "templates/schemas/class/v0.1.0/schema.json").read_text())
        self.new = json.loads((self.root / "templates/schemas/class/v0.2.0/schema.json").read_text())
        self.validator = Draft7Validator(self.new["properties"]["specializations"])

    def test_previous_strings_and_mixed_representation(self):
        self.assertFalse(list(self.validator.iter_errors(["forest-guardian"])))
        example = json.loads((self.root / "docs/examples/class-specializations-mixed.json").read_text())
        self.assertFalse(list(self.validator.iter_errors(example["specializations"])))

    def test_invalid_scalar_and_identifier_shapes_are_rejected(self):
        for value in ([12], [True], [""], [{"name": "Missing identifier"}], {"id": "not-an-array"}):
            with self.subTest(value=value):
                self.assertTrue(list(self.validator.iter_errors(value)))

    def test_other_authoring_constraints_are_preserved(self):
        self.old["properties"]["specializations"] = self.new["properties"]["specializations"]
        self.assertEqual(self.old, self.new)
        Draft7Validator.check_schema(self.new)


if __name__ == "__main__":
    unittest.main()
