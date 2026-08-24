# Pilot Family Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish strict-v1 declarative replacements and strict family schemas for `classes`, `races`, `items`, `spells`, and `monsters`, while preserving every legacy byte and producing a private read-only Zig link-readiness audit.

**Architecture:** A pure allowlist converter classifies every pilot legacy document before any write. Deterministic generators create the five family schemas, minimal v1 documents, catalog entries, family READMEs, and one complete migration report; collisions and malformed sources remain legacy-only with explicit dispositions. A separate audit reads the Zig template tree and emits only a local ignored report, never compatibility metadata.

**Tech Stack:** Python 3.13, standard-library `unittest`, `jsonschema==4.26.0`, Draft 2020-12 JSON Schema, existing Template Contract v1 validator.

**Spec:** `docs/superpowers/specs/2026-08-21-template-contract-v1-design.md`

## Global Constraints

- This plan depends on PR #3 and MUST execute only after its foundation commits are present.
- Published legacy JSON and README files remain byte-identical.
- Pilot families are exactly `classes`, `races`, `items`, `spells`, and `monsters`.
- V1 documents contain declarative identity and classification only; runtime values, stats, cooldowns, ranges, costs, probabilities, AI weights, loot contents, lore, dialogue, and asset paths are not copied.
- Every generated document uses `version: "1.0.0"`, `contract_version: "1.0.0"`, `authority: "declarative"`, and `compatibility: []`.
- Every generated schema uses `validation_profile: "strict-schema-v1"`; every generated template uses `validation_profile: "strict-v1"`.
- Dependencies and supersession links use exact `<family>:<slug>@<semver>` references.
- Normalized slug collisions are never resolved by ordinal suffix or guessing; all colliding legacy documents receive `manual-review`.
- Private server paths and absolute local paths MUST NOT enter committed files.
- The Zig audit is read-only, never activates an adapter, and never populates compatibility evidence.

## Measured Scope

| Family | Legacy templates | Atypical version paths | Normalized slug collisions |
| --- | ---: | ---: | ---: |
| `classes` | 74 | 8 | 7 slug groups / 14 files |
| `races` | 41 | 8 | 0 |
| `items` | 161 | 6 | 0 |
| `spells` | 1,623 | 8 | 0 |
| `monsters` | 428 | 0 | 0 |
| **Total** | **2,327** | **30** | **14 files** |

The seven known colliding class slugs are `druid`, `mage`, `necromancer`, `paladin`, `ranger`, `rogue`, and `warrior`. Both legacy variants of each slug remain legacy-only until manual review chooses canonical provenance.

## File Structure

| File | Responsibility |
| --- | --- |
| `scripts/pilot_contracts.py` | Family definitions, safe scalar normalization, collision detection, pure conversion, schema and README generation. |
| `scripts/migrate_pilot_families.py` | Deterministic write/check CLI, catalog updates, report aggregation, and legacy supersession finalization. |
| `scripts/audit_zig_link_candidates.py` | Read-only candidate resolution against an explicitly supplied server template root. |
| `tests/test_pilot_contracts.py` | Converter, schema, collision, idempotence, and no-runtime-field tests. |
| `tests/test_pilot_migration.py` | Filesystem, catalog, report, legacy-byte, and repeated-run tests. |
| `tests/test_zig_link_audit.py` | Exact path, unique basename, unique ID, ambiguity, and missing-link tests. |
| `templates/schemas/{classes,races,items,spells,monsters}/v1.0.0/schema.json` | Exact strict-v1 family contracts. |
| `templates/{classes,races,items,spells,monsters}/README.md` | Family purpose, fields, exclusions, consumers, and versioning. |
| `MIGRATION-V1.json` | Public per-document disposition report using registry-relative paths only. |
| `templates/catalog.json` | V1 schema/template entries plus reviewed legacy supersession metadata. |
| `.gitignore` | Ignore `local-audit/`, which may contain private relative server paths. |

---

### Task 1: Pure pilot converter and disposition model

**Files:**
- Create: `scripts/pilot_contracts.py`
- Create: `tests/test_pilot_contracts.py`

**Interfaces:**
- Consumes: `convert_legacy(family: str, source_file: str, document: Any, colliding_slugs: set[str])`.
- Produces: `MigrationResult`, `normalize_slug(value: str)`, `find_slug_collisions(paths: Iterable[str])`, and `build_v1_document(result: MigrationResult) -> dict[str, Any]`.

