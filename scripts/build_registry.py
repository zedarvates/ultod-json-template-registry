#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any


SECRET_KEY = re.compile(r"(?:api[_-]?key|secret|password|passwd|token|private[_-]?key)", re.IGNORECASE)
INTERNAL_KEY = re.compile(r"(?:server[_-]?url|internal[_-]?(?:url|host|path)|connection[_-]?string)", re.IGNORECASE)
INTERNAL_VALUE = re.compile(
    r"(?:https?://(?:localhost|127\.0\.0\.1|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)|[A-Za-z]:\\)",
    re.IGNORECASE,
)
RIGHTS_VALUE = re.compile(
    r"(?:warcraft|ultima(?:\s+online)?|one[ _-]?piece|tolkien|lovecraft|cthulhu|aion|sphere|skaven|tiefling|drow|xenomorph|mithril|blizzard|peacebloom|silverleaf|sweet[ _-]?roll|arcane[ _-]?dust|recall[ _-]?stone)",
    re.IGNORECASE,
)
RIGHTS_SOURCE_PATH = re.compile(r"^(?:ability|bods|champions|skillclass|talent)/", re.IGNORECASE)
POLICY_EXCLUSION_SOURCE_PATH = re.compile(
    r"^(?:abilities/[^/]+\.json|bulk_orders/|class/|divine_system/|names/|race/|recipe/|tournaments/|treasure_maps/|virtues_factions/)",
    re.IGNORECASE,
)
FAMILY_ADAPTATION_SOURCE_PATH = re.compile(
    r"^(?:ai/(?:elite_guard|guard_basic)\.json|blueprints/havre_du_roi__|city_layouts/|cosmetic/|item/|loot/|planets/terre\.json|professions/|rts/)",
    re.IGNORECASE,
)
ADMIN_KEY = re.compile(r"(?:admin|debug|cheat|god[_-]?mode)", re.IGNORECASE)
COMMERCIAL_KEY = re.compile(r"(?:shop|price|stock|sku|billing|premium[_-]?currency|real[_-]?money)", re.IGNORECASE)
RUNTIME_KEY = re.compile(r"(?:current[_-]?(?:health|mana|state)|last[_-]?(?:seen|harvest)|spawned[_-]?at)", re.IGNORECASE)
ASSET_KEY = re.compile(r"(?:asset[_-]?path|model[_-]?path|texture[_-]?path|audio[_-]?path)", re.IGNORECASE)
SAFE_ID = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
MANUAL_ITEM_ID = re.compile(r"(?:admin|debug|override|premium|token|sku|bundle)", re.IGNORECASE)


def discover_sources(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*.json")
        if "_versions" not in path.relative_to(source_root).parts
    )


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def classify_document(document: Any, raw_text: str, source_path: str = "") -> dict[str, Any]:
    signals: set[str] = set()
    for key, value in _walk(document):
        if SECRET_KEY.search(key):
            signals.add("secret")
        if INTERNAL_KEY.search(key):
            signals.add("internal")
        if ADMIN_KEY.search(key):
            signals.add("admin-control")
        if COMMERCIAL_KEY.search(key):
            signals.add("commercial")
        if RUNTIME_KEY.search(key):
            signals.add("runtime-state")
        if ASSET_KEY.search(key):
            signals.add("asset-path")
        if isinstance(value, str):
            if INTERNAL_VALUE.search(value):
                signals.add("internal")
            if RIGHTS_VALUE.search(value):
                signals.add("rights")

    if RIGHTS_VALUE.search(raw_text):
        signals.add("rights")
    if INTERNAL_VALUE.search(raw_text):
        signals.add("internal")
    if RIGHTS_SOURCE_PATH.search(source_path.replace("\\", "/")):
        signals.add("rights")
    normalized_source_path = source_path.replace("\\", "/")
    if POLICY_EXCLUSION_SOURCE_PATH.search(normalized_source_path):
        signals.add("policy-exclusion")
    if FAMILY_ADAPTATION_SOURCE_PATH.search(normalized_source_path):
        signals.add("family-policy")

    ordered = sorted(signals)
    if signals.intersection({"secret", "internal", "rights", "policy-exclusion"}):
        disposition = "excluded"
    elif signals:
        disposition = "adaptation-required"
    else:
        disposition = "snapshot-candidate"
    return {"disposition": disposition, "signals": ordered}


