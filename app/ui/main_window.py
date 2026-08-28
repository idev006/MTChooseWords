from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QLocale, QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QRadioButton,
    QSlider, QSpinBox, QStatusBar, QTabWidget, QVBoxLayout, QWidget,
)

from app.core.config import AppConfig
from app.core.contracts import PdfExporter, WordExtractor, WordStore
from app.core.import_audit import audit_word_sources, write_audit_report
from app.core.pdf_generator import ReportLabPdfExporter
from app.core.source_contract import write_import_report
from app.core.word_source_extractor import TableWordSourceExtractor
from app.core.output_naming import build_pdf_filename
from app.core.document_batch import select_document_batches
from app.ui.range_slider import RangeSlider
from app.db.database import WordRepository


class GenerateWorker(QObject):
    progress = Signal(int, str)
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, documents, outputs, cfg, font_path, exporter: PdfExporter):
        super().__init__()
        self.documents = documents
        self.outputs = outputs
        self.cfg = cfg
        self.font_path = font_path
        self.exporter = exporter

    @Slot()
    def run(self):
        try:
            total_documents = len(self.documents)
            for document_index, (words_by_page, output) in enumerate(zip(self.documents, self.outputs)):
                def update(current, total):
                    local = current / max(total, 1)
                    percent = int((document_index + local) * 100 / max(total_documents, 1))
                    self.progress.emit(percent, f"กำลังสร้างชุดที่ {document_index + 1}/{total_documents} คำ {current}/{total}")
                self.exporter.export(words_by_page, output, self.cfg, self.font_path, progress=update)
            self.done.emit("\n".join(str(path) for path in self.outputs))
        except Exception as exc:
            if isinstance(exc, ValueError) and "ไม่สามารถจัดวาง" in str(exc):
                self.failed.emit(str(exc))
            else:
                self.failed.emit(traceback.format_exc())


class ImportAuditWorker(QObject):
    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, sources, review_registry_path: Path, audit_report_path: Path):
        super().__init__()
        self.sources = sources
        self.review_registry_path = review_registry_path
        self.audit_report_path = audit_report_path

    @Slot()
    def run(self):
        try:
            def update(done: int, total: int, message: str):
                percent = int(done * 90 / max(total, 1))
                self.progress.emit(max(5, percent), message)

            self.progress.emit(3, "กำลังเริ่มตรวจ source คำศัพท์")
            audit = audit_word_sources(self.sources, self.review_registry_path, progress=update)
            self.progress.emit(95, "กำลังบันทึกรายงาน audit")
            write_audit_report(self.audit_report_path, audit)
            self.progress.emit(100, "ตรวจ source เสร็จแล้ว")
            self.done.emit(audit)
        except Exception:
            self.failed.emit(traceback.format_exc())


class WordImportWorker(QObject):
    progress = Signal(int, str)
    done = Signal(int, str)
    failed = Signal(str)

    def __init__(self, audit, repository: WordStore, clear_before_import: bool, import_report_path: Path):
        super().__init__()
        self.audit = audit
        self.repository = repository
        self.clear_before_import = clear_before_import
        self.import_report_path = import_report_path

    @Slot()
    def run(self):
        try:
            if self.audit.import_report is None:
                raise ValueError("ไม่พบรายงานตรวจรับสำหรับนำเข้าคำ")
            self.progress.emit(10, "กำลังเตรียมนำคำเข้า database")
            if self.clear_before_import:
                self.progress.emit(35, "กำลังล้างคลังคำเดิมและนำเข้าชุดใหม่")
                count = self.repository.replace_words(self.audit.rows)
                action = "อัปเดต"
            else:
                self.progress.emit(35, "กำลังเพิ่มคำเข้า database")
                count = self.repository.add_words(self.audit.rows)
                action = "เพิ่ม"
            self.progress.emit(85, "กำลังบันทึกรายงาน import")
            write_import_report(self.import_report_path, self.audit.import_report)
            self.progress.emit(100, "นำเข้าคำเสร็จแล้ว")
            self.done.emit(count, action)
        except Exception:
            self.failed.emit(traceback.format_exc())


class ClearWordsWorker(QObject):
    progress = Signal(int, str)
    done = Signal()
    failed = Signal(str)

    def __init__(self, repository: WordStore):
        super().__init__()
        self.repository = repository

    @Slot()
    def run(self):
        try:
            self.progress.emit(35, "กำลังล้างข้อมูลคำในฐานข้อมูล")
            self.repository.clear_all()
            self.progress.emit(100, "ล้างข้อมูลคำเสร็จแล้ว")
            self.done.emit()
        except Exception:
            self.failed.emit(traceback.format_exc())


