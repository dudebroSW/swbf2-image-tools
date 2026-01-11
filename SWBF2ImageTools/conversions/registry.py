from __future__ import annotations

from .csnam_to_cnorm import CsNamToCnormConversion
from .base import ConversionDefinition


def get_conversions() -> list[ConversionDefinition]:
    # Add future conversions here.
    return [
        CsNamToCnormConversion(),
    ]
