from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from app.core.config import AppConfig

ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class WordEntry:
    text: str
    source_file: str
    grade: int
    source_index: int | None = None


class WordStore(Protocol):
    """Contract used by UI/application services for word persistence."""

    def add_words(self, rows: list[WordEntry] | list[tuple[str, str]]) -> int: ...
    def clear_all(self) -> None: ...
    def replace_words(self, rows: list[WordEntry] | list[tuple[str, str]]) -> int: ...
    def count(self, grades: list[int] | None = None) -> int: ...
    def random_words(self, amount: int, rng, grades: list[int] | None = None) -> list[str]: ...


class WordExtractor(Protocol):
    """Contract for extracting words from source files."""

    def extract(self, directory: Path) -> list[WordEntry]: ...


class PdfExporter(Protocol):
    """Contract for exporting selected words to a PDF document."""

    def export(self, words_by_page: list[list[str]], output: Path, config: AppConfig, font_path: Path, progress: ProgressCallback | None = None) -> None: ...
