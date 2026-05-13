from wagon_fem.parametric import load_params
from wagon_fem.parametric.schemas import wagon_params_from_dict
from wagon_fem.parametric.sections import FIRST_STAGE_CATALOG, get_section


def test_load_open_wagon_yaml_params():
    params = load_params("docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml")

    assert params.wagon_type == "open_wagon"
    assert params.geometry.length == 13920.0
    assert params.geometry.bolster_positions == (1850.0, 12070.0)
    assert params.layout.side_height_divisions == 4
    assert params.loads.vertical_distributed_load.enabled is True


def test_params_from_dict_uses_defaults():
    params = wagon_params_from_dict({"wagon_type": "covered_wagon"})

    assert params.wagon_type == "covered_wagon"
    assert params.geometry.width == 3120.0
    assert params.sections.center_sill == "center_sill_heavy"


def test_first_stage_catalog_contains_expected_center_sill():
    section = get_section("center_sill_heavy")

    assert section.E == 210000.0
    assert section.A == 18000.0
    assert "diagonal_tie_equiv" in FIRST_STAGE_CATALOG


def test_load_passenger_yaml_params():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml")

    assert params.wagon_type == "passenger_single_deck"
    assert params.levels.window_sill_y == 1100.0
    assert len(params.openings.side_windows[0].expanded()) == 8
    assert params.supports.support_points[0].flags.dy is True


def test_passenger_section_tags_resolve():
    params = load_params("docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml")

    for field_name in params.sections.__dataclass_fields__:
        tag = getattr(params.sections, field_name)
        if isinstance(tag, str) and field_name != "catalog":
            get_section(tag)
