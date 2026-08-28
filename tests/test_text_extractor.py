from pathlib import Path

from app.core.import_audit import audit_word_sources
from app.core.source_adapters import default_source_registry
from app.core.text_extractor import extract_text_words
from app.core.word_source_extractor import TableWordSourceExtractor


def test_text_extractor_reads_one_word_per_non_empty_line(tmp_path):
    source = tmp_path / "คลังคำศัพท์ภาษาไทย_ป1_VISUAL_VERIFIED.txt"
    source.write_text("\ufeffกา\n\nขา\n  คำ  \n", encoding="utf-8")

    rows = extract_text_words(source)

    assert [(row.grade, row.source_index, row.text) for row in rows] == [
        (1, 1, "กา"),
        (1, 3, "ขา"),
        (1, 4, "คำ"),
    ]


def test_table_source_extractor_reads_txt_production_source(tmp_path):
    source = tmp_path / "คลังคำศัพท์ภาษาไทย_ป2_VISUAL_VERIFIED.txt"
    source.write_text("เรือ\nน้ำ\n", encoding="utf-8")

    rows = TableWordSourceExtractor().extract(tmp_path)

    assert [(row.grade, row.text) for row in rows] == [(2, "เรือ"), (2, "น้ำ")]


def test_default_source_registry_supports_txt_and_docx_but_not_pdf(tmp_path):
    (tmp_path / "คลังคำศัพท์ภาษาไทย_ป1_VISUAL_VERIFIED.txt").write_text("กา\n", encoding="utf-8")
    (tmp_path / "บัญชีคำพื้นฐาน ป.1.pdf").write_bytes(b"%PDF-1.4\n")

    sources = default_source_registry().sources_from(tmp_path)

    assert [path.suffix for path in sources] == [".txt"]


def test_audit_writes_source_folder_journal(tmp_path):
    source = tmp_path / "คลังคำศัพท์ภาษาไทย_ป3_VISUAL_VERIFIED.txt"
    source.write_text("ภูเขา\nทะเล\nภูเขา\n", encoding="utf-8")

    audit = audit_word_sources(tmp_path)

    journal = tmp_path / "mtchoosewords_import_journal.json"
    assert journal.exists()
    text = journal.read_text(encoding="utf-8")
    assert '"production_source_formats": [' in text
    assert '"unique_words": 2' in text
    assert audit.summary.total_cells == 3
