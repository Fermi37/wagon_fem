from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class GeometryParams:
    length: float = 13920.0
    width: float = 3120.0
    external_width: float | None = None
    floor_y: float = 0.0
    lowered_floor_y: float | None = None
    side_height: float = 2200.0
    roof_height: float = 600.0
    height_from_rail: float | None = None
    bolster_positions: tuple[float, ...] = (1850.0, 12070.0)
    end_positions: tuple[float, float] = (0.0, 13920.0)
    coupler_axis_y: float | None = None
    body_reference: str | None = None
    gauge_profile: str | None = None
    frame_length: float | None = None
    truck_base: float | None = None
    frame_width: float | None = None
    rail_head_y: float | None = None


@dataclass(frozen=True)
class LayoutParams:
    cross_beam_pitch: float = 1200.0
    side_post_pitch: float = 1000.0
    side_height_divisions: int = 4
    roof_bow_pitch: float = 1000.0
    include_diagonals: bool = True
    include_rigid_offsets: bool = False
    floor_longitudinal_count_each_side: int = 1
    include_interdeck: bool = False
    tank_ring_pitch: float | None = None
    angular_divisions: int | None = None


@dataclass(frozen=True)
class SideDoor:
    x_start: float
    x_end: float
    y_bottom: float = 0.0
    y_top: float = 0.0
    z_side: str = "both"

    def contains_midpoint(self, x_mid: float, z: float, width: float) -> bool:
        if not (self.x_start <= x_mid <= self.x_end):
            return False
        if self.z_side == "both":
            return True
        if self.z_side == "left":
            return z < 0.0
        if self.z_side == "right":
            return z > 0.0
        return True


@dataclass(frozen=True)
class OpeningParams:
    side_doors: tuple[SideDoor, ...] = ()
    side_windows: tuple["SideWindow", ...] = ()
    end_doors: tuple["EndDoor", ...] = ()


@dataclass(frozen=True)
class RepeatSpec:
    count: int = 1
    pitch: float = 0.0


@dataclass(frozen=True)
class SideWindow:
    x_start: float
    x_end: float
    y_bottom: float
    y_top: float
    z_side: str = "both"
    repeat: RepeatSpec = field(default_factory=RepeatSpec)

    def expanded(self) -> tuple["SideWindow", ...]:
        count = max(1, int(self.repeat.count))
        return tuple(
            SideWindow(
                x_start=self.x_start + idx * self.repeat.pitch,
                x_end=self.x_end + idx * self.repeat.pitch,
                y_bottom=self.y_bottom,
                y_top=self.y_top,
                z_side=self.z_side,
            )
            for idx in range(count)
        )


@dataclass(frozen=True)
class EndDoor:
    x: float
    z_start: float
    z_end: float
    y_bottom: float
    y_top: float


@dataclass(frozen=True)
class LevelsParams:
    main_floor_y: float | None = None
    lower_floor_y: float | None = None
    interdeck_floor_y: float | None = None
    side_belt_lower_y: float | None = None
    window_sill_y: float | None = None
    window_head_y: float | None = None
    side_belt_upper_y: float | None = None
    lower_window_sill_y: float | None = None
    lower_window_head_y: float | None = None
    upper_window_sill_y: float | None = None
    upper_window_head_y: float | None = None
    roof_side_y: float | None = None
    roof_ridge_y: float | None = None


@dataclass(frozen=True)
class Zone:
    x_start: float
    x_end: float
    name: str | None = None


@dataclass(frozen=True)
class ZoneParams:
    vestibules: tuple[Zone, ...] = ()
    service_rooms: tuple[Zone, ...] = ()
    passenger_compartments: tuple[Zone, ...] = ()
    sanitary_modules: tuple[Zone, ...] = ()
    stairwells: tuple[Zone, ...] = ()
    lowered_floor: tuple[Zone, ...] = ()
    roof_equipment: tuple[Zone, ...] = ()


