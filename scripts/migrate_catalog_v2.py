from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def migrate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    migrated = copy.deepcopy(catalog)
    migrated["registry_version"] = "2.0.0"
    migrated["aliases"] = list(migrated.get("aliases", []))
    for entry in migrated.get("entries", []):
        entry.setdefault("validation_profile", "legacy-unvalidated")
        entry.setdefault("contract_version", None)
    return migrated


def ensure_contract_schema_entry(catalog: dict[str, Any], root: Path) -> None:
    path = root / "templates/schemas/template-contract/v1.0.0/schema.json"
    relative = path.relative_to(root).as_posix()
    if any(entry.get("file") == relative for entry in catalog.get("entries", [])):
        return
    catalog.setdefault("entries", []).append(
        {
            "name": "template-contract",
            "kind": "json-schema",
            "version": "1.0.0",
            "status": "experimental",
            "file": relative,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "compatibility": [],
            "validation_profile": "strict-schema-v1",
            "contract_version": "1.0.0",
        }
    )


def main():
    parser = argparse.ArgumentParser(description="Migrate the registry catalog to v2")
    parser.add_argument(
        "--catalog", type=Path, default=Path("templates/catalog.json")
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    original = json.loads(args.catalog.read_text(encoding="utf-8"))
    migrated = migrate_catalog(original)
    ensure_contract_schema_entry(migrated, args.catalog.parent.parent)
    rendered = json.dumps(migrated, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        raise SystemExit(
            0 if args.catalog.read_text(encoding="utf-8") == rendered else 1
        )
    args.catalog.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
