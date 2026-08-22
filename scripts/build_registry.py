#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import shutil
import copy
import re
import unicodedata
from typing import Any


BLOCKED_KEYS = {
    "admin_controls",
    "admin_only",
    "debug_mode",
    "admin_command",
    "requires_permission",
    "server_url",
    "connection_string",
    "asset_path",
    "model_path",
    "texture_path",
    "audio_path",
    "shop_info",
    "buy_price",
    "sell_price",
    "stock_limit",
    "sku",
    "billing",
    "premium_currency",
    "real_money",
}

RIGHTS_TERMS = re.compile(
    r"(?:warcraft|ultima(?: online)?|one[ _-]?piece|tolkien|lovecraft|cthulhu|aion|sphere|xenomorph|mithril|peacebloom|silverleaf)",
    re.IGNORECASE,
)
BLOCKED_KEY_PATTERN = re.compile(
    r"(?:admin|debug|one_piece|aion|mithril|peacebloom|silverleaf|xenomorph|warcraft|ultima|tolkien|lovecraft|cthulhu|(?:^|_)(?:buy_|sell_|base_sell_)?price(?:$|_))",
    re.IGNORECASE,
)
BLOCKED_VALUE_PATTERN = re.compile(r"(?:admin_only|admin_command)", re.IGNORECASE)

FAMILY_TYPES = {
    "abilities": "ability",
    "ability": "ability",
    "classes": "class",
    "class": "class",
    "creatures": "creature",
    "item": "item",
    "items": "item",
    "monsters": "monster",
    "npcs": "npc",
    "quests": "quest",
    "race": "race",
    "races": "race",
    "spells": "spell",
}

PUBLIC_FOLDERS = {
    "ability": "abilities",
    "class": "classes",
    "item": "items",
    "lineage": "lineages",
    "race": "races",
    "racial_traits": "racial-traits",
    "social_event": "social-events",
    "treasure_maps": "treasure-maps",
    "virtues_factions": "virtues-factions",
}


def template_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "template"


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize_value(child)
            for key, child in value.items()
            if key.lower() not in BLOCKED_KEYS
            and not BLOCKED_KEY_PATTERN.search(key)
            and not (isinstance(child, str) and BLOCKED_VALUE_PATTERN.search(child))
        }
    if isinstance(value, list):
        return [
            _sanitize_value(child)
            for child in value
            if not (
                isinstance(child, str)
                and (child.lower() in BLOCKED_KEYS or BLOCKED_KEY_PATTERN.search(child))
            )
        ]
    if isinstance(value, str):
        return BLOCKED_VALUE_PATTERN.sub("adapted_reference", RIGHTS_TERMS.sub("adapted_reference", value))
    return copy.deepcopy(value)


def _replace_identity(value: Any, old_id: str, old_name: str, new_id: str, new_name: str) -> Any:
    if isinstance(value, dict):
        return {
            key: _replace_identity(child, old_id, old_name, new_id, new_name)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_replace_identity(child, old_id, old_name, new_id, new_name) for child in value]
    if not isinstance(value, str):
        return value
    if old_id and value.casefold() == old_id.casefold():
        return new_id
    if old_name and value.casefold() == old_name.casefold():
        return new_name
    result = value
    if old_id:
        result = re.sub(re.escape(old_id), new_id, result, flags=re.IGNORECASE)
    if old_name:
        result = re.sub(re.escape(old_name), new_name, result, flags=re.IGNORECASE)
    return result


def _semantic_alias(document: dict[str, Any], family: str, sequence: int) -> tuple[str, str]:
    if family == "monsters":
        descriptor = template_slug(str(document.get("category") or "monster")).replace("-", "_")
        return f"{descriptor}_creature_{sequence:04d}", f"{descriptor.replace('_', ' ').title()} Creature {sequence:04d}"
    if family == "spells":
        school = document.get("school") or document.get("spell_school") or document.get("category") or "arcane"
        descriptor = template_slug(str(school)).replace("-", "_")
        return f"{descriptor}_spell_{sequence:04d}", f"{descriptor.replace('_', ' ').title()} Spell {sequence:04d}"
    family_name = template_slug(family).replace("-", "_")
    return f"{family_name}_template_{sequence:04d}", f"{family_name.replace('_', ' ').title()} Template {sequence:04d}"


