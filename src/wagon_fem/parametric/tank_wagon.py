from __future__ import annotations

import math

from .builder import FrameBuilder
from .grid import pitch_coordinates, unique_sorted
from .schemas import GeneratedFrame, SupportFlags, TankTotalLoad, WagonParams
from .validation import assert_valid_generated_frame


TANK_REQUIRED_TAGS = {
    "center_sill",
    "bolster_beam",
    "end_beam",
    "cross_beam",
    "tank_longitudinal",
    "tank_ring",
    "tank_end_ring",
    "saddle_support",
    "middle_tank_lug",
}


def _section(params: WagonParams, role: str) -> str:
    return str(getattr(params.sections, role))


def _layout_tank_pitch(params: WagonParams) -> float:
    return float(getattr(params.layout, "tank_ring_pitch", params.tank.ring_pitch) or params.tank.ring_pitch)


def _tank_station_values(params: WagonParams) -> list[float]:
    tank = params.tank
    values = [tank.x_start, tank.x_end, *tank.extra_ring_positions]
    values.extend(params.geometry.bolster_positions)
    if tank.drain_x is not None:
        values.append(tank.drain_x)
    if tank.manhole_x is not None:
        values.append(tank.manhole_x)
    values.extend(item.x for item in params.attachments.saddles)
    values.extend(item.x for item in params.attachments.middle_lugs)
    values.extend(params.attachments.straps.stations)
    values.extend(pitch_coordinates(tank.x_start, tank.x_end, _layout_tank_pitch(params)))
    return unique_sorted([v for v in values if tank.x_start - 1e-6 <= v <= tank.x_end + 1e-6])


def _frame_station_values(params: WagonParams, tank_stations: list[float]) -> list[float]:
    length = params.geometry.length
    values = [0.0, length, *params.geometry.bolster_positions, *tank_stations]
    values.extend(pitch_coordinates(0.0, length, params.layout.cross_beam_pitch))
    for support in params.supports.support_points:
        values.append(support.x)
    return unique_sorted([v for v in values if -1e-6 <= v <= length + 1e-6])


def _angles(params: WagonParams) -> list[float]:
    divisions = max(6, int(params.tank.angular_divisions))
    return [360.0 * idx / divisions for idx in range(divisions)]


def _ring_coord(params: WagonParams, x: float, angle_deg: float) -> tuple[float, float, float]:
    theta = math.radians(angle_deg)
    return (
        x,
        params.tank.center_y + params.tank.radius * math.sin(theta),
        params.tank.center_z + params.tank.radius * math.cos(theta),
    )


def _nearest_angle_index(angles: list[float], angle: float) -> int:
    normalized = angle % 360.0
    return min(range(len(angles)), key=lambda idx: abs(((angles[idx] - normalized + 180.0) % 360.0) - 180.0))


def _angle_in_span(angle: float, start: float, end: float) -> bool:
    angle = angle % 360.0
    start = start % 360.0
    end = end % 360.0
    if start <= end:
        return start <= angle <= end
    return angle >= start or angle <= end


def _node(builder: FrameBuilder, coord: tuple[float, float, float], tag: str) -> int:
    return builder.add_node(coord[0], coord[1], coord[2], tags=(tag,))


def _add_polyline(builder: FrameBuilder, coords: list[tuple[float, float, float]], tag: str, section_tag: str) -> None:
    nodes = [_node(builder, coord, tag) for coord in coords]
    builder.add_polyline(nodes, tag, section_tag, tags=(tag,))


