# Zig Public Template Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a disabled-by-default Zig adapter that verifies exact strict-v1 registry documents and mappings for the five pilot families without changing the existing runtime template loader or importing public balance values as authority.

**Architecture:** The adapter is an isolated Verify -> Resolve -> Project boundary beside `TemplateManager`, not inside its filesystem fallback. It accepts exact server-owned mappings, validates full-file and canonical-spec SHA-256, parses the common envelope, projects a minimal declarative DTO, and returns errors before any ECS or runtime mutation. Activation requires both a false-by-default global feature flag and an enabled exact mapping.

**Tech Stack:** Zig 0.15.2, `std.json`, `std.crypto.hash.sha2.Sha256`, existing `FeatureFlags`, existing Zig build/test modules.

**Spec:** `docs/superpowers/specs/2026-08-21-template-contract-v1-design.md`

## Global Constraints

- Server work belongs only under `Development/Backend/Servers/zig-server-v2/`.
- The public registry remains a separate repository and is read-only during server implementation.
- `TemplateManager.loadTemplate`, `HybridTemplateManager`, embedded templates, and flat legacy paths remain unchanged.
- The global flag is exactly `public_template_contract_v1` and defaults to false.
- Missing, ambiguous, disabled, stale-checksum, unsupported-version, or invalid-family mappings fail closed.
- No fuzzy matching, basename fallback, implicit latest version, or automatic mapping from the audit report is permitted.
- Public HP, damage, armor, cooldown, range, cost, loot, probability, AI weight, timing, or asset path values are never projected.
- No database migration, external listener, server restart, production data, or runtime deployment is authorized.
- Compatibility metadata remains empty until the adapter passes exact mapping, typed projection, legacy isolation, and isolated end-to-end proof gates.

## Context Map

### Files to Modify

| File | Purpose | Changes Needed |
| --- | --- | --- |
| `src/core/public_template_contract.zig` | New adapter boundary | Parse, verify checksums and versions, validate family specs, project DTOs. |
| `src/data/public_template_links.zig` | New server-owned mapping model | Parse exact mappings, index exact refs, reject duplicates and ambiguity. |
| `config/public_template_links.json` | Disabled mapping catalog | Store reviewed exact registry/server references; all initial entries disabled. |
| `tests/public_template_contract_test.zig` | Isolated proof | Envelope, checksum, mapping, projection, flag, and legacy isolation tests. |
| `build.zig` | Module/test wiring | Register two modules and one filtered test artifact. |
| `src/networking/server.zig` | Feature flag initialization | Register `public_template_contract_v1` as false only. |

### Dependencies

| File | Relationship |
| --- | --- |
| `src/core/templates.zig` | Existing flat loader and authoritative validators; must remain unchanged. |
| `src/core/hybrid_template_manager.zig` | Existing cache/secure/file fallback; must not import the adapter. |
| `src/data/template_schemas.zig` | Authoritative runtime DTOs; adapter does not populate numeric fields. |
| `src/core/feature_flags.zig` | Global kill switch API and deterministic rollout behavior. |
| `src/core/creature_locomotion_contract.zig` | Reference pattern for versioned envelope parsing and bounded validation. |
| `src/core/addon_manifest.zig` | Reference pattern for fail-closed dynamic JSON validation. |

### Test Files

| Test | Coverage |
| --- | --- |
| `tests/public_template_contract_test.zig` | New adapter and mapping proof. |
| `src/tests/test_templates.zig` | Existing template loading, caching, and hot reload regression. |
| `tests/test_spell_templates.zig` | Existing authoritative spell parsing regression. |
| `tests/test_monster_templates.zig` | Existing authoritative monster parsing regression. |
| `tests/test_quest_templates.zig` | Existing template infrastructure regression. |

### Risk Assessment

- [x] Breaking public/runtime API: prevented by an isolated module and false default.
- [ ] Database migration needed: none.
- [x] Configuration change: new disabled mapping file and feature flag.
- [x] Authority confusion: projection excludes every numeric/runtime field.
- [x] Broken links: exact versioned mapping and SHA-256 are mandatory.
- [x] False compatibility: public metadata remains unchanged until proof completion.

---

### Task 1: Strict envelope parser and bounds

**Files:**
- Create: `src/core/public_template_contract.zig`
- Create: `tests/public_template_contract_test.zig`
- Modify: `build.zig`

**Interfaces:**
- Produces: `parseEnvelope(allocator, bytes) !ParsedEnvelope`, `validateEnvelope(envelope) !void`, and `ParsedEnvelope.deinit()`.

- [ ] **Step 1: Write failing envelope tests**

Create tests for a valid `classes:cleric@1.0.0` envelope and these exact failures:

