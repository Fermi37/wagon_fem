"""Модель конструкции вагона для FEM расчета."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import numpy as np

from .loader import Edge


@dataclass
class Node:
    """Узел конструкции."""

    id: int
    x: float
    y: float
    z: float
    support: Tuple[bool, bool, bool, bool, bool, bool] = field(
        default_factory=lambda: (False, False, False, False, False, False)
    )
    # support: (DX, DY, DZ, RX, RY, RZ) - закрепления по степеням свободы


@dataclass
class BeamElement:
    """Балочный элемент Pynite."""

    id: str
    node_i: int
    node_j: int
    material: str
    section: str


class WagonModel:
    """Модель конструкции кузова вагона."""

    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.elements: Dict[str, BeamElement] = {}
        self.edges: List[Edge] = []

    def add_node(
        self,
        node_id: int,
        x: float,
        y: float,
        z: float,
        support: Tuple[bool, bool, bool, bool, bool, bool] = None,
    ):
        """Добавить узел в модель."""
        if support is None:
            support = (False, False, False, False, False, False)
        self.nodes[node_id] = Node(node_id, x, y, z, support)

    def add_element(self, elem_id: str, node_i: int, node_j: int, material: str = "steel", section: str = "default"):
        """Добавить балочный элемент в модель."""
        self.elements[elem_id] = BeamElement(elem_id, node_i, node_j, material, section)

    def from_edges(self, edges: List[Edge]):
        """
        Создать модель из списка ребер.

        Автоматически создает узлы и элементы на основе ребер.
        """
        self.edges = edges
        unique_nodes = set()

        for edge in edges:
            # Добавляем узлы
            if edge.node_i not in unique_nodes:
                self.add_node(edge.node_i, edge.x_i, edge.y_i, edge.z_i)
                unique_nodes.add(edge.node_i)
            if edge.node_j not in unique_nodes:
                self.add_node(edge.node_j, edge.x_j, edge.y_j, edge.z_j)
                unique_nodes.add(edge.node_j)

            # Добавляем элемент
            elem_id = f"E{edge.node_i}_{edge.node_j}"
            self.add_element(elem_id, edge.node_i, edge.node_j, edge.material, edge.section)

    def apply_support(self, node_id: int, dx=False, dy=False, dz=False, rx=False, ry=False, rz=False):
        """Применить закрепление к узлу."""
        if node_id in self.nodes:
            self.nodes[node_id].support = (dx, dy, dz, rx, ry, rz)

    def get_unique_nodes(self) -> List[Tuple[int, float, float, float]]:
        """Вернуть список уникальных узлов (id, x, y, z)."""
        return [(n.id, n.x, n.y, n.z) for n in self.nodes.values()]

    def get_elements(self) -> List[BeamElement]:
        """Вернуть список элементов."""
        return list(self.elements.values())
