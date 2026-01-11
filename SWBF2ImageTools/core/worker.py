from __future__ import annotations

from typing import Any, Sequence

from PySide6.QtCore import QThread, Signal

from ..conversions.base import ConversionDefinition, DetectedInput


class SplitWorker(QThread):
    progress = Signal(int, int)
    status = Signal(str)
    error = Signal(str)
    finished_ok = Signal()

    def __init__(
        self,
        conversion: ConversionDefinition,
        detected: Sequence[DetectedInput],
        cfg: Any,
    ):
        super().__init__()
        self._conversion = conversion
        self._detected = list(detected)
        self._cfg = cfg

    def run(self) -> None:
        try:
            total = len(self._detected)
            if total == 0:
                self.error.emit("No valid inputs found for the selected conversion.")
                return

            def progress_cb(done: int, _total: int) -> None:
                self.progress.emit(done, total)

            def status_cb(msg: str) -> None:
                self.status.emit(msg)

            self._conversion.run(self._detected, self._cfg, progress_cb, status_cb)
            self.finished_ok.emit()

        except Exception as ex:
            self.error.emit(str(ex))
