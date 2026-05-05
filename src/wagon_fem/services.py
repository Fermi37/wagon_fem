from __future__ import annotations

import atexit
import base64
import io
import json
import logging
import math
import os
import shutil
import struct
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .model import create_simple_wagon_model, load_model_from_csv
from .solver import get_displacements_table, get_moments_table, run_analysis

logger = logging.getLogger(__name__)

DEFAULT_MODEL_RELATIVE_PATH = "data/wagon_frame.csv"


@dataclass(slots=True)
class AnalysisOptions:
    show_deformed: bool = True
    scale: float = 100.0
    apply_node_props: bool = True
    result_metric: str = "Mz"
    max_member_length: float = 0.0
    show_colorbar: bool = True
    colormap: str = "viridis"
    sample_resolution: int = 11
    viewer_format: str = "gltf"


@dataclass(slots=True)
class PreparedTables:
    task_nodes: pd.DataFrame
    task_members: pd.DataFrame
    nodes: pd.DataFrame
    edges: pd.DataFrame


@dataclass(slots=True)
class AnalysisResult:
    status_text: str
    moments_table: pd.DataFrame
    displacements_table: pd.DataFrame
    viewer_model_path: str | None
    viewer_legend: dict[str, Any]
    moments_csv_path: str | None
    displacements_csv_path: str | None
    model_csv_path: str | None
    task_nodes: pd.DataFrame
    task_members: pd.DataFrame
    model: Any


NODE_LOAD_COLUMNS = [
    "support_dx",
    "support_dy",
    "support_dz",
    "support_rx",
    "support_ry",
    "support_rz",
    "fx",
    "fy",
    "fz",
    "mx",
    "my",
    "mz",
]
TASK_NODE_COLUMNS = ["node_id"] + NODE_LOAD_COLUMNS
TASK_MEMBER_COLUMNS = ["edge_id", "w", "w1", "w2", "dist_dir"]
EDGE_LOAD_COLUMNS = ["w", "w1", "w2", "dist_dir", "dist_load_dir", "load_dir", "dir", "direction"]

RESULT_METRIC_SPECS: dict[str, dict[str, str]] = {
    "None": {"entity_type": "neutral", "units": "", "label": "Neutral"},
    "Mz": {"entity_type": "member", "units": "N*mm", "label": "Bending moment Mz"},
    "My": {"entity_type": "member", "units": "N*mm", "label": "Bending moment My"},
    "Axial": {"entity_type": "member", "units": "N", "label": "Axial force"},
    "Shear Fy": {"entity_type": "member", "units": "N", "label": "Shear force Fy"},
    "Shear Fz": {"entity_type": "member", "units": "N", "label": "Shear force Fz"},
    "Torque": {"entity_type": "member", "units": "N*mm", "label": "Torque"},
    "Dx": {"entity_type": "node", "units": "mm", "label": "Displacement Dx"},
    "Dy": {"entity_type": "node", "units": "mm", "label": "Displacement Dy"},
    "Dz": {"entity_type": "node", "units": "mm", "label": "Displacement Dz"},
    "Rx": {"entity_type": "node", "units": "rotation", "label": "Rotation Rx"},
    "Ry": {"entity_type": "node", "units": "rotation", "label": "Rotation Ry"},
    "Rz": {"entity_type": "node", "units": "rotation", "label": "Rotation Rz"},
    "RxnFX": {"entity_type": "node", "units": "N", "label": "Reaction force Fx"},
    "RxnFY": {"entity_type": "node", "units": "N", "label": "Reaction force Fy"},
    "RxnFZ": {"entity_type": "node", "units": "N", "label": "Reaction force Fz"},
    "RxnMX": {"entity_type": "node", "units": "N*mm", "label": "Reaction moment Mx"},
    "RxnMY": {"entity_type": "node", "units": "N*mm", "label": "Reaction moment My"},
    "RxnMZ": {"entity_type": "node", "units": "N*mm", "label": "Reaction moment Mz"},
}

