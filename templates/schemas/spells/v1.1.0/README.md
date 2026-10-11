# Spells schema 1.1.0

Owner: Ultimate Odycer / zedarvates. Status: experimental.

Adds optional `spec.capability_tags`: 1–16 unique ASCII kebab-case labels, each
at most 64 characters. Existing 1.0.0 spec fields and requiredness are retained;
the spec remains closed to unknown properties. The 1.0.0 schema is immutable.

Labels describe capabilities for content tools and future adapters. They are
not executable effects, profile bindings, permissions, costs, damage values,
duration or availability claims. Consumers must select schema 1.1.0 explicitly.
Unknown labels must fail explicitly in an adapter, never become silent effects.

Intended consumers: LLM pipeline and future explicit Zig adapters.
Verified runtime consumer versions: none. Schema tests are not runtime proof.
Validation date: 2026-10-11; repository CI validates schema and pack.
