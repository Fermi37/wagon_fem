from wagon_fem import ui
from wagon_fem import solver
import pytest

plotly = pytest.importorskip("plotly")


class DummyNode:
    def __init__(self, name, x, y, z):
        self.name = name
        self.X = x
        self.Y = y
        self.Z = z
        self.DX = {}
        self.DY = {}
        self.DZ = {}


class DummyMember:
    def __init__(self, name, i_node, j_node):
        self.name = name
        self.i_node = i_node
        self.j_node = j_node
        self._L = ((i_node.X - j_node.X) ** 2 + (i_node.Y - j_node.Y)
                   ** 2 + (i_node.Z - j_node.Z) ** 2) ** 0.5

    def L(self):
        return self._L

    def moment(self, label, pos):
        return 1.0


class DummyModel:
    def __init__(self):
        n1 = DummyNode('1', 0, 0, 0)
        n2 = DummyNode('2', 1000, 0, 0)
        m = DummyMember('M1', n1, n2)
        self.nodes = {'1': n1, '2': n2}
        self.members = {'M1': m}


def test_get_3d_figure_includes_customdata():
    model = DummyModel()
    fig = solver.get_3d_figure(model, prefer_plotly=True)
    # Ensure it's a plotly Figure and that at least one trace has customdata
    assert hasattr(fig, 'data')
    has_custom = any(getattr(t, 'customdata', None)
                     is not None for t in fig.data)
    assert has_custom


def test_on_3d_plot_click_highlights_member():
    model = DummyModel()
    # Simulate a Plotly click event payload selecting the member M1
    click_data = {'points': [{'customdata': 'MEM:M1'}]}
    new_fig, sel_text = ui.on_3d_plot_click(click_data, model)
    assert new_fig is not None
    assert 'M1' in sel_text
