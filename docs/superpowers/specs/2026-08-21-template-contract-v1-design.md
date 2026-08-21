# Template Contract v1 and Zig Compatibility Design

**Status:** Approved in principle on 2026-08-21; implementation requires review of this written design.

## Purpose

Define a strict, public, declarative template contract without rewriting already published `v0.1.0` snapshots, then prove that adopting the contract does not silently break Ultimate Odycer's Zig server template links.

The public registry and the server runtime have different responsibilities:

- the registry describes portable content contracts and logical references;
- the Zig server owns gameplay authority, balance, permissions, persistence, runtime timing, spawn decisions, loot resolution, and asset resolution;
- an explicit adapter may project an approved registry document into a server-owned type;
- the Zig server must never execute a registry document directly as authoritative configuration.

## Measured Baseline

The 2026-08-21 audit found:

- 4,047 `template.json` documents and 16 `schema.json` documents;
- 66 top-level template families;
- one family-level README;
- 4,063 catalog entries and 4,064 JSON documents including the catalog;
- 1,934 catalog entries with `source_file` metadata;
- 111 `source_file` names resolving uniquely in the current server template tree;
- 10 resolving ambiguously by basename;
- 1,813 not resolving by basename;
- no direct compatibility between the registry's versioned paths and the server's current flat `templates/<type>/<id>.json` lookup.

The current registry validator checks JSON parsing, catalog membership, SHA-256 integrity, public-content policy, and forbidden hash-placeholder paths. It does not enforce `TEMPLATE-SPEC.md`, per-family schemas, reference closure, naming consistency, or declarative authority.

## Goals

1. Preserve every published `v0.1.0` document byte-for-byte as legacy history.
2. Introduce a strict common envelope for all conforming `v1.x` documents.
3. Give every migrated family a Draft 2020-12 JSON Schema and a family README.
4. Normalize names and types without inventing data.
5. Remove runtime authority, implicit assets, long lore, and dialogue from public `v1` documents.
6. Replace runtime values with server-owned logical profile references where the concept remains useful.
7. Validate all catalog paths, schema references, logical references, aliases, and checksums.
8. Add a fail-closed Zig adapter and link audit before claiming any server compatibility.
9. Migrate families in independently reviewable cohorts and publish an explicit exception report.

## Non-goals

- Rewriting or deleting existing `v0.1.0` snapshots.
- Copying server implementation, private paths, runtime configuration, production data, or proprietary logic into the public registry.
- Making the public registry the Zig server's live configuration directory.
- Declaring Godot, VR, Zig, or LLM compatibility without versioned evidence.
- Assigning artificial versions merely to make families appear different.
- Creating empty `v1` templates when safe semantic content cannot be recovered.

## Selected Architecture

```text
legacy v0.1.0 snapshots
        |
        | audit only; never auto-consumed
        v
registry migration pipeline --> strict v1 envelope + family schema
                                      |
                                      | catalog, schema, reference and policy validation
                                      v
                               approved public artifact
                                      |
                    +-----------------+-----------------+
                    |                                   |
             Zig adapter                         other adapters
        validate -> map -> project             Godot / LLM, separately
                    |
                    v
          server-owned typed DTOs
                    |
                    v
     authoritative profiles and runtime logic
```

There is no direct path from a public template to runtime authority.

## Common v1 Envelope

Every conforming `template.json` must use this shape:

```json
{
  "$schema": "../../../schemas/monsters/v1.0.0/schema.json",
  "contract_version": "1.0.0",
  "id": "monsters:forest-wolf",
  "slug": "forest-wolf",
  "family": "monsters",
  "version": "1.0.0",
  "authority": "declarative",
  "intended_consumers": ["zig-server-v2", "godot-vr", "llm-pipeline"],
  "compatibility": [],
  "dependencies": [],
  "spec_checksum": "sha256:<canonical-spec-digest>",
  "spec": {}
}
```

### Envelope rules

- JSON property names use ASCII `snake_case`.
- Directory names and `slug` use ASCII `kebab-case`.
- `id` is `<family>:<slug>` and is immutable after publication.
- `family` must equal the top-level family directory.
- `version` must equal the version directory without its `v` prefix.
- `contract_version` versions the common envelope independently of family content.
- `authority` has the single allowed v1 value `declarative`.
- `intended_consumers` states routing intent, not proven compatibility.
- `compatibility` remains empty until an exact consumer version and evidence reference are recorded.
- `dependencies` contains canonical registry IDs, never paths or display names.
- `spec` contains only family-specific declarative content.
- The common and family schemas use `additionalProperties: false` at every object boundary unless an explicitly typed extension map is required.

### Checksums

The catalog SHA-256 covers the complete file bytes and remains the publication-integrity value. `spec_checksum` covers canonical JSON serialization of `spec` using sorted keys, UTF-8, no insignificant whitespace, and JSON number semantics. This avoids an impossible self-referential whole-file checksum.

