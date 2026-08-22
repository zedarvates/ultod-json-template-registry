from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable


KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


@dataclass(frozen=True)
class TemplatePath:
    family: str
    slug: str
    version: str


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value):
    raise ValueError(f"non-finite JSON number: {value}")


def decode_json_bytes(data: bytes) -> Any:
    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_non_finite,
    )


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def compute_spec_checksum(spec: Any) -> str:
    digest = hashlib.sha256(canonical_json_bytes(spec)).hexdigest()
    return f"sha256:{digest}"


def validate_document_limits(value: Any, content_size: int) -> list[str]:
    errors = []
    if content_size > 262_144:
        errors.append("document exceeds 262144 bytes")

    def visit(child: Any, depth: int, path: str):
        if depth > 32:
            errors.append(f"{path}: nesting exceeds 32 levels")
            return
        if isinstance(child, str) and len(child) > 4096:
            errors.append(f"{path}: string exceeds 4096 characters")
        elif isinstance(child, list):
            if len(child) > 1024:
                errors.append(f"{path}: array exceeds 1024 items")
            for index, item in enumerate(child):
                visit(item, depth + 1, f"{path}/{index}")
        elif isinstance(child, dict):
            if len(child) > 256:
                errors.append(f"{path}: object exceeds 256 properties")
            for key, item in child.items():
                visit(item, depth + 1, f"{path}/{key}")

    visit(value, 0, "$")
    return sorted(set(errors))


def parse_strict_template_path(path: str) -> TemplatePath:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    if len(parts) != 5 or parts[0] != "templates" or parts[4] != "template.json":
        raise ValueError(
            "strict template path must be templates/<family>/<slug>/v<semver>/template.json"
        )
    family, slug, version_dir = parts[1], parts[2], parts[3]
    if not KEBAB.fullmatch(family) or not KEBAB.fullmatch(slug):
        raise ValueError("family and slug must use kebab-case")
    if not version_dir.startswith("v") or not SEMVER.fullmatch(version_dir[1:]):
        raise ValueError("version directory must use v<semver>")
    return TemplatePath(family=family, slug=slug, version=version_dir[1:])


def validate_envelope_identity(path: str, document: dict[str, Any]) -> list[str]:
    parsed = parse_strict_template_path(path)
    expected = {
        "family": parsed.family,
        "slug": parsed.slug,
        "id": f"{parsed.family}:{parsed.slug}",
        "version": parsed.version,
    }
    return [
        f"{key} must equal {value}"
        for key, value in expected.items()
        if document.get(key) != value
    ]


def validate_schema_identity(path: str, document: dict[str, Any]) -> list[str]:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    if len(parts) != 5 or parts[:2] != ("templates", "schemas") or parts[4] != "schema.json":
        return ["strict schema path must be templates/schemas/<family>/v<semver>/schema.json"]
    family, version_dir = parts[2], parts[3]
    if (
        not KEBAB.fullmatch(family)
        or not version_dir.startswith("v")
        or not SEMVER.fullmatch(version_dir[1:])
    ):
        return ["strict schema family and version path are invalid"]
    expected = f"https://ultimateodycer.com/schemas/{family}/{version_dir[1:]}"
    return [] if document.get("$id") == expected else [f"$id must equal {expected}"]


def load_schema_store(root: Path):
    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    for path in sorted((root / "templates/schemas").rglob("schema.json")):
        document = decode_json_bytes(path.read_bytes())
        schema_id = document.get("$id") if isinstance(document, dict) else None
        if not isinstance(schema_id, str):
            continue
        schemas[path.relative_to(root).as_posix()] = document
        registry = registry.with_resource(schema_id, Resource.from_contents(document))
    return schemas, registry


def _schema_refs(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                yield child
            yield from _schema_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _schema_refs(child)


def validate_schema_references(root: Path, schema_file: str) -> list[str]:
    schemas, _ = load_schema_store(root)
    schema = schemas.get(schema_file)
    if schema is None:
        return [f"schema file not found: {schema_file}"]
    known_ids = {
        document["$id"]
        for document in schemas.values()
        if isinstance(document.get("$id"), str)
    }
    errors = []
    for reference in _schema_refs(schema):
        base = reference.split("#", 1)[0]
        if base and base not in known_ids:
            errors.append(f"unresolved local schema reference: {reference}")
    return sorted(set(errors))


def validate_with_schema(root: Path, schema_file: str, document: Any) -> list[str]:
    schemas, registry = load_schema_store(root)
    schema = schemas.get(schema_file)
    if schema is None:
        return [f"schema file not found: {schema_file}"]
    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(
            schema,
            registry=registry,
            format_checker=FormatChecker(),
        )
        return [
            f"{'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
            for error in sorted(
                validator.iter_errors(document), key=lambda item: list(item.absolute_path)
            )
        ]
    except (SchemaError, Unresolvable) as error:
        return [f"schema resolution failed: {error}"]
