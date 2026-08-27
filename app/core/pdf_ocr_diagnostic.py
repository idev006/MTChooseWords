from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable

import pdfplumber
import pymupdf
import pytesseract
from PIL import Image, ImageOps

from app.core.source_contract import source_index_from_text
from app.core.thai_normalizer import normalize_thai_word

OcrProgress = Callable[[int, int, str], None]
_THAI_SPACED_CHARS_RE = re.compile(r"(?<=[ก-๛])\s+(?=[ก-๛])")
_WORDISH_RE = re.compile(r"[ก-๛A-Za-z]")
_THAI_WORDISH_RE = re.compile(r"[ก-๛]")
_NUMBERISH_RE = re.compile(r"^[\d๐-๙\s.]+$")
_THAI_DIGITISH_RE = re.compile(r"^[๐-๙\s.]+$")
_HEADER_WORDS = {"คำ", "คํา", "คำที่", "คําที่"}


@dataclass(frozen=True)
class OcrCellCandidate:
    table_index: int
    row_index: int
    pair_index: int
    source_index_text: str
    source_index: int | None
    word_text: str
    confidence: float
    status: str
    reasons: list[str]
    evidence_image: str | None = None


def _configure_tesseract() -> None:
    command = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(command).exists():
        pytesseract.pytesseract.tesseract_cmd = command


def _render_cell(page, cell, scale: float = 4.0) -> Image.Image:
    x0, top, x1, bottom = cell
    rect = pymupdf.Rect(x0 - 1, top - 1, x1 + 1, bottom + 1)
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=rect, alpha=False)
    return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)


def _ocr_image(image: Image.Image) -> tuple[str, float]:
    image = ImageOps.grayscale(image)
    data = pytesseract.image_to_data(
        image,
        lang="tha+eng",
        config="--psm 7",
        output_type=pytesseract.Output.DICT,
    )
    words: list[str] = []
    confidences: list[float] = []
    for text, confidence in zip(data.get("text", []), data.get("conf", [])):
        cleaned = " ".join(str(text).split())
        if not cleaned:
            continue
        words.append(cleaned)
        try:
            value = float(confidence)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            confidences.append(value)
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return " ".join(words), average_confidence


def _ocr_cell(page, cell, scale: float = 4.0) -> tuple[str, float]:
    return _ocr_image(_render_cell(page, cell, scale))


def clean_ocr_word(text: str) -> str:
    cleaned = " ".join(text.split())
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = _THAI_SPACED_CHARS_RE.sub("", cleaned)
    cleaned = re.sub(r"\(\s+", "(", cleaned)
    cleaned = re.sub(r"\s+\)", ")", cleaned)
    cleaned = re.sub(r"\s*-\s*", "-", cleaned)
    return normalize_thai_word(cleaned)


def _usable_cells(cells) -> list:
    usable = [cell for cell in cells if cell is not None and cell[2] - cell[0] > 8 and cell[3] - cell[1] > 8]
    return sorted(usable, key=lambda cell: (cell[0], cell[1]))


def _candidate_tables(tables, page_width: float, page_height: float) -> list:
    candidates = []
    for table in tables:
        if len(table.rows) < 3:
            continue
        max_columns = max((len(_usable_cells(row.cells)) for row in table.rows), default=0)
        if max_columns < 6:
            continue
        x0, top, x1, bottom = table.bbox
        width = x1 - x0
        height = bottom - top
        if width > page_width * 1.05 or height > page_height * 0.7:
            continue
        candidates.append(table)
    return candidates


def _candidate_review_reasons(source_index_text: str, word_text: str, confidence: float) -> list[str]:
    reasons: list[str] = []
    if confidence < 90:
        reasons.append("low_ocr_confidence")
    if not _THAI_WORDISH_RE.search(word_text):
        reasons.append("no_thai_letters")
    if not _THAI_DIGITISH_RE.match(" ".join(source_index_text.split())):
        reasons.append("source_index_needs_review")
    return reasons


def _valid_ocr_word_candidate(word_text: str) -> bool:
    return bool(word_text and _WORDISH_RE.search(word_text) and word_text not in _HEADER_WORDS)


