import unittest

from jsonschema import Draft202012Validator
from scripts.pilot_contracts import convert_legacy, family_schema, find_slug_collisions


class PilotConversionTests(unittest.TestCase):
    def test_collision_is_manual_review(self):
        result = convert_legacy("classes", "templates/classes/mage/v0.1.0/template.json", {"name": "Mage"}, {"mage"})
        self.assertEqual(result.disposition, "manual-review")
        self.assertIsNone(result.document)

    def test_spell_omits_runtime_values(self):
        result = convert_legacy("spells", "templates/spells/fireball/v0.1.0/template.json", {
            "name": "Fireball", "school": "fire", "rarity": "common",
            "spell_type": "damage", "target_type": "single", "damage": {"base": 25},
            "range": 6, "cooldown": 1000, "mana_cost": 20,
        }, set())
        self.assertEqual(result.disposition, "migrated")
        self.assertEqual(result.document["spec"], {
            "display_name": "Fireball", "school": "fire", "rarity": "common",
            "spell_kind": "damage", "target_kind": "single",
        })
        self.assertNotIn("cooldown", str(result.document))

    def test_collisions_normalize_underscores(self):
        self.assertEqual(find_slug_collisions([
            "templates/classes/arcane_mage/0.1.0/template.json",
            "templates/classes/arcane-mage/v0.1.0/template.json",
        ]), {"arcane-mage"})

    def test_family_schemas_close_spec(self):
        for family in ("classes", "races", "items", "spells", "monsters"):
            schema = family_schema(family)
            Draft202012Validator.check_schema(schema)
            spec = schema["allOf"][1]["properties"]["spec"]
            self.assertFalse(spec["additionalProperties"])
            self.assertEqual(spec["required"], ["display_name"])
