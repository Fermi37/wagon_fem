from __future__ import annotations

from .builder import FrameBuilder
from .grid import pitch_coordinates, unique_sorted
from .passenger_common import (
    PASSENGER_DOUBLE_DECK_TAGS,
    add_line,
    add_segment,
    apply_passenger_supports,
    build_metadata,
    double_deck_y_lines,
    load_for,
    passenger_x_lines,
    section,
    validate_passenger_frame,
    z_floor_lines,
)
from .passenger_single_deck import _add_end_walls, _add_roof, _add_side_walls
from .schemas import GeneratedFrame, WagonParams


def _main_floor_y(params: WagonParams) -> float:
    return params.levels.main_floor_y if params.levels.main_floor_y is not None else params.geometry.floor_y


def _lower_floor_y(params: WagonParams) -> float:
    if params.levels.lower_floor_y is not None:
        return params.levels.lower_floor_y
    if params.geometry.lowered_floor_y is not None:
        return params.geometry.lowered_floor_y
    return _main_floor_y(params)


def _interdeck_y(params: WagonParams) -> float:
    if params.levels.interdeck_floor_y is not None:
        return params.levels.interdeck_floor_y
    return _main_floor_y(params) + 0.45 * params.geometry.side_height


def _inside_any(x_mid: float, intervals: tuple[object, ...]) -> bool:
    return any(getattr(zone, "x_start") <= x_mid <= getattr(zone, "x_end") for zone in intervals)


def _floor_y_for_station(params: WagonParams, x: float) -> float:
    if _inside_any(x, params.zones.lowered_floor):
        return _lower_floor_y(params)
    return _main_floor_y(params)


def _add_double_floor(builder: FrameBuilder, params: WagonParams, x_lines: list[float], z_lines: list[float]) -> None:
    g = params.geometry
    half = g.width / 2.0

    add_line(
        builder,
        [(x, _main_floor_y(params), 0.0) for x in x_lines],
        "center_sill",
        section(params, "center_sill"),
        **load_for(params, "center_sill"),
    )
    for z in (-half, half):
        add_line(
            builder,
            [(x, _floor_y_for_station(params, x), z) for x in x_lines],
            "side_sill",
            section(params, "side_sill"),
            **load_for(params, "side_sill"),
        )
    for z in z_lines:
        if abs(z) <= 1e-6 or abs(abs(z) - half) <= 1e-6:
            continue
        add_line(
            builder,
            [(x, _floor_y_for_station(params, x), z) for x in x_lines],
            "floor_longitudinal",
            section(params, "floor_longitudinal"),
            **load_for(params, "floor_longitudinal"),
        )

    cross_positions = set(pitch_coordinates(0.0, g.length, params.layout.cross_beam_pitch))
    cross_positions.update(g.bolster_positions)
    cross_positions.update([0.0, g.length])
    for zone in params.zones.lowered_floor:
        cross_positions.update([zone.x_start, zone.x_end])
    for zone in params.zones.stairwells:
        cross_positions.update([zone.x_start, zone.x_end])

    for x in unique_sorted(tuple(cross_positions)):
        if abs(x) <= 1e-6 or abs(x - g.length) <= 1e-6:
            tag = "end_beam"
        elif any(abs(x - b) <= 1e-6 for b in g.bolster_positions):
            tag = "bolster_beam"
        else:
            tag = "cross_beam"
        add_line(
            builder,
            [(x, _floor_y_for_station(params, x), z) for z in z_lines],
            tag,
            section(params, tag),
            **load_for(params, tag),
        )


def _add_interdeck(builder: FrameBuilder, params: WagonParams, x_lines: list[float], z_lines: list[float]) -> None:
    y = _interdeck_y(params)
    half = params.geometry.width / 2.0
    for z in z_lines:
        for x0, x1 in zip(x_lines, x_lines[1:]):
            mid_x = 0.5 * (x0 + x1)
            if abs(z) < half - 1e-6 and _inside_any(mid_x, params.zones.stairwells):
                continue
            add_segment(
                builder,
                (x0, y, z),
                (x1, y, z),
                "interdeck_longitudinal",
                section(params, "interdeck_longitudinal"),
                **load_for(params, "interdeck_longitudinal"),
            )

    cross_positions = set(pitch_coordinates(0.0, params.geometry.length, params.layout.cross_beam_pitch))
    cross_positions.update(params.geometry.bolster_positions)
    for zone in params.zones.stairwells:
        cross_positions.update([zone.x_start, zone.x_end])
    for x in unique_sorted(tuple(cross_positions)):
        add_line(
            builder,
            [(x, y, z) for z in z_lines],
            "interdeck_cross_beam",
            section(params, "interdeck_cross_beam"),
            **load_for(params, "interdeck_cross_beam"),
        )


def _add_stairwell_frames(builder: FrameBuilder, params: WagonParams, z_lines: list[float]) -> None:
    y0 = _main_floor_y(params)
    y1 = _interdeck_y(params)
    for zone in params.zones.stairwells:
        for x in (zone.x_start, zone.x_end):
            for z in z_lines:
                add_segment(builder, (x, y0, z), (x, y1, z), "opening_post", section(params, "opening_post"))


def build_passenger_double_deck(params: WagonParams) -> GeneratedFrame:
    builder = FrameBuilder(tolerance=params.generation.coordinate_tolerance)
    x_lines = passenger_x_lines(params)
    y_lines = double_deck_y_lines(params)
    z_lines = z_floor_lines(params)

    _add_double_floor(builder, params, x_lines, z_lines)
    _add_side_walls(builder, params, x_lines, y_lines)
    _add_interdeck(builder, params, x_lines, z_lines)
    _add_stairwell_frames(builder, params, z_lines)
    _add_end_walls(builder, params, y_lines, z_lines)
    _add_roof(builder, params, x_lines)
    apply_passenger_supports(builder, params)

    frame = builder.build(build_metadata(params, "passenger_double_deck", x_lines, y_lines, z_lines))
    validate_passenger_frame(frame, PASSENGER_DOUBLE_DECK_TAGS)
    return frame
