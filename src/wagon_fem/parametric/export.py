from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

NODE_COLUMNS = [
    "node_id", "x", "y", "z",
    "support_dx", "support_dy", "support_dz", "support_rx", "support_ry", "support_rz",
    "fx", "fy", "fz", "mx", "my", "mz",
]
EDGE_COLUMNS = [
    "edge_id", "start_node", "end_node", "E", "Iy", "Iz", "J", "A",
    "w", "w1", "w2", "dist_dir", "section_tag", "member_tag", "n_segments",
]


def normalize_nodes(nodes_df: pd.DataFrame, decimals: int = 6) -> pd.DataFrame:
    result = nodes_df.copy()
    for col in NODE_COLUMNS:
        if col not in result.columns:
            result[col] = False if col.startswith("support_") else 0.0
    result = result[NODE_COLUMNS].sort_values("node_id").reset_index(drop=True)
    for col in ("x", "y", "z", "fx", "fy", "fz", "mx", "my", "mz"):
        result[col] = result[col].astype(float).round(decimals)
    return result


def normalize_edges(edges_df: pd.DataFrame, decimals: int = 6) -> pd.DataFrame:
    result = edges_df.copy()
    for col in EDGE_COLUMNS:
        if col not in result.columns:
            result[col] = None
    result = result[EDGE_COLUMNS].sort_values("edge_id").reset_index(drop=True)
    for col in ("E", "Iy", "Iz", "J", "A", "w", "w1", "w2"):
        result[col] = pd.to_numeric(result[col], errors="coerce").round(decimals)
    return result


def combined_csv_text(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> str:
    nodes = normalize_nodes(nodes_df)
    edges = normalize_edges(edges_df)
    return nodes.to_csv(index=False, lineterminator="\n") + edges.to_csv(index=False, lineterminator="\n")


def export_model_csv(nodes_df: pd.DataFrame, edges_df: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(combined_csv_text(nodes_df, edges_df), encoding="utf-8")
    return path


def normalized_csv_hash(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> str:
    text = combined_csv_text(nodes_df, edges_df)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
