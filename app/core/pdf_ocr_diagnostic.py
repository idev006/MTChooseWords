from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
import re

import pdfplumber
import pymupdf
import pytesseract
from PIL import Image, ImageOps

from app.core.source_contract import source_index_from_text
from app.core.thai_normalizer import normalize_thai_word

_THAI_SPACED_CHARS_RE = re.compile(r"(?<=[ก-๛])\s+(?=[ก-๛])")
_WORDISH_RE = re.compile(r"[ก-๛A-Za-z]")
_THAI_WORDISH_RE = re.compile(r"[ก-๛]")
_NUMBERISH_RE = re.compile(r"^[\d๐-๙\s.]+$")
_THAI_DIGITISH_RE = re.compile(r"^[๐-๙\s.]+$")


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


def _candidate_review_reasons(source_index_text: str, word_text: str, confidence: float) -> list[str]:
    reasons: list[str] = []
    if confidence < 90:
        reasons.append("low_ocr_confidence")
    if not _THAI_WORDISH_RE.search(word_text):
        reasons.append("no_thai_letters")
    if not _THAI_DIGITISH_RE.match(" ".join(source_index_text.split())):
        reasons.append("source_index_needs_review")
    return reasons


def _save_cell_evidence(evidence_dir: Path | None, pdf: Path, page_number: int, candidate_number: int, image: Image.Image) -> str | None:
    if evidence_dir is None:
        return None
    target_dir = evidence_dir / pdf.stem / f"page-{page_number:03d}"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"cell-{candidate_number:03d}.png"
    image.save(path)
    return str(path)


def diagnose_pdf_ocr_cells(
    pdf: Path,
    page_number: int,
    max_cells: int = 80,
    evidence_dir: Path | None = None,
) -> list[OcrCellCandidate]:
    _configure_tesseract()
    candidates: list[OcrCellCandidate] = []
    with pymupdf.open(pdf) as image_doc, pdfplumber.open(pdf) as text_doc:
        image_page = image_doc[page_number - 1]
        text_page = text_doc.pages[page_number - 1]
        tables = text_page.find_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"})
        for table_index, table in enumerate(tables):
            if len(table.rows) < 2:
                continue
            for row_index, row in enumerate(table.rows):
                cells = _usable_cells(row.cells)
                for pair_index in range(0, len(cells) - 1):
                    number_cell = cells[pair_index]
                    word_cell = cells[pair_index + 1]
                    number_text, _ = _ocr_cell(image_page, number_cell)
                    if not _NUMBERISH_RE.match(" ".join(number_text.split())):
                        continue
                    source_index = source_index_from_text(number_text)
                    if source_index is None or source_index < 1:
                        continue
                    word_image = _render_cell(image_page, word_cell)
                    word_text, confidence = _ocr_image(word_image)
                    word_text = clean_ocr_word(word_text)
                    if not word_text or not _WORDISH_RE.search(word_text):
                        continue
                    reasons = _candidate_review_reasons(number_text, word_text, confidence)
                    evidence_image = _save_cell_evidence(evidence_dir, pdf, page_number, len(candidates) + 1, word_image)
                    candidates.append(OcrCellCandidate(
                        table_index,
                        row_index,
                        pair_index,
                        number_text,
                        source_index,
                        word_text,
                        confidence,
                        "REVIEW" if reasons else "ACCEPT",
                        reasons,
                        evidence_image,
                    ))
                    if len(candidates) >= max_cells:
                        return candidates
    return candidates
