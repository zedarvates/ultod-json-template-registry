import unittest

from jsonschema import Draft202012Validator

from scripts.cohort_one_contracts import convert_legacy, family_schema


class CohortOneConversionTests(unittest.TestCase):
    def test_achievements_remain_authoritative_legacy(self):
        result = convert_legacy("achievements", "templates/achievements/combat/v0.1.0/template.json", {"achievements": [{"required_progress": 10}]}, set())
        self.assertEqual(result.disposition, "legacy-only-authoritative")
        self.assertIsNone(result.document)

    def test_avatar_keeps_only_identity_tags(self):
        result = convert_legacy("avatars", "templates/avatars/scout/v0.1.0/template.json", {
            "name": "Scout", "style_profile": {"species": "Human", "variant": "Light", "body_frame": "Feminine"},
            "morphs": {"values": {"height": 0.5}}, "hair": {"style": "asset_hair"},
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "Scout", "species_tag": "human", "variant_tag": "light", "body_frame_tag": "feminine"})
        self.assertEqual(result.document["intended_consumers"], ["llm-pipeline"])
        self.assertNotIn("morphs", str(result.document))
        self.assertNotIn("asset_hair", str(result.document))

    def test_biome_omits_balance_spawns_and_assets(self):
        result = convert_legacy("biomes", "templates/biomes/cave/v0.1.0/template.json", {
            "name": "Cave", "category": "Dangerous", "climate": "Cool", "terrain_types": ["Cave Walls"],
            "level_range": {"min": 10}, "resources": [{"respawn_time": 100}], "visual_theme": {"ground_texture": "cave.png"},
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "Cave", "category_tag": "dangerous", "climate_tag": "cool", "terrain_tags": ["cave-walls"]})
        self.assertNotIn("respawn", str(result.document))
        self.assertNotIn("texture", str(result.document))

    def test_currency_omits_runtime_limits_and_asset_path(self):
        result = convert_legacy("currencies", "templates/currencies/1/v0.1.0/template.json", {
            "name": "gold_pieces", "display_name": "Gold Pieces", "max_amount": 999, "tradeable": True, "icon_path": "gold.png",
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "Gold Pieces", "currency_code": "gold-pieces"})
        self.assertEqual(result.target_file, "templates/currencies/gold-pieces/v1.0.0/template.json")
        self.assertNotIn("max_amount", str(result.document))
        self.assertNotIn("icon_path", str(result.document))

    def test_name_family_omits_name_lists_and_epithets(self):
        result = convert_legacy("names", "templates/names/elfe/v0.1.0/template.json", {
            "display_name": "Elfes", "culture": "elfe", "models": {"first": {"names": ["Ael"]}}, "epithets": ["the Great"],
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "Elfes", "culture_tag": "elfe"})
        self.assertNotIn("epithets", str(result.document))

    def test_nonsemantic_sanitized_name_requires_manual_review(self):
        result = convert_legacy("names", "templates/names/names-template-0004/v0.1.0/template.json", {
            "display_name": "Unknown", "culture": "adapted_referenceien",
        }, set())
        self.assertEqual(result.disposition, "manual-review")
        self.assertIsNone(result.document)

    def test_schemas_are_closed_and_valid(self):
        for family in ("avatars", "biomes", "currencies", "names"):
            schema = family_schema(family)
            Draft202012Validator.check_schema(schema)
            self.assertFalse(schema["allOf"][1]["properties"]["spec"]["additionalProperties"])
