from pathlib import Path

import pandas as pd

from wagon_fem.parametric import build_covered_wagon, build_open_wagon, load_params, normalized_csv_hash


FIXTURE_DIR = Path("tests/fixtures/parametric")


def _read_combined_csv(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    lines = path.read_text(encoding="utf-8").splitlines()
    edge_header = next(
        idx for idx, line in enumerate(lines)
        if line.lower().startswith("edge_id") or "start_node" in line.lower()
    )
    nodes = pd.read_csv(path, nrows=edge_header - 1)
    edges = pd.read_csv(path, skiprows=edge_header)
    return nodes, edges


def test_open_wagon_golden_fixture_matches_normalized_export():
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    frame = build_open_wagon(params)
    fixture_nodes, fixture_edges = _read_combined_csv(FIXTURE_DIR / "open_wagon.csv")

    assert len(fixture_nodes) == 362
    assert len(fixture_edges) == 865
    assert set(["center_sill", "side_longitudinal", "diagonal_tie"]).issubset(set(fixture_edges["member_tag"]))
    assert normalized_csv_hash(frame.nodes_df, frame.edges_df) == (
        "9c2bf8c10c6a325a22246a6d258187dcbd743af537d6632d1d4cc7618c296901"
    )


def test_covered_wagon_golden_fixture_matches_normalized_export():
    params = load_params("docs/parametric_generator_v0_1_0/params.covered_wagon.example.yaml")
    frame = build_covered_wagon(params)
    fixture_nodes, fixture_edges = _read_combined_csv(FIXTURE_DIR / "covered_wagon.csv")

    assert len(fixture_nodes) == 388
    assert len(fixture_edges) == 980
    assert set(["roof_bow", "roof_longitudinal", "door_lintel"]).issubset(set(fixture_edges["member_tag"]))
    assert normalized_csv_hash(frame.nodes_df, frame.edges_df) == (
        "a3e9d65b8b017d05be76d7ceec717b17639618164c240c297bbfaf083d1378c0"
    )
