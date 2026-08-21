import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_registry import (
    adapt_item_document,
    adapt_manual_item_source,
    adapt_monster_document,
    adapt_spell_document,
    adapt_generic_document,
    build_monster_drafts,
    build_item_drafts,
    build_spell_drafts,
    build_generic_drafts,
    build_inventory,
    classify_document,
    discover_sources,
    main,
    promote_item_drafts,
    promote_monster_drafts,
    promote_spell_drafts,
    promote_generic_drafts,
    remove_legacy_spell_entries,
    remove_catalog_files,
    summarize_families,
    update_audit_coverage,
)


class DiscoverSourcesTests(unittest.TestCase):
    def test_excludes_history_and_returns_sorted_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "items").mkdir()
            (root / "abilities").mkdir()
            (root / "_versions" / "item" / "old").mkdir(parents=True)
            (root / "items" / "zeta.json").write_text("{}", encoding="utf-8")
            (root / "abilities" / "alpha.json").write_text("{}", encoding="utf-8")
            (root / "_versions" / "item" / "old" / "1.json").write_text("{}", encoding="utf-8")

            paths = discover_sources(root)

            self.assertEqual(
                [path.relative_to(root).as_posix() for path in paths],
                ["abilities/alpha.json", "items/zeta.json"],
            )


class ClassificationTests(unittest.TestCase):
    def test_marks_admin_and_shop_fields_for_adaptation(self):
        document = {
            "id": "sample",
            "admin_controls": {"enabled": True},
            "shop_info": {"buy_price": 10},
        }

        result = classify_document(document, json.dumps(document))

        self.assertEqual(result["disposition"], "adaptation-required")
        self.assertEqual(result["signals"], ["admin-control", "commercial"])

    def test_excludes_secrets_internal_endpoints_and_third_party_references(self):
        document = {
            "api_token": "not-a-real-secret",
            "server_url": "http://internal-host:8080",
            "inspiration": "Warcraft",
        }

        result = classify_document(document, json.dumps(document))

        self.assertEqual(result["disposition"], "excluded")
        self.assertEqual(result["signals"], ["internal", "rights", "secret"])

    def test_accepts_portable_declarative_template_as_snapshot_candidate(self):
        document = {
            "id": "portable_sample",
            "template_type": "item",
            "version": "0.1.0",
            "weight_kg": 0.5,
        }

        result = classify_document(document, json.dumps(document))

        self.assertEqual(result, {"disposition": "snapshot-candidate", "signals": []})

    def test_excludes_known_mixed_rights_source_families_by_path(self):
        for source_path in (
            "ability/fireball.json",
            "bods/blacksmith_order.json",
            "champions/vermin.json",
            "skillclass/warrior.json",
            "talent/tree.json",
        ):
            with self.subTest(source_path=source_path):
                result = classify_document({"id": "generic"}, '{"id":"generic"}', source_path)
                self.assertEqual(result, {"disposition": "excluded", "signals": ["rights"]})

    def test_excludes_known_third_party_terms_missed_by_initial_inventory(self):
        for identifier in (
            "xenomorph",
            "mithril_vein",
            "blizzard",
            "peacebloom",
            "silverleaf",
            "sweet_roll",
            "arcane_dust",
            "recall_stone_basic",
        ):
            with self.subTest(identifier=identifier):
                document = {"id": identifier}
                result = classify_document(document, json.dumps(document))
                self.assertEqual(result, {"disposition": "excluded", "signals": ["rights"]})

    def test_requires_adaptation_for_uncovered_internal_or_mixed_source_families(self):
        for source_path in (
            "ai/guard_basic.json",
            "blueprints/havre_du_roi__npc_house_0.json",
            "city_layouts/havre_du_roi.json",
            "cosmetic/wings_of_fire.json",
            "item/generic.json",
            "loot/defaults.json",
            "planets/terre.json",
            "professions/cooking.json",
            "rts/units.json",
        ):
            with self.subTest(source_path=source_path):
                result = classify_document({"id": "generic"}, '{"id":"generic"}', source_path)
                self.assertEqual(
                    result,
                    {"disposition": "adaptation-required", "signals": ["family-policy"]},
                )

    def test_excludes_uncovered_families_with_documented_rights_or_cultural_risk(self):
        for source_path in (
            "abilities/fireball.json",
            "bulk_orders/order.json",
            "class/warrior.json",
            "divine_system/ritual.json",
            "names/fantasy.json",
            "race/elf.json",
            "recipe/healing_potion.json",
            "tournaments/arena.json",
            "treasure_maps/tier_5.json",
            "virtues_factions/honor.json",
        ):
            with self.subTest(source_path=source_path):
                result = classify_document({"id": "generic"}, '{"id":"generic"}', source_path)
                self.assertEqual(
                    result,
                    {"disposition": "excluded", "signals": ["policy-exclusion"]},
                )


