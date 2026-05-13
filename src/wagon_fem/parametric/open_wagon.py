from __future__ import annotations

from .builder import FrameBuilder
from .grid import floor_z_lines, height_lines, pitch_coordinates, unique_sorted
from .schemas import GeneratedFrame, SupportFlags, WagonParams


def _section(params: WagonParams, role: str) -> str:
    return str(getattr(params.sections, role))


def _load_for(params: WagonParams, member_tag: str) -> dict[str, object]:
    load = params.loads.vertical_distributed_load
    if load.enabled and member_tag in load.target_tags:
        return {"w": load.w, "dist_dir": load.dist_dir}
    return {}


def _node_line(builder: FrameBuilder, coords: list[tuple[float, float, float]], tag: str) -> list[int]:
    return [builder.add_node(x, y, z, tags=(tag,)) for x, y, z in coords]


def _add_line(builder: FrameBuilder, coords: list[tuple[float, float, float]],
              member_tag: str, section_tag: str, node_tag: str | None = None,
              **load_kwargs: object) -> list[int]:
    nodes = _node_line(builder, coords, node_tag or member_tag)
    return builder.add_polyline(nodes, member_tag, section_tag, tags=(member_tag,), **load_kwargs)


def _door_omits(params: WagonParams, x0: float, x1: float, z: float) -> bool:
    x_mid = 0.5 * (x0 + x1)
    return any(door.contains_midpoint(x_mid, z, params.geometry.width) for door in params.openings.side_doors)


def _support_node(builder: FrameBuilder, x: float, y: float, z: float) -> int:
    return builder.add_node(x, y, z, tags=("support",))


def _apply_flags(builder: FrameBuilder, node_id: int, flags: SupportFlags) -> None:
    builder.set_support(node_id, flags.dx, flags.dy, flags.dz, flags.rx, flags.ry, flags.rz)


