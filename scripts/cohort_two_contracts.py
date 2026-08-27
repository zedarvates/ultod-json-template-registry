from __future__ import annotations

from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any

from scripts.pilot_contracts import MigrationResult, normalize_slug
from scripts.template_contract import compute_spec_checksum


COHORT_TWO_FAMILIES = ("cities", "city-layouts", "dungeons", "locations", "planets", "solar-systems")
STRICT_FAMILIES = ("dungeons", "locations", "planets", "solar-systems")
KIND_BY_FAMILY = {
    "dungeons": "dungeon-template",
    "locations": "location-template",
    "planets": "planet-template",
    "solar-systems": "solar-system-template",
}
_NON_SEMANTIC_MARKERS = ("template", "demo-", "grammar-generated")


def _path_slug(path: str) -> str:
    return normalize_slug(PurePosixPath(path.replace("\\", "/")).parts[-3])


def _text(value: Any, maximum: int = 100, *, tag: bool = False) -> str | None:
    if not isinstance(value, str) or not (value := value.strip()) or len(value) > maximum:
        return None
    return normalize_slug(value) if tag else value


def candidate_slug(family: str, source_file: str, document: Any) -> str:
    if family == "locations" and isinstance(document, dict):
        value = document.get("location_id")
        if isinstance(value, str):
            return normalize_slug(value)
    return _path_slug(source_file)


def _dungeon_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("name"))
    if name is None:
        return None
    spec: dict[str, Any] = {"display_name": name}
    theme = _text(document.get("theme"), 64, tag=True)
    if theme is not None:
        spec["theme_tag"] = theme
    return spec


def _location_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("name"))
    kind = _text(document.get("location_type"), 64, tag=True)
    if name is None or kind is None:
        return None
    spec: dict[str, Any] = {"display_name": name, "location_kind": kind}
    for source, target in (("size", "size_tag"), ("rarity", "rarity_tag")):
        value = _text(document.get(source), 64, tag=True)
        if value is not None:
            spec[target] = value
    return spec


def _planet_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("name"))
    if name is None:
        return None
    spec: dict[str, Any] = {"display_name": name}
    planet_types = document.get("planet_types")
    if isinstance(planet_types, dict):
        for source, target in (("primary", "primary_type_tag"), ("secondary", "secondary_type_tag")):
            value = _text(planet_types.get(source), 64, tag=True)
            if value is not None:
                spec[target] = value
    return spec


def _solar_system_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("name"))
    return {"display_name": name} if name is not None else None


def convert_legacy(family: str, source_file: str, document: Any, colliding_slugs: set[str]) -> MigrationResult:
    slug = candidate_slug(family, source_file, document)
    if slug in colliding_slugs:
        return MigrationResult(source_file, family, slug, "manual-review", ("normalized-slug-collision",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    if family in ("cities", "city-layouts"):
        return MigrationResult(
            source_file,
            family,
            slug,
            "legacy-only-authoritative",
            ("runtime-layout-assets-and-metrics",),
            None,
            None,
        )
    name_tag = normalize_slug(document.get("name", "")) if isinstance(document.get("name"), str) else ""
    if any(marker in slug or marker in name_tag for marker in _NON_SEMANTIC_MARKERS):
        return MigrationResult(source_file, family, slug, "manual-review", ("nonsemantic-or-fixture-identity",), None, None)
    builders = {
        "dungeons": _dungeon_spec,
        "locations": _location_spec,
        "planets": _planet_spec,
        "solar-systems": _solar_system_spec,
    }
    spec = builders[family](document)
    if spec is None:
        return MigrationResult(source_file, family, slug, "manual-review", ("missing-declarative-identity",), None, None)
    target = f"templates/{family}/{slug}/v1.0.0/template.json"
    result = MigrationResult(source_file, family, slug, "migrated", (), target, None)
    strict = {
        "$schema": f"../../../schemas/{family}/v1.0.0/schema.json",
        "contract_version": "1.0.0",
        "id": f"{family}:{slug}",
        "slug": slug,
        "family": family,
        "version": "1.0.0",
        "authority": "declarative",
        "intended_consumers": ["llm-pipeline"],
        "compatibility": [],
        "dependencies": [],
        "spec_checksum": compute_spec_checksum(spec),
        "spec": spec,
    }
    return replace(result, document=strict)


def family_schema(family: str) -> dict[str, Any]:
    tag = {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64}
    properties: dict[str, Any] = {
        "display_name": {"type": "string", "minLength": 1, "maxLength": 100}
    }
    required = ["display_name"]
    if family == "dungeons":
        properties["theme_tag"] = tag
    elif family == "locations":
        properties.update({"location_kind": tag, "size_tag": tag, "rarity_tag": tag})
        required.append("location_kind")
    elif family == "planets":
        properties.update({"primary_type_tag": tag, "secondary_type_tag": tag})
    elif family != "solar-systems":
        raise ValueError(f"unsupported strict family: {family}")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://ultimateodycer.com/schemas/{family}/1.0.0",
        "title": f"Ultimate Odycer {family} Template v1",
        "allOf": [
            {"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"},
            {"properties": {"spec": {"type": "object", "required": required, "properties": properties, "additionalProperties": False}}},
        ],
    }
