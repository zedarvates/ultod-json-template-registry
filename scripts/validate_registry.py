#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

def main():
    files = sorted(Path("templates").rglob("*.json"))
    if not files:
        raise SystemExit("No JSON templates found")

    catalog_path = Path("templates/catalog.json")
    if not catalog_path.exists():
        raise SystemExit("templates/catalog.json missing")

    with catalog_path.open(encoding="utf-8") as f:
        catalog_data = json.load(f)

    entries = catalog_data.get("entries", catalog_data) if isinstance(catalog_data, dict) else catalog_data
    catalog_entries = {entry["file"]: entry for entry in entries}
    print(f"Loaded {len(catalog_entries)} catalog entries")

    errors = []
    for path in files:
        with path.open("rb") as stream:
            content = stream.read()
        try:
            json.loads(content.decode("utf-8"))
        except Exception as e:
            errors.append(f"{path}: JSON parse error: {e}")

        rel_posix = path.as_posix()
        if rel_posix == "templates/catalog.json":
            continue

        if rel_posix not in catalog_entries:
            errors.append(f"{rel_posix}: not listed in templates/catalog.json")
        else:
            expected_sha = catalog_entries[rel_posix].get("sha256")
            sha_raw = hashlib.sha256(content).hexdigest()
            sha_lf = hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
            sha_crlf = hashlib.sha256(content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
            if expected_sha not in (sha_raw, sha_lf, sha_crlf):
                errors.append(f"{rel_posix}: SHA-256 mismatch (catalog: {expected_sha}, file: {sha_raw})")

    if errors:
        for err in errors[:50]:
            print(f"Error: {err}")
        if len(errors) > 50:
            print(f"... and {len(errors) - 50} more errors")
        raise SystemExit(1)

    print(f"Successfully validated {len(files)} JSON documents and verified full catalog SHA-256 integrity.")

if __name__ == "__main__":
    main()
