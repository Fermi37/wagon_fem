from __future__ import annotations

import atexit
import io
import logging
import os
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .model import create_simple_wagon_model, load_model_from_csv
from .solver import get_3d_figure, get_displacements_table, get_moments_table, run_analysis

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AnalysisOptions:
    show_deformed: bool = True
    scale: float = 100.0
    apply_node_props: bool = True
    color_by: str = "Mz"
    max_member_length: float = 0.0
    show_colorbar: bool = True
    colormap: str = "viridis"
    sample_resolution: int = 11
    use_plotly: bool = True


@dataclass(slots=True)
class PreparedTables:
    node_properties: pd.DataFrame
    nodes: pd.DataFrame
    edges: pd.DataFrame


@dataclass(slots=True)
class AnalysisResult:
    status_text: str
    moments_table: pd.DataFrame
    displacements_table: pd.DataFrame
    viewer_figure: Any
    moments_csv_path: str | None
    displacements_csv_path: str | None
    model_csv_path: str | None
    node_properties: pd.DataFrame
    model: Any


NODE_PROPERTY_COLUMNS = [
    "node_id",
    "x",
    "y",
    "z",
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

SUPPORT_LOAD_COLUMNS = [
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

EDGE_COLUMNS = ["edge_id", "start_node", "end_node", "E", "Iy", "Iz", "J", "A", "w", "dist_dir"]

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
        first = source[0]
        return resolve_input_path(first)
    return None


def _default_model_path() -> str | None:
    path = Path(__file__).resolve().parents[2] / "data" / "wagon_frame.csv"
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


def _detect_node_id_column(df: pd.DataFrame) -> str:
    if "node_id" in df.columns:
        return "node_id"
    if "id" in df.columns:
        return "id"
    raise ValueError("Node table must contain either 'node_id' or 'id'.")


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
    if "start_node" not in df.columns or "end_node" not in df.columns:
        raise ValueError("Edge table must contain 'start_node' and 'end_node'.")


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
        nodes_df = pd.read_csv(io.StringIO("".join(lines)))
        return nodes_df, pd.DataFrame(columns=EDGE_COLUMNS)

    nodes_df = pd.read_csv(io.StringIO("".join(lines[:edge_header_idx])))
    edges_df = pd.read_csv(io.StringIO("".join(lines[edge_header_idx:])))
    return nodes_df, edges_df


def prepare_node_table(source: Any) -> pd.DataFrame:
    nodes_df, _ = prepare_model_tables(source)
    if nodes_df.empty:
        return pd.DataFrame(columns=NODE_PROPERTY_COLUMNS)

    node_id_col = "node_id" if "node_id" in nodes_df.columns else "id" if "id" in nodes_df.columns else None
    if node_id_col is None:
        return pd.DataFrame(columns=NODE_PROPERTY_COLUMNS)

    rows = []
    for _, row in nodes_df.iterrows():
        entry = {
            "node_id": row.get(node_id_col),
            "x": row.get("x"),
            "y": row.get("y"),
            "z": row.get("z"),
            "support_dx": _to_bool(row.get("support_dx")),
            "support_dy": _to_bool(row.get("support_dy")),
            "support_dz": _to_bool(row.get("support_dz")),
            "support_rx": _to_bool(row.get("support_rx")),
            "support_ry": _to_bool(row.get("support_ry")),
            "support_rz": _to_bool(row.get("support_rz")),
            "fx": float(row.get("fx", 0.0) or 0.0),
            "fy": float(row.get("fy", 0.0) or 0.0),
            "fz": float(row.get("fz", 0.0) or 0.0),
            "mx": float(row.get("mx", 0.0) or 0.0),
            "my": float(row.get("my", 0.0) or 0.0),
            "mz": float(row.get("mz", 0.0) or 0.0),
        }
        rows.append(entry)
    return pd.DataFrame(rows, columns=NODE_PROPERTY_COLUMNS)


def prepare_ui_tables(source: Any) -> PreparedTables:
    nodes_df, edges_df = prepare_model_tables(source)
    node_props = prepare_node_table(source)
    return PreparedTables(node_properties=node_props, nodes=nodes_df, edges=edges_df)


def save_model_csv(nodes_df: Any, edges_df: Any, node_properties: Any = None) -> str:
    nodes = _coerce_dataframe(nodes_df)
    edges = _coerce_dataframe(edges_df)
    node_props = _coerce_dataframe(node_properties)

    if not nodes.empty:
        validate_node_table(nodes)
    if not edges.empty:
        validate_edge_table(edges)

    export_nodes = nodes.copy()
    if not node_props.empty:
        validate_node_table(node_props.rename(columns={"node_id": "id"}) if "node_id" in node_props.columns and "node_id" not in nodes.columns and "id" in nodes.columns else node_props)
        node_key = "node_id" if "node_id" in export_nodes.columns else "id"
        prop_key = _detect_node_id_column(node_props)
        prop_frame = node_props.rename(columns={prop_key: node_key}).copy()
        prop_frame = prop_frame[[node_key] + SUPPORT_LOAD_COLUMNS]
        export_nodes = export_nodes.drop(columns=[c for c in SUPPORT_LOAD_COLUMNS if c in export_nodes.columns], errors="ignore")
        export_nodes = export_nodes.merge(prop_frame, on=node_key, how="left")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".modified.csv")
    with open(tmp.name, "w", encoding="utf-8") as handle:
        export_nodes.to_csv(handle, index=False)
        handle.write("\n")
        edges.to_csv(handle, index=False)
    _register_temp_path(tmp.name)
    return tmp.name


def _write_dataframe_csv(df: pd.DataFrame, suffix: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    df.to_csv(tmp.name, index=False)
    _register_temp_path(tmp.name)
    return tmp.name


def _model_to_node_properties(model: Any) -> pd.DataFrame:
    rows = []
    for node in model.nodes.values():
        rows.append(
            {
                "node_id": node.name,
                "x": node.X,
                "y": node.Y,
                "z": node.Z,
                "support_dx": False,
                "support_dy": False,
                "support_dz": False,
                "support_rx": False,
                "support_ry": False,
                "support_rz": False,
                "fx": 0.0,
                "fy": 0.0,
                "fz": 0.0,
                "mx": 0.0,
                "my": 0.0,
                "mz": 0.0,
            }
        )
    return pd.DataFrame(rows, columns=NODE_PROPERTY_COLUMNS)


def load_documentation() -> str:
    parts = []
    base = Path(__file__).resolve().parents[2]
    for path in [base / "README.md", base / "docs" / "index.md", base / "docs" / "usage.md", base / "docs" / "api.md"]:
        if path.exists():
            parts.append(f"## {path.name}\n\n{path.read_text(encoding='utf-8')}")
    if not parts:
        return "Документация не найдена в репозитории."
    return "\n\n---\n\n".join(parts)


def analyze_model(
    source: Any,
    node_properties: Any,
    model_nodes: Any,
    model_edges: Any,
    options: AnalysisOptions,
) -> AnalysisResult:
    nodes_df = _coerce_dataframe(model_nodes)
    edges_df = _coerce_dataframe(model_edges)
    node_props_df = _coerce_dataframe(node_properties)

    effective_model_csv = None
    if not nodes_df.empty or not edges_df.empty:
        if nodes_df.empty or edges_df.empty:
            raise ValueError("Both node and edge tables are required when editing construction data.")
        effective_model_csv = save_model_csv(nodes_df, edges_df, node_props_df)
    else:
        source_path = resolve_input_path(source)
        if source_path:
            loaded_nodes, loaded_edges = prepare_model_tables(source_path)
            effective_model_csv = save_model_csv(loaded_nodes, loaded_edges, node_props_df)

    if effective_model_csv:
        model = load_model_from_csv(
            effective_model_csv,
            apply_node_props=options.apply_node_props,
            max_member_length=options.max_member_length,
        )
        node_props_out = prepare_node_table(effective_model_csv)
    else:
        model = create_simple_wagon_model()
        node_props_out = _model_to_node_properties(model)

    solved_model = run_analysis(model)
    moments_table = get_moments_table(solved_model)
    displacements_table = get_displacements_table(solved_model)
    viewer_figure = get_3d_figure(
        solved_model,
        deformed=options.show_deformed,
        scale=options.scale,
        color_by=options.color_by,
        sample_resolution=max(3, int(options.sample_resolution)),
        colormap=options.colormap,
        show_colorbar=options.show_colorbar,
        prefer_plotly=options.use_plotly,
    )

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
        viewer_figure=viewer_figure,
        moments_csv_path=_write_dataframe_csv(moments_table, ".moments.csv"),
        displacements_csv_path=_write_dataframe_csv(displacements_table, ".displacements.csv"),
        model_csv_path=effective_model_csv,
        node_properties=node_props_out,
        model=solved_model,
    )
