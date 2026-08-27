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


@dataclass(frozen=True)
class OcrCellCandidate:
    table_index: int
    row_index: int
    pair_index: int
    source_index_text: str
    source_index: int | None
    word_text: str
    confidence: float


def _configure_tesseract() -> None:
    command = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(command).exists():
        pytesseract.pytesseract.tesseract_cmd = command


def _ocr_cell(page, cell, scale: float = 4.0) -> tuple[str, float]:
    x0, top, x1, bottom = cell
    rect = pymupdf.Rect(x0 - 1, top - 1, x1 + 1, bottom + 1)
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=rect, alpha=False)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
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


def diagnose_pdf_ocr_cells(pdf: Path, page_number: int, max_cells: int = 80) -> list[OcrCellCandidate]:
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
                cells = row.cells
                for pair_index in range(0, len(cells) - 1, 2):
                    number_cell = cells[pair_index]
                    word_cell = cells[pair_index + 1]
                    if not number_cell or not word_cell:
                        continue
                    number_text, _ = _ocr_cell(image_page, number_cell)
                    source_index = source_index_from_text(number_text)
                    if source_index is None or source_index < 1:
                        continue
                    word_text, confidence = _ocr_cell(image_page, word_cell)
                    word_text = clean_ocr_word(word_text)
                    if not word_text or not _WORDISH_RE.search(word_text):
                        continue
                    candidates.append(OcrCellCandidate(
                        table_index,
                        row_index,
                        pair_index // 2,
                        number_text,
                        source_index,
                        word_text,
                        confidence,
                    ))
                    if len(candidates) >= max_cells:
                        return candidates
    return candidates
