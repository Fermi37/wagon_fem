from __future__ import annotations

from .open_wagon import _build_body
from .schemas import GeneratedFrame, WagonParams


def build_covered_wagon(params: WagonParams) -> GeneratedFrame:
    return _build_body(params, covered=True)
