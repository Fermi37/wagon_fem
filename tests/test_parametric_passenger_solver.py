import math

from wagon_fem.model import load_model_from_csv
from wagon_fem.parametric import (
    build_passenger_double_deck,
    build_passenger_single_deck,
    export_model_csv,
    load_params,
)
from wagon_fem.solver import get_displacements_table, run_analysis


def _assert_passenger_model_solves(tmp_path, params_path, builder, name):
    params = load_params(params_path)
    frame = builder(params)
    csv_path = export_model_csv(frame.nodes_df, frame.edges_df, tmp_path / f"{name}.csv")

    solved = run_analysis(load_model_from_csv(str(csv_path)))
    displacements = get_displacements_table(solved)

    assert not displacements.empty
    assert displacements[["Dx", "Dy", "Dz"]].map(math.isfinite).all().all()


def test_passenger_single_deck_solver_smoke(tmp_path):
    _assert_passenger_model_solves(
        tmp_path,
        "docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml",
        build_passenger_single_deck,
        "passenger_single_deck",
    )


def test_passenger_double_deck_solver_smoke(tmp_path):
    _assert_passenger_model_solves(
        tmp_path,
        "docs/parametric_generator_v0_2_0/params.passenger_double_deck.example.yaml",
        build_passenger_double_deck,
        "passenger_double_deck",
    )
