from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pdfplumber
from app.core.contracts import WordEntry
from app.core.source_contract import grade_from_name, source_index_from_text, validate_word_entries
from app.core.thai_normalizer import normalize_thai_word


_NOISE = re.compile(r"^(?:www\.|https?://|[\w.+-]+@[\w.-]+$|โทร$|หน้า\s*\d+|ป\.[ก-ฮ0-9๐-๙]+$)", re.I)
PdfProgress = Callable[[int, int, str], None]


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    words: list[str]
    source_indexes: list[int]


@dataclass(frozen=True)
class PdfPageDiagnostic:
    page_number: int
    table_count: int
    selected_rows: int
    selected_columns: int
    indexed_word_count: int
    legacy_word_count: int
    sample_words: list[str]
    error: str | None = None


def _cell_text(page, x0: float, x1: float, y0: float, y1: float) -> str:
    chars = []
    for char in page.chars:
        cx = (char["x0"] + char["x1"]) / 2
        cy = (char["top"] + char["bottom"]) / 2
        if x0 < cx < x1 and y0 < cy < y1 and char.get("text", "").strip():
            chars.append(char)
    chars.sort(key=lambda char: (char["x0"], char["top"]))
    # Some Thai PDFs place a combining mark after the following consonant
    # when sorted by x-coordinate (for example ก + น + ั). Move a run of
    # zero-width Thai marks back before that following consonant when their
    # x-coordinate is at its left edge. This restores logical Unicode order.
    i = 0
    while i + 2 < len(chars):
        current, following, mark = chars[i], chars[i + 1], chars[i + 2]
        if (unicodedata.category(mark["text"]).startswith("M")
                and not unicodedata.category(following["text"]).startswith("M")
                and mark["x0"] <= following["x0"] + 1.0):
            marks = [mark]
            j = i + 3
            while j < len(chars) and unicodedata.category(chars[j]["text"]).startswith("M"):
                marks.append(chars[j])
                j += 1
            chars[i + 1:j] = marks + [following]
            i = j
        else:
            i += 1
    return normalize_thai_word("".join(char["text"] for char in chars))


def _word_from_cell(page, cell) -> str:
    if not cell:
        return ""
    x0, top, x1, bottom = cell
    return _cell_text(page, x0, x1, top, bottom)


def _valid_pdf_word(word: str) -> bool:
    return bool(word and not _NOISE.match(word) and len(word) <= 60)


def _extract_indexed_pairs(page, table) -> tuple[list[str], list[int]]:
    words: list[str] = []
    source_indexes: list[int] = []
    for row in table.rows:
        cells = row.cells
        for cell_index in range(0, len(cells) - 1, 2):
            number_cell = cells[cell_index]
            word_cell = cells[cell_index + 1]
            if not number_cell or not word_cell:
                continue
            source_index = source_index_from_text(_word_from_cell(page, number_cell))
            if source_index is None:
                continue
            word = _word_from_cell(page, word_cell)
            if _valid_pdf_word(word):
                source_indexes.append(source_index)
                words.append(word)
            elif word:
                raise ValueError(f"page {page.page_number}: invalid word cell near index {source_index}: {word!r}")
    return words, source_indexes


def _extract_legacy_columns(page, table) -> tuple[list[str], list[int]]:
    words: list[str] = []
    source_indexes: list[int] = []
    for row in table.rows[2:]:
        for cell_index in (1, 5):
            if cell_index >= len(row.cells):
                continue
            word = _word_from_cell(page, row.cells[cell_index])
            if _valid_pdf_word(word):
                source_indexes.append(len(source_indexes) + 1)
                words.append(word)
            elif word:
                raise ValueError(f"page {page.page_number}: invalid legacy word cell: {word!r}")
    return words, source_indexes