class InventoryTests(unittest.TestCase):
    def test_summarizes_family_coverage_from_real_record_dispositions(self):
        inventory = {
            "records": [
                {"path": "abilities/a.json", "disposition": "covered"},
                {"path": "abilities/b.json", "disposition": "adapted"},
                {"path": "items/a.json", "disposition": "adaptation-required"},
            ]
        }

        families = summarize_families(inventory)

        self.assertEqual(
            families,
            [
                {
                    "family": "abilities",
                    "audit_state": "complete",
                    "source_current_count": 2,
                    "snapshot_covered_count": 1,
                    "adaptation_covered_count": 1,
                    "remaining_count": 0,
                    "invalid_count": 0,
                },
                {
                    "family": "items",
                    "audit_state": "pending",
                    "source_current_count": 1,
                    "snapshot_covered_count": 0,
                    "adaptation_covered_count": 0,
                    "remaining_count": 1,
                    "invalid_count": 0,
                },
            ],
        )

    def test_updates_machine_readable_audit_without_dropping_security_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / "audit.json"
            audit_path.write_text(
                json.dumps(
                    {
                        "format_version": 1,
                        "scope": "public aggregate",
                        "gitleaks": {"public_registry": "historical-clean"},
                        "families": [],
                    }
                ),
                encoding="utf-8",
            )
            inventory = {
                "summary": {
                    "source_count": 2,
                    "covered": 1,
                    "adapted": 1,
                    "invalid": 0,
                    "snapshot_candidates": 0,
                    "adaptation_required": 0,
                    "excluded": 0,
                },
                "records": [
                    {"path": "abilities/a.json", "disposition": "covered"},
                    {"path": "abilities/b.json", "disposition": "adapted"},
                ],
            }

            update_audit_coverage(audit_path, inventory, catalog_count=3)

            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(audit["format_version"], 2)
            self.assertEqual(audit["catalog_entry_count"], 3)
            self.assertEqual(audit["server_current_total_accounted"], 2)
            self.assertEqual(audit["server_current_remaining"], 0)
            self.assertEqual(audit["families"][0]["audit_state"], "complete")
            self.assertEqual(audit["gitleaks"], {"public_registry": "historical-clean"})

    def test_reports_covered_invalid_and_uncovered_sources_deterministically(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "items").mkdir()
            covered_content = b'{"id":"covered","template_type":"item","version":"0.1.0"}\n'
            (root / "items" / "covered.json").write_bytes(covered_content)
            (root / "items" / "needs_adaptation.json").write_text(
                '{"id":"priced","shop_info":{"buy_price":2}}',
                encoding="utf-8",
            )
            (root / "items" / "invalid.json").write_text("{", encoding="utf-8")
            catalog_entries = [{"sha256": hashlib.sha256(covered_content).hexdigest()}]

            inventory = build_inventory(root, catalog_entries)

            self.assertEqual(
                inventory["summary"],
                {
                    "source_count": 3,
                    "covered": 1,
                    "adapted": 0,
                    "invalid": 1,
                    "snapshot_candidates": 0,
                    "adaptation_required": 1,
                    "excluded": 0,
                },
            )
            self.assertEqual(
                [record["path"] for record in inventory["records"]],
                ["items/covered.json", "items/invalid.json", "items/needs_adaptation.json"],
            )
            self.assertEqual(inventory["records"][0]["disposition"], "covered")
            self.assertEqual(inventory["records"][1]["disposition"], "invalid")
            self.assertEqual(inventory["records"][2]["signals"], ["commercial"])


