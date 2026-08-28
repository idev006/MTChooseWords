from __future__ import annotations

from pathlib import Path

from app.core.contracts import WordEntry
from app.core.source_contract import grade_from_name, validate_word_entries
from app.core.thai_normalizer import normalize_thai_word


def extract_text_words(path: Path) -> list[WordEntry]:
    grade = grade_from_name(path)
    entries: list[WordEntry] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        word = normalize_thai_word(line.strip())
        if not word:
            continue
        entries.append(WordEntry(word, str(path), grade, line_number))
    if not entries:
        raise ValueError(f"{path.name}: ไม่พบคำศัพท์ในไฟล์ text")
    validate_word_entries(entries)
    return entries


class TextLineExtractor:
    """Extract one vocabulary word per non-empty line from UTF-8 text files."""

    def extract(self, directory: Path) -> list[WordEntry]:
        rows: list[WordEntry] = []
        for path in sorted(directory.glob("*.txt")):
            if path.name.startswith("~$"):
                continue
            rows.extend(extract_text_words(path))
        if not rows:
            raise ValueError(f"ไม่พบไฟล์ .txt ใน {directory}")
        validate_word_entries(rows)
        return rows
