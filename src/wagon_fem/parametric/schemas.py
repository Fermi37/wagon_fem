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
    floor_y: float = 0.0
    side_height: float = 2200.0
    roof_height: float = 600.0
    bolster_positions: tuple[float, ...] = (1850.0, 12070.0)
    end_positions: tuple[float, float] = (0.0, 13920.0)


@dataclass(frozen=True)
class LayoutParams:
    cross_beam_pitch: float = 1200.0
    side_post_pitch: float = 1000.0
    side_height_divisions: int = 4
    roof_bow_pitch: float = 1000.0
    include_diagonals: bool = True
    include_rigid_offsets: bool = False
    floor_longitudinal_count_each_side: int = 1


@dataclass(frozen=True)
class SideDoor:
    x_start: float
    x_end: float
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


@dataclass(frozen=True)
class SectionAssignment:
    default_E: float = 210000.0
    catalog: str = "first_stage_v0.1.0"
    center_sill: str = "center_sill_heavy"
    bolster_beam: str = "bolster_beam_heavy"
    end_beam: str = "end_beam_medium"
    side_longitudinal: str = "side_longitudinal_medium"
    cross_beam: str = "cross_beam_medium"
    floor_longitudinal: str = "floor_longitudinal_light"
    side_post: str = "side_post_light"
    end_post: str = "end_post_light"
    upper_belt: str = "upper_belt_light"
    horizontal_belt: str = "horizontal_belt_light"
    roof_bow: str = "roof_bow_light"
    roof_longitudinal: str = "roof_longitudinal_light"
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


@dataclass(frozen=True)
class WagonParams:
    wagon_type: str = "open_wagon"
    geometry: GeometryParams = field(default_factory=GeometryParams)
    layout: LayoutParams = field(default_factory=LayoutParams)
    openings: OpeningParams = field(default_factory=OpeningParams)
    sections: SectionAssignment = field(default_factory=SectionAssignment)
    loads: LoadParams = field(default_factory=LoadParams)
    supports: SupportParams = field(default_factory=SupportParams)


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


def wagon_params_from_dict(data: dict[str, Any]) -> WagonParams:
    geometry_raw = data.get("geometry", {})
    length = float(geometry_raw.get("length", GeometryParams.length))
    geometry = GeometryParams(
        length=length,
        width=float(geometry_raw.get("width", GeometryParams.width)),
        floor_y=float(geometry_raw.get("floor_y", GeometryParams.floor_y)),
        side_height=float(geometry_raw.get("side_height", GeometryParams.side_height)),
        roof_height=float(geometry_raw.get("roof_height", GeometryParams.roof_height)),
        bolster_positions=_tuple_float(geometry_raw.get("bolster_positions", GeometryParams.bolster_positions)),
        end_positions=tuple(
            float(v) for v in geometry_raw.get("end_positions", (0.0, length))
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
    )

    openings_raw = data.get("openings", {})
    doors = []
    for item in openings_raw.get("side_doors", []) or []:
        doors.append(
            SideDoor(
                x_start=float(item["x_start"]),
                x_end=float(item["x_end"]),
                z_side=str(item.get("z_side", "both")),
            )
        )
    openings = OpeningParams(side_doors=tuple(doors))

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
    )

    support_defaults = SupportParams()
    supports_raw = data.get("supports", {})
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
    )

    return WagonParams(
        wagon_type=str(data.get("wagon_type", "open_wagon")),
        geometry=geometry,
        layout=layout,
        openings=openings,
        sections=sections,
        loads=loads,
        supports=supports,
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
