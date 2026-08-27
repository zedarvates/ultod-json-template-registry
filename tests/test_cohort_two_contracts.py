import unittest

from jsonschema import Draft202012Validator

from scripts.cohort_two_contracts import convert_legacy, family_schema


class CohortTwoConversionTests(unittest.TestCase):
    def test_runtime_city_families_remain_authoritative_legacy(self):
        for family in ("cities", "city-layouts"):
            result = convert_legacy(family, f"templates/{family}/template/v0.1.0/template.json", {"name": "Template"}, set())
            self.assertEqual(result.disposition, "legacy-only-authoritative")
            self.assertIsNone(result.document)

    def test_dungeon_keeps_only_identity_and_theme(self):
        result = convert_legacy("dungeons", "templates/dungeons/crypt/v0.1.0/template.json", {
            "name": "The Crypt", "theme": "Shadow", "min_level": 10,
            "rewards": [{"gold": 100}], "levels": [{"tiles": [{"x": 1, "z": 2}]}],
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "The Crypt", "theme_tag": "shadow"})
        self.assertNotIn("rewards", str(result.document))
        self.assertNotIn("min_level", str(result.document))

    def test_location_keeps_only_classification(self):
        result = convert_legacy("locations", "templates/locations/nexus/v0.1.0/template.json", {
            "location_id": "temporal_nexus", "name": "Temporal Nexus", "location_type": "Dungeon",
            "size": "Large", "rarity": "Epic", "coordinates": {"x": 1}, "entry_mechanics": {"cooldown": 10},
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "Temporal Nexus", "location_kind": "dungeon", "size_tag": "large", "rarity_tag": "epic"})
        self.assertNotIn("coordinates", str(result.document))

    def test_planet_keeps_only_type_tags(self):
        result = convert_legacy("planets", "templates/planets/seladris/0.1.0/template.json", {
            "name": "Seladris", "planet_types": {"primary": "Ocean", "secondary": "Archipelago"},
            "planetary_generation": {"gravity_modifier": 0.95},
        }, set())
        self.assertEqual(result.document["spec"], {"display_name": "Seladris", "primary_type_tag": "ocean", "secondary_type_tag": "archipelago"})
        self.assertEqual(result.document["intended_consumers"], ["llm-pipeline"])

    def test_fixture_identity_requires_manual_review(self):
        result = convert_legacy("dungeons", "templates/dungeons/demo-crypt/v0.1.0/template.json", {"name": "Demo Crypt"}, set())
        self.assertEqual(result.disposition, "manual-review")
        self.assertIsNone(result.document)

    def test_schemas_are_closed_and_valid(self):
        for family in ("dungeons", "locations", "planets", "solar-systems"):
            schema = family_schema(family)
            Draft202012Validator.check_schema(schema)
            self.assertFalse(schema["allOf"][1]["properties"]["spec"]["additionalProperties"])
