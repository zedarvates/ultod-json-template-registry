from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def audit_coverage(root: Path):
    legacy = {
        path.relative_to(root).as_posix()
        for path in (root / "templates").rglob("template.json")
        if path.parent.name != "v1.0.0"
    }
    seen = defaultdict(list)
    reports = sorted(root.glob("MIGRATION-V1*.json"))
    for report_path in reports:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for result in report.get("results", []):
            source = result.get("source_file")
            if isinstance(source, str):
                seen[source].append(report_path.name)
    duplicates = {source: names for source, names in seen.items() if len(names) > 1}
    return {
        "legacy_sources": len(legacy),
        "classified_sources": len(legacy.intersection(seen)),
        "report_count": len(reports),
        "missing": sorted(legacy.difference(seen)),
        "duplicates": dict(sorted(duplicates.items())),
        "extraneous": sorted(set(seen).difference(legacy)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = audit_coverage(args.root)
    print(json.dumps({
        "legacy_sources": result["legacy_sources"],
        "classified_sources": result["classified_sources"],
        "report_count": result["report_count"],
        "missing": len(result["missing"]),
        "duplicates": len(result["duplicates"]),
        "extraneous": len(result["extraneous"]),
    }, sort_keys=True))
    if result["missing"] or result["duplicates"] or result["extraneous"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
