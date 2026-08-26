from pathlib import Path

from pypdf import PdfReader

from app.core.config import AppConfig
from app.core.pdf_generator import ReportLabPdfExporter


def test_pdf_exporter_creates_requested_pages(tmp_path):
    root = Path(__file__).parents[1]
    cfg = AppConfig(font_min_pt=12, font_max_pt=14, colors=["#123456"], title="ทดสอบ")
    output = tmp_path / "result.pdf"
    font = next((root / "app/assets/fonts").glob("*.ttf"))
    ReportLabPdfExporter().export([["กัน", "กระบุง"], ["กระจง"]], output, cfg, font)
    reader = PdfReader(str(output))
    assert len(reader.pages) == 2
    assert output.stat().st_size > 0