def sanitize_template(document: Any, family: str, sequence: int) -> dict[str, Any]:
    family = family.lower()
    template_type = FAMILY_TYPES.get(family, family.rstrip("s").replace("-", "_") or "template")
    if isinstance(document, list):
        family_name = template_slug(family).replace("-", "_")
        return {
            "id": f"{family_name}_catalog_{sequence:04d}",
            "template_type": f"{template_type}_catalog",
            "version": "0.1.0",
            "name": f"{family_name.replace('_', ' ').title()} Catalog {sequence:04d}",
            "entries": _sanitize_value(document),
        }
    if not isinstance(document, dict):
        raise ValueError("template root must be an object or array")

    sanitized = _sanitize_value(document)
    old_id = str(document.get("id") or document.get("item_id") or "")
    old_name = str(document.get("name") or "")
    needs_alias = family in {"monsters", "spells"} or RIGHTS_TERMS.search(old_id) or RIGHTS_TERMS.search(old_name)
    if needs_alias:
        new_id, new_name = _semantic_alias(document, family, sequence)
        sanitized = _replace_identity(sanitized, old_id, old_name, new_id, new_name)
        modifiers = {"adult", "ancient", "basic", "custom", "default", "elite", "enhanced", "greater", "lesser", "template", "young"}
        roots = [token for token in re.split(r"[^a-z0-9]+", old_id.lower()) if len(token) >= 4 and token not in modifiers]
        if roots:
            sanitized = _replace_identity(sanitized, roots[0], "", new_id, new_name)
    else:
        candidate = old_id or template_slug(old_name).replace("-", "_")
        new_id = template_slug(candidate).replace("-", "_") if candidate else _semantic_alias(document, family, sequence)[0]
        new_name = old_name or new_id.replace("_", " ").title()

    sanitized["id"] = new_id
    sanitized["name"] = new_name
    sanitized["template_type"] = template_type
    sanitized["version"] = "0.1.0"
    return sanitized


def sanitize_existing_template(document: Any) -> Any:
    return _sanitize_value(document)


def sanitize_catalogued_files(registry_root: Path, catalog_path: Path) -> dict[str, int]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    changed = 0
    for entry in entries:
        file_path = registry_root / entry["file"]
        document = json.loads(file_path.read_text(encoding="utf-8"))
        sanitized = sanitize_existing_template(document)
        if sanitized == document:
            continue
        file_path.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        entry["sha256"] = hashlib.sha256(file_path.read_bytes()).hexdigest()
        changed += 1
    if changed:
        catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"sanitized": changed}


def _hash_variants(content: bytes) -> set[str]:
    lf = content.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {
        hashlib.sha256(content).hexdigest(),
        hashlib.sha256(lf).hexdigest(),
        hashlib.sha256(crlf).hexdigest(),
    }