def _save_cell_evidence(evidence_dir: Path | None, pdf: Path, page_number: int, candidate_number: int, image: Image.Image) -> str | None:
    if evidence_dir is None:
        return None
    target_dir = evidence_dir / pdf.stem / f"page-{page_number:03d}"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"cell-{candidate_number:03d}.png"
    image.save(path)
    return str(path)


def _diagnose_open_page(
    pdf: Path,
    image_page,
    text_page,
    page_number: int,
    max_cells: int = 80,
    evidence_dir: Path | None = None,
    evidence_statuses: set[str] | None = None,
) -> list[OcrCellCandidate]:
    candidates: list[OcrCellCandidate] = []
    tables = text_page.find_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"})
    for table_index, table in enumerate(_candidate_tables(tables, text_page.width, text_page.height)):
        for row_index, row in enumerate(table.rows):
            cells = _usable_cells(row.cells)
            for pair_index in range(0, len(cells) - 1):
                number_cell = cells[pair_index]
                word_cell = cells[pair_index + 1]
                word_image = _render_cell(image_page, word_cell)
                word_text, confidence = _ocr_image(word_image)
                word_text = clean_ocr_word(word_text)
                if not _valid_ocr_word_candidate(word_text):
                    continue
                number_text, _ = _ocr_cell(image_page, number_cell)
                source_index = source_index_from_text(number_text)
                is_numberish = _NUMBERISH_RE.match(" ".join(number_text.split())) is not None
                if not is_numberish and pair_index % 2 != 0:
                    continue
                if source_index is not None and source_index < 1:
                    source_index = None
                reasons = _candidate_review_reasons(number_text, word_text, confidence)
                if not is_numberish or source_index is None:
                    reasons.append("source_index_missing_or_unreadable")
                status = "REVIEW" if reasons else "ACCEPT"
                should_save_evidence = evidence_statuses is None or status in evidence_statuses
                evidence_image = _save_cell_evidence(evidence_dir, pdf, page_number, len(candidates) + 1, word_image) if should_save_evidence else None
                candidates.append(OcrCellCandidate(
                    table_index,
                    row_index,
                    pair_index,
                    number_text,
                    source_index,
                    word_text,
                    confidence,
                    status,
                    reasons,
                    evidence_image,
                ))
                if len(candidates) >= max_cells:
                    return candidates
    return candidates


def diagnose_pdf_ocr_cells(
    pdf: Path,
    page_number: int,
    max_cells: int = 80,
    evidence_dir: Path | None = None,
    evidence_statuses: set[str] | None = None,
) -> list[OcrCellCandidate]:
    _configure_tesseract()
    with pymupdf.open(pdf) as image_doc, pdfplumber.open(pdf) as text_doc:
        image_page = image_doc[page_number - 1]
        text_page = text_doc.pages[page_number - 1]
        return _diagnose_open_page(pdf, image_page, text_page, page_number, max_cells, evidence_dir, evidence_statuses)


def diagnose_pdf_ocr_file(
    pdf: Path,
    start_page: int = 1,
    max_pages: int | None = None,
    max_cells_per_page: int = 120,
    evidence_dir: Path | None = None,
    evidence_statuses: set[str] | None = None,
    progress: OcrProgress | None = None,
) -> list[tuple[int, list[OcrCellCandidate]]]:
    _configure_tesseract()
    pages: list[tuple[int, list[OcrCellCandidate]]] = []
    with pymupdf.open(pdf) as image_doc, pdfplumber.open(pdf) as text_doc:
        total_pages = len(image_doc)
        first_index = max(start_page - 1, 0)
        last_index = min(total_pages, first_index + max_pages) if max_pages else total_pages
        for page_index in range(first_index, last_index):
            page_number = page_index + 1
            if progress:
                progress(page_number - first_index - 1, last_index - first_index, f"กำลัง OCR หน้า {page_number}/{total_pages}: {pdf.name}")
            candidates = _diagnose_open_page(
                pdf,
                image_doc[page_index],
                text_doc.pages[page_index],
                page_number,
                max_cells=max_cells_per_page,
                evidence_dir=evidence_dir,
                evidence_statuses=evidence_statuses,
            )
            pages.append((page_number, candidates))
            if progress:
                progress(page_number - first_index, last_index - first_index, f"OCR หน้า {page_number}/{total_pages} ได้ {len(candidates)} รายการ")
    return pages
