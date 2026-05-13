from __future__ import annotations

from typing import Iterable

from .builder import FrameBuilder
from .grid import floor_z_lines, height_lines, pitch_coordinates, unique_sorted
from .schemas import (
    GeneratedFrame,
    ReferencePoint,
    SideDoor,
    SideWindow,
    SupportFlags,
    WagonParams,
    Zone,
)


PASSENGER_SINGLE_DECK_TAGS = {
    "center_sill",
    "side_sill",
    "bolster_beam",
    "end_beam",
    "cross_beam",
    "floor_longitudinal",
    "side_post",
    "opening_post",
    "side_belt",
    "end_post",
    "main_impact_post",
    "roof_bow",
    "roof_longitudinal",
}

PASSENGER_DOUBLE_DECK_TAGS = PASSENGER_SINGLE_DECK_TAGS | {
    "interdeck_cross_beam",
    "interdeck_longitudinal",
}


def section(params: WagonParams, role: str) -> str:
    return str(getattr(params.sections, role))


def expanded_windows(params: WagonParams) -> tuple[SideWindow, ...]:
    windows: list[SideWindow] = []
    for window in params.openings.side_windows:
        windows.extend(window.expanded())
    return tuple(windows)


def zone_boundaries(zones: Iterable[Zone]) -> list[float]:
    values: list[float] = []
    for zone in zones:
        values.extend([zone.x_start, zone.x_end])
    return values


def passenger_x_lines(params: WagonParams) -> list[float]:
    g = params.geometry
    values = [0.0, g.length, *g.bolster_positions]
    values.extend(pitch_coordinates(0.0, g.length, params.layout.cross_beam_pitch))
    values.extend(pitch_coordinates(0.0, g.length, params.layout.side_post_pitch))
    values.extend(pitch_coordinates(0.0, g.length, params.layout.roof_bow_pitch))
    for door in params.openings.side_doors:
        values.extend([door.x_start, door.x_end])
    for window in expanded_windows(params):
        values.extend([window.x_start, window.x_end])
    zones = params.zones
    for group in (
        zones.vestibules,
        zones.service_rooms,
        zones.passenger_compartments,
        zones.sanitary_modules,
        zones.stairwells,
        zones.lowered_floor,
        zones.roof_equipment,
    ):
        values.extend(zone_boundaries(group))
    return unique_sorted([v for v in values if -1e-6 <= v <= g.length + 1e-6])


def single_deck_y_lines(params: WagonParams) -> list[float]:
    g = params.geometry
    levels = params.levels
    floor_y = levels.main_floor_y if levels.main_floor_y is not None else g.floor_y
    roof_side_y = levels.roof_side_y if levels.roof_side_y is not None else floor_y + g.side_height
    values = height_lines(floor_y, roof_side_y - floor_y, params.layout.side_height_divisions)
    values.extend(
        value
        for value in (
            levels.side_belt_lower_y,
            levels.window_sill_y,
            levels.window_head_y,
            levels.side_belt_upper_y,
            roof_side_y,
        )
        if value is not None
    )
    for door in params.openings.side_doors:
        values.extend([door.y_bottom, door.y_top])
    for door in params.openings.end_doors:
        values.extend([door.y_bottom, door.y_top])
    for window in expanded_windows(params):
        values.extend([window.y_bottom, window.y_top])
    return unique_sorted(values)


def double_deck_y_lines(params: WagonParams) -> list[float]:
    g = params.geometry
    levels = params.levels
    floor_y = levels.lower_floor_y if levels.lower_floor_y is not None else (g.lowered_floor_y or g.floor_y)
    roof_side_y = levels.roof_side_y if levels.roof_side_y is not None else g.floor_y + g.side_height
    values = height_lines(floor_y, roof_side_y - floor_y, params.layout.side_height_divisions)
    values.extend(
        value
        for value in (
            levels.main_floor_y,
            levels.lower_floor_y,
            levels.interdeck_floor_y,
            levels.lower_window_sill_y,
            levels.lower_window_head_y,
            levels.upper_window_sill_y,
            levels.upper_window_head_y,
            roof_side_y,
        )
        if value is not None
    )
    for door in params.openings.side_doors:
        values.extend([door.y_bottom, door.y_top])
    for door in params.openings.end_doors:
        values.extend([door.y_bottom, door.y_top])
    for window in expanded_windows(params):
        values.extend([window.y_bottom, window.y_top])
    return unique_sorted(values)


def z_floor_lines(params: WagonParams) -> list[float]:
    return floor_z_lines(params.geometry.width, params.layout.floor_longitudinal_count_each_side)


