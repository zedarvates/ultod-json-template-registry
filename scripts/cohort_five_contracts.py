from __future__ import annotations

from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any

from scripts.pilot_contracts import MigrationResult, normalize_slug
from scripts.template_contract import compute_spec_checksum


COHORT_FIVE_FAMILIES = ("bosses", "creatures", "events", "mount", "quests", "rifts", "styles", "tournaments", "treasure-maps")
STRICT_FAMILIES = ("bosses", "creatures", "events", "mount", "quests", "styles", "tournaments")
KIND_BY_FAMILY = {family: f"{family.rstrip('s')}-template" for family in STRICT_FAMILIES}
KIND_BY_FAMILY.update({"bosses": "boss-template", "creatures": "creature-template", "tournaments": "tournament-template"})
_NON_SEMANTIC_MARKERS = ("template", "example", "original", "adapted-reference")


def _path_slug(path: str) -> str:
    return normalize_slug(PurePosixPath(path.replace("\\", "/")).parts[-3])


def _text(value: Any, maximum: int = 100, *, tag: bool = False) -> str | None:
    if not isinstance(value, str) or not (value := value.strip()) or len(value) > maximum:
        return None
    return normalize_slug(value) if tag else value


def candidate_slug(family: str, source_file: str, document: Any) -> str:
    if not isinstance(document, dict):
        return _path_slug(source_file)
    keys = {
        "bosses": ("id",), "creatures": ("species_id", "id"), "events": ("event_id",),
        "mount": ("id",), "quests": (), "rifts": ("rift_id",), "styles": ("style_id",),
        "tournaments": ("tournament_id",), "treasure-maps": ("map_id",),
    }[family]
    for key in keys:
        if isinstance(document.get(key), str):
            return normalize_slug(document[key])
    return _path_slug(source_file)


def _display_name(family: str, document: dict[str, Any]) -> str | None:
    keys = {
        "creatures": ("species_name", "name"), "events": ("event_name", "name"),
        "rifts": ("rift_name",), "tournaments": ("tournament_name", "name"),
        "treasure-maps": ("title", "name"),
    }.get(family, ("name",))
    for key in keys:
        value = _text(document.get(key))
        if value is not None:
            return value
    return None


def _spec(family: str, document: dict[str, Any]) -> dict[str, Any] | None:
    name = _display_name(family, document)
    if name is None:
        return None
    spec: dict[str, Any] = {"display_name": name}
    mappings = {
        "bosses": (), "creatures": (("chemistry", "chemistry_tag"),),
        "events": (("event_type", "event_kind"), ("rarity", "rarity_tag")),
        "mount": (("rarity", "rarity_tag"),),
        "quests": (("difficulty", "difficulty_tag"),),
        "styles": (("applies_to", "applies_to_tag"),),
        "tournaments": (("tournament_type", "tournament_kind"), ("rarity", "rarity_tag")),
    }[family]
    for source, target in mappings:
        value = _text(document.get(source), 64, tag=True)
        if value is not None:
            spec[target] = value
    return spec


def convert_legacy(family: str, source_file: str, document: Any, colliding_slugs: set[str]) -> MigrationResult:
    slug = candidate_slug(family, source_file, document)
    if slug in colliding_slugs:
        return MigrationResult(source_file, family, slug, "manual-review", ("normalized-slug-collision",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    identity = " ".join(str(value) for value in (slug, _display_name(family, document) or "")).lower().replace("_", "-")
    if any(marker in identity for marker in _NON_SEMANTIC_MARKERS):
        return MigrationResult(source_file, family, slug, "manual-review", ("nonsemantic-or-fixture-identity",), None, None)
    if family not in STRICT_FAMILIES:
        return MigrationResult(source_file, family, slug, "manual-review", ("no-reviewed-declarative-identity",), None, None)
    spec = _spec(family, document)
    if spec is None:
        return MigrationResult(source_file, family, slug, "manual-review", ("missing-declarative-identity",), None, None)
    target = f"templates/{family}/{slug}/v1.0.0/template.json"
    result = MigrationResult(source_file, family, slug, "migrated", (), target, None)
    strict = {
        "$schema": f"../../../schemas/{family}/v1.0.0/schema.json", "contract_version": "1.0.0",
        "id": f"{family}:{slug}", "slug": slug, "family": family, "version": "1.0.0",
        "authority": "declarative", "intended_consumers": ["llm-pipeline"], "compatibility": [],
        "dependencies": [], "spec_checksum": compute_spec_checksum(spec), "spec": spec,
    }
    return replace(result, document=strict)


def family_schema(family: str) -> dict[str, Any]:
    tag = {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64}
    properties: dict[str, Any] = {"display_name": {"type": "string", "minLength": 1, "maxLength": 100}}
    fields = {
        "bosses": (), "creatures": ("chemistry_tag",), "events": ("event_kind", "rarity_tag"),
        "mount": ("rarity_tag",), "quests": ("difficulty_tag",), "styles": ("applies_to_tag",),
        "tournaments": ("tournament_kind", "rarity_tag"),
    }[family]
    properties.update({field: tag for field in fields})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"https://ultimateodycer.com/schemas/{family}/1.0.0", "title": f"Ultimate Odycer {family} Template v1", "allOf": [{"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"}, {"properties": {"spec": {"type": "object", "required": ["display_name"], "properties": properties, "additionalProperties": False}}}]}