- [ ] **Step 1: Write failing disposition tests**

Create `tests/test_pilot_contracts.py`:

```python
import unittest

from scripts.pilot_contracts import convert_legacy, find_slug_collisions


class PilotConversionTests(unittest.TestCase):
    def test_collision_is_manual_review_without_document(self):
        result = convert_legacy(
            "classes",
            "templates/classes/mage/v0.1.0/template.json",
            {"id": "mage", "name": "Mage"},
            {"mage"},
        )
        self.assertEqual(result.disposition, "manual-review")
        self.assertEqual(result.reason_codes, ("normalized-slug-collision",))
        self.assertIsNone(result.document)

    def test_non_object_source_is_invalid(self):
        result = convert_legacy(
            "items",
            "templates/items/catalog/v0.1.0/template.json",
            [],
            set(),
        )
        self.assertEqual(result.disposition, "invalid-source")
        self.assertEqual(result.reason_codes, ("root-not-object",))

    def test_spell_keeps_only_declarative_classification(self):
        result = convert_legacy(
            "spells",
            "templates/spells/fireball/v0.1.0/template.json",
            {
                "id": "fireball",
                "name": "Fireball",
                "description": "Long lore is omitted.",
                "school": "fire",
                "rarity": "common",
                "spell_type": "damage",
                "target_type": "single",
                "damage": {"base_damage": 25},
                "range": 6,
                "cast_time": 300,
                "cooldown": 1000,
                "mana_cost": 20,
                "visual_effects": {"asset_path": "private/fire.glb"},
            },
            set(),
        )
        self.assertEqual(result.disposition, "migrated")
        self.assertEqual(result.document["spec"], {
            "display_name": "Fireball",
            "school": "fire",
            "rarity": "common",
            "spell_kind": "damage",
            "target_kind": "single",
        })
        serialized = str(result.document).lower()
        for forbidden in ("damage", "range", "cast_time", "cooldown", "mana_cost", "asset_path"):
            self.assertNotIn(forbidden, serialized)

    def test_collisions_are_found_after_underscore_normalization(self):
        paths = [
            "templates/classes/arcane_mage/0.1.0/template.json",
            "templates/classes/arcane-mage/v0.1.0/template.json",
            "templates/classes/cleric/v0.1.0/template.json",
        ]
        self.assertEqual(find_slug_collisions(paths), {"arcane-mage"})
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
rtk python -m unittest discover -s tests -p "test_pilot_contracts.py" -v
```

Expected: FAIL because `scripts.pilot_contracts` does not exist.

- [ ] **Step 3: Implement the pure converter**

Create `scripts/pilot_contracts.py` with:

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable

from scripts.template_contract import compute_spec_checksum


PILOT_FAMILIES = ("classes", "races", "items", "spells", "monsters")
SLUG_TOKEN = re.compile(r"[^a-z0-9]+")

FIELD_MAP = {
    "classes": {
        "name": "display_name",
        "primary_resource": "resource_kind",
    },
    "races": {
        "name": "display_name",
        "category": "category",
        "rarity": "rarity",
        "faction": "faction_tag",
    },
    "items": {
        "name": "display_name",
        "category": "category",
        "rarity": "rarity",
        "item_type": "item_kind",
        "sub_type": "subtype",
    },
    "spells": {
        "name": "display_name",
        "school": "school",
        "rarity": "rarity",
        "spell_type": "spell_kind",
        "target_type": "target_kind",
    },
    "monsters": {
        "name": "display_name",
        "category": "category",
        "rarity": "rarity",
    },
}

INTENDED_CONSUMERS = ["llm-pipeline", "zig-server-v2"]


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
    slug = SLUG_TOKEN.sub("-", value.strip().lower()).strip("-")
    if not slug or len(slug) > 64:
        raise ValueError("slug is empty or exceeds 64 characters")
    return slug


def _path_slug(path: str) -> str:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    if len(parts) < 5 or parts[0] != "templates" or parts[-1] != "template.json":
        raise ValueError("legacy template path is invalid")
    return normalize_slug(parts[-3])


