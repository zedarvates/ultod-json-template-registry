import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_registry import (
    export_missing_templates,
    promote_exports,
    sanitize_catalogued_files,
    sanitize_existing_template,
    sanitize_template,
    template_slug,
)


class SemanticTemplateSanitizerTests(unittest.TestCase):
    def test_existing_schema_removes_blocked_properties_and_required_names(self):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "debug_mode"],
            "properties": {
                "id": {"type": "string"},
                "debug_mode": {"type": "boolean"},
                "admin_controls": {"type": "object"},
            },
        }

        sanitized = sanitize_existing_template(schema)

        self.assertEqual(sanitized["required"], ["id"])
        self.assertEqual(list(sanitized["properties"]), ["id"])
        self.assertEqual(sanitized["$schema"], schema["$schema"])

    def test_catalogued_file_sanitization_updates_only_changed_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            unsafe_path = root / "templates/spells/fireball/v0.1.0/template.json"
            safe_path = root / "templates/items/iron-ore/v0.1.0/template.json"
            unsafe_path.parent.mkdir(parents=True)
            safe_path.parent.mkdir(parents=True)
            unsafe_path.write_text(
                json.dumps({"id": "fireball", "base_stats": {"power": 10}, "admin_controls": {}}),
                encoding="utf-8",
            )
            safe_path.write_text(json.dumps({"id": "iron_ore"}), encoding="utf-8")
            catalog_path = root / "templates/catalog.json"
            entries = [
                {"file": unsafe_path.relative_to(root).as_posix(), "sha256": "old-unsafe"},
                {"file": safe_path.relative_to(root).as_posix(), "sha256": "old-safe"},
            ]
            catalog_path.write_text(json.dumps({"entries": entries}), encoding="utf-8")

            result = sanitize_catalogued_files(root, catalog_path)

            self.assertEqual(result, {"sanitized": 1})
            unsafe = json.loads(unsafe_path.read_text(encoding="utf-8"))
            self.assertEqual(unsafe["base_stats"], {"power": 10})
            self.assertNotIn("admin_controls", unsafe)
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))["entries"]
            self.assertEqual(catalog[1]["sha256"], "old-safe")
            self.assertEqual(catalog[0]["sha256"], hashlib.sha256(unsafe_path.read_bytes()).hexdigest())

    def test_monster_keeps_gameplay_contract_but_removes_privileged_controls(self):
        source = {
            "id": "aboleth",
            "name": "Aboleth",
            "description": "An ancient aquatic creature.",
            "category": "aberration",
            "rarity": "legendary",
            "base_stats": {"health": 10000, "mana": 5000},
            "properties": {"size": "medium", "speed": 6.0},
            "loot_table": {"rare_drops": ["aboleth_eye", "memory_pearl"]},
            "ai_behavior": {"attack_pattern": "tidal_assault"},
            "abilities": ["memory_wave"],
            "admin_controls": {"spawn_limit": 1, "requires_permission": True},
            "debug_mode": False,
            "version": "1.0.0",
        }

        sanitized = sanitize_template(source, family="monsters", sequence=1)

        self.assertEqual(sanitized["id"], "aberration_creature_0001")
        self.assertEqual(sanitized["name"], "Aberration Creature 0001")
        self.assertEqual(sanitized["template_type"], "monster")
        self.assertEqual(sanitized["version"], "0.1.0")
        self.assertEqual(sanitized["base_stats"], source["base_stats"])
        self.assertEqual(sanitized["properties"], source["properties"])
        self.assertEqual(
            sanitized["loot_table"],
            {"rare_drops": ["aberration_creature_0001_eye", "memory_pearl"]},
        )
        self.assertEqual(sanitized["ai_behavior"], source["ai_behavior"])
        self.assertEqual(sanitized["abilities"], source["abilities"])
        self.assertNotIn("admin_controls", sanitized)
        self.assertNotIn("debug_mode", sanitized)
        self.assertNotIn("aboleth", json.dumps(sanitized).lower())

    def test_monster_alias_replaces_distinctive_root_in_nested_references(self):
        source = {
            "id": "beholder_enhanced",
            "name": "Beholder Enhanced",
            "category": "aberration",
            "loot_table": {"rare_drops": ["beholder_eye", "beholder_artifact"]},
        }

        sanitized = sanitize_template(source, family="monsters", sequence=2)

        self.assertNotIn("beholder", json.dumps(sanitized).lower())
        self.assertEqual(
            sanitized["loot_table"]["rare_drops"],
            ["aberration_creature_0002_eye", "aberration_creature_0002_artifact"],
        )

    def test_safe_item_preserves_semantic_identity_and_useful_fields(self):
        source = {
            "id": "iron_ore",
            "name": "Iron Ore",
            "category": "material",
            "base_stats": {"weight": 0.8, "durability": 1},
            "properties": {"stackable": True},
            "shop_info": {"buy_price": 10, "stock_limit": 100},
            "value": {"base_sell_price": 4},
        }

        sanitized = sanitize_template(source, family="item", sequence=3)

        self.assertEqual(sanitized["id"], "iron_ore")
        self.assertEqual(sanitized["name"], "Iron Ore")
        self.assertEqual(sanitized["base_stats"], source["base_stats"])
        self.assertEqual(sanitized["properties"], source["properties"])
        self.assertNotIn("shop_info", sanitized)
        self.assertEqual(sanitized.get("value"), {})

    def test_removes_nested_admin_and_third_party_contract_sections(self):
        source = {
            "id": "safe_template",
            "one_piece_integration_systems": {"pirate_power": 10},
            "aion_class_details": {"slots": 4},
            "materials": {"mithril_steel": {"quality": 10}, "iron": {"quality": 2}},
            "tool_access": "admin_only",
            "admin_effect": "admin_command_echo",
        }

        sanitized = sanitize_template(source, family="skills", sequence=1)
        serialized = json.dumps(sanitized).lower()

        self.assertNotIn("one_piece", serialized)
        self.assertNotIn("aion", serialized)
        self.assertNotIn("mithril", serialized)
        self.assertNotIn("admin", serialized)
        self.assertEqual(sanitized["materials"], {"iron": {"quality": 2}})

    def test_root_array_becomes_named_catalog_without_losing_entries(self):
        source = [
            {"id": "set_guard", "name": "Guard Set", "bonuses": [{"defense": 10}]},
            {"id": "set_scout", "name": "Scout Set", "bonuses": [{"speed": 5}]},
        ]

        sanitized = sanitize_template(source, family="item", sequence=7)

        self.assertEqual(sanitized["id"], "item_catalog_0007")
        self.assertEqual(sanitized["name"], "Item Catalog 0007")
        self.assertEqual(sanitized["template_type"], "item_catalog")
        self.assertEqual(len(sanitized["entries"]), 2)
        self.assertEqual(sanitized["entries"][0]["bonuses"], [{"defense": 10}])

    def test_template_slug_is_readable_and_never_hash_named(self):
        self.assertEqual(template_slug("aberration_creature_0001"), "aberration-creature-0001")
        self.assertEqual(template_slug("Iron Ore"), "iron-ore")
        self.assertNotIn("original-", template_slug("Iron Ore"))


