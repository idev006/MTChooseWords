from pathlib import Path

from app.core.docx_extractor import DocxTableExtractor
from app.core.extractor import PdfTableExtractor
from app.core.word_source_extractor import TableWordSourceExtractor
from app.core.pdf_generator import ReportLabPdfExporter
from app.db.database import WordRepository


def test_production_adapters_expose_expected_boundaries(tmp_path):
    assert hasattr(PdfTableExtractor(), "extract")
    assert hasattr(DocxTableExtractor(), "extract")
    assert hasattr(TableWordSourceExtractor(), "extract")
    assert hasattr(ReportLabPdfExporter(), "export")
    assert hasattr(WordRepository(tmp_path / "words.sqlite3"), "replace_words")
