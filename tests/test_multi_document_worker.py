from pathlib import Path

from app.core.config import AppConfig
from app.core.contracts import WordEntry
from app.core.source_contract import validate_word_entries
from app.ui.main_window import ClearWordsWorker, GenerateWorker, WordImportWorker


class RecordingExporter:
    def __init__(self):
        self.calls = []

    def export(self, words_by_page, output, config, font_path, progress=None):
        self.calls.append((words_by_page, output))


class RecordingRepository:
    def __init__(self):
        self.added_rows = None
        self.clear_calls = 0
        self.replace_calls = 0

    def add_words(self, rows):
        self.added_rows = rows
        return len(rows)

    def clear_all(self):
        self.clear_calls += 1

    def replace_words(self, rows):
        self.replace_calls += 1
        return len(rows)


def test_worker_exports_each_document_to_a_separate_file():
    exporter = RecordingExporter()
    documents = [[['ก', 'ข']], [['ค', 'ง']]]
    outputs = [Path("set01.pdf"), Path("set02.pdf")]
    worker = GenerateWorker(documents, outputs, AppConfig(), Path("font.ttf"), exporter)

    worker.run()

    assert [call[1] for call in exporter.calls] == outputs
    assert [call[0] for call in exporter.calls] == documents


def test_word_import_button_worker_adds_without_clearing(tmp_path):
    rows = [WordEntry("กา", "p1.txt", 1, 1), WordEntry("ขา", "p1.txt", 1, 2)]
    audit = type("Audit", (), {"import_report": validate_word_entries(rows), "rows": rows})()
    repository = RecordingRepository()
    finished = []
    worker = WordImportWorker(audit, repository, False, tmp_path / "word_import_report.json")
    worker.done.connect(lambda count, action: finished.append((count, action)))

    worker.run()

    assert repository.added_rows == rows
    assert repository.clear_calls == 0
    assert repository.replace_calls == 0
    assert finished == [(2, "เพิ่ม")]


def test_clear_words_button_worker_only_clears_database():
    repository = RecordingRepository()
    finished = []
    worker = ClearWordsWorker(repository)
    worker.done.connect(lambda: finished.append(True))

    worker.run()

    assert repository.clear_calls == 1
    assert repository.added_rows is None
    assert repository.replace_calls == 0
    assert finished == [True]