@dataclass(frozen=True)
class SectionAssignment:
    default_E: float = 210000.0
    catalog: str = "first_stage_v0.1.0"
    center_sill: str = "center_sill_heavy"
    side_sill: str = "side_longitudinal_medium"
    side_beam: str = "side_longitudinal_medium"
    bolster_beam: str = "bolster_beam_heavy"
    end_beam: str = "end_beam_medium"
    side_longitudinal: str = "side_longitudinal_medium"
    cross_beam: str = "cross_beam_medium"
    floor_longitudinal: str = "floor_longitudinal_light"
    side_post: str = "side_post_light"
    opening_post: str = "side_post_light"
    end_post: str = "end_post_light"
    main_impact_post: str = "end_post_light"
    side_belt: str = "horizontal_belt_light"
    upper_belt: str = "upper_belt_light"
    horizontal_belt: str = "horizontal_belt_light"
    roof_bow: str = "roof_bow_light"
    roof_longitudinal: str = "roof_longitudinal_light"
    interdeck_cross_beam: str = "cross_beam_medium"
    interdeck_longitudinal: str = "floor_longitudinal_light"
    tank_longitudinal: str = "side_longitudinal_medium"
    tank_ring: str = "cross_beam_medium"
    tank_end_ring: str = "cross_beam_medium"
    saddle_support: str = "rigid_offset_stub"
    strap_tie: str = "diagonal_tie_equiv"
    support_pad_stub: str = "rigid_offset_stub"
    draft_gear_stub: str = "center_sill_heavy"
    diagonal_tie: str = "diagonal_tie_equiv"
    rigid_offset: str = "rigid_offset_stub"


@dataclass(frozen=True)
class DistributedLoad:
    enabled: bool = False
    target_tags: tuple[str, ...] = ()
    w: float = 0.0
    dist_dir: str = "FY"


@dataclass(frozen=True)
class LateralBulkPressure:
    enabled: bool = False
    direction_left: str = "FZ"
    direction_right: str = "FZ"


@dataclass(frozen=True)
class LoadParams:
    vertical_distributed_load: DistributedLoad = field(default_factory=DistributedLoad)
    lateral_bulk_pressure: LateralBulkPressure = field(default_factory=LateralBulkPressure)
    equipment_zone_loads: tuple["EquipmentZoneLoad", ...] = ()
    longitudinal_end_load: "LongitudinalEndLoad" = field(default_factory=lambda: LongitudinalEndLoad())
    tank_self_weight: "TankTotalLoad" = field(default_factory=lambda: TankTotalLoad())
    payload: "TankTotalLoad" = field(default_factory=lambda: TankTotalLoad())
    lateral_inertial_load: "LateralInertialLoad" = field(default_factory=lambda: LateralInertialLoad())


@dataclass(frozen=True)
class EquipmentZoneLoad:
    name: str
    x_start: float
    x_end: float
    y: float
    target_tags: tuple[str, ...] = ()
    w: float = 0.0
    dist_dir: str = "FY"


@dataclass(frozen=True)
class LongitudinalEndLoad:
    enabled: bool = False
    x_end: float = 0.0
    force: float = 0.0
    apply_at: str = "center_sill"
    direction: str = "FX"


@dataclass(frozen=True)
class TankTotalLoad:
    enabled: bool = False
    total_force: float = 0.0
    distribute_to: str = "tank_lattice"
    dist_dir: str = "FY"
    fill_level: float | None = None


@dataclass(frozen=True)
class LateralInertialLoad:
    enabled: bool = False
    coefficient_g: float = 0.0
    direction: str = "FZ"


@dataclass(frozen=True)
class SupportFlags:
    dx: bool = False
    dy: bool = False
    dz: bool = False
    rx: bool = False
    ry: bool = False
    rz: bool = False


@dataclass(frozen=True)
class SupportParams:
    scheme: str = "two_bolster_reference"
    restrain_primary_bolster: SupportFlags = field(
        default_factory=lambda: SupportFlags(dx=True, dy=True, dz=True)
    )
    restrain_secondary_bolster: SupportFlags = field(
        default_factory=lambda: SupportFlags(dy=True, dz=True)
    )
    support_points: tuple["SupportPoint", ...] = ()
    reference_restraints: "ReferenceRestraints" = field(default_factory=lambda: ReferenceRestraints())


@dataclass(frozen=True)
class SupportPoint:
    x: float
    y: float
    z: float
    flags: SupportFlags


@dataclass(frozen=True)
class ReferencePoint:
    x: float
    y: float
    z: float
    flags: SupportFlags


