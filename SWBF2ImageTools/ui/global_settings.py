from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QGroupBox, QLabel

from ..models.config import GlobalConfig


class GlobalSettingsWidget(QGroupBox):
    def __init__(self) -> None:
        super().__init__("Global Settings")

        grid = QGridLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "TGA"])
        self.format_combo.setCurrentText("PNG")
        self.format_combo.currentTextChanged.connect(self._on_format_changed)

        self.tga_rle_cb = QCheckBox("TGA RLE compression (lossless)")
        self.tga_rle_cb.setChecked(False)
        self.tga_rle_cb.setEnabled(False)

        grid.addWidget(QLabel("Output format:"), 0, 0)
        grid.addWidget(self.format_combo, 0, 1)
        grid.addWidget(self.tga_rle_cb, 1, 0, 1, 2)

        self.setLayout(grid)

    def _on_format_changed(self, fmt: str) -> None:
        is_tga = (fmt.upper() == "TGA")
        self.tga_rle_cb.setEnabled(is_tga)
        if not is_tga:
            self.tga_rle_cb.setChecked(False)

    def build_config(self) -> GlobalConfig:
        out_ext = self.format_combo.currentText().lower()
        tga_rle = self.tga_rle_cb.isChecked() if out_ext == "tga" else False
        return GlobalConfig(out_ext=out_ext, tga_rle=tga_rle)

    def set_enabled_for_processing(self, enabled: bool) -> None:
        self.setEnabled(enabled)
