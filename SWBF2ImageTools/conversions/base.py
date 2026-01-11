from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class DetectedInput:
    key: str
    display_line: str
    payload: Any


class ConversionDefinition(Protocol):
    id: str
    display_name: str

    def build_settings_widget(self) -> QWidget:
        ...

    def set_settings_enabled(self, enabled: bool) -> None:
        ...

    def detect_inputs(self, input_folder: Path) -> list[DetectedInput]:
        ...

    def make_job_config(self, input_folder: Path, output_folder: Path, global_cfg: Any) -> Any:
        ...

    def run(
        self,
        detected: Sequence[DetectedInput],
        cfg: Any,
        progress_cb: Callable[[int, int], None],
        status_cb: Callable[[str], None],
    ) -> None:
        ...
