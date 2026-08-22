#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.registry_catalog import build_catalog_index, exact_ref, validate_reference_graph
from scripts.template_contract import (
    compute_spec_checksum,
    decode_json_bytes,
    validate_document_limits,
    validate_envelope_identity,
    validate_schema_identity,
    validate_schema_references,
    validate_with_schema,
)
from scripts.validation_report import ValidationIssue, ValidationReport


ADMIN_KEY = re.compile(r"(?:admin|debug|requires_permission)", re.IGNORECASE)
COMMERCIAL_KEY = re.compile(
    r"(?:shop_info|buy_price|sell_price|stock_limit|sku|billing|premium_currency|real_money)",
    re.IGNORECASE,
)
INTERNAL_KEY = re.compile(
    r"(?:server_url|connection_string|asset_path|model_path|texture_path|audio_path)",
    re.IGNORECASE,
)
RIGHTS_TERM = re.compile(
    r"(?:\bwarcraft\b|\bultima(?:[ _-]+online)?\b|\bone[ _-]?piece\b|\btolkien\b|\blovecraft\b|\bcthulhu\b|\baion\b|\bxenomorph\b|\bmithril\b|\bpeacebloom\b|\bsilverleaf\b)",
    re.IGNORECASE,
)
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
        if RIGHTS_TERM.search(key) or (
            isinstance(value, str) and RIGHTS_TERM.search(value)
        ):
            violations.add("third-party-reference")
    return sorted(violations)


def validate_public_path(path: str) -> list[str]:
    normalized = path.replace("\\", "/")
    return ["hash-placeholder-name"] if HASH_PLACEHOLDER.search(normalized) else []


def _sha_variants(content: bytes) -> set[str]:
    normalized_lf = content.replace(b"\r\n", b"\n")
    return {
        hashlib.sha256(content).hexdigest(),
        hashlib.sha256(normalized_lf).hexdigest(),
        hashlib.sha256(normalized_lf.replace(b"\n", b"\r\n")).hexdigest(),
    }


def _append_messages(
    report: ValidationReport, path: str, code: str, messages: list[str]
) -> None:
    for message in messages:
        report.issues.append(ValidationIssue(path, code, message))


