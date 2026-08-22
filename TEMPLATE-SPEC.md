# Ultimate Odycer JSON Template Specification

Specification version: `1.0.0`

Catalog version: `2.0.0`

This document defines the public contract for human contributors, generators, LLMs, clients, and server adapters. The terms **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

## 1. Validation profiles

Every catalog entry MUST declare exactly one validation profile.

| Profile | Purpose | Guarantees |
| --- | --- | --- |
| `legacy-unvalidated` | Preserve historical snapshots | Strict JSON, public policy, catalog membership, and full-file SHA-256 only |
| `strict-v1` | Versioned public template | Common envelope, exact family schema, naming, checksums, and link closure |
| `strict-schema-v1` | Versioned v1 schema | Valid Draft 2020-12 schema, stable `$id`, local reference closure, and checksum |

Legacy presence is not compatibility evidence. A strict consumer MUST reject `legacy-unvalidated` unless it explicitly opts in.

## 2. Immutable layout

A strict template MUST use:

```text
templates/<family>/<slug>/v<MAJOR>.<MINOR>.<PATCH>/template.json
```

A strict family schema MUST use:

```text
templates/schemas/<family>/v<MAJOR>.<MINOR>.<PATCH>/schema.json
```

- `<family>` and `<slug>` MUST use ASCII `kebab-case`.
- Published version directories MUST NOT be modified.
- A change creates a new version directory.
- Nested strict families such as `family/subfamily/slug` are forbidden; classification belongs in `spec`.
- Absolute paths and filesystem traversal are forbidden.

## 3. Strict v1 envelope

Every `strict-v1` template MUST contain exactly the common fields allowed by its schema:

```json
{
  "$schema": "../../../schemas/monsters/v1.0.0/schema.json",
  "contract_version": "1.0.0",
  "id": "monsters:forest-wolf",
  "slug": "forest-wolf",
  "family": "monsters",
  "version": "1.0.0",
  "authority": "declarative",
  "intended_consumers": ["zig-server-v2"],
  "compatibility": [],
  "dependencies": ["items:forest-token@1.0.0"],
  "spec_checksum": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "spec": {}
}
```

The example checksum illustrates the format only. Publication MUST use the checksum calculated from the actual `spec` value.

### 3.1 Identity

- `id` MUST equal `<family>:<slug>`.
- `family`, `slug`, and `version` MUST agree with the path.
- `contract_version` MUST be `1.0.0` for this envelope.
- `authority` MUST be `declarative`.
- IDs MUST remain stable after publication.

### 3.2 Naming and JSON types

- Property names MUST use ASCII `snake_case`.
- Slugs, tags, consumer names, and logical identifiers MUST use ASCII `kebab-case`.
- Numbers MUST be JSON numbers, never numeric strings.
- `NaN`, `Infinity`, duplicate keys, and comments are invalid JSON.
- Booleans MUST be `true` or `false`.
- Missing optional values SHOULD be omitted; `null` is allowed only when the family schema defines a distinct meaning.
- Coordinates MUST be `{ "x": number, "y": number, "z": number }` with units documented by the family.
- Rewards MUST be arrays of typed declarative references, never free-form strings.
- Unknown root and family `spec` properties MUST be rejected.

### 3.3 Exact references

Every dependency, alias, supersession, and successor reference MUST use:

```text
<family>:<slug>@<MAJOR>.<MINOR>.<PATCH>
```

References MUST resolve to exactly one catalog entry. Implicit latest-version selection, fuzzy matching, silent aliases, missing targets, self-reference, and alias cycles are forbidden.

## 4. Checksums

The catalog `sha256` covers the complete file bytes.

`spec_checksum` covers only canonical JSON serialization of `spec`:

- UTF-8;
- object keys sorted lexicographically;
- no insignificant whitespace;
- JSON separators `,` and `:`;
- non-ASCII characters preserved;
- non-finite numbers rejected.

The stored form is `sha256:<64 lowercase hexadecimal characters>`. Both the template and catalog MUST contain the computed `spec_checksum` for `strict-v1`.

## 5. Family schemas

Every strict template MUST reference one exact `strict-schema-v1` family schema.

- Schemas MUST use JSON Schema Draft 2020-12.
- `$id` MUST equal `https://ultimateodycer.com/schemas/<family>/<version>`.
- The family schema MUST compose the common contract schema and close its `spec` object with `additionalProperties: false`.
- Every required and optional field MUST have one stable type.
- Numeric fields MUST define meaningful bounds.
- Strings, arrays, objects, file size, and nesting MUST be bounded.
- `$ref` targets MUST resolve from schemas stored in this repository.
- Validation MUST NOT retrieve schemas from the network.
- Required fields live in the schema and MUST NOT be duplicated in template metadata.

