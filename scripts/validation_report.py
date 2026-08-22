from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True, order=True)
class ValidationIssue:
    path: str
    code: str
    message: str


@dataclass
class ValidationReport:
    documents_checked: int = 0
    catalog_entries: int = 0
    legacy_entries: int = 0
    strict_entries: int = 0
    strict_schema_entries: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    def sorted_issues(self):
        return sorted(self.issues)

    def write_json(self, path: Path):
        payload = {
            "summary": {
                "documents_checked": self.documents_checked,
                "catalog_entries": self.catalog_entries,
                "legacy_entries": self.legacy_entries,
                "strict_entries": self.strict_entries,
                "strict_schema_entries": self.strict_schema_entries,
                "issue_count": len(self.issues),
            },
            "issues": [asdict(issue) for issue in self.sorted_issues()],
        }
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
