import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from scripts.cohort_six_contracts import convert_legacy, family_schema
from scripts.migrate_cohort_six import build_migration


class CohortSixTests(unittest.TestCase):
    def test_masterpiece_is_minimal(self):
        result=convert_legacy("masterpieces","templates/masterpieces/blade/v0.1.0/template.json",{"id":"blade","name":"Blade","profession":"Blacksmithing","difficulty":99,"special_materials":[1]},set()); self.assertEqual(result.document["spec"],{"display_name":"Blade","profession_tag":"blacksmithing"}); self.assertNotIn("difficulty",str(result.document))
    def test_narrative_and_runtime_are_not_migrated(self):
        self.assertEqual(convert_legacy("prologues","templates/prologues/storm/v0.1.0/template.json",{"id":"storm","title":"Storm","beats":[]},set()).disposition,"legacy-only-narrative")
        self.assertEqual(convert_legacy("virtues-factions","templates/virtues-factions/template/v0.1.0/template.json",{"id":"template"},set()).disposition,"legacy-only-authoritative")
    def test_schemas_closed(self):
        for family in ("masterpieces","skillclass"):
            schema=family_schema(family); Draft202012Validator.check_schema(schema); self.assertFalse(schema["allOf"][1]["properties"]["spec"]["additionalProperties"])
    def test_real_cohort(self):
        plan=build_migration(Path(".")); self.assertEqual(len(plan["results"]),15); self.assertEqual(plan["counts"],{"legacy-only-authoritative":2,"legacy-only-narrative":5,"migrated":8})
