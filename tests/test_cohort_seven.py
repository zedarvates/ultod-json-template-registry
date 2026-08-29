import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from scripts.cohort_seven_contracts import convert,schema
from scripts.migrate_cohort_seven import build
class Tests(unittest.TestCase):
    def test_recipe_minimal(self):
        r=convert("recipes","templates/recipes/sword/v0.1.0/template.json",{"id":"sword","name":"Sword","profession":"Blacksmithing","station_type":"Forge","ingredients":[1],"crafting_time_seconds":10},set());self.assertEqual(r.document["spec"],{"display_name":"Sword","profession_tag":"blacksmithing","station_kind":"forge"});self.assertNotIn("ingredients",str(r.document))
    def test_runtime_configs(self):
        self.assertEqual(convert("loot","templates/loot/template/v0.1.0/template.json",{"id":"template"},set()).disposition,"legacy-only-authoritative")
        self.assertEqual(convert("bulk-orders","templates/bulk-orders/system/v0.1.0/template.json",{"name":"System","global_settings":{}},set()).disposition,"legacy-only-authoritative")
    def test_schemas(self):
        for f in ("recipes","recipe","bulk-orders"):Draft202012Validator.check_schema(schema(f))
    def test_real(self):
        p=build(Path("."));self.assertEqual(len(p["results"]),16);self.assertEqual(p["counts"],{"legacy-only-authoritative":5,"migrated":11})
