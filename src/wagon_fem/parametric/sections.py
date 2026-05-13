from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SectionProperties:
    E: float
    A: float
    Iy: float
    Iz: float
    J: float


FIRST_STAGE_CATALOG: dict[str, SectionProperties] = {
    "center_sill_heavy": SectionProperties(210000.0, 18000.0, 2.20e8, 4.50e8, 1.50e7),
    "bolster_beam_heavy": SectionProperties(210000.0, 16000.0, 1.80e8, 3.20e8, 1.20e7),
    "end_beam_medium": SectionProperties(210000.0, 12000.0, 9.00e7, 1.80e8, 8.00e6),
    "side_longitudinal_medium": SectionProperties(210000.0, 11000.0, 8.00e7, 1.60e8, 7.00e6),
    "cross_beam_medium": SectionProperties(210000.0, 9000.0, 6.00e7, 1.20e8, 5.00e6),
    "floor_longitudinal_light": SectionProperties(210000.0, 6500.0, 3.00e7, 7.00e7, 2.50e6),
    "side_post_light": SectionProperties(210000.0, 5000.0, 2.50e7, 5.00e7, 1.50e6),
    "end_post_light": SectionProperties(210000.0, 5000.0, 2.50e7, 5.00e7, 1.50e6),
    "upper_belt_light": SectionProperties(210000.0, 6000.0, 3.50e7, 7.00e7, 2.00e6),
    "horizontal_belt_light": SectionProperties(210000.0, 4500.0, 2.00e7, 4.00e7, 1.20e6),
    "roof_bow_light": SectionProperties(210000.0, 4500.0, 2.00e7, 4.50e7, 1.00e6),
    "roof_longitudinal_light": SectionProperties(210000.0, 4000.0, 1.80e7, 3.50e7, 9.00e5),
    "diagonal_tie_equiv": SectionProperties(210000.0, 1800.0, 5.00e5, 5.00e5, 1.00e4),
    "rigid_offset_stub": SectionProperties(210000.0, 50000.0, 1.00e10, 1.00e10, 1.00e9),
}


def get_section(tag: str) -> SectionProperties:
    try:
        return FIRST_STAGE_CATALOG[tag]
    except KeyError as exc:
        raise KeyError(f"Unknown section tag: {tag}") from exc
