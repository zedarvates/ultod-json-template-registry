from __future__ import annotations

from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any

from scripts.pilot_contracts import MigrationResult, normalize_slug
from scripts.template_contract import compute_spec_checksum


COHORT_SIX_FAMILIES = ("masterpieces", "prologues", "skillclass", "virtues-factions")
STRICT_FAMILIES = ("masterpieces", "skillclass")
KIND_BY_FAMILY = {"masterpieces": "masterpiece-template", "skillclass": "skillclass-template"}


def _path_slug(path: str) -> str:
    return normalize_slug(PurePosixPath(path.replace("\\", "/")).parts[-3])


def candidate_slug(source_file: str, document: Any) -> str:
    if isinstance(document, dict) and isinstance(document.get("id"), str):
        return normalize_slug(document["id"])
    return _path_slug(source_file)


def _text(value: Any, maximum=100, *, tag=False):
    if not isinstance(value, str) or not (value := value.strip()) or len(value) > maximum:
        return None
    return normalize_slug(value) if tag else value


def convert_legacy(family: str, source_file: str, document: Any, collisions: set[str]) -> MigrationResult:
    slug = candidate_slug(source_file, document)
    if family == "virtues-factions":
        return MigrationResult(source_file, family, slug, "legacy-only-authoritative", ("runtime-points-tiers-rewards-and-buffs",), None, None)
    if slug in collisions:
        return MigrationResult(source_file, family, slug, "manual-review", ("normalized-slug-collision",), None, None)
    if family == "prologues":
        return MigrationResult(source_file, family, slug, "legacy-only-narrative", ("narrative-beats-and-outcomes",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    name = _text(document.get("name"))
    if name is None:
        return MigrationResult(source_file, family, slug, "manual-review", ("missing-display-name",), None, None)
    spec = {"display_name": name}
    if family == "masterpieces":
        profession = _text(document.get("profession"), 64, tag=True)
        if profession is not None:
            spec["profession_tag"] = profession
    target = f"templates/{family}/{slug}/v1.0.0/template.json"
    result = MigrationResult(source_file, family, slug, "migrated", (), target, None)
    strict = {
        "$schema": f"../../../schemas/{family}/v1.0.0/schema.json", "contract_version": "1.0.0",
        "id": f"{family}:{slug}", "slug": slug, "family": family, "version": "1.0.0",
        "authority": "declarative", "intended_consumers": ["llm-pipeline"], "compatibility": [],
        "dependencies": [], "spec_checksum": compute_spec_checksum(spec), "spec": spec,
    }
    return replace(result, document=strict)


def family_schema(family: str):
    properties = {"display_name": {"type": "string", "minLength": 1, "maxLength": 100}}
    if family == "masterpieces":
        properties["profession_tag"] = {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64}
    elif family != "skillclass":
        raise ValueError(family)
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"https://ultimateodycer.com/schemas/{family}/1.0.0", "title": f"Ultimate Odycer {family} Template v1", "allOf": [{"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"}, {"properties": {"spec": {"type": "object", "required": ["display_name"], "properties": properties, "additionalProperties": False}}}]}