def load_for(params: WagonParams, member_tag: str, x0: float | None = None, x1: float | None = None) -> dict[str, object]:
    load = params.loads.vertical_distributed_load
    if load.enabled and member_tag in load.target_tags:
        return {"w": load.w, "dist_dir": load.dist_dir}
    if x0 is not None and x1 is not None:
        mid = 0.5 * (x0 + x1)
        for zone_load in params.loads.equipment_zone_loads:
            if member_tag in zone_load.target_tags and zone_load.x_start <= mid <= zone_load.x_end:
                return {"w": zone_load.w, "dist_dir": zone_load.dist_dir}
    return {}


def add_line(
    builder: FrameBuilder,
    coords: list[tuple[float, float, float]],
    member_tag: str,
    section_tag: str,
    node_tag: str | None = None,
    **load_kwargs: object,
) -> list[int]:
    node_ids = [builder.add_node(x, y, z, tags=(node_tag or member_tag,)) for x, y, z in coords]
    return builder.add_polyline(node_ids, member_tag, section_tag, tags=(member_tag,), **load_kwargs)


def add_segment(
    builder: FrameBuilder,
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    member_tag: str,
    section_tag: str,
    **load_kwargs: object,
) -> int:
    n0 = builder.add_node(*a, tags=(member_tag,))
    n1 = builder.add_node(*b, tags=(member_tag,))
    return builder.add_member(n0, n1, member_tag, section_tag, tags=(member_tag,), **load_kwargs)


def side_applies(z_side: str, z: float) -> bool:
    if z_side == "both":
        return True
    if z_side == "left":
        return z < 0.0
    if z_side == "right":
        return z > 0.0
    return True


def side_opening_contains(params: WagonParams, x_mid: float, y_mid: float, z: float) -> bool:
    for door in params.openings.side_doors:
        if side_applies(door.z_side, z) and door.x_start <= x_mid <= door.x_end:
            if door.y_bottom <= y_mid <= max(door.y_top, door.y_bottom):
                return True
    for window in expanded_windows(params):
        if side_applies(window.z_side, z) and window.x_start <= x_mid <= window.x_end:
            if window.y_bottom <= y_mid <= window.y_top:
                return True
    return False


def is_opening_boundary(params: WagonParams, x: float, tolerance: float = 1.0e-6) -> bool:
    boundaries: list[float] = []
    for door in params.openings.side_doors:
        boundaries.extend([door.x_start, door.x_end])
    for window in expanded_windows(params):
        boundaries.extend([window.x_start, window.x_end])
    return any(abs(x - value) <= tolerance for value in boundaries)


def apply_flags(builder: FrameBuilder, node_id: int, flags: SupportFlags) -> None:
    builder.set_support(node_id, flags.dx, flags.dy, flags.dz, flags.rx, flags.ry, flags.rz)


def apply_reference(builder: FrameBuilder, point: ReferencePoint | None) -> None:
    if point is None:
        return
    node = builder.add_node(point.x, point.y, point.z, tags=("support", "reference_restraint"))
    apply_flags(builder, node, point.flags)


def apply_passenger_supports(builder: FrameBuilder, params: WagonParams) -> None:
    if params.supports.support_points:
        for support in params.supports.support_points:
            node = builder.add_node(support.x, support.y, support.z, tags=("support",))
            apply_flags(builder, node, support.flags)
            anchor = builder.add_node(support.x, support.y, 0.0, tags=("support_anchor",))
            if anchor != node:
                builder.add_member(
                    anchor,
                    node,
                    "rigid_offset",
                    section(params, "rigid_offset"),
                    tags=("rigid_offset", "support_transfer"),
                )
        apply_reference(builder, params.supports.reference_restraints.primary)
        apply_reference(builder, params.supports.reference_restraints.secondary)
        return

    g = params.geometry
    half = g.width / 2.0
    bolsters = list(g.bolster_positions) or [g.length / 2.0]
    primary_x = bolsters[0]
    secondary_x = bolsters[-1]
    for x in (primary_x, secondary_x):
        for z in (-half, half):
            builder.set_support(builder.add_node(x, g.floor_y, z, tags=("support",)), False, True, False)
    builder.set_support(builder.add_node(primary_x, g.floor_y, 0.0, tags=("support",)), True, True, True)
    builder.set_support(builder.add_node(secondary_x, g.floor_y, 0.0, tags=("support",)), False, False, True)


def build_metadata(params: WagonParams, wagon_type: str, x_lines: list[float], y_lines: list[float], z_lines: list[float]) -> dict[str, object]:
    return {
        "wagon_type": wagon_type,
        "support_scheme": params.supports.scheme,
        "x_lines": x_lines,
        "y_lines": y_lines,
        "z_floor_lines": z_lines,
        "load_placement": "member_distributed",
    }


def validate_passenger_frame(frame: GeneratedFrame, required_tags: set[str]) -> None:
    from .validation import assert_valid_generated_frame

    assert_valid_generated_frame(frame, required_tags=required_tags)
