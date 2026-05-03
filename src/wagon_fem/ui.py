import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
import tempfile
from typing import Optional
from .model import create_simple_wagon_model, load_model_from_csv
from .solver import run_analysis, get_moments_table, get_displacements_table, get_3d_figure


def prepare_node_table(file) -> pd.DataFrame:
    """Return a pandas DataFrame suitable for editing node supports and nodal loads.

    If a CSV is uploaded, the function loads the nodes from it (without applying
    supports) and returns a DataFrame pre-filled with node coordinates and blank
    support/load columns ready for user editing.
    """
    cols = [
        "node_id", "x", "y", "z",
        "support_dx", "support_dy", "support_dz", "support_rx", "support_ry", "support_rz",
        "fx", "fy", "fz", "mx", "my", "mz",
    ]

    if not file:
        return pd.DataFrame(columns=cols)

    # Resolve file path
    path = None
    try:
        if isinstance(file, str):
            path = file
        elif isinstance(file, dict) and "name" in file:
            path = file["name"]
        elif hasattr(file, "name"):
            path = file.name
        elif isinstance(file, (list, tuple)) and len(file) > 0:
            path = file[0]
    except Exception:
        path = None

    if not path:
        return pd.DataFrame(columns=cols)

    try:
        model = load_model_from_csv(path, apply_node_props=False)
        rows = []
        for nid in sorted(model.nodes.keys(), key=lambda x: (str(type(x)), x)):
            n = model.nodes[nid]
            rows.append({
                "node_id": nid,
                "x": getattr(n, "X", None),
                "y": getattr(n, "Y", None),
                "z": getattr(n, "Z", None),
                "support_dx": False,
                "support_dy": False,
                "support_dz": False,
                "support_rx": False,
                "support_ry": False,
                "support_rz": False,
                "fx": 0.0,
                "fy": 0.0,
                "fz": 0.0,
                "mx": 0.0,
                "my": 0.0,
                "mz": 0.0,
            })
        return pd.DataFrame(rows, columns=cols)
    except Exception:
        return pd.DataFrame(columns=cols)


