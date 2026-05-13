from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from .export import normalized_csv_hash
from .schemas import GeneratedFrame


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def _edge_pairs(edges_df: pd.DataFrame) -> Iterable[tuple[int, int]]:
    for row in edges_df.itertuples(index=False):
        yield int(getattr(row, "start_node")), int(getattr(row, "end_node"))


def graph_is_connected(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> bool:
    if nodes_df.empty:
        return False
    node_ids = {int(v) for v in nodes_df["node_id"]}
    if not node_ids:
        return False
    adjacency = {node_id: set() for node_id in node_ids}
    for start, end in _edge_pairs(edges_df):
        if start in adjacency and end in adjacency:
            adjacency[start].add(end)
            adjacency[end].add(start)
    seen = set()
    stack = [next(iter(node_ids))]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency[node] - seen)
    return seen == node_ids


def validate_generated_frame(frame: GeneratedFrame, required_tags: set[str] | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    nodes = frame.nodes_df
    edges = frame.edges_df

    if nodes["node_id"].duplicated().any():
        issues.append(ValidationIssue("duplicate_nodes", "Node identifiers must be unique."))
    if edges["edge_id"].duplicated().any():
        issues.append(ValidationIssue("duplicate_edges", "Edge identifiers must be unique."))

    node_ids = set(nodes["node_id"].astype(int).tolist())
    for row in edges.itertuples(index=False):
        if int(row.start_node) not in node_ids or int(row.end_node) not in node_ids:
            issues.append(ValidationIssue("missing_node_reference", f"Edge {row.edge_id} references a missing node."))

    node_lookup = nodes.set_index("node_id")[["x", "y", "z"]].to_dict("index")
    duplicate_keys: set[tuple[int, int, str]] = set()
    seen_keys: set[tuple[int, int, str]] = set()
    for row in edges.itertuples(index=False):
        start = int(row.start_node)
        end = int(row.end_node)
        if start in node_lookup and end in node_lookup:
            a = node_lookup[start]
            b = node_lookup[end]
            length = math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))
            if length <= 0.0:
                issues.append(ValidationIssue("zero_length_member", f"Edge {row.edge_id} has zero length."))
        key = (*sorted((start, end)), str(row.member_tag))
        if key in seen_keys:
            duplicate_keys.add(key)
        seen_keys.add(key)
    if duplicate_keys:
        issues.append(ValidationIssue("duplicate_members", "Duplicate members exist for the same node pair and tag."))

    if not graph_is_connected(nodes, edges):
        issues.append(ValidationIssue("disconnected_graph", "Generated member graph must be connected."))

    if required_tags:
        present = set(edges["member_tag"].dropna().astype(str).tolist())
        missing = required_tags - present
        if missing:
            issues.append(ValidationIssue("missing_tags", f"Missing structural tags: {sorted(missing)}."))

    return issues


def assert_valid_generated_frame(frame: GeneratedFrame, required_tags: set[str] | None = None) -> None:
    issues = validate_generated_frame(frame, required_tags)
    if issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(details)


def topology_summary(frame: GeneratedFrame) -> dict[str, object]:
    return {
        "node_count": int(len(frame.nodes_df)),
        "edge_count": int(len(frame.edges_df)),
        "member_tags": sorted(frame.edges_df["member_tag"].dropna().astype(str).unique().tolist()),
        "sha256": normalized_csv_hash(frame.nodes_df, frame.edges_df),
    }


def write_validation_report(frame: GeneratedFrame, output_path: str | Path, required_tags: set[str] | None = None) -> Path:
    issues = validate_generated_frame(frame, required_tags)
    summary = topology_summary(frame)
    lines = [
        "# Parametric Generator Validation Report",
        "",
        f"- Nodes: {summary['node_count']}",
        f"- Members: {summary['edge_count']}",
        f"- SHA-256: `{summary['sha256']}`",
        f"- Tags: {', '.join(summary['member_tags'])}",
        "",
        "## Issues",
    ]
    if issues:
        lines.extend(f"- `{issue.code}`: {issue.message}" for issue in issues)
    else:
        lines.append("- None")
    path = Path(output_path)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
