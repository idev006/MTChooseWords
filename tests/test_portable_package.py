from pathlib import Path


def test_pyinstaller_spec_does_not_bundle_word_assets_into_exe():
    spec = Path("mt_choose_words.spec").read_text(encoding="utf-8")

    assert "app\" / \"assets" not in spec
    assert "app/assets" not in spec
    assert "config.toml" not in spec


def test_portable_builder_excludes_retired_pdf_and_doc_sources():
    script = Path("scripts/build_portable.py").read_text(encoding="utf-8")

    assert "app/assets/words/pdf" not in script
    assert '{".docx", ".json"}' in script
    assert '{".txt", ".json"}' in script
    assert '".doc"' not in script
    assert '"pdf_ocr_cells"' in script
    assert '"pdf_ocr_page_reports"' in script
    assert "Run_MTChooseWords_Portable.bat" in script