def analyze_structure(
    file,
    show_deformed: bool = True,
    scale: float = 100.0,
    apply_node_props: bool = True,
    color_by: str = 'Mz',
    max_member_length: float = 0.0,
    node_props=None,
    show_colorbar: bool = True,
    colormap: str = 'viridis',
    sample_resolution: int = 11,
    use_plotly: bool = True,
):
    """Load model (or demo), apply node supports/loads (from CSV or edited table), run analysis,
    and return plots/tables and exportable CSV files.

    Returns:
      text_result, matplotlib figure, moments DF, displacements DF, 3D figure,
      moments_csv_path, displacements_csv_path, modified_model_csv_path, node_props_out
    """
    # Resolve uploaded file path
    path: Optional[str] = None
    if file is None:
        model = create_simple_wagon_model()
    else:
        try:
            if isinstance(file, str):
                path = file
            elif isinstance(file, dict) and "name" in file:
                path = file["name"]
            elif hasattr(file, "name"):
                path = file.name
            elif isinstance(file, (list, tuple)) and len(file) > 0:
                path = file[0]
        except Exception:
            path = None

        try:
            # If user wants to use supports declared in CSV and didn't provide
            # an edited node table, load with apply_node_props=True.
            if path and apply_node_props and (node_props is None or (hasattr(node_props, 'shape') and node_props.shape[0] == 0)):
                model = load_model_from_csv(
                    path, apply_node_props=True, max_member_length=max_member_length)
            else:
                model = load_model_from_csv(
                    path, apply_node_props=False, max_member_length=max_member_length) if path else create_simple_wagon_model()
        except Exception as e:
            return f"Ошибка загрузки файла: {e}", None, None, None, None, None, None, None, prepare_node_table(file)

    # Helper to interpret truthy values from editable table
    def _truthy(v):
        if v is None:
            return False
        if isinstance(v, (bool, int, float)):
            return bool(v)
        s = str(v).strip().lower()
        return s in ("1", "true", "t", "yes", "y", "x", "on")

    # Apply node_props table values (if provided)
    node_props_out = None
    if node_props is not None:
        try:
            df = node_props if hasattr(
                node_props, "columns") else pd.DataFrame(node_props)
            node_props_out = df
            for _, row in df.iterrows():
                nid = row.get(
                    "node_id") if "node_id" in df.columns else row.iloc[0]
                try:
                    if pd.isna(nid):
                        continue
                except Exception:
                    pass
                try:
                    nid_cast = int(nid)
                except Exception:
                    nid_cast = nid

                # Supports
                sdx = _truthy(row.get("support_dx"))
                sdy = _truthy(row.get("support_dy"))
                sdz = _truthy(row.get("support_dz"))
                srx = _truthy(row.get("support_rx"))
                sry = _truthy(row.get("support_ry"))
                srz = _truthy(row.get("support_rz"))
                if any((sdx, sdy, sdz, srx, sry, srz)):
                    try:
                        model.def_support(nid_cast, sdx, sdy,
                                          sdz, srx, sry, srz)
                    except Exception:
                        pass

                # Nodal loads
                for dk in ("fx", "fy", "fz", "mx", "my", "mz"):
                    if dk in df.columns:
                        try:
                            val = row.get(dk)
                            if val is not None and not (isinstance(val, float) and pd.isna(val)) and float(val) != 0.0:
                                model.add_node_load(
                                    nid_cast, dk.upper(), float(val))
                        except Exception:
                            pass
        except Exception:
            node_props_out = prepare_node_table(file)
    else:
        # If no edited table provided, prepare a table to return for UI display
        node_props_out = prepare_node_table(file)

    # Run analysis
    model = run_analysis(model)

    # Tables
    df_moments = get_moments_table(model)
    df_disp = get_displacements_table(model)

    # Example 2D matplotlib plot (first member moment diagram)
    fig, ax = plt.subplots()
    if len(model.members) > 0:
        member = list(model.members.values())[0]
        try:
            x = [0, member.L()]
            y = [member.moment('Mz', 0), member.moment('Mz', member.L())]
            ax.plot(x, y, marker='o')
            ax.set_title(f"Эпюра моментов Mz для элемента {member.name}")
            ax.set_xlabel("Длина (мм)")
            ax.set_ylabel("Момент (Н*мм)")
            ax.grid(True)
        except Exception:
            ax.text(0.5, 0.5, 'Не удалось построить эпюру для примера', ha='center')

    text_result = f"Расчет завершен.\nВсего элементов: {len(model.members)}\nМаксимальный момент: {df_moments['Max_Mz'].max():.2f} Н*мм"

    # 3D viewer (interactive if plotly is available)
    try:
        sr = max(1, int(sample_resolution))
    except Exception:
        sr = 11
    fig3d = get_3d_figure(
        model,
        deformed=show_deformed,
        scale=scale,
        color_by=color_by,
        sample_resolution=sr,
        colormap=colormap,
        show_colorbar=show_colorbar,
        prefer_plotly=use_plotly,
    )

    # Create separate export CSVs for moments and displacements
    moments_path = None
    disp_path = None
    modified_csv_path = None
    try:
        tmpm = tempfile.NamedTemporaryFile(delete=False, suffix='.moments.csv')
        df_moments.to_csv(tmpm.name, index=False)
        moments_path = tmpm.name
    except Exception:
        moments_path = None

    try:
        tmpd = tempfile.NamedTemporaryFile(
            delete=False, suffix='.displacements.csv')
        df_disp.to_csv(tmpd.name, index=False)
        disp_path = tmpd.name
    except Exception:
        disp_path = None

    # Persist edited node table back to CSV (nodes block + original edges block when possible)
    try:
        nodes_df = node_props_out if node_props_out is not None else prepare_node_table(
            file)
        original_edges = []
        if path:
            with open(path, 'r', encoding='utf-8') as fh:
                orig_lines = fh.readlines()
            # detect start of edge table
            edge_header_idx = None
            for i, line in enumerate(orig_lines):
                low = line.strip().lower()
                if low.startswith('edge_id') or 'start_node' in low or 'end_node' in low:
                    edge_header_idx = i
                    break
            if edge_header_idx is not None:
                original_edges = orig_lines[edge_header_idx:]

        tmpc = tempfile.NamedTemporaryFile(
            delete=False, suffix='.modified.csv')
        with open(tmpc.name, 'w', encoding='utf-8') as fh:
            nodes_df.to_csv(fh, index=False)
            fh.write('\n')
            if original_edges:
                fh.writelines(original_edges)
        modified_csv_path = tmpc.name
    except Exception:
        modified_csv_path = None

    return text_result, fig, df_moments, df_disp, fig3d, moments_path, disp_path, modified_csv_path, node_props_out


