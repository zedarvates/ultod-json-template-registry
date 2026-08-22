import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.template_contract import compute_spec_checksum
from scripts.validate_registry import (
    validate_public_content,
    validate_public_path,
    validate_registry,
)


class PublicRegistryPolicyTests(unittest.TestCase):
    def test_rejects_hash_placeholder_directory(self):
        violations = validate_public_path(
            "templates/monsters/original-aberration-1234567890/v0.1.0/template.json"
        )
        self.assertEqual(violations, ["hash-placeholder-name"])

    def test_rejects_privileged_and_commercial_fields(self):
        document = {
            "id": "sample",
            "admin_controls": {},
            "shop_info": {"buy_price": 10},
        }
        self.assertEqual(
            validate_public_content(document),
            ["admin-control", "commercial"],
        )

    def test_accepts_semantic_sanitized_template(self):
        document = {
            "id": "aberration_creature_0001",
            "base_stats": {"health": 100},
            "loot_table": {},
        }
        self.assertEqual(validate_public_content(document), [])
        self.assertEqual(
            validate_public_path(
                "templates/monsters/aberration-creature-0001/v0.1.0/template.json"
            ),
            [],
        )


def install_test_schemas(root):
    common_source = Path("templates/schemas/template-contract/v1.0.0/schema.json")
    common_target = root / common_source
    common_target.parent.mkdir(parents=True)
    shutil.copyfile(common_source, common_target)
    family = root / "templates/schemas/monsters/v1.0.0/schema.json"
    family.parent.mkdir(parents=True)
    family.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://ultimateodycer.com/schemas/monsters/1.0.0",
                "allOf": [
                    {
                        "$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"
                    },
                    {
                        "properties": {
                            "spec": {
                                "type": "object",
                                "required": ["category"],
                                "properties": {"category": {"type": "string"}},
                                "additionalProperties": False,
                            }
                        }
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def strict_monster(spec):
    return {
        "$schema": "../../../schemas/monsters/v1.0.0/schema.json",
        "contract_version": "1.0.0",
        "id": "monsters:forest-wolf",
        "slug": "forest-wolf",
        "family": "monsters",
        "version": "1.0.0",
        "authority": "declarative",
        "intended_consumers": [],
        "compatibility": [],
        "dependencies": [],
        "spec_checksum": compute_spec_checksum(spec),
        "spec": spec,
    }


def strict_entry(path, root, document):
    return {
        "id": document["id"],
        "slug": document["slug"],
        "family": document["family"],
        "name": document["slug"],
        "kind": "monster-template",
        "version": document["version"],
        "contract_version": document["contract_version"],
        "validation_profile": "strict-v1",
        "status": "experimental",
        "schema_file": "templates/schemas/monsters/v1.0.0/schema.json",
        "file": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "spec_checksum": document["spec_checksum"],
        "intended_consumers": [],
        "compatibility": [],
        "supersedes": [],
    }


def write_catalog(root, entries):
    catalog = root / "templates/catalog.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps(
            {
                "registry_version": "2.0.0",
                "aliases": [],
                "entries": entries,
            }
        ),
        encoding="utf-8",
    )


class DualProfileValidationTests(unittest.TestCase):
    def test_legacy_document_is_not_forced_through_v1_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "templates/items/legacy-item/v0.1.0/template.json"
            path.parent.mkdir(parents=True)
            path.write_bytes(b'{"id":"legacy_item","mixedCase":true}')
            write_catalog(
                root,
                [
                    {
                        "name": "legacy-item",
                        "kind": "item-template",
                        "version": "0.1.0",
                        "status": "experimental",
                        "file": path.relative_to(root).as_posix(),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "compatibility": [],
                        "validation_profile": "legacy-unvalidated",
                        "contract_version": None,
                    }
                ],
            )
            self.assertEqual(validate_registry(root).issues, [])

    def test_strict_document_fails_on_wrong_checksum_and_missing_dependency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            install_test_schemas(root)
            path = root / "templates/monsters/forest-wolf/v1.0.0/template.json"
            path.parent.mkdir(parents=True)
            spec = {"category": "animal"}
            document = strict_monster(spec)
            document["spec_checksum"] = "sha256:" + "0" * 64
            document["dependencies"] = ["items:missing@1.0.0"]
            path.write_text(json.dumps(document), encoding="utf-8")
            write_catalog(root, [strict_entry(path, root, document)])
            messages = [issue.message for issue in validate_registry(root).issues]
            self.assertTrue(any("spec checksum mismatch" in message for message in messages))
            self.assertTrue(
                any("missing dependency items:missing@1.0.0" in message for message in messages)
            )


if __name__ == "__main__":
    unittest.main()
