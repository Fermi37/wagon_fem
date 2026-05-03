"""Basic tests for wagon_fem."""

from wagon_fem.model import create_simple_wagon_model


def test_create_model():
    model = create_simple_wagon_model()
    assert len(model.nodes) > 0
    assert len(model.members) > 0