class SemanticExportTests(unittest.TestCase):
    def test_exports_missing_templates_with_readable_paths_and_useful_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "item").mkdir(parents=True)
            (source_root / "monsters").mkdir()
            item_content = b'{"id":"iron_ore","name":"Iron Ore","category":"material","base_stats":{"weight":0.8},"shop_info":{"buy_price":10}}'
            monster_content = b'{"id":"aboleth","name":"Aboleth","category":"aberration","base_stats":{"health":10000},"admin_controls":{"spawn_limit":1}}'
            (source_root / "item/iron_ore.json").write_bytes(item_content)
            (source_root / "monsters/aboleth.json").write_bytes(monster_content)

            manifest = export_missing_templates(source_root, staging_root, [])

            self.assertEqual([entry["name"] for entry in manifest["generated"]], [
                "iron-ore",
                "aberration-creature-0001",
            ])
            item_entry, monster_entry = manifest["generated"]
            item = json.loads((staging_root / item_entry["template_file"]).read_text(encoding="utf-8"))
            monster = json.loads((staging_root / monster_entry["template_file"]).read_text(encoding="utf-8"))
            self.assertEqual(item["base_stats"], {"weight": 0.8})
            self.assertNotIn("shop_info", item)
            self.assertEqual(monster["base_stats"], {"health": 10000})
            self.assertNotIn("admin_controls", monster)
            self.assertTrue(item_entry["expose_source_file"])
            self.assertFalse(monster_entry["expose_source_file"])
            self.assertFalse(any("original-" in entry["template_file"] for entry in manifest["generated"]))

    def test_collision_uses_readable_ordinal_suffix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "item").mkdir(parents=True)
            (source_root / "item/iron_ore.json").write_text(
                '{"id":"iron_ore","name":"Iron Ore"}',
                encoding="utf-8",
            )
            catalog_entries = [
                {"file": "templates/items/iron-ore/v0.1.0/template.json", "sha256": "0" * 64}
            ]

            manifest = export_missing_templates(source_root, staging_root, catalog_entries)

            self.assertEqual(manifest["generated"][0]["name"], "iron-ore-2")

    def test_promotion_catalogs_safe_paths_and_sensitive_aliases_differently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            registry_root = root / "registry"
            (source_root / "item").mkdir(parents=True)
            (source_root / "monsters").mkdir()
            item_content = b'{"id":"iron_ore","name":"Iron Ore"}'
            monster_content = b'{"id":"aboleth","name":"Aboleth","category":"aberration"}'
            (source_root / "item/iron_ore.json").write_bytes(item_content)
            (source_root / "monsters/aboleth.json").write_bytes(monster_content)
            manifest = export_missing_templates(source_root, staging_root, [])
            (staging_root / "export-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (registry_root / "templates").mkdir(parents=True)
            catalog_path = registry_root / "templates/catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")

            result = promote_exports(staging_root, registry_root, catalog_path)

            entries = json.loads(catalog_path.read_text(encoding="utf-8"))["entries"]
            self.assertEqual(result, {"promoted": 2})
            item_entry = next(entry for entry in entries if entry["name"] == "iron-ore")
            monster_entry = next(entry for entry in entries if entry["name"] == "aberration-creature-0001")
            self.assertEqual(item_entry["source_file"], "item/iron_ore.json")
            self.assertNotIn("source_sha256", item_entry)
            self.assertEqual(monster_entry["source_sha256"], hashlib.sha256(monster_content).hexdigest())
            self.assertNotIn("source_file", monster_entry)


if __name__ == "__main__":
    unittest.main()
