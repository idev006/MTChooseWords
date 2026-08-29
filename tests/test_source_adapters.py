from pathlib import Path

from app.core.contracts import WordEntry
from app.core.source_adapters import SourceAdapterRegistry, default_source_registry
from app.core.word_source_extractor import TableWordSourceExtractor


class FakeAdapter:
    extensions = {".fake"}

    def extract(self, path: Path, progress=None):
        if progress:
            progress(1, 1, f"read {path.name}")
        return [WordEntry("กา", str(path), 1, 1)]


def test_table_source_extractor_uses_injected_adapter_registry(tmp_path):
    source = tmp_path / "บัญชีคำพื้นฐาน ป.1.fake"
    source.write_text("fixture", encoding="utf-8")
    registry = SourceAdapterRegistry([FakeAdapter()])

    rows = TableWordSourceExtractor(registry).extract(tmp_path)

    assert [(row.grade, row.text) for row in rows] == [(1, "กา")]


def test_default_source_registry_disables_pdf_for_production_import(tmp_path):
    pdf = tmp_path / "บัญชีคำพื้นฐาน ป.1.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    assert default_source_registry().sources_from(tmp_path) == []


def test_pdf_word_reader_dependencies_are_not_in_local_scope():
    blocked = {"pdfplumber", "pymupdf", "pytesseract", "pythainlp"}
    requirements = Path("requirements.txt").read_text(encoding="utf-8").casefold()
    spec = Path("mt_choose_words.spec").read_text(encoding="utf-8").casefold()

    for package in blocked:
        assert package not in requirements
        assert package not in spec
