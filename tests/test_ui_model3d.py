from pathlib import Path

from wagon_fem import ui
from wagon_fem.services import AnalysisOptions, analyze_model, prepare_ui_tables


def test_load_tables_for_ui_returns_geometry_and_task_tables():
    task_nodes, task_members, nodes, edges = ui.load_tables_for_ui(Path("data/wagon_frame.csv"))

    assert len(task_nodes) > 0
    assert len(task_members) > 0
    assert len(nodes) > 0
    assert len(edges) > 0


def test_run_analysis_for_ui_returns_model3d_payload():
    tables = prepare_ui_tables(Path("data/wagon_frame.csv"))

    outputs = ui.run_analysis_for_ui(
        Path("data/wagon_frame.csv"),
        True,
        100.0,
        True,
        "Mz",
        0.0,
        tables.task_nodes,
        tables.task_members,
        True,
        "viridis",
        11,
        tables.nodes,
        tables.edges,
    )

    viewer_model_path = outputs[1]
    assert viewer_model_path.endswith(".gltf")
    assert Path(viewer_model_path).exists()
    legend_html = outputs[2]
    assert "legend" in legend_html.lower()
    assert "Mz" in legend_html
    assert "ticks" in legend_html.lower()
    assert "legend-overlay" in legend_html
    assert "color:#000" in legend_html


def test_ui_module_exposes_viewer_metric_choices():
    assert "Mz" in ui.RESULT_METRIC_CHOICES
    assert "Axial" in ui.RESULT_METRIC_CHOICES
    assert "Dx" in ui.RESULT_METRIC_CHOICES
    assert "RxnFY" in ui.RESULT_METRIC_CHOICES

def test_ui_module_exposes_metric_reference_html():
    assert "Available metrics" in ui.METRIC_REFERENCE_HTML
    assert "Mz" in ui.METRIC_REFERENCE_HTML
    assert "RxnMY" in ui.METRIC_REFERENCE_HTML


def test_ui_module_uses_overlay_css_and_no_viewer_summary():
    assert "#viewer-legend" in ui.APP_CSS
    assert "position: absolute" in ui.APP_CSS
    assert "Viewer summary" not in Path(ui.__file__).read_text(encoding="utf-8")
