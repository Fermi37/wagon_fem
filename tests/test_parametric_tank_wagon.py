import math

from wagon_fem.model import load_model_from_csv
from wagon_fem.parametric import build_tank_wagon, export_model_csv, load_params, normalized_csv_hash
from wagon_fem.parametric.tank_wagon import TANK_REQUIRED_TAGS
from wagon_fem.parametric.validation import validate_generated_frame
from wagon_fem.solver import get_displacements_table, run_analysis


def test_tank_wagon_generates_valid_frame():
    params = load_params("docs/parametric_generator_v0_3_0/params.tank_wagon.example.yaml")
    frame = build_tank_wagon(params)

    assert validate_generated_frame(frame, required_tags=TANK_REQUIRED_TAGS) == []
    assert set(TANK_REQUIRED_TAGS).issubset(set(frame.edges_df["member_tag"]))
    assert frame.metadata["wagon_type"] == "tank_wagon"


def test_tank_wagon_ring_and_load_invariants():
    params = load_params("docs/parametric_generator_v0_3_0/params.tank_wagon.example.yaml")
    frame = build_tank_wagon(params)
    tank_nodes = frame.nodes_df[
        (frame.nodes_df["x"] >= params.tank.x_start)
        & (frame.nodes_df["x"] <= params.tank.x_end)
        & ((frame.nodes_df["y"] - params.tank.center_y).abs() <= params.tank.radius + 1e-6)
    ]

    assert len(frame.metadata["tank_angles_deg"]) == params.tank.angular_divisions
    assert "tank_end_ring" in set(frame.edges_df["member_tag"])
    assert not tank_nodes.empty
    assert math.isclose(
        frame.nodes_df["fy"].sum(),
        params.loads.tank_self_weight.total_force + params.loads.payload.total_force,
        rel_tol=0.0,
        abs_tol=1e-6,
    )


def test_tank_wagon_generation_is_deterministic():
    params = load_params("docs/parametric_generator_v0_3_0/params.tank_wagon.example.yaml")
    first = build_tank_wagon(params)
    second = build_tank_wagon(params)

    assert normalized_csv_hash(first.nodes_df, first.edges_df) == normalized_csv_hash(
        second.nodes_df,
        second.edges_df,
    )


def test_tank_wagon_golden_hash():
    params = load_params("docs/parametric_generator_v0_3_0/params.tank_wagon.example.yaml")
    frame = build_tank_wagon(params)

    assert len(frame.nodes_df) == 239
    assert len(frame.edges_df) == 440
    assert normalized_csv_hash(frame.nodes_df, frame.edges_df) == (
        "4703b6f391daf81ebf7616556f5011090a707530b4cdac0796b60496db5d0ff1"
    )


def test_tank_wagon_solver_smoke(tmp_path):
    params = load_params("docs/parametric_generator_v0_3_0/params.tank_wagon.example.yaml")
    frame = build_tank_wagon(params)
    csv_path = export_model_csv(frame.nodes_df, frame.edges_df, tmp_path / "tank_wagon.csv")

    solved = run_analysis(load_model_from_csv(str(csv_path)))
    displacements = get_displacements_table(solved)

    assert not displacements.empty
    assert displacements[["Dx", "Dy", "Dz"]].map(math.isfinite).all().all()