def validate_registry(root: Path) -> ValidationReport:
    report = ValidationReport()
    catalog_path = root / "templates/catalog.json"
    if not catalog_path.is_file():
        report.issues.append(
            ValidationIssue("templates/catalog.json", "catalog-missing", "catalog is missing")
        )
        return report

    try:
        catalog = decode_json_bytes(catalog_path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        report.issues.append(
            ValidationIssue("templates/catalog.json", "catalog-json", str(error))
        )
        return report

    entries = catalog.get("entries", []) if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        report.issues.append(
            ValidationIssue("templates/catalog.json", "catalog-entries", "entries must be an array")
        )
        return report
    report.catalog_entries = len(entries)
    if catalog.get("registry_version") != "2.0.0":
        report.issues.append(
            ValidationIssue(
                "templates/catalog.json", "catalog-version", "registry_version must equal 2.0.0"
            )
        )
    if not isinstance(catalog.get("aliases"), list):
        report.issues.append(
            ValidationIssue("templates/catalog.json", "catalog-aliases", "aliases must be an array")
        )

    by_file = {}
    for entry in entries:
        if not isinstance(entry, dict):
            report.issues.append(
                ValidationIssue(
                    "templates/catalog.json", "catalog-entry", "every entry must be an object"
                )
            )
            continue
        file = entry.get("file")
        if not isinstance(file, str):
            report.issues.append(
                ValidationIssue(
                    "templates/catalog.json", "catalog-file", "entry file must be a string"
                )
            )
        elif file in by_file:
            report.issues.append(
                ValidationIssue(file, "catalog-duplicate-file", "file is listed more than once")
            )
        else:
            by_file[file] = entry

    disk_files = {
        path.relative_to(root).as_posix()
        for path in (root / "templates").rglob("*.json")
    }
    documents_by_ref = {}
    for rel in sorted(disk_files - {"templates/catalog.json"}):
        path = root / rel
        report.documents_checked += 1
        entry = by_file.get(rel)
        if entry is None:
            report.issues.append(
                ValidationIssue(rel, "catalog-unlisted", "JSON file is not listed in catalog")
            )
            continue
        try:
            content = path.read_bytes()
            document = decode_json_bytes(content)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            report.issues.append(ValidationIssue(rel, "json-parse", str(error)))
            continue

        _append_messages(report, rel, "public-path", validate_public_path(rel))
        _append_messages(report, rel, "public-content", validate_public_content(document))
        if entry.get("sha256") not in _sha_variants(content):
            report.issues.append(ValidationIssue(rel, "sha256", "catalog SHA-256 mismatch"))

        profile = entry.get("validation_profile")
        if profile == "legacy-unvalidated":
            report.legacy_entries += 1
            continue
        if not isinstance(document, dict):
            report.issues.append(
                ValidationIssue(rel, "strict-root", "strict document root must be an object")
            )
            continue
        _append_messages(
            report,
            rel,
            "document-limits",
            validate_document_limits(document, len(content)),
        )

        if profile == "strict-schema-v1":
            report.strict_schema_entries += 1
            try:
                Draft202012Validator.check_schema(document)
            except jsonschema.exceptions.SchemaError as error:
                report.issues.append(ValidationIssue(rel, "schema-meta", error.message))
            _append_messages(report, rel, "schema-id", validate_schema_identity(rel, document))
            _append_messages(
                report, rel, "schema-resolution", validate_schema_references(root, rel)
            )
            continue

        if profile != "strict-v1":
            report.issues.append(
                ValidationIssue(
                    rel, "validation-profile", f"unknown validation profile: {profile!r}"
                )
            )
            continue

        report.strict_entries += 1
        try:
            _append_messages(
                report, rel, "identity", validate_envelope_identity(rel, document)
            )
        except ValueError as error:
            report.issues.append(ValidationIssue(rel, "strict-path", str(error)))

        schema_file = entry.get("schema_file")
        if not isinstance(schema_file, str):
            report.issues.append(
                ValidationIssue(rel, "schema-file", "strict entry schema_file must be a string")
            )
        else:
            _append_messages(
                report, rel, "schema", validate_with_schema(root, schema_file, document)
            )
            expected_schema_ref = posixpath.relpath(
                schema_file, start=str(PurePosixPath(rel).parent)
            )
            if document.get("$schema") != expected_schema_ref:
                report.issues.append(
                    ValidationIssue(
                        rel,
                        "schema-reference",
                        f"$schema must equal {expected_schema_ref}",
                    )
                )

        computed_spec_checksum = compute_spec_checksum(document.get("spec"))
        if document.get("spec_checksum") != computed_spec_checksum:
            report.issues.append(
                ValidationIssue(rel, "spec-checksum", "spec checksum mismatch")
            )
        if entry.get("spec_checksum") != computed_spec_checksum:
            report.issues.append(
                ValidationIssue(
                    rel, "catalog-spec-checksum", "catalog spec checksum mismatch"
                )
            )
        for key in (
            "id",
            "slug",
            "family",
            "version",
            "contract_version",
            "intended_consumers",
            "compatibility",
        ):
            if entry.get(key) != document.get(key):
                report.issues.append(
                    ValidationIssue(
                        rel, "catalog-envelope", f"catalog {key} does not match document"
                    )
                )
        try:
            documents_by_ref[exact_ref(entry)] = document
        except KeyError as error:
            report.issues.append(
                ValidationIssue(rel, "catalog-reference", f"missing catalog field {error}")
            )

    for file in sorted(set(by_file) - disk_files):
        report.issues.append(
            ValidationIssue(file, "catalog-file-missing", "catalogued file does not exist")
        )

    index, index_errors = build_catalog_index(catalog)
    _append_messages(report, "templates/catalog.json", "catalog-index", index_errors)
    if index is not None:
        _append_messages(
            report,
            "templates/catalog.json",
            "reference-graph",
            validate_reference_graph(index, documents_by_ref),
        )
    report.issues = report.sorted_issues()
    return report


def main():
    parser = argparse.ArgumentParser(description="Validate the public template registry")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = validate_registry(args.root)
    print(f"Loaded {report.catalog_entries} catalog entries")
    if args.report:
        report.write_json(args.report)
    for issue in report.sorted_issues()[:50]:
        print(f"Error: {issue.path}: [{issue.code}] {issue.message}")
    if len(report.issues) > 50:
        print(f"... and {len(report.issues) - 50} more errors")
    if report.issues:
        raise SystemExit(1)
    print(
        f"Successfully validated {report.documents_checked + 1} JSON documents "
        "and verified full catalog SHA-256 integrity."
    )


if __name__ == "__main__":
    main()