def _apply_supports(builder: FrameBuilder, params: WagonParams, x_lines: list[float]) -> None:
    g = params.geometry
    bolsters = list(g.bolster_positions) or [x_lines[len(x_lines) // 2]]
    primary_x = bolsters[0]
    secondary_x = bolsters[-1]
    half = g.width / 2.0
    scheme = params.supports.scheme

    if scheme == "solver_stability_clamped_reference":
        primary = _support_node(builder, primary_x, g.floor_y, 0.0)
        builder.set_support(primary, True, True, True, True, True, True)
        for x in (primary_x, secondary_x):
            for z in (-half, half):
                builder.set_support(_support_node(builder, x, g.floor_y, z), False, True, True, False, False, False)
        return

    if scheme == "four_point_vertical":
        primary = _support_node(builder, primary_x, g.floor_y, 0.0)
        builder.set_support(primary, True, True, True, False, False, False)
        for x in (primary_x, secondary_x):
            for z in (-half, half):
                builder.set_support(_support_node(builder, x, g.floor_y, z), False, True, False, False, False, False)
        secondary = _support_node(builder, secondary_x, g.floor_y, 0.0)
        builder.set_support(secondary, False, False, True, False, False, False)
        return

    primary = _support_node(builder, primary_x, g.floor_y, 0.0)
    secondary = _support_node(builder, secondary_x, g.floor_y, 0.0)
    _apply_flags(builder, primary, params.supports.restrain_primary_bolster)
    _apply_flags(builder, secondary, params.supports.restrain_secondary_bolster)
    for x in (primary_x, secondary_x):
        for z in (-half, half):
            builder.set_support(_support_node(builder, x, g.floor_y, z), False, True, False, False, False, False)


def _common_x_lines(params: WagonParams) -> list[float]:
    g = params.geometry
    values = [0.0, g.length, *g.bolster_positions]
    values.extend(pitch_coordinates(0.0, g.length, params.layout.cross_beam_pitch))
    values.extend(pitch_coordinates(0.0, g.length, params.layout.side_post_pitch))
    for door in params.openings.side_doors:
        values.extend([door.x_start, door.x_end])
    return unique_sorted([v for v in values if -1e-6 <= v <= g.length + 1e-6])


def _build_body(params: WagonParams, covered: bool = False) -> GeneratedFrame:
    g = params.geometry
    builder = FrameBuilder()
    x_lines = _common_x_lines(params)
    y_lines = height_lines(g.floor_y, g.side_height, params.layout.side_height_divisions)
    z_floor = floor_z_lines(g.width, params.layout.floor_longitudinal_count_each_side)
    half = g.width / 2.0
    floor_y = g.floor_y
    top_y = floor_y + g.side_height

    _add_line(
        builder,
        [(x, floor_y, 0.0) for x in x_lines],
        "center_sill",
        _section(params, "center_sill"),
        **_load_for(params, "center_sill"),
    )
    for z in (-half, half):
        _add_line(
            builder,
            [(x, floor_y, z) for x in x_lines],
            "side_longitudinal",
            _section(params, "side_longitudinal"),
            **_load_for(params, "side_longitudinal"),
        )
    for z in z_floor:
        if abs(z) in (0.0, half):
            continue
        _add_line(
            builder,
            [(x, floor_y, z) for x in x_lines],
            "floor_longitudinal",
            _section(params, "floor_longitudinal"),
            **_load_for(params, "floor_longitudinal"),
        )

    cross_positions = set(pitch_coordinates(0.0, g.length, params.layout.cross_beam_pitch))
    cross_positions.update(g.bolster_positions)
    cross_positions.update([0.0, g.length])
    for x in unique_sorted(tuple(cross_positions)):
        if abs(x) < 1e-6 or abs(x - g.length) < 1e-6:
            tag = "end_beam"
            section = _section(params, "end_beam")
        elif any(abs(x - b) < 1e-6 for b in g.bolster_positions):
            tag = "bolster_beam"
            section = _section(params, "bolster_beam")
        else:
            tag = "cross_beam"
            section = _section(params, "cross_beam")
        _add_line(builder, [(x, floor_y, z) for z in z_floor], tag, section, **_load_for(params, tag))

    for z in (-half, half):
        for x in x_lines:
            if covered and _door_omits(params, max(0.0, x - 1e-6), min(g.length, x + 1e-6), z):
                pass
            _add_line(
                builder,
                [(x, y, z) for y in y_lines],
                "side_post",
                _section(params, "side_post"),
            )

        for y in y_lines[1:]:
            member_tag = "upper_belt" if abs(y - top_y) < 1e-6 else "horizontal_belt"
            section = _section(params, "upper_belt" if member_tag == "upper_belt" else "horizontal_belt")
            for x0, x1 in zip(x_lines, x_lines[1:]):
                if covered and _door_omits(params, x0, x1, z):
                    continue
                n0 = builder.add_node(x0, y, z, tags=(member_tag,))
                n1 = builder.add_node(x1, y, z, tags=(member_tag,))
                builder.add_member(n0, n1, member_tag, section, tags=(member_tag,))

        if params.layout.include_diagonals:
            for x0, x1 in zip(x_lines, x_lines[1:]):
                if covered and _door_omits(params, x0, x1, z):
                    continue
                for y0, y1 in zip(y_lines, y_lines[1:]):
                    n0 = builder.add_node(x0, y0, z, tags=("diagonal_tie",))
                    n1 = builder.add_node(x1, y1, z, tags=("diagonal_tie",))
                    builder.add_member(n0, n1, "diagonal_tie", _section(params, "diagonal_tie"), tags=("diagonal_tie",))

    for x in (0.0, g.length):
        for z in z_floor:
            _add_line(builder, [(x, y, z) for y in y_lines], "end_post", _section(params, "end_post"))
        for y in y_lines[1:]:
            member_tag = "upper_belt" if abs(y - top_y) < 1e-6 else "horizontal_belt"
            section = _section(params, "upper_belt" if member_tag == "upper_belt" else "horizontal_belt")
            _add_line(builder, [(x, y, z) for z in z_floor], member_tag, section)

    if covered:
        roof_height = g.roof_height if g.roof_height > 0.0 else 600.0
        ridge_y = top_y + roof_height
        roof_x = unique_sorted([*x_lines, *pitch_coordinates(0.0, g.length, params.layout.roof_bow_pitch)])
        for z in (-half, half):
            _add_line(
                builder,
                [(x, top_y, z) for x in roof_x],
                "roof_longitudinal",
                _section(params, "roof_longitudinal"),
            )
        _add_line(
            builder,
            [(x, ridge_y, 0.0) for x in roof_x],
            "roof_longitudinal",
            _section(params, "roof_longitudinal"),
            node_tag="roof_ridge",
        )
        for x in roof_x:
            left = builder.add_node(x, top_y, -half, tags=("roof_bow",))
            ridge = builder.add_node(x, ridge_y, 0.0, tags=("roof_bow", "roof_ridge"))
            right = builder.add_node(x, top_y, half, tags=("roof_bow",))
            builder.add_member(left, ridge, "roof_bow", _section(params, "roof_bow"), tags=("roof_bow",))
            builder.add_member(ridge, right, "roof_bow", _section(params, "roof_bow"), tags=("roof_bow",))
        for door in params.openings.side_doors:
            for z in (-half, half):
                for x in (door.x_start, door.x_end):
                    _add_line(builder, [(x, y, z) for y in y_lines], "door_post", _section(params, "side_post"))
                lintel_y = top_y
                threshold_y = floor_y
                for member_tag, y in (("door_lintel", lintel_y), ("door_threshold", threshold_y)):
                    n0 = builder.add_node(door.x_start, y, z, tags=(member_tag,))
                    n1 = builder.add_node(door.x_end, y, z, tags=(member_tag,))
                    section = _section(params, "upper_belt" if member_tag == "door_lintel" else "horizontal_belt")
                    builder.add_member(n0, n1, member_tag, section, tags=(member_tag,))

    _apply_supports(builder, params, x_lines)
    frame = builder.build(
        {
            "wagon_type": "covered_wagon" if covered else "open_wagon",
            "support_scheme": params.supports.scheme,
            "x_lines": x_lines,
            "y_lines": y_lines,
            "z_floor_lines": z_floor,
        }
    )
    return frame


def build_open_wagon(params: WagonParams) -> GeneratedFrame:
    return _build_body(params, covered=False)
