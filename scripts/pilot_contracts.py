from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import PurePosixPath
from typing import Any, Iterable

from scripts.template_contract import compute_spec_checksum

PILOT_FAMILIES = ("classes", "races", "items", "spells", "monsters")
FIELD_MAP = {
    "classes": {"name": "display_name", "primary_resource": "resource_kind"},
    "races": {"name": "display_name", "category": "category", "rarity": "rarity", "faction": "faction_tag"},
    "items": {"name": "display_name", "category": "category", "rarity": "rarity", "item_type": "item_kind", "sub_type": "subtype"},
    "spells": {"name": "display_name", "school": "school", "rarity": "rarity", "spell_type": "spell_kind", "target_type": "target_kind"},
    "monsters": {"name": "display_name", "category": "category", "rarity": "rarity"},
}
SPEC_FIELDS = {
    family: tuple(target for source, target in fields.items() if source != "name")
    for family, fields in FIELD_MAP.items()
}
_NON_SLUG = re.compile(r"[^a-z0-9]+")

@dataclass(frozen=True)
class MigrationResult:
    source_file: str
    family: str
    slug: str
    disposition: str
    reason_codes: tuple[str, ...]
    target_file: str | None
    document: dict[str, Any] | None

def normalize_slug(value: str) -> str:
    value = _NON_SLUG.sub("-", value.strip().lower()).strip("-")
    if not value or len(value) > 64:
        raise ValueError("invalid slug")
    return value

def _path_slug(path: str) -> str:
    return normalize_slug(PurePosixPath(path.replace("\\", "/")).parts[-3])

def find_slug_collisions(paths: Iterable[str]) -> set[str]:
    counts = {}
    for path in paths:
        slug = _path_slug(path)
        counts[slug] = counts.get(slug, 0) + 1
    return {slug for slug, count in counts.items() if count > 1}

def _text(value: Any, maximum: int, tag: bool = False):
    if not isinstance(value, str) or not (value := value.strip()) or len(value) > maximum:
        return None
    return normalize_slug(value) if tag else value

def convert_legacy(family, source_file, document, colliding_slugs):
    slug = _path_slug(source_file)
    if slug in colliding_slugs:
        return MigrationResult(source_file, family, slug, "manual-review", ("normalized-slug-collision",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    name = _text(document.get("name"), 100)
    if name is None:
        return MigrationResult(source_file, family, slug, "manual-review", ("missing-display-name",), None, None)
    spec = {"display_name": name}
    dropped = []
    for source, target in FIELD_MAP[family].items():
        if source == "name" or source not in document:
            continue
        value = _text(document[source], 64, True)
        if value is None:
            dropped.append(f"invalid-{source}")
        else:
            spec[target] = value
    result = MigrationResult(source_file, family, slug, "migrated", tuple(sorted(dropped)), f"templates/{family}/{slug}/v1.0.0/template.json", None)
    doc = {
        "$schema": f"../../../schemas/{family}/v1.0.0/schema.json",
        "contract_version": "1.0.0", "id": f"{family}:{slug}", "slug": slug,
        "family": family, "version": "1.0.0", "authority": "declarative",
        "intended_consumers": ["llm-pipeline", "zig-server-v2"], "compatibility": [],
        "dependencies": [], "spec_checksum": compute_spec_checksum(spec), "spec": spec,
    }
    return replace(result, document=doc)

def family_schema(family: str):
    properties = {"display_name": {"type": "string", "minLength": 1, "maxLength": 100}}
    for field in SPEC_FIELDS[family]:
        properties[field] = {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://ultimateodycer.com/schemas/{family}/1.0.0",
        "title": f"Ultimate Odycer {family} Template v1",
        "allOf": [
            {"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"},
            {"properties": {"spec": {"type": "object", "required": ["display_name"], "properties": properties, "additionalProperties": False}}},
        ],
    }