def export_missing_templates(
    source_root: Path,
    staging_root: Path,
    catalog_entries: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    known_hashes = {entry.get("sha256") for entry in catalog_entries if entry.get("sha256")}
    known_source_hashes = {
        entry.get("source_sha256") for entry in catalog_entries if entry.get("source_sha256")
    }
    known_source_files = {
        str(entry.get("source_file")).replace("\\", "/")
        for entry in catalog_entries
        if entry.get("source_file")
    }
    used_files = {entry.get("file") for entry in catalog_entries if entry.get("file")}
    generated = []
    covered = []
    family_sequences: dict[str, int] = {}

    source_paths = sorted(
        path
        for path in source_root.rglob("*.json")
        if "_versions" not in path.relative_to(source_root).parts
    )
    for source_path in source_paths:
        relative_source = source_path.relative_to(source_root).as_posix()
        content = source_path.read_bytes()
        raw_sha = hashlib.sha256(content).hexdigest()
        if (
            _hash_variants(content).intersection(known_hashes)
            or raw_sha in known_source_hashes
            or relative_source in known_source_files
        ):
            covered.append({"source_file": relative_source})
            continue

        family = relative_source.split("/", 1)[0]
        family_sequences[family] = family_sequences.get(family, 0) + 1
        sequence = family_sequences[family]
        document = json.loads(content.decode("utf-8"))
        sanitized = sanitize_template(document, family=family, sequence=sequence)
        base_slug = template_slug(str(sanitized["id"]))
        public_folder = PUBLIC_FOLDERS.get(family, family.replace("_", "-"))
        document_name = "schema.json" if family == "schemas" else "template.json"
        slug = base_slug
        ordinal = 2
        relative_template = f"templates/{public_folder}/{slug}/v0.1.0/{document_name}"
        while relative_template in used_files or (staging_root / relative_template).exists():
            slug = f"{base_slug}-{ordinal}"
            ordinal += 1
            relative_template = f"templates/{public_folder}/{slug}/v0.1.0/{document_name}"
        used_files.add(relative_template)

        template_path = staging_root / relative_template
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        source_text = content.decode("utf-8", errors="replace")
        expose_source_file = family not in {"monsters", "spells"} and not RIGHTS_TERMS.search(source_text)
        provenance = (
            f"Source auditée : `{relative_source}`."
            if expose_source_file
            else f"Source privée reliée par SHA-256 : `{raw_sha}`."
        )
        template_path.with_name("README.md").write_text(
            f"# {sanitized['name']} v0.1.0\n\n"
            "Statut : `experimental`.\n\n"
            f"{provenance} Les contrôles administratifs, données commerciales et chemins internes sont retirés.\n\n"
            "Aucune compatibilité client ou serveur n'est certifiée.\n",
            encoding="utf-8",
        )
        generated.append(
            {
                "source_file": relative_source,
                "source_sha256": raw_sha,
                "expose_source_file": expose_source_file,
                "name": slug,
                "kind": f"{sanitized['template_type']}-template",
                "template_file": relative_template,
            }
        )
    return {"generated": generated, "covered": covered, "rejected": []}


def promote_exports(staging_root: Path, registry_root: Path, catalog_path: Path) -> dict[str, int]:
    manifest = json.loads((staging_root / "export-manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get("entries", catalog) if isinstance(catalog, dict) else catalog
    existing_files = {entry.get("file") for entry in entries}
    promotions = []
    for item in manifest.get("generated", []):
        template_file = item["template_file"]
        source_template = staging_root / template_file
        source_version_dir = source_template.parent
        target_version_dir = registry_root / Path(template_file).parent
        if template_file in existing_files or target_version_dir.exists():
            raise FileExistsError(f"promotion collision: {template_file}")
        entry = {
            "name": item["name"],
            "kind": item["kind"],
            "version": "0.1.0",
            "status": "experimental",
            "file": template_file,
            "sha256": hashlib.sha256(source_template.read_bytes()).hexdigest(),
            "compatibility": [],
            "validation_profile": "legacy-unvalidated",
            "contract_version": None,
        }
        if item["expose_source_file"]:
            entry["source_file"] = item["source_file"]
        else:
            entry["source_sha256"] = item["source_sha256"]
        promotions.append((source_version_dir, target_version_dir, entry))

    copied = []
    try:
        for source_version_dir, target_version_dir, entry in promotions:
            shutil.copytree(source_version_dir, target_version_dir)
            copied.append(target_version_dir)
            entries.append(entry)
        catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        for target in reversed(copied):
            shutil.rmtree(target)
        raise
    return {"promoted": len(promotions)}
