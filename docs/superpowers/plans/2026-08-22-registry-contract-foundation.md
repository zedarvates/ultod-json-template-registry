# Registry Contract Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the strict Template Contract v1 foundation, dual-profile catalog, deterministic checksums, reference validation, and CI gates without changing any published legacy template bytes.

**Architecture:** Keep every existing template on the `legacy-unvalidated` profile while introducing reusable Python contract primitives, a Draft 2020-12 common envelope schema, exact versioned references, and a fail-closed strict-v1 validation path. The registry CLI remains the single orchestration entry point; schema handling, catalog graph handling, and report formatting live in focused modules.

**Tech Stack:** Python 3.13, standard-library `unittest`, `jsonschema==4.26.0`, Draft 2020-12 JSON Schema, GitHub Actions, JSON.

**Spec:** `docs/superpowers/specs/2026-08-21-template-contract-v1-design.md`

## Global Constraints

- Published `v0.1.0` template and schema files remain byte-identical.
- V1 JSON property names use ASCII `snake_case`; directory names and slugs use ASCII `kebab-case`.
- Every v1 ID is `<family>:<slug>` and every dependency is `<family>:<slug>@<semver>`.
- `authority` has the single v1 value `declarative`.
- V1 template entries use `validation_profile: "strict-v1"`; v1 schema entries use `validation_profile: "strict-schema-v1"`; historical entries use `validation_profile: "legacy-unvalidated"`.
- A strict consumer never selects an implicit latest version and never falls back by fuzzy name.
- The catalog SHA-256 covers complete file bytes; `spec_checksum` covers canonical JSON for `spec` only.
- Compatibility remains empty without exact versioned evidence.
- No server code, private path, runtime balance, production data, commercial data, or unaudited asset path enters this public repository.
- This plan does not migrate a content family and does not modify the Zig server.

## File Structure

| File | Responsibility |
| --- | --- |
| `requirements-dev.txt` | Pin the JSON Schema implementation used locally and in CI. |
| `.gitignore` | Exclude Python cache and local validation-report artifacts. |
| `scripts/template_contract.py` | Canonical JSON, checksums, naming, path identity, and schema-store validation. |
| `scripts/registry_catalog.py` | Catalog indexing, exact references, aliases, dependency closure, and cycle checks. |
| `scripts/validation_report.py` | Stable issue/report types and machine-readable JSON output. |
| `scripts/validate_registry.py` | Orchestrate legacy and strict-v1 profiles; expose the CLI. |
| `scripts/migrate_catalog_v2.py` | Deterministically add legacy metadata without touching template files. |
| `scripts/build_registry.py` | Emit dual-profile metadata for later exports and promotions. |
| `templates/schemas/template-contract/v1.0.0/schema.json` | Common strict-v1 envelope schema. |
| `templates/catalog.json` | Catalog v2 with explicit legacy profiles and an empty alias list. |
| `TEMPLATE-SPEC.md` | Normative dual-profile contract for contributors and consumers. |
| `README.md` | Briefly explain legacy versus strict-v1 status. |
| `tests/test_template_contract.py` | Contract primitive and schema-store tests. |
| `tests/test_registry_catalog.py` | Exact-reference and graph tests. |
| `tests/test_validate_registry.py` | End-to-end dual-profile validator tests. |
| `tests/test_build_registry.py` | Catalog migration and builder regression tests. |

---

### Task 1: Canonical contract primitives and reproducible dependency

**Files:**
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `scripts/template_contract.py`
- Create: `tests/test_template_contract.py`
- Modify: `.github/workflows/validate.yml`

**Interfaces:**
- Consumes: Python dictionaries loaded from JSON and strict template paths relative to the repository root.
- Produces: `decode_json_bytes(data: bytes) -> Any`, `canonical_json_bytes(value: Any) -> bytes`, `compute_spec_checksum(spec: Any) -> str`, `validate_document_limits(value: Any, content_size: int) -> list[str]`, `parse_strict_template_path(path: str) -> TemplatePath`, `validate_envelope_identity(path: str, document: dict[str, Any]) -> list[str]`, and `validate_schema_identity(path: str, document: dict[str, Any]) -> list[str]`.

- [ ] **Step 1: Write failing canonicalization and identity tests**

Create `tests/test_template_contract.py` with these initial tests:

```python
import unittest

from scripts.template_contract import (
    compute_spec_checksum,
    decode_json_bytes,
    parse_strict_template_path,
    validate_document_limits,
    validate_envelope_identity,
    validate_schema_identity,
)


class TemplateContractPrimitiveTests(unittest.TestCase):
    def test_spec_checksum_is_stable_across_key_order(self):
        left = {"tags": ["forest"], "category": "animal"}
        right = {"category": "animal", "tags": ["forest"]}
        self.assertEqual(compute_spec_checksum(left), compute_spec_checksum(right))
        self.assertRegex(compute_spec_checksum(left), r"^sha256:[0-9a-f]{64}$")

    def test_strict_json_rejects_duplicate_keys_and_non_finite_numbers(self):
        for content in (b'{"id":"a","id":"b"}', b'{"value":NaN}', b'{"value":Infinity}'):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    decode_json_bytes(content)

    def test_document_limits_reject_excessive_depth_and_file_size(self):
        nested = {}
        cursor = nested
        for _ in range(33):
            cursor["child"] = {}
            cursor = cursor["child"]
        errors = validate_document_limits(nested, content_size=262145)
        self.assertIn("document exceeds 262144 bytes", errors)
        self.assertTrue(any("nesting exceeds 32 levels" in error for error in errors))

    def test_strict_path_extracts_family_slug_and_version(self):
        parsed = parse_strict_template_path(
            "templates/monsters/forest-wolf/v1.2.3/template.json"
        )
        self.assertEqual(parsed.family, "monsters")
        self.assertEqual(parsed.slug, "forest-wolf")
        self.assertEqual(parsed.version, "1.2.3")

    def test_identity_rejects_path_document_disagreement(self):
        document = {
            "id": "monsters:wrong-wolf",
            "slug": "forest-wolf",
            "family": "monsters",
            "version": "1.2.3",
        }
        self.assertEqual(
            validate_envelope_identity(
                "templates/monsters/forest-wolf/v1.2.3/template.json", document
            ),
            ["id must equal monsters:forest-wolf"],
        )

    def test_strict_path_rejects_unversioned_or_nested_layouts(self):
        for path in (
            "templates/monsters/forest-wolf/template.json",
            "templates/generated-content/quests/example/v1.0.0/template.json",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    parse_strict_template_path(path)

    def test_schema_id_must_match_family_and_version_path(self):
        errors = validate_schema_identity(
            "templates/schemas/monsters/v1.2.3/schema.json",
            {"$id": "https://ultimateodycer.com/schemas/items/1.2.3"},
        )
        self.assertEqual(
            errors,
            ["$id must equal https://ultimateodycer.com/schemas/monsters/1.2.3"],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```powershell
