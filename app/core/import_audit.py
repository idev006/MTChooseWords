from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from app.core.contracts import WordEntry
from app.core.docx_extractor import extract_docx_words
from app.core.extractor import extract_pdf_file_words
from app.core.review_registry import load_reviewed_suspicions
from app.core.source_contract import WordImportReport, collect_word_suspicions, validate_word_entries
from app.core.word_source_extractor import TableWordSourceExtractor


@dataclass(frozen=True)
class SourceAuditFile:
    source_file: str
    status: str = "PASS"
    error: str | None = None
    total_cells: int = 0
    unique_words: int = 0
    suspicions: list[dict] = field(default_factory=list)
    unresolved_suspicions: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class SourceAuditSummary:
    pass_count: int
    review_count: int
    fail_count: int
    total_cells: int
    unique_words: int


@dataclass(frozen=True)
class SourceAuditResult:
    source_count: int
    summary: SourceAuditSummary
    files: list[SourceAuditFile]
    rows: list[WordEntry]
    import_report: WordImportReport | None

    @property
    def can_import(self) -> bool:
        return self.summary.fail_count == 0 and self.summary.review_count == 0

    def blocking_message(self) -> str:
        return (
            f"PASS {self.summary.pass_count} ไฟล์, "
            f"REVIEW {self.summary.review_count} ไฟล์, "
            f"FAIL {self.summary.fail_count} ไฟล์"
        )


def extract_source_file(path: Path) -> list[WordEntry]:
    if path.suffix.lower() == ".docx":
        return extract_docx_words(path)
    if path.suffix.lower() == ".pdf":
        return extract_pdf_file_words(path)
    return []


def audit_word_sources(
    source: Path | Iterable[Path],
    review_registry_path: Path | None = None,
    extractor: TableWordSourceExtractor | None = None,
) -> SourceAuditResult:
    source_extractor = extractor or TableWordSourceExtractor()
    sources = source_extractor.sources_from(source)
    if not sources:
        raise ValueError("ไม่พบไฟล์ .docx หรือ .pdf ใน source ที่เลือก")

    reviewed = load_reviewed_suspicions(review_registry_path) if review_registry_path else set()
    files: list[SourceAuditFile] = []
    all_rows: list[WordEntry] = []

    for source_path in sources:
        try:
            rows = extract_source_file(source_path)
            report = validate_word_entries(rows)
            suspicions = collect_word_suspicions(rows)
            unresolved = [
                item for item in suspicions
                if (item.grade, item.text.casefold(), item.reason) not in reviewed
            ]
            files.append(SourceAuditFile(
                source_file=str(source_path),
                status="REVIEW" if unresolved else "PASS",
                total_cells=report.total_cells,
                unique_words=report.unique_words,
                suspicions=[asdict(item) for item in suspicions],
                unresolved_suspicions=[asdict(item) for item in unresolved],
            ))
            all_rows.extend(rows)
        except Exception as exc:
            files.append(SourceAuditFile(source_file=str(source_path), status="FAIL", error=str(exc)))

    import_report = validate_word_entries(all_rows) if all_rows else None
    summary = SourceAuditSummary(
        pass_count=sum(1 for item in files if item.status == "PASS"),
        review_count=sum(1 for item in files if item.status == "REVIEW"),
        fail_count=sum(1 for item in files if item.status == "FAIL"),
        total_cells=sum(item.total_cells for item in files),
        unique_words=import_report.unique_words if import_report else 0,
    )
    return SourceAuditResult(len(sources), summary, files, all_rows, import_report)


def write_audit_report(path: Path, result: SourceAuditResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_count": result.source_count,
        "summary": {
            "pass": result.summary.pass_count,
            "review": result.summary.review_count,
            "fail": result.summary.fail_count,
            "total_cells": result.summary.total_cells,
            "unique_words": result.summary.unique_words,
        },
        "files": [asdict(item) for item in result.files],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
