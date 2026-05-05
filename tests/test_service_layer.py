from pathlib import Path

import pandas as pd
import pytest

from wagon_fem.model import create_simply_supported_beam
from wagon_fem.services import AnalysisOptions, analyze_model, prepare_ui_tables
from wagon_fem.solver import get_3d_figure, get_moments_table, run_analysis


def test_get_moments_table_samples_member_end_at_physical_length():
    model = create_simply_supported_beam(L=4000.0, w=-10.0, support_type="clamped", n_segments=1)
    solved = run_analysis(model)

    member = list(solved.members.values())[0]
    expected_end = member.moment("Mz", member.L())

    table = get_moments_table(solved)

    assert table.loc[0, "Mz_end"] == expected_end


def test_prepare_ui_tables_populates_node_properties_and_geometry_tables():
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))

    assert not tables.node_properties.empty
    assert not tables.nodes.empty
    assert not tables.edges.empty
    assert "support_dx" in tables.node_properties.columns


def test_analyze_model_returns_expected_ui_payload_shape():
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))
    options = AnalysisOptions()

    result = analyze_model(
        source=Path("data/wagon_frame.csv"),
        node_properties=tables.node_properties,
        model_nodes=tables.nodes,
        model_edges=tables.edges,
        options=options,
    )

    assert "Расчет завершен" in result.status_text
    assert isinstance(result.moments_table, pd.DataFrame)
    assert isinstance(result.displacements_table, pd.DataFrame)
    assert result.moments_csv_path is not None
    assert result.displacements_csv_path is not None
    assert result.model_csv_path is not None
    assert result.viewer_figure is not None
    assert isinstance(result.node_properties, pd.DataFrame)


def test_highlighted_node_uses_distinct_color_and_size():
    pytest.importorskip("plotly")
    model = create_simply_supported_beam(L=2000.0, w=-5.0, support_type="clamped", n_segments=1)
    solved = run_analysis(model)

    fig = get_3d_figure(solved, prefer_plotly=True, highlight_node="1")
    node_trace = next(trace for trace in fig.data if getattr(trace, "name", "") == "nodes")

    assert node_trace.marker.color[0] != node_trace.marker.color[1]
    assert node_trace.marker.size[0] != node_trace.marker.size[1]