```zig
try std.testing.expectError(error.UnsupportedContractVersion, parseEnvelope(a, unsupported));
try std.testing.expectError(error.NonDeclarativeAuthority, parseEnvelope(a, authoritative));
try std.testing.expectError(error.IdentityMismatch, parseEnvelope(a, wrong_slug));
try std.testing.expectError(error.UnsupportedFamily, parseEnvelope(a, unknown_family));
try std.testing.expectError(error.TooLarge, parseEnvelope(a, oversized));
```

Run the new filtered test and verify RED because the module is missing.

- [ ] **Step 2: Implement bounded dynamic parsing**

Define:

```zig
pub const supported_contract_version = "1.0.0";
pub const max_document_bytes = 256 * 1024;
pub const SupportedFamily = enum { classes, races, items, spells, monsters };

pub const ParsedEnvelope = struct {
    parsed: std.json.Parsed(std.json.Value),
    id: []const u8,
    slug: []const u8,
    family: SupportedFamily,
    version: []const u8,
    spec: std.json.Value,
    spec_checksum: []const u8,
    pub fn deinit(self: *ParsedEnvelope) void { self.parsed.deinit(); }
};
```

Require root object, all common fields, `contract_version == 1.0.0`, `version == 1.0.0`, `authority == declarative`, `id == family:slug`, empty or typed arrays, object `spec`, maximum 64-byte slug, and no ignored unknown root fields. Keep `std.json.Value` ownership inside `ParsedEnvelope`.

- [ ] **Step 3: Wire the module and focused test**

Add `public_template_contract` and its imports to `build.zig`. Run the filtered test; expected GREEN.

- [ ] **Step 4: Commit**

Stage only the new module, test, and exact `build.zig` changes. Commit `feat(templates): parse strict public envelopes`.

---

### Task 2: Canonical spec checksum and full-file integrity

**Files:**
- Modify: `src/core/public_template_contract.zig`
- Modify: `tests/public_template_contract_test.zig`

**Interfaces:**
- Produces: `canonicalSpecSha256(allocator, spec) ![32]u8`, `verifySpecChecksum`, and `verifyFileChecksum`.

- [ ] **Step 1: Write failing checksum vectors**

Use the Python registry implementation to freeze three canonical vectors: reordered object keys, UTF-8 text, and nested arrays. Assert Zig produces the exact 32-byte digests and rejects uppercase, malformed, or stale `sha256:` values.

- [ ] **Step 2: Implement canonical JSON**

Recursively serialize null, bool, integer, float, string, array, and object. Sort object keys lexicographically by raw UTF-8 bytes; use no whitespace; reject non-finite floats. Feed bytes incrementally to `Sha256` rather than allocating a second full document.

- [ ] **Step 3: Implement complete-file SHA-256**

```zig
pub fn verifyFileChecksum(bytes: []const u8, expected_hex: []const u8) !void
```

Require exactly 64 lowercase hexadecimal characters and constant-time compare decoded bytes.

- [ ] **Step 4: Run focused tests and commit**

Commit `feat(templates): verify registry checksums`.

---

### Task 3: Exact server-owned mapping catalog

**Files:**
- Create: `src/data/public_template_links.zig`
- Create: `config/public_template_links.json`
- Modify: `tests/public_template_contract_test.zig`
- Modify: `build.zig`

**Interfaces:**
- Produces: `LinkCatalog.load(allocator, bytes)`, `resolveExact(registry_ref)`, and `LinkCatalog.deinit()`.

- [ ] **Step 1: Write failing mapping tests**

Test duplicate `registry_ref`, duplicate enabled `(server_type, server_id)`, invalid SemVer reference, unsupported family/type mapping, disabled entry, and missing exact reference. Assert no basename or ID fallback API exists.

- [ ] **Step 2: Implement mapping schema**

```zig
pub const LinkEntry = struct {
    registry_ref: []const u8,
    registry_file: []const u8,
    sha256: []const u8,
    server_type: []const u8,
    server_id: []const u8,
    projection_version: u16,
    enabled: bool,
};
```

Only `projection_version == 1` is supported. `resolveExact` returns `error.MappingDisabled` for a present disabled entry and `error.MappingNotFound` for absence.

- [ ] **Step 3: Create fail-closed initial configuration**

```json
{
  "mapping_version": 1,
  "entries": []
}
```

No audit candidate is automatically promoted.

- [ ] **Step 4: Run tests and commit**

Commit `feat(templates): add exact public link catalog`.

---

### Task 4: Minimal projections for five families

**Files:**
- Modify: `src/core/public_template_contract.zig`
- Modify: `tests/public_template_contract_test.zig`

**Interfaces:**
- Produces: `project(envelope) !DeclarativeProjection`.

- [ ] **Step 1: Write five failing projection tests**

Define one fixture per family and assert only these fields survive:

```zig
pub const DeclarativeProjection = struct {
    registry_id: []const u8,
    display_name: []const u8,
    category: ?[]const u8 = null,
    rarity: ?[]const u8 = null,
    kind: ?[]const u8 = null,
    target_kind: ?[]const u8 = null,
};
```