rtk python -m unittest tests.test_template_contract -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.template_contract'`.

- [ ] **Step 3: Add the pinned dependency and cache ignores**

Create `requirements-dev.txt`:

```text
jsonschema==4.26.0
```

Create `.gitignore`:

```text
__pycache__/
*.py[cod]
validation-report.json
```

Add this CI step immediately after `actions/setup-python@v5` in `.github/workflows/validate.yml`:

```yaml
      - name: Install validation dependencies
        run: python -m pip install --disable-pip-version-check -r requirements-dev.txt
```

- [ ] **Step 4: Implement the minimal primitives**

Create `scripts/template_contract.py`:

```python
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any


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
        raise ValueError("strict template path must be templates/<family>/<slug>/v<semver>/template.json")
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
    if not KEBAB.fullmatch(family) or not version_dir.startswith("v") or not SEMVER.fullmatch(version_dir[1:]):
        return ["strict schema family and version path are invalid"]
    expected = f"https://ultimateodycer.com/schemas/{family}/{version_dir[1:]}"
    return [] if document.get("$id") == expected else [f"$id must equal {expected}"]
```

- [ ] **Step 5: Run the focused test and verify GREEN**

Run:

```powershell
rtk python -m unittest tests.test_template_contract -v
```

Expected: 4 tests pass.

- [ ] **Step 6: Commit Task 1**

```powershell
rtk git add -- .gitignore requirements-dev.txt .github/workflows/validate.yml scripts/template_contract.py tests/test_template_contract.py
rtk git commit -m "feat(contract): add canonical v1 primitives"
```

---

### Task 2: Common envelope schema and local schema store

**Files:**
- Create: `templates/schemas/template-contract/v1.0.0/schema.json`
- Modify: `scripts/template_contract.py`
- Modify: `tests/test_template_contract.py`

**Interfaces:**
- Consumes: a repository root, a catalog `schema_file`, and a parsed JSON document.
- Produces: `load_schema_store(root: Path) -> tuple[dict[str, dict[str, Any]], referencing.Registry]`, `validate_schema_references(root: Path, schema_file: str) -> list[str]`, and `validate_with_schema(root: Path, schema_file: str, document: Any) -> list[str]`.

- [ ] **Step 1: Add failing schema-store tests**

Append to `tests/test_template_contract.py`:

```python
import json
import tempfile
from pathlib import Path

from scripts.template_contract import validate_schema_references, validate_with_schema


class SchemaStoreTests(unittest.TestCase):
    def test_family_schema_refines_and_closes_spec(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            common = root / "templates/schemas/template-contract/v1.0.0/schema.json"
            family = root / "templates/schemas/monsters/v1.0.0/schema.json"
            common.parent.mkdir(parents=True)
            family.parent.mkdir(parents=True)
            common.write_text(
                Path("templates/schemas/template-contract/v1.0.0/schema.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            family.write_text(json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://ultimateodycer.com/schemas/monsters/1.0.0",
                "allOf": [
                    {"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"},
                    {"properties": {"spec": {"type": "object", "required": ["category"], "properties": {"category": {"type": "string"}}, "additionalProperties": False}}},
                ],
            }), encoding="utf-8")
            document = strict_document(spec={"category": "animal", "runtime_hp": 100})
            errors = validate_with_schema(
                root, "templates/schemas/monsters/v1.0.0/schema.json", document
            )
            self.assertTrue(any("runtime_hp" in error for error in errors))

    def test_common_schema_rejects_unknown_root_field(self):
        document = strict_document(spec={"category": "animal"})
        document["unexpected"] = True
        errors = validate_with_schema(
            Path("."),
            "templates/schemas/template-contract/v1.0.0/schema.json",
            document,
        )
        self.assertTrue(any("unexpected" in error for error in errors))

    def test_schema_reference_must_resolve_from_local_store(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            schema = root / "templates/schemas/monsters/v1.0.0/schema.json"
            schema.parent.mkdir(parents=True)
            schema.write_text(json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://ultimateodycer.com/schemas/monsters/1.0.0",
                "$ref": "https://ultimateodycer.com/schemas/missing/1.0.0",
            }), encoding="utf-8")
            self.assertEqual(
                validate_schema_references(root, "templates/schemas/monsters/v1.0.0/schema.json"),
                ["unresolved local schema reference: https://ultimateodycer.com/schemas/missing/1.0.0"],
            )
```

Add this helper above `SchemaStoreTests`:

