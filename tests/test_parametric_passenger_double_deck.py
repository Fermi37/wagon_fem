from wagon_fem.parametric import build_passenger_double_deck, load_params, normalized_csv_hash
from wagon_fem.parametric.passenger_common import PASSENGER_DOUBLE_DECK_TAGS
from wagon_fem.parametric.validation import validate_generated_frame


def test_passenger_double_deck_generates_valid_frame():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_double_deck.example.yaml")
    frame = build_passenger_double_deck(params)

    assert validate_generated_frame(frame, required_tags=PASSENGER_DOUBLE_DECK_TAGS) == []
    assert set(PASSENGER_DOUBLE_DECK_TAGS).issubset(set(frame.edges_df["member_tag"]))
    assert frame.metadata["wagon_type"] == "passenger_double_deck"


def test_passenger_double_deck_has_interdeck_and_lowered_floor_levels():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_double_deck.example.yaml")
    frame = build_passenger_double_deck(params)

    assert "interdeck_cross_beam" in set(frame.edges_df["member_tag"])
    assert "interdeck_longitudinal" in set(frame.edges_df["member_tag"])
    assert params.levels.lower_floor_y in set(frame.nodes_df["y"])


def test_passenger_double_deck_generation_is_deterministic():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_double_deck.example.yaml")
    first = build_passenger_double_deck(params)
    second = build_passenger_double_deck(params)

    assert normalized_csv_hash(first.nodes_df, first.edges_df) == normalized_csv_hash(
        second.nodes_df,
        second.edges_df,
    )


def test_passenger_double_deck_golden_hash():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_double_deck.example.yaml")
    frame = build_passenger_double_deck(params)

    assert len(frame.nodes_df) == 3393
    assert len(frame.edges_df) == 6327
    assert normalized_csv_hash(frame.nodes_df, frame.edges_df) == (
        "e8bf6542036c0d03f8dd88e037b46c5a414c7d8e15282ca9d2722b9de3a92a58"
    )
