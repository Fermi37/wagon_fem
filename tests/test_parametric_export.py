from wagon_fem.model import load_model_from_csv
from wagon_fem.parametric import build_open_wagon, export_model_csv, load_params, normalized_csv_hash


def test_exported_open_wagon_csv_loads_through_existing_loader(tmp_path):
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    frame = build_open_wagon(params)
    csv_path = export_model_csv(frame.nodes_df, frame.edges_df, tmp_path / "open.csv")

    model = load_model_from_csv(str(csv_path))

    assert len(model.nodes) == len(frame.nodes_df)
    assert len(model.members) == len(frame.edges_df)


def test_normalized_hash_is_stable_for_identical_generation():
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    first = build_open_wagon(params)
    second = build_open_wagon(params)

    assert normalized_csv_hash(first.nodes_df, first.edges_df) == normalized_csv_hash(second.nodes_df, second.edges_df)