class MainWindow(QMainWindow):
    def __init__(self, root: Path, repository: WordStore | None = None, extractor: WordExtractor | None = None, exporter: PdfExporter | None = None):
        super().__init__()
        self.root = root
        self.config_path = root / "config.toml"
        self.cfg = AppConfig.load(self.config_path)
        self.repo = repository or WordRepository(self.cfg.resolve(self.cfg.database))
        self.extractor = extractor or TableWordSourceExtractor()
        self.exporter = exporter or ReportLabPdfExporter()
        self.setWindowTitle("MT Choose Words — สร้าง PDF คำศัพท์")
        self.resize(920, 680)
        self._build_ui()
        self._load_fonts()
        self._refresh_word_status()

    def _spin(self, value, minimum, maximum):
        box = QSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        box.setLocale(QLocale.c())
        return box

    def _slider(self, value, minimum, maximum, suffix=""):
        """Create a slider with an editable Arabic-number input."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        slider = QSlider()
        slider.setOrientation(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        number_input = QSpinBox()
        number_input.setRange(minimum, maximum)
        number_input.setValue(value)
        number_input.setLocale(QLocale.c())
        number_input.setSuffix(suffix)
        number_input.setFixedWidth(82)
        slider.valueChanged.connect(number_input.setValue)
        number_input.valueChanged.connect(slider.setValue)
        row.addWidget(slider, 1)
        row.addWidget(number_input)
        container.slider = slider
        container.number_input = number_input
        return container

    def _range(self, lower, upper, minimum, maximum, suffix=""):
        """Create one two-handle slider for a Min–Max setting."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        slider = RangeSlider(minimum, maximum, lower, upper)
        values = QLabel()
        values.setMinimumWidth(92)
        values.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def update_values(*_):
            low, high = slider.values()
            values.setText(f"{low}{suffix} – {high}{suffix}")

        slider.lowerValueChanged.connect(update_values)
        slider.upperValueChanged.connect(update_values)
        update_values()
        row.addWidget(slider, 1)
        row.addWidget(values)
        container.range_slider = slider
        return container

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)
        heading = QLabel("สร้าง PDF คำศัพท์แบบกระจายอย่างมีศิลปะ")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        # All user-adjustable bounded quantities use sliders for fast visual tuning.
        self.pages = self._slider(self.cfg.pages, 1, 100, " หน้า")
        self.words = self._slider(self.cfg.words_per_page, 1, 1000, " คำ")
        self.document_sets = self._slider(self.cfg.document_sets, 1, 20, " ชุด")
        self.font_range = self._range(self.cfg.font_min_pt, self.cfg.font_max_pt, 10, 100, " pt")
        self.rotation_range = self._range(self.cfg.rotation_min, self.cfg.rotation_max, -45, 45, "°")
        self.title_size = self._slider(self.cfg.title_font_size, 10, 100, " pt")
        self.title_margin = self._slider(self.cfg.title_margin_top_px, 0, 100, " px")
        self.title_margin_bottom = self._slider(self.cfg.title_margin_bottom_px, 0, 150, " px")
        self.title_padding = self._slider(self.cfg.title_padding_px, 0, 50, " px")
        self.seed = self._spin(self.cfg.seed, 0, 2_147_483_647)
        self.title = QLineEdit(self.cfg.title)
        self.title_color = QLineEdit(self.cfg.title_color)
        self.title_bgcolor = QLineEdit(self.cfg.title_bgcolor)
        self.source_files = QLineEdit(self._source_summary())
        self.source_files.setReadOnly(True)
        self.source_picker = QPushButton("เลือกไฟล์")
        source_row = QWidget()
        source_layout = QHBoxLayout(source_row)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addWidget(self.source_files, 1)
        source_layout.addWidget(self.source_picker)
        self.orientation = QWidget()
        orientation_row = QHBoxLayout(self.orientation)
        orientation_row.setContentsMargins(0, 0, 0, 0)
        self.portrait = QRadioButton("แนวตั้ง")
        self.landscape = QRadioButton("แนวนอน")
        (self.portrait if self.cfg.orientation == "portrait" else self.landscape).setChecked(True)
        orientation_row.addWidget(self.portrait)
        orientation_row.addWidget(self.landscape)
        orientation_row.addStretch()
        self.grade_checks: dict[int, QCheckBox] = {}
        self.grade_selector = QWidget()
        grade_row = QHBoxLayout(self.grade_selector)
        grade_row.setContentsMargins(0, 0, 0, 0)
        for grade in range(1, 7):
            checkbox = QCheckBox(f"ป.{grade}")
            checkbox.setChecked(grade in self.cfg.selected_grades)
            self.grade_checks[grade] = checkbox
            grade_row.addWidget(checkbox)
        grade_row.addStretch()
        self.fonts = QComboBox()

        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        import_box = QGroupBox("ขั้นตอนที่ 1: นำเข้าคลังคำ (DOCX/TXT)")
        import_form = QGridLayout(import_box)
        import_fields = [("ไฟล์คำศัพท์", source_row)]
        for i, (label, widget) in enumerate(import_fields):
            import_form.addWidget(QLabel(label), i, 0)
            import_form.addWidget(widget, i, 1)
        self.clear_words_button = QPushButton("ล้างข้อมูลคำในฐานข้อมูล")
        self.import_words_button = QPushButton("นำเข้ารายการคำ")
        import_buttons = QHBoxLayout()
        import_buttons.addStretch()
        import_buttons.addWidget(self.clear_words_button)
        import_buttons.addWidget(self.import_words_button)
        import_layout.addWidget(import_box)
        import_layout.addLayout(import_buttons)
        import_layout.addStretch()
        tabs.addTab(import_tab, "1 นำเข้าข้อมูล")

        worksheet_tab = QWidget()
        worksheet_layout = QVBoxLayout(worksheet_tab)
        worksheet_box = QGroupBox("ขั้นตอนที่ 2: สร้างไฟล์ใบงาน")
        worksheet_form = QGridLayout(worksheet_box)
        worksheet_fields = [("จำนวนชุดเอกสาร", self.document_sets), ("จำนวนหน้า/ชุด", self.pages), ("จำนวนคำต่อหน้า", self.words), ("ระดับชั้น", self.grade_selector), ("ฟอนท์", self.fonts), ("การวางกระดาษ", self.orientation), ("ช่วงขนาดฟอนท์ (pt)", self.font_range), ("ช่วงองศาหมุน", self.rotation_range), ("ข้อความ Title", self.title), ("ขนาด Title (pt)", self.title_size), ("สีตัวอักษร Title", self.title_color), ("สีพื้น Title", self.title_bgcolor), ("ระยะห่างบน (px)", self.title_margin), ("ระยะห่างล่าง (px)", self.title_margin_bottom), ("Padding Title (px)", self.title_padding), ("Seed (0 = สุ่มใหม่)", self.seed)]
        for i, (label, widget) in enumerate(worksheet_fields):
            worksheet_form.addWidget(QLabel(label), i // 2, (i % 2) * 2)
            worksheet_form.addWidget(widget, i // 2, (i % 2) * 2 + 1)
        self.save = QPushButton("บันทึกการตั้งค่า")
        self.output = QPushButton("เลือกโฟลเดอร์ผลลัพธ์")
        self.generate = QPushButton("สร้าง PDF")
        worksheet_buttons = QHBoxLayout()
        worksheet_buttons.addStretch()
        for b in (self.save, self.output, self.generate):
            worksheet_buttons.addWidget(b)
        worksheet_layout.addWidget(worksheet_box)
        worksheet_layout.addLayout(worksheet_buttons)
        worksheet_layout.addStretch()
        tabs.addTab(worksheet_tab, "2 สร้างใบงาน")

        self.info = QLabel()
        layout.addWidget(self.info)
        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.clear_words_button.clicked.connect(self._clear_words)
        self.import_words_button.clicked.connect(self._import_words)
        self.source_picker.clicked.connect(self._choose_sources)
        self.save.clicked.connect(self._save_config)
        self.output.clicked.connect(self._choose_output)
        self.generate.clicked.connect(self._generate)
        self.setStyleSheet("QLabel#heading { font-size: 22px; font-weight: 700; padding: 8px; } QGroupBox { font-weight: 600; margin-top: 10px; } QPushButton { padding: 8px 14px; }")

    def _load_fonts(self):
        self.fonts.clear()
        for path in sorted(self.cfg.resolve(self.cfg.fonts_dir).glob("*")):
            if path.suffix.lower() in {".ttf", ".otf", ".ttc"}:
                self.fonts.addItem(path.name, str(path))
        if self.fonts.count() == 0:
            self.info.setText("ยังไม่พบฟอนท์ใน app/assets/fonts")

    def _source_summary(self) -> str:
        if not self.cfg.word_source_files:
            return f"ทั้งโฟลเดอร์: {self.cfg.words_dir}"
        names = [Path(value).name for value in self.cfg.word_source_files]
        return ", ".join(names[:3]) + (f" และอีก {len(names) - 3} ไฟล์" if len(names) > 3 else "")

    def _selected_word_sources(self) -> Path | list[Path]:
        if self.cfg.word_source_files:
            return [self.cfg.resolve(value) for value in self.cfg.word_source_files]
        return self.cfg.resolve(self.cfg.words_dir)

    def _review_registry_path(self) -> Path:
        return self.root / "app/assets/words/reviewed_suspicions.json"

    def _audit_report_path(self) -> Path:
        return self.root / "app/doc/evidence/word_source_audit_report.json"

    def _import_report_path(self) -> Path:
        return self.root / "app/doc/evidence/word_import_report.json"

    def _choose_sources(self):
        start = str(self.cfg.resolve(self.cfg.words_dir))
        paths, _ = QFileDialog.getOpenFileNames(self, "เลือกไฟล์คำศัพท์", start, "Word/Text (*.docx *.txt)")
        if paths:
            self.cfg.word_source_files = paths
            self.source_files.setText(self._source_summary())

    def _refresh_word_status(self):
        try:
            if hasattr(self.repo, "count_by_grade"):
                by_grade = self.repo.count_by_grade()
                details = " | ".join(f"ป.{grade}: {by_grade.get(f'ป.{grade}', 0)}" for grade in range(1, 7))
                self.info.setText(f"คลังคำปัจจุบัน ({details})")
            else:
                self.info.setText(f"คลังคำปัจจุบัน: {self.repo.count()} คำ")
        except Exception:
            self.info.setText("ยังอ่านจำนวนคำในคลังไม่ได้")

    def _preview_message(self, total_cells: int, unique_words: int, source_count: int) -> str:
        return (
            "ตรวจ source ผ่านแล้ว\n\n"
            f"ไฟล์ที่เลือก: {source_count} ไฟล์\n"
            f"จำนวน cell คำที่อ่านได้: {total_cells}\n"
            f"จำนวนคำไม่ซ้ำที่จะใช้ได้: {unique_words}\n"
            "โหมด: นำเข้า/เพิ่มคำ โดยไม่ล้างข้อมูลเดิม\n\n"
            "ถ้าต้องการเริ่มฐานข้อมูลใหม่ ให้กดปุ่ม 'ล้างข้อมูลคำในฐานข้อมูล' ก่อน\n\n"
            "ยืนยันให้นำคำชุดนี้เข้า database หรือไม่?"
        )

    def _blocked_files_message(self, audit) -> str:
        lines = [audit.blocking_message(), "", "ยังไม่นำคำเข้า database เพราะมี source ที่ต้องแก้หรือตรวจรับ:"]
        for item in audit.files[:8]:
            if item.status != "PASS":
                name = Path(item.source_file).name
                detail = item.error or f"พบรายการต้อง review {len(item.unresolved_suspicions)} จุด"
                lines.append(f"- {name}: {item.status} ({detail})")
        if len(audit.files) > 8:
            lines.append("- ...")
        lines.append("")
        lines.append("ดูรายละเอียดได้ที่ app/doc/evidence/word_source_audit_report.json")
        return "\n".join(lines)

    def _import_words(self):
        self._set_import_busy(True, "กำลังตรวจ source คำศัพท์ กรุณารอสักครู่...")
        self.import_audit_thread = QThread()
        self.import_audit_worker = ImportAuditWorker(
            self._selected_word_sources(),
            self._review_registry_path(),
            self._audit_report_path(),
        )
        self.import_audit_worker.moveToThread(self.import_audit_thread)
        self.import_audit_thread.started.connect(self.import_audit_worker.run)
        self.import_audit_worker.progress.connect(self._on_progress)
        self.import_audit_worker.done.connect(self._audit_finished)
        self.import_audit_worker.failed.connect(self._import_failed)
        self.import_audit_worker.done.connect(self.import_audit_thread.quit)
        self.import_audit_worker.failed.connect(self.import_audit_thread.quit)
        self.import_audit_thread.finished.connect(self.import_audit_worker.deleteLater)
        self.import_audit_thread.finished.connect(self.import_audit_thread.deleteLater)
        self.import_audit_thread.start()

    def _set_import_busy(self, busy: bool, message: str = ""):
        self.import_words_button.setEnabled(not busy)
        self.clear_words_button.setEnabled(not busy)
        self.source_picker.setEnabled(not busy)
        self.save.setEnabled(not busy)
        self.output.setEnabled(not busy)
        self.generate.setEnabled(not busy)
        self.progress.setRange(0, 100)
        self.progress.setValue(0 if busy else self.progress.value())
        if message:
            self.status.showMessage(message)

    def _audit_finished(self, audit):
        self.progress.setValue(100)
        if not audit.can_import or audit.import_report is None:
            self._set_import_busy(False)
            QMessageBox.warning(self, "ยัง Reload ไม่ได้", self._blocked_files_message(audit))
            self.status.showMessage("นำเข้าถูกหยุดเพื่อรอตรวจรับ source")
            return

        answer = QMessageBox.question(
            self,
            "ยืนยันนำเข้ารายการคำ",
            self._preview_message(audit.summary.total_cells, audit.summary.unique_words, audit.source_count),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self._set_import_busy(False)
            self.status.showMessage("ยกเลิกนำเข้ารายการคำ")
            return
        self._start_word_import(audit)

    def _start_word_import(self, audit):
        self.progress.setValue(0)
        self.status.showMessage("กำลังนำคำเข้า database...")
        self.word_import_thread = QThread()
        self.word_import_worker = WordImportWorker(audit, self.repo, False, self._import_report_path())
        self.word_import_worker.moveToThread(self.word_import_thread)
        self.word_import_thread.started.connect(self.word_import_worker.run)
        self.word_import_worker.progress.connect(self._on_progress)
        self.word_import_worker.done.connect(self._word_import_finished)
        self.word_import_worker.failed.connect(self._import_failed)
        self.word_import_worker.done.connect(self.word_import_thread.quit)
        self.word_import_worker.failed.connect(self.word_import_thread.quit)
        self.word_import_thread.finished.connect(self.word_import_worker.deleteLater)
        self.word_import_thread.finished.connect(self.word_import_thread.deleteLater)
        self.word_import_thread.start()

    def _word_import_finished(self, count: int, action: str):
        self._set_import_busy(False)
        self.progress.setValue(100)
        if hasattr(self.repo, "count_by_grade"):
            by_grade = self.repo.count_by_grade()
            details = " | ".join(f"ป.{grade}: {by_grade.get(f'ป.{grade}', 0)}" for grade in range(1, 7))
            self.info.setText(f"{action}คำสำเร็จ: {count} คำ ({details})")
        else:
            self.info.setText(f"{action}คำสำเร็จ: {count} คำ")
        self.status.showMessage("อัปเดตคลังคำสำเร็จ")

    def _import_failed(self, details: str):
        self._set_import_busy(False)
        self.status.showMessage("งานนำเข้า/ล้างข้อมูลไม่สำเร็จ")
        QMessageBox.critical(self, "งานนำเข้า/ล้างข้อมูลไม่สำเร็จ", details)

    def _clear_words(self):
        answer = QMessageBox.question(
            self,
            "ยืนยันล้างข้อมูลคำ",
            "ต้องการล้างข้อมูลคำทั้งหมดในฐานข้อมูลหรือไม่?\n\nการล้างข้อมูลจะไม่ลบไฟล์ source DOCX/TXT และสามารถนำเข้ารายการคำใหม่ได้ภายหลัง",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.status.showMessage("ยกเลิกการล้างข้อมูลคำ")
            return
        self._set_import_busy(True, "กำลังล้างข้อมูลคำในฐานข้อมูล...")
        self.clear_words_thread = QThread()
        self.clear_words_worker = ClearWordsWorker(self.repo)
        self.clear_words_worker.moveToThread(self.clear_words_thread)
        self.clear_words_thread.started.connect(self.clear_words_worker.run)
        self.clear_words_worker.progress.connect(self._on_progress)
        self.clear_words_worker.done.connect(self._clear_words_finished)
        self.clear_words_worker.failed.connect(self._import_failed)
        self.clear_words_worker.done.connect(self.clear_words_thread.quit)
        self.clear_words_worker.failed.connect(self.clear_words_thread.quit)
        self.clear_words_thread.finished.connect(self.clear_words_worker.deleteLater)
        self.clear_words_thread.finished.connect(self.clear_words_thread.deleteLater)
        self.clear_words_thread.start()

    def _clear_words_finished(self):
        self._set_import_busy(False)
        self.progress.setValue(100)
        self._refresh_word_status()
        self.status.showMessage("ล้างข้อมูลคำในฐานข้อมูลสำเร็จ")

    def _selected_grades(self) -> list[int]:
        return [grade for grade, checkbox in self.grade_checks.items() if checkbox.isChecked()]

    def _save_config(self):
        self.cfg.pages = self.pages.slider.value(); self.cfg.words_per_page = self.words.slider.value(); self.cfg.document_sets = self.document_sets.slider.value()
        self.cfg.font_min_pt, self.cfg.font_max_pt = self.font_range.range_slider.values()
        self.cfg.rotation_min, self.cfg.rotation_max = self.rotation_range.range_slider.values()
        self.cfg.title = self.title.text(); self.cfg.title_font_size = self.title_size.slider.value(); self.cfg.title_color = self.title_color.text(); self.cfg.title_bgcolor = self.title_bgcolor.text(); self.cfg.title_margin_top_px = self.title_margin.slider.value(); self.cfg.title_margin_bottom_px = self.title_margin_bottom.slider.value(); self.cfg.title_padding_px = self.title_padding.slider.value(); self.cfg.seed = self.seed.value()
        self.cfg.orientation = "portrait" if self.portrait.isChecked() else "landscape"
        self.cfg.selected_grades = self._selected_grades()
        self.cfg.save(self.config_path)
        self.status.showMessage("บันทึกการตั้งค่าแล้ว")

    def _choose_output(self):
        value = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์ผลลัพธ์", str(self.cfg.resolve(self.cfg.output_dir)))
        if value: self.cfg.output_dir = value

    def _generate(self):
        if not self.fonts.currentData():
            QMessageBox.warning(self, "ยังไม่มีฟอนท์", "กรุณาใส่ฟอนท์ใน app/assets/fonts ก่อนสร้าง PDF")
            return
        document_sets = self.document_sets.slider.value()
        pages_per_set = self.pages.slider.value()
        words_per_page = self.words.slider.value()
        words_per_document = pages_per_set * words_per_page
        selected_grades = self._selected_grades()
        if not selected_grades:
            QMessageBox.warning(self, "ยังไม่ได้เลือกระดับชั้น", "กรุณาเลือกอย่างน้อย 1 ระดับชั้น")
            return
        available = self.repo.count(selected_grades)
        if words_per_document > available:
            grade_text = ", ".join(f"ป.{grade}" for grade in selected_grades)
            QMessageBox.warning(self, "จำนวนคำไม่เพียงพอ", f"ต้องการ {words_per_document} คำต่อไฟล์จาก {grade_text} แต่มีคำไม่ซ้ำ {available} คำ")
            return
        self._save_config()
        import random
        rng = random.Random(self.cfg.seed or None)
        documents = select_document_batches(self.repo, document_sets, pages_per_set, words_per_page, rng, selected_grades)
        outputs = [self.cfg.resolve(self.cfg.output_dir) / build_pdf_filename(words_per_page, set_number=index)
                   for index in range(1, document_sets + 1)]
        self.generate.setEnabled(False); self.progress.setValue(0)
        self.status.showMessage("กำลังสร้าง PDF และจัดวางคำ กรุณารอสักครู่...")
        self.thread = QThread()
        self.worker = GenerateWorker(documents, outputs, self.cfg, Path(self.fonts.currentData()), self.exporter)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._finished)
        self.worker.failed.connect(self._failed)
        self.worker.done.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_progress(self, percent: int, message: str):
        self.progress.setValue(percent)
        self.status.showMessage(message)

    def _finished(self, path):
        self.generate.setEnabled(True)
        self.progress.setValue(100)
        self.status.showMessage("สร้าง PDF สำเร็จ")
        # Show modal UI only after the worker thread has fully stopped.
        self.thread.finished.connect(lambda: QMessageBox.information(self, "สำเร็จ", f"สร้างไฟล์แล้ว:\n{path}"))

    def _failed(self, details):
        self.generate.setEnabled(True)
        self.status.showMessage("สร้าง PDF ไม่สำเร็จ")
        self.thread.finished.connect(lambda: QMessageBox.critical(self, "สร้าง PDF ไม่สำเร็จ", details))
