from pathlib import Path

from app.core.contracts import WordEntry
from app.core.source_adapters import SourceAdapterRegistry
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
