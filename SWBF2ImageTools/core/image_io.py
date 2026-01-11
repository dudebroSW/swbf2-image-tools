from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image

from ..models.config import GlobalConfig


def open_rgba(path: Path) -> Image.Image:
    img = Image.open(path)
    img.load()
    return img.convert("RGBA")


def channel_index(ch: str) -> int:
    return {"R": 0, "G": 1, "B": 2, "A": 3}[ch]


def extract_channel(img_rgba: Image.Image, ch: str) -> Image.Image:
    return img_rgba.getchannel(channel_index(ch))  # "L"


def invert_l(img_l: Image.Image) -> Image.Image:
    if img_l.mode != "L":
        img_l = img_l.convert("L")
    return img_l.point(lambda v: 255 - v)


def resize_l(img_l: Image.Image, size_wh: Tuple[int, int]) -> Image.Image:
    if img_l.mode != "L":
        img_l = img_l.convert("L")
    return img_l.resize(size_wh, resample=Image.Resampling.LANCZOS)


def save_image(img: Image.Image, out_path: Path, global_cfg: GlobalConfig) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = global_cfg.out_ext.lower()

    if ext == "png":
        img.save(out_path, format="PNG", optimize=True)
        return
    if ext == "tga":
        img.save(out_path, format="TGA", compress=bool(global_cfg.tga_rle))
        return

    raise ValueError(f"Unsupported output format: {global_cfg.out_ext}")
