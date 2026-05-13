import pytest

from wagon_fem.parametric.builder import FrameBuilder
from wagon_fem.parametric.grid import floor_z_lines, height_lines, pitch_coordinates


def test_frame_builder_merges_duplicate_nodes_by_coordinate():
    builder = FrameBuilder()

    first = builder.add_node(0.0, 0.0, 0.0, tags=("a",))
    second = builder.add_node(0.0, 0.0, 0.0, tags=("b",))
    frame = builder.build()

    assert first == second
    assert len(frame.nodes_df) == 1
    assert frame.node_tags[first] == {"a", "b"}


def test_frame_builder_rejects_duplicate_member_with_same_tag():
    builder = FrameBuilder()
    n1 = builder.add_node(0.0, 0.0, 0.0)
    n2 = builder.add_node(1.0, 0.0, 0.0)

    builder.add_member(n1, n2, "center_sill", "center_sill_heavy")

    with pytest.raises(ValueError, match="Duplicate member"):
        builder.add_member(n2, n1, "center_sill", "center_sill_heavy")


def test_grid_helpers_are_deterministic():
    assert pitch_coordinates(0.0, 2500.0, 1000.0) == [0.0, 1000.0, 2000.0, 2500.0]
    assert height_lines(0.0, 2000.0, 4) == [0.0, 500.0, 1000.0, 1500.0, 2000.0]
    assert floor_z_lines(3000.0, 1) == [-1500.0, -750.0, 0.0, 750.0, 1500.0]
