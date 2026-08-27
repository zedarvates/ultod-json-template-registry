from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.template_contract import decode_json_bytes

def audit_links(registry_root: Path, server_root: Path):
    migration = decode_json_bytes((registry_root / "MIGRATION-V1.json").read_bytes())
    catalog = decode_json_bytes((registry_root / "templates/catalog.json").read_bytes())
    by_source = {e.get("file"): e for e in catalog.get("entries", [])}
    server_files = sorted(p for p in server_root.rglob("*.json") if "_versions" not in p.parts)
    by_name, by_id = {}, {}
    for path in server_files:
        relative = path.relative_to(server_root).as_posix()
        by_name.setdefault(path.name.lower(), []).append(relative)
        try:
            doc = decode_json_bytes(path.read_bytes())
            if isinstance(doc, dict) and isinstance(doc.get("id"), str):
                by_id.setdefault(doc["id"].lower(), []).append(relative)
        except Exception:
            pass
    results = []
    for item in migration["results"]:
        if item["disposition"] != "migrated":
            continue
        legacy = by_source.get(item["source_file"], {})
        source_file = legacy.get("source_file")
        matches, disposition = [], "missing"
        if isinstance(source_file, str) and (server_root / source_file).is_file():
            matches, disposition = [Path(source_file).as_posix()], "exact-source-path"
        else:
            basename = Path(source_file).name.lower() if isinstance(source_file, str) else ""
            candidates = by_name.get(basename, []) if basename else []
            if len(candidates) == 1:
                matches, disposition = candidates, "unique-basename"
            elif len(candidates) > 1:
                matches, disposition = candidates, "ambiguous"
            else:
                candidates = by_id.get(item["slug"].replace("-", "_"), [])
                if len(candidates) == 1:
                    matches, disposition = candidates, "unique-id"
                elif len(candidates) > 1:
                    matches, disposition = candidates, "ambiguous"
        results.append({
            "registry_id": f"{item['family']}:{item['slug']}@1.0.0",
            "disposition": disposition,
            "server_file": matches[0] if len(matches) == 1 else None,
            "candidate_files": matches if len(matches) != 1 else [],
        })
    results.sort(key=lambda value: value["registry_id"])
    counts = dict(sorted(Counter(r["disposition"] for r in results).items()))
    return {"report_version": "1.0.0", "compatibility_claimed": False, "summary": counts, "results": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-root", type=Path, default=Path("."))
    parser.add_argument("--server-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = audit_links(args.registry_root, args.server_root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))

if __name__ == "__main__":
    main()
