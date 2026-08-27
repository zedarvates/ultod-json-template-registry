from __future__ import annotations

from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any

from scripts.pilot_contracts import MigrationResult, normalize_slug
from scripts.template_contract import compute_spec_checksum


COHORT_THREE_FAMILIES = ("abilities", "professions", "skills", "talent")
KIND_BY_FAMILY = {
    "abilities": "ability-template",
    "professions": "profession-template",
    "skills": "skill-template",
    "talent": "talent-template",
}
_AUTHORITATIVE_PROFESSION_KEYS = {
    "achievement_system", "advancement_system", "market_integration", "profession_synergies",
}
_NON_SEMANTIC_MARKERS = ("template", "original", "adapted-reference")


def _path_slug(path: str) -> str:
    return normalize_slug(PurePosixPath(path.replace("\\", "/")).parts[-3])


def _text(value: Any, maximum: int = 100, *, tag: bool = False) -> str | None:
    if not isinstance(value, str) or not (value := value.strip()) or len(value) > maximum:
        return None
    return normalize_slug(value) if tag else value


def candidate_slug(family: str, source_file: str, document: Any) -> str:
    if isinstance(document, dict):
        value = document.get("id")
        if isinstance(value, str) and value.strip():
            return normalize_slug(value)
    return _path_slug(source_file)


def _display_name(family: str, document: dict[str, Any]) -> str | None:
    if family == "professions":
        return _text(document.get("display_name")) or _text(document.get("name"))
    return _text(document.get("name"))


def _spec(family: str, document: dict[str, Any]) -> dict[str, Any] | None:
    name = _display_name(family, document)
    if name is None:
        return None
    spec: dict[str, Any] = {"display_name": name}
    mappings = {
        "abilities": (("ability_type", "ability_kind"), ("category", "category_tag"), ("target_type", "target_kind")),
        "professions": (("category", "category_tag"), ("subcategory", "subcategory_tag")),
        "skills": (("category", "category_tag"), ("subcategory", "subcategory_tag"), ("skill_type", "skill_kind")),
        "talent": (("type", "talent_kind"),),
    }[family]
    for source, target in mappings:
        value = _text(document.get(source), 64, tag=True)
        if value is not None and value not in (family.rstrip("s"), family):
            spec[target] = value
    return spec


def convert_legacy(family: str, source_file: str, document: Any, colliding_slugs: set[str]) -> MigrationResult:
    slug = candidate_slug(family, source_file, document)
    if slug in colliding_slugs:
        return MigrationResult(source_file, family, slug, "manual-review", ("normalized-slug-collision",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    if (
        family == "professions"
        and _AUTHORITATIVE_PROFESSION_KEYS.intersection(document)
        and not any(key in document for key in ("profession", "profession_id", "display_name"))
    ):
        return MigrationResult(source_file, family, slug, "legacy-only-authoritative", ("runtime-progression-or-market-system",), None, None)
    identity_text = " ".join(str(document.get(key, "")) for key in ("id", "name", "display_name", "profession")).lower().replace("_", "-")
    if slug.startswith("uo-") or any(marker in slug or marker in identity_text for marker in _NON_SEMANTIC_MARKERS):
        return MigrationResult(source_file, family, slug, "manual-review", ("nonsemantic-or-adapted-identity",), None, None)
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
        "abilities": ("ability_kind", "category_tag", "target_kind"),
        "professions": ("category_tag", "subcategory_tag"),
        "skills": ("category_tag", "subcategory_tag", "skill_kind"),
        "talent": ("talent_kind",),
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
