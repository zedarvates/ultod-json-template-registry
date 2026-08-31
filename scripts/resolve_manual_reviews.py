from __future__ import annotations

import argparse
import json
from pathlib import Path


def _render(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(root: Path):
    manual = []
    for report_path in sorted(root.glob("MIGRATION-V1*.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for result in report.get("results", []):
            if result.get("disposition") == "manual-review":
                manual.append((result, report_path.name))
    resolutions = []
    for result, report_name in sorted(manual, key=lambda item: item[0]["source_file"]):
        collision = "normalized-slug-collision" in result.get("reason_codes", [])
        resolutions.append({
            "source_file": result["source_file"],
            "family": result["family"],
            "original_report": report_name,
            "original_reason_codes": result.get("reason_codes", []),
            "resolution_disposition": "legacy-only-authoritative",
            "resolution_reason_codes": [
                "ambiguous-duplicate-identity-not-promoted"
                if collision
                else "technical-fixture-identity-not-promoted"
            ],
            "strict_target_file": None,
        })
    document = {
        "report_version": "1.0.0",
        "resolution_policy": "no-guessing-v1",
        "summary": {
            "manual_reviews": len(manual),
            "resolved": len(resolutions),
            "unresolved": 0,
        },
        "resolutions": resolutions,
    }
    return {"resolutions": resolutions, "content": _render(document)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plan = build(args.root)
    output = args.root / "MANUAL-REVIEW-RESOLUTIONS-V1.json"
    if args.write:
        output.write_bytes(plan["content"])
    elif not output.is_file() or output.read_bytes() != plan["content"]:
        raise SystemExit(1)
    print(json.dumps({"resolved": len(plan["resolutions"]), "unresolved": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
