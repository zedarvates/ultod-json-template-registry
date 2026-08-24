from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.pilot_contracts import PILOT_FAMILIES, convert_legacy, family_schema, find_slug_collisions
from scripts.template_contract import decode_json_bytes

def _render(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

def _readme(family):
    excluded = "stats, timings, costs, probabilities, loot contents, AI weights, lore, dialogue, and asset paths"
    return (f"# {family.title()} templates\n\n## Purpose\n\nMinimal declarative {family} classifications.\n\n## Required fields\n\n`display_name`.\n\n## Optional fields\n\nOnly fields defined by the exact family schema.\n\n## Authoritative exclusions\n\nExcluded: {excluded}.\n\n## Intended consumers\n\nLLM pipeline and the future disabled-by-default Zig adapter.\n\n## Compatibility evidence\n\nNone verified.\n\n## Versioning\n\nEach template and family schema follows independent SemVer.\n").encode("utf-8")

def build_migration(root: Path, families: tuple[str, ...]):
    catalog = decode_json_bytes((root / "templates/catalog.json").read_bytes())
    entries = [e for e in catalog["entries"] if not (
        e.get("validation_profile") == "strict-v1" and e.get("family") in families
    ) and not (
        e.get("validation_profile") == "strict-schema-v1" and e.get("name") in families
    )]
    by_file = {e["file"]: e for e in entries}
    results = []
    files = {}
    for family in families:
        paths = sorted(
            p.relative_to(root).as_posix()
            for p in (root / "templates" / family).rglob("template.json")
            if p.parent.name != "v1.0.0"
        )
        collisions = find_slug_collisions(paths)
        for source in paths:
            try:
                document = decode_json_bytes((root / source).read_bytes())
                result = convert_legacy(family, source, document, collisions)
            except Exception as error:
                from scripts.pilot_contracts import MigrationResult
                result = MigrationResult(source, family, "", "invalid-source", (type(error).__name__,), None, None)
            results.append(result)
            if result.disposition != "migrated":
                continue
            content = _render(result.document)
            files[result.target_file] = content
            legacy = by_file[source]
            legacy.update({
                "id": f"{family}:{result.slug}", "slug": result.slug, "family": family,
                "superseded_by": f"{family}:{result.slug}@1.0.0",
            })
            entries.append({
                "id": f"{family}:{result.slug}", "slug": result.slug, "family": family,
                "name": result.slug, "kind": f"{family.rstrip('s')}-template",
                "version": "1.0.0", "contract_version": "1.0.0",
                "validation_profile": "strict-v1", "status": "experimental",
                "schema_file": f"templates/schemas/{family}/v1.0.0/schema.json",
                "file": result.target_file, "sha256": hashlib.sha256(content).hexdigest(),
                "spec_checksum": result.document["spec_checksum"],
                "intended_consumers": result.document["intended_consumers"], "compatibility": [],
                "supersedes": [f"{family}:{result.slug}@0.1.0"],
            })
        schema_path = f"templates/schemas/{family}/v1.0.0/schema.json"
        schema_content = _render(family_schema(family))
        files[schema_path] = schema_content
        entries.append({
            "name": family, "kind": "json-schema", "version": "1.0.0",
            "status": "experimental", "file": schema_path,
            "sha256": hashlib.sha256(schema_content).hexdigest(), "compatibility": [],
            "validation_profile": "strict-schema-v1", "contract_version": "1.0.0",
        })
        files[f"templates/{family}/README.md"] = _readme(family)
    results.sort(key=lambda r: r.source_file)
    counts = dict(sorted(Counter(r.disposition for r in results).items()))
    report = {
        "report_version": "1.0.0", "families": list(families),
        "summary": {"total": len(results), "dispositions": counts},
        "results": [{
            "source_file": r.source_file, "family": r.family, "slug": r.slug,
            "disposition": r.disposition, "reason_codes": list(r.reason_codes),
            "target_file": r.target_file,
        } for r in results],
    }
    catalog["entries"] = entries
    files["MIGRATION-V1.json"] = _render(report)
    files["templates/catalog.json"] = _render(catalog)
    return {"results": results, "counts": counts, "files": files}

def write_migration(root, plan):
    for relative, content in sorted(plan["files"].items()):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and "v1.0.0/template.json" in relative and path.read_bytes() != content:
            raise FileExistsError(relative)
        path.write_bytes(content)

def check_migration(root, plan):
    return [path for path, content in sorted(plan["files"].items()) if not (root / path).is_file() or (root / path).read_bytes() != content]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--families", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    families = tuple(args.families.split(","))
    if any(f not in PILOT_FAMILIES for f in families):
        raise SystemExit("unsupported family")
    plan = build_migration(args.root, families)
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
