from __future__ import annotations

import logging
import os
from typing import Any

import gradio as gr

from .services import (
    AnalysisOptions,
    analyze_model,
    load_guide_markdown,
    prepare_ui_tables,
    render_legend_html,
    render_metric_reference_html,
    render_viewer_payload,
    save_model_csv,
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

APP_CSS = """
#viewer-shell {
  position: relative;
}

#viewer-shell .gr-model3d {
  min-height: 520px;
}

#viewer-legend {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 20;
  max-width: min(460px, calc(100% - 36px));
  pointer-events: none;
}

#viewer-legend .legend-box {
  color: #000 !important;
}
"""

RESULT_METRIC_CHOICES = [
    "Mz",
    "My",
    "Axial",
    "Shear Fy",
    "Shear Fz",
    "Torque",
    "Dx",
    "Dy",
    "Dz",
    "Rx",
    "Ry",
    "Rz",
    "RxnFX",
    "RxnFY",
    "RxnFZ",
    "RxnMX",
    "RxnMY",
    "RxnMZ",
    "None",
]
METRIC_REFERENCE_HTML = render_metric_reference_html()


def load_tables_for_ui(source: Any) -> tuple[Any, Any, Any, Any]:
    tables = prepare_ui_tables(source)
    return tables.task_nodes, tables.task_members, tables.nodes, tables.edges


def run_analysis_for_ui(
    source: Any,
    show_deformed: bool,
    scale: float,
    apply_node_props: bool,
    result_metric: str,
    max_member_length: float,
    task_nodes: Any,
    task_members: Any,
    show_colorbar: bool,
    colormap: str,
    sample_resolution: int,
    model_nodes: Any,
    model_edges: Any,
):
    options = AnalysisOptions(
        show_deformed=show_deformed,
        scale=scale,
        apply_node_props=apply_node_props,
        result_metric=result_metric,
        max_member_length=max_member_length,
        show_colorbar=show_colorbar,
        colormap=colormap,
        sample_resolution=sample_resolution,
    )
    result = analyze_model(
        source=source,
        task_nodes=task_nodes,
        task_members=task_members,
        model_nodes=model_nodes,
        model_edges=model_edges,
        options=options,
    )
    return (
        result.status_text,
        result.viewer_model_path,
        render_legend_html(result.viewer_legend, colormap),
        result.moments_table,
        result.displacements_table,
        result.moments_csv_path,
        result.displacements_csv_path,
        result.model_csv_path,
        result.task_nodes,
        result.task_members,
        result.model,
    )


def update_viewer_for_ui(
    model: Any,
    show_deformed: bool,
    scale: float,
    result_metric: str,
    show_colorbar: bool,
    colormap: str,
    sample_resolution: int,
):
    options = AnalysisOptions(
        show_deformed=show_deformed,
        scale=scale,
        result_metric=result_metric,
        show_colorbar=show_colorbar,
        colormap=colormap,
        sample_resolution=sample_resolution,
    )
    viewer_model_path, viewer_legend = render_viewer_payload(model, options)
    return viewer_model_path, render_legend_html(viewer_legend, colormap)


def build_demo() -> gr.Blocks:
    default_tables = prepare_ui_tables(None)
    with gr.Blocks(title="Wagon FEM Analysis", css=APP_CSS) as demo:
        gr.Markdown("# Wagon FEM Analysis")
        gr.Markdown("Upload geometry, review task data, run the solver, and inspect exports.")

        with gr.Tabs():
            with gr.Tab("Main"):
                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(label="Upload model CSV")
                        run_button = gr.Button("Run analysis", variant="primary")
                        output_text = gr.Textbox(label="Solver status", lines=4)
                    with gr.Column(scale=1):
                        export_moments_file = gr.File(label="Moments CSV")
                        export_disp_file = gr.File(label="Displacements CSV")
                        export_model_file = gr.File(label="Merged model CSV")

            with gr.Tab("Construction Data"):
                model_nodes_table = gr.DataFrame(value=default_tables.nodes, label="Nodes", interactive=True)
                model_edges_table = gr.DataFrame(value=default_tables.edges, label="Edges", interactive=True)
                save_model_button = gr.Button("Save merged CSV")

            with gr.Tab("Task Data"):
                task_nodes_table = gr.DataFrame(value=default_tables.task_nodes, label="Node supports and nodal loads", interactive=True)
                task_members_table = gr.DataFrame(value=default_tables.task_members, label="Member distributed loads", interactive=True)

            with gr.Tab("3D Viewer"):
                with gr.Group(elem_id="viewer-shell"):
                    viewer_model = gr.Model3D(
                        label="3D structure",
                        clear_color=(0.97, 0.98, 1.0, 1.0),
                        height=520,
                    )
                    legend_html = gr.HTML(label="Legend", elem_id="viewer-legend")
                with gr.Group():
                    gr.Markdown("### Viewer controls")
                    result_metric_dd = gr.Dropdown(choices=RESULT_METRIC_CHOICES, value="Mz", label="Calculated parameter")
                    show_deformed_ck = gr.Checkbox(label="Show deformed geometry", value=True)
                    scale_slider = gr.Slider(0.0, 1000.0, value=100.0, step=1.0, label="Deformation scale")
                    max_elem_len = gr.Slider(0.0, 20000.0, value=0.0, step=100.0, label="Maximum member length (mm)")
                    colormap_dd = gr.Dropdown(
                        choices=["viridis", "plasma", "inferno", "magma", "cividis"],
                        value="viridis",
                        label="Color map",
                    )
                    sample_res = gr.Slider(3, 101, value=11, step=1, label="Sampling resolution")
                    apply_node_props_ck = gr.Checkbox(label="Apply task data from editor", value=True)
                    show_colorbar_ck = gr.Checkbox(label="Show numeric legend", value=True)

            with gr.Tab("Results"):
                table_moments = gr.DataFrame(label="Moments table")
                table_disp = gr.DataFrame(label="Displacements table")

            with gr.Tab("Guide"):
                gr.Markdown(load_guide_markdown())
                gr.HTML(value=METRIC_REFERENCE_HTML, label="Available metrics")

        model_state = gr.State()

        file_input.change(
            fn=load_tables_for_ui,
            inputs=[file_input],
            outputs=[task_nodes_table, task_members_table, model_nodes_table, model_edges_table],
        )

        run_button.click(
            fn=run_analysis_for_ui,
            inputs=[
                file_input,
                show_deformed_ck,
                scale_slider,
                apply_node_props_ck,
                result_metric_dd,
                max_elem_len,
                task_nodes_table,
                task_members_table,
                show_colorbar_ck,
                colormap_dd,
                sample_res,
                model_nodes_table,
                model_edges_table,
            ],
            outputs=[
                output_text,
                viewer_model,
                legend_html,
                table_moments,
                table_disp,
                export_moments_file,
                export_disp_file,
                export_model_file,
                task_nodes_table,
                task_members_table,
                model_state,
            ],
            api_name="run_analysis",
            show_progress="full",
            queue=True,
            concurrency_limit=1,
        )

        save_model_button.click(
            fn=save_model_csv,
            inputs=[model_nodes_table, model_edges_table, task_nodes_table, task_members_table],
            outputs=[export_model_file],
            queue=False,
        )

        viewer_controls = [
            show_deformed_ck,
            scale_slider,
            result_metric_dd,
            show_colorbar_ck,
            colormap_dd,
            sample_res,
        ]
        for component in viewer_controls:
            component.change(
                fn=update_viewer_for_ui,
                inputs=[
                    model_state,
                    show_deformed_ck,
                    scale_slider,
                    result_metric_dd,
                    show_colorbar_ck,
                    colormap_dd,
                    sample_res,
                ],
                outputs=[viewer_model, legend_html],
                queue=False,
            )
    return demo


demo = build_demo()


def main():
    host = os.environ.get("WAGON_FEM_HOST", os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"))
    port = int(os.environ.get("WAGON_FEM_PORT", os.environ.get("PORT", 7860)))
    share = os.environ.get("WAGON_FEM_SHARE", os.environ.get("GRADIO_SHARE", "false")).lower() in {
        "1",
        "true",
        "yes",
        "y",
    }

    try:
        demo.queue()
    except Exception:
        logger.debug("demo.queue() not available; continuing without global queue")

    demo.launch(server_name=host, server_port=port, share=share)


if __name__ == "__main__":
    main()
