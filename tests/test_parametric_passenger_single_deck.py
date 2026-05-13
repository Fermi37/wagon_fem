from wagon_fem.parametric import build_passenger_single_deck, load_params, normalized_csv_hash
from wagon_fem.parametric.passenger_common import PASSENGER_SINGLE_DECK_TAGS
from wagon_fem.parametric.validation import validate_generated_frame


def test_passenger_single_deck_generates_valid_frame():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml")
    frame = build_passenger_single_deck(params)

    assert validate_generated_frame(frame, required_tags=PASSENGER_SINGLE_DECK_TAGS) == []
    assert set(PASSENGER_SINGLE_DECK_TAGS).issubset(set(frame.edges_df["member_tag"]))
    assert frame.metadata["wagon_type"] == "passenger_single_deck"


def test_passenger_single_deck_generation_is_deterministic():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml")
    first = build_passenger_single_deck(params)
    second = build_passenger_single_deck(params)

    assert normalized_csv_hash(first.nodes_df, first.edges_df) == normalized_csv_hash(
        second.nodes_df,
        second.edges_df,
    )


def test_passenger_single_deck_golden_hash():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml")
    frame = build_passenger_single_deck(params)

    assert len(frame.nodes_df) == 2502
    assert len(frame.edges_df) == 4580
    assert normalized_csv_hash(frame.nodes_df, frame.edges_df) == (
        "3acb96982056baf6fcf0af472390f66d9069f8c2712baf6ecbcdea48e0065e63"
    )
