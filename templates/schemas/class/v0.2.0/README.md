# Legacy class authoring schema 0.2.0

- Owner: Ultimate Odycer template registry.
- Status: experimental, opt-in legacy authoring schema.
- Change: specialization items accept the previous nonempty strings,
  objects with a nonempty identifier, or null. Other v0.1.0 constraints
  are preserved; the published v0.1.0 file is not rewritten.
- Intended consumer: raw class catalog adapters that explicitly support
  both representations. This is not a strict-v1 envelope schema.
- Compatibility: no registry-wide runtime compatibility claim. Private
  .NET 8/Godot headless fixture checks are described separately in
  `docs/consumers/godot-net8-catalog-loading.md`.
- Validation date: 2026-10-10, specialization item-schema tests and full
  registry validation.
- Public-policy exclusions and server authority remain unchanged.