```python
def strict_document(spec):
    return {
        "$schema": "../../../schemas/monsters/v1.0.0/schema.json",
        "contract_version": "1.0.0",
        "id": "monsters:forest-wolf",
        "slug": "forest-wolf",
        "family": "monsters",
        "version": "1.0.0",
        "authority": "declarative",
        "intended_consumers": [],
        "compatibility": [],
        "dependencies": [],
        "spec_checksum": compute_spec_checksum(spec),
        "spec": spec,
    }
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
rtk python -m unittest tests.test_template_contract.SchemaStoreTests -v
```

Expected: FAIL because `validate_with_schema` does not exist.

- [ ] **Step 3: Create the common Draft 2020-12 schema**

Create `templates/schemas/template-contract/v1.0.0/schema.json` with these required root properties and constraints:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ultimateodycer.com/schemas/template-contract/1.0.0",
  "title": "Ultimate Odycer Template Contract v1",
  "type": "object",
  "required": [
    "$schema",
    "contract_version",
    "id",
    "slug",
    "family",
    "version",
    "authority",
    "intended_consumers",
    "compatibility",
    "dependencies",
    "spec_checksum",
    "spec"
  ],
  "properties": {
    "$schema": {"type": "string", "minLength": 1, "maxLength": 256},
    "contract_version": {"const": "1.0.0"},
    "id": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 129},
    "slug": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64},
    "family": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64},
    "version": {"type": "string", "pattern": "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$"},
    "authority": {"const": "declarative"},
    "intended_consumers": {"type": "array", "items": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"}, "uniqueItems": true, "maxItems": 16},
    "compatibility": {"type": "array", "maxItems": 16, "items": {"$ref": "#/$defs/compatibility"}},
    "dependencies": {"type": "array", "items": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*@(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$"}, "uniqueItems": true, "maxItems": 128},
    "spec_checksum": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
    "spec": {"type": "object"}
  },
  "$defs": {
    "compatibility": {
      "type": "object",
      "required": ["consumer", "version", "verified_at", "evidence"],
      "properties": {
        "consumer": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
        "version": {"type": "string", "minLength": 1, "maxLength": 64},
        "verified_at": {"type": "string", "format": "date-time"},
        "evidence": {"type": "string", "pattern": "^[a-z0-9]+(?:[-/:._a-z0-9]+)$", "maxLength": 256}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Implement local-only schema resolution**

Append to `scripts/template_contract.py`:

```python
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable


def load_schema_store(root: Path):
    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    for path in sorted((root / "templates/schemas").rglob("schema.json")):
        document = decode_json_bytes(path.read_bytes())
        schema_id = document.get("$id")
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
    known_ids = {document["$id"] for document in schemas.values() if isinstance(document.get("$id"), str)}
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
            for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
        ]
    except (SchemaError, Unresolvable) as error:
        return [f"schema resolution failed: {error}"]
```

Do not enable network retrieval. An unresolved `$ref` must surface as a validation failure in Task 4.

- [ ] **Step 5: Verify GREEN and existing tests**

Run:

```powershell
rtk python -m unittest tests.test_template_contract -v
rtk python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 2**

```powershell
rtk git add -- templates/schemas/template-contract/v1.0.0/schema.json scripts/template_contract.py tests/test_template_contract.py
rtk git commit -m "feat(contract): add strict v1 envelope schema"
```

---

### Task 3: Exact catalog references, aliases, and graph closure

**Files:**
- Create: `scripts/registry_catalog.py`
- Create: `tests/test_registry_catalog.py`

**Interfaces:**
- Consumes: catalog data and strict-v1 documents keyed by exact reference.
- Produces: `exact_ref(entry: Mapping[str, Any]) -> str`, `build_catalog_index(catalog: Mapping[str, Any]) -> tuple[CatalogIndex | None, list[str]]`, and `validate_reference_graph(index: CatalogIndex, documents: Mapping[str, Mapping[str, Any]]) -> list[str]`.

- [ ] **Step 1: Write failing catalog graph tests**

Create `tests/test_registry_catalog.py`:

```python
import unittest

from scripts.registry_catalog import build_catalog_index, validate_reference_graph


def entry(ref, file):
    template_id, version = ref.split("@", 1)
    family, slug = template_id.split(":", 1)
    return {
        "id": template_id,
        "family": family,
        "slug": slug,
        "version": version,
        "file": file,
        "validation_profile": "strict-v1",
    }


class CatalogIndexTests(unittest.TestCase):
    def test_duplicate_exact_reference_is_rejected(self):
        duplicate = entry("items:iron-ore@1.0.0", "templates/items/iron-ore/v1.0.0/template.json")
        index, errors = build_catalog_index({"entries": [duplicate, dict(duplicate)], "aliases": []})
        self.assertIsNone(index)
        self.assertEqual(errors, ["duplicate catalog reference: items:iron-ore@1.0.0"])

    def test_missing_dependency_is_rejected(self):
        source = entry("recipes:iron-ingot@1.0.0", "templates/recipes/iron-ingot/v1.0.0/template.json")
        index, errors = build_catalog_index({"entries": [source], "aliases": []})
        self.assertEqual(errors, [])
        documents = {"recipes:iron-ingot@1.0.0": {"dependencies": ["items:iron-ore@1.0.0"]}}
        self.assertEqual(
            validate_reference_graph(index, documents),
            ["recipes:iron-ingot@1.0.0: missing dependency items:iron-ore@1.0.0"],
        )

    def test_alias_cycle_is_rejected(self):
        catalog = {
            "entries": [
                entry("items:a@1.0.0", "templates/items/a/v1.0.0/template.json"),
                entry("items:b@1.0.0", "templates/items/b/v1.0.0/template.json"),
            ],
            "aliases": [
                {"from": "items:a@1.0.0", "to": "items:b@1.0.0"},
                {"from": "items:b@1.0.0", "to": "items:a@1.0.0"},
            ],
        }
        index, errors = build_catalog_index(catalog)
        self.assertIsNone(index)
        self.assertEqual(errors, ["alias cycle: items:a@1.0.0 -> items:b@1.0.0 -> items:a@1.0.0"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
rtk python -m unittest tests.test_registry_catalog -v
```

Expected: FAIL because `scripts.registry_catalog` does not exist.

- [ ] **Step 3: Implement the exact index and fail-closed graph**

Create `scripts/registry_catalog.py` with these public types and rules:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class CatalogIndex:
    by_ref: dict[str, Mapping[str, Any]]
    by_file: dict[str, Mapping[str, Any]]
    aliases: dict[str, str]


def exact_ref(entry: Mapping[str, Any]) -> str:
    return f"{entry['id']}@{entry['version']}"


def _find_alias_cycle(aliases: Mapping[str, str]) -> list[str] | None:
    for start in sorted(aliases):
        chain: list[str] = []
        positions: dict[str, int] = {}
        current = start
        while current in aliases:
            if current in positions:
                return chain[positions[current]:] + [current]
            positions[current] = len(chain)
            chain.append(current)
            current = aliases[current]
    return None


def build_catalog_index(catalog: Mapping[str, Any]):
    by_ref = {}
    by_file = {}
    errors = []
    for entry in catalog.get("entries", []):
        if all(isinstance(entry.get(key), str) for key in ("id", "version")):
            ref = exact_ref(entry)
            if ref in by_ref:
                errors.append(f"duplicate catalog reference: {ref}")
            else:
                by_ref[ref] = entry
        file = entry.get("file")
        if file in by_file:
            errors.append(f"duplicate catalog file: {file}")
        else:
            by_file[file] = entry
    aliases = {}
    for alias in catalog.get("aliases", []):
        source, target = alias.get("from"), alias.get("to")
        if source in aliases:
            errors.append(f"duplicate alias source: {source}")
        elif source == target:
            errors.append(f"self alias: {source}")
        else:
            aliases[source] = target
    cycle = _find_alias_cycle(aliases)
    if cycle:
        errors.append(f"alias cycle: {' -> '.join(cycle)}")
    if errors:
        return None, sorted(errors)
    return CatalogIndex(by_ref=by_ref, by_file=by_file, aliases=aliases), []


def validate_reference_graph(index: CatalogIndex, documents: Mapping[str, Mapping[str, Any]]) -> list[str]:
    errors = []
    for source_ref, document in sorted(documents.items()):
        for dependency in document.get("dependencies", []):
            if dependency not in index.by_ref:
                errors.append(f"{source_ref}: missing dependency {dependency}")
        entry = index.by_ref[source_ref]
        for superseded in entry.get("supersedes", []):
            if superseded == source_ref:
                errors.append(f"{source_ref}: cannot supersede itself")
            elif superseded not in index.by_ref:
                errors.append(f"{source_ref}: missing superseded reference {superseded}")
    for ref, entry in sorted(index.by_ref.items()):
        successor = entry.get("superseded_by")
        if successor is not None:
            if successor == ref:
                errors.append(f"{ref}: cannot be superseded by itself")
            elif successor not in index.by_ref:
                errors.append(f"{ref}: missing successor reference {successor}")
    for source, target in sorted(index.aliases.items()):
        if source not in index.by_ref:
            errors.append(f"alias source missing: {source}")
        if target not in index.by_ref:
            errors.append(f"alias target missing: {target}")
    return sorted(errors)
```

Legacy entries without reviewed canonical `id` metadata are intentionally absent from `by_ref` and cannot be targeted by `supersedes`. A pilot migration must first add their reviewed canonical ID; the foundation never derives it by guessing from a path.

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
rtk python -m unittest tests.test_registry_catalog -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit Task 3**

```powershell
rtk git add -- scripts/registry_catalog.py tests/test_registry_catalog.py
rtk git commit -m "feat(catalog): enforce exact reference closure"
```

---

### Task 4: Dual-profile validator and machine-readable report

**Files:**
- Create: `scripts/validation_report.py`
- Modify: `scripts/validate_registry.py`
- Modify: `tests/test_validate_registry.py`

**Interfaces:**
- Consumes: `validate_registry(root: Path)`, an optional `--report` output path, catalog v2, local schemas, and JSON documents.
- Produces: `ValidationIssue`, `ValidationReport`, deterministic human output, deterministic report JSON, and process exit code 1 on any issue.

- [ ] **Step 1: Add a failing end-to-end dual-profile test**

Append to `tests/test_validate_registry.py`:

```python
import hashlib
import json
import tempfile
from pathlib import Path

from scripts.template_contract import compute_spec_checksum
from scripts.validate_registry import validate_registry


class DualProfileValidationTests(unittest.TestCase):
    def test_legacy_document_is_not_forced_through_v1_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "templates/items/legacy-item/v0.1.0/template.json"
            path.parent.mkdir(parents=True)
            path.write_bytes(b'{"id":"legacy_item","mixedCase":true}')
            write_catalog(root, [{
                "name": "legacy-item",
                "kind": "item-template",
                "version": "0.1.0",
                "status": "experimental",
                "file": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "compatibility": [],
                "validation_profile": "legacy-unvalidated",
                "contract_version": None,
            }])
            self.assertEqual(validate_registry(root).issues, [])

    def test_strict_document_fails_on_wrong_checksum_and_missing_dependency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            install_test_schemas(root)
            path = root / "templates/monsters/forest-wolf/v1.0.0/template.json"
            path.parent.mkdir(parents=True)
            spec = {"category": "animal"}
            document = strict_monster(spec)
            document["spec_checksum"] = "sha256:" + "0" * 64
            document["dependencies"] = ["items:missing@1.0.0"]
            path.write_text(json.dumps(document), encoding="utf-8")
            write_catalog(root, [strict_entry(path, root, document)])
            messages = [issue.message for issue in validate_registry(root).issues]
            self.assertTrue(any("spec checksum mismatch" in message for message in messages))
            self.assertTrue(any("missing dependency items:missing@1.0.0" in message for message in messages))
```

Add these exact helpers above `DualProfileValidationTests`:

```python
import shutil


def install_test_schemas(root):
    common_source = Path("templates/schemas/template-contract/v1.0.0/schema.json")
    common_target = root / common_source
    common_target.parent.mkdir(parents=True)
    shutil.copyfile(common_source, common_target)
    family = root / "templates/schemas/monsters/v1.0.0/schema.json"
    family.parent.mkdir(parents=True)
    family.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ultimateodycer.com/schemas/monsters/1.0.0",
        "allOf": [
            {"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"},
            {"properties": {"spec": {
                "type": "object",
                "required": ["category"],
                "properties": {"category": {"type": "string"}},
                "additionalProperties": False,
            }}},
        ],
    }), encoding="utf-8")


def strict_monster(spec):
    return {
        "$schema": "../../../schemas/monsters/v1.0.0/schema.json",
        "contract_version": "1.0.0",
        "id": "monsters:forest-wolf",
        "slug": "forest-wolf",
        "family": "monsters",
        "version": "1.0.0",
        "authority": "declarative",
        "intended_consumers": [],
        "compatibility": [],
        "dependencies": [],
        "spec_checksum": compute_spec_checksum(spec),
        "spec": spec,
    }


def strict_entry(path, root, document):
    return {
        "id": document["id"],
        "slug": document["slug"],
        "family": document["family"],
        "name": document["slug"],
        "kind": "monster-template",
        "version": document["version"],
        "contract_version": document["contract_version"],
        "validation_profile": "strict-v1",
        "status": "experimental",
        "schema_file": "templates/schemas/monsters/v1.0.0/schema.json",
        "file": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "spec_checksum": document["spec_checksum"],
        "intended_consumers": [],
        "compatibility": [],
        "supersedes": [],
    }


def write_catalog(root, entries):
    catalog = root / "templates/catalog.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(json.dumps({
        "registry_version": "2.0.0",
        "aliases": [],
        "entries": entries,
    }), encoding="utf-8")
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
rtk python -m unittest tests.test_validate_registry.DualProfileValidationTests -v
```

Expected: FAIL because `validate_registry` and report types do not exist.

- [ ] **Step 3: Implement stable report types**

Create `scripts/validation_report.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True, order=True)
class ValidationIssue:
    path: str
    code: str
    message: str


@dataclass
class ValidationReport:
    documents_checked: int = 0
    catalog_entries: int = 0
    legacy_entries: int = 0
    strict_entries: int = 0
    strict_schema_entries: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    def sorted_issues(self):
        return sorted(self.issues)

    def write_json(self, path: Path):
        payload = {
            "summary": {
                "documents_checked": self.documents_checked,
                "catalog_entries": self.catalog_entries,
                "legacy_entries": self.legacy_entries,
                "strict_entries": self.strict_entries,
                "strict_schema_entries": self.strict_schema_entries,
                "issue_count": len(self.issues),
            },
            "issues": [asdict(issue) for issue in self.sorted_issues()],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Refactor validation into a pure orchestration function**

Keep `validate_public_content` and `validate_public_path` behavior. Add:

```python
def validate_registry(root: Path) -> ValidationReport:
    """Read and validate a registry without mutating it."""
```

Implement `validate_registry` with this control flow:

```python
def validate_registry(root: Path) -> ValidationReport:
    report = ValidationReport()
    catalog_path = root / "templates/catalog.json"
    if not catalog_path.is_file():
        report.issues.append(ValidationIssue("templates/catalog.json", "catalog-missing", "catalog is missing"))
        return report

    try:
        catalog = decode_json_bytes(catalog_path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        report.issues.append(ValidationIssue("templates/catalog.json", "catalog-json", str(error)))
        return report

    entries = catalog.get("entries", []) if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        report.issues.append(ValidationIssue("templates/catalog.json", "catalog-entries", "entries must be an array"))
        return report
    report.catalog_entries = len(entries)
    if catalog.get("registry_version") != "2.0.0":
        report.issues.append(ValidationIssue("templates/catalog.json", "catalog-version", "registry_version must equal 2.0.0"))
    if not isinstance(catalog.get("aliases"), list):
        report.issues.append(ValidationIssue("templates/catalog.json", "catalog-aliases", "aliases must be an array"))

    by_file = {}
    for entry in entries:
        if not isinstance(entry, dict):
            report.issues.append(ValidationIssue("templates/catalog.json", "catalog-entry", "every entry must be an object"))
            continue
        file = entry.get("file")
        if not isinstance(file, str):
            report.issues.append(ValidationIssue("templates/catalog.json", "catalog-file", "entry file must be a string"))
        elif file in by_file:
            report.issues.append(ValidationIssue(file, "catalog-duplicate-file", "file is listed more than once"))
        else:
            by_file[file] = entry

    documents_by_ref = {}
    for path in sorted((root / "templates").rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        if rel == "templates/catalog.json":
            continue
        report.documents_checked += 1
        entry = by_file.get(rel)
        if entry is None:
            report.issues.append(ValidationIssue(rel, "catalog-unlisted", "JSON file is not listed in catalog"))
            continue
        try:
            content = path.read_bytes()
            document = decode_json_bytes(content)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            report.issues.append(ValidationIssue(rel, "json-parse", str(error)))
            continue
        for violation in validate_public_path(rel):
            report.issues.append(ValidationIssue(rel, "public-path", violation))
        for violation in validate_public_content(document):
            report.issues.append(ValidationIssue(rel, "public-content", violation))
        normalized_lf = content.replace(b"\r\n", b"\n")
        hashes = {
            hashlib.sha256(content).hexdigest(),
            hashlib.sha256(normalized_lf).hexdigest(),
            hashlib.sha256(normalized_lf.replace(b"\n", b"\r\n")).hexdigest(),
        }
        if entry.get("sha256") not in hashes:
            report.issues.append(ValidationIssue(rel, "sha256", "catalog SHA-256 mismatch"))
        profile = entry.get("validation_profile")
        if profile == "legacy-unvalidated":
            report.legacy_entries += 1
            continue
        if not isinstance(document, dict):
            report.issues.append(ValidationIssue(rel, "strict-root", "strict document root must be an object"))
            continue
        for message in validate_document_limits(document, len(content)):
            report.issues.append(ValidationIssue(rel, "document-limits", message))
        if profile == "strict-schema-v1":
            report.strict_schema_entries += 1
            try:
                Draft202012Validator.check_schema(document)
            except jsonschema.exceptions.SchemaError as error:
                report.issues.append(ValidationIssue(rel, "schema-meta", error.message))
            for message in validate_schema_identity(rel, document):
                report.issues.append(ValidationIssue(rel, "schema-id", message))
            for message in validate_schema_references(root, rel):
                report.issues.append(ValidationIssue(rel, "schema-resolution", message))
            continue
        if profile != "strict-v1":
            report.issues.append(ValidationIssue(rel, "validation-profile", f"unknown validation profile: {profile!r}"))
            continue
        report.strict_entries += 1
        try:
            for message in validate_envelope_identity(rel, document):
                report.issues.append(ValidationIssue(rel, "identity", message))
        except ValueError as error:
            report.issues.append(ValidationIssue(rel, "strict-path", str(error)))
        schema_file = entry.get("schema_file")
        if not isinstance(schema_file, str):
            report.issues.append(ValidationIssue(rel, "schema-file", "strict entry schema_file must be a string"))
        else:
            for message in validate_with_schema(root, schema_file, document):
                report.issues.append(ValidationIssue(rel, "schema", message))
            expected_schema_ref = posixpath.relpath(
                schema_file,
                start=str(PurePosixPath(rel).parent),
            )
            if document.get("$schema") != expected_schema_ref:
                report.issues.append(ValidationIssue(rel, "schema-reference", f"$schema must equal {expected_schema_ref}"))
        computed_spec_checksum = compute_spec_checksum(document.get("spec"))
        if document.get("spec_checksum") != computed_spec_checksum:
            report.issues.append(ValidationIssue(rel, "spec-checksum", "spec checksum mismatch"))
        if entry.get("spec_checksum") != computed_spec_checksum:
            report.issues.append(ValidationIssue(rel, "catalog-spec-checksum", "catalog spec checksum mismatch"))
        for key in ("id", "slug", "family", "version", "contract_version", "intended_consumers", "compatibility"):
            if entry.get(key) != document.get(key):
                report.issues.append(ValidationIssue(rel, "catalog-envelope", f"catalog {key} does not match document"))
        documents_by_ref[exact_ref(entry)] = document

    for file in sorted(set(by_file) - {path.relative_to(root).as_posix() for path in (root / "templates").rglob("*.json")}):
        report.issues.append(ValidationIssue(file, "catalog-file-missing", "catalogued file does not exist"))

    index, index_errors = build_catalog_index(catalog)
    for message in index_errors:
        report.issues.append(ValidationIssue("templates/catalog.json", "catalog-index", message))
    if index is not None:
        for message in validate_reference_graph(index, documents_by_ref):
            report.issues.append(ValidationIssue("templates/catalog.json", "reference-graph", message))
    report.issues = report.sorted_issues()
    return report
```

Import `hashlib`, `jsonschema`, `posixpath`, `Draft202012Validator`, `PurePosixPath`, `compute_spec_checksum`, `decode_json_bytes`, `validate_document_limits`, `validate_envelope_identity`, `validate_schema_identity`, `validate_schema_references`, `validate_with_schema`, `exact_ref`, `build_catalog_index`, and `validate_reference_graph` at module scope. Each returned message becomes a stable `ValidationIssue`; do not swallow or downgrade it.

The orchestration enforces these exact rules:

1. Load `templates/catalog.json` and count entries.
2. Require top-level `registry_version == "2.0.0"` and `aliases` to be an array.
3. Index every catalog file path exactly once.
4. Apply the legacy profile only to entries explicitly marked `legacy-unvalidated`.
5. Apply Draft 2020-12 meta-schema validation and local `$ref` closure to `strict-schema-v1` entries.
6. Apply public policy, path policy, catalog SHA-256, common identity, family schema, `$schema` path agreement, `spec_checksum`, and exact graph closure to `strict-v1` entries.
7. Reject absent or unknown `validation_profile` values.
8. Convert `jsonschema` reference and schema errors returned by `validate_with_schema` into validation issues rather than a traceback.
9. Report catalog entries whose files are missing and JSON files not present in the catalog.
10. Never modify any input file.

Update `main()` to accept:

```text
--root <registry-root>       default: .
--report <json-path>         optional
```

Print at most 50 human-readable issues, then a total. Exit 1 when `report.issues` is non-empty.

- [ ] **Step 5: Verify GREEN and regression coverage**

Run:

```powershell
rtk python -m unittest tests.test_validate_registry -v
rtk python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 4**

```powershell
rtk git add -- scripts/validation_report.py scripts/validate_registry.py tests/test_validate_registry.py
rtk git commit -m "feat(validation): add dual-profile registry gate"
```

---

### Task 5: Deterministic catalog v2 backfill without legacy rewrites

**Files:**
- Create: `scripts/migrate_catalog_v2.py`
- Modify: `scripts/build_registry.py`
- Modify: `tests/test_build_registry.py`
- Modify: `templates/catalog.json`

**Interfaces:**
- Consumes: a catalog v1 dictionary and a registry root.
- Produces: `migrate_catalog(catalog: dict[str, Any]) -> dict[str, Any]`, a deterministic catalog v2 file, and builder entries with explicit validation profiles.

- [ ] **Step 1: Write failing migration and immutability tests**

Append to `tests/test_build_registry.py`:

```python
from scripts.migrate_catalog_v2 import ensure_contract_schema_entry, migrate_catalog


class CatalogV2MigrationTests(unittest.TestCase):
    def test_backfill_marks_existing_entries_legacy_without_dropping_metadata(self):
        source = {
            "registry_version": "1.0.0",
            "generated_at": "2026-08-19",
            "entries": [{
                "name": "iron-ore",
                "version": "0.1.0",
                "file": "templates/items/iron-ore/v0.1.0/template.json",
                "sha256": "a" * 64,
                "source_file": "item/iron_ore.json",
            }],
        }
        migrated = migrate_catalog(source)
        self.assertEqual(migrated["registry_version"], "2.0.0")
        self.assertEqual(migrated["aliases"], [])
        self.assertEqual(migrated["entries"][0]["validation_profile"], "legacy-unvalidated")
        self.assertIsNone(migrated["entries"][0]["contract_version"])
        self.assertEqual(migrated["entries"][0]["source_file"], "item/iron_ore.json")

    def test_catalog_migration_does_not_touch_template_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "templates/items/iron-ore/v0.1.0/template.json"
            template.parent.mkdir(parents=True)
            template.write_bytes(b'{"id":"iron_ore"}\r\n')
            before = hashlib.sha256(template.read_bytes()).hexdigest()
            migrated = migrate_catalog({"entries": []})
            (root / "templates/catalog.json").write_text(json.dumps(migrated), encoding="utf-8")
            after = hashlib.sha256(template.read_bytes()).hexdigest()
            self.assertEqual(after, before)

    def test_contract_schema_entry_is_added_once_with_real_checksum(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            schema = root / "templates/schemas/template-contract/v1.0.0/schema.json"
            schema.parent.mkdir(parents=True)
            schema.write_bytes(b'{"$id":"https://ultimateodycer.com/schemas/template-contract/1.0.0"}')
            catalog = {"entries": []}
            ensure_contract_schema_entry(catalog, root)
            ensure_contract_schema_entry(catalog, root)
            self.assertEqual(len(catalog["entries"]), 1)
            self.assertEqual(catalog["entries"][0]["validation_profile"], "strict-schema-v1")
            self.assertEqual(catalog["entries"][0]["sha256"], hashlib.sha256(schema.read_bytes()).hexdigest())
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
rtk python -m unittest tests.test_build_registry.CatalogV2MigrationTests -v
```

Expected: FAIL because `scripts.migrate_catalog_v2` does not exist.

- [ ] **Step 3: Implement the pure migration and CLI**

Create `scripts/migrate_catalog_v2.py`:

```python
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def migrate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    migrated = copy.deepcopy(catalog)
    migrated["registry_version"] = "2.0.0"
    migrated["aliases"] = list(migrated.get("aliases", []))
    for entry in migrated.get("entries", []):
        entry.setdefault("validation_profile", "legacy-unvalidated")
        entry.setdefault("contract_version", None)
    return migrated


def ensure_contract_schema_entry(catalog: dict[str, Any], root: Path) -> None:
    path = root / "templates/schemas/template-contract/v1.0.0/schema.json"
    relative = path.relative_to(root).as_posix()
    if any(entry.get("file") == relative for entry in catalog.get("entries", [])):
        return
    catalog.setdefault("entries", []).append({
        "name": "template-contract",
        "kind": "json-schema",
        "version": "1.0.0",
        "status": "experimental",
        "file": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "compatibility": [],
        "validation_profile": "strict-schema-v1",
        "contract_version": "1.0.0",
    })
    catalog["entries"].sort(key=lambda entry: entry["file"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("templates/catalog.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    original = json.loads(args.catalog.read_text(encoding="utf-8"))
    migrated = migrate_catalog(original)
    ensure_contract_schema_entry(migrated, args.catalog.parent.parent)
    rendered = json.dumps(migrated, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        raise SystemExit(0 if args.catalog.read_text(encoding="utf-8") == rendered else 1)
    args.catalog.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Make the builder emit explicit legacy metadata**

In every catalog entry created by `promote_exports`, add:

```python
"validation_profile": "legacy-unvalidated",
"contract_version": None,
```

Do not add `superseded_by`; that field is created only by a successful family migration.

- [ ] **Step 5: Verify tests and migrate the real catalog**

Run:

```powershell
rtk python -m unittest tests.test_build_registry -v
rtk python scripts/migrate_catalog_v2.py --catalog templates/catalog.json
rtk python scripts/migrate_catalog_v2.py --catalog templates/catalog.json --check
rtk git diff -- templates/catalog.json
```

Expected:

- tests pass;
- `--check` exits 0 after migration;
- the catalog diff contains only top-level v2/alias metadata and per-entry `validation_profile`/`contract_version` additions;
- no file below `templates/` except `templates/catalog.json` and the common schema from Task 2 is modified.

- [ ] **Step 6: Commit Task 5**

```powershell
rtk git add -- scripts/migrate_catalog_v2.py scripts/build_registry.py tests/test_build_registry.py templates/catalog.json
rtk git commit -m "feat(catalog): backfill explicit legacy profiles"
```

---

### Task 6: Apply the normative specification and final foundation gate

**Files:**
- Modify: `TEMPLATE-SPEC.md`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-08-21-template-contract-v1-design.md`
- Test: complete repository test and validation suite

**Interfaces:**
- Consumes: the implemented contract and catalog behavior from Tasks 1-5.
- Produces: contributor-facing rules that match executable validation exactly.

- [ ] **Step 1: Replace permissive historical wording in `TEMPLATE-SPEC.md`**

Make these statements normative and exact:

```text
Specification version: 1.0.0
Catalog version: 2.0.0
Legacy profile: legacy-unvalidated
Strict template profile: strict-v1
Strict schema profile: strict-schema-v1
Canonical ID: <family>:<slug>
Exact reference: <family>:<slug>@<semver>
Authority: declarative
Unknown root or family-spec properties: rejected
Implicit latest-version resolution: forbidden
Compatibility without exact evidence: forbidden
Published version-directory mutation: forbidden
```

Document the complete common envelope, checksum algorithm, legacy rules, strict rules, schema requirements, naming rules, catalog fields, declarative/authoritative table, compatibility evidence fields, and contributor commands:

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/validate_registry.py --report validation-report.json
python scripts/migrate_catalog_v2.py --check
```

Remove the exception that lets new or historical documents claim compatibility without the explicit validation profile.

- [ ] **Step 2: Add a concise status section to `README.md`**

Add this content near the experimental-registry notice:

```markdown
### Validation profiles

- `legacy-unvalidated` preserves published `v0.1.0` snapshots and applies JSON, public-policy, catalog, and checksum checks only.
- `strict-v1` requires the common envelope, an exact family schema, canonical references, declarative authority, and full link validation.
- `strict-schema-v1` requires a valid Draft 2020-12 schema, a stable `$id`, local reference closure, and catalog integrity.

Legacy presence is not compatibility evidence. Strict consumers must reject legacy entries unless they explicitly opt in.
```

- [ ] **Step 3: Verify the design correction is present**

Confirm the design document consistently requires exact versioned dependencies:

```powershell
rtk rg -n "<family>:<slug>@<semver>|implicit latest-version" docs/superpowers/specs/2026-08-21-template-contract-v1-design.md TEMPLATE-SPEC.md
```

Expected: both documents contain the exact-reference rule and forbid implicit latest selection.

- [ ] **Step 4: Run the full fresh verification gate**

Run:

```powershell
rtk python -m pip install --disable-pip-version-check -r requirements-dev.txt
rtk python -m unittest discover -s tests -v
rtk python scripts/migrate_catalog_v2.py --check
rtk python scripts/validate_registry.py --report validation-report.json
rtk git diff --check
rtk powershell -NoProfile -Command '$env:PYTHONPATH="C:/Users/redga/botte-secrete"; python -m skills.checkup.cli .'
```

Expected:

- every unit test passes;
- catalog migration check exits 0;
- registry validation reports 0 issues across all legacy documents and the common schema;
- `git diff --check` exits 0;
- checkup reports no malicious pattern or taint candidate;
- any unrelated checkup infrastructure warning is reported separately and not misrepresented as a contract failure.

- [ ] **Step 5: Prove legacy template immutability against `origin/main`**

Run:

```powershell
rtk git diff --name-only origin/main...HEAD -- templates | rtk rg -v "^templates/catalog\.json$|^templates/schemas/template-contract/v1\.0\.0/schema\.json$"
```

Expected: no output. If any legacy template or legacy schema path appears, stop and restore the implementation by editing forward; do not reset or discard unrelated work.

- [ ] **Step 6: Commit Task 6**

```powershell
rtk git add -- TEMPLATE-SPEC.md README.md docs/superpowers/specs/2026-08-21-template-contract-v1-design.md
rtk git commit -m "docs(contract): apply template contract v1 rules"
```

- [ ] **Step 7: Inspect the final branch without publishing or merging**

Run:

```powershell
rtk git status --short --branch
rtk git log --oneline origin/main..HEAD
rtk git diff --stat origin/main...HEAD
```

Expected: clean worktree and only the design plus six foundation commits. Publication, PR creation, and merge remain a separate explicit gate after review.

## Deferred Plans

The following work is intentionally excluded from this plan and must not be bundled into its commits:

1. Pilot schemas and migrations for `classes`, `races`, `items`, `spells`, and `monsters`.
2. Family README generation and per-document migration dispositions.
3. Zig `public_template_contract.zig`, private link mappings, feature flag, and isolated adapter tests.
4. Remaining family migration cohorts.
5. Godot/VR and LLM consumer adapters.

## Plan Self-review Result

| Foundation requirement | Covered by |
| --- | --- |
| Legacy byte immutability | Tasks 5 and 6 |
| Strict JSON and deterministic `spec_checksum` | Task 1 |
| Common Draft 2020-12 envelope and local schema closure | Task 2 |
| Exact versioned dependencies, aliases, and supersession | Task 3 |
| Legacy, strict template, and strict schema profiles | Task 4 |
| Explicit catalog v2 metadata | Task 5 |
| Normative contributor documentation and CI proof | Task 6 |

No contract-foundation requirement is left without an implementation task. Family-specific types, migration dispositions, Zig links, and runtime projection remain deliberately assigned to the separate plans listed above.
