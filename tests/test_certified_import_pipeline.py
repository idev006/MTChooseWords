import sqlite3
from pathlib import Path

from app.core.source_adapters import default_source_registry
from app.core.source_contract import validate_word_entries
from app.core.word_source_extractor import TableWordSourceExtractor


ROOT = Path(__file__).parents[1]
LOT1 = ROOT / "app/assets/words/lot1"
TEXT = ROOT / "app/assets/words/text"
DATABASE = ROOT / "app/mtchoosewords.sqlite3"

EXPECTED_COUNTS_BY_GRADE = {
    "ป.1": 1937,
    "ป.2": 2543,
    "ป.3": 2679,
    "ป.4": 2692,
    "ป.5": 2520,
    "ป.6": 2003,
}

EXPECTED_DATABASE_COUNTS = {
    "ป.1": 1544,
    "ป.2": 1474,
    "ป.3": 1498,
    "ป.4": 1443,
    "ป.5": 1513,
    "ป.6": 1233,
}


def test_real_docx_txt_sources_match_certified_baseline():
    sources = default_source_registry().sources_from([LOT1, TEXT])

    assert len(sources) == 12
    assert {source.suffix.lower() for source in sources} == {".docx", ".txt"}

    rows = TableWordSourceExtractor().extract([LOT1, TEXT])
    report = validate_word_entries(rows)

    assert report.total_cells == 14374
    assert report.unique_words == 8705
    assert report.duplicate_cells == 5669
    assert report.counts_by_grade == EXPECTED_COUNTS_BY_GRADE


def test_committed_database_matches_certified_import_baseline():
    assert DATABASE.exists()

    with sqlite3.connect(DATABASE) as connection:
        schema = connection.execute("pragma table_info(words)").fetchall()
        counts = dict(connection.execute("select grade, count(*) from words group by grade order by grade").fetchall())
        total = connection.execute("select count(*) from words").fetchone()[0]
        trim_violations = connection.execute("select count(*) from words where text != trim(text)").fetchone()[0]
        duplicate_keys = connection.execute(
            "select count(*) from (select grade, normalized, count(*) as n from words group by grade, normalized having n > 1)"
        ).fetchone()[0]
        sample = connection.execute(
            "select grade, normalized, text from words where normalized = ? order by grade",
            ("กา",),
        ).fetchall()
        absolute_source_paths = connection.execute(
            "select count(*) from words where source_file like 'F:%' or source_file like 'C:%' or source_file like '/%'"
        ).fetchone()[0]

    assert schema[0][1:3] == ("grade", "VARCHAR(8)")
    assert total == 8705
    assert counts == EXPECTED_DATABASE_COUNTS
    assert trim_violations == 0
    assert duplicate_keys == 0
    assert absolute_source_paths == 0
    assert sample == [("ป.1", "กา", "กา")]


def test_committed_import_evidence_uses_portable_paths():
    evidence_files = [
        ROOT / "app/doc/evidence/word_import_report.json",
        ROOT / "app/doc/evidence/word_source_audit_report.json",
        LOT1 / "mtchoosewords_import_journal.json",
        TEXT / "mtchoosewords_import_journal.json",
    ]

    for evidence in evidence_files:
        text = evidence.read_text(encoding="utf-8")
        assert str(ROOT) not in text
        assert "F:\\" not in text
        assert "C:\\" not in text
