from __future__ import annotations

from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any

from scripts.pilot_contracts import MigrationResult, normalize_slug
from scripts.template_contract import compute_spec_checksum


COHORT_FOUR_FAMILIES = ("npcs", "gods", "guilds", "sects", "lineages", "racial-traits")
STRICT_FAMILIES = ("npcs", "gods", "sects", "lineages", "racial-traits")
KIND_BY_FAMILY = {
    "npcs": "npc-template", "gods": "god-template", "sects": "sect-template",
    "lineages": "lineage-template", "racial-traits": "racial-trait-template",
}
_NON_SEMANTIC_MARKERS = ("template", "original", "adapted-reference")


def _path_slug(path: str) -> str:
    return normalize_slug(PurePosixPath(path.replace("\\", "/")).parts[-3])


def _text(value: Any, maximum: int = 100, *, tag: bool = False) -> str | None:
    if not isinstance(value, str) or not (value := value.strip()) or len(value) > maximum:
        return None
    return normalize_slug(value) if tag else value


def candidate_slug(family: str, source_file: str, document: Any) -> str:
    if isinstance(document, dict) and isinstance(document.get("id"), str):
        return normalize_slug(document["id"])
    return _path_slug(source_file)


def _spec(family: str, document: dict[str, Any]) -> dict[str, Any] | None:
    name = _text(document.get("name"))
    if name is None:
        return None
    spec: dict[str, Any] = {"display_name": name}
    mappings = {
        "npcs": (("category", "category_tag"), ("rarity", "rarity_tag"), ("npc_type", "npc_kind")),
        "gods": (("domain", "domain_tag"), ("alignment", "alignment_tag")),
        "sects": (("school", "school_tag"), ("type", "sect_kind")),
        "lineages": (("rarity", "rarity_tag"),),
        "racial-traits": (("category", "category_tag"), ("rarity", "rarity_tag")),
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
    if family == "guilds":
        return MigrationResult(source_file, family, slug, "legacy-only-authoritative", ("permissions-economy-or-standing",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    if family == "gods" and "relic_template" in document:
        return MigrationResult(source_file, family, slug, "legacy-only-authoritative", ("runtime-relic-template",), None, None)
    identity = " ".join(str(document.get(key, "")) for key in ("id", "name")).lower().replace("_", "-")
    if any(marker in slug or marker in identity for marker in _NON_SEMANTIC_MARKERS):
        return MigrationResult(source_file, family, slug, "manual-review", ("nonsemantic-identity",), None, None)
    spec = _spec(family, document)
    if spec is None:
        return MigrationResult(source_file, family, slug, "manual-review", ("missing-declarative-identity",), None, None)
    target = f"templates/{family}/{slug}/v1.0.0/template.json"
    result = MigrationResult(source_file, family, slug, "migrated", (), target, None)
    strict = {
        "$schema": f"../../../schemas/{family}/v1.0.0/schema.json",
        "contract_version": "1.0.0", "id": f"{family}:{slug}", "slug": slug,
        "family": family, "version": "1.0.0", "authority": "declarative",
        "intended_consumers": ["llm-pipeline"], "compatibility": [], "dependencies": [],
        "spec_checksum": compute_spec_checksum(spec), "spec": spec,
    }
    return replace(result, document=strict)


def family_schema(family: str) -> dict[str, Any]:
    tag = {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64}
    properties: dict[str, Any] = {"display_name": {"type": "string", "minLength": 1, "maxLength": 100}}
    fields = {
        "npcs": ("category_tag", "rarity_tag", "npc_kind"),
        "gods": ("domain_tag", "alignment_tag"),
        "sects": ("school_tag", "sect_kind"),
        "lineages": ("rarity_tag",),
        "racial-traits": ("category_tag", "rarity_tag"),
    }[family]
    properties.update({field: tag for field in fields})
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://ultimateodycer.com/schemas/{family}/1.0.0",
        "title": f"Ultimate Odycer {family} Template v1",
        "allOf": [
            {"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"},
            {"properties": {"spec": {"type": "object", "required": ["display_name"], "properties": properties, "additionalProperties": False}}},
        ],
    }