## 6. Declarative and authoritative separation

The public registry describes intent. The server retains authority.

| Allowed public value | Forbidden public authority |
| --- | --- |
| identity, category, tags | HP, damage, armor, economy values |
| logical dependencies | cooldowns, cast timing, tick timing |
| capability and role labels | spawn rates, waves, population budgets |
| `balance_profile_id` | balance values and formulas |
| `loot_table_id` | drop probabilities and loot rolls |
| `behavior_profile_id` | AI decision weights and execution |
| optional logical `asset_ref` | paths, bundles, load policy, asset availability claims |

A strict template MUST NOT contain admin controls, server addresses, connection strings, secrets, production data, commercial configuration, runtime commands, embedded scripts, behavior trees, long lore, dialogue, or unverified third-party material.

The Zig server, Godot client, VR client, and LLM pipeline MUST consume strict templates through explicit adapters. No consumer may treat a public template as authorization.

## 7. Consumer metadata

`intended_consumers` is a unique array of routing hints. It does not prove support.

`compatibility` MUST remain empty until a real integration is verified. Each compatibility record MUST contain:

```json
{
  "consumer": "zig-server-v2",
  "version": "2.4.0",
  "verified_at": "2026-08-22T12:00:00Z",
  "evidence": "tests/public-template-contract/commit-abcdef1"
}
```

- `consumer` identifies one exact adapter or application.
- `version` is the exact tested version.
- `verified_at` is an ISO 8601 timestamp.
- `evidence` points to a test, report, or commit that can be inspected.
- Schema validity alone is not compatibility or runtime proof.

## 8. Catalog v2

`templates/catalog.json` is the canonical index. It MUST contain:

```json
{
  "registry_version": "2.0.0",
  "aliases": [],
  "entries": []
}
```

Every entry MUST retain its existing provenance metadata and declare:

- `name`, `kind`, `version`, `status`, `file`, `sha256`, and `compatibility`;
- `validation_profile` and `contract_version`.

A `strict-v1` entry additionally MUST declare:

- `id`, `slug`, `family`, and `schema_file`;
- `spec_checksum` and `intended_consumers`;
- `supersedes`, even when empty;
- `provenance_ref` when private provenance exists.

Raw private paths MUST NOT be added to v1 entries. Historical `source_file` fields remain legacy metadata and are not resolvable links.

## 9. Legacy preservation and migration

Existing published `v0.1.0` documents remain byte-identical and use:

```json
{
  "validation_profile": "legacy-unvalidated",
  "contract_version": null
}
```

These fields belong to the catalog entry, not the historical template file.

A migration MUST assign exactly one disposition:

- `migrated`;
- `manual-review`;
- `legacy-only-authoritative`;
- `legacy-only-narrative`;
- `excluded-public-policy`;
- `invalid-source`.

Ambiguous data MUST NOT be guessed. Only a validated v1 replacement may set `superseded_by` on a reviewed legacy catalog entry.

## 10. Independent versioning

The common contract, family schema, and individual template evolve independently.

- Major: incompatible field, type, unit, meaning, requiredness, or enumeration change.
- Minor: backward-compatible optional capability.
- Patch: correction that does not change the contract or expected behavior.

Equal initial `1.0.0` versions do not couple future releases. A consumer MUST select an exact supported version.

## 11. LLM generation rules

An LLM producing a strict template MUST:

1. select one existing family and exact schema version;
2. emit strict JSON only;
3. use the common envelope and schema-defined `spec` fields only;
4. use exact versioned references;
5. omit compatibility without evidence;
6. use symbolic profile references instead of runtime values;
7. avoid lore, dialogue, implicit assets, and invented identifiers;
8. calculate the canonical `spec_checksum`;
9. run the complete validator before proposing publication.

## 12. Zig and client rules

- The registry path layout is not the Zig server runtime layout.
- Zig MUST use an explicit, disabled-by-default adapter before consuming v1.
- The adapter MUST verify, resolve, project, and bind in separate fail-closed stages.
- Runtime profile resolution remains server-side.
- Godot and VR clients MUST NOT derive authority from template values.
- Missing references MUST fail explicitly; consumers MUST NOT select a similarly named fallback.
- Compatibility is recorded only after typed parsing, link closure, and an isolated end-to-end load pass.

## 13. Contributor commands

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/migrate_catalog_v2.py --check
python scripts/validate_registry.py --report validation-report.json
```

Publication is blocked if any command fails.