def _add_underframe(builder: FrameBuilder, params: WagonParams, frame_stations: list[float]) -> dict[tuple[float, str], int]:
    frame = params.frame
    length = params.geometry.length
    width = params.geometry.frame_width or params.geometry.width
    side_z = frame.side_beam_z or (-width / 2.0, width / 2.0)
    nodes: dict[tuple[float, str], int] = {}

    _add_polyline(
        builder,
        [(x, frame.center_sill_y, frame.center_sill_z) for x in frame_stations],
        "center_sill",
        _section(params, "center_sill"),
    )
    for x in frame_stations:
        nodes[(x, "center_sill")] = builder.add_node(x, frame.center_sill_y, frame.center_sill_z, tags=("center_sill",))

    if frame.include_side_beams:
        for z in side_z:
            _add_polyline(
                builder,
                [(x, frame.side_beam_y, z) for x in frame_stations],
                "side_beam",
                _section(params, "side_beam"),
            )
            for x in frame_stations:
                side = "right_side_beam" if z > 0.0 else "left_side_beam"
                nodes[(x, side)] = builder.add_node(x, frame.side_beam_y, z, tags=("side_beam",))

    for x in frame_stations:
        if abs(x) <= 1e-6 or abs(x - length) <= 1e-6:
            tag = "end_beam"
        elif any(abs(x - b) <= 1e-6 for b in params.geometry.bolster_positions):
            tag = "bolster_beam"
        else:
            tag = "cross_beam"
        coords = [(x, frame.side_beam_y, min(side_z)), (x, frame.center_sill_y, frame.center_sill_z), (x, frame.side_beam_y, max(side_z))]
        _add_polyline(builder, coords, tag, _section(params, tag))

    for x in (0.0, length):
        sign = -1.0 if abs(x) <= 1e-6 else 1.0
        end = max(0.0, min(length, x + sign * frame.draft_gear_length))
        if abs(end - x) > 1e-6:
            _add_polyline(
                builder,
                [(x, frame.center_sill_y, frame.center_sill_z), (end, frame.center_sill_y, frame.center_sill_z)],
                "draft_gear_stub",
                _section(params, "draft_gear_stub"),
            )
    return nodes