@dataclass(frozen=True)
class ReferenceRestraints:
    primary: ReferencePoint | None = None
    secondary: ReferencePoint | None = None
    primary_x: float | None = None
    lock_dx: bool = False
    lock_rigid_body_rotation: bool = False


@dataclass(frozen=True)
class GenerationParams:
    coordinate_tolerance: float = 1.0e-6
    stable_ids: bool = True
    export_member_tags: bool = True
    export_node_tags: bool = False
    target_result_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class TankParams:
    length: float = 0.0
    diameter: float = 0.0
    radius: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0
    x_start: float = 0.0
    x_end: float = 0.0
    end_shape: str = "flat"
    bottom_slope_to_drain: bool = False
    drain_x: float | None = None
    manhole_x: float | None = None
    angular_divisions: int = 8
    ring_pitch: float = 900.0
    extra_ring_positions: tuple[float, ...] = ()


@dataclass(frozen=True)
class TankFrameParams:
    center_sill_z: float = 0.0
    center_sill_y: float = 0.0
    side_beam_z: tuple[float, ...] = ()
    side_beam_y: float = 0.0
    include_side_beams: bool = True
    include_intermediate_cross_beams: bool = True
    include_console_side_beams: bool = True
    draft_gear_length: float = 900.0


@dataclass(frozen=True)
class MiddleLug:
    x: float
    angular_position_deg: float = 270.0
    connect_to: str = "center_sill"
    longitudinal_lock: bool = False


@dataclass(frozen=True)
class Saddle:
    x: float
    angular_span_deg: tuple[float, float] = (225.0, 315.0)
    connect_to: str = "bolster_beam"
    allow_longitudinal_slip: bool = False


@dataclass(frozen=True)
class StrapParams:
    enabled: bool = False
    stations: tuple[float, ...] = ()
    angular_anchor_deg: tuple[float, float] = (210.0, 330.0)


@dataclass(frozen=True)
class AttachmentParams:
    middle_lugs: tuple[MiddleLug, ...] = ()
    saddles: tuple[Saddle, ...] = ()
    straps: StrapParams = field(default_factory=StrapParams)


@dataclass(frozen=True)
class WagonParams:
    wagon_type: str = "open_wagon"
    geometry: GeometryParams = field(default_factory=GeometryParams)
    layout: LayoutParams = field(default_factory=LayoutParams)
    levels: LevelsParams = field(default_factory=LevelsParams)
    openings: OpeningParams = field(default_factory=OpeningParams)
    zones: ZoneParams = field(default_factory=ZoneParams)
    sections: SectionAssignment = field(default_factory=SectionAssignment)
    loads: LoadParams = field(default_factory=LoadParams)
    supports: SupportParams = field(default_factory=SupportParams)
    generation: GenerationParams = field(default_factory=GenerationParams)
    metadata: dict[str, object] = field(default_factory=dict)
    tank: TankParams = field(default_factory=TankParams)
    frame: TankFrameParams = field(default_factory=TankFrameParams)
    attachments: AttachmentParams = field(default_factory=AttachmentParams)


@dataclass
class GeneratedFrame:
    nodes_df: pd.DataFrame
    edges_df: pd.DataFrame
    node_tags: dict[int, set[str]]
    edge_tags: dict[int, set[str]]
    metadata: dict[str, object]


def _tuple_float(value: Any) -> tuple[float, ...]:
    if value is None:
        return ()
    if isinstance(value, (int, float)):
        return (float(value),)
    return tuple(float(v) for v in value)


def _flags(data: dict[str, Any] | None, default: SupportFlags) -> SupportFlags:
    if data is None:
        return default
    return SupportFlags(
        dx=bool(data.get("dx", default.dx)),
        dy=bool(data.get("dy", default.dy)),
        dz=bool(data.get("dz", default.dz)),
        rx=bool(data.get("rx", default.rx)),
        ry=bool(data.get("ry", default.ry)),
        rz=bool(data.get("rz", default.rz)),
    )


def _support_flags_from_item(data: dict[str, Any]) -> SupportFlags:
    return SupportFlags(
        dx=bool(data.get("dx", False)),
        dy=bool(data.get("dy", False)),
        dz=bool(data.get("dz", False)),
        rx=bool(data.get("rx", False)),
        ry=bool(data.get("ry", False)),
        rz=bool(data.get("rz", False)),
    )


