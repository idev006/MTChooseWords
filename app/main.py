import sys
from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication
from app.core.paths import application_root
from app.ui.main_window import MainWindow


def main() -> int:
    QLocale.setDefault(QLocale.c())
    app = QApplication(sys.argv)
    app.setApplicationName("MT Choose Words")
    window = MainWindow(application_root())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
