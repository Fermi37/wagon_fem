from __future__ import annotations

import argparse
from pathlib import Path

from .services import AnalysisOptions, analyze_model, prepare_ui_tables


def _parse_support_flags(raw: str) -> list[bool]:
    values = [item.strip().lower() for item in raw.split(",")]
    if len(values) != 6:
        raise ValueError("expected 6 support flags")
    return [value in {"1", "true", "yes", "y"} for value in values]


def main() -> None:
    parser = argparse.ArgumentParser(description="FEM расчет конструкции вагона")
    parser.add_argument("csv_file", type=str, help="Путь к CSV файлу модели")
    parser.add_argument(
        "--supports",
        type=str,
        nargs="*",
        default=[],
        help="Закрепления узлов в формате node_id:dx,dy,dz,rx,ry,rz",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        raise SystemExit(f"Ошибка: файл {csv_path} не найден.")

    tables = prepare_ui_tables(csv_path)
    node_props = tables.node_properties.copy()

    for support_def in args.supports:
        node_id_str, raw_flags = support_def.split(":", 1)
        flags = _parse_support_flags(raw_flags)
        node_mask = node_props["node_id"].astype(str) == node_id_str
        if not node_mask.any():
            raise SystemExit(f"Ошибка: узел {node_id_str} отсутствует в модели.")
        for column, value in zip(
            ["support_dx", "support_dy", "support_dz", "support_rx", "support_ry", "support_rz"],
            flags,
        ):
            node_props.loc[node_mask, column] = value

    result = analyze_model(
        source=csv_path,
        node_properties=node_props,
        model_nodes=tables.nodes,
        model_edges=tables.edges,
        options=AnalysisOptions(use_plotly=False),
    )

    print(result.status_text)
    print()
    print("Таблица моментов:")
    print(result.moments_table.to_string(index=False))
    print()
    print("Таблица перемещений:")
    print(result.displacements_table.to_string(index=False))


if __name__ == "__main__":
    main()