class ItemAdapterTests(unittest.TestCase):
    def test_manual_adapter_originalizes_operational_token(self):
        adapted = adapt_manual_item_source({}, "item/balance_override_token.json")

        self.assertEqual(adapted["id"], "calibration_marker")
        self.assertEqual(adapted["template_type"], "item")
        self.assertEqual(adapted["category"], "material")
        self.assertNotIn("effects", adapted)

    def test_manual_adapter_replaces_commercial_mount_token(self):
        adapted = adapt_manual_item_source({}, "item/cosmetic_frost_mount_token_item.json")

        self.assertEqual(adapted["id"], "winter_mount_ornament")
        self.assertEqual(adapted["category"], "cosmetic")
        self.assertNotIn("shop_info", adapted)

    def test_manual_adapter_converts_legacy_arrays_to_statless_catalogs(self):
        sets = adapt_manual_item_source([], "item/sets.json")
        wings = adapt_manual_item_source([], "item/wings.json")

        self.assertEqual(sets["template_type"], "item_set_catalog")
        self.assertEqual(
            sets["sets"],
            [
                {"id": "iron_guard_set", "name": "Iron Guard Set"},
                {"id": "aether_weaver_set", "name": "Aether Weaver Set"},
            ],
        )
        self.assertEqual(wings["template_type"], "cosmetic_style_catalog")
        self.assertEqual(
            [style["id"] for style in wings["styles"]],
            ["luminous_feather", "ember_membrane", "ancient_scale"],
        )

    def test_accepts_legacy_item_id_without_copying_legacy_contract(self):
        adapted = adapt_item_document(
            {
                "item_id": "balance_rune",
                "category": "material",
                "rarity": "uncommon",
                "weight": 0.8,
                "admin_controls": {"enabled": True},
            },
            "item/balance_rune.json",
        )

        self.assertEqual(adapted["id"], "balance_rune")
        self.assertEqual(adapted["name"], "Balance Rune")
        self.assertEqual(adapted["weight_kg"], 0.1)
        self.assertNotIn("admin_controls", adapted)

    def test_rejects_non_object_item_source_for_manual_review(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            adapt_item_document([], "item/sets.json")

    def test_builds_portable_item_without_copying_commercial_or_runtime_fields(self):
        source = {
            "id": "copper_gear",
            "name": "Internal Copper Gear",
            "description": "Production-only description",
            "icon": "private/gear.png",
            "category": "material",
            "rarity": "common",
            "base_stats": {"weight": 0.4, "value": 99},
            "effects": [{"type": "grant_gold", "amount": 100}],
            "shop_info": {"buy_price": 200, "stock": 5},
            "admin_controls": {"enabled": True},
        }

        adapted = adapt_item_document(source, "item/copper_gear.json")

        self.assertEqual(
            adapted,
            {
                "id": "copper_gear",
                "template_type": "item",
                "version": "0.1.0",
                "name": "Copper Gear",
                "description": "A portable material component for public template workflows.",
                "category": "material",
                "rarity": "common",
                "stack_limit": 50,
                "weight_kg": 0.4,
                "tags": ["adapted", "material"],
                "dependencies": [],
            },
        )

    def test_rejects_operational_or_commercial_identifiers_for_manual_review(self):
        for identifier in ("premium_starter_bundle", "balance_override_token", "admin_spawn_kit"):
            with self.subTest(identifier=identifier):
                with self.assertRaisesRegex(ValueError, "manual review"):
                    adapt_item_document(
                        {"id": identifier, "category": "material", "rarity": "common"},
                        f"item/{identifier}.json",
                    )

    def test_builds_versioned_item_drafts_and_records_manual_rejections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "item").mkdir(parents=True)
            (source_root / "item" / "copper_gear.json").write_text(
                '{"id":"copper_gear","category":"material","rarity":"common",'
                '"base_stats":{"weight":0.4},"shop_info":{"buy_price":2}}',
                encoding="utf-8",
            )
            (source_root / "item" / "premium_starter_bundle.json").write_text(
                '{"id":"premium_starter_bundle","category":"material"}',
                encoding="utf-8",
            )
            (source_root / "item" / "balance_override_token.json").write_text(
                '{"item_id":"balance_override_token","admin_controls":{"enabled":true}}',
                encoding="utf-8",
            )
            inventory = {
                "records": [
                    {"path": "item/copper_gear.json", "disposition": "adaptation-required"},
                    {"path": "item/premium_starter_bundle.json", "disposition": "adaptation-required"},
                    {"path": "item/balance_override_token.json", "disposition": "adaptation-required"},
                ]
            }

            batch = build_item_drafts(source_root, staging_root, inventory)

            self.assertEqual(
                batch["generated"],
                [
                    {
                        "source_file": "item/balance_override_token.json",
                        "name": "calibration-marker",
                        "template_file": "templates/items/calibration-marker/v0.1.0/template.json",
                    },
                    {
                        "source_file": "item/copper_gear.json",
                        "name": "copper-gear",
                        "template_file": "templates/items/copper-gear/v0.1.0/template.json",
                    }
                ],
            )
            self.assertEqual(
                [entry["source_file"] for entry in batch["rejected"]],
                ["item/premium_starter_bundle.json"],
            )
            template_path = staging_root / "templates/items/copper-gear/v0.1.0/template.json"
            readme_path = staging_root / "templates/items/copper-gear/v0.1.0/README.md"
            self.assertEqual(json.loads(template_path.read_text(encoding="utf-8"))["id"], "copper_gear")
            self.assertTrue(readme_path.exists())
            self.assertFalse((staging_root / "templates/items/premium-starter-bundle").exists())

    def test_refuses_to_overwrite_existing_staged_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "item").mkdir(parents=True)
            (source_root / "item" / "copper_gear.json").write_text(
                '{"id":"copper_gear","category":"material"}',
                encoding="utf-8",
            )
            existing = staging_root / "templates/items/copper-gear/v0.1.0"
            existing.mkdir(parents=True)
            (existing / "template.json").write_text("{}", encoding="utf-8")
            inventory = {
                "records": [
                    {"path": "item/copper_gear.json", "disposition": "adaptation-required"}
                ]
            }

            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                build_item_drafts(source_root, staging_root, inventory)


