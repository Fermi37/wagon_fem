import math

from wagon_fem.model import load_model_from_csv
from wagon_fem.parametric import build_open_wagon, export_model_csv, load_params
from wagon_fem.parametric.validation import graph_is_connected, validate_generated_frame
from wagon_fem.solver import get_displacements_table, get_moments_table, run_analysis


REQUIRED_OPEN_TAGS = {
    "center_sill",
    "side_longitudinal",
    "bolster_beam",
    "cross_beam",
    "side_post",
    "upper_belt",
    "diagonal_tie",
}


def test_open_wagon_contains_required_topology():
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    frame = build_open_wagon(params)

    assert not frame.nodes_df.empty
    assert not frame.edges_df.empty
    assert REQUIRED_OPEN_TAGS.issubset(set(frame.edges_df["member_tag"]))
    assert graph_is_connected(frame.nodes_df, frame.edges_df)
    assert validate_generated_frame(frame, REQUIRED_OPEN_TAGS) == []


def test_open_wagon_is_left_right_symmetric():
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    frame = build_open_wagon(params)
    coords = {
        (round(row.x, 6), round(row.y, 6), round(row.z, 6))
        for row in frame.nodes_df.itertuples(index=False)
    }

    for x, y, z in coords:
        if abs(z) > 1e-6:
            assert (x, y, round(-z, 6)) in coords


def test_open_wagon_vertical_slice_solves(tmp_path):
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    frame = build_open_wagon(params)
    csv_path = export_model_csv(frame.nodes_df, frame.edges_df, tmp_path / "open.csv")

    model = run_analysis(load_model_from_csv(str(csv_path)))
    moments = get_moments_table(model)
    displacements = get_displacements_table(model)

    assert not moments.empty
    assert not displacements.empty
    assert moments["Max_Mz"].map(math.isfinite).all()
    assert displacements[["Dx", "Dy", "Dz"]].map(math.isfinite).all().all()
