from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from app.core.contracts import WordEntry
from app.core.review_registry import load_reviewed_suspicions
from app.core.source_adapters import SourceAdapterRegistry, default_source_registry
from app.core.source_contract import WordImportReport, collect_word_suspicions, validate_word_entries

AuditProgress = Callable[[int, int, str], None]


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


def _input_paths(source: Path | Iterable[Path]) -> list[Path]:
    return [source] if isinstance(source, Path) else list(source)


def _journal_folders(paths: list[Path]) -> list[Path]:
    folders: set[Path] = set()
    for path in paths:
        folders.add(path if path.is_dir() else path.parent)
    return sorted(folders)


def _write_source_journals(
    folders: list[Path],
    input_paths: list[Path],
    supported_sources: list[Path],
    result: SourceAuditResult | None,
    error: str | None = None,
) -> None:
    supported_names = {str(path) for path in supported_sources}
    files_payload = [asdict(item) for item in result.files] if result else []
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "production_source_formats": [".docx", ".txt"],
        "diagnostic_only_formats": [".pdf"],
        "inputs": [str(path) for path in input_paths],
        "supported_sources": sorted(supported_names),
        "summary": asdict(result.summary) if result else None,
        "can_import": result.can_import if result else False,
        "error": error,
        "files": files_payload,
    }
    for folder in folders:
        if folder.exists() and folder.is_dir():
            (folder / "mtchoosewords_import_journal.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )


def audit_word_sources(
    source: Path | Iterable[Path],
    review_registry_path: Path | None = None,
    registry: SourceAdapterRegistry | None = None,
    progress: AuditProgress | None = None,
) -> SourceAuditResult:
    source_registry = registry or default_source_registry()
    requested_paths = _input_paths(source)
    journal_folders = _journal_folders(requested_paths)
    sources = source_registry.sources_from(source)
    if not sources:
        message = "ไม่พบไฟล์ .docx หรือ .txt ใน source ที่เลือก; PDF ถูกปิดสำหรับ production import ชั่วคราว"
        _write_source_journals(journal_folders, requested_paths, sources, None, error=message)
        raise ValueError(message)

    reviewed = load_reviewed_suspicions(review_registry_path) if review_registry_path else set()
    files: list[SourceAuditFile] = []
    all_rows: list[WordEntry] = []

    for index, source_path in enumerate(sources, start=1):
        if progress:
            progress(index - 1, len(sources), f"กำลังตรวจ {source_path.name}")
        try:
            def source_progress(done: int, total: int, message: str):
                if progress:
                    file_fraction = done / max(total, 1)
                    overall_done = (index - 1) + file_fraction
                    progress(int(overall_done * 100), len(sources) * 100, message)

            rows = source_registry.extract(source_path, progress=source_progress)
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
        if progress:
            progress(index, len(sources), f"ตรวจแล้ว {source_path.name}")

    import_report = validate_word_entries(all_rows) if all_rows else None
    summary = SourceAuditSummary(
        pass_count=sum(1 for item in files if item.status == "PASS"),
        review_count=sum(1 for item in files if item.status == "REVIEW"),
        fail_count=sum(1 for item in files if item.status == "FAIL"),
        total_cells=sum(item.total_cells for item in files),
        unique_words=import_report.unique_words if import_report else 0,
    )
    result = SourceAuditResult(len(sources), summary, files, all_rows, import_report)
    _write_source_journals(journal_folders, requested_paths, sources, result)
    return result


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
