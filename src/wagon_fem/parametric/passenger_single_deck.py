from __future__ import annotations

from .builder import FrameBuilder
from .grid import pitch_coordinates, unique_sorted
from .passenger_common import (
    PASSENGER_SINGLE_DECK_TAGS,
    add_line,
    add_segment,
    apply_passenger_supports,
    build_metadata,
    expanded_windows,
    is_opening_boundary,
    load_for,
    passenger_x_lines,
    section,
    side_opening_contains,
    single_deck_y_lines,
    validate_passenger_frame,
    z_floor_lines,
)
from .schemas import GeneratedFrame, WagonParams


def _floor_y(params: WagonParams) -> float:
    return params.levels.main_floor_y if params.levels.main_floor_y is not None else params.geometry.floor_y


def _roof_side_y(params: WagonParams) -> float:
    return (
        params.levels.roof_side_y
        if params.levels.roof_side_y is not None
        else _floor_y(params) + params.geometry.side_height
    )


def _roof_ridge_y(params: WagonParams) -> float:
    return (
        params.levels.roof_ridge_y
        if params.levels.roof_ridge_y is not None
        else _roof_side_y(params) + params.geometry.roof_height
    )


def _add_floor(builder: FrameBuilder, params: WagonParams, x_lines: list[float], z_lines: list[float]) -> None:
    g = params.geometry
    floor_y = _floor_y(params)
    half = g.width / 2.0

    add_line(
        builder,
        [(x, floor_y, 0.0) for x in x_lines],
        "center_sill",
        section(params, "center_sill"),
        **load_for(params, "center_sill"),
    )
    for z in (-half, half):
        add_line(
            builder,
            [(x, floor_y, z) for x in x_lines],
            "side_sill",
            section(params, "side_sill"),
            **load_for(params, "side_sill"),
        )
    for z in z_lines:
        if abs(z) <= 1e-6 or abs(abs(z) - half) <= 1e-6:
            continue
        add_line(
            builder,
            [(x, floor_y, z) for x in x_lines],
            "floor_longitudinal",
            section(params, "floor_longitudinal"),
            **load_for(params, "floor_longitudinal"),
        )

    cross_positions = set(pitch_coordinates(0.0, g.length, params.layout.cross_beam_pitch))
    cross_positions.update(g.bolster_positions)
    cross_positions.update([0.0, g.length])
    for x in unique_sorted(tuple(cross_positions)):
        if abs(x) <= 1e-6 or abs(x - g.length) <= 1e-6:
            tag = "end_beam"
        elif any(abs(x - b) <= 1e-6 for b in g.bolster_positions):
            tag = "bolster_beam"
        else:
            tag = "cross_beam"
        add_line(
            builder,
            [(x, floor_y, z) for z in z_lines],
            tag,
            section(params, tag),
            **load_for(params, tag),
        )


def _add_side_walls(builder: FrameBuilder, params: WagonParams, x_lines: list[float], y_lines: list[float]) -> None:
    half = params.geometry.width / 2.0
    floor_y = _floor_y(params)
    for z in (-half, half):
        for x in x_lines:
            tag = "opening_post" if is_opening_boundary(params, x) else "side_post"
            add_line(builder, [(x, y, z) for y in y_lines], tag, section(params, tag))

        for y in y_lines[1:]:
            for x0, x1 in zip(x_lines, x_lines[1:]):
                mid_x = 0.5 * (x0 + x1)
                mid_y = 0.5 * (floor_y + y)
                if side_opening_contains(params, mid_x, mid_y, z):
                    continue
                add_segment(
                    builder,
                    (x0, y, z),
                    (x1, y, z),
                    "side_belt",
                    section(params, "side_belt"),
                )

        for opening in (*params.openings.side_doors, *expanded_windows(params)):
            if not (opening.z_side == "both" or (opening.z_side == "left" and z < 0.0) or (opening.z_side == "right" and z > 0.0)):
                continue
            for y in (opening.y_bottom, opening.y_top):
                add_segment(
                    builder,
                    (opening.x_start, y, z),
                    (opening.x_end, y, z),
                    "side_belt",
                    section(params, "side_belt"),
                )


