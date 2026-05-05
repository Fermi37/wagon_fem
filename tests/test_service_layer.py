from pathlib import Path

import pandas as pd
import pytest

from wagon_fem.model import create_simply_supported_beam
from wagon_fem.services import AnalysisOptions, analyze_model, load_guide_markdown, prepare_ui_tables, render_legend_html, render_metric_reference_html
from wagon_fem.solver import get_moments_table, run_analysis


def test_get_moments_table_samples_member_end_at_physical_length():
    model = create_simply_supported_beam(L=4000.0, w=-10.0, support_type="clamped", n_segments=1)
    solved = run_analysis(model)

    member = list(solved.members.values())[0]
    expected_end = member.moment("Mz", member.L())

    table = get_moments_table(solved)

    assert table.loc[0, "Mz_end"] == expected_end


def test_prepare_ui_tables_populates_task_and_geometry_tables():
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))

    assert not tables.task_nodes.empty
    assert not tables.task_members.empty
    assert not tables.nodes.empty
    assert not tables.edges.empty
    assert "support_dx" in tables.task_nodes.columns
    assert "dist_dir" in tables.task_members.columns


def test_analyze_model_returns_expected_ui_payload_shape():
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))
    options = AnalysisOptions(result_metric="Mz")

    result = analyze_model(
        source=Path("data/wagon_frame.csv"),
        task_nodes=tables.task_nodes,
        task_members=tables.task_members,
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
    assert result.viewer_model_path is not None
    assert result.viewer_model_path.endswith(".gltf")
    assert Path(result.viewer_model_path).exists()
    assert result.viewer_legend["metric"] == "Mz"
    assert result.viewer_legend["entity_type"] == "member"
    assert result.viewer_legend["units"] == "N*mm"
    assert not hasattr(result, "viewer_summary")
    assert isinstance(result.task_nodes, pd.DataFrame)
    assert isinstance(result.task_members, pd.DataFrame)


@pytest.mark.parametrize(
    ("metric", "entity_type", "units"),
    [
        ("Mz", "member", "N*mm"),
        ("My", "member", "N*mm"),
        ("Axial", "member", "N"),
        ("Torque", "member", "N*mm"),
        ("Dx", "node", "mm"),
        ("Dy", "node", "mm"),
        ("Dz", "node", "mm"),
        ("RxnFY", "node", "N"),
        ("RxnMZ", "node", "N*mm"),
    ],
)
def test_supported_viewer_metrics_return_legend_data(metric, entity_type, units):
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))
    result = analyze_model(
        source=Path("data/wagon_frame.csv"),
        task_nodes=tables.task_nodes,
        task_members=tables.task_members,
        model_nodes=tables.nodes,
        model_edges=tables.edges,
        options=AnalysisOptions(result_metric=metric),
    )

    assert result.viewer_model_path.endswith(".gltf")
    assert result.viewer_legend["metric"] == metric
    assert result.viewer_legend["entity_type"] == entity_type
    assert result.viewer_legend["units"] == units
    assert "min" in result.viewer_legend
    assert "max" in result.viewer_legend


def test_none_metric_hides_numeric_scale():
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))
    result = analyze_model(
        source=Path("data/wagon_frame.csv"),
        task_nodes=tables.task_nodes,
        task_members=tables.task_members,
        model_nodes=tables.nodes,
        model_edges=tables.edges,
        options=AnalysisOptions(result_metric="None"),
    )

    assert result.viewer_legend["metric"] == "None"
    assert result.viewer_legend["scale_visible"] is False


def test_render_legend_html_contains_tick_labels():
    legend = {
        "metric": "Mz",
        "label": "Bending moment Mz",
        "units": "N*mm",
        "entity_type": "member",
        "min": -1200.0,
        "max": 3400.0,
        "scale_visible": True,
    }

    html = render_legend_html(legend, "viridis")

    assert "Legend" in html
    assert "min:" in html
    assert "max:" in html
    assert "ticks" in html.lower()
    assert "-1.2e+03" in html or "-1200" in html
    assert "3.4e+03" in html or "3400" in html
    assert "legend-overlay" in html
    assert "color:#000" in html


def test_render_metric_reference_html_contains_compact_metric_list():
    html = render_metric_reference_html()

    assert "Available metrics" in html
    assert "Mz" in html
    assert "Axial" in html
    assert "Dx" in html
    assert "RxnFY" in html


def test_task_node_validation_fails_for_missing_support_columns():
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))
    bad_task_nodes = tables.task_nodes.drop(columns=["support_dx"])

    with pytest.raises(ValueError, match="support_dx"):
        analyze_model(
            source=Path("data/wagon_frame.csv"),
            task_nodes=bad_task_nodes,
            task_members=tables.task_members,
            model_nodes=tables.nodes,
            model_edges=tables.edges,
            options=AnalysisOptions(),
        )


def test_guide_markdown_is_curated_not_aggregated():
    guide = load_guide_markdown()

    assert "## Workflow" in guide
    assert "## CSV Format" in guide
    assert "## Hugging Face Notes" in guide
    assert "overlay directly on top of the 3D viewer" in guide
    assert "README.md" not in guide
    assert "Settings" not in guide
    assert "под 3D viewer" in guide or "under the 3D viewer" in guide