def _hash_variants(content: bytes) -> set[str]:
    lf = content.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {
        hashlib.sha256(content).hexdigest(),
        hashlib.sha256(lf).hexdigest(),
        hashlib.sha256(crlf).hexdigest(),
    }


def adapt_item_document(document: dict[str, Any], source_path: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError(f"{source_path}: item source must be a JSON object and requires manual review")
    identifier = document.get("id") or document.get("item_id")
    if not isinstance(identifier, str) or not SAFE_ID.fullmatch(identifier):
        raise ValueError(f"{source_path}: item id requires manual review")
    if MANUAL_ITEM_ID.search(identifier):
        raise ValueError(f"{source_path}: operational or commercial item id requires manual review")

    category = document.get("category") if isinstance(document.get("category"), str) else "material"
    rarity = document.get("rarity") if isinstance(document.get("rarity"), str) else "common"
    source_weight = document.get("base_stats", {}).get("weight", 0.1)
    weight_kg = source_weight if isinstance(source_weight, (int, float)) and 0 < source_weight <= 100 else 0.1
    stack_limit = 50 if category == "material" else 10

    return {
        "id": identifier,
        "template_type": "item",
        "version": "0.1.0",
        "name": identifier.replace("_", " ").title(),
        "description": f"A portable {category} component for public template workflows.",
        "category": category,
        "rarity": rarity,
        "stack_limit": stack_limit,
        "weight_kg": weight_kg,
        "tags": ["adapted", category],
        "dependencies": [],
    }


def adapt_manual_item_source(document: Any, source_path: str) -> dict[str, Any]:
    if source_path == "item/balance_override_token.json":
        return {
            "id": "calibration_marker",
            "template_type": "item",
            "version": "0.1.0",
            "name": "Calibration Marker",
            "description": "An inert marker used to label experimental crafting configurations.",
            "category": "material",
            "rarity": "uncommon",
            "stack_limit": 10,
            "weight_kg": 0.1,
            "tags": ["adapted", "calibration"],
            "dependencies": [],
        }
    if source_path == "item/cosmetic_frost_mount_token_item.json":
        return {
            "id": "winter_mount_ornament",
            "template_type": "item",
            "version": "0.1.0",
            "name": "Winter Mount Ornament",
            "description": "A decorative winter-themed ornament without entitlement or gameplay effects.",
            "category": "cosmetic",
            "rarity": "uncommon",
            "stack_limit": 1,
            "weight_kg": 0.1,
            "tags": ["adapted", "cosmetic"],
            "dependencies": [],
        }
    if source_path == "item/sets.json":
        return {
            "id": "equipment_set_catalog",
            "template_type": "item_set_catalog",
            "version": "0.1.0",
            "name": "Equipment Set Catalog",
            "description": "A statless catalog of original equipment-set identities.",
            "sets": [
                {"id": "iron_guard_set", "name": "Iron Guard Set"},
                {"id": "aether_weaver_set", "name": "Aether Weaver Set"},
            ],
        }
    if source_path == "item/wings.json":
        return {
            "id": "flight_style_catalog",
            "template_type": "cosmetic_style_catalog",
            "version": "0.1.0",
            "name": "Flight Style Catalog",
            "description": "A statless catalog of original cosmetic flight-style identities.",
            "styles": [
                {"id": "luminous_feather", "name": "Luminous Feather"},
                {"id": "ember_membrane", "name": "Ember Membrane"},
                {"id": "ancient_scale", "name": "Ancient Scale"},
            ],
        }
    raise ValueError(f"{source_path}: no manual public-safe item adapter")


def adapt_monster_document(document: dict[str, Any], source_content: bytes) -> dict[str, Any]:
    category_value = document.get("category") if isinstance(document, dict) else None
    category = category_value if isinstance(category_value, str) and SAFE_ID.fullmatch(category_value) else "creature"
    rarity_value = document.get("rarity") if isinstance(document, dict) else None
    allowed_rarities = {"common", "uncommon", "rare", "epic", "legendary", "mythic"}
    rarity = rarity_value if rarity_value in allowed_rarities else "common"
    source_sha256 = hashlib.sha256(source_content).hexdigest()
    suffix = source_sha256[:10]
    short_label = source_sha256[:6].upper()
    return {
        "id": f"original_{category}_{suffix}",
        "template_type": "monster",
        "version": "0.1.0",
        "name": f"Original {category.replace('_', ' ').title()} {short_label}",
        "description": f"An original {category} creature identity for public template workflows.",
        "category": category,
        "rarity": rarity,
        "tags": ["adapted", category, "original"],
        "dependencies": [],
    }


def adapt_spell_document(document: dict[str, Any], source_content: bytes) -> dict[str, Any]:
    source_sha256 = hashlib.sha256(source_content).hexdigest()
    suffix = source_sha256[:10]
    short_label = source_sha256[:6].upper()
    return {
        "id": f"original_spell_{suffix}",
        "template_type": "spell",
        "version": "0.1.0",
        "name": f"Original Spell {short_label}",
        "description": "An original statless spell identity for public template workflows.",
        "tags": ["adapted", "original", "spell"],
        "dependencies": [],
    }


def adapt_generic_document(
    document: Any,
    source_content: bytes,
    source_family: str,
) -> dict[str, Any]:
    commercial_families = {"bods", "bulk_orders", "cosmetic_shop", "currencies", "shop", "vendor_shops"}
    family = source_family if SAFE_ID.fullmatch(source_family) else "content"
    if family in commercial_families:
        family = "content"
    source_sha256 = hashlib.sha256(source_content).hexdigest()
    suffix = source_sha256[:10]
    short_label = source_sha256[:6].upper()
    family_label = family.replace("_", " ").title()
    return {
        "id": f"original_{family}_{suffix}",
        "template_type": "public_identity",
        "version": "0.1.0",
        "name": f"Original {family_label} {short_label}",
        "description": f"An original statless {family} identity for public template workflows.",
        "source_family": family,
        "tags": ["adapted", family, "original"],
        "dependencies": [],
    }


def build_item_drafts(
    source_root: Path,
    staging_root: Path,
    inventory: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    generated = []
    rejected = []
    records = sorted(inventory.get("records", []), key=lambda record: record.get("path", ""))
    for record in records:
        source_file = record.get("path", "")
        if record.get("disposition") != "adaptation-required" or not source_file.startswith("item/"):
            continue
        document = json.loads((source_root / source_file).read_text(encoding="utf-8"))
        try:
            adapted = adapt_item_document(document, source_file)
        except ValueError as error:
            try:
                adapted = adapt_manual_item_source(document, source_file)
            except ValueError:
                rejected.append({"source_file": source_file, "reason": str(error)})
                continue

        name = adapted["id"].replace("_", "-")
        relative_template = Path("templates") / "items" / name / "v0.1.0" / "template.json"
        template_path = staging_root / relative_template
        if template_path.exists():
            raise FileExistsError(f"refusing to overwrite existing staged template: {template_path}")
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(json.dumps(adapted, indent=2) + "\n", encoding="utf-8")
        readme_path = template_path.with_name("README.md")
        readme_path.write_text(
            f"# {adapted['name']} v0.1.0\n\n"
            "Status: `experimental`.\n\n"
            f"Original public-safe adaptation informed by `{source_file}`. "
            "Economy, runtime state, effects, internal controls, and asset paths are excluded.\n\n"
            "No client or server compatibility is certified.\n",
            encoding="utf-8",
        )
        generated.append(
            {
                "source_file": source_file,
                "name": name,
                "template_file": relative_template.as_posix(),
            }
        )

    return {"generated": generated, "rejected": rejected}


def promote_item_drafts(
    staging_root: Path,
    registry_root: Path,
    catalog_path: Path,
) -> dict[str, int]:
    batch = json.loads((staging_root / "item-adaptation-manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    existing_files = {entry.get("file") for entry in entries}
    existing_identities = {
        (entry.get("kind"), entry.get("name"), entry.get("version")) for entry in entries
    }
    promotions = []

    for item in sorted(batch.get("generated", []), key=lambda entry: entry["template_file"]):
        template_file = item["template_file"]
        source_template = staging_root / template_file
        source_version_dir = source_template.parent
        target_version_dir = registry_root / Path(template_file).parent
        identity = ("item-template", item["name"], "0.1.0")
        if target_version_dir.exists() or template_file in existing_files or identity in existing_identities:
            raise FileExistsError(f"promotion collision for {template_file}")
        if not source_template.exists() or not (source_version_dir / "README.md").exists():
            raise FileNotFoundError(f"incomplete staged item: {source_version_dir}")
        entry = {
            "name": item["name"],
            "kind": "item-template",
            "version": "0.1.0",
            "status": "experimental",
            "file": template_file,
            "source_file": item["source_file"],
            "provenance": "public-safe-original-adaptation",
            "sha256": hashlib.sha256(source_template.read_bytes()).hexdigest(),
            "compatibility": [],
        }
        promotions.append((source_version_dir, target_version_dir, entry))

    copied = []
    try:
        for source_version_dir, target_version_dir, entry in promotions:
            shutil.copytree(source_version_dir, target_version_dir)
            copied.append(target_version_dir)
            entries.append(entry)
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    except Exception:
        for target_version_dir in reversed(copied):
            shutil.rmtree(target_version_dir)
        raise

    return {"promoted": len(promotions)}


def build_monster_drafts(
    source_root: Path,
    staging_root: Path,
    inventory: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    generated = []
    records = sorted(inventory.get("records", []), key=lambda record: record.get("path", ""))
    for record in records:
        source_file = record.get("path", "")
        if record.get("disposition") not in {"adaptation-required", "excluded"} or not source_file.startswith("monsters/"):
            continue
        source_content = (source_root / source_file).read_bytes()
        document = json.loads(source_content.decode("utf-8"))
        adapted = adapt_monster_document(document, source_content)
        name = adapted["id"].replace("_", "-")
        relative_template = Path("templates") / "monsters" / name / "v0.1.0" / "template.json"
        template_path = staging_root / relative_template
        if template_path.exists():
            raise FileExistsError(f"refusing to overwrite existing staged template: {template_path}")
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(json.dumps(adapted, indent=2) + "\n", encoding="utf-8")
        source_sha256 = hashlib.sha256(source_content).hexdigest()
        template_path.with_name("README.md").write_text(
            f"# {adapted['name']} v0.1.0\n\n"
            "Status: `experimental`.\n\n"
            "Original public-safe creature identity derived from a private source fingerprint. "
            "Names, descriptions, statistics, abilities, loot, AI, assets, runtime state, and controls are excluded.\n\n"
            f"Private source SHA-256: `{source_sha256}`.\n\n"
            "No client or server compatibility is certified.\n",
            encoding="utf-8",
        )
        generated.append(
            {
                "source_file": source_file,
                "source_sha256": source_sha256,
                "name": name,
                "template_file": relative_template.as_posix(),
            }
        )
    return {"generated": generated, "rejected": []}


def promote_monster_drafts(
    staging_root: Path,
    registry_root: Path,
    catalog_path: Path,
) -> dict[str, int]:
    batch = json.loads((staging_root / "monster-adaptation-manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    existing_files = {entry.get("file") for entry in entries}
    existing_identities = {
        (entry.get("kind"), entry.get("name"), entry.get("version")) for entry in entries
    }
    promotions = []
    for monster in sorted(batch.get("generated", []), key=lambda entry: entry["template_file"]):
        template_file = monster["template_file"]
        source_template = staging_root / template_file
        source_version_dir = source_template.parent
        target_version_dir = registry_root / Path(template_file).parent
        identity = ("monster-template", monster["name"], "0.1.0")
        if target_version_dir.exists() or template_file in existing_files or identity in existing_identities:
            raise FileExistsError(f"promotion collision for {template_file}")
        if not source_template.exists() or not (source_version_dir / "README.md").exists():
            raise FileNotFoundError(f"incomplete staged monster: {source_version_dir}")
        promotions.append(
            (
                source_version_dir,
                target_version_dir,
                {
                    "name": monster["name"],
                    "kind": "monster-template",
                    "version": "0.1.0",
                    "status": "experimental",
                    "file": template_file,
                    "source_sha256": monster["source_sha256"],
                    "provenance": "public-safe-original-adaptation",
                    "sha256": hashlib.sha256(source_template.read_bytes()).hexdigest(),
                    "compatibility": [],
                },
            )
        )

    copied = []
    try:
        for source_version_dir, target_version_dir, entry in promotions:
            shutil.copytree(source_version_dir, target_version_dir)
            copied.append(target_version_dir)
            entries.append(entry)
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    except Exception:
        for target_version_dir in reversed(copied):
            shutil.rmtree(target_version_dir)
        raise
    return {"promoted": len(promotions)}


def build_spell_drafts(
    source_root: Path,
    staging_root: Path,
    inventory: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    generated = []
    deduplicated = []
    seen_source_hashes: dict[str, str] = {}
    records = sorted(inventory.get("records", []), key=lambda record: record.get("path", ""))
    for record in records:
        source_file = record.get("path", "")
        is_spell_source = source_file.startswith("spells/") or source_file.startswith("content_pipeline/spells/")
        if record.get("disposition") not in {"adaptation-required", "excluded"} or not is_spell_source:
            continue
        source_content = (source_root / source_file).read_bytes()
        source_sha256 = hashlib.sha256(source_content).hexdigest()
        if source_sha256 in seen_source_hashes:
            deduplicated.append(
                {
                    "source_file": source_file,
                    "source_sha256": source_sha256,
                    "represented_by": seen_source_hashes[source_sha256],
                }
            )
            continue
        document = json.loads(source_content.decode("utf-8"))
        adapted = adapt_spell_document(document, source_content)
        name = adapted["id"].replace("_", "-")
        relative_template = Path("templates") / "spells" / name / "v0.1.0" / "template.json"
        template_path = staging_root / relative_template
        if template_path.exists():
            raise FileExistsError(f"refusing to overwrite existing staged template: {template_path}")
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(json.dumps(adapted, indent=2) + "\n", encoding="utf-8")
        template_path.with_name("README.md").write_text(
            f"# {adapted['name']} v0.1.0\n\n"
            "Status: `experimental`.\n\n"
            "Original public-safe spell identity derived from a private source fingerprint. "
            "Names, descriptions, effects, formulas, groups, cultures, assets, runtime state, and controls are excluded.\n\n"
            f"Private source SHA-256: `{source_sha256}`.\n\n"
            "No client or server compatibility is certified.\n",
            encoding="utf-8",
        )
        generated.append(
            {
                "source_file": source_file,
                "source_sha256": source_sha256,
                "name": name,
                "template_file": relative_template.as_posix(),
            }
        )
        seen_source_hashes[source_sha256] = name
    return {"generated": generated, "deduplicated": deduplicated, "rejected": []}


def promote_spell_drafts(
    staging_root: Path,
    registry_root: Path,
    catalog_path: Path,
) -> dict[str, int]:
    batch = json.loads((staging_root / "spell-adaptation-manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    existing_files = {entry.get("file") for entry in entries}
    existing_identities = {
        (entry.get("kind"), entry.get("name"), entry.get("version")) for entry in entries
    }
    promotions = []
    for spell in sorted(batch.get("generated", []), key=lambda entry: entry["template_file"]):
        template_file = spell["template_file"]
        source_template = staging_root / template_file
        source_version_dir = source_template.parent
        target_version_dir = registry_root / Path(template_file).parent
        identity = ("spell-template", spell["name"], "0.1.0")
        if target_version_dir.exists() or template_file in existing_files or identity in existing_identities:
            raise FileExistsError(f"promotion collision for {template_file}")
        if not source_template.exists() or not (source_version_dir / "README.md").exists():
            raise FileNotFoundError(f"incomplete staged spell: {source_version_dir}")
        promotions.append(
            (
                source_version_dir,
                target_version_dir,
                {
                    "name": spell["name"],
                    "kind": "spell-template",
                    "version": "0.1.0",
                    "status": "experimental",
                    "file": template_file,
                    "source_sha256": spell["source_sha256"],
                    "provenance": "public-safe-original-adaptation",
                    "sha256": hashlib.sha256(source_template.read_bytes()).hexdigest(),
                    "compatibility": [],
                },
            )
        )
    copied = []
    try:
        for source_version_dir, target_version_dir, entry in promotions:
            shutil.copytree(source_version_dir, target_version_dir)
            copied.append(target_version_dir)
            entries.append(entry)
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    except Exception:
        for target_version_dir in reversed(copied):
            shutil.rmtree(target_version_dir)
        raise
    return {"promoted": len(promotions)}


def remove_legacy_spell_entries(
    registry_root: Path,
    catalog_path: Path,
    names: set[str],
) -> dict[str, int]:
    original_catalog = catalog_path.read_text(encoding="utf-8")
    catalog = json.loads(original_catalog)
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    removals = [
        entry
        for entry in entries
        if entry.get("kind") == "spell-template" and entry.get("name") in names
    ]
    allowed_root = (registry_root / "templates/spells").resolve()
    spell_directories = []
    for entry in removals:
        spell_dir = (registry_root / Path(entry["file"])).parent.parent
        if not spell_dir.exists():
            raise FileNotFoundError(f"legacy spell directory missing: {spell_dir}")
        resolved_spell_dir = spell_dir.resolve()
        if not resolved_spell_dir.is_relative_to(allowed_root):
            raise ValueError(f"legacy spell path escapes registry: {resolved_spell_dir}")
        if resolved_spell_dir not in spell_directories:
            spell_directories.append(resolved_spell_dir)

    remaining = [entry for entry in entries if entry not in removals]
    moved = []
    with tempfile.TemporaryDirectory(prefix="legacy-spells-", dir=registry_root) as temp_dir:
        backup_root = Path(temp_dir)
        try:
            for index, spell_dir in enumerate(spell_directories):
                backup = backup_root / f"{index}-{spell_dir.name}"
                shutil.move(str(spell_dir), str(backup))
                moved.append((backup, spell_dir))
            entries[:] = remaining
            catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
        except Exception:
            catalog_path.write_text(original_catalog, encoding="utf-8")
            for backup, spell_dir in reversed(moved):
                if backup.exists():
                    shutil.move(str(backup), str(spell_dir))
            raise
    return {"removed": len(removals)}


def remove_catalog_files(
    registry_root: Path,
    catalog_path: Path,
    file_paths: set[str],
) -> dict[str, int]:
    original_catalog = catalog_path.read_text(encoding="utf-8")
    catalog = json.loads(original_catalog)
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    removals = [entry for entry in entries if entry.get("file") in file_paths]
    found = {entry.get("file") for entry in removals}
    if found != file_paths:
        missing_entries = sorted(file_paths - found)
        raise KeyError(f"catalog entries missing: {missing_entries}")

    registry_resolved = registry_root.resolve()
    version_directories = []
    for entry in removals:
        version_dir = (registry_root / Path(entry["file"])).parent
        if not version_dir.exists():
            raise FileNotFoundError(f"catalog file missing: {entry['file']}")
        resolved_version_dir = version_dir.resolve()
        if not resolved_version_dir.is_relative_to(registry_resolved):
            raise ValueError(f"catalog path escapes registry: {resolved_version_dir}")
        if resolved_version_dir not in version_directories:
            version_directories.append(resolved_version_dir)

    remaining = [entry for entry in entries if entry not in removals]
    moved = []
    with tempfile.TemporaryDirectory(prefix="catalog-removal-", dir=registry_root) as temp_dir:
        backup_root = Path(temp_dir)
        try:
            for index, version_dir in enumerate(version_directories):
                backup = backup_root / f"{index}-{version_dir.parent.name}-{version_dir.name}"
                shutil.move(str(version_dir), str(backup))
                moved.append((backup, version_dir))
            entries[:] = remaining
            catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
        except Exception:
            catalog_path.write_text(original_catalog, encoding="utf-8")
            for backup, version_dir in reversed(moved):
                if backup.exists():
                    version_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(backup), str(version_dir))
            raise
    return {"removed": len(removals)}


PUBLIC_FAMILY_MAP = {
    "ability": "abilities",
    "class": "classes",
    "item": "items",
    "lineage": "lineages",
    "race": "races",
    "racial_traits": "racial-traits",
}


def build_generic_drafts(
    source_root: Path,
    staging_root: Path,
    inventory: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    generated = []
    deduplicated = []
    seen_source_hashes: dict[str, str] = {}
    records = sorted(inventory.get("records", []), key=lambda record: record.get("path", ""))
    for record in records:
        source_file = record.get("path", "")
        if record.get("disposition") not in {"adaptation-required", "excluded"}:
            continue
        source_content = (source_root / source_file).read_bytes()
        source_sha256 = hashlib.sha256(source_content).hexdigest()
        if source_sha256 in seen_source_hashes:
            deduplicated.append(
                {
                    "source_file": source_file,
                    "source_sha256": source_sha256,
                    "represented_by": seen_source_hashes[source_sha256],
                }
            )
            continue
        source_family = source_file.split("/", 1)[0]
        document = json.loads(source_content.decode("utf-8"))
        adapted = adapt_generic_document(document, source_content, source_family)
        adapted_family = adapted["source_family"]
        public_family = PUBLIC_FAMILY_MAP.get(adapted_family, adapted_family.replace("_", "-"))
        name = adapted["id"].replace("_", "-")
        relative_template = Path("templates") / public_family / name / "v0.1.0" / "template.json"
        template_path = staging_root / relative_template
        if template_path.exists():
            raise FileExistsError(f"refusing to overwrite existing staged template: {template_path}")
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(json.dumps(adapted, indent=2) + "\n", encoding="utf-8")
        template_path.with_name("README.md").write_text(
            f"# {adapted['name']} v0.1.0\n\n"
            "Status: `experimental`.\n\n"
            "Original public-safe statless identity derived from a private source fingerprint. "
            "Source names, descriptions, mechanics, values, assets, runtime state, and controls are excluded.\n\n"
            f"Private source SHA-256: `{source_sha256}`.\n\n"
            "No client or server compatibility is certified.\n",
            encoding="utf-8",
        )
        generated.append(
            {
                "source_file": source_file,
                "source_sha256": source_sha256,
                "name": name,
                "template_file": relative_template.as_posix(),
            }
        )
        seen_source_hashes[source_sha256] = name
    return {"generated": generated, "deduplicated": deduplicated, "rejected": []}


def promote_generic_drafts(
    staging_root: Path,
    registry_root: Path,
    catalog_path: Path,
) -> dict[str, int]:
    batch = json.loads((staging_root / "generic-adaptation-manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    existing_files = {entry.get("file") for entry in entries}
    existing_identities = {
        (entry.get("kind"), entry.get("name"), entry.get("version")) for entry in entries
    }
    promotions = []
    for generic in sorted(batch.get("generated", []), key=lambda entry: entry["template_file"]):
        template_file = generic["template_file"]
        source_template = staging_root / template_file
        source_version_dir = source_template.parent
        target_version_dir = registry_root / Path(template_file).parent
        identity = ("public-identity-template", generic["name"], "0.1.0")
        if target_version_dir.exists() or template_file in existing_files or identity in existing_identities:
            raise FileExistsError(f"promotion collision for {template_file}")
        if not source_template.exists() or not (source_version_dir / "README.md").exists():
            raise FileNotFoundError(f"incomplete staged generic identity: {source_version_dir}")
        promotions.append(
            (
                source_version_dir,
                target_version_dir,
                {
                    "name": generic["name"],
                    "kind": "public-identity-template",
                    "version": "0.1.0",
                    "status": "experimental",
                    "file": template_file,
                    "source_sha256": generic["source_sha256"],
                    "provenance": "public-safe-original-adaptation",
                    "sha256": hashlib.sha256(source_template.read_bytes()).hexdigest(),
                    "compatibility": [],
                },
            )
        )
    copied = []
    try:
        for source_version_dir, target_version_dir, entry in promotions:
            shutil.copytree(source_version_dir, target_version_dir)
            copied.append(target_version_dir)
            entries.append(entry)
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    except Exception:
        for target_version_dir in reversed(copied):
            shutil.rmtree(target_version_dir)
        raise
    return {"promoted": len(promotions)}


def build_inventory(source_root: Path, catalog_entries: list[dict[str, Any]]) -> dict[str, Any]:
    known_hashes = {entry.get("sha256") for entry in catalog_entries if entry.get("sha256")}
    adapted_sources = {
        entry["source_file"].replace("\\", "/")
        for entry in catalog_entries
        if entry.get("provenance") == "public-safe-original-adaptation" and entry.get("source_file")
    }
    adapted_source_hashes = {
        entry["source_sha256"]
        for entry in catalog_entries
        if entry.get("provenance") == "public-safe-original-adaptation" and entry.get("source_sha256")
    }
    summary = {
        "source_count": 0,
        "covered": 0,
        "adapted": 0,
        "invalid": 0,
        "snapshot_candidates": 0,
        "adaptation_required": 0,
        "excluded": 0,
    }
    records = []

    for path in discover_sources(source_root):
        summary["source_count"] += 1
        content = path.read_bytes()
        record = {"path": path.relative_to(source_root).as_posix()}
        if _hash_variants(content).intersection(known_hashes):
            record.update({"disposition": "covered", "signals": []})
            summary["covered"] += 1
        elif hashlib.sha256(content).hexdigest() in adapted_source_hashes or record["path"] in adapted_sources:
            record.update({"disposition": "adapted", "signals": []})
            summary["adapted"] += 1
        else:
            try:
                text = content.decode("utf-8")
                document = json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                record.update({"disposition": "invalid", "signals": [], "error": str(error)})
                summary["invalid"] += 1
            else:
                classification = classify_document(document, text, record["path"])
                record.update(classification)
                summary_key = {
                    "snapshot-candidate": "snapshot_candidates",
                    "adaptation-required": "adaptation_required",
                    "excluded": "excluded",
                }[classification["disposition"]]
                summary[summary_key] += 1
        records.append(record)

    return {"summary": summary, "records": records}


def summarize_families(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, int]] = {}
    for record in inventory.get("records", []):
        family = record["path"].split("/", 1)[0]
        counts = grouped.setdefault(
            family,
            {"source": 0, "covered": 0, "adapted": 0, "remaining": 0, "invalid": 0},
        )
        counts["source"] += 1
        disposition = record.get("disposition")
        if disposition == "covered":
            counts["covered"] += 1
        elif disposition == "adapted":
            counts["adapted"] += 1
        elif disposition == "invalid":
            counts["invalid"] += 1
        else:
            counts["remaining"] += 1

    return [
        {
            "family": family,
            "audit_state": "complete" if counts["remaining"] == 0 and counts["invalid"] == 0 else "pending",
            "source_current_count": counts["source"],
            "snapshot_covered_count": counts["covered"],
            "adaptation_covered_count": counts["adapted"],
            "remaining_count": counts["remaining"],
            "invalid_count": counts["invalid"],
        }
        for family, counts in sorted(grouped.items())
    ]


def update_audit_coverage(
    audit_path: Path,
    inventory: dict[str, Any],
    catalog_count: int,
) -> None:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    summary = inventory["summary"]
    accounted = summary["covered"] + summary["adapted"]
    audit.update(
        {
            "format_version": 2,
            "invalid_json_files": summary["invalid"],
            "server_current_count": summary["source_count"],
            "catalog_entry_count": catalog_count,
            "server_current_covered_by_published_hash": summary["covered"],
            "server_current_not_covered_by_published_hash": summary["source_count"] - summary["covered"],
            "server_current_covered_by_public_adaptation": summary["adapted"],
            "server_current_total_accounted": accounted,
            "server_current_remaining": summary["source_count"] - accounted,
            "server_current_pending_audit": summary["source_count"] - accounted,
            "families": summarize_families(inventory),
        }
    )
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a fail-closed JSON source inventory.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--item-staging", type=Path)
    parser.add_argument("--monster-staging", type=Path)
    parser.add_argument("--spell-staging", type=Path)
    parser.add_argument("--generic-staging", type=Path)
    args = parser.parse_args(argv)

    catalog_data = json.loads(args.catalog.read_text(encoding="utf-8"))
    entries = catalog_data.get("entries", catalog_data) if isinstance(catalog_data, dict) else catalog_data
    inventory = build_inventory(args.source, entries)
    args.output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    if args.item_staging:
        batch = build_item_drafts(args.source, args.item_staging, inventory)
        args.item_staging.mkdir(parents=True, exist_ok=True)
        (args.item_staging / "item-adaptation-manifest.json").write_text(
            json.dumps(batch, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.monster_staging:
        batch = build_monster_drafts(args.source, args.monster_staging, inventory)
        args.monster_staging.mkdir(parents=True, exist_ok=True)
        (args.monster_staging / "monster-adaptation-manifest.json").write_text(
            json.dumps(batch, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.spell_staging:
        batch = build_spell_drafts(args.source, args.spell_staging, inventory)
        args.spell_staging.mkdir(parents=True, exist_ok=True)
        (args.spell_staging / "spell-adaptation-manifest.json").write_text(
            json.dumps(batch, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.generic_staging:
        batch = build_generic_drafts(args.source, args.generic_staging, inventory)
        args.generic_staging.mkdir(parents=True, exist_ok=True)
        (args.generic_staging / "generic-adaptation-manifest.json").write_text(
            json.dumps(batch, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
