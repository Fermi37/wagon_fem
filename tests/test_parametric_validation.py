from wagon_fem.parametric import build_open_wagon, load_params
from wagon_fem.parametric.validation import topology_summary, validate_generated_frame


def test_validation_summary_contains_counts_tags_and_hash():
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    frame = build_open_wagon(params)
    summary = topology_summary(frame)

    assert summary["node_count"] == len(frame.nodes_df)
    assert summary["edge_count"] == len(frame.edges_df)
    assert "center_sill" in summary["member_tags"]
    assert len(summary["sha256"]) == 64
    assert validate_generated_frame(frame) == []