def _add_end_walls(builder: FrameBuilder, params: WagonParams, y_lines: list[float], z_lines: list[float]) -> None:
    floor_y = _floor_y(params)
    roof_side_y = _roof_side_y(params)
    for x in params.geometry.end_positions:
        end_doors = [door for door in params.openings.end_doors if abs(door.x - x) <= 1e-6]
        boundary_z = list(z_lines)
        for door in end_doors:
            boundary_z.extend([door.z_start, door.z_end])
        boundary_z = unique_sorted(boundary_z)

        for z in boundary_z:
            tag = "main_impact_post" if any(abs(z - d.z_start) <= 1e-6 or abs(z - d.z_end) <= 1e-6 for d in end_doors) else "end_post"
            add_line(builder, [(x, y, z) for y in y_lines], tag, section(params, tag))
        for y in y_lines[1:]:
            for z0, z1 in zip(boundary_z, boundary_z[1:]):
                mid_z = 0.5 * (z0 + z1)
                if any(door.z_start <= mid_z <= door.z_end and door.y_bottom <= y <= door.y_top for door in end_doors):
                    continue
                add_segment(builder, (x, y, z0), (x, y, z1), "side_belt", section(params, "side_belt"))
        for door in end_doors:
            for y in (door.y_bottom, door.y_top):
                add_segment(builder, (x, y, door.z_start), (x, y, door.z_end), "side_belt", section(params, "side_belt"))
            for z in (door.z_start, door.z_end):
                add_segment(builder, (x, floor_y, z), (x, roof_side_y, z), "main_impact_post", section(params, "main_impact_post"))


def _add_roof(builder: FrameBuilder, params: WagonParams, x_lines: list[float]) -> None:
    half = params.geometry.width / 2.0
    roof_side_y = _roof_side_y(params)
    roof_ridge_y = _roof_ridge_y(params)
    roof_x = unique_sorted([*x_lines, *pitch_coordinates(0.0, params.geometry.length, params.layout.roof_bow_pitch)])

    for z in (-half, half):
        add_line(
            builder,
            [(x, roof_side_y, z) for x in roof_x],
            "roof_longitudinal",
            section(params, "roof_longitudinal"),
            **load_for(params, "roof_longitudinal"),
        )
    add_line(
        builder,
        [(x, roof_ridge_y, 0.0) for x in roof_x],
        "roof_longitudinal",
        section(params, "roof_longitudinal"),
        node_tag="roof_ridge",
        **load_for(params, "roof_longitudinal"),
    )
    for x0, x1 in zip(roof_x, roof_x[1:]):
        kwargs = load_for(params, "roof_bow", x0, x1)
        if kwargs:
            # Roof-bow loads are represented on the nearest transverse bow below.
            pass
    for x in roof_x:
        left = builder.add_node(x, roof_side_y, -half, tags=("roof_bow",))
        ridge = builder.add_node(x, roof_ridge_y, 0.0, tags=("roof_bow", "roof_ridge"))
        right = builder.add_node(x, roof_side_y, half, tags=("roof_bow",))
        builder.add_member(left, ridge, "roof_bow", section(params, "roof_bow"), tags=("roof_bow",), **load_for(params, "roof_bow", x, x))
        builder.add_member(ridge, right, "roof_bow", section(params, "roof_bow"), tags=("roof_bow",), **load_for(params, "roof_bow", x, x))


def build_passenger_single_deck(params: WagonParams) -> GeneratedFrame:
    builder = FrameBuilder(tolerance=params.generation.coordinate_tolerance)
    x_lines = passenger_x_lines(params)
    y_lines = single_deck_y_lines(params)
    z_lines = z_floor_lines(params)

    _add_floor(builder, params, x_lines, z_lines)
    _add_side_walls(builder, params, x_lines, y_lines)
    _add_end_walls(builder, params, y_lines, z_lines)
    _add_roof(builder, params, x_lines)
    apply_passenger_supports(builder, params)

    frame = builder.build(build_metadata(params, "passenger_single_deck", x_lines, y_lines, z_lines))
    validate_passenger_frame(frame, PASSENGER_SINGLE_DECK_TAGS)
    return frame