def _reference_point(data: dict[str, Any] | None) -> ReferencePoint | None:
    if not data:
        return None
    return ReferencePoint(
        x=float(data.get("x", 0.0)),
        y=float(data.get("y", 0.0)),
        z=float(data.get("z", 0.0)),
        flags=_support_flags_from_item(data),
    )


def _zones(items: list[dict[str, Any]] | None) -> tuple[Zone, ...]:
    result: list[Zone] = []
    for item in items or []:
        result.append(
            Zone(
                x_start=float(item["x_start"]),
                x_end=float(item["x_end"]),
                name=str(item["name"]) if "name" in item else None,
            )
        )
    return tuple(result)


def wagon_params_from_dict(data: dict[str, Any]) -> WagonParams:
    geometry_raw = data.get("geometry", {})
    length = float(
        geometry_raw.get(
            "length",
            geometry_raw.get(
                "frame_length",
                geometry_raw.get("length_over_coupler_axes", GeometryParams.length),
            ),
        )
    )
    geometry = GeometryParams(
        length=length,
        width=float(geometry_raw.get("width", GeometryParams.width)),
        external_width=(
            float(geometry_raw["external_width"])
            if geometry_raw.get("external_width") is not None
            else None
        ),
        floor_y=float(geometry_raw.get("floor_y", GeometryParams.floor_y)),
        lowered_floor_y=(
            float(geometry_raw["lowered_floor_y"])
            if geometry_raw.get("lowered_floor_y") is not None
            else None
        ),
        side_height=float(geometry_raw.get("side_height", GeometryParams.side_height)),
        roof_height=float(geometry_raw.get("roof_height", GeometryParams.roof_height)),
        height_from_rail=(
            float(geometry_raw["height_from_rail"])
            if geometry_raw.get("height_from_rail") is not None
            else None
        ),
        bolster_positions=_tuple_float(geometry_raw.get("bolster_positions", GeometryParams.bolster_positions)),
        end_positions=tuple(
            float(v) for v in geometry_raw.get("end_positions", (0.0, length))
        ),
        coupler_axis_y=(
            float(geometry_raw["coupler_axis_y"])
            if geometry_raw.get("coupler_axis_y") is not None
            else None
        ),
        body_reference=(
            str(geometry_raw["body_reference"])
            if geometry_raw.get("body_reference") is not None
            else None
        ),
        gauge_profile=(
            str(geometry_raw["gauge_profile"])
            if geometry_raw.get("gauge_profile") is not None
            else None
        ),
        frame_length=(
            float(geometry_raw["frame_length"])
            if geometry_raw.get("frame_length") is not None
            else None
        ),
        truck_base=(
            float(geometry_raw["truck_base"])
            if geometry_raw.get("truck_base") is not None
            else None
        ),
        frame_width=(
            float(geometry_raw["frame_width"])
            if geometry_raw.get("frame_width") is not None
            else None
        ),
        rail_head_y=(
            float(geometry_raw["rail_head_y"])
            if geometry_raw.get("rail_head_y") is not None
            else None
        ),
    )

    layout_raw = data.get("layout", {})
    layout = LayoutParams(
        cross_beam_pitch=float(layout_raw.get("cross_beam_pitch", LayoutParams.cross_beam_pitch)),
        side_post_pitch=float(layout_raw.get("side_post_pitch", LayoutParams.side_post_pitch)),
        side_height_divisions=int(layout_raw.get("side_height_divisions", LayoutParams.side_height_divisions)),
        roof_bow_pitch=float(layout_raw.get("roof_bow_pitch", LayoutParams.roof_bow_pitch)),
        include_diagonals=bool(layout_raw.get("include_diagonals", LayoutParams.include_diagonals)),
        include_rigid_offsets=bool(layout_raw.get("include_rigid_offsets", LayoutParams.include_rigid_offsets)),
        floor_longitudinal_count_each_side=int(
            layout_raw.get(
                "floor_longitudinal_count_each_side",
                LayoutParams.floor_longitudinal_count_each_side,
            )
        ),
        include_interdeck=bool(layout_raw.get("include_interdeck", LayoutParams.include_interdeck)),
        tank_ring_pitch=(
            float(layout_raw["tank_ring_pitch"])
            if layout_raw.get("tank_ring_pitch") is not None
            else None
        ),
        angular_divisions=(
            int(layout_raw["angular_divisions"])
            if layout_raw.get("angular_divisions") is not None
            else None
        ),
    )

    openings_raw = data.get("openings", {})
    doors = []
    for item in openings_raw.get("side_doors", []) or []:
        doors.append(
            SideDoor(
                x_start=float(item["x_start"]),
                x_end=float(item["x_end"]),
                y_bottom=float(item.get("y_bottom", 0.0)),
                y_top=float(item.get("y_top", 0.0)),
                z_side=str(item.get("z_side", "both")),
            )
        )
    windows = []
    for item in openings_raw.get("side_windows", []) or []:
        repeat_raw = item.get("repeat") or {}
        windows.append(
            SideWindow(
                x_start=float(item["x_start"]),
                x_end=float(item["x_end"]),
                y_bottom=float(item["y_bottom"]),
                y_top=float(item["y_top"]),
                z_side=str(item.get("z_side", "both")),
                repeat=RepeatSpec(
                    count=int(repeat_raw.get("count", 1)),
                    pitch=float(repeat_raw.get("pitch", 0.0)),
                ),
            )
        )
    end_doors = []
    for item in openings_raw.get("end_doors", []) or []:
        end_doors.append(
            EndDoor(
                x=float(item["x"]),
                z_start=float(item["z_start"]),
                z_end=float(item["z_end"]),
                y_bottom=float(item["y_bottom"]),
                y_top=float(item["y_top"]),
            )
        )
    openings = OpeningParams(
        side_doors=tuple(doors),
        side_windows=tuple(windows),
        end_doors=tuple(end_doors),
    )

    levels_raw = data.get("levels", {})
    level_defaults = LevelsParams()
    levels = LevelsParams(
        **{
            field_name: (
                float(levels_raw[field_name])
                if levels_raw.get(field_name) is not None
                else getattr(level_defaults, field_name)
            )
            for field_name in level_defaults.__dataclass_fields__
        }
    )

    zones_raw = data.get("zones", {})
    zones = ZoneParams(
        vestibules=_zones(zones_raw.get("vestibules")),
        service_rooms=_zones(zones_raw.get("service_rooms")),
        passenger_compartments=_zones(zones_raw.get("passenger_compartments")),
        sanitary_modules=_zones(zones_raw.get("sanitary_modules")),
        stairwells=_zones(zones_raw.get("stairwells")),
        lowered_floor=_zones(zones_raw.get("lowered_floor")),
        roof_equipment=_zones(zones_raw.get("roof_equipment")),
    )

    sections_raw = data.get("sections", {})
    section_defaults = SectionAssignment()
    sections = SectionAssignment(
        **{
            field_name: sections_raw.get(field_name, getattr(section_defaults, field_name))
            for field_name in section_defaults.__dataclass_fields__
        }
    )

    loads_raw = data.get("loads", {})
    vertical_raw = loads_raw.get("vertical_distributed_load", {})
    lateral_raw = loads_raw.get("lateral_bulk_pressure", {})
    equipment_loads = []
    for item in loads_raw.get("equipment_zone_loads", []) or []:
        equipment_loads.append(
            EquipmentZoneLoad(
                name=str(item.get("name", "equipment")),
                x_start=float(item["x_start"]),
                x_end=float(item["x_end"]),
                y=float(item.get("y", 0.0)),
                target_tags=tuple(str(v) for v in item.get("target_tags", ())),
                w=float(item.get("w", 0.0)),
                dist_dir=str(item.get("dist_dir", "FY")).upper(),
            )
        )
    longitudinal_raw = loads_raw.get("longitudinal_end_load", {})
    tank_self_weight_raw = loads_raw.get("tank_self_weight", {})
    payload_raw = loads_raw.get("payload", {})
    lateral_inertial_raw = loads_raw.get("lateral_inertial_load", {})
    loads = LoadParams(
        vertical_distributed_load=DistributedLoad(
            enabled=bool(vertical_raw.get("enabled", False)),
            target_tags=tuple(str(v) for v in vertical_raw.get("target_tags", ())),
            w=float(vertical_raw.get("w", 0.0)),
            dist_dir=str(vertical_raw.get("dist_dir", "FY")).upper(),
        ),
        lateral_bulk_pressure=LateralBulkPressure(
            enabled=bool(lateral_raw.get("enabled", False)),
            direction_left=str(lateral_raw.get("direction_left", "FZ")).upper(),
            direction_right=str(lateral_raw.get("direction_right", "FZ")).upper(),
        ),
        equipment_zone_loads=tuple(equipment_loads),
        longitudinal_end_load=LongitudinalEndLoad(
            enabled=bool(longitudinal_raw.get("enabled", False)),
            x_end=float(longitudinal_raw.get("x_end", 0.0)),
            force=float(longitudinal_raw.get("force", 0.0)),
            apply_at=str(longitudinal_raw.get("apply_at", "center_sill")),
            direction=str(longitudinal_raw.get("direction", "FX")).upper(),
        ),
        tank_self_weight=TankTotalLoad(
            enabled=bool(tank_self_weight_raw.get("enabled", False)),
            total_force=float(tank_self_weight_raw.get("total_force", 0.0)),
            distribute_to=str(tank_self_weight_raw.get("distribute_to", "tank_lattice")),
            dist_dir=str(tank_self_weight_raw.get("dist_dir", "FY")).upper(),
        ),
        payload=TankTotalLoad(
            enabled=bool(payload_raw.get("enabled", False)),
            total_force=float(payload_raw.get("total_force", 0.0)),
            distribute_to=str(payload_raw.get("distribute_to", "tank_lattice")),
            dist_dir=str(payload_raw.get("dist_dir", "FY")).upper(),
            fill_level=(
                float(payload_raw["fill_level"])
                if payload_raw.get("fill_level") is not None
                else None
            ),
        ),
        lateral_inertial_load=LateralInertialLoad(
            enabled=bool(lateral_inertial_raw.get("enabled", False)),
            coefficient_g=float(lateral_inertial_raw.get("coefficient_g", 0.0)),
            direction=str(lateral_inertial_raw.get("direction", "FZ")).upper(),
        ),
    )

    support_defaults = SupportParams()
    supports_raw = data.get("supports", {})
    support_points = tuple(
        SupportPoint(
            x=float(item["x"]),
            y=float(item.get("y", 0.0)),
            z=float(item.get("z", 0.0)),
            flags=_support_flags_from_item(item),
        )
        for item in supports_raw.get("support_points", []) or []
    )
    reference_raw = supports_raw.get("reference_restraints") or {}
    reference_restraints = ReferenceRestraints(
        primary=_reference_point(reference_raw.get("primary")),
        secondary=_reference_point(reference_raw.get("secondary")),
        primary_x=(
            float(reference_raw["primary_x"])
            if reference_raw.get("primary_x") is not None
            else None
        ),
        lock_dx=bool(reference_raw.get("lock_dx", False)),
        lock_rigid_body_rotation=bool(reference_raw.get("lock_rigid_body_rotation", False)),
    )
    supports = SupportParams(
        scheme=str(supports_raw.get("scheme", support_defaults.scheme)),
        restrain_primary_bolster=_flags(
            supports_raw.get("restrain_primary_bolster"),
            support_defaults.restrain_primary_bolster,
        ),
        restrain_secondary_bolster=_flags(
            supports_raw.get("restrain_secondary_bolster"),
            support_defaults.restrain_secondary_bolster,
        ),
        support_points=support_points,
        reference_restraints=reference_restraints,
    )

    generation_raw = data.get("generation", {})
    generation = GenerationParams(
        coordinate_tolerance=float(
            generation_raw.get("coordinate_tolerance", GenerationParams.coordinate_tolerance)
        ),
        stable_ids=bool(generation_raw.get("stable_ids", GenerationParams.stable_ids)),
        export_member_tags=bool(
            generation_raw.get("export_member_tags", GenerationParams.export_member_tags)
        ),
        export_node_tags=bool(
            generation_raw.get("export_node_tags", GenerationParams.export_node_tags)
        ),
        target_result_tags=tuple(str(v) for v in generation_raw.get("target_result_tags", ())),
    )

    tank_raw = data.get("tank", {})
    tank_diameter = float(tank_raw.get("diameter", 0.0))
    tank_radius = float(tank_raw.get("radius", tank_diameter / 2.0 if tank_diameter else 0.0))
    tank = TankParams(
        length=float(tank_raw.get("length", 0.0)),
        diameter=tank_diameter,
        radius=tank_radius,
        center_y=float(tank_raw.get("center_y", 0.0)),
        center_z=float(tank_raw.get("center_z", 0.0)),
        x_start=float(tank_raw.get("x_start", 0.0)),
        x_end=float(tank_raw.get("x_end", 0.0)),
        end_shape=str(tank_raw.get("end_shape", "flat")),
        bottom_slope_to_drain=bool(tank_raw.get("bottom_slope_to_drain", False)),
        drain_x=(float(tank_raw["drain_x"]) if tank_raw.get("drain_x") is not None else None),
        manhole_x=(float(tank_raw["manhole_x"]) if tank_raw.get("manhole_x") is not None else None),
        angular_divisions=int(tank_raw.get("angular_divisions", layout.angular_divisions or 8)),
        ring_pitch=float(tank_raw.get("ring_pitch", layout.tank_ring_pitch or layout.cross_beam_pitch)),
        extra_ring_positions=_tuple_float(tank_raw.get("extra_ring_positions", ())),
    )

    frame_raw = data.get("frame", {})
    tank_frame = TankFrameParams(
        center_sill_z=float(frame_raw.get("center_sill_z", 0.0)),
        center_sill_y=float(frame_raw.get("center_sill_y", 0.0)),
        side_beam_z=_tuple_float(frame_raw.get("side_beam_z", ())),
        side_beam_y=float(frame_raw.get("side_beam_y", 0.0)),
        include_side_beams=bool(frame_raw.get("include_side_beams", True)),
        include_intermediate_cross_beams=bool(frame_raw.get("include_intermediate_cross_beams", True)),
        include_console_side_beams=bool(frame_raw.get("include_console_side_beams", True)),
        draft_gear_length=float(frame_raw.get("draft_gear_length", 900.0)),
    )

    attachments_raw = data.get("attachments", {})
    middle_lugs = tuple(
        MiddleLug(
            x=float(item["x"]),
            angular_position_deg=float(item.get("angular_position_deg", 270.0)),
            connect_to=str(item.get("connect_to", "center_sill")),
            longitudinal_lock=bool(item.get("longitudinal_lock", False)),
        )
        for item in attachments_raw.get("middle_lugs", []) or []
    )
    saddles = tuple(
        Saddle(
            x=float(item["x"]),
            angular_span_deg=tuple(float(v) for v in item.get("angular_span_deg", (225.0, 315.0))),
            connect_to=str(item.get("connect_to", "bolster_beam")),
            allow_longitudinal_slip=bool(item.get("allow_longitudinal_slip", False)),
        )
        for item in attachments_raw.get("saddles", []) or []
    )
    straps_raw = attachments_raw.get("straps", {}) or {}
    attachments = AttachmentParams(
        middle_lugs=middle_lugs,
        saddles=saddles,
        straps=StrapParams(
            enabled=bool(straps_raw.get("enabled", False)),
            stations=_tuple_float(straps_raw.get("stations", ())),
            angular_anchor_deg=tuple(
                float(v) for v in straps_raw.get("angular_anchor_deg", (210.0, 330.0))
            ),
        ),
    )

    return WagonParams(
        wagon_type=str(data.get("wagon_type", "open_wagon")),
        geometry=geometry,
        layout=layout,
        levels=levels,
        openings=openings,
        zones=zones,
        sections=sections,
        loads=loads,
        supports=supports,
        generation=generation,
        metadata=dict(data.get("metadata", {}) or {}),
        tank=tank,
        frame=tank_frame,
        attachments=attachments,
    )


def load_params(path: str | Path) -> WagonParams:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except Exception as exc:
            raise RuntimeError("YAML parameter files require PyYAML.") from exc
        data = yaml.safe_load(text) or {}
    return wagon_params_from_dict(data)
