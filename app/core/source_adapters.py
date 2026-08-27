from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Protocol

from app.core.contracts import WordEntry
from app.core.docx_extractor import extract_docx_words
from app.core.extractor import extract_pdf_file_words

SourceProgress = Callable[[int, int, str], None]


class WordSourceAdapter(Protocol):
    extensions: set[str]

    def extract(self, path: Path, progress: SourceProgress | None = None) -> list[WordEntry]: ...


@dataclass(frozen=True)
class DocxSourceAdapter:
    extensions: set[str]

    def extract(self, path: Path, progress: SourceProgress | None = None) -> list[WordEntry]:
        if progress:
            progress(0, 1, f"กำลังอ่าน DOCX {path.name}")
        rows = extract_docx_words(path)
        if progress:
            progress(1, 1, f"อ่าน DOCX แล้ว {path.name}")
        return rows


@dataclass(frozen=True)
class PdfSourceAdapter:
    extensions: set[str]

    def extract(self, path: Path, progress: SourceProgress | None = None) -> list[WordEntry]:
        return extract_pdf_file_words(path, progress=progress)


class SourceAdapterRegistry:
    def __init__(self, adapters: Iterable[WordSourceAdapter]):
        self._by_extension: dict[str, WordSourceAdapter] = {}
        for adapter in adapters:
            for extension in adapter.extensions:
                self._by_extension[extension.lower()] = adapter

    def adapter_for(self, path: Path) -> WordSourceAdapter | None:
        return self._by_extension.get(path.suffix.lower())

    def is_supported(self, path: Path) -> bool:
        return path.is_file() and not path.name.startswith("~$") and self.adapter_for(path) is not None

    def sources_from(self, source: Path | Iterable[Path]) -> list[Path]:
        candidates = [source] if isinstance(source, Path) else list(source)
        sources: list[Path] = []
        for candidate in candidates:
            if candidate.is_dir():
                sources.extend(sorted(candidate.iterdir()))
            else:
                sources.append(candidate)
        return [path for path in sources if self.is_supported(path)]

    def extract(self, path: Path, progress: SourceProgress | None = None) -> list[WordEntry]:
        adapter = self.adapter_for(path)
        if adapter is None:
            raise ValueError(f"ไม่รองรับไฟล์ source: {path.name}")
        return adapter.extract(path, progress=progress)


def default_source_registry() -> SourceAdapterRegistry:
    return SourceAdapterRegistry([
        DocxSourceAdapter({".docx"}),
        PdfSourceAdapter({".pdf"}),
    ])