class ItemPromotionTests(unittest.TestCase):
    def test_promotes_staged_item_and_appends_integrity_catalog_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            registry_root = root / "registry"
            (source_root / "item").mkdir(parents=True)
            (source_root / "item" / "copper_gear.json").write_text(
                '{"id":"copper_gear","category":"material","shop_info":{"buy_price":2}}',
                encoding="utf-8",
            )
            inventory = {
                "records": [
                    {"path": "item/copper_gear.json", "disposition": "adaptation-required"}
                ]
            }
            batch = build_item_drafts(source_root, staging_root, inventory)
            (staging_root / "item-adaptation-manifest.json").write_text(
                json.dumps(batch),
                encoding="utf-8",
            )
            (registry_root / "templates").mkdir(parents=True)
            catalog_path = registry_root / "templates/catalog.json"
            catalog_path.write_text(
                '{"registry_version":"1.0.0","generated_at":"2026-08-20","entries":[]}',
                encoding="utf-8",
            )

            result = promote_item_drafts(staging_root, registry_root, catalog_path)

            promoted_path = registry_root / "templates/items/copper-gear/v0.1.0/template.json"
            content = promoted_path.read_bytes()
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.assertEqual(result, {"promoted": 1})
            self.assertEqual(len(catalog["entries"]), 1)
            self.assertEqual(
                catalog["entries"][0],
                {
                    "name": "copper-gear",
                    "kind": "item-template",
                    "version": "0.1.0",
                    "status": "experimental",
                    "file": "templates/items/copper-gear/v0.1.0/template.json",
                    "source_file": "item/copper_gear.json",
                    "provenance": "public-safe-original-adaptation",
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "compatibility": [],
                },
            )

    def test_preflight_collision_prevents_partial_promotion_and_catalog_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            staging_root = root / "staging"
            registry_root = root / "registry"
            for name in ("alpha", "beta"):
                version_dir = staging_root / f"templates/items/{name}/v0.1.0"
                version_dir.mkdir(parents=True)
                (version_dir / "template.json").write_text(
                    json.dumps({"id": name, "template_type": "item", "version": "0.1.0"}),
                    encoding="utf-8",
                )
                (version_dir / "README.md").write_text(f"# {name}\n", encoding="utf-8")
            manifest = {
                "generated": [
                    {
                        "source_file": "item/alpha.json",
                        "name": "alpha",
                        "template_file": "templates/items/alpha/v0.1.0/template.json",
                    },
                    {
                        "source_file": "item/beta.json",
                        "name": "beta",
                        "template_file": "templates/items/beta/v0.1.0/template.json",
                    },
                ],
                "rejected": [],
            }
            (staging_root / "item-adaptation-manifest.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            existing = registry_root / "templates/items/beta/v0.1.0"
            existing.mkdir(parents=True)
            (existing / "template.json").write_text("{}", encoding="utf-8")
            catalog_path = registry_root / "templates/catalog.json"
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            original_catalog = '{"entries":[]}'
            catalog_path.write_text(original_catalog, encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "promotion collision"):
                promote_item_drafts(staging_root, registry_root, catalog_path)

            self.assertFalse((registry_root / "templates/items/alpha").exists())
            self.assertEqual(catalog_path.read_text(encoding="utf-8"), original_catalog)


class MonsterAdapterTests(unittest.TestCase):
    def test_stages_rights_excluded_monster_as_fully_originalized_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "monsters").mkdir(parents=True)
            content = b'{"id":"uo_dragon","category":"dragon","admin_controls":{}}'
            (source_root / "monsters" / "uo_dragon.json").write_bytes(content)
            inventory = {
                "records": [
                    {"path": "monsters/uo_dragon.json", "disposition": "excluded"}
                ]
            }

            batch = build_monster_drafts(source_root, staging_root, inventory)

            self.assertEqual(len(batch["generated"]), 1)
            template = json.loads(
                (staging_root / batch["generated"][0]["template_file"]).read_text(encoding="utf-8")
            )
            self.assertNotIn("uo", json.dumps(template).lower())
            self.assertNotIn("uo_dragon", template["id"])

    def test_generates_original_deterministic_identity_without_source_name_or_contract(self):
        source_content = b'{"id":"beholder"}'
        source = {
            "id": "beholder",
            "name": "Beholder",
            "description": "Third-party creature description",
            "category": "aberration",
            "rarity": "legendary",
            "base_stats": {"health": 10000},
            "loot_table": {"epic_drops": ["eye"]},
            "ai_behavior": {"attack_pattern": "eye_ray"},
            "admin_controls": {"spawn_limit": 1},
        }

        adapted = adapt_monster_document(source, source_content)

        self.assertEqual(
            adapted,
            {
                "id": "original_aberration_42042307c9",
                "template_type": "monster",
                "version": "0.1.0",
                "name": "Original Aberration 420423",
                "description": "An original aberration creature identity for public template workflows.",
                "category": "aberration",
                "rarity": "legendary",
                "tags": ["adapted", "aberration", "original"],
                "dependencies": [],
            },
        )
        serialized = json.dumps(adapted).lower()
        self.assertNotIn("beholder", serialized)
        self.assertNotIn("health", serialized)
        self.assertNotIn("loot", serialized)

    def test_normalizes_unsafe_category_and_rarity(self):
        adapted = adapt_monster_document(
            {"category": "../../internal", "rarity": "admin"},
            b"unsafe-category",
        )

        self.assertEqual(adapted["category"], "creature")
        self.assertEqual(adapted["rarity"], "common")

    def test_stages_original_monster_without_exposing_private_path_in_public_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "monsters").mkdir(parents=True)
            content = b'{"id":"beholder","name":"Beholder","category":"aberration","rarity":"legendary","admin_controls":{}}'
            (source_root / "monsters" / "beholder.json").write_bytes(content)
            inventory = {
                "records": [
                    {"path": "monsters/beholder.json", "disposition": "adaptation-required"}
                ]
            }

            batch = build_monster_drafts(source_root, staging_root, inventory)

            self.assertEqual(len(batch["generated"]), 1)
            entry = batch["generated"][0]
            self.assertEqual(entry["source_sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(entry["name"], "original-aberration-e5d90cbdd7")
            template_path = staging_root / entry["template_file"]
            readme = template_path.with_name("README.md").read_text(encoding="utf-8").lower()
            self.assertNotIn("beholder", readme)
            self.assertNotIn("monsters/beholder.json", readme)


class MonsterPromotionTests(unittest.TestCase):
    def test_promotes_monster_with_private_source_hash_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            registry_root = root / "registry"
            (source_root / "monsters").mkdir(parents=True)
            content = b'{"id":"beholder","category":"aberration","admin_controls":{}}'
            (source_root / "monsters" / "beholder.json").write_bytes(content)
            inventory = {
                "records": [
                    {"path": "monsters/beholder.json", "disposition": "adaptation-required"}
                ]
            }
            batch = build_monster_drafts(source_root, staging_root, inventory)
            (staging_root / "monster-adaptation-manifest.json").write_text(
                json.dumps(batch),
                encoding="utf-8",
            )
            (registry_root / "templates").mkdir(parents=True)
            catalog_path = registry_root / "templates/catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")

            result = promote_monster_drafts(staging_root, registry_root, catalog_path)

            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            entry = catalog["entries"][0]
            self.assertEqual(result, {"promoted": 1})
            self.assertEqual(entry["kind"], "monster-template")
            self.assertEqual(entry["source_sha256"], hashlib.sha256(content).hexdigest())
            self.assertNotIn("source_file", entry)
            self.assertNotIn("beholder", json.dumps(entry).lower())


class SpellAdapterTests(unittest.TestCase):
    def test_generates_original_spell_without_source_identity_or_effects(self):
        content = b'{"id":"fireball"}'
        source = {
            "id": "fireball",
            "name": "Fireball",
            "description": "Known spell description",
            "damage": 100,
            "effects": [{"type": "burn"}],
            "admin_controls": {"enabled": True},
        }

        adapted = adapt_spell_document(source, content)

        self.assertEqual(
            adapted,
            {
                "id": "original_spell_65ed665052",
                "template_type": "spell",
                "version": "0.1.0",
                "name": "Original Spell 65ED66",
                "description": "An original statless spell identity for public template workflows.",
                "tags": ["adapted", "original", "spell"],
                "dependencies": [],
            },
        )
        serialized = json.dumps(adapted).lower()
        self.assertNotIn("fireball", serialized)
        self.assertNotIn("damage", serialized)
        self.assertNotIn("burn", serialized)

    def test_staging_deduplicates_identical_spell_sources_by_private_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "content_pipeline/spells").mkdir(parents=True)
            (source_root / "spells").mkdir()
            content = b'{"id":"fireball","admin_controls":{}}'
            (source_root / "content_pipeline/spells/fireball.json").write_bytes(content)
            (source_root / "spells/fireball.json").write_bytes(content)
            inventory = {
                "records": [
                    {
                        "path": "content_pipeline/spells/fireball.json",
                        "disposition": "adaptation-required",
                    },
                    {"path": "spells/fireball.json", "disposition": "excluded"},
                ]
            }

            batch = build_spell_drafts(source_root, staging_root, inventory)

            self.assertEqual(len(batch["generated"]), 1)
            self.assertEqual(len(batch["deduplicated"]), 1)
            self.assertEqual(batch["generated"][0]["source_sha256"], hashlib.sha256(content).hexdigest())
            template_path = staging_root / batch["generated"][0]["template_file"]
            self.assertNotIn("fireball", template_path.read_text(encoding="utf-8").lower())


