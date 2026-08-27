from pathlib import Path
from zipfile import ZipFile

from app.core.contracts import WordEntry
from app.core.docx_extractor import DocxTableExtractor
from app.core.import_audit import audit_word_sources
from app.core.review_registry import load_reviewed_suspicions
from app.core.source_contract import collect_word_suspicions, validate_word_entries
from app.core.word_source_extractor import TableWordSourceExtractor
from scripts.audit_word_sources import main as audit_main


DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>ข้อความนอกตารางต้องไม่ถูกอ่าน</w:t></w:r></w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>ที่</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>คำ</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>ที่</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>คำ</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>๑.</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>กา</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>๒.</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>คำ</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""


def _write_docx(path: Path) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", DOCUMENT_XML)


def _write_docx_with_word(path: Path, word: str) -> None:
    xml = DOCUMENT_XML.replace("<w:t>กา</w:t>", f"<w:t>{word}</w:t>").replace("<w:t>คำ</w:t>", "<w:t>ขา</w:t>")
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


def test_docx_extractor_reads_only_table_word_cells(tmp_path):
    source = tmp_path / "บัญชีคำพื้นฐาน ป.1.docx"
    _write_docx(source)

    rows = DocxTableExtractor().extract(tmp_path)

    assert [(row.grade, row.source_index, row.text) for row in rows] == [
        (1, 1, "กา"),
        (1, 2, "คำ"),
    ]


def test_table_source_extractor_reads_docx_and_ignores_doc(tmp_path):
    _write_docx(tmp_path / "บัญชีคำพื้นฐาน ป.1.docx")
    (tmp_path / "บัญชีคำพื้นฐาน ป.1.doc").write_text("ไม่ควรถูกอ่าน", encoding="utf-8")

    rows = TableWordSourceExtractor().extract(tmp_path)

    assert [row.text for row in rows] == ["กา", "คำ"]


def test_source_contract_rejects_missing_grade(tmp_path):
    source = tmp_path / "บัญชีคำพื้นฐาน.docx"
    _write_docx(source)

    try:
        DocxTableExtractor().extract(tmp_path)
    except ValueError as exc:
        assert "ไม่พบระดับชั้น" in str(exc)
    else:
        raise AssertionError("missing grade should fail closed")


def test_import_report_counts_duplicate_cells():
    report = validate_word_entries([
        WordEntry("กา", "p1.docx", 1, 1),
        WordEntry("กา", "p1.docx", 1, 2),
        WordEntry("ขา", "p2.docx", 2, 1),
    ])

    assert report.total_cells == 3
    assert report.unique_words == 2
    assert report.duplicate_cells == 1
    assert report.counts_by_grade == {1: 2, 2: 1}


def test_source_contract_rejects_corrupt_pdf_text_layer_characters():
    try:
        validate_word_entries([WordEntry("ฟาງ", "p3.pdf", 3, 1)])
    except ValueError as exc:
        assert "อักขระผิดปกติ" in str(exc)
    else:
        raise AssertionError("corrupt text-layer characters should fail closed")


def test_long_wrapped_words_are_allowed_but_marked_for_review():
    long_word = "พระราชบัญญัติการศึกษาแห่งชาติฉบับปรับปรุงเพิ่มเติม"
    rows = [WordEntry(long_word, "p6.docx", 6, 1)]

    report = validate_word_entries(rows)
    suspicions = collect_word_suspicions(rows)

    assert report.total_cells == 1
    assert suspicions[0].reason == "long_cell_review"


def test_review_registry_loads_approved_suspicions(tmp_path):
    registry = tmp_path / "reviewed.json"
    registry.write_text('{"approved_suspicions":[{"grade":1,"text":" ชิ้น ","reason":"duplicate_in_same_grade"}]}', encoding="utf-8")

    assert load_reviewed_suspicions(registry) == {(1, "ชิ้น", "duplicate_in_same_grade")}


def test_audit_cli_fails_when_review_is_unresolved(tmp_path, monkeypatch):
    source = tmp_path / "บัญชีคำพื้นฐาน ป.1.docx"
    _write_docx_with_word(source, "พระราชบัญญัติการศึกษาแห่งชาติฉบับปรับปรุงเพิ่มเติม")
    monkeypatch.setattr("sys.argv", ["audit_word_sources.py", str(source), "--output", str(tmp_path / "audit.json")])

    assert audit_main() == 1


def test_import_audit_blocks_unreviewed_suspicions(tmp_path):
    source = tmp_path / "บัญชีคำพื้นฐาน ป.1.docx"
    _write_docx_with_word(source, "พระราชบัญญัติการศึกษาแห่งชาติฉบับปรับปรุงเพิ่มเติม")

    audit = audit_word_sources(source, tmp_path / "reviewed.json")

    assert audit.can_import is False
    assert audit.summary.review_count == 1


def test_import_audit_allows_reviewed_suspicions(tmp_path):
    source = tmp_path / "บัญชีคำพื้นฐาน ป.1.docx"
    reviewed = tmp_path / "reviewed.json"
    word = "พระราชบัญญัติการศึกษาแห่งชาติฉบับปรับปรุงเพิ่มเติม"
    _write_docx_with_word(source, word)
    reviewed.write_text(
        '{"approved_suspicions":[{"grade":1,"text":"พระราชบัญญัติการศึกษาแห่งชาติฉบับปรับปรุงเพิ่มเติม","reason":"long_cell_review"}]}',
        encoding="utf-8",
    )

    audit = audit_word_sources(source, reviewed)

    assert audit.can_import is True
    assert audit.summary.pass_count == 1


def test_import_audit_reports_progress(tmp_path):
    source = tmp_path / "บัญชีคำพื้นฐาน ป.1.docx"
    events = []
    _write_docx(source)

    audit_word_sources(source, progress=lambda done, total, message: events.append((done, total, message)))

    assert events[0][0] == 0
    assert events[-1][0] == events[-1][1]
    assert "บัญชีคำพื้นฐาน ป.1.docx" in events[-1][2]
