"""Решатель для FEM расчета на основе Pynite."""

from typing import Dict, List, Tuple
from Pynite import FEModel3D

from .model import WagonModel


def solve_and_get_moments(model: WagonModel, load_cases: Dict = None) -> Dict:
    """
    Выполнить расчет модели и вернуть моменты в элементах.

    Args:
        model: Модель конструкции вагона
        load_cases: Словарь с нагрузками (по умолчанию - собственный вес)

    Returns:
        Словарь с результатами расчетов (моменты в узлах элементов)
    """
    # Создаем модель Pynite
    fe_model = FEModel3D()

    # Материал по умолчанию (сталь)
    E = 210e9  # Модуль упругости, Па
    G = 80e9   # Модуль сдвига, Па
    nu = 0.3   # Коэффициент Пуассона
    rho = 7850 # Плотность, кг/м³

    # Сечения по умолчанию (прямоугольное)
    A = 0.01      # Площадь сечения, м²
    Jz = 8.33e-6  # Момент инерции вокруг Z, м⁴
    Jy = 8.33e-6  # Момент инерции вокруг Y, м⁴
    Jx = 1.67e-5  # Полярный момент инерции, м⁴

    # Добавляем материал и сечение
    fe_model.add_material("steel", E, G, nu, rho)
    fe_model.add_section("default", A, Jy, Jz, Jx)

    # Добавляем узлы в модель Pynite
    for node in model.nodes.values():
        nx, ny, nz = node.x, node.y, node.z
        fe_model.add_node(str(node.id), nx, ny, nz)
        
        # Применяем закрепления
        support_dx, support_dy, support_dz, support_rx, support_ry, support_rz = node.support
        if any([support_dx, support_dy, support_dz, support_rx, support_ry, support_rz]):
            fe_model.def_support(
                str(node.id),
                support_DX=support_dx,
                support_DY=support_dy,
                support_DZ=support_dz,
                support_RX=support_rx,
                support_RY=support_ry,
                support_RZ=support_rz,
            )

    # Добавляем элементы (балки) в модель Pynite
    for elem in model.elements.values():
        elem_id = elem.id
        node_i = str(elem.node_i)
        node_j = str(elem.node_j)
        
        fe_model.add_member(
            name=elem_id,
            i_node=node_i,
            j_node=node_j,
            material_name="steel",
            section_name="default",
        )

    # Применяем нагрузки
    if load_cases is None:
        # Нагрузка по умолчанию - собственный вес (гравитация вниз по Y)
        g = 9.81  # ускорение свободного падения, м/с²
        for elem in model.elements.values():
            elem_id = elem.id
            # Распределенная нагрузка от собственного веса
            weight_per_meter = A * rho * g  # Н/м
            # Нагрузка направлена вниз (отрицательный глобальный Y)
            fe_model.add_member_dist_load(
                member_name=elem_id,
                direction="FY",
                w1=-weight_per_meter,
                w2=-weight_per_meter,
                case="Dead Load",
            )
    else:
        # Применяем пользовательские нагрузки
        for load_case, loads in load_cases.items():
            for load in loads:
                if load["type"] == "member_dist":
                    fe_model.add_member_dist_load(
                        member_name=load["member"],
                        direction=load["direction"],
                        w1=load["w1"],
                        w2=load["w2"],
                        case=load_case,
                    )
                elif load["type"] == "node_force":
                    fe_model.add_node_load(
                        node_name=load["node"],
                        direction=load["direction"],
                        force=load["force"],
                        case=load_case,
                    )

    # Анализируем модель
    fe_model.analyze(check_statics=True, check_stability=True)

    # Собираем результаты - моменты в элементах
    results = {}
    for elem in model.elements.values():
        elem_id = elem.id
        member = fe_model.members[elem_id]
        
        # Моменты на концах элемента (i-узел и j-узел)
        # Mz - изгибающий момент вокруг оси Z
        # My - изгибающий момент вокруг оси Y
        results[elem_id] = {
            "Mi_z": member.moment("Mz", 0),    # Момент Mz в начале элемента
            "Mj_z": member.moment("Mz", 1),    # Момент Mz в конце элемента
            "Mi_y": member.moment("My", 0),    # Момент My в начале элемента
            "Mj_y": member.moment("My", 1),    # Момент My в конце элемента
            "node_i": elem.node_i,
            "node_j": elem.node_j,
        }

    return results


def print_results(results: Dict):
    """Вывести результаты расчета в консоль."""
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ РАСЧЕТА МОМЕНТОВ В БАЛКАХ КОНСТРУКЦИИ ВАГОНА")
    print("=" * 80)
    print(f"\n{'Элемент':<15} {'Узлы':<15} {'Mi_z (Н·м)':<15} {'Mj_z (Н·м)':<15} {'Mi_y (Н·м)':<15} {'Mj_y (Н·м)':<15}")
    print("-" * 90)
    
    for elem_id, data in results.items():
        nodes = f"N{data['node_i']}-N{data['node_j']}"
        mi_z = f"{data['Mi_z']:>10.2f}"
        mj_z = f"{data['Mj_z']:>10.2f}"
        mi_y = f"{data['Mi_y']:>10.2f}"
        mj_y = f"{data['Mj_y']:>10.2f}"
        print(f"{elem_id:<15} {nodes:<15} {mi_z:<15} {mj_z:<15} {mi_y:<15} {mj_y:<15}")
    
    print("=" * 80)
    
    # Статистика
    all_mz = [abs(data["Mi_z"]) for data in results.values()] + [abs(data["Mj_z"]) for data in results.values()]
    all_my = [abs(data["Mi_y"]) for data in results.values()] + [abs(data["Mj_y"]) for data in results.values()]
    
    print(f"\nМаксимальный момент Mz: {max(all_mz):.2f} Н·м")
    print(f"Максимальный момент My: {max(all_my):.2f} Н·м")
    print("=" * 80 + "\n")