def _add_tank_lattice(builder: FrameBuilder, params: WagonParams, stations: list[float], angles: list[float]) -> dict[tuple[float, int], int]:
    ring_nodes: dict[tuple[float, int], int] = {}
    for x in stations:
        tag = "tank_end_ring" if abs(x - params.tank.x_start) <= 1e-6 or abs(x - params.tank.x_end) <= 1e-6 else "tank_ring"
        ring = []
        for idx, angle in enumerate(angles):
            node = _node(builder, _ring_coord(params, x, angle), tag)
            ring_nodes[(x, idx)] = node
            ring.append(node)
        for start, end in zip(ring, [*ring[1:], ring[0]]):
            builder.add_member(start, end, tag, _section(params, tag), tags=(tag,))
        if tag == "tank_end_ring":
            center = builder.add_node(x, params.tank.center_y, params.tank.center_z, tags=("tank_end_center",))
            for idx in range(0, len(ring), max(1, len(ring) // 4)):
                builder.add_member(center, ring[idx], "tank_end_ring", _section(params, "tank_end_ring"), tags=("tank_end_ring", "tank_end_spoke"))

    for x0, x1 in zip(stations, stations[1:]):
        for idx in range(len(angles)):
            builder.add_member(
                ring_nodes[(x0, idx)],
                ring_nodes[(x1, idx)],
                "tank_longitudinal",
                _section(params, "tank_longitudinal"),
                tags=("tank_longitudinal",),
            )
    return ring_nodes


def _frame_anchor(builder: FrameBuilder, params: WagonParams, x: float, z: float = 0.0) -> int:
    return builder.add_node(x, params.frame.center_sill_y, z, tags=("frame_anchor",))


def _add_attachments(
    builder: FrameBuilder,
    params: WagonParams,
    ring_nodes: dict[tuple[float, int], int],
    angles: list[float],
) -> None:
    for saddle in params.attachments.saddles:
        anchor = _frame_anchor(builder, params, saddle.x)
        for idx, angle in enumerate(angles):
            if _angle_in_span(angle, saddle.angular_span_deg[0], saddle.angular_span_deg[1]):
                builder.add_member(
                    anchor,
                    ring_nodes[(saddle.x, idx)],
                    "saddle_support",
                    _section(params, "saddle_support"),
                    tags=("saddle_support",),
                )

    for lug in params.attachments.middle_lugs:
        anchor = _frame_anchor(builder, params, lug.x)
        idx = _nearest_angle_index(angles, lug.angular_position_deg)
        builder.add_member(
            anchor,
            ring_nodes[(lug.x, idx)],
            "middle_tank_lug",
            _section(params, "saddle_support"),
            tags=("middle_tank_lug", "longitudinal_lock" if lug.longitudinal_lock else "lug"),
        )

    if params.attachments.straps.enabled:
        for x in params.attachments.straps.stations:
            for angle in params.attachments.straps.angular_anchor_deg:
                idx = _nearest_angle_index(angles, angle)
                z = params.tank.center_z + params.tank.radius * math.cos(math.radians(angle))
                anchor = _frame_anchor(builder, params, x, z=0.65 * z)
                builder.add_member(
                    anchor,
                    ring_nodes[(x, idx)],
                    "strap_tie",
                    _section(params, "strap_tie"),
                    tags=("strap_tie",),
                )


def _add_node_load(builder: FrameBuilder, node_id: int, direction: str, value: float) -> None:
    key = direction.lower()
    if key in {"fx", "fy", "fz", "mx", "my", "mz"}:
        builder.add_node_load(node_id, **{key: value})


def _apply_total_load(
    builder: FrameBuilder,
    params: WagonParams,
    ring_nodes: dict[tuple[float, int], int],
    angles: list[float],
    load: TankTotalLoad,
) -> tuple[str, float]:
    if not load.enabled or abs(load.total_force) <= 0.0:
        return (load.distribute_to, 0.0)
    selected: list[int] = []
    if load.distribute_to == "tank_bottom_generators":
        idx = _nearest_angle_index(angles, 270.0)
        selected = [ring_nodes[(x, idx)] for x in sorted({key[0] for key in ring_nodes})]
    else:
        threshold = params.tank.center_y + params.tank.radius
        if load.fill_level is not None:
            threshold = params.tank.center_y - params.tank.radius + 2.0 * params.tank.radius * load.fill_level
        for (x, idx), node in ring_nodes.items():
            _, y, _ = _ring_coord(params, x, angles[idx])
            if y <= threshold + 1e-6:
                selected.append(node)
    if not selected:
        return (load.distribute_to, 0.0)
    share = load.total_force / len(selected)
    for node_id in selected:
        _add_node_load(builder, node_id, load.dist_dir, share)
    return (load.distribute_to, load.total_force)


def _apply_supports(builder: FrameBuilder, params: WagonParams) -> None:
    for support in params.supports.support_points:
        node = builder.add_node(support.x, support.y, support.z, tags=("support",))
        builder.set_support(
            node,
            support.flags.dx,
            support.flags.dy,
            support.flags.dz,
            support.flags.rx,
            support.flags.ry,
            support.flags.rz,
        )
        anchor = _frame_anchor(builder, params, support.x)
        if anchor != node:
            builder.add_member(anchor, node, "support_pad_stub", _section(params, "support_pad_stub"), tags=("support_pad_stub",))

    ref = params.supports.reference_restraints
    if ref.primary_x is not None:
        node = _frame_anchor(builder, params, ref.primary_x)
        flags = SupportFlags(dx=ref.lock_dx, dy=False, dz=True, rz=ref.lock_rigid_body_rotation)
        builder.set_support(node, flags.dx, flags.dy, flags.dz, flags.rx, flags.ry, flags.rz)


def build_tank_wagon(params: WagonParams) -> GeneratedFrame:
    if params.tank.radius <= 0.0:
        raise ValueError("Tank radius must be positive.")
    if params.tank.x_end <= params.tank.x_start:
        raise ValueError("Tank x_end must be greater than x_start.")
    if params.tank.angular_divisions < 6:
        raise ValueError("Tank angular_divisions must be at least 6.")

    builder = FrameBuilder(tolerance=params.generation.coordinate_tolerance)
    tank_stations = _tank_station_values(params)
    frame_stations = _frame_station_values(params, tank_stations)
    angles = _angles(params)

    _add_underframe(builder, params, frame_stations)
    ring_nodes = _add_tank_lattice(builder, params, tank_stations, angles)
    _add_attachments(builder, params, ring_nodes, angles)
    self_weight_meta = _apply_total_load(builder, params, ring_nodes, angles, params.loads.tank_self_weight)
    payload_meta = _apply_total_load(builder, params, ring_nodes, angles, params.loads.payload)
    _apply_supports(builder, params)

    metadata = {
        **params.metadata,
        "wagon_type": "tank_wagon",
        "support_scheme": params.supports.scheme,
        "frame_stations": frame_stations,
        "tank_stations": tank_stations,
        "tank_angles_deg": angles,
        "load_placement": {
            "tank_self_weight": self_weight_meta,
            "payload": payload_meta,
        },
        "saddle_slip": {saddle.x: saddle.allow_longitudinal_slip for saddle in params.attachments.saddles},
    }
    frame = builder.build(metadata)
    assert_valid_generated_frame(frame, required_tags=TANK_REQUIRED_TAGS)
    return frame
