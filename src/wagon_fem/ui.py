from __future__ import annotations

import logging
import os
from typing import Any

import gradio as gr

from .services import AnalysisOptions, analyze_model, load_documentation, prepare_ui_tables, save_model_csv
from .solver import get_3d_figure

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def load_tables_for_ui(source: Any) -> tuple[Any, Any, Any]:
    tables = prepare_ui_tables(source)
    return tables.node_properties, tables.nodes, tables.edges


def run_analysis_for_ui(
    source: Any,
    show_deformed: bool,
    scale: float,
    apply_node_props: bool,
    color_by: str,
    max_member_length: float,
    node_props: Any,
    show_colorbar: bool,
    colormap: str,
    sample_resolution: int,
    use_plotly: bool,
    model_nodes: Any,
    model_edges: Any,
):
    options = AnalysisOptions(
        show_deformed=show_deformed,
        scale=scale,
        apply_node_props=apply_node_props,
        color_by=color_by,
        max_member_length=max_member_length,
        show_colorbar=show_colorbar,
        colormap=colormap,
        sample_resolution=sample_resolution,
        use_plotly=use_plotly,
    )
    result = analyze_model(
        source=source,
        node_properties=node_props,
        model_nodes=model_nodes,
        model_edges=model_edges,
        options=options,
    )
    return (
        result.status_text,
        result.moments_table,
        result.displacements_table,
        result.viewer_figure,
        result.moments_csv_path,
        result.displacements_csv_path,
        result.model_csv_path,
        result.node_properties,
        result.model,
    )


def on_3d_plot_click(evt, model):
    try:
        if not evt:
            return None, "No selection"
        points = evt.get("points") if isinstance(evt, dict) else None
    except Exception:
        points = None

    if not points or model is None:
        return None, "No selection"

    point = points[0]
    customdata = point.get("customdata") if isinstance(point, dict) else None
    custom_value = customdata[0] if isinstance(customdata, (list, tuple)) else customdata

    selection_type = None
    selection_id = None
    if isinstance(custom_value, str):
        if custom_value.startswith("MEM:"):
            selection_type = "member"
            selection_id = custom_value.split(":", 1)[1]
        elif custom_value.startswith("NODE:"):
            selection_type = "node"
            selection_id = custom_value.split(":", 1)[1]

    if selection_id is None:
        return None, "Selection not recognized"

    if selection_type == "member":
        figure = get_3d_figure(model, prefer_plotly=True, highlight_member=selection_id)
        return figure, f"Selected member: {selection_id}"

    figure = get_3d_figure(model, prefer_plotly=True, highlight_node=selection_id)
    return figure, f"Selected node: {selection_id}"


default_tables = prepare_ui_tables(None)

with gr.Blocks(title="Wagon FEM Analysis") as demo:
    gr.Markdown("# Wagon FEM Analysis")

    with gr.Tabs():
        with gr.Tab("Main"):
            with gr.Row():
                with gr.Column():
                    file_input = gr.File(label="Загрузить CSV модели")
                    run_button = gr.Button("Выполнить расчет", variant="primary")
                with gr.Column():
                    output_text = gr.Textbox(label="Статус расчета", lines=4)
                    selection_info = gr.Textbox(label="Selection", interactive=False)

        with gr.Tab("Node Properties"):
            node_props_table = gr.DataFrame(
                value=default_tables.node_properties,
                label="Node supports and loads",
                interactive=True,
            )

        with gr.Tab("Construction Data"):
            model_nodes_table = gr.DataFrame(
                value=default_tables.nodes,
                label="Nodes",
                interactive=True,
            )
            model_edges_table = gr.DataFrame(
                value=default_tables.edges,
                label="Edges",
                interactive=True,
            )
            save_model_button = gr.Button("Сохранить текущий CSV")

        with gr.Tab("Settings"):
            show_deformed = gr.Checkbox(label="Показать деформированную форму", value=True)
            scale_slider = gr.Slider(0.0, 1000.0, value=100.0, step=1.0, label="Масштаб деформации")
            apply_node_props_ck = gr.Checkbox(label="Применять опоры и нагрузки узлов", value=True)
            color_by_dd = gr.Dropdown(choices=["Mz", "My", "None"], value="Mz", label="Раскраска элементов")
            max_elem_len = gr.Slider(0.0, 20000.0, value=0.0, step=100.0, label="Максимальная длина элемента (мм)")
            show_colorbar_ck = gr.Checkbox(label="Показывать шкалу цветов", value=True)
            colormap_dd = gr.Dropdown(
                choices=["viridis", "plasma", "inferno", "magma", "cividis"],
                value="viridis",
                label="Colormap",
            )
            sample_res = gr.Slider(3, 101, value=11, step=1, label="Количество точек на элемент")
            use_plotly_ck = gr.Checkbox(label="Использовать Plotly", value=True)

        with gr.Tab("3D Viewer"):
            plot_3d = gr.Plot(label="3D Viewer")

        with gr.Tab("Results"):
            table_moments = gr.DataFrame(label="Таблица моментов")
            table_disp = gr.DataFrame(label="Таблица перемещений")

        with gr.Tab("Exports"):
            export_moments_file = gr.File(label="Moments CSV")
            export_disp_file = gr.File(label="Displacements CSV")
            export_model_file = gr.File(label="Model CSV")

        with gr.Tab("Documentation"):
            gr.Markdown(load_documentation())

    model_state = gr.State()

    file_input.change(
        fn=load_tables_for_ui,
        inputs=[file_input],
        outputs=[node_props_table, model_nodes_table, model_edges_table],
    )

    run_button.click(
        fn=run_analysis_for_ui,
        inputs=[
            file_input,
            show_deformed,
            scale_slider,
            apply_node_props_ck,
            color_by_dd,
            max_elem_len,
            node_props_table,
            show_colorbar_ck,
            colormap_dd,
            sample_res,
            use_plotly_ck,
            model_nodes_table,
            model_edges_table,
        ],
        outputs=[
            output_text,
            table_moments,
            table_disp,
            plot_3d,
            export_moments_file,
            export_disp_file,
            export_model_file,
            node_props_table,
            model_state,
        ],
        api_name="run_analysis",
        show_progress="full",
        queue=True,
        concurrency_limit=1,
    )

    save_model_button.click(
        fn=save_model_csv,
        inputs=[model_nodes_table, model_edges_table, node_props_table],
        outputs=[export_model_file],
        queue=False,
    )

    try:
        plot_3d.select(
            fn=on_3d_plot_click,
            inputs=[model_state],
            outputs=[plot_3d, selection_info],
            queue=False,
        )
    except Exception:
        logger.debug("Plot event binding not available in this Gradio version")


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