with gr.Blocks(title="Wagon FEM Analysis") as demo:
    gr.Markdown("# 🚂 Расчет конструкции вагона (Pynite + Gradio)")

    with gr.Row():
        with gr.Column():
            file_input = gr.File(
                label="Загрузить CSV (или оставить пустым для демо)")
            btn_run = gr.Button("Выполнить расчет", variant="primary")
            show_deformed = gr.Checkbox(
                label="Показать деформированную форму", value=True)
            scale_slider = gr.Slider(
                minimum=0.0, maximum=1000.0, step=1.0, value=100.0, label="Масштаб деформации")
            apply_node_props_ck = gr.Checkbox(
                label="Применять опоры и силы из CSV", value=True)
            color_by_dd = gr.Dropdown(
                choices=['Mz', 'My', 'None'], value='Mz', label='Color members by')
            max_elem_len = gr.Slider(minimum=0.0, maximum=20000.0, step=100.0,
                                     value=0.0, label='Максимальная длина элемента (мм); 0 = без разбиения')
            show_colorbar_ck = gr.Checkbox(
                label="Показывать шкалу цветов (colorbar)", value=True)
            colormap_dd = gr.Dropdown(choices=[
                                      'viridis', 'plasma', 'inferno', 'magma', 'cividis'], value='viridis', label='Colormap')
            sample_res = gr.Slider(minimum=3, maximum=101, step=1, value=11,
                                   label='Количество точек на элемент (sampling resolution)')
            use_plotly_ck = gr.Checkbox(
                label="Use Plotly interactive viewer", value=True)

            # Node properties table moved to top-level Tab (see Tabs below)

        with gr.Column():
            output_text = gr.Textbox(label="Статус расчета")
            export_moments_file = gr.File(label="Export moments (CSV)")
            export_disp_file = gr.File(label="Export displacements (CSV)")
            export_modified_csv = gr.File(label="Modified model CSV")

    # Organize plots and tables into top-level tabs. Place node properties and exports
    # into their own top-level tabs so users can edit supports/loads and download
    # CSVs conveniently.
    with gr.Tabs():
        with gr.Tab("Node properties"):
            node_table_headers = [
                "node_id", "x", "y", "z",
                "support_dx", "support_dy", "support_dz", "support_rx", "support_ry", "support_rz",
                "fx", "fy", "fz", "mx", "my", "mz",
            ]
            empty_df = pd.DataFrame(columns=node_table_headers)
            node_props_table = gr.DataFrame(
                value=empty_df, label="Node properties (supports & loads)", interactive=True)

        with gr.Tab("3D Viewer"):
            plot_3d = gr.Plot(label="3D Viewer")

        with gr.Tab("Plots"):
            plot_output = gr.Plot(label="Эпюра моментов (пример)")

        with gr.Tab("Results"):
            with gr.Row():
                with gr.Column():
                    table_moments = gr.DataFrame(label="Таблица моментов")
                with gr.Column():
                    table_disp = gr.DataFrame(
                        label="Таблица перемещений узлов")

        with gr.Tab("Exports"):
            export_moments_file = gr.File(label="Export moments (CSV)")
            export_disp_file = gr.File(label="Export displacements (CSV)")
            export_modified_csv = gr.File(label="Modified model CSV")

    # Populate node table when a CSV is uploaded
    file_input.change(fn=prepare_node_table, inputs=[
                      file_input], outputs=[node_props_table])

    # Run analysis
    btn_run.click(
        fn=analyze_structure,
        inputs=[file_input, show_deformed, scale_slider, apply_node_props_ck, color_by_dd,
                max_elem_len, node_props_table, show_colorbar_ck, colormap_dd, sample_res, use_plotly_ck],
        outputs=[output_text, plot_output, table_moments, table_disp, plot_3d,
                 export_moments_file, export_disp_file, export_modified_csv, node_props_table],
    )


def main():
    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
