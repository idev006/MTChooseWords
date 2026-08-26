from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from app.core.contracts import WordEntry
from app.core.source_contract import grade_from_name, source_index_from_text, validate_word_entries
from app.core.thai_normalizer import normalize_thai_word

_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
_NOISE = re.compile(r"^(?:หน้า\s*\d+|บัญชีคำ|www\.|https?://)", re.I)


def _cell_text(cell: ElementTree.Element) -> str:
    parts: list[str] = []
    for text in cell.findall(".//w:t", _NS):
        if text.text:
            parts.append(text.text)
    return " ".join("".join(parts).split())


def _table_rows(document_xml: bytes) -> list[list[str]]:
    root = ElementTree.fromstring(document_xml)
    rows: list[list[str]] = []
    for table in root.findall(".//w:tbl", _NS):
        for row in table.findall("./w:tr", _NS):
            rows.append([_cell_text(cell) for cell in row.findall("./w:tc", _NS)])
    return rows


def _is_valid_word(value: str) -> bool:
    if not value or _NOISE.match(value):
        return False
    if len(value) > 60:
        return False
    return not bool(re.fullmatch(r"[\d๐-๙.\s]+", value))


def _entries_from_rows(rows: list[list[str]], path: Path, grade: int) -> list[WordEntry]:
    entries: list[WordEntry] = []
    for cells in rows:
        if len(cells) < 2:
            continue
        for index in range(0, len(cells) - 1, 2):
            source_index = source_index_from_text(cells[index])
            if source_index is None:
                continue
            word = normalize_thai_word(cells[index + 1])
            if _is_valid_word(word):
                entries.append(WordEntry(word, str(path), grade, source_index))
            elif word:
                raise ValueError(f"{path.name}: cell ลำดับ {source_index} ไม่ใช่คำศัพท์ที่อ่านได้: {word}")
    return entries


def _validate_entries(entries: list[WordEntry], path: Path, grade: int) -> None:
    if not entries:
        raise ValueError(f"{path.name}: ไม่พบคำศัพท์ในตาราง")


def extract_docx_words(path: Path) -> list[WordEntry]:
    grade = grade_from_name(path)
    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
    entries = _entries_from_rows(_table_rows(document_xml), path, grade)
    _validate_entries(entries, path, grade)
    return sorted(entries, key=lambda entry: entry.source_index or 0)


class DocxTableExtractor:
    """Extract only vocabulary cells from DOCX tables."""

    def extract(self, directory: Path) -> list[WordEntry]:
        rows: list[WordEntry] = []
        for path in sorted(directory.glob("*.docx")):
            if path.name.startswith("~$"):
                continue
            rows.extend(extract_docx_words(path))
        if not rows:
            raise ValueError(f"ไม่พบไฟล์ .docx ใน {directory}")
        validate_word_entries(rows)
        return rows
