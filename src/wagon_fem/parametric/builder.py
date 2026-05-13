from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import pandas as pd

from .grid import rounded_key
from .schemas import GeneratedFrame
from .sections import get_section


SUPPORT_COLUMNS = ["support_dx", "support_dy", "support_dz", "support_rx", "support_ry", "support_rz"]
NODE_LOAD_COLUMNS = ["fx", "fy", "fz", "mx", "my", "mz"]


@dataclass
class _NodeRecord:
    node_id: int
    x: float
    y: float
    z: float
    tags: set[str] = field(default_factory=set)
    supports: dict[str, bool] = field(default_factory=dict)
    loads: dict[str, float] = field(default_factory=dict)


@dataclass
class _EdgeRecord:
    edge_id: int
    start_node: int
    end_node: int
    member_tag: str
    section_tag: str
    tags: set[str]
    w: float | None = None
    w1: float | None = None
    w2: float | None = None
    dist_dir: str | None = None
    n_segments: int | None = None


class FrameBuilder:
    def __init__(self, tolerance: float = 1e-6) -> None:
        self.tolerance = tolerance
        self._nodes: dict[tuple[float, float, float], _NodeRecord] = {}
        self._node_by_id: dict[int, _NodeRecord] = {}
        self._edges: list[_EdgeRecord] = []
        self._member_keys: set[tuple[int, int, str]] = set()

    def add_node(self, x: float, y: float, z: float, tags: Iterable[str] = ()) -> int:
        key = (
            rounded_key(x, self.tolerance),
            rounded_key(y, self.tolerance),
            rounded_key(z, self.tolerance),
        )
        if key in self._nodes:
            record = self._nodes[key]
            record.tags.update(tags)
            return record.node_id
        node_id = len(self._nodes) + 1
        record = _NodeRecord(node_id=node_id, x=key[0], y=key[1], z=key[2], tags=set(tags))
        self._nodes[key] = record
        self._node_by_id[node_id] = record
        return node_id

    def set_support(self, node_id: int, dx: bool = False, dy: bool = False, dz: bool = False,
                    rx: bool = False, ry: bool = False, rz: bool = False) -> None:
        record = self._node_by_id[node_id]
        values = {
            "support_dx": dx,
            "support_dy": dy,
            "support_dz": dz,
            "support_rx": rx,
            "support_ry": ry,
            "support_rz": rz,
        }
        for key, value in values.items():
            record.supports[key] = bool(record.supports.get(key, False) or value)

    def add_node_load(self, node_id: int, **loads: float) -> None:
        record = self._node_by_id[node_id]
        for key, value in loads.items():
            if key in NODE_LOAD_COLUMNS:
                record.loads[key] = float(record.loads.get(key, 0.0) + value)

    def add_member(self, start_node: int, end_node: int, member_tag: str, section_tag: str,
                   tags: Iterable[str] = (), w: float | None = None, w1: float | None = None,
                   w2: float | None = None, dist_dir: str | None = None,
                   n_segments: int | None = None) -> int:
        if start_node == end_node:
            raise ValueError("Member endpoints must be different.")
        low, high = sorted((int(start_node), int(end_node)))
        key = (low, high, member_tag)
        if key in self._member_keys:
            raise ValueError(f"Duplicate member for nodes {low}-{high} and tag {member_tag}.")
        self._member_keys.add(key)
        edge_id = len(self._edges) + 1
        all_tags = set(tags)
        all_tags.add(member_tag)
        self._edges.append(
            _EdgeRecord(
                edge_id=edge_id,
                start_node=start_node,
                end_node=end_node,
                member_tag=member_tag,
                section_tag=section_tag,
                tags=all_tags,
                w=w,
                w1=w1,
                w2=w2,
                dist_dir=dist_dir,
                n_segments=n_segments,
            )
        )
        return edge_id

    def add_polyline(self, node_ids: list[int], member_tag: str, section_tag: str,
                     tags: Iterable[str] = (), **load_kwargs: object) -> list[int]:
        edge_ids = []
        for start, end in zip(node_ids, node_ids[1:]):
            if start != end:
                edge_ids.append(
                    self.add_member(start, end, member_tag, section_tag, tags=tags, **load_kwargs)
                )
        return edge_ids

    def build(self, metadata: dict[str, object] | None = None) -> GeneratedFrame:
        node_rows = []
        for record in sorted(self._node_by_id.values(), key=lambda item: item.node_id):
            row: dict[str, object] = {
                "node_id": record.node_id,
                "x": record.x,
                "y": record.y,
                "z": record.z,
            }
            for col in SUPPORT_COLUMNS:
                row[col] = bool(record.supports.get(col, False))
            for col in NODE_LOAD_COLUMNS:
                row[col] = float(record.loads.get(col, 0.0))
            node_rows.append(row)

        edge_rows = []
        for record in self._edges:
            section = get_section(record.section_tag)
            edge_rows.append(
                {
                    "edge_id": record.edge_id,
                    "start_node": record.start_node,
                    "end_node": record.end_node,
                    "E": section.E,
                    "Iy": section.Iy,
                    "Iz": section.Iz,
                    "J": section.J,
                    "A": section.A,
                    "w": record.w,
                    "w1": record.w1,
                    "w2": record.w2,
                    "dist_dir": record.dist_dir,
                    "section_tag": record.section_tag,
                    "member_tag": record.member_tag,
                    "n_segments": record.n_segments,
                }
            )

        nodes_df = pd.DataFrame(node_rows)
        edges_df = pd.DataFrame(edge_rows)
        node_tags = {record.node_id: set(record.tags) for record in self._node_by_id.values()}
        edge_tags = {record.edge_id: set(record.tags) for record in self._edges}
        return GeneratedFrame(nodes_df, edges_df, node_tags, edge_tags, metadata or {})
