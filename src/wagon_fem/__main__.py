"""Command-line entrypoint for wagon_fem package."""

import argparse
from pathlib import Path

from .loader import load_edges_from_csv
from .model import WagonModel
from .solver import solve_and_get_moments, print_results


def main() -> None:
    """Main entry point for the wagon-fem CLI."""
    parser = argparse.ArgumentParser(
        description="FEM расчет моментов в балках конструкции вагона"
    )
    parser.add_argument(
        "csv_file",
        type=str,
        help="Путь к CSV файлу с геометрией конструкции (ребра)",
    )
    parser.add_argument(
        "--supports",
        type=str,
        nargs="+",
        help="Закрепления узлов в формате node_id:dx,dy,dz,rx,ry,rz (например 1:True,False,True,False,False,False)",
        default=[],
    )

    args = parser.parse_args()

    # Загружаем геометрию из CSV
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Ошибка: Файл {csv_path} не найден")
        return

    print(f"Загрузка геометрии из {csv_path}...")
    edges = load_edges_from_csv(str(csv_path))
    print(f"Загружено {len(edges)} ребер")

    # Создаем модель
    model = WagonModel()
    model.from_edges(edges)
    print(f"Создано {len(model.nodes)} узлов и {len(model.elements)} элементов")

    # Применяем закрепления
    for support_def in args.supports:
        try:
            node_id_str, supports_str = support_def.split(":")
            node_id = int(node_id_str)
            supports = [s.strip().lower() == "true" for s in supports_str.split(",")]
            if len(supports) != 6:
                print(f"Ошибка: Для узла {node_id} указано {len(supports)} степеней свободы (ожидалось 6)")
                continue
            model.apply_support(node_id, *supports)
            print(f"Применено закрепление к узлу {node_id}: {supports}")
        except ValueError as e:
            print(f"Ошибка разбора закрепления '{support_def}': {e}")

    # Если закрепления не были указаны явно, применяем стандартные (опоры по углам)
    if not args.supports:
        # Находим минимальные и максимальные координаты для определения опор
        nodes_list = list(model.nodes.values())
        if nodes_list:
            # Закрепляем первые 4 узла как опоры (упрощенно)
            sorted_nodes = sorted(nodes_list, key=lambda n: (n.x, n.z))
            if len(sorted_nodes) >= 4:
                # Закрепляем 4 угловых узла
                for i, node in enumerate(sorted_nodes[:4]):
                    model.apply_support(node.id, dx=True, dy=True, dz=True, rx=False, ry=False, rz=False)
                    print(f"Автоматически закреплен узел {node.id} (DX, DY, DZ)")

    # Выполняем расчет
    print("\nВыполнение расчета...")
    results = solve_and_get_moments(model)

    # Выводим результаты
    print_results(results)


if __name__ == "__main__":
    main()
