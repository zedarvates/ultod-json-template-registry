#!/usr/bin/env python3
import json
import hashlib
import re
from pathlib import Path
from typing import Any


SECRET_KEY = re.compile(r"(?:api[_-]?key|secret|password|passwd|authorization|bearer|private[_-]?key|connection[_-]?string)", re.IGNORECASE)
ADMIN_KEY = re.compile(r"(?:admin_controls|admin_only|debug_mode|admin_command)", re.IGNORECASE)
COMMERCIAL_KEY = re.compile(r"(?:shop_info|buy_price|sell_price|sku|billing|premium_currency|real_money|stock_limit)", re.IGNORECASE)
INTERNAL_KEY = re.compile(r"(?:server_url|connection_string|asset_path|model_path|texture_path|audio_path)", re.IGNORECASE)
INTERNAL_TEXT = re.compile(r"(?:https?://(?:localhost|127\.0\.0\.1|10\.|192\.168\.)|[A-Za-z]:\\)", re.IGNORECASE)
RIGHTS_TEXT = re.compile(r"(?:warcraft|ultima online|one[ _-]?piece|tolkien|lovecraft|cthulhu|aion|\bsphere\b|xenomorph|mithril|peacebloom|silverleaf)", re.IGNORECASE)


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def validate_public_content(document: Any, raw_text: str) -> list[str]:
    violations = set()
    for key, value in _walk(document):
        if SECRET_KEY.search(key):
            violations.add("secret")
        if ADMIN_KEY.search(key):
            violations.add("admin-control")
        if COMMERCIAL_KEY.search(key):
            violations.add("commercial")
        if INTERNAL_KEY.search(key):
            violations.add("internal")
        if isinstance(value, str) and INTERNAL_TEXT.search(value):
            violations.add("internal")
    if INTERNAL_TEXT.search(raw_text):
        violations.add("internal")
    if RIGHTS_TEXT.search(raw_text):
        violations.add("rights")
    return sorted(violations)

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
            text = content.decode("utf-8")
            document = json.loads(text)
        except Exception as e:
            errors.append(f"{path}: JSON parse error: {e}")
            document = None
            text = ""

        rel_posix = path.as_posix()
        if rel_posix == "templates/catalog.json":
            continue

        if document is not None:
            violations = validate_public_content(document, text)
            if violations:
                errors.append(f"{rel_posix}: prohibited public content ({', '.join(violations)})")

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
