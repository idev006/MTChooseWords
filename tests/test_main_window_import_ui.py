import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


class UiRepository:
    def count_by_grade(self):
        return {f"ป.{grade}": 0 for grade in range(1, 7)}

    def count(self, grades=None):
        return 0

    def random_words(self, amount, rng, grades=None):
        return []


def test_import_tab_uses_separate_clear_and_import_buttons():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Path(__file__).parents[1], repository=UiRepository())

    try:
        assert window.clear_words_button.text() == "ล้างข้อมูลคำในฐานข้อมูล"
        assert window.import_words_button.text() == "นำเข้ารายการคำ"
        assert not hasattr(window, "clear_before_reload")
    finally:
        window.close()
