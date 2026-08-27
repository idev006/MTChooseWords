from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.core.contracts import WordEntry
from app.core.source_contract import validate_word_entries
from app.core.source_adapters import SourceAdapterRegistry, default_source_registry


class TableWordSourceExtractor:
    """Read supported table-based word sources: DOCX and text-layer PDF."""

    def __init__(self, registry: SourceAdapterRegistry | None = None):
        self.registry = registry or default_source_registry()

    def sources_from(self, source: Path | Iterable[Path]) -> list[Path]:
        return self.registry.sources_from(source)

    def _is_supported(self, path: Path) -> bool:
        return self.registry.is_supported(path)

    def extract(self, source: Path | Iterable[Path]) -> list[WordEntry]:
        rows: list[WordEntry] = []
        sources = self.sources_from(source)
        if not sources:
            raise ValueError("ไม่พบไฟล์ .docx หรือ .pdf ใน source ที่เลือก")

        for path in sources:
            rows.extend(self.registry.extract(path))

        validate_word_entries(rows)
        return rows
