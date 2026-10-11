import copy
import hashlib
import unittest
from pathlib import Path

from scripts.template_contract import (
    compute_spec_checksum, decode_json_bytes, validate_with_schema,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "templates/schemas/spells/v1.1.0/schema.json"


class TheDukePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = decode_json_bytes((ROOT / "templates/catalog.json").read_bytes())
        cls.entries = {f"{e['id']}@{e['version']}": e for e in catalog["entries"] if "id" in e}
        cls.egg = cls.document("items:the-duke-class-egg@1.0.0")
        cls.klass = cls.document("classes:the-duke@1.0.0")

    @classmethod
    def document(cls, ref):
        return decode_json_bytes((ROOT / cls.entries[ref]["file"]).read_bytes())

    def test_egg_bundle_resolves_to_class_spells_and_three_complete_talent_chains(self):
        refs = self.egg["dependencies"]
        self.assertEqual(len(refs), 56)
        self.assertEqual(len(set(refs)), 56)
        self.assertEqual([r for r in refs if r.startswith("classes:")], ["classes:the-duke@1.0.0"])
        spells = [r for r in refs if r.startswith("spells:")]
        self.assertEqual(set(refs) - {"classes:the-duke@1.0.0"}, set(self.klass["dependencies"]))
        self.assertEqual(len(spells), 19)
        self.assertEqual(sum(self.document(r)["spec"]["spell_kind"] == "passive" for r in spells), 4)
        for ref in spells:
            doc = self.document(ref)
            self.assertEqual(doc["spec"]["school"], "the-duke")
            self.assertEqual(doc["dependencies"], [])
        nodes = [self.document(r) for r in refs if r.startswith("skills:")]
        self.assertEqual(len(nodes), 36)
        for branch in ["action-hero", "explosives-expert", "ego-titan"]:
            chain = [d for d in nodes if d["spec"]["subcategory_tag"] == branch]
            self.assertEqual(len(chain), 12)
            members = {d["id"] + "@1.0.0" for d in chain}
            roots = []
            edges = {}
            for d in chain:
                predecessors = [r for r in d["dependencies"] if r.startswith("skills:")]
                self.assertEqual(len([r for r in d["dependencies"] if r.startswith("spells:")]), 1)
                for r in d["dependencies"]:
                    self.assertIn(r, self.entries)
                if not predecessors:
                    roots.append(d["id"] + "@1.0.0")
                else:
                    self.assertEqual(len(predecessors), 1)
                    self.assertIn(predecessors[0], members)
                    self.assertNotIn(predecessors[0], edges)
                    edges[predecessors[0]] = d["id"] + "@1.0.0"
            self.assertEqual(len(roots), 1)
            seen = set()
            current = roots[0]
            while current not in seen:
                seen.add(current)
                if current not in edges:
                    break
                current = edges[current]
            self.assertEqual(seen, members)

    def test_pack_checksums_schema_and_unverified_compatibility(self):
        for ref in ["items:the-duke-class-egg@1.0.0", *self.egg["dependencies"]]:
            entry = self.entries[ref]
            doc = self.document(ref)
            with self.subTest(ref=ref):
                content = (ROOT / entry["file"]).read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(entry["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(doc["spec_checksum"], compute_spec_checksum(doc["spec"]))
                self.assertEqual(doc["compatibility"], [])
                self.assertEqual(entry["compatibility"], [])
                self.assertEqual(entry["status"], "experimental")
                self.assertEqual(validate_with_schema(ROOT, entry["schema_file"], doc), [])

    def test_gadget_intents_are_explicit_and_no_authoritative_numbers_are_published(self):
        expectations = {
            "mighty-kick": "knockback", "pipe-bomb": "remote-detonation",
            "freezethrower": "freeze", "chaingun-cyclone": "channelled",
            "holo-duke": "aggro-decoy", "steroids": "grit-regeneration",
            "hail-to-the-king": "critical-window", "nuke-strike": "residual-burn",
            "balls-of-steel": "damage-reflection", "trash-talk-overdrive": "taunt",
            "royal-insult-protocol": "dispel", "ego-meltdown": "mental-resistance-debuff",
        }
        for slug, tag in expectations.items():
            self.assertIn(tag, self.document(f"spells:the-duke-{slug}@1.0.0")["spec"]["capability_tags"])

        def walk(value):
            if isinstance(value, dict):
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
            else:
                self.assertIsInstance(value, str)
        for ref in ["items:the-duke-class-egg@1.0.0", *self.egg["dependencies"]]:
            walk(self.document(ref)["spec"])

    def test_optional_capability_labels_preserve_existing_spell_contract(self):
        doc = self.document("spells:the-duke-mighty-kick@1.0.0")
        del doc["spec"]["capability_tags"]
        self.assertEqual(validate_with_schema(ROOT, SCHEMA, doc), [])
        previous = decode_json_bytes((ROOT / "templates/schemas/spells/v1.0.0/schema.json").read_bytes())
        current = decode_json_bytes((ROOT / SCHEMA).read_bytes())
        old_spec = previous["allOf"][1]["properties"]["spec"]
        new_spec = current["allOf"][1]["properties"]["spec"]
        self.assertEqual(old_spec["required"], new_spec["required"])
        self.assertFalse(new_spec["additionalProperties"])
        self.assertEqual(old_spec["properties"], {k: v for k, v in new_spec["properties"].items() if k != "capability_tags"})

    def test_capabilities_reject_duplicates_bad_types_unbounded_values_and_runtime_fields(self):
        base = self.document("spells:the-duke-mighty-kick@1.0.0")
        for tags in [[], ["melee", "melee"], [42], ["Upper_Case"], ["x" * 65], [f"tag-{i}" for i in range(17)]]:
            doc = copy.deepcopy(base)
            doc["spec"]["capability_tags"] = tags
            with self.subTest(tags=tags):
                self.assertTrue(validate_with_schema(ROOT, SCHEMA, doc))

    def test_class_roles_resources_and_new_schema_bounds(self):
        self.assertEqual(self.klass["spec"]["role_tags"], ["dps", "bruiser"])
        self.assertEqual(self.klass["spec"]["resource_kinds"], ["grit", "ammunition"])
        schema = "templates/schemas/classes/v1.1.0/schema.json"
        for field in ["resource_kinds", "role_tags", "specialization_tags"]:
            for value in [[], ["grit", "grit"], [True], ["not_valid"], ["x" * 65], [f"tag-{i}" for i in range(17)]]:
                doc = copy.deepcopy(self.klass)
                doc["spec"][field] = value
                with self.subTest(field=field, value=value):
                    self.assertTrue(validate_with_schema(ROOT, schema, doc))
        old = self.document("classes:gunslinger@1.0.0")
        self.assertEqual(validate_with_schema(ROOT, schema, old), [])
        for forbidden in ["damage", "cooldown", "mana_cost", "effects", "unknown_field"]:
            doc = copy.deepcopy(self.klass)
            doc["spec"][forbidden] = 100
            with self.subTest(field=forbidden):
                self.assertTrue(validate_with_schema(ROOT, schema, doc))
