from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def audit_resolutions(root: Path):
    manual = []
    for report_path in sorted(root.glob("MIGRATION-V1*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        manual.extend(
            result["source_file"]
            for result in report.get("results", [])
            if result.get("disposition") == "manual-review"
        )
    resolution_path = root / "MANUAL-REVIEW-RESOLUTIONS-V1.json"
    document = json.loads(resolution_path.read_text(encoding="utf-8"))
    resolutions = [item.get("source_file") for item in document.get("resolutions", [])]
    counts = Counter(resolutions)
    return {
        "manual_reviews": len(manual),
        "resolved": len(set(manual).intersection(resolutions)),
        "missing": sorted(set(manual).difference(resolutions)),
        "duplicates": sorted(source for source, count in counts.items() if count > 1),
        "extraneous": sorted(set(resolutions).difference(manual)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = audit_resolutions(args.root)
    print(json.dumps({
        "manual_reviews": result["manual_reviews"],
        "resolved": result["resolved"],
        "missing": len(result["missing"]),
        "duplicates": len(result["duplicates"]),
        "extraneous": len(result["extraneous"]),
    }, sort_keys=True))
    if result["missing"] or result["duplicates"] or result["extraneous"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
