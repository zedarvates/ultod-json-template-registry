import unittest

from jsonschema import Draft202012Validator

from scripts.cohort_three_contracts import convert_legacy, family_schema


class CohortThreeConversionTests(unittest.TestCase):
    def test_ability_omits_balance_and_effects(self):
        result = convert_legacy("abilities", "templates/abilities/fire/v0.1.0/template.json", {
            "id": "fire_wave", "name": "Fire Wave", "ability_type": "Active", "category": "Magic", "target_type": "Area",
            "cooldown": 10, "mana_cost": 20, "effects": [{"damage": 100}], "visual_effects": {"asset": "fire"},
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "Fire Wave", "ability_kind": "active", "category_tag": "magic", "target_kind": "area"})
        self.assertNotIn("cooldown", str(result.document))

    def test_profession_system_remains_authoritative(self):
        result = convert_legacy("professions", "templates/professions/market/v0.1.0/template.json", {"id": "market", "name": "Market", "market_integration": {}}, set())
        self.assertEqual(result.disposition, "legacy-only-authoritative")
        self.assertIsNone(result.document)

    def test_adapted_profession_requires_manual_review(self):
        result = convert_legacy("professions", "templates/professions/uo-smith/v0.1.0/template.json", {"id": "uo_smith", "name": "Uo Smith", "display_name": "Smith adapted_reference"}, set())
        self.assertEqual(result.disposition, "manual-review")

    def test_skill_and_talent_keep_only_tags(self):
        skill = convert_legacy("skills", "templates/skills/alchemy/v0.1.0/template.json", {"id": "alchemy", "name": "Alchemy", "category": "Crafting", "subcategory": "Potions", "max_level": 100}, set())
        talent = convert_legacy("talent", "templates/talent/guard/v0.1.0/template.json", {"id": "guard", "name": "Guard", "type": "Stat Bonus", "effects": [{"value": 5}]}, set())
        self.assertEqual(skill.document["spec"], {"display_name": "Alchemy", "category_tag": "crafting", "subcategory_tag": "potions"})
        self.assertEqual(talent.document["spec"], {"display_name": "Guard", "talent_kind": "stat-bonus"})

    def test_collision_requires_manual_review(self):
        result = convert_legacy("skills", "templates/skills/mining/v0.1.0/template.json", {"id": "mining", "name": "Mining"}, {"mining"})
        self.assertEqual(result.disposition, "manual-review")

    def test_schemas_are_closed_and_valid(self):
        for family in ("abilities", "professions", "skills", "talent"):
            schema = family_schema(family)
            Draft202012Validator.check_schema(schema)
            self.assertFalse(schema["allOf"][1]["properties"]["spec"]["additionalProperties"])
