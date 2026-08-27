from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cohort_two_contracts import COHORT_TWO_FAMILIES, KIND_BY_FAMILY, STRICT_FAMILIES, candidate_slug, convert_legacy, family_schema
from scripts.pilot_contracts import MigrationResult
from scripts.template_contract import decode_json_bytes


def _render(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _readme(family: str) -> bytes:
    fields = {
        "dungeons": "`display_name`; optional `theme_tag`.",
        "locations": "`display_name`, `location_kind`; optional size and rarity tags.",
        "planets": "`display_name`; optional primary and secondary type tags.",
        "solar-systems": "`display_name`.",
    }[family]
    return (
        f"# {family.title()} templates\n\n"
        f"## Purpose\n\nMinimal declarative {family} identity and classification.\n\n"
        f"## Fields\n\n{fields}\n\n"
        "## Authoritative exclusions\n\nExcluded: layouts, coordinates, physics, timings, rewards, probabilities, spawns, runtime metrics, lore, dialogue, and asset paths.\n\n"
        "## Intended consumers\n\nLLM pipeline only. Zig support requires separate typed-adapter evidence.\n\n"
        "## Compatibility evidence\n\nNone verified.\n\n"
        "## Versioning\n\nTemplates and family schemas follow independent SemVer.\n"
    ).encode("utf-8")


def build_migration(root: Path, families: tuple[str, ...] = COHORT_TWO_FAMILIES):
    if tuple(families) != COHORT_TWO_FAMILIES:
        raise ValueError("cohort two families are fixed for reproducible review")
    catalog = decode_json_bytes((root / "templates/catalog.json").read_bytes())
    strict_families = set(STRICT_FAMILIES)
    entries = [
        entry
        for entry in catalog["entries"]
        if not (entry.get("validation_profile") == "strict-v1" and entry.get("family") in strict_families)
        and not (entry.get("validation_profile") == "strict-schema-v1" and entry.get("name") in strict_families)
    ]
    by_file = {entry["file"]: entry for entry in entries}
    results: list[MigrationResult] = []
    files: dict[str, bytes] = {}
    for family in families:
        paths = sorted(
            path.relative_to(root).as_posix()
            for path in (root / "templates" / family).rglob("template.json")
            if path.parent.name != "v1.0.0"
        )
        decoded = {}
        candidates = []
        for source in paths:
            try:
                document = decode_json_bytes((root / source).read_bytes())
                decoded[source] = document
                candidates.append(candidate_slug(family, source, document))
            except Exception:
                pass
        collisions = {slug for slug, count in Counter(candidates).items() if count > 1}
        for source in paths:
            try:
                result = convert_legacy(family, source, decoded[source], collisions)
            except Exception as error:
                result = MigrationResult(source, family, "", "invalid-source", (type(error).__name__,), None, None)
            results.append(result)
            legacy = by_file[source]
            for key in ("id", "slug", "family", "superseded_by"):
                legacy.pop(key, None)
            if result.disposition != "migrated":
                continue
            content = _render(result.document)
            files[result.target_file] = content
            legacy.update({
                "id": f"{family}:{result.slug}", "slug": result.slug, "family": family,
                "superseded_by": f"{family}:{result.slug}@1.0.0",
            })
            entries.append({
                "id": f"{family}:{result.slug}", "slug": result.slug, "family": family,
                "name": result.slug, "kind": KIND_BY_FAMILY[family], "version": "1.0.0",
                "contract_version": "1.0.0", "validation_profile": "strict-v1", "status": "experimental",
                "schema_file": f"templates/schemas/{family}/v1.0.0/schema.json",
                "file": result.target_file, "sha256": hashlib.sha256(content).hexdigest(),
                "spec_checksum": result.document["spec_checksum"],
                "intended_consumers": result.document["intended_consumers"], "compatibility": [],
                "supersedes": [f"{family}:{result.slug}@0.1.0"],
            })
        if family not in strict_families:
            continue
        schema_path = f"templates/schemas/{family}/v1.0.0/schema.json"
        schema_content = _render(family_schema(family))
        files[schema_path] = schema_content
        entries.append({
            "name": family, "kind": "json-schema", "version": "1.0.0", "status": "experimental",
            "file": schema_path, "sha256": hashlib.sha256(schema_content).hexdigest(), "compatibility": [],
            "validation_profile": "strict-schema-v1", "contract_version": "1.0.0",
        })
        files[f"templates/{family}/README.md"] = _readme(family)
    results.sort(key=lambda result: result.source_file)
    counts = dict(sorted(Counter(result.disposition for result in results).items()))
    report = {
        "report_version": "1.0.0", "cohort": "2", "families": list(families),
        "summary": {"total": len(results), "dispositions": counts},
        "results": [{
            "source_file": result.source_file, "family": result.family, "slug": result.slug,
            "disposition": result.disposition, "reason_codes": list(result.reason_codes),
            "target_file": result.target_file,
        } for result in results],
    }
    catalog["entries"] = entries
    files["MIGRATION-V1-COHORT-2.json"] = _render(report)
    files["templates/catalog.json"] = _render(catalog)
    return {"results": results, "counts": counts, "files": files}


def write_migration(root: Path, plan):
    for relative, content in sorted(plan["files"].items()):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and "v1.0.0/template.json" in relative and path.read_bytes() != content:
            raise FileExistsError(relative)
        path.write_bytes(content)


def check_migration(root: Path, plan):
    return [relative for relative, content in sorted(plan["files"].items()) if not (root / relative).is_file() or (root / relative).read_bytes() != content]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plan = build_migration(args.root)
    if args.write:
        write_migration(args.root, plan)
    else:
        mismatches = check_migration(args.root, plan)
        if mismatches:
            print("\n".join(mismatches[:50]))
            raise SystemExit(1)
    print(json.dumps({"counts": plan["counts"], "total": len(plan["results"])}, sort_keys=True))


if __name__ == "__main__":
    main()
