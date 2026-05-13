import math

from wagon_fem.model import FEModel3D
from wagon_fem.solver import get_displacements_table, run_analysis


def _cantilever_displacement(end_xyz, load_dir):
    model = FEModel3D()
    model.add_node("A", 0.0, 0.0, 0.0)
    model.add_node("B", *end_xyz)
    model.add_material("steel", 210000.0, 80769.230769, 0.3, 7850.0)
    model.add_section("asym", 5000.0, 1.0e6, 1.0e8, 1.0e5)
    model.add_member("M1", "A", "B", "steel", "asym")
    model.def_support("A", True, True, True, True, True, True)
    model.add_node_load("B", load_dir, -1000.0)
    run_analysis(model)
    table = get_displacements_table(model).set_index("Узел")
    row = table.loc["B"]
    return max(abs(float(row["Dx"])), abs(float(row["Dy"])), abs(float(row["Dz"])))


def test_local_axis_mini_models_solve_with_finite_displacements():
    cases = [
        ((1000.0, 0.0, 0.0), "FY"),
        ((0.0, 1000.0, 0.0), "FX"),
        ((0.0, 0.0, 1000.0), "FY"),
        ((1000.0, 300.0, 500.0), "FY"),
    ]

    for end_xyz, load_dir in cases:
        displacement = _cantilever_displacement(end_xyz, load_dir)
        assert math.isfinite(displacement)
        assert displacement > 0.0
