from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from ..conversions.base import ConversionDefinition
from ..conversions.registry import get_conversions
from ..core.worker import SplitWorker
from .drop_list import DropList
from .global_settings import GlobalSettingsWidget

from SWBF2ImageTools import __version__

def app_version() -> str:
    return __version__


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"SWBF2 / Frosty Texture Image Tools v{app_version()} (by dudebroSW)")
        self.resize(940, 700)
        self.setAcceptDrops(True)

        self.input_folder: Optional[Path] = None
        self.output_folder: Optional[Path] = None

        self._worker: Optional[SplitWorker] = None

        self._conversions: list[ConversionDefinition] = get_conversions()
        self._conversion_by_name = {c.display_name: c for c in self._conversions}

        # --- Conversion ---
        self.conversion_combo = QComboBox()
        self.conversion_combo.addItems([c.display_name for c in self._conversions])
        self.conversion_combo.currentTextChanged.connect(self.on_conversion_changed)

        conversion_row = QHBoxLayout()
        conversion_row.addWidget(QLabel("Conversion:"))
        conversion_row.addWidget(self.conversion_combo, 1)

        # --- Input Folder ---
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Drop a folder here, or click Browse…")
        self.input_edit.setReadOnly(True)

        input_browse_btn = QPushButton("Browse…")
        input_browse_btn.clicked.connect(self.on_browse_input)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.on_refresh_clear)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Input folder:"))
        top_row.addWidget(self.input_edit, 1)
        top_row.addWidget(input_browse_btn)
        top_row.addWidget(clear_btn)

        # --- Output Folder ---
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Defaults to input folder")
        self.output_edit.setReadOnly(True)

        output_browse_btn = QPushButton("Browse…")
        output_browse_btn.clicked.connect(self.on_browse_output)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output folder:"))
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(output_browse_btn)

        # --- Drop list ---
        self.drop_list = DropList()
        self.drop_list.setToolTip("Drag & drop a folder or texture files here.")
        self.drop_list.dropped.connect(self.on_dropped)

        # --- Conversion settings ---
        self.settings_stack = QStackedWidget()
        for c in self._conversions:
            self.settings_stack.addWidget(c.build_settings_widget())

        settings_box = QGroupBox("Conversion Settings")
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.settings_stack)
        settings_box.setLayout(settings_layout)

        # --- Global settings ---
        self.global_settings = GlobalSettingsWidget()

        # --- Process + Progress ---
        self.process_btn = QPushButton("Process")
        self.process_btn.clicked.connect(self.on_process)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        self.status_label = QLabel("Drop a folder or files to begin.")
        self.status_label.setWordWrap(True)

        bottom = QHBoxLayout()
        bottom.addWidget(self.process_btn)
        bottom.addWidget(self.progress, 1)

        layout = QVBoxLayout()
        layout.addLayout(conversion_row)
        layout.addLayout(top_row)
        layout.addLayout(output_row)
        layout.addWidget(QLabel("Detected inputs (only valid for the selected conversion type):"))
        layout.addWidget(self.drop_list, 1)
        layout.addWidget(settings_box)          # conversion settings on top
        layout.addWidget(self.global_settings)  # global settings below
        layout.addLayout(bottom)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.on_conversion_changed(self.conversion_combo.currentText())

    # --- Window-level drag/drop ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if paths:
            self.on_dropped(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def current_conversion(self) -> ConversionDefinition:
        name = self.conversion_combo.currentText()
        return self._conversion_by_name[name]

    # --- handlers ---
    def on_conversion_changed(self, _text: str) -> None:
        conv = self.current_conversion()
        idx = [c.display_name for c in self._conversions].index(conv.display_name)
        self.settings_stack.setCurrentIndex(idx)
        self.refresh_detected_inputs()

    def on_browse_input(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select input folder")
        if folder:
            self.set_input_folder(Path(folder))

    def on_browse_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.set_output_folder(Path(folder))

    def on_refresh_clear(self) -> None:
        self.input_folder = None
        self.output_folder = None
        self.input_edit.clear()
        self.output_edit.clear()
        self.drop_list.clear()
        self.progress.setValue(0)
        self.status_label.setText("Cleared. Drop a folder or files to begin.")

    def on_dropped(self, paths: list) -> None:
        dropped_paths = [Path(p) for p in paths]
        folders = [p for p in dropped_paths if p.exists() and p.is_dir()]
        if folders:
            self.set_input_folder(folders[0])
            return

        files = [p for p in dropped_paths if p.exists() and p.is_file()]
        if not files:
            return

        self.set_input_folder(files[0].parent)

    def set_input_folder(self, folder: Path) -> None:
        self.input_folder = folder
        self.input_edit.setText(str(folder))

        if self.output_folder is None:
            self.set_output_folder(folder, refresh=False)
        else:
            self.output_edit.setText(str(self.output_folder))

        self.refresh_detected_inputs()

    def set_output_folder(self, folder: Path, refresh: bool = False) -> None:
        self.output_folder = folder
        self.output_edit.setText(str(folder))
        if refresh:
            self.refresh_detected_inputs()

    def refresh_detected_inputs(self) -> None:
        self.drop_list.clear()

        if not self.input_folder or not self.input_folder.exists():
            self.status_label.setText("No input folder selected.")
            return

        conv = self.current_conversion()
        detected = conv.detect_inputs(self.input_folder)

        if not detected:
            item = QListWidgetItem("No valid inputs found for the selected conversion type.")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.drop_list.addItem(item)
            self.status_label.setText("Ready. No valid inputs for this conversion.")
            return

        for item in detected:
            self.drop_list.addItem(item.display_line)

        out_text = str(self.output_folder) if self.output_folder else "(not set)"
        self.status_label.setText(f"Ready. Detected {len(detected)} valid inputs. Output → {out_text}")

    def set_busy(self, busy: bool) -> None:
        self.process_btn.setEnabled(not busy)
        self.drop_list.setEnabled(not busy)
        self.conversion_combo.setEnabled(not busy)

        self.global_settings.set_enabled_for_processing(not busy)
        self.current_conversion().set_settings_enabled(not busy)

        if busy:
            self.progress.setValue(0)

    def on_process(self) -> None:
        if not self.input_folder or not self.input_folder.exists():
            QMessageBox.warning(self, "No input folder", "Please select or drop an input folder containing textures.")
            return

        if not self.output_folder:
            self.output_folder = self.input_folder
            self.output_edit.setText(str(self.output_folder))

        if self.output_folder.exists() and not self.output_folder.is_dir():
            QMessageBox.warning(self, "Bad output folder", "Output path exists but is not a folder.")
            return

        conv = self.current_conversion()
        detected = conv.detect_inputs(self.input_folder)
        if not detected:
            QMessageBox.warning(self, "No inputs", "No valid inputs found for the selected conversion type.")
            return

        global_cfg = self.global_settings.build_config()
        cfg = conv.make_job_config(self.input_folder, self.output_folder, global_cfg)

        self.set_busy(True)
        self.status_label.setText("Starting...")

        self._worker = SplitWorker(conv, detected, cfg)
        self._worker.progress.connect(self.on_progress)
        self._worker.status.connect(self.on_status)
        self._worker.error.connect(self.on_error)
        self._worker.finished_ok.connect(self.on_done)
        self._worker.start()

    def on_progress(self, done: int, total: int) -> None:
        pct = int((done / total) * 100) if total else 0
        self.progress.setValue(pct)

    def on_status(self, msg: str) -> None:
        self.status_label.setText(msg)

    def on_error(self, msg: str) -> None:
        self.set_busy(False)
        self.status_label.setText("Error.")
        QMessageBox.critical(self, "Error", msg)

    def on_done(self) -> None:
        self.set_busy(False)
        self.progress.setValue(100)
        self.status_label.setText("Finished successfully.")