COLORMAP_STOPS = {
    "viridis": ["#440154", "#482777", "#3f4a8a", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"],
    "plasma": ["#0d0887", "#46039f", "#7201a8", "#9c179e", "#bd3786", "#d8576b", "#ed7953", "#fb9f3a", "#fdca26", "#f0f921"],
    "inferno": ["#000004", "#1b0c41", "#4a0c6b", "#781c6d", "#a52c60", "#cf4446", "#ed6925", "#fb9b06", "#f7d13d", "#fcffa4"],
    "magma": ["#000004", "#180f3d", "#440f76", "#721f81", "#9e2f7f", "#cd4071", "#f1605d", "#fd9668", "#feca8d", "#fcfdbf"],
    "cividis": ["#00224e", "#123570", "#3b496c", "#575d6d", "#707173", "#8a8678", "#a59c74", "#c3b369", "#e1cc55", "#fee838"],
}

_TEMP_PATH_REGISTRY: list[tuple[str, float]] = []
_TEMP_REG_LOCK = threading.Lock()
_CLEANUP_INTERVAL = int(os.environ.get("WAGON_FEM_TEMP_CLEAN_INTERVAL", 60))
_CLEANUP_AGE = int(os.environ.get("WAGON_FEM_TEMP_MAX_AGE", 300))


def _register_temp_path(path: str | None) -> None:
    if not path:
        return
    with _TEMP_REG_LOCK:
        _TEMP_PATH_REGISTRY.append((path, time.time()))


def _remove_path(path: str) -> None:
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def _cleanup_once() -> None:
    now = time.time()
    stale: list[tuple[str, float]] = []
    with _TEMP_REG_LOCK:
        for item in list(_TEMP_PATH_REGISTRY):
            path, created_at = item
            if now - created_at >= _CLEANUP_AGE:
                try:
                    _remove_path(path)
                except Exception:
                    logger.debug("Failed to remove temp path %s", path, exc_info=True)
                stale.append(item)
        for item in stale:
            try:
                _TEMP_PATH_REGISTRY.remove(item)
            except ValueError:
                pass


def _cleanup_worker() -> None:
    while True:
        try:
            _cleanup_once()
        except Exception:
            logger.exception("Temp cleanup worker error")
        time.sleep(_CLEANUP_INTERVAL)


def _cleanup_all() -> None:
    with _TEMP_REG_LOCK:
        paths = list(_TEMP_PATH_REGISTRY)
        _TEMP_PATH_REGISTRY.clear()
    for path, _ in paths:
        try:
            _remove_path(path)
        except Exception:
            logger.debug("Failed to cleanup temp path %s", path, exc_info=True)


try:
    _cleanup_thread = threading.Thread(target=_cleanup_worker, daemon=True)
    _cleanup_thread.start()
except Exception:
    logger.debug("Failed to start temp cleanup thread", exc_info=True)

atexit.register(_cleanup_all)


def resolve_input_path(source: Any) -> str | None:
    if source is None:
        return None
    if isinstance(source, Path):
        return str(source)
    if isinstance(source, str):
        return source
    if isinstance(source, dict) and "name" in source:
        return source["name"]
    if hasattr(source, "name"):
        return str(source.name)
    if isinstance(source, (list, tuple)) and source:
        return resolve_input_path(source[0])
    return None


def _default_model_path() -> str | None:
    path = Path(__file__).resolve().parents[2] / DEFAULT_MODEL_RELATIVE_PATH
    return str(path) if path.exists() else None


def _coerce_dataframe(value: Any) -> pd.DataFrame:
    if value is None:
        return pd.DataFrame()
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame(value)


def _to_bool(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "x", "on"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    if value == "":
        return default
    return float(value)


def _nullable_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if value == "":
        return None
    return float(value)


def _detect_node_id_column(df: pd.DataFrame) -> str:
    if "node_id" in df.columns:
        return "node_id"
    if "id" in df.columns:
        return "id"
    raise ValueError("Node table must contain either 'node_id' or 'id'.")


def _detect_edge_id_column(df: pd.DataFrame) -> str:
    if "edge_id" in df.columns:
        return "edge_id"
    if "id" in df.columns:
        return "id"
    raise ValueError("Edge table must contain either 'edge_id' or 'id'.")


def validate_node_table(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("Node table is empty.")
    node_id_col = _detect_node_id_column(df)
    required = {node_id_col, "x", "y", "z"}
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Node table is missing required columns: {', '.join(sorted(missing))}.")


def validate_edge_table(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("Edge table is empty.")
    missing = [col for col in ("start_node", "end_node") if col not in df.columns]
    if missing:
        raise ValueError(f"Edge table is missing required columns: {', '.join(missing)}.")


def validate_task_nodes(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("Task node table is empty.")
    missing = [col for col in TASK_NODE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Task node table is missing required columns: {', '.join(missing)}.")


def validate_task_members(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("Task member table is empty.")
    missing = [col for col in TASK_MEMBER_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Task member table is missing required columns: {', '.join(missing)}.")


def prepare_model_tables(source: Any) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = resolve_input_path(source) or _default_model_path()
    if not path:
        return pd.DataFrame(), pd.DataFrame()

    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()

    edge_header_idx = None
    for idx, line in enumerate(lines):
        lowered = line.strip().lower()
        if lowered.startswith("edge_id") or "start_node" in lowered or "end_node" in lowered:
            edge_header_idx = idx
            break

    if edge_header_idx is None:
        return pd.read_csv(io.StringIO("".join(lines))), pd.DataFrame()

    nodes_df = pd.read_csv(io.StringIO("".join(lines[:edge_header_idx])))
    edges_df = pd.read_csv(io.StringIO("".join(lines[edge_header_idx:])))
    return nodes_df, edges_df


def _split_nodes_and_task_nodes(nodes_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if nodes_df.empty:
        return pd.DataFrame(), pd.DataFrame(columns=TASK_NODE_COLUMNS)

    validate_node_table(nodes_df)
    node_key = _detect_node_id_column(nodes_df)
    task_rows = []
    for _, row in nodes_df.iterrows():
        task_rows.append(
            {
                "node_id": row.get(node_key),
                "support_dx": _to_bool(row.get("support_dx")),
                "support_dy": _to_bool(row.get("support_dy")),
                "support_dz": _to_bool(row.get("support_dz")),
                "support_rx": _to_bool(row.get("support_rx")),
                "support_ry": _to_bool(row.get("support_ry")),
                "support_rz": _to_bool(row.get("support_rz")),
                "fx": _safe_float(row.get("fx")),
                "fy": _safe_float(row.get("fy")),
                "fz": _safe_float(row.get("fz")),
                "mx": _safe_float(row.get("mx")),
                "my": _safe_float(row.get("my")),
                "mz": _safe_float(row.get("mz")),
            }
        )
    geometry_nodes = nodes_df.drop(columns=[c for c in NODE_LOAD_COLUMNS if c in nodes_df.columns], errors="ignore").copy()
    return geometry_nodes, pd.DataFrame(task_rows, columns=TASK_NODE_COLUMNS)


def _split_edges_and_task_members(edges_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if edges_df.empty:
        return pd.DataFrame(), pd.DataFrame(columns=TASK_MEMBER_COLUMNS)

    validate_edge_table(edges_df)
    edge_key = _detect_edge_id_column(edges_df)
    task_rows = []
    for _, row in edges_df.iterrows():
        task_rows.append(
            {
                "edge_id": row.get(edge_key),
                "w": _nullable_float(row.get("w")),
                "w1": _nullable_float(row.get("w1")),
                "w2": _nullable_float(row.get("w2")),
                "dist_dir": row.get("dist_dir") or row.get("dir") or row.get("load_dir") or row.get("dist_load_dir") or "FY",
            }
        )
    geometry_edges = edges_df.drop(columns=[c for c in EDGE_LOAD_COLUMNS if c in edges_df.columns], errors="ignore").copy()
    return geometry_edges, pd.DataFrame(task_rows, columns=TASK_MEMBER_COLUMNS)


def prepare_ui_tables(source: Any) -> PreparedTables:
    raw_nodes, raw_edges = prepare_model_tables(source)
    nodes, task_nodes = _split_nodes_and_task_nodes(raw_nodes)
    edges, task_members = _split_edges_and_task_members(raw_edges)
    return PreparedTables(task_nodes=task_nodes, task_members=task_members, nodes=nodes, edges=edges)


def _merge_nodes_with_task_data(nodes_df: pd.DataFrame, task_nodes: pd.DataFrame) -> pd.DataFrame:
    merged_nodes = nodes_df.copy()
    if merged_nodes.empty:
        return merged_nodes
    validate_node_table(merged_nodes)
    validate_task_nodes(task_nodes)
    node_key = _detect_node_id_column(merged_nodes)
    task_frame = task_nodes.rename(columns={"node_id": node_key})[[node_key] + NODE_LOAD_COLUMNS].copy()
    merged_nodes = merged_nodes.drop(columns=[c for c in NODE_LOAD_COLUMNS if c in merged_nodes.columns], errors="ignore")
    return merged_nodes.merge(task_frame, on=node_key, how="left")


def _merge_edges_with_task_data(edges_df: pd.DataFrame, task_members: pd.DataFrame) -> pd.DataFrame:
    merged_edges = edges_df.copy()
    if merged_edges.empty:
        return merged_edges
    validate_edge_table(merged_edges)
    validate_task_members(task_members)
    edge_key = _detect_edge_id_column(merged_edges)
    task_frame = task_members.rename(columns={"edge_id": edge_key}).copy()
    merged_edges = merged_edges.drop(columns=[c for c in EDGE_LOAD_COLUMNS if c in merged_edges.columns], errors="ignore")
    return merged_edges.merge(task_frame, on=edge_key, how="left")


def save_model_csv(nodes_df: Any, edges_df: Any, task_nodes: Any = None, task_members: Any = None) -> str:
    nodes = _coerce_dataframe(nodes_df)
    edges = _coerce_dataframe(edges_df)
    task_nodes_df = _coerce_dataframe(task_nodes)
    task_members_df = _coerce_dataframe(task_members)

    if not nodes.empty:
        validate_node_table(nodes)
    if not edges.empty:
        validate_edge_table(edges)

    export_nodes = _merge_nodes_with_task_data(nodes, task_nodes_df) if not task_nodes_df.empty else nodes
    export_edges = _merge_edges_with_task_data(edges, task_members_df) if not task_members_df.empty else edges

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".modified.csv")
    with open(tmp.name, "w", encoding="utf-8") as handle:
        export_nodes.to_csv(handle, index=False)
        handle.write("\n")
        export_edges.to_csv(handle, index=False)
    _register_temp_path(tmp.name)
    return tmp.name


def _write_dataframe_csv(df: pd.DataFrame, suffix: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    df.to_csv(tmp.name, index=False)
    _register_temp_path(tmp.name)
    return tmp.name


def _pick_combo_value(mapping: Any, combo: str = "Combo 1") -> float:
    if mapping is None:
        return 0.0
    if isinstance(mapping, dict):
        if not mapping:
            return 0.0
        if combo in mapping:
            return float(mapping[combo])
        return float(next(iter(mapping.values())))
    return float(mapping)


def _resolve_member_points(member: Any, show_deformed: bool, scale: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    start = (member.i_node.X, member.i_node.Y, member.i_node.Z)
    end = (member.j_node.X, member.j_node.Y, member.j_node.Z)
    if not show_deformed:
        return start, end
    start = (
        start[0] + scale * _pick_combo_value(getattr(member.i_node, "DX", {})),
        start[1] + scale * _pick_combo_value(getattr(member.i_node, "DY", {})),
        start[2] + scale * _pick_combo_value(getattr(member.i_node, "DZ", {})),
    )
    end = (
        end[0] + scale * _pick_combo_value(getattr(member.j_node, "DX", {})),
        end[1] + scale * _pick_combo_value(getattr(member.j_node, "DY", {})),
        end[2] + scale * _pick_combo_value(getattr(member.j_node, "DZ", {})),
    )
    return start, end


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(v * v for v in vector))
    if length <= 1e-9:
        return (1.0, 0.0, 0.0)
    return tuple(v / length for v in vector)


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    color = hex_color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _interpolate_color(stops: list[str], t: float) -> tuple[float, float, float]:
    if len(stops) == 1:
        return _hex_to_rgb(stops[0])
    t = min(1.0, max(0.0, t))
    segments = len(stops) - 1
    idx = min(int(t * segments), segments - 1)
    local_t = (t * segments) - idx
    a = _hex_to_rgb(stops[idx])
    b = _hex_to_rgb(stops[idx + 1])
    return (
        a[0] + (b[0] - a[0]) * local_t,
        a[1] + (b[1] - a[1]) * local_t,
        a[2] + (b[2] - a[2]) * local_t,
    )


def _metric_color(value: float, min_value: float, max_value: float, colormap: str) -> tuple[float, float, float, float]:
    if max_value <= min_value:
        rgb = _interpolate_color(COLORMAP_STOPS.get(colormap, COLORMAP_STOPS["viridis"]), 0.5)
    else:
        rgb = _interpolate_color(COLORMAP_STOPS.get(colormap, COLORMAP_STOPS["viridis"]), (value - min_value) / (max_value - min_value))
    return (rgb[0], rgb[1], rgb[2], 1.0)


def _sample_positions(length: float, sample_resolution: int) -> list[float]:
    samples = max(2, int(sample_resolution))
    if length <= 0:
        return [0.0]
    return [i * (length / (samples - 1)) for i in range(samples)]


def _member_metric_value(member: Any, metric: str, sample_resolution: int) -> float:
    try:
        length = float(member.L())
    except Exception:
        length = 0.0
    values: list[float] = []
    for pos in _sample_positions(length, sample_resolution):
        try:
            if metric == "Mz":
                values.append(float(member.moment("Mz", pos)))
            elif metric == "My":
                values.append(float(member.moment("My", pos)))
            elif metric == "Axial":
                values.append(float(member.axial(pos)))
            elif metric == "Shear Fy":
                values.append(float(member.shear("Fy", pos)))
            elif metric == "Shear Fz":
                values.append(float(member.shear("Fz", pos)))
            elif metric == "Torque":
                values.append(float(member.torque(pos)))
        except Exception:
            continue
    if not values:
        return 0.0
    return max(values, key=lambda v: abs(v))


def _node_metric_value(node: Any, metric: str) -> float:
    return float(_pick_combo_value(getattr(node, metric, {})))


def _compute_metric_values(model: Any, metric: str, sample_resolution: int) -> tuple[dict[str, float], dict[str, Any]]:
    spec = RESULT_METRIC_SPECS[metric]
    entity_type = spec["entity_type"]
    if metric == "None":
        return {}, {
            "metric": "None",
            "label": spec["label"],
            "units": "",
            "entity_type": entity_type,
            "min": None,
            "max": None,
            "scale_visible": False,
        }

    if entity_type == "member":
        values = {str(member.name): _member_metric_value(member, metric, sample_resolution) for member in model.members.values()}
    else:
        values = {str(node.name): _node_metric_value(node, metric) for node in model.nodes.values()}

    numeric_values = list(values.values())
    min_value = min(numeric_values) if numeric_values else 0.0
    max_value = max(numeric_values) if numeric_values else 0.0
    return values, {
        "metric": metric,
        "label": spec["label"],
        "units": spec["units"],
        "entity_type": entity_type,
        "min": float(min_value),
        "max": float(max_value),
        "scale_visible": True,
    }


def _add_box(start: tuple[float, float, float], end: tuple[float, float, float], half_width: float) -> tuple[list[tuple[float, float, float]], list[int]]:
    direction = _normalize((end[0] - start[0], end[1] - start[1], end[2] - start[2]))
    helper = (0.0, 0.0, 1.0) if abs(direction[2]) < 0.95 else (0.0, 1.0, 0.0)
    u = _normalize(_cross(direction, helper))
    v = _normalize(_cross(direction, u))

    def offset(point: tuple[float, float, float], su: float, sv: float) -> tuple[float, float, float]:
        return (
            point[0] + su * half_width * u[0] + sv * half_width * v[0],
            point[1] + su * half_width * u[1] + sv * half_width * v[1],
            point[2] + su * half_width * u[2] + sv * half_width * v[2],
        )

    vertices = [
        offset(start, -1, -1),
        offset(start, 1, -1),
        offset(start, 1, 1),
        offset(start, -1, 1),
        offset(end, -1, -1),
        offset(end, 1, -1),
        offset(end, 1, 1),
        offset(end, -1, 1),
    ]
    indices = [
        0, 1, 2, 0, 2, 3,
        4, 6, 5, 4, 7, 6,
        0, 4, 5, 0, 5, 1,
        1, 5, 6, 1, 6, 2,
        2, 6, 7, 2, 7, 3,
        3, 7, 4, 3, 4, 0,
    ]
    return vertices, indices


def _add_cube(center: tuple[float, float, float], half_width: float) -> tuple[list[tuple[float, float, float]], list[int]]:
    x, y, z = center
    vertices = [
        (x - half_width, y - half_width, z - half_width),
        (x + half_width, y - half_width, z - half_width),
        (x + half_width, y + half_width, z - half_width),
        (x - half_width, y + half_width, z - half_width),
        (x - half_width, y - half_width, z + half_width),
        (x + half_width, y - half_width, z + half_width),
        (x + half_width, y + half_width, z + half_width),
        (x - half_width, y + half_width, z + half_width),
    ]
    indices = [
        0, 1, 2, 0, 2, 3,
        4, 6, 5, 4, 7, 6,
        0, 4, 5, 0, 5, 1,
        1, 5, 6, 1, 6, 2,
        2, 6, 7, 2, 7, 3,
        3, 7, 4, 3, 4, 0,
    ]
    return vertices, indices


def _append_primitive(gltf: dict[str, Any], vertices: list[tuple[float, float, float]], indices: list[int], color: tuple[float, float, float, float]) -> None:
    positions_blob = b"".join(struct.pack("<3f", *vertex) for vertex in vertices)
    indices_blob = b"".join(struct.pack("<I", index) for index in indices)
    combined_blob = positions_blob + indices_blob
    encoded = base64.b64encode(combined_blob).decode("ascii")

    buffer_index = len(gltf["buffers"])
    position_view_index = len(gltf["bufferViews"])
    index_view_index = position_view_index + 1
    position_accessor_index = len(gltf["accessors"])
    index_accessor_index = position_accessor_index + 1
    material_index = len(gltf["materials"])

    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]

    gltf["buffers"].append({
        "uri": f"data:application/octet-stream;base64,{encoded}",
        "byteLength": len(combined_blob),
    })
    gltf["bufferViews"].append({"buffer": buffer_index, "byteOffset": 0, "byteLength": len(positions_blob), "target": 34962})
    gltf["bufferViews"].append({"buffer": buffer_index, "byteOffset": len(positions_blob), "byteLength": len(indices_blob), "target": 34963})
    gltf["accessors"].append({
        "bufferView": position_view_index,
        "componentType": 5126,
        "count": len(vertices),
        "type": "VEC3",
        "min": [min(xs), min(ys), min(zs)],
        "max": [max(xs), max(ys), max(zs)],
    })
    gltf["accessors"].append({
        "bufferView": index_view_index,
        "componentType": 5125,
        "count": len(indices),
        "type": "SCALAR",
        "min": [min(indices) if indices else 0],
        "max": [max(indices) if indices else 0],
    })
    gltf["materials"].append({
        "pbrMetallicRoughness": {
            "baseColorFactor": [color[0], color[1], color[2], color[3]],
            "metallicFactor": 0.05,
            "roughnessFactor": 0.9,
        },
        "doubleSided": True,
    })
    gltf["meshes"][0]["primitives"].append({
        "attributes": {"POSITION": position_accessor_index},
        "indices": index_accessor_index,
        "mode": 4,
        "material": material_index,
    })


def build_model3d_asset(
    model: Any, *, show_deformed: bool, scale: float, result_metric: str, colormap: str, sample_resolution: int
) -> tuple[str, dict[str, Any]]:
    metric_values, legend = _compute_metric_values(model, result_metric, sample_resolution)
    gltf: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "wagon_fem"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "wagon-fem-model"}],
        "meshes": [{"primitives": []}],
        "materials": [],
        "buffers": [],
        "bufferViews": [],
        "accessors": [],
    }

    points = []
    for member in model.members.values():
        start, end = _resolve_member_points(member, show_deformed, scale)
        points.extend([start, end])
    if not points:
        points = [(0.0, 0.0, 0.0)]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)
    member_half_width = max(span * 0.01, 5.0)
    node_half_width = member_half_width * 1.4

    neutral_member = (0.58, 0.64, 0.74, 1.0)
    neutral_node = (0.82, 0.24, 0.24, 1.0)

    for member in model.members.values():
        start, end = _resolve_member_points(member, show_deformed, scale)
        vertices, indices = _add_box(start, end, member_half_width)
        if legend["entity_type"] == "member" and legend["scale_visible"]:
            color = _metric_color(metric_values.get(str(member.name), 0.0), legend["min"], legend["max"], colormap)
        else:
            color = neutral_member
        _append_primitive(gltf, vertices, indices, color)

    for node in model.nodes.values():
        point = (node.X, node.Y, node.Z)
        if show_deformed:
            point = (
                point[0] + scale * _pick_combo_value(getattr(node, "DX", {})),
                point[1] + scale * _pick_combo_value(getattr(node, "DY", {})),
                point[2] + scale * _pick_combo_value(getattr(node, "DZ", {})),
            )
        vertices, indices = _add_cube(point, node_half_width)
        if legend["entity_type"] == "node" and legend["scale_visible"]:
            color = _metric_color(metric_values.get(str(node.name), 0.0), legend["min"], legend["max"], colormap)
        else:
            color = neutral_node
        _append_primitive(gltf, vertices, indices, color)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".gltf", mode="w", encoding="utf-8")
    json.dump(gltf, tmp)
    tmp.flush()
    tmp.close()
    _register_temp_path(tmp.name)

    return tmp.name, legend


def render_legend_html(legend: dict[str, Any], colormap: str) -> str:
    if not legend.get("scale_visible", False):
        return (
            '<style>'
            '.legend-box,.legend-box *{color:#000 !important;opacity:1 !important;text-shadow:none !important;}'
            '</style>'
            '<div class="legend-box legend-overlay" '
            'style="border:1px solid #cfd8e3;padding:12px;border-radius:14px;'
            'background:rgba(255,255,255,0.96);color:#000;box-shadow:0 10px 24px rgba(15,23,42,0.14);">'
            '<strong style="color:#000;">Legend</strong><div style="color:#000;">Neutral rendering mode</div></div>'
        )

    stops = ", ".join(COLORMAP_STOPS.get(colormap, COLORMAP_STOPS["viridis"]))
    min_value = legend.get("min")
    max_value = legend.get("max")
    units = legend.get("units") or ""
    if min_value is None or max_value is None:
        tick_values = []
    elif max_value == min_value:
        tick_values = [min_value]
    else:
        tick_values = [min_value + (max_value - min_value) * frac for frac in (0.0, 0.25, 0.5, 0.75, 1.0)]
    tick_labels = "".join(
        f'<span style="flex:1;text-align:{align};padding:{padding};font-weight:600;color:#000 !important;opacity:1 !important;">{value:.3g}</span>'
        for value, align, padding in zip(
            tick_values,
            ["left", "center", "center", "center", "right"],
            ["0 10px 0 2px", "0 4px", "0 4px", "0 4px", "0 2px 0 10px"],
        )
    )
    return f'''
<style>
.legend-box,.legend-box * {{
  color:#000 !important;
  opacity:1 !important;
  text-shadow:none !important;
}}
</style>
<div class="legend-box legend-overlay" style="border:1px solid #cfd8e3;padding:14px 16px;border-radius:16px;background:rgba(255,255,255,0.96);max-width:460px;color:#000;box-shadow:0 10px 24px rgba(15,23,42,0.14);">
  <div style="font-weight:800;font-size:15px;margin-bottom:8px;color:#000 !important;">Legend</div>
  <div style="font-size:13px;font-weight:600;margin-bottom:10px;color:#000 !important;">{legend['label']} ({legend['entity_type']})</div>
  <div style="height:18px;border-radius:999px;background:linear-gradient(90deg, {stops});margin-bottom:8px;"></div>
  <div class="legend-ticks" style="display:flex;gap:0;font-size:12px;line-height:1.2;background:rgba(255,255,255,0.88);border-radius:10px;padding:6px 4px;margin-bottom:10px;color:#000 !important;">{tick_labels}</div>
  <div style="display:flex;justify-content:space-between;font-size:12px;font-weight:700;gap:12px;color:#000 !important;">
    <span style="padding-right:8px;">min: {min_value:.3g} {units}</span>
    <span style="padding-left:8px;text-align:right;">max: {max_value:.3g} {units}</span>
  </div>
</div>
'''


def render_viewer_payload(model: Any, options: AnalysisOptions) -> tuple[str | None, dict[str, Any]]:
    if model is None:
        return None, {
            "metric": "None",
            "label": "Neutral",
            "units": "",
            "entity_type": "neutral",
            "min": None,
            "max": None,
            "scale_visible": False,
        }

    viewer_model_path, viewer_legend = build_model3d_asset(
        model,
        show_deformed=options.show_deformed,
        scale=options.scale,
        result_metric=options.result_metric,
        colormap=options.colormap,
        sample_resolution=options.sample_resolution,
    )
    if not options.show_colorbar:
        viewer_legend = dict(viewer_legend)
        viewer_legend["scale_visible"] = False
    return viewer_model_path, viewer_legend


def render_metric_reference_html() -> str:
    rows = []
    for metric, spec in RESULT_METRIC_SPECS.items():
        if metric == "None":
            continue
        rows.append(
            f"<tr>"
            f"<td style='padding:4px 8px 4px 0;font-weight:700;color:#000 !important;opacity:1 !important;'>{metric}</td>"
            f"<td style='padding:4px 8px;color:#000 !important;opacity:1 !important;'>{spec['entity_type']}</td>"
            f"<td style='padding:4px 0;color:#000 !important;opacity:1 !important;'>{spec['units']}</td>"
            f"</tr>"
        )
    body = "".join(rows)
    return f'''
<style>
.metric-reference,.metric-reference * {{
  color:#000 !important;
  opacity:1 !important;
  text-shadow:none !important;
}}
</style>
<div class="metric-reference" style="border:1px solid #d8e0ea;border-radius:10px;padding:10px 12px;background:rgba(255,255,255,0.98);max-width:420px;color:#000 !important;">
  <div style="font-weight:800;margin-bottom:6px;color:#000 !important;">Available metrics</div>
  <table style="width:100%;border-collapse:collapse;font-size:12px;color:#000 !important;">
    <thead>
      <tr>
        <th style="text-align:left;padding:2px 8px 4px 0;color:#000 !important;font-weight:800;">Metric</th>
        <th style="text-align:left;padding:2px 8px 4px 0;color:#000 !important;font-weight:800;">Type</th>
        <th style="text-align:left;padding:2px 0 4px 0;color:#000 !important;font-weight:800;">Units</th>
      </tr>
    </thead>
    <tbody>{body}</tbody>
  </table>
</div>
'''


def load_guide_markdown() -> str:
    return """# Wagon FEM Guide

## Workflow

1. Upload a combined CSV file with nodes and edges.
2. Review geometry in **Construction Data**.
3. Review supports and loads in **Task Data**.
4. Open **3D Viewer** and use the controls under the 3D viewer to choose the result metric and rendering settings.
5. Run the analysis from **Main** and inspect the 3D model, tables, and CSV exports.

## Editor Tabs

- **Construction Data**: node coordinates and member properties.
- **Task Data**: node supports, nodal loads, and member distributed loads.
- **3D Viewer**: model, legend, metric switcher, and rendering settings.
- **Guide**: the single in-app reference for workflow and troubleshooting.

## CSV Format

- Node geometry columns: `node_id` or `id`, `x`, `y`, `z`.
- Task node columns: `support_dx`, `support_dy`, `support_dz`, `support_rx`, `support_ry`, `support_rz`, `fx`, `fy`, `fz`, `mx`, `my`, `mz`.
- Edge geometry columns: `edge_id` or `id`, `start_node`, `end_node`, `E`, `Iy`, `Iz`, `J`, `A`.
- Task member columns: `w`, `w1`, `w2`, `dist_dir`.

## 3D Metrics

Available metrics include bending moments, axial force, shear forces, torque, nodal displacements, nodal rotations, and support reactions.
The legend shows the active metric, the entity type, and the current min/max range.
The legend is shown as an overlay directly on top of the 3D viewer.

## Export Behavior

- The app exports moments and displacements as CSV.
- The app exports the merged geometry + task data model as CSV.
- The 3D viewer is served as a generated `.gltf` artifact for the Gradio `Model3D` component.

## Hugging Face Notes

- The viewer avoids Plotly and targets Gradio `Model3D` for better Spaces compatibility.
- Interactive picking is not required in this version.
- If the browser does not display the 3D scene, download the `.gltf` artifact and inspect the exported model locally.

## Troubleshooting

- If analysis fails, verify that node IDs referenced by edges exist in the node table.
- If supports or loads look wrong, check the **Task Data** tab instead of the geometry tables.
- If the 3D scene looks too large or too small, adjust the deformation scale in the controls under the 3D viewer before rerunning the analysis.
"""


def analyze_model(source: Any, task_nodes: Any, task_members: Any, model_nodes: Any, model_edges: Any, options: AnalysisOptions) -> AnalysisResult:
    nodes_df = _coerce_dataframe(model_nodes)
    edges_df = _coerce_dataframe(model_edges)
    task_nodes_df = _coerce_dataframe(task_nodes)
    task_members_df = _coerce_dataframe(task_members)

    effective_model_csv = None
    if not nodes_df.empty or not edges_df.empty:
        if nodes_df.empty or edges_df.empty:
            raise ValueError("Both node and edge tables are required when editing construction data.")
        validate_task_nodes(task_nodes_df)
        validate_task_members(task_members_df)
        effective_model_csv = save_model_csv(nodes_df, edges_df, task_nodes_df, task_members_df)
    else:
        source_path = resolve_input_path(source)
        if source_path:
            prepared = prepare_ui_tables(source_path)
            task_nodes_df = prepared.task_nodes if task_nodes_df.empty else task_nodes_df
            task_members_df = prepared.task_members if task_members_df.empty else task_members_df
            nodes_df = prepared.nodes
            edges_df = prepared.edges
            validate_task_nodes(task_nodes_df)
            validate_task_members(task_members_df)
            effective_model_csv = save_model_csv(nodes_df, edges_df, task_nodes_df, task_members_df)

    if effective_model_csv:
        model = load_model_from_csv(
            effective_model_csv,
            apply_node_props=options.apply_node_props,
            max_member_length=options.max_member_length,
        )
        normalized = prepare_ui_tables(effective_model_csv)
        task_nodes_out = normalized.task_nodes
        task_members_out = normalized.task_members
    else:
        model = create_simple_wagon_model()
        normalized = prepare_ui_tables(_default_model_path())
        task_nodes_out = normalized.task_nodes
        task_members_out = normalized.task_members

    solved_model = run_analysis(model)
    moments_table = get_moments_table(solved_model)
    displacements_table = get_displacements_table(solved_model)
    viewer_model_path, viewer_legend = render_viewer_payload(solved_model, options)

    max_mz = float(moments_table["Max_Mz"].max()) if not moments_table.empty and "Max_Mz" in moments_table.columns else 0.0
    status_text = (
        "Расчет завершен.\n"
        f"Всего элементов: {len(solved_model.members)}\n"
        f"Максимальный момент: {max_mz:.2f} Н*мм"
    )

    return AnalysisResult(
        status_text=status_text,
        moments_table=moments_table,
        displacements_table=displacements_table,
        viewer_model_path=viewer_model_path,
        viewer_legend=viewer_legend,
        moments_csv_path=_write_dataframe_csv(moments_table, ".moments.csv"),
        displacements_csv_path=_write_dataframe_csv(displacements_table, ".displacements.csv"),
        model_csv_path=effective_model_csv,
        task_nodes=task_nodes_out,
        task_members=task_members_out,
        model=solved_model,
    )
