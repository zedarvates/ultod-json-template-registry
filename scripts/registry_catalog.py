from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class CatalogIndex:
    by_ref: dict[str, Mapping[str, Any]]
    by_file: dict[str, Mapping[str, Any]]
    aliases: dict[str, str]


def exact_ref(entry: Mapping[str, Any]) -> str:
    return f"{entry['id']}@{entry['version']}"


def _find_alias_cycle(aliases: Mapping[str, str]) -> list[str] | None:
    for start in sorted(aliases):
        chain: list[str] = []
        positions: dict[str, int] = {}
        current = start
        while current in aliases:
            if current in positions:
                return chain[positions[current] :] + [current]
            positions[current] = len(chain)
            chain.append(current)
            current = aliases[current]
    return None


def build_catalog_index(catalog: Mapping[str, Any]):
    by_ref = {}
    by_file = {}
    errors = []
    for entry in catalog.get("entries", []):
        if not isinstance(entry, Mapping):
            errors.append("catalog entry must be an object")
            continue
        if all(isinstance(entry.get(key), str) for key in ("id", "version")):
            ref = exact_ref(entry)
            if ref in by_ref:
                errors.append(f"duplicate catalog reference: {ref}")
            else:
                by_ref[ref] = entry
        file = entry.get("file")
        if not isinstance(file, str):
            errors.append("catalog entry file must be a string")
        elif file in by_file:
            errors.append(f"duplicate catalog file: {file}")
        else:
            by_file[file] = entry

    aliases = {}
    for alias in catalog.get("aliases", []):
        if not isinstance(alias, Mapping):
            errors.append("alias must be an object")
            continue
        source, target = alias.get("from"), alias.get("to")
        if not isinstance(source, str) or not isinstance(target, str):
            errors.append("alias from and to must be strings")
        elif source in aliases:
            errors.append(f"duplicate alias source: {source}")
        elif source == target:
            errors.append(f"self alias: {source}")
        else:
            aliases[source] = target

    cycle = _find_alias_cycle(aliases)
    if cycle:
        errors.append(f"alias cycle: {' -> '.join(cycle)}")
    if errors:
        return None, sorted(errors)
    return CatalogIndex(by_ref=by_ref, by_file=by_file, aliases=aliases), []


def validate_reference_graph(
    index: CatalogIndex, documents: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    errors = []
    for source_ref, document in sorted(documents.items()):
        for dependency in document.get("dependencies", []):
            if dependency not in index.by_ref:
                errors.append(f"{source_ref}: missing dependency {dependency}")
        entry = index.by_ref.get(source_ref)
        if entry is None:
            errors.append(f"document missing catalog reference: {source_ref}")
            continue
        for superseded in entry.get("supersedes", []):
            if superseded == source_ref:
                errors.append(f"{source_ref}: cannot supersede itself")
            elif superseded not in index.by_ref:
                errors.append(f"{source_ref}: missing superseded reference {superseded}")

    for ref, entry in sorted(index.by_ref.items()):
        successor = entry.get("superseded_by")
        if successor is not None:
            if successor == ref:
                errors.append(f"{ref}: cannot be superseded by itself")
            elif successor not in index.by_ref:
                errors.append(f"{ref}: missing successor reference {successor}")

    for source, target in sorted(index.aliases.items()):
        if source not in index.by_ref:
            errors.append(f"alias source missing: {source}")
        if target not in index.by_ref:
            errors.append(f"alias target missing: {target}")
    return sorted(errors)
