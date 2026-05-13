from dataclasses import replace

from wagon_fem.parametric import build_covered_wagon, load_params
from wagon_fem.parametric.schemas import OpeningParams, SideDoor
from wagon_fem.parametric.validation import validate_generated_frame


def _covered_params():
    base = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")
    return replace(
        base,
        wagon_type="covered_wagon",
        openings=OpeningParams(side_doors=(SideDoor(x_start=5000.0, x_end=7000.0),)),
    )


def test_covered_wagon_contains_roof_and_door_members():
    frame = build_covered_wagon(_covered_params())
    tags = set(frame.edges_df["member_tag"])

    assert {"roof_bow", "roof_longitudinal", "door_post", "door_lintel", "door_threshold"}.issubset(tags)
    assert validate_generated_frame(frame) == []


def test_covered_wagon_omits_wall_panel_members_inside_door_opening():
    frame = build_covered_wagon(_covered_params())
    nodes = frame.nodes_df.set_index("node_id")

    for edge in frame.edges_df.itertuples(index=False):
        if edge.member_tag not in {"horizontal_belt", "diagonal_tie"}:
            continue
        a = nodes.loc[edge.start_node]
        b = nodes.loc[edge.end_node]
        if abs(a.z) == 1560.0 and abs(b.z) == 1560.0:
            midpoint_x = 0.5 * (float(a.x) + float(b.x))
            assert not (5000.0 <= midpoint_x <= 7000.0)