The validator recomputes both values. A mismatch fails publication.

## Legacy Policy

Published `v0.1.0` files remain unchanged. Their catalog entries gain non-content metadata:

```json
{
  "validation_profile": "legacy-unvalidated",
  "contract_version": null,
  "superseded_by": "monsters:forest-wolf@1.0.0"
}
```

`superseded_by` is present only after a v1 replacement passes all gates. Legacy files continue to receive JSON, security, path, and checksum checks, but they do not receive a false v1 compliance claim. Consumers must opt in explicitly to legacy documents; strict consumers reject them by default.

## Family Contracts

Each migrated family receives:

```text
templates/schemas/<family>/v1.0.0/schema.json
templates/<family>/README.md
```

The schema composes the common envelope and defines the exact `spec` type. The README documents:

- purpose and excluded responsibilities;
- required and optional fields;
- allowed logical references;
- declarative versus authoritative boundaries;
- canonical minimal and advanced examples;
- intended consumers and current compatibility evidence;
- independent family version history;
- migration notes and known exclusions.

The schema is the sole machine-readable source for required fields. Templates do not duplicate a `required_fields` list.

## Normalized Types

The following common concepts have one representation in v1:

| Concept | Canonical representation |
| --- | --- |
| identifier | namespaced string `<family>:<slug>` |
| slug | `kebab-case` string |
| coordinates | object `{ "x": number, "y": number, "z": number }` with documented unit |
| tags | unique array of `kebab-case` strings |
| dependencies | unique array of canonical IDs |
| rewards | array of typed declarative references, never free-form strings |
| stats | forbidden in the common envelope; family schemas may expose symbolic `balance_profile_id` only |
| durations | forbidden when they control runtime; descriptive durations require explicit units and family justification |
| assets | logical `asset_ref` string only, optional, with no file path or availability claim |

Migration never changes an array into an object, or a string into a structured value, by guessing. Ambiguous cases are reported and remain legacy-only.

## Declarative and Authoritative Separation

| Public declarative content | Server-authoritative content |
| --- | --- |
| identity, category, tags | HP, damage, armor, economy values |
| logical dependencies | cooldowns, cast timing, tick timing |
| capability or role labels | spawn rates, waves, population budgets |
| symbolic `balance_profile_id` | profile values and balance formulas |
| symbolic `loot_table_id` | drop probabilities and loot rolls |
| symbolic `behavior_profile_id` | AI decision weights and execution |
| optional logical `asset_ref` | filesystem paths, bundle IDs, load policy |

Long lore, dialogue, narrative prose, embedded scripts, and behavior trees are excluded from v1. A short human description is allowed only when it is bounded by the family schema.

## Catalog and Reference Model

The catalog becomes the canonical index. Every v1 entry includes:

- `id`, `slug`, `family`, `kind`, `version`, `contract_version`;
- `validation_profile: "strict-v1"`;
- `schema_file`, `file`, full-file `sha256`, and `spec_checksum`;
- `status`, `intended_consumers`, `compatibility`, and `supersedes`;
- an opaque `provenance_ref` when private audit provenance exists.

Raw private paths and ambiguous basenames are not links. Existing `source_file` values are retained only on legacy entries. V1 uses opaque provenance references whose resolution remains outside the public repository.

All dependency and supersession references must resolve to exactly one catalog entry. Aliases are explicit, versioned, acyclic, and map a previous canonical ID to a current canonical ID. Silent fuzzy matching is forbidden.

## Zig Server Compatibility

### Current incompatibilities

The current server template manager:

- loads `templates/<type>/<id>.pb` or `templates/<type>/<id>.json`;
- stores template version as `u32`;
- accepts a numeric JSON `version` and otherwise defaults to `1`;
- registers validators under server-specific singular and plural type names;
- parses loaded JSON directly into server-owned structs;
- sometimes uses `ignore_unknown_fields = true`;
- contains runtime-authoritative fields such as base stats, cooldowns, rewards, AI cadence, and thresholds.

The registry's nested SemVer paths and v1 envelope therefore cannot be passed directly to `TemplateManager.loadTemplate`.

### Required adapter boundary

The Zig server receives a new opt-in adapter with four stages:

1. **Verify:** parse the common envelope, require `authority == "declarative"`, verify the supported contract and family schema versions, and verify the catalog checksum.
2. **Resolve:** resolve canonical IDs and explicit aliases; reject missing, ambiguous, cyclic, or cross-family references.
3. **Project:** convert `spec` into a narrowly scoped server ingestion DTO. The DTO may contain symbolic profile IDs but never imports public balance values as authority.
4. **Bind:** resolve symbolic profiles through server-owned registries and validators before any ECS or runtime mutation.

