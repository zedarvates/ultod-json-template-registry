# Classes schema 1.1.0

Owner: Ultimate Odycer / zedarvates. Status: experimental. Validation: 2026-10-11.
Adds optional `resource_kinds`, `role_tags` and `specialization_tags` arrays of
1–16 unique kebab-case labels (maximum 64 characters each). The 1.0.0 fields,
requiredness and closed spec remain unchanged. `resource_kind` remains the
primary label; `resource_kinds`, when present, lists the intended resources.
These labels grant no resource, gameplay stat, specialization or permission.
Consumers select 1.1.0 explicitly; unknown labels must fail in the adapter.
Intended consumers: LLM pipeline and future explicit Zig adapters.
No runtime compatible version is verified. Published 1.0.0 remains immutable.
