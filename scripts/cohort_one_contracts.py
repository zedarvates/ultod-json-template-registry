from __future__ import annotations

from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any

from scripts.pilot_contracts import MigrationResult, normalize_slug
from scripts.template_contract import compute_spec_checksum


COHORT_ONE_FAMILIES = ("achievements", "avatars", "biomes", "currencies", "names")
KIND_BY_FAMILY = {
    "avatars": "avatar-template",
    "biomes": "biome-template",
    "currencies": "currency-template",
    "names": "name-template",
}
_NON_SEMANTIC_MARKERS = ("adapted-reference", "original", "template-")


def _path_slug(path: str) -> str:
    return normalize_slug(PurePosixPath(path.replace("\\", "/")).parts[-3])


def candidate_slug(family: str, source_file: str, document: Any) -> str:
    if isinstance(document, dict) and family == "currencies":
        value = document.get("name")
    elif isinstance(document, dict) and family == "names":
        value = document.get("culture")
    else:
        return _path_slug(source_file)
    if not isinstance(value, str):
        return _path_slug(source_file)
    return normalize_slug(value)


def _text(value: Any, maximum: int = 100, *, tag: bool = False) -> str | None:
    if not isinstance(value, str) or not (value := value.strip()) or len(value) > maximum:
        return None
    return normalize_slug(value) if tag else value


def _tag_list(value: Any, maximum: int = 32) -> list[str] | None:
    if not isinstance(value, list) or len(value) > maximum:
        return None
    tags = []
    for item in value:
        tag = _text(item, 64, tag=True)
        if tag is None:
            return None
        if tag not in tags:
            tags.append(tag)
    return tags


def _avatar_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("name"))
    if name is None:
        return None
    spec: dict[str, Any] = {"display_name": name}
    style = document.get("style_profile")
    if isinstance(style, dict):
        for source, target in (
            ("species", "species_tag"),
            ("variant", "variant_tag"),
            ("body_frame", "body_frame_tag"),
        ):
            value = _text(style.get(source), 64, tag=True)
            if value is not None:
                spec[target] = value
    return spec


def _biome_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("name"))
    if name is None:
        return None
    spec: dict[str, Any] = {"display_name": name}
    for source, target in (("category", "category_tag"), ("climate", "climate_tag")):
        value = _text(document.get(source), 64, tag=True)
        if value is not None:
            spec[target] = value
    terrain_tags = _tag_list(document.get("terrain_types"))
    if terrain_tags:
        spec["terrain_tags"] = terrain_tags
    return spec


def _currency_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("display_name"))
    code = _text(document.get("name"), 64, tag=True)
    if name is None or code is None:
        return None
    return {"display_name": name, "currency_code": code}


def _name_spec(document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("display_name"))
    culture = _text(document.get("culture"), 64, tag=True)
    if name is None or culture is None:
        return None
    return {"display_name": name, "culture_tag": culture}


def convert_legacy(family: str, source_file: str, document: Any, colliding_slugs: set[str]) -> MigrationResult:
    slug = candidate_slug(family, source_file, document)
    if slug in colliding_slugs:
        return MigrationResult(source_file, family, slug, "manual-review", ("normalized-slug-collision",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    if family == "achievements":
        return MigrationResult(
            source_file,
            family,
            slug,
            "legacy-only-authoritative",
            ("runtime-progression-and-rewards",),
            None,
            None,
        )
    if any(marker in slug for marker in _NON_SEMANTIC_MARKERS):
        return MigrationResult(source_file, family, slug, "manual-review", ("nonsemantic-identity",), None, None)
    builders = {
        "avatars": _avatar_spec,
        "biomes": _biome_spec,
        "currencies": _currency_spec,
        "names": _name_spec,
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
    if family == "avatars":
        properties.update({key: tag for key in ("species_tag", "variant_tag", "body_frame_tag")})
    elif family == "biomes":
        properties.update({"category_tag": tag, "climate_tag": tag})
        properties["terrain_tags"] = {"type": "array", "items": tag, "uniqueItems": True, "maxItems": 32}
    elif family == "currencies":
        properties["currency_code"] = tag
    elif family == "names":
        properties["culture_tag"] = tag
    else:
        raise ValueError(f"unsupported strict family: {family}")
    required = {
        "avatars": ["display_name"],
        "biomes": ["display_name"],
        "currencies": ["display_name", "currency_code"],
        "names": ["display_name", "culture_tag"],
    }[family]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://ultimateodycer.com/schemas/{family}/1.0.0",
        "title": f"Ultimate Odycer {family} Template v1",
        "allOf": [
            {"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"},
            {"properties": {"spec": {"type": "object", "required": required, "properties": properties, "additionalProperties": False}}},
        ],
    }
