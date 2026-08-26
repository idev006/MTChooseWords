from pathlib import Path

from app.core.config import AppConfig
from app.ui.main_window import GenerateWorker


class RecordingExporter:
    def __init__(self):
        self.calls = []

    def export(self, words_by_page, output, config, font_path, progress=None):
        self.calls.append((words_by_page, output))


def test_worker_exports_each_document_to_a_separate_file():
    exporter = RecordingExporter()
    documents = [[['ก', 'ข']], [['ค', 'ง']]]
    outputs = [Path("set01.pdf"), Path("set02.pdf")]
    worker = GenerateWorker(documents, outputs, AppConfig(), Path("font.ttf"), exporter)

    worker.run()

    assert [call[1] for call in exporter.calls] == outputs
    assert [call[0] for call in exporter.calls] == documents
