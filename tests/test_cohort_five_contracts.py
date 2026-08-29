import unittest
from jsonschema import Draft202012Validator
from scripts.cohort_five_contracts import convert_legacy, family_schema


class CohortFiveConversionTests(unittest.TestCase):
    def test_runtime_fields_are_omitted(self):
        boss=convert_legacy("bosses","templates/bosses/beast/v0.1.0/template.json",{"id":"beast","name":"Beast","base_hp":1000,"phases":[1]},set())
        creature=convert_legacy("creatures","templates/creatures/fae/v0.1.0/template.json",{"species_id":"fae","species_name":"Fae","chemistry":"Water Carbon","parts":[1],"loot_table":{}},set())
        self.assertEqual(boss.document["spec"],{"display_name":"Beast"})
        self.assertEqual(creature.document["spec"],{"display_name":"Fae","chemistry_tag":"water-carbon"})
        self.assertNotIn("loot_table",str(creature.document))

    def test_event_and_quest_keep_only_classification(self):
        event=convert_legacy("events","templates/events/crisis/v0.1.0/template.json",{"event_id":"crisis","event_name":"Crisis","event_type":"World Event","rarity":"Mythic","rewards":{}},set())
        quest=convert_legacy("quests","templates/quests/hunt/v0.1.0/template.json",{"id":1002,"name":"Hunt","difficulty":"Easy","objectives":[],"rewards":{}},set())
        self.assertEqual(event.document["spec"],{"display_name":"Crisis","event_kind":"world-event","rarity_tag":"mythic"})
        self.assertEqual(quest.document["spec"],{"display_name":"Hunt","difficulty_tag":"easy"})

    def test_technical_identity_requires_review(self):
        result=convert_legacy("rifts","templates/rifts/chaos/v0.1.0/template.json",{"rift_id":"chaos_rift_template","rift_name":"Chaos Rift"},set())
        self.assertEqual(result.disposition,"manual-review")

    def test_schemas_are_closed(self):
        for family in ("bosses","creatures","events","mount","quests","styles","tournaments"):
            schema=family_schema(family); Draft202012Validator.check_schema(schema); self.assertFalse(schema["allOf"][1]["properties"]["spec"]["additionalProperties"])
