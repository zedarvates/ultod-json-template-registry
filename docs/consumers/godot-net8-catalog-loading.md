# Godot .NET 8 raw-catalog loading

This profile describes a scoped consumer change. It does not change the
strict-v1 envelope or publish private server/client implementation code.

## Specializations

The raw class consumer accepts an array containing identifier strings,
specialization objects, and null entries. A string becomes an object with
the same `Id`; it does not invent a display name, description, abilities,
or talents. Objects retain their declared fields. Numbers, booleans and
a non-array `specializations` value are rejected.

The optional authoring schema at
`templates/schemas/class/v0.2.0/schema.json` widens the immutable legacy
`v0.1.0` schema's item representation. Its other authoring restrictions
remain unchanged. It is not proof that every raw catalog file satisfies
that full schema. The example in `docs/examples/class-specializations-mixed.json`
illustrates the consumer representation; it is not a strict-v1 template.

## Evidence and limits

Private raw-fixture checks on 2026-10-10 covered 33 races and 66 classes.
The compared consumers produced identical complete objects and dictionaries.
The class reference was adapted to the same specialization representation;
the historical unadapted reader loaded only 42 of the 66 class fixtures.

Three .NET 8 runs, 21 batches of 50 combined loads per run:

| Combined operation | Adapted Newtonsoft | Optimized consumer |
| --- | ---: | ---: |
| In-memory input | 0.772 ms | 0.420 ms |
| File reads, new dictionaries | 5.176 ms | 4.512 ms |
| File reads, reused dictionaries | 5.200 ms | 4.610 ms |

These local medians use warm OS and serializer caches. Enumeration, UTF-8
decoding, parsing and dictionary updates are included in the file phases.
They exclude other catalogs, engine signals and log output. They are not
universal performance guarantees or FPS/startup measurements.

A source-isolated Godot Mono 4.7.1/.NET 8 headless scene verified both
dictionaries initially, after a race-file edit and after a class-file edit.
The real file watcher, deferred reload and catalog signals were exercised.
Mixed specialization objects retained their fields. The main client build
used SDK 4.7.2; no rendered/VR/full-game compatibility is claimed.

Public legacy snapshots are sanitized and may differ from those private
fixtures. The private checks do not certify the public snapshots or the
strict-v1 projections. Existing catalog `compatibility` arrays stay empty.
Server validation and permission checks remain authoritative and independent
of this consumer representation.
