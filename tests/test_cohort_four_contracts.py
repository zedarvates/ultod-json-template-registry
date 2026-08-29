import unittest

from jsonschema import Draft202012Validator

from scripts.cohort_four_contracts import convert_legacy, family_schema


class CohortFourConversionTests(unittest.TestCase):
    def test_npc_omits_runtime_behavior_and_dialogue(self):
        result = convert_legacy("npcs", "templates/npcs/alchemist/v0.1.0/template.json", {"id": "alchemist", "name": "Alchemist", "category": "Merchant", "rarity": "Uncommon", "npc_type": "Specialized Merchant", "base_stats": {"hp": 100}, "awareness": {"range": 10}, "dialogue": ["hello"]}, set())
        self.assertEqual(result.document["spec"], {"display_name": "Alchemist", "category_tag": "merchant", "rarity_tag": "uncommon", "npc_kind": "specialized-merchant"})
        self.assertNotIn("dialogue", str(result.document))

    def test_guild_and_relic_configs_remain_authoritative(self):
        guild = convert_legacy("guilds", "templates/guilds/ranks/v0.1.0/template.json", {"ranks": []}, set())
        factions = convert_legacy("guilds", "templates/guilds/factions/v0.1.0/template.json", [], set())
        relic = convert_legacy("gods", "templates/gods/relic/v0.1.0/template.json", {"relic_template": {}}, set())
        self.assertEqual(guild.disposition, "legacy-only-authoritative")
        self.assertEqual(factions.disposition, "legacy-only-authoritative")
        self.assertEqual(relic.disposition, "legacy-only-authoritative")

    def test_social_specs_keep_only_tags(self):
        god = convert_legacy("gods", "templates/gods/balance/v0.1.0/template.json", {"id": "balance_god", "name": "Themis", "domain": "Balance", "alignment": "Lawful Neutral", "divine_power": 99}, set())
        trait = convert_legacy("racial-traits", "templates/racial-traits/camo/v0.1.0/template.json", {"id": "camouflage", "name": "Camouflage", "category": "Stealth", "rarity": "Rare", "stat_modifiers": {"stealth": 1}}, set())
        self.assertEqual(god.document["spec"], {"display_name": "Themis", "domain_tag": "balance", "alignment_tag": "lawful-neutral"})
        self.assertEqual(trait.document["spec"], {"display_name": "Camouflage", "category_tag": "stealth", "rarity_tag": "rare"})

    def test_technical_identity_requires_manual_review(self):
        result = convert_legacy("npcs", "templates/npcs/town/v0.1.0/template.json", {"id": "town_guard_template", "name": "Town Guard Template"}, set())
        self.assertEqual(result.disposition, "manual-review")

    def test_schemas_are_closed_and_valid(self):
        for family in ("npcs", "gods", "sects", "lineages", "racial-traits"):
            schema = family_schema(family)
            Draft202012Validator.check_schema(schema)
            self.assertFalse(schema["allOf"][1]["properties"]["spec"]["additionalProperties"])