The adapter is disabled by default. The existing flat server templates remain the active source until a family-specific compatibility gate passes. Failure is closed: no fallback to a similarly named template, default privileged resource, or partially parsed document.

### Link preservation

For each migrated family, a private server-side mapping records:

```text
server template type + server template id
    -> registry canonical id + exact registry version
    -> adapter projection version
    -> evidence test
```

The public registry stores only the canonical ID and compatibility evidence reference. It does not publish local server paths.

Before enabling a family, the link audit must prove:

- every mapped registry path exists and matches its catalog checksum;
- every `$schema`, dependency, alias, and supersession link resolves once;
- every server target type and ID exists or is deliberately introduced by the adapter;
- no two registry IDs map to the same authoritative server target unless an explicit alias documents it;
- removing or renaming a registry document is detected by CI;
- legacy server loading still succeeds with the adapter disabled.

## Migration Pipeline

Each legacy document receives exactly one migration disposition:

- `migrated`: deterministic safe conversion produced a strict v1 document;
- `manual-review`: useful declarative content exists but a type or reference is ambiguous;
- `legacy-only-authoritative`: content is primarily runtime authority and remains server-side;
- `legacy-only-narrative`: content is primarily lore, dialogue, or long prose;
- `excluded-public-policy`: content violates public security, privacy, commercial, or rights policy;
- `invalid-source`: the legacy JSON or its catalog linkage is invalid.

Migration output includes counts and per-document reasons. Only `migrated` documents receive `superseded_by`. The pipeline must be deterministic and idempotent.

## Validation Profiles

### Legacy profile

- valid UTF-8 JSON;
- public policy scan;
- forbidden-path scan;
- catalog membership;
- full-file checksum.

### Strict v1 profile

All legacy checks plus:

- Draft 2020-12 schema validation;
- common-envelope and family-schema validation;
- path, family, ID, slug, and version agreement;
- `snake_case` keys and `kebab-case` slugs;
- `additionalProperties: false` enforcement;
- canonical `spec_checksum`;
- dependency, alias, schema, supersession, and evidence-link closure;
- declarative-authority policy;
- forbidden runtime, narrative, asset-path, internal, commercial, administrative, and third-party fields;
- bounded strings, arrays, nesting depth, file size, and numeric ranges.

Validation failure blocks publication. The validator prints every failure in a machine-readable report and a bounded human summary.

## Versioning

`contract_version`, family schema version, and template content version evolve independently.

- The first conforming envelope is `contract_version: 1.0.0`.
- Each family's first strict schema may be `1.0.0`; equal initial numbers do not imply coupled future releases.
- A template's `version` changes only when that template changes.
- A family schema changes only when its contract changes.
- The common contract changes only when the envelope changes.
- Published version directories are immutable.
- Breaking schema or semantic changes require a major version.
- Migration from legacy is recorded as a new v1 version, never an in-place rewrite.

## Rollout and Proof Gates

The work is split into independently reviewable subprojects:

1. **Registry contract foundation:** common schema, catalog format, strict validator, canonical checksum rules, and tests.
2. **Pilot families:** migrate `classes`, `races`, `items`, `spells`, and `monsters`; generate their family READMEs and migration report.
3. **Zig adapter and link audit:** add the disabled-by-default adapter, projections for pilot families, mapping audit, and isolated server tests.
4. **Bulk family cohorts:** migrate remaining families in bounded groups, with manual-review and legacy-only dispositions.
5. **Other consumers:** add Godot/VR and LLM adapters only after separate compatibility designs and evidence.

A family is not marked compatible until registry validation, adapter unit tests, server typed parsing, link closure, and an isolated end-to-end load all pass. A schema-valid fixture alone is not runtime proof.

## Test Strategy

### Registry tests

- reject missing common fields and unknown fields;
- reject mixed naming styles and path/version mismatches;
- reject inconsistent representations of coordinates, rewards, and references;
- reject runtime-authoritative, narrative, implicit-asset, administrative, internal, and commercial fields;
- reject missing, ambiguous, cyclic, or cross-family references;
- verify deterministic migration and checksum output;
- prove legacy bytes are unchanged;
- prove all strict-v1 catalog entries validate against their family schema.

### Zig tests

- reject unsupported contract and family schema versions;
- reject non-declarative authority and malformed envelopes;
- reject ambiguous and broken mappings;
- reject public numeric balance values where symbolic profile references are required;
- project valid pilot documents into exact typed DTOs;
- resolve profile IDs only through server-owned registries;
- preserve existing flat-template loading when the adapter is disabled;
- fail closed when a catalog file, checksum, dependency, alias, or server profile is missing;
- perform an isolated end-to-end load for each pilot family without ECS structural mutation during queries.

## Context Map

### Files to Modify

