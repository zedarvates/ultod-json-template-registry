#!/usr/bin/env python3
import json
import hashlib
import re
from pathlib import Path
from typing import Any


ADMIN_KEY = re.compile(r"(?:admin|debug|requires_permission)", re.IGNORECASE)
COMMERCIAL_KEY = re.compile(r"(?:shop_info|buy_price|sell_price|stock_limit|sku|billing|premium_currency|real_money)", re.IGNORECASE)
INTERNAL_KEY = re.compile(r"(?:server_url|connection_string|asset_path|model_path|texture_path|audio_path)", re.IGNORECASE)
RIGHTS_TERM = re.compile(r"(?:warcraft|ultima(?: online)?|one[ _-]?piece|tolkien|lovecraft|cthulhu|aion|xenomorph|mithril|peacebloom|silverleaf)", re.IGNORECASE)
HASH_PLACEHOLDER = re.compile(r"/original-[^/]+-[0-9a-f]{10}/", re.IGNORECASE)


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def validate_public_content(document: Any) -> list[str]:
    violations = set()
    for key, value in _walk(document):
        if ADMIN_KEY.search(key):
            violations.add("admin-control")
        if COMMERCIAL_KEY.search(key):
            violations.add("commercial")
        if INTERNAL_KEY.search(key):
            violations.add("internal")
        if RIGHTS_TERM.search(key) or (isinstance(value, str) and RIGHTS_TERM.search(value)):
            violations.add("third-party-reference")
    return sorted(violations)


def validate_public_path(path: str) -> list[str]:
    return ["hash-placeholder-name"] if HASH_PLACEHOLDER.search(path.replace("\\", "/")) else []

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
            document = json.loads(content.decode("utf-8"))
        except Exception as e:
            errors.append(f"{path}: JSON parse error: {e}")
            document = None

        rel_posix = path.as_posix()
        if rel_posix == "templates/catalog.json":
            continue

        path_violations = validate_public_path(rel_posix)
        content_violations = validate_public_content(document) if document is not None else []
        if path_violations or content_violations:
            violations = sorted(set(path_violations + content_violations))
            errors.append(f"{rel_posix}: public policy violation ({', '.join(violations)})")

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
