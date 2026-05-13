from dataclasses import replace

import pytest

from wagon_fem.model import load_model_from_csv
from wagon_fem.parametric import build_open_wagon, export_model_csv, load_params
from wagon_fem.parametric.schemas import SupportParams
from wagon_fem.solver import get_displacements_table, run_analysis


@pytest.mark.parametrize(
    "scheme",
    ["two_bolster_reference", "four_point_vertical", "solver_stability_clamped_reference"],
)
def test_named_support_schemes_solve_with_finite_displacements(tmp_path, scheme):
    base = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    params = replace(base, supports=replace(base.supports, scheme=scheme))
    frame = build_open_wagon(params)
    csv_path = export_model_csv(frame.nodes_df, frame.edges_df, tmp_path / f"{scheme}.csv")

    model = run_analysis(load_model_from_csv(str(csv_path)))
    displacements = get_displacements_table(model)

    assert displacements[["Dx", "Dy", "Dz"]].notna().all().all()


def test_support_scheme_is_recorded_in_metadata():
    base = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    params = replace(base, supports=SupportParams(scheme="four_point_vertical"))
    frame = build_open_wagon(params)

    assert frame.metadata["support_scheme"] == "four_point_vertical"