def extract_table_pages(pdf: Path, progress: PdfProgress | None = None) -> list[ExtractedPage]:
    extracted: list[ExtractedPage] = []
    with pdfplumber.open(pdf) as document:
        total_pages = len(document.pages)
        for page_number, page in enumerate(document.pages, start=1):
            if progress:
                progress(page_number - 1, total_pages, f"กำลังอ่านหน้า {page_number}/{total_pages} ของ {pdf.name}")
            tables = page.find_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"})
            table = next((candidate for candidate in tables if len(candidate.rows) >= 5 and len(candidate.rows[0].cells) >= 4), None)
            if table is None:
                if progress:
                    progress(page_number, total_pages, f"ไม่พบตารางคำในหน้า {page_number}/{total_pages}")
                continue
            words, source_indexes = _extract_indexed_pairs(page, table)
            try:
                legacy_words, legacy_indexes = _extract_legacy_columns(page, table)
            except ValueError:
                legacy_words, legacy_indexes = [], []
            if len(legacy_words) > len(words):
                words, source_indexes = legacy_words, legacy_indexes
            if words:
                extracted.append(ExtractedPage(page_number, words, source_indexes))
            if progress:
                progress(page_number, total_pages, f"อ่านหน้า {page_number}/{total_pages} ได้ {len(words)} คำ")
    if not extracted:
        raise ValueError("no worksheet word tables found in PDF")
    return extracted


def extract_pdf_file_words(pdf: Path, progress: PdfProgress | None = None) -> list[WordEntry]:
    grade = grade_from_name(pdf)
    rows: list[WordEntry] = []
    try:
        for page in extract_table_pages(pdf, progress=progress):
            rows.extend(
                WordEntry(word, f"{pdf}#page={page.page_number}", grade, source_index)
                for source_index, word in zip(page.source_indexes, page.words)
            )
    except ValueError as exc:
        raise ValueError(f"{pdf.name}: {exc}") from exc
    return rows


def extract_pdf_words(directory: Path) -> list[WordEntry]:
    rows: list[WordEntry] = []
    for pdf in sorted(directory.glob("*.pdf")):
        rows.extend(extract_pdf_file_words(pdf))
    validate_word_entries(rows)
    return rows


def diagnose_pdf_file(pdf: Path, max_pages: int | None = None, start_page: int = 1, progress: PdfProgress | None = None) -> list[PdfPageDiagnostic]:
    diagnostics: list[PdfPageDiagnostic] = []
    with pdfplumber.open(pdf) as document:
        total_pages = len(document.pages)
        first_index = max(start_page - 1, 0)
        last_index = first_index + max_pages if max_pages else total_pages
        pages = document.pages[first_index:last_index]
        checked_pages = len(pages)
        for page_number, page in enumerate(pages, start=first_index + 1):
            if progress:
                progress(page_number - first_index - 1, checked_pages, f"กำลังตรวจหน้า {page_number} ของ {pdf.name}")
            try:
                tables = page.find_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"})
                table = next((candidate for candidate in tables if len(candidate.rows) >= 5 and len(candidate.rows[0].cells) >= 4), None)
                if table is None:
                    diagnostics.append(PdfPageDiagnostic(page_number, len(tables), 0, 0, 0, 0, []))
                else:
                    words, _ = _extract_indexed_pairs(page, table)
                    legacy_words, _ = _extract_legacy_columns(page, table)
                    sample = (legacy_words if len(legacy_words) > len(words) else words)[:10]
                    diagnostics.append(PdfPageDiagnostic(
                        page_number,
                        len(tables),
                        len(table.rows),
                        len(table.rows[0].cells),
                        len(words),
                        len(legacy_words),
                        sample,
                    ))
            except Exception as exc:
                diagnostics.append(PdfPageDiagnostic(page_number, 0, 0, 0, 0, 0, [], str(exc)))
            if progress:
                progress(page_number - first_index, checked_pages, f"ตรวจหน้า {page_number} แล้ว")
    return diagnostics


class PdfTableExtractor:
    """Production extractor implementing the application boundary contract."""

    def extract(self, directory: Path) -> list[WordEntry]:
        return extract_pdf_words(directory)
