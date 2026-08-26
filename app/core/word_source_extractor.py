from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.core.contracts import WordEntry
from app.core.docx_extractor import extract_docx_words
from app.core.extractor import extract_pdf_file_words
from app.core.source_contract import validate_word_entries


class TableWordSourceExtractor:
    """Read supported table-based word sources: DOCX and text-layer PDF."""

    def _sources(self, source: Path | Iterable[Path]) -> list[Path]:
        if isinstance(source, Path):
            candidates = [source]
        else:
            candidates = list(source)
        sources: list[Path] = []
        for candidate in candidates:
            if candidate.is_dir():
                sources.extend(sorted(candidate.iterdir()))
            else:
                sources.append(candidate)
        return [path for path in sources if self._is_supported(path)]

    def _is_supported(self, path: Path) -> bool:
        return (
            path.is_file()
            and not path.name.startswith("~$")
            and path.suffix.lower() in {".docx", ".pdf"}
        )

    def extract(self, source: Path | Iterable[Path]) -> list[WordEntry]:
        rows: list[WordEntry] = []
        sources = self._sources(source)
        if not sources:
            raise ValueError("ไม่พบไฟล์ .docx หรือ .pdf ใน source ที่เลือก")

        for path in sources:
            if path.suffix.lower() == ".docx":
                rows.extend(extract_docx_words(path))
            elif path.suffix.lower() == ".pdf":
                rows.extend(extract_pdf_file_words(path))

        validate_word_entries(rows)
        return rows
