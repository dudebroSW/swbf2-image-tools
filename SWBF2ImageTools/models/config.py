from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GlobalConfig:
    out_ext: str  # "png" or "tga"
    tga_rle: bool


@dataclass(frozen=True)
class JobBase:
    conversion_id: str
    input_folder: Path
    output_folder: Path
    global_cfg: GlobalConfig
