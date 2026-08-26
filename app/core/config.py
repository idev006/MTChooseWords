from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from tomlkit import dumps, parse


@dataclass
class AppConfig:
    words_dir: str = "app/assets/words/lot1"
    word_source_files: list[str] = field(default_factory=list)
    fonts_dir: str = "app/assets/fonts"
    output_dir: str = "app/output"
    database: str = "app/mtchoosewords.sqlite3"
    orientation: str = "portrait"
    pages: int = 1
    words_per_page: int = 30
    document_sets: int = 1
    font_min_pt: int = 20
    font_max_pt: int = 60
    rotation_min: int = -45
    rotation_max: int = 45
    title: str = "คำศัพท์"
    title_font_size: int = 28
    title_color: str = "#263238"
    title_margin_top_px: int = 10
    title_margin_bottom_px: int = 18
    title_padding_px: int = 6
    title_bgcolor: str = "#FFFFFF"
    page_margin_pt: int = 24
    seed: int = 0
    selected_grades: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6])
    clear_words_before_import: bool = True
    colors: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        if not path.exists():
            return cls()
        doc = parse(path.read_text(encoding="utf-8"))
        paths, pdf, colors = doc.get("paths", {}), doc.get("pdf", {}), doc.get("colors", {})
        selected_grades = [int(value) for value in pdf.get("selected_grades", cls().selected_grades)]
        return cls(
            words_dir=str(paths.get("words_dir", cls.words_dir)),
            word_source_files=list(paths.get("word_source_files", [])),
            fonts_dir=str(paths.get("fonts_dir", cls.fonts_dir)),
            output_dir=str(paths.get("output_dir", cls.output_dir)),
            database=str(paths.get("database", cls.database)),
            orientation=str(pdf.get("orientation", cls.orientation)),
            pages=int(pdf.get("pages", cls.pages)), words_per_page=int(pdf.get("words_per_page", cls.words_per_page)),
            document_sets=int(pdf.get("document_sets", cls.document_sets)),
            font_min_pt=int(pdf.get("font_min_pt", cls.font_min_pt)), font_max_pt=int(pdf.get("font_max_pt", cls.font_max_pt)),
            rotation_min=int(pdf.get("rotation_min", cls.rotation_min)), rotation_max=int(pdf.get("rotation_max", cls.rotation_max)),
            title=str(pdf.get("title", cls.title)), title_font_size=int(pdf.get("title_font_size", cls.title_font_size)),
            title_color=str(pdf.get("title_color", cls.title_color)), title_margin_top_px=int(pdf.get("title_margin_top_px", cls.title_margin_top_px)),
            title_margin_bottom_px=int(pdf.get("title_margin_bottom_px", cls.title_margin_bottom_px)),
            title_padding_px=int(pdf.get("title_padding_px", cls.title_padding_px)), title_bgcolor=str(pdf.get("title_bgcolor", cls.title_bgcolor)),
            page_margin_pt=int(pdf.get("page_margin_pt", cls.page_margin_pt)), seed=int(pdf.get("seed", cls.seed)),
            selected_grades=[grade for grade in selected_grades if 1 <= grade <= 6] or cls().selected_grades,
            clear_words_before_import=bool(pdf.get("clear_words_before_import", cls.clear_words_before_import)),
            colors=list(colors.get("values", [])),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        doc: dict[str, Any] = {"paths": {}, "pdf": {}, "colors": {}}
        for key in ("words_dir", "fonts_dir", "output_dir", "database", "word_source_files"):
            doc["paths"][key] = getattr(self, key)
        for key in ("orientation", "pages", "words_per_page", "document_sets", "font_min_pt", "font_max_pt", "rotation_min", "rotation_max", "title", "title_font_size", "title_color", "title_margin_top_px", "title_margin_bottom_px", "title_padding_px", "title_bgcolor", "page_margin_pt", "seed"):
            doc["pdf"][key] = getattr(self, key)
        doc["pdf"]["selected_grades"] = self.selected_grades
        doc["pdf"]["clear_words_before_import"] = self.clear_words_before_import
        doc["colors"]["values"] = self.colors
        path.write_text(dumps(doc), encoding="utf-8")

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else Path.cwd() / path