class SpellPromotionTests(unittest.TestCase):
    def test_promotes_spell_with_source_fingerprint_and_no_source_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            registry_root = root / "registry"
            (source_root / "spells").mkdir(parents=True)
            content = b'{"id":"fireball","admin_controls":{}}'
            (source_root / "spells/fireball.json").write_bytes(content)
            inventory = {
                "records": [
                    {"path": "spells/fireball.json", "disposition": "adaptation-required"}
                ]
            }
            batch = build_spell_drafts(source_root, staging_root, inventory)
            (staging_root / "spell-adaptation-manifest.json").write_text(
                json.dumps(batch),
                encoding="utf-8",
            )
            (registry_root / "templates").mkdir(parents=True)
            catalog_path = registry_root / "templates/catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")

            result = promote_spell_drafts(staging_root, registry_root, catalog_path)

            entry = json.loads(catalog_path.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(result, {"promoted": 1})
            self.assertEqual(entry["kind"], "spell-template")
            self.assertEqual(entry["source_sha256"], hashlib.sha256(content).hexdigest())
            self.assertNotIn("source_file", entry)
            self.assertNotIn("fireball", json.dumps(entry).lower())

    def test_removes_unsafe_legacy_spell_entries_and_keeps_unrelated_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "templates/catalog.json"
            catalog_path.parent.mkdir(parents=True)
            entries = []
            for name in ("alpha", "beta", "gamma"):
                version_dir = root / f"templates/spells/{name}/0.1.0"
                version_dir.mkdir(parents=True)
                (version_dir / "template.json").write_text("{}", encoding="utf-8")
                entries.append(
                    {
                        "name": name,
                        "kind": "spell-template",
                        "version": "0.1.0",
                        "file": f"templates/spells/{name}/0.1.0/template.json",
                    }
                )
            catalog_path.write_text(json.dumps({"entries": entries}), encoding="utf-8")

            result = remove_legacy_spell_entries(root, catalog_path, {"alpha", "beta"})

            self.assertEqual(result, {"removed": 2})
            self.assertFalse((root / "templates/spells/alpha").exists())
            self.assertFalse((root / "templates/spells/beta").exists())
            self.assertTrue((root / "templates/spells/gamma").exists())
            remaining = json.loads(catalog_path.read_text(encoding="utf-8"))["entries"]
            self.assertEqual([entry["name"] for entry in remaining], ["gamma"])

    def test_legacy_removal_preflight_preserves_everything_when_directory_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "templates/catalog.json"
            catalog_path.parent.mkdir(parents=True)
            version_dir = root / "templates/spells/alpha/0.1.0"
            version_dir.mkdir(parents=True)
            (version_dir / "template.json").write_text("{}", encoding="utf-8")
            original = json.dumps(
                {
                    "entries": [
                        {
                            "name": "alpha",
                            "kind": "spell-template",
                            "version": "0.1.0",
                            "file": "templates/spells/alpha/0.1.0/template.json",
                        },
                        {
                            "name": "missing",
                            "kind": "spell-template",
                            "version": "0.1.0",
                            "file": "templates/spells/missing/0.1.0/template.json",
                        },
                    ]
                }
            )
            catalog_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(FileNotFoundError, "legacy spell directory missing"):
                remove_legacy_spell_entries(root, catalog_path, {"alpha", "missing"})

            self.assertTrue((root / "templates/spells/alpha").exists())
            self.assertEqual(catalog_path.read_text(encoding="utf-8"), original)


class GenericAdapterTests(unittest.TestCase):
    def test_neutralizes_commercial_source_family(self):
        adapted = adapt_generic_document({}, b"commercial-source", "vendor_shops")

        self.assertEqual(adapted["source_family"], "content")
        self.assertTrue(adapted["id"].startswith("original_content_"))
        self.assertNotIn("shop", json.dumps(adapted).lower())

    def test_generates_original_family_identity_without_source_content(self):
        content = b'{"id":"private"}'
        adapted = adapt_generic_document(
            {
                "id": "private",
                "name": "Private Name",
                "description": "Sensitive narrative",
                "admin_controls": {"enabled": True},
            },
            content,
            "class",
        )

        self.assertEqual(
            adapted,
            {
                "id": "original_class_baff6ecfdf",
                "template_type": "public_identity",
                "version": "0.1.0",
                "name": "Original Class BAFF6E",
                "description": "An original statless class identity for public template workflows.",
                "source_family": "class",
                "tags": ["adapted", "class", "original"],
                "dependencies": [],
            },
        )
        serialized = json.dumps(adapted).lower()
        self.assertNotIn("private name", serialized)
        self.assertNotIn("sensitive narrative", serialized)
        self.assertNotIn("admin_controls", serialized)

    def test_generic_staging_deduplicates_identical_remaining_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            (source_root / "class").mkdir(parents=True)
            (source_root / "race").mkdir()
            content = b'{"id":"private","admin_controls":{}}'
            (source_root / "class/private.json").write_bytes(content)
            (source_root / "race/private.json").write_bytes(content)
            inventory = {
                "records": [
                    {"path": "class/private.json", "disposition": "excluded"},
                    {"path": "race/private.json", "disposition": "excluded"},
                ]
            }

            batch = build_generic_drafts(source_root, staging_root, inventory)

            self.assertEqual(len(batch["generated"]), 1)
            self.assertEqual(len(batch["deduplicated"]), 1)
            self.assertEqual(batch["generated"][0]["source_sha256"], hashlib.sha256(content).hexdigest())
            self.assertTrue((staging_root / batch["generated"][0]["template_file"]).exists())


class GenericPromotionTests(unittest.TestCase):
    def test_removes_arbitrary_unsafe_catalog_files_transactionally(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "templates/catalog.json"
            catalog_path.parent.mkdir(parents=True)
            unsafe_file = "templates/classes/legacy/0.1.0/template.json"
            safe_file = "templates/classes/safe/0.1.0/template.json"
            for file_path in (unsafe_file, safe_file):
                path = root / file_path
                path.parent.mkdir(parents=True)
                path.write_text("{}", encoding="utf-8")
            catalog_path.write_text(
                json.dumps(
                    {
                        "entries": [
                            {"name": "legacy", "kind": "class-template", "file": unsafe_file},
                            {"name": "safe", "kind": "class-template", "file": safe_file},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = remove_catalog_files(root, catalog_path, {unsafe_file})

            self.assertEqual(result, {"removed": 1})
            self.assertFalse((root / unsafe_file).exists())
            self.assertTrue((root / safe_file).exists())
            entries = json.loads(catalog_path.read_text(encoding="utf-8"))["entries"]
            self.assertEqual([entry["name"] for entry in entries], ["safe"])

    def test_arbitrary_removal_missing_file_fails_before_any_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "templates/catalog.json"
            catalog_path.parent.mkdir(parents=True)
            existing_file = "templates/classes/existing/0.1.0/template.json"
            missing_file = "templates/classes/missing/0.1.0/template.json"
            path = root / existing_file
            path.parent.mkdir(parents=True)
            path.write_text("{}", encoding="utf-8")
            original = json.dumps(
                {
                    "entries": [
                        {"name": "existing", "file": existing_file},
                        {"name": "missing", "file": missing_file},
                    ]
                }
            )
            catalog_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(FileNotFoundError, "catalog file missing"):
                remove_catalog_files(root, catalog_path, {existing_file, missing_file})

            self.assertTrue(path.exists())
            self.assertEqual(catalog_path.read_text(encoding="utf-8"), original)

    def test_promotes_generic_identity_without_source_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            staging_root = root / "staging"
            registry_root = root / "registry"
            (source_root / "class").mkdir(parents=True)
            content = b'{"id":"private","admin_controls":{}}'
            (source_root / "class/private.json").write_bytes(content)
            inventory = {
                "records": [
                    {"path": "class/private.json", "disposition": "excluded"}
                ]
            }
            batch = build_generic_drafts(source_root, staging_root, inventory)
            (staging_root / "generic-adaptation-manifest.json").write_text(
                json.dumps(batch),
                encoding="utf-8",
            )
            (registry_root / "templates").mkdir(parents=True)
            catalog_path = registry_root / "templates/catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")

            result = promote_generic_drafts(staging_root, registry_root, catalog_path)

            entry = json.loads(catalog_path.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(result, {"promoted": 1})
            self.assertEqual(entry["kind"], "public-identity-template")
            self.assertEqual(entry["source_sha256"], hashlib.sha256(content).hexdigest())
            self.assertNotIn("source_file", entry)
            self.assertNotIn("private", json.dumps(entry).lower())


class CommandLineTests(unittest.TestCase):
    def test_optional_generic_staging_writes_remaining_original_identities(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            (source_root / "class").mkdir(parents=True)
            (source_root / "class/private.json").write_text(
                '{"id":"private","admin_controls":{}}',
                encoding="utf-8",
            )
            catalog_path = root / "catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")
            output_path = root / "inventory.json"
            staging_root = root / "staging"

            exit_code = main(
                [
                    "--source",
                    str(source_root),
                    "--catalog",
                    str(catalog_path),
                    "--output",
                    str(output_path),
                    "--generic-staging",
                    str(staging_root),
                ]
            )

            self.assertEqual(exit_code, 0)
            batch = json.loads(
                (staging_root / "generic-adaptation-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(batch["generated"]), 1)
            self.assertNotIn("private", batch["generated"][0]["name"])

    def test_optional_spell_staging_writes_deduplicated_original_drafts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            (source_root / "spells").mkdir(parents=True)
            (source_root / "spells/fireball.json").write_text(
                '{"id":"fireball","admin_controls":{}}',
                encoding="utf-8",
            )
            catalog_path = root / "catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")
            output_path = root / "inventory.json"
            staging_root = root / "staging"

            exit_code = main(
                [
                    "--source",
                    str(source_root),
                    "--catalog",
                    str(catalog_path),
                    "--output",
                    str(output_path),
                    "--spell-staging",
                    str(staging_root),
                ]
            )

            self.assertEqual(exit_code, 0)
            batch = json.loads(
                (staging_root / "spell-adaptation-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(batch["generated"]), 1)
            self.assertNotIn("fireball", batch["generated"][0]["name"])

    def test_optional_monster_staging_writes_originalized_drafts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            (source_root / "monsters").mkdir(parents=True)
            (source_root / "monsters" / "beholder.json").write_text(
                '{"id":"beholder","category":"aberration","admin_controls":{}}',
                encoding="utf-8",
            )
            catalog_path = root / "catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")
            output_path = root / "inventory.json"
            staging_root = root / "staging"

            exit_code = main(
                [
                    "--source",
                    str(source_root),
                    "--catalog",
                    str(catalog_path),
                    "--output",
                    str(output_path),
                    "--monster-staging",
                    str(staging_root),
                ]
            )

            self.assertEqual(exit_code, 0)
            batch = json.loads(
                (staging_root / "monster-adaptation-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(batch["generated"]), 1)
            self.assertNotIn("beholder", batch["generated"][0]["name"])

    def test_counts_private_source_fingerprint_adaptation_without_source_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            (source_root / "monsters").mkdir(parents=True)
            content = b'{"id":"third_party_name","admin_controls":{}}'
            (source_root / "monsters" / "private-name.json").write_bytes(content)
            catalog_entries = [
                {
                    "source_sha256": hashlib.sha256(content).hexdigest(),
                    "provenance": "public-safe-original-adaptation",
                    "sha256": "0" * 64,
                }
            ]

            inventory = build_inventory(source_root, catalog_entries)

            self.assertEqual(inventory["summary"]["adapted"], 1)
            self.assertEqual(inventory["records"][0]["disposition"], "adapted")

    def test_optional_item_staging_writes_drafts_and_batch_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            (source_root / "item").mkdir(parents=True)
            (source_root / "item" / "copper_gear.json").write_text(
                '{"id":"copper_gear","category":"material","shop_info":{"buy_price":2}}',
                encoding="utf-8",
            )
            catalog_path = root / "catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")
            output_path = root / "inventory.json"
            staging_root = root / "staging"

            exit_code = main(
                [
                    "--source",
                    str(source_root),
                    "--catalog",
                    str(catalog_path),
                    "--output",
                    str(output_path),
                    "--item-staging",
                    str(staging_root),
                ]
            )

            self.assertEqual(exit_code, 0)
            batch = json.loads(
                (staging_root / "item-adaptation-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual([entry["name"] for entry in batch["generated"]], ["copper-gear"])
            self.assertTrue(
                (staging_root / "templates/items/copper-gear/v0.1.0/template.json").exists()
            )

    def test_counts_explicit_public_safe_adaptation_as_adapted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            (source_root / "items").mkdir(parents=True)
            (source_root / "items" / "legacy.json").write_text(
                '{"id":"legacy","shop_info":{"buy_price":2}}',
                encoding="utf-8",
            )
            catalog_entries = [
                {
                    "source_file": "items/legacy.json",
                    "provenance": "public-safe-original-adaptation",
                    "sha256": "0" * 64,
                }
            ]

            inventory = build_inventory(source_root, catalog_entries)

            self.assertEqual(inventory["summary"]["adapted"], 1)
            self.assertEqual(inventory["summary"]["adaptation_required"], 0)
            self.assertEqual(
                inventory["records"],
                [{"path": "items/legacy.json", "disposition": "adapted", "signals": []}],
            )

    def test_writes_deterministic_inventory_manifest_without_changing_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            source_root.mkdir()
            source_path = source_root / "portable.json"
            source_content = '{"id":"portable","template_type":"item","version":"0.1.0"}'
            source_path.write_text(source_content, encoding="utf-8")
            catalog_path = root / "catalog.json"
            catalog_path.write_text('{"entries":[]}', encoding="utf-8")
            output_path = root / "inventory.json"

            exit_code = main(
                [
                    "--source",
                    str(source_root),
                    "--catalog",
                    str(catalog_path),
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(source_path.read_text(encoding="utf-8"), source_content)
            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8")),
                {
                    "summary": {
                        "source_count": 1,
                        "covered": 0,
                        "adapted": 0,
                        "invalid": 0,
                        "snapshot_candidates": 1,
                        "adaptation_required": 0,
                        "excluded": 0,
                    },
                    "records": [
                        {
                            "path": "portable.json",
                            "disposition": "snapshot-candidate",
                            "signals": [],
                        }
                    ],
                },
            )


if __name__ == "__main__":
    unittest.main()
