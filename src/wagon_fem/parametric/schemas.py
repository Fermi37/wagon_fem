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
    direction: str = "FX"


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
    length = float(geometry_raw.get("length", GeometryParams.length))
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
            direction=str(longitudinal_raw.get("direction", "FX")).upper(),
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