def find_slug_collisions(paths: Iterable[str]) -> set[str]:
    counts = {}
    for path in paths:
        slug = _path_slug(path)
        counts[slug] = counts.get(slug, 0) + 1
    return {slug for slug, count in counts.items() if count > 1}


def _safe_text(value: Any, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if 1 <= len(normalized) <= maximum else None


def _safe_tag(value: Any) -> str | None:
    text = _safe_text(value, 64)
    if text is None:
        return None
    try:
        return normalize_slug(text)
    except ValueError:
        return None


def convert_legacy(family, source_file, document, colliding_slugs):
    if family not in PILOT_FAMILIES:
        raise ValueError(f"unsupported pilot family: {family}")
    try:
        slug = _path_slug(source_file)
    except ValueError:
        return MigrationResult(source_file, family, "", "invalid-source", ("invalid-path",), None, None)
    if slug in colliding_slugs:
        return MigrationResult(source_file, family, slug, "manual-review", ("normalized-slug-collision",), None, None)
    if not isinstance(document, dict):
        return MigrationResult(source_file, family, slug, "invalid-source", ("root-not-object",), None, None)
    display_name = _safe_text(document.get("name"), 100)
    if display_name is None:
        return MigrationResult(source_file, family, slug, "manual-review", ("missing-display-name",), None, None)

    spec = {"display_name": display_name}
    dropped = []
    for source_key, target_key in FIELD_MAP[family].items():
        if source_key == "name":
            continue
        if source_key not in document:
            continue
        value = _safe_tag(document[source_key])
        if value is None:
            dropped.append(f"invalid-{source_key}")
        else:
            spec[target_key] = value

    target_file = f"templates/{family}/{slug}/v1.0.0/template.json"
    result = MigrationResult(
        source_file=source_file,
        family=family,
        slug=slug,
        disposition="migrated",
        reason_codes=tuple(sorted(dropped)),
        target_file=target_file,
        document=None,
    )
    document_v1 = build_v1_document(result, spec)
    return MigrationResult(**{**result.__dict__, "document": document_v1})


def build_v1_document(result: MigrationResult, spec: dict[str, Any]):
    return {
        "$schema": f"../../../schemas/{result.family}/v1.0.0/schema.json",
        "contract_version": "1.0.0",
        "id": f"{result.family}:{result.slug}",
        "slug": result.slug,
        "family": result.family,
        "version": "1.0.0",
        "authority": "declarative",
        "intended_consumers": list(INTENDED_CONSUMERS),
        "compatibility": [],
        "dependencies": [],
        "spec_checksum": compute_spec_checksum(spec),
        "spec": spec,
    }
```

- [ ] **Step 4: Verify GREEN and full regression suite**

Run:

```powershell
rtk python -m unittest discover -s tests -p "test_pilot_contracts.py" -v
rtk python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit Task 1**

```powershell
rtk git add -- scripts/pilot_contracts.py tests/test_pilot_contracts.py
rtk git commit -m "feat(migration): add pilot disposition engine"
```

---

### Task 2: Generate five strict family schemas

**Files:**
- Modify: `scripts/pilot_contracts.py`
- Modify: `tests/test_pilot_contracts.py`
- Create: `templates/schemas/classes/v1.0.0/schema.json`
- Create: `templates/schemas/races/v1.0.0/schema.json`
- Create: `templates/schemas/items/v1.0.0/schema.json`
- Create: `templates/schemas/spells/v1.0.0/schema.json`
- Create: `templates/schemas/monsters/v1.0.0/schema.json`

**Interfaces:**
- Consumes: `family_schema(family: str) -> dict[str, Any]`.
- Produces: five byte-stable Draft 2020-12 schemas that compose the common contract and close `spec`.

- [ ] **Step 1: Add failing schema tests**

Add to `tests/test_pilot_contracts.py`:

```python
from jsonschema import Draft202012Validator
from scripts.pilot_contracts import family_schema


class PilotSchemaTests(unittest.TestCase):
    def test_all_pilot_schemas_are_valid_and_close_spec(self):
        for family in ("classes", "races", "items", "spells", "monsters"):
            with self.subTest(family=family):
                schema = family_schema(family)
                Draft202012Validator.check_schema(schema)
                spec_schema = schema["allOf"][1]["properties"]["spec"]
                self.assertFalse(spec_schema["additionalProperties"])
                self.assertEqual(spec_schema["required"], ["display_name"])

    def test_spell_schema_rejects_runtime_fields(self):
        schema = family_schema("spells")
        spec_schema = schema["allOf"][1]["properties"]["spec"]
        self.assertNotIn("cooldown", spec_schema["properties"])
        self.assertNotIn("damage", spec_schema["properties"])
        self.assertNotIn("mana_cost", spec_schema["properties"])
```

- [ ] **Step 2: Verify RED**

Run the focused test and expect an import failure for `family_schema`.

- [ ] **Step 3: Implement schema generation**

Add a `SPEC_FIELDS` mapping whose optional fields exactly match `FIELD_MAP` targets. Implement:

```python
def family_schema(family: str):
    if family not in PILOT_FAMILIES:
        raise ValueError(f"unsupported pilot family: {family}")
    properties = {
        "display_name": {"type": "string", "minLength": 1, "maxLength": 100},
    }
    for field in SPEC_FIELDS[family]:
        properties[field] = {
            "type": "string",
            "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
            "maxLength": 64,
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://ultimateodycer.com/schemas/{family}/1.0.0",
        "title": f"Ultimate Odycer {family} Template v1",
        "allOf": [
            {"$ref": "https://ultimateodycer.com/schemas/template-contract/1.0.0"},
            {"properties": {"spec": {
                "type": "object",
                "required": ["display_name"],
                "properties": properties,
                "additionalProperties": False,
            }}},
        ],
    }
```

Generate each schema using `json.dumps(schema, indent=2, ensure_ascii=False) + "\n"` and `apply_patch`; do not use a shell redirect.

- [ ] **Step 4: Validate schemas locally**

Run the focused tests, then call `validate_schema_references` for all five schema paths. Expected: zero errors.

- [ ] **Step 5: Commit Task 2**

Stage only `scripts/pilot_contracts.py`, `tests/test_pilot_contracts.py`, and the five new schema files. Commit `feat(schema): add pilot family contracts`.

---

### Task 3: Deterministic migration writer and catalog transaction

**Files:**
- Create: `scripts/migrate_pilot_families.py`
- Create: `tests/test_pilot_migration.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `build_migration(root: Path, families: tuple[str, ...]) -> MigrationPlan`, `write_migration(root: Path, plan: MigrationPlan)`, and `check_migration(root: Path, plan: MigrationPlan) -> list[str]`.
- Produces: deterministic v1 files, schema/template catalog entries, reviewed legacy metadata, and `MIGRATION-V1.json`.

- [ ] **Step 1: Write failing filesystem tests**

Create a temporary registry with one legacy item, one colliding class pair, catalog v2, common schema, and generated pilot schemas. Assert:

```python
plan = build_migration(root, ("items", "classes"))
self.assertEqual(plan.counts, {"migrated": 1, "manual-review": 2})
write_migration(root, plan)
self.assertTrue((root / "templates/items/iron-ore/v1.0.0/template.json").is_file())
self.assertFalse((root / "templates/classes/mage/v1.0.0/template.json").exists())
self.assertEqual(check_migration(root, build_migration(root, ("items", "classes"))), [])
self.assertEqual(hashlib.sha256(legacy_item.read_bytes()).hexdigest(), legacy_sha_before)
```

Also assert the v1 item catalog entry uses `strict-v1`, the schema entry uses `strict-schema-v1`, the legacy item gains exact `id`, `family`, `slug`, and `superseded_by`, and both colliding class entries gain no supersession metadata.

- [ ] **Step 2: Verify RED**

Run `test_pilot_migration.py`; expect `scripts.migrate_pilot_families` to be missing.

- [ ] **Step 3: Implement the migration plan model**

Use immutable records:

```python
@dataclass(frozen=True)
class GeneratedFile:
    path: str
    content: bytes

@dataclass(frozen=True)
class MigrationPlan:
    results: tuple[MigrationResult, ...]
    generated_files: tuple[GeneratedFile, ...]
    catalog: dict[str, Any]
    report: dict[str, Any]
    counts: dict[str, int]
```

`build_migration` MUST:

1. enumerate legacy `template.json` paths only, excluding every `v1.0.0` path;
2. calculate collisions before conversion;
3. parse with `decode_json_bytes`;
4. convert every source exactly once;
5. add v1 entries with real SHA-256 and `spec_checksum`;
6. add schema entries with `strict-schema-v1` if absent;
7. add exact legacy `id`, `slug`, `family`, and `superseded_by` only for migrated documents;
8. add `supersedes: ["family:slug@0.1.0"]` to the v1 entry;
9. sort results by `source_file` and generated files by path;
10. create report counts whose sum equals the number of enumerated sources.

`write_migration` MUST refuse overwriting a non-identical existing v1 file. `check_migration` compares expected bytes, catalog JSON, and report JSON without writing.

- [ ] **Step 4: Add the CLI**

Support:

```text
--root <path>                 default .
--families <comma-list>       required subset of pilot families
--write                       write generated output
--check                       verify idempotent output
```

Exactly one of `--write` or `--check` is required.

- [ ] **Step 5: Verify GREEN and commit**

Run focused tests and the full suite. Commit the writer, tests, and `.gitignore` change as `feat(migration): add deterministic pilot writer`.

---

### Task 4: Migrate classes, races, and items

**Files:**
- Create: v1 templates under `templates/classes`, `templates/races`, and `templates/items`
- Modify: `templates/catalog.json`
- Create/Modify: `MIGRATION-V1.json`

**Interfaces:**
- Consumes: Task 3 CLI with `--families classes,races,items`.
- Produces: strict-v1 output for every unambiguous source and explicit dispositions for all 276 sources.

- [ ] **Step 1: Capture legacy hashes**

Run this read-only PowerShell check and retain the printed digest in the task log:

```powershell
rtk powershell -NoProfile -Command '$families=@("classes","races","items"); $rows=foreach($family in $families){ Get-ChildItem -LiteralPath (Join-Path "templates" $family) -Recurse -File -Filter template.json | Where-Object { $_.Directory.Name -ne "v1.0.0" } | Sort-Object FullName | ForEach-Object { $relative=$_.FullName.Substring((Resolve-Path .).Path.Length+1).Replace("\","/"); "$relative $((Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLower())" } }; $bytes=[Text.Encoding]::UTF8.GetBytes(($rows -join "`n")); $sha=[Security.Cryptography.SHA256]::HashData($bytes); "legacy_aggregate=" + [Convert]::ToHexString($sha).ToLower()'
```

Do not create a committed baseline file.

- [ ] **Step 2: Run migration write**

```powershell
rtk python scripts/migrate_pilot_families.py --families classes,races,items --write
```

- [ ] **Step 3: Run strict checks**

```powershell
rtk python scripts/migrate_pilot_families.py --families classes,races,items --check
rtk python scripts/validate_registry.py --report validation-report.json
```

Expected: zero validator issues; 14 colliding class files are `manual-review`; no ordinal class slug exists.

- [ ] **Step 4: Recompute legacy aggregate**

Run the exact command from Step 1 again. Expected: exact equality with the recorded digest.

- [ ] **Step 5: Commit Task 4**

Stage only the three families' v1 files, catalog, and migration report. Commit `feat(migration): migrate class race and item pilots`.

---

### Task 5: Migrate spells and monsters

**Files:**
- Create: v1 templates under `templates/spells` and `templates/monsters`
- Modify: `templates/catalog.json`
- Modify: `MIGRATION-V1.json`

**Interfaces:**
- Consumes: Task 3 CLI with all five pilot families so the report remains exhaustive and deterministic.
- Produces: strict-v1 output or an explicit non-migrated disposition for all 2,327 pilot sources.

- [ ] **Step 1: Write a failing recursive runtime-field test**

Add `from scripts.pilot_contracts import find_forbidden_runtime_keys` and a test that migrates representative spell and monster documents, then calls the missing function:

```python
FORBIDDEN_RUNTIME_KEYS = {
    "base_stats", "stats", "damage", "range", "cast_time", "cooldown",
    "mana_cost", "effects", "loot_table", "ai_behavior", "abilities",
    "resistances", "weaknesses", "properties", "visual_effects", "sound_effects",
}
```

```python
self.assertEqual(find_forbidden_runtime_keys(spell_result.document), set())
self.assertEqual(find_forbidden_runtime_keys(monster_result.document), set())
```

Run the focused test. Expected RED: import failure because `find_forbidden_runtime_keys` does not exist.

- [ ] **Step 2: Implement the recursive guard**

Add the exact public constant above and implement:

```python
def find_forbidden_runtime_keys(value: Any) -> set[str]:
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_RUNTIME_KEYS:
                found.add(key)
            found.update(find_forbidden_runtime_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(find_forbidden_runtime_keys(child))
    return found
```

Call this guard from `build_migration`; any generated document containing a forbidden key raises `ValueError` before writes.

- [ ] **Step 3: Run the complete write**

```powershell
rtk python scripts/migrate_pilot_families.py --families classes,races,items,spells,monsters --write
```

- [ ] **Step 4: Verify exhaustive accounting**

Assert in a test and command-line check:

```text
sum(MIGRATION-V1.json summary dispositions) == 2327
every source_file appears once
every migrated target_file exists once
every non-migrated result has target_file null
```

- [ ] **Step 5: Run full tests and validator**

Expected: zero validation issues and no legacy-byte changes.

- [ ] **Step 6: Commit Task 5**

Commit generated spell/monster v1 files, updated catalog/report, and regression test as `feat(migration): migrate spell and monster pilots`.

---

### Task 6: Generate family READMEs

**Files:**
- Create: `templates/classes/README.md`
- Create: `templates/races/README.md`
- Create: `templates/items/README.md`
- Create: `templates/spells/README.md`
- Create: `templates/monsters/README.md`
- Modify: `scripts/pilot_contracts.py`
- Modify: `tests/test_pilot_contracts.py`

**Interfaces:**
- Consumes: `family_readme(family: str) -> str`.
- Produces: five deterministic READMEs documenting purpose, required/optional fields, exclusions, exact schema, consumers, evidence state, and versioning.

- [ ] **Step 1: Write a failing README contract test**

For every pilot family, assert the rendered README contains these headings:

```text
# <Family> templates
## Purpose
## Required fields
## Optional fields
## Authoritative exclusions
## Intended consumers
## Compatibility evidence
## Versioning
```

Also assert `Compatibility evidence` states `None verified` and every runtime exclusion from that family is named.

- [ ] **Step 2: Verify RED and implement `family_readme`**

Use family metadata constants; do not infer documentation from legacy files. Render LF-terminated Markdown with no placeholder language.

- [ ] **Step 3: Generate and inspect the five files**

Use `apply_patch` with the renderer output. Run `git diff --check` and focused tests.

- [ ] **Step 4: Commit Task 6**

Commit the renderer, tests, and five README files as `docs: add pilot family contracts`.

---

### Task 7: Read-only Zig link-readiness audit

**Files:**
- Create: `scripts/audit_zig_link_candidates.py`
- Create: `tests/test_zig_link_audit.py`
- Modify: `.gitignore`
- Local ignored output: `local-audit/zig-link-readiness.json`

**Interfaces:**
- Consumes: `audit_links(registry_root: Path, server_root: Path) -> dict[str, Any]`.
- Produces: per-migrated-template dispositions `exact-source-path`, `unique-basename`, `unique-id`, `ambiguous`, or `missing`, using server-root-relative paths only.

- [ ] **Step 1: Write failing resolution tests**

Create temporary registry/server trees proving:

- an existing catalog `source_file` relative path wins;
- a unique basename is accepted only when exact path is absent;
- a unique parsed JSON `id` is accepted only when path and basename fail;
- two basename or ID matches are `ambiguous`;
- no match is `missing`;
- output never contains the absolute temporary root.

- [ ] **Step 2: Verify RED**

Expected: import failure for `scripts.audit_zig_link_candidates`.

- [ ] **Step 3: Implement bounded read-only audit**

The audit MUST:

1. read `MIGRATION-V1.json` and catalog only;
2. consider only `migrated` pilot results;
3. enumerate server `*.json` below the supplied root while excluding `_versions`;
4. parse IDs with `decode_json_bytes`, treating parse failures as non-matches;
5. apply exact path, unique basename, then unique ID in that order;
6. return sorted relative paths and counts;
7. never modify either input tree;
8. set `compatibility_claimed: false` in the report.

- [ ] **Step 4: Add CLI and local ignore**

Support `--registry-root`, `--server-root`, and `--report`. Add `local-audit/` to `.gitignore`.

- [ ] **Step 5: Run against the real Zig template tree**

```powershell
rtk python scripts/audit_zig_link_candidates.py --registry-root . --server-root "F:/_Serv ULtimate Od/Development/Backend/Servers/zig-server-v2/templates" --report local-audit/zig-link-readiness.json
```

Report exact counts for every disposition. Do not mark any template compatible and do not modify `zig-server-v2`.

- [ ] **Step 6: Commit Task 7**

Commit only script, tests, and `.gitignore` as `feat(audit): add Zig link readiness report`. The local report remains ignored.

---

### Task 8: Final pilot proof gate

**Files:**
- Test: complete repository

**Interfaces:**
- Consumes: Tasks 1-7.
- Produces: a clean reviewable branch with exhaustive migration and explicit remaining gaps.

- [ ] **Step 1: Run fresh dependency, test, migration, and validation gates**

```powershell
rtk python -m pip install --disable-pip-version-check -r requirements-dev.txt
rtk python -m unittest discover -s tests -v
rtk python scripts/migrate_catalog_v2.py --check
rtk python scripts/migrate_pilot_families.py --families classes,races,items,spells,monsters --check
rtk python scripts/validate_registry.py --report validation-report.json
rtk proxy git diff --check
```

- [ ] **Step 2: Prove exhaustive disposition accounting**

Run:

```powershell
rtk powershell -NoProfile -Command '$report=Get-Content -Raw -LiteralPath "MIGRATION-V1.json" | ConvertFrom-Json; $results=@($report.results); $unique=@($results.source_file | Sort-Object -Unique); $grouped=@{}; $results | Group-Object disposition | ForEach-Object { $grouped[$_.Name]=$_.Count }; if($results.Count -ne 2327){throw "expected 2327 results, got $($results.Count)"}; if($unique.Count -ne $results.Count){throw "duplicate source_file"}; foreach($property in $report.summary.dispositions.PSObject.Properties){ if($grouped[$property.Name] -ne [int]$property.Value){throw "summary mismatch for $($property.Name)"} }; "migration_accounting=2327"'
```

- [ ] **Step 3: Prove legacy immutability**

List every changed path below the five families. Permit only:

```text
templates/<family>/README.md
templates/<family>/<slug>/v1.0.0/template.json
```

Any changed legacy `v0.1.0`, atypical `0.1.0`, or version README path blocks completion.

Run:

```powershell
rtk powershell -NoProfile -Command '$families="classes|races|items|spells|monsters"; $changed=git diff --name-only origin/main -- templates; $pilot=$changed | Where-Object { $_ -match "^templates/($families)/" }; $unexpected=$pilot | Where-Object { $_ -notmatch "^templates/($families)/README\.md$" -and $_ -notmatch "^templates/($families)/[^/]+/v1\.0\.0/template\.json$" }; "pilot_changed=$($pilot.Count)"; "unexpected_legacy_changes=$($unexpected.Count)"; if($unexpected){$unexpected; exit 1}'
```

- [ ] **Step 4: Re-run Zig audit and inspect gaps**

The report may contain `ambiguous` or `missing`; those are honest inputs to the next Zig-adapter plan, not failures of this registry migration. The gate fails only if the report is absent, internally inconsistent, contains absolute paths, or claims compatibility.

- [ ] **Step 5: Run checkup**

```powershell
rtk powershell -NoProfile -Command '$env:PYTHONPATH="C:/Users/redga/botte-secrete"; python -m skills.checkup.cli .'
```

Report infrastructure warnings separately from template-contract failures.

- [ ] **Step 6: Inspect branch and publish only after review**

Run status, log, and diff-stat commands. Keep the worktree and branch; do not merge PR #3 or create a pilot PR without an explicit integration choice.

## Plan Self-review Result

| Pilot requirement | Covered by |
| --- | --- |
| Deterministic allowlist conversion | Task 1 |
| One strict schema per family | Task 2 |
| Catalog/report/idempotent writer | Task 3 |
| Classes, races, items | Task 4 |
| Spells, monsters, runtime omission | Task 5 |
| Family documentation | Task 6 |
| Read-only Zig link audit | Task 7 |
| Full validation, accounting, immutability | Task 8 |

No pilot requirement is unassigned. Actual Zig parsing, profile binding, feature flags, ECS integration, and compatibility evidence remain outside this plan and belong to the next adapter-specific plan.
