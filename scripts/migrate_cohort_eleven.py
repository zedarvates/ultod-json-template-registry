from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.template_contract import decode_json_bytes


FAMILIES = ("content-pipeline", "generated-content")


def _render(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(root: Path):
    results = []
    for family in FAMILIES:
        paths = sorted(
            path.relative_to(root).as_posix()
            for path in (root / "templates" / family).rglob("template.json")
            if path.parent.name != "v1.0.0"
        )
        for source in paths:
            decode_json_bytes((root / source).read_bytes())
            slug = Path(source).parts[-3]
            reason = (
                "generated-balanced-spell-runtime-output"
                if family == "content-pipeline"
                else "generated-quest-runtime-output-or-manifest"
            )
            results.append({
                "source_file": source,
                "family": family,
                "slug": slug,
                "disposition": "legacy-only-authoritative",
                "reason_codes": [reason],
                "target_file": None,
            })
    counts = dict(sorted(Counter(result["disposition"] for result in results).items()))
    report = {
        "report_version": "1.0.0",
        "cohort": "11",
        "families": list(FAMILIES),
        "summary": {"total": len(results), "dispositions": counts},
        "results": results,
    }
    return {"results": results, "counts": counts, "content": _render(report)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plan = build(args.root)
    output = args.root / "MIGRATION-V1-COHORT-11.json"
    if args.write:
        output.write_bytes(plan["content"])
    elif not output.is_file() or output.read_bytes() != plan["content"]:
        raise SystemExit(1)
    print(json.dumps({"counts": plan["counts"], "total": len(plan["results"])}, sort_keys=True))


if __name__ == "__main__":
    main()
