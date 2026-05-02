"""Загрузка геометрии конструкции из CSV файла."""

import csv
from dataclasses import dataclass
from typing import List


@dataclass
class Edge:
    """Ребро конструкции - соединение двух узлов."""

    node_i: int  # номер начального узла
    node_j: int  # номер конечного узла
    x_i: float  # координата X начального узла
    y_i: float  # координата Y начального узла
    z_i: float  # координата Z начального узла
    x_j: float  # координата X конечного узла
    y_j: float  # координата Y конечного узла
    z_j: float  # координата Z конечного узла
    material: str = "steel"  # материал по умолчанию
    section: str = "default"  # сечение по умолчанию


def load_edges_from_csv(filepath: str) -> List[Edge]:
    """
    Загрузить список ребер из CSV файла.

    Формат CSV:
    node_i,node_j,x_i,y_i,z_i,x_j,y_j,z_j,material,section

    Args:
        filepath: Путь к CSV файлу

    Returns:
        Список объектов Edge
    """
    edges = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            edge = Edge(
                node_i=int(row["node_i"]),
                node_j=int(row["node_j"]),
                x_i=float(row["x_i"]),
                y_i=float(row["y_i"]),
                z_i=float(row["z_i"]),
                x_j=float(row["x_j"]),
                y_j=float(row["y_j"]),
                z_j=float(row["z_j"]),
                material=row.get("material", "steel"),
                section=row.get("section", "default"),
            )
            edges.append(edge)
    return edges