| File | Purpose | Changes Needed |
| --- | --- | --- |
| `TEMPLATE-SPEC.md` | Public normative contract | Replace permissive historical exception with dual validation profiles and v1 rules. |
| `templates/catalog.json` | Canonical registry index | Add strict-v1 metadata, schema links, opaque provenance, aliases, and legacy status. |
| `scripts/validate_registry.py` | Publication gate | Split validation profiles and enforce schemas, naming, checksums, links, and authority. |
| `scripts/build_registry.py` | Migration and catalog builder | Produce deterministic dispositions and strict v1 output without guesses. |
| `templates/schemas/template-contract/v1.0.0/schema.json` | Common envelope schema | Define mandatory metadata and close the envelope. |
| `templates/schemas/<family>/v1.0.0/schema.json` | Family contract | Define the exact typed `spec` payload for each migrated family. |
| `templates/<family>/README.md` | Family documentation | Document purpose, fields, references, consumers, versioning, and exclusions. |
| `Development/Backend/Servers/zig-server-v2/src/core/public_template_contract.zig` | Server adapter boundary | Verify, resolve, and project public v1 documents without granting authority. |
| `Development/Backend/Servers/zig-server-v2/src/data/public_template_links.zig` | Private server mapping | Map server IDs to exact registry IDs and adapter projection versions. |
| `Development/Backend/Servers/zig-server-v2/build.zig` | Zig module and test wiring | Register adapter and isolated compatibility tests. |

### Dependencies That May Need Updates

| File | Relationship |
| --- | --- |
| `src/core/templates.zig` | Existing flat loader, validators, numeric version model, cache, archive, and save behavior. |
| `src/core/hybrid_template_manager.zig` | Existing cache/secure/file fallback path; adapter must remain outside its default path initially. |
| `src/data/template_schemas.zig` | Server-authoritative typed structs and runtime fields used as projection targets. |
| `src/core/character.zig` | Direct class/race template loading and typed parsing. |
| `src/game/class_race_system.zig` | Direct class/race/talent loading and runtime application. |
| `src/embedded_templates.zig` | Embedded fallback behavior that must not hide broken public links. |
| `asset_registry.json` | Existing hashes and server template paths; audit input, not a public link manifest. |
| `sdk.manifest.json` | References server schema paths that must remain valid. |

### Test Files

| Test | Coverage |
| --- | --- |
| `tests/test_build_registry.py` | Deterministic sanitization and migration behavior. |
| `tests/test_validate_registry.py` | Public policy and strict registry validation. |
| `src/tests/test_templates.zig` | Existing hybrid manager loading, caching, hot reload, and schema behavior. |
| `tests/test_spell_templates.zig` | Current spell template parsing and behavior. |
| `tests/test_monster_templates.zig` | Current monster template parsing and behavior. |
| `tests/test_quest_templates.zig` | Current quest template parsing and behavior. |
| `tests/test_god_templates.zig` | Current god template parsing and behavior. |
| `tests/public_template_contract_test.zig` | New envelope, mapping, projection, failure, and compatibility tests. |

### Reference Patterns

| File | Pattern |
| --- | --- |
| `src/core/addon_manifest.zig` | Fail-closed dynamic JSON validation with explicit required fields. |
| `src/core/creature_locomotion_contract.zig` | Versioned envelope parsing and bounded validation. |
| `src/data/template_schemas.zig` | Typed server-owned DTOs and explicit semantic validators. |
| `scripts/validate_registry.py` | Existing catalog and checksum traversal to extend. |

### Risk Assessment

- [x] Breaking changes to public API: isolated behind v1; legacy remains immutable.
- [ ] Database migrations needed: none in the contract foundation or pilot adapter.
- [x] Configuration changes required: a server feature flag is required before any adapter activation.
- [x] Runtime authority risk: mitigated by symbolic references and server-side binding.
- [x] Broken-link risk: mitigated by exact mappings, reference closure, and fail-closed CI.
- [x] False compatibility risk: mitigated by evidence-bound compatibility entries.
- [x] Large generated diff risk: mitigated by family cohorts and deterministic manifests.

## Acceptance Criteria

The architecture is implemented only when:

1. every published legacy file remains byte-identical;
2. every strict-v1 document validates against one exact family schema;
3. every strict-v1 catalog and logical reference resolves exactly once;
4. no strict-v1 document contains server-authoritative values, implicit asset paths, long lore, or dialogue;
5. every family has a README before its first v1 publication;
6. migration reports account for every legacy document without claiming ambiguous conversions;
7. the Zig adapter remains disabled by default and existing server template tests still pass;
8. pilot link audits report zero missing or ambiguous active mappings;
9. pilot adapters pass typed parsing and isolated end-to-end loads;
10. compatibility metadata is added only with an exact consumer version and evidence reference.
