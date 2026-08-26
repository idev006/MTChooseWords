from pathlib import Path

import pytest

from app.core.extractor import extract_table_pages


@pytest.mark.integration
def test_source_pdf_table_is_extracted_completely():
    pdf = next((Path(__file__).parents[1] / "app/assets/words").glob("*.pdf"), None)
    if pdf is None:
        pytest.skip("PDF fixture is not included in lightweight source checkout")
    pages = extract_table_pages(pdf)
    assert len(pages) == 41
    assert sum(len(page.words) for page in pages) == 1210
    assert pages[0].words[:4] == ["กัน", "กระบุง", "กระจง", "กระมัง"]
    assert len(pages[-1].words) == 10
    assert all(word.strip() for page in pages for word in page.words)
