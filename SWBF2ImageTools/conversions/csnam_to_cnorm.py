from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QLabel, QWidget
from PIL import Image

from ..core.image_io import extract_channel, invert_l, open_rgba, resize_l, save_image
from ..models.config import GlobalConfig, JobBase
from .base import ConversionDefinition, DetectedInput

VALID_CHANNELS = ["R", "G", "B", "A"]


@dataclass(frozen=True)
class CsNamJob(JobBase):
    smooth_channel: str
    invert_smoothness_to_roughness: bool
    ao_channel: str
    metallic_channel: str
    drop_orm_alpha: bool


def _parse_prefix_and_suffix(path: Path) -> Optional[tuple[str, str]]:
    name = path.stem
    if name.endswith("_CS"):
        return name[:-3], "CS"
    if name.endswith("_NAM"):
        return name[:-4], "NAM"
    return None


def _build_pairs(folder: Path) -> list[tuple[str, Path, Path]]:
    by_prefix: dict[str, dict[str, Path]] = {}

    for p in folder.iterdir():
        if not p.is_file():
            continue
        parsed = _parse_prefix_and_suffix(p)
        if not parsed:
            continue
        prefix, suffix = parsed
        by_prefix.setdefault(prefix, {})[suffix] = p

    pairs: list[tuple[str, Path, Path]] = []
    for prefix, found in sorted(by_prefix.items(), key=lambda kv: kv[0].lower()):
        cs = found.get("CS")
        nam = found.get("NAM")
        if cs and nam:
            pairs.append((prefix, cs, nam))
    return pairs


def _process_pair(prefix: str, cs_path: Path, nam_path: Path, cfg: CsNamJob) -> None:
    g = cfg.global_cfg

    cs_rgba = open_rgba(cs_path)
    nam_rgba = open_rgba(nam_path)

    cs_w, cs_h = cs_rgba.size
    nam_w, nam_h = nam_rgba.size

    out_c = cfg.output_folder / f"{prefix}_C.{g.out_ext}"
    out_n = cfg.output_folder / f"{prefix}_N.{g.out_ext}"
    out_orm = cfg.output_folder / f"{prefix}_ORM.{g.out_ext}"

    # _C
    save_image(cs_rgba.convert("RGB"), out_c, g)

    # _N
    save_image(nam_rgba.convert("RGB"), out_n, g)

    # _ORM
    ao = extract_channel(nam_rgba, cfg.ao_channel)
    metal = extract_channel(nam_rgba, cfg.metallic_channel)
    smooth = extract_channel(cs_rgba, cfg.smooth_channel)

    if (cs_w, cs_h) != (nam_w, nam_h):
        smooth = resize_l(smooth, (nam_w, nam_h))

    rough = invert_l(smooth) if cfg.invert_smoothness_to_roughness else smooth
    orm_rgb = Image.merge("RGB", (ao, rough, metal))

    if cfg.drop_orm_alpha:
        save_image(orm_rgb, out_orm, g)
    else:
        alpha = Image.new("L", (nam_w, nam_h), 255)
        r, gg, b = orm_rgb.split()
        orm_rgba = Image.merge("RGBA", (r, gg, b, alpha))
        save_image(orm_rgba, out_orm, g)


class CsNamToCnormConversion(ConversionDefinition):
    id = "csnam_to_cnorm"
    display_name = "CS/NAM → C/N/ORM"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._smooth_combo: Optional[QComboBox] = None
        self._ao_combo: Optional[QComboBox] = None
        self._metal_combo: Optional[QComboBox] = None
        self._invert_cb: Optional[QCheckBox] = None
        self._drop_alpha_cb: Optional[QCheckBox] = None

    def build_settings_widget(self) -> QWidget:
        if self._widget is not None:
            return self._widget

        w = QWidget()
        grid = QGridLayout()

        self._smooth_combo = QComboBox()
        self._smooth_combo.addItems(VALID_CHANNELS)
        self._smooth_combo.setCurrentText("A")

        self._ao_combo = QComboBox()
        self._ao_combo.addItems(VALID_CHANNELS)
        self._ao_combo.setCurrentText("A")

        self._metal_combo = QComboBox()
        self._metal_combo.addItems(VALID_CHANNELS)
        self._metal_combo.setCurrentText("B")

        self._invert_cb = QCheckBox("Invert smoothness → roughness")
        self._invert_cb.setChecked(True)

        self._drop_alpha_cb = QCheckBox("Drop alpha channel from _ORM output")
        self._drop_alpha_cb.setChecked(True)

        grid.addWidget(QLabel("Smoothness channel in *_CS:"), 0, 0)
        grid.addWidget(self._smooth_combo, 0, 1)

        grid.addWidget(QLabel("AO channel in *_NAM:"), 1, 0)
        grid.addWidget(self._ao_combo, 1, 1)

        grid.addWidget(QLabel("Metallic channel in *_NAM:"), 2, 0)
        grid.addWidget(self._metal_combo, 2, 1)

        grid.addWidget(self._invert_cb, 3, 0, 1, 2)
        grid.addWidget(self._drop_alpha_cb, 4, 0, 1, 2)

        w.setLayout(grid)
        self._widget = w
        return w

    def set_settings_enabled(self, enabled: bool) -> None:
        if self._widget is not None:
            self._widget.setEnabled(enabled)

    def detect_inputs(self, input_folder: Path) -> list[DetectedInput]:
        pairs = _build_pairs(input_folder)
        return [
            DetectedInput(
                key=prefix,
                display_line=f"{prefix}: (_CS and _NAM found)",
                payload=(cs_path, nam_path),
            )
            for prefix, cs_path, nam_path in pairs
        ]

    def make_job_config(self, input_folder: Path, output_folder: Path, global_cfg: GlobalConfig) -> CsNamJob:
        assert self._smooth_combo and self._ao_combo and self._metal_combo and self._invert_cb and self._drop_alpha_cb

        return CsNamJob(
            conversion_id=self.id,
            input_folder=input_folder,
            output_folder=output_folder,
            global_cfg=global_cfg,
            smooth_channel=self._smooth_combo.currentText(),
            invert_smoothness_to_roughness=self._invert_cb.isChecked(),
            ao_channel=self._ao_combo.currentText(),
            metallic_channel=self._metal_combo.currentText(),
            drop_orm_alpha=self._drop_alpha_cb.isChecked(),
        )

    def run(
        self,
        detected: Sequence[DetectedInput],
        cfg: Any,
        progress_cb: Callable[[int, int], None],
        status_cb: Callable[[str], None],
    ) -> None:
        job: CsNamJob = cfg  # type: ignore[assignment]
        total = len(detected)
        if total == 0:
            return

        for i, item in enumerate(detected, start=1):
            prefix = item.key
            cs_path, nam_path = item.payload
            status_cb(f"Processing: {prefix}")
            _process_pair(prefix, cs_path, nam_path, job)
            progress_cb(i, total)

        status_cb("Done.")
