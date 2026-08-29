from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.contracts import WordEntry
from app.core.paths import PathManager

THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
GRADE_RE = re.compile(r"(?:ป\.?|p)\s*([1-6๑-๖])", re.I)
ALLOWED_WORD_RE = re.compile(r"^[ก-๛A-Za-z0-9 .()/*+\-–_'\"“”]+$")


@dataclass(frozen=True)
class WordImportReport:
    total_cells: int
    unique_words: int
    counts_by_grade: dict[str, int]
    duplicate_cells: int
    source_files: list[str]


@dataclass(frozen=True)
class WordSuspicion:
    grade: int
    text: str
    source_file: str
    source_index: int | None
    reason: str


def grade_from_name(path: Path) -> int:
    match = GRADE_RE.search(path.stem)
    if not match:
        raise ValueError(f"ไม่พบระดับชั้น ป.1-ป.6 ในชื่อไฟล์: {path.name}")
    return int(match.group(1).translate(THAI_DIGITS))


def grade_key(grade: int) -> str:
    if not 1 <= grade <= 6:
        raise ValueError(f"ระดับชั้นไม่ถูกต้อง: {grade}")
    return f"ป.{grade}"


def source_index_from_text(value: str) -> int | None:
    cleaned = value.translate(THAI_DIGITS)
    cleaned = re.sub(r"[^\d]", "", cleaned)
    return int(cleaned) if cleaned else None


def _clean_word(text: str) -> str:
    return " ".join(text.split())


def collect_word_suspicions(entries: list[WordEntry]) -> list[WordSuspicion]:
    suspicions: list[WordSuspicion] = []
    seen: set[tuple[int, str]] = set()

    for entry in entries:
        text = _clean_word(entry.text)
        key = (grade_key(entry.grade), text.casefold())
        if key in seen:
            suspicions.append(WordSuspicion(entry.grade, text, entry.source_file, entry.source_index, "duplicate_in_same_grade"))
        seen.add(key)
        if len(text) > 40:
            suspicions.append(WordSuspicion(entry.grade, text, entry.source_file, entry.source_index, "long_cell_review"))
        if not re.search(r"[ก-๛A-Za-z]", text):
            suspicions.append(WordSuspicion(entry.grade, text, entry.source_file, entry.source_index, "no_letter_found"))
        if re.search(r"[^\w\sก-๛.()/*+\-–_'\"“”]", text, re.UNICODE):
            suspicions.append(WordSuspicion(entry.grade, text, entry.source_file, entry.source_index, "unusual_character_review"))
    return suspicions


def validate_word_entries(entries: list[WordEntry]) -> WordImportReport:
    if not entries:
        raise ValueError("ไม่พบคำศัพท์จาก source ที่กำหนด")

    keys: set[tuple[str, str]] = set()
    counts: Counter[str] = Counter()
    sources: set[str] = set()
    duplicate_cells = 0

    for entry in entries:
        if not 1 <= entry.grade <= 6:
            raise ValueError(f"ระดับชั้นไม่ถูกต้องจาก {entry.source_file}: {entry.grade}")
        text = _clean_word(entry.text)
        if not text:
            raise ValueError(f"พบ cell คำว่างจาก {entry.source_file}")
        if any(ord(char) < 32 for char in text):
            raise ValueError(f"พบ control character ในคำจาก {entry.source_file}: {text!r}")
        if not ALLOWED_WORD_RE.fullmatch(text):
            raise ValueError(f"พบอักขระผิดปกติในคำจาก {entry.source_file}: {text!r}")
        if len(text) > 120:
            raise ValueError(f"คำยาวผิดปกติจาก {entry.source_file}: {text}")

        grade = grade_key(entry.grade)
        counts[grade] += 1
        sources.add(entry.source_file)
        key = (grade, text.casefold())
        if key in keys:
            duplicate_cells += 1
        keys.add(key)

    return WordImportReport(
        total_cells=len(entries),
        unique_words=len(keys),
        counts_by_grade=dict(sorted(counts.items())),
        duplicate_cells=duplicate_cells,
        source_files=sorted(sources),
    )


def write_import_report(path: Path, report: WordImportReport, path_manager: PathManager | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    if path_manager:
        payload["source_files"] = [path_manager.display(source) for source in report.source_files]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