Inject `base_stats`, `cooldown`, `loot_table`, and `asset_path` into negative fixtures and require `error.UnknownSpecField`, not silent ignore.

- [ ] **Step 2: Implement exact per-family allowlists**

- classes: `display_name`, optional `resource_kind` -> `kind`;
- races: `display_name`, optional `category`, `rarity`, `faction_tag`;
- items: `display_name`, optional `category`, `rarity`, `item_kind` -> `kind`, `subtype`;
- spells: `display_name`, optional `school` -> `category`, `rarity`, `spell_kind` -> `kind`, `target_kind`;
- monsters: `display_name`, optional `category`, `rarity`.

Reject every other key.

- [ ] **Step 3: Run tests and commit**

Commit `feat(templates): project declarative pilot specs`.

---

### Task 5: Disabled feature flag and legacy isolation

**Files:**
- Modify: `src/networking/server.zig`
- Modify: `tests/public_template_contract_test.zig`
- Test: `src/tests/test_templates.zig`

**Interfaces:**
- Produces: registered false flag only; no loader integration.

- [ ] **Step 1: Write failing flag/isolation tests**

Assert a fresh server flag set reports `public_template_contract_v1 == false`. Assert existing flat template loading succeeds with the flag false. Search imports to prove `templates.zig` and `hybrid_template_manager.zig` do not import `public_template_contract`.

- [ ] **Step 2: Register the false default**

Add exactly:

```zig
try feature_flags.setBoolean("public_template_contract_v1", false);
```

Do not add percentage rollout or environment override.

- [ ] **Step 3: Run legacy and new tests**

Run the new filtered suite plus existing template, spell, monster, and quest tests. Commit `feat(templates): gate public adapter off by default`.

---

### Task 6: Reviewed fixture mappings and isolated end-to-end proof

**Files:**
- Create: `tests/fixtures/public-template-contract/` with one v1 template per family and one mapping catalog
- Modify: `tests/public_template_contract_test.zig`

**Interfaces:**
- Consumes: committed fixtures copied from exact PR #5 documents with recalculated SHA-256.
- Produces: `loadMappedProjection` isolated test helper.

- [ ] **Step 1: Select five exact fixtures**

Choose one audit result per family only when its disposition is `exact-source-path`, `unique-basename`, or `unique-id`. If a family has no unique candidate, use a test-only server ID and label it fixture-only; do not add it to production config.

- [ ] **Step 2: Write failing end-to-end tests**

For each fixture: resolve exact ref, verify file checksum, parse envelope, verify spec checksum, project DTO, and assert the expected server type/ID. Corrupt each boundary once and require the corresponding error.

- [ ] **Step 3: Run isolated proof**

This proves adapter behavior only. It does not prove live runtime consumption, ECS wiring, or production compatibility.

- [ ] **Step 4: Commit**

Commit fixtures and tests as `test(templates): prove mapped public projections`.

---

### Task 7: Full server regression and evidence report

**Files:**
- Create: `docs/testing/public-template-contract-v1.md`

**Interfaces:**
- Produces: exact commands, commit IDs, fixture refs, pass/fail counts, and explicit unproven boundaries.

- [ ] **Step 1: Run focused tests**

```powershell
rtk zig build test -Dfilter=public-template-contract
```

- [ ] **Step 2: Run existing template regressions**

Run the exact `build.zig` test steps for templates, spells, monsters, and quests discovered during implementation. Then run `rtk zig build test` and inspect full output, not exit code alone.

- [ ] **Step 3: Verify source isolation**

```powershell
rtk rg -n "public_template_contract" src/core/templates.zig src/core/hybrid_template_manager.zig src/embedded_templates.zig
```

Expected: no matches.

- [ ] **Step 4: Run project checkup**

Run the required Botte checkup from the server root and report infrastructure warnings separately.

- [ ] **Step 5: Write evidence report**

Record what passed, exact fixture mappings, flag default false, and these unresolved claims: no live loader activation, no ECS integration, no production/staging proof, no Godot/VR proof, and no public compatibility metadata.

- [ ] **Step 6: Commit and stop before publication**

Commit `docs(testing): record public template adapter proof`. Do not merge PR #5, activate mappings, restart services, or publish compatibility without a separate integration decision.

## Plan Self-review Result

| Requirement | Covered by |
| --- | --- |
| Bounded strict envelope | Task 1 |
| Canonical and full-file SHA-256 | Task 2 |
| Exact fail-closed mappings | Task 3 |
| Five-family declarative projection | Task 4 |
| False default and legacy isolation | Task 5 |
| Isolated mapped proof | Task 6 |
| Full regression and honest evidence | Task 7 |

No adapter requirement is unassigned. Live activation, authoritative profile binding, ECS integration, service restart, deployment, Godot/VR consumption, and compatibility publication remain explicitly out of scope.
