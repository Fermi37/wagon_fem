import os
import logging
from typing import Optional, Tuple

import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
import io
import tempfile
import zipfile
import shutil
import threading
import time
import atexit
from .model import create_simple_wagon_model, load_model_from_csv
from .solver import run_analysis, get_moments_table, get_displacements_table, get_3d_figure


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# Temporary file registry + background cleanup
_TEMP_PATH_REGISTRY = []  # list of tuples (path, created_time)
_TEMP_REG_LOCK = threading.Lock()
_CLEANUP_INTERVAL = int(os.environ.get("WAGON_FEM_TEMP_CLEAN_INTERVAL", 60))
_CLEANUP_AGE = int(os.environ.get("WAGON_FEM_TEMP_MAX_AGE", 300))


def _register_temp_path(p: Optional[str]):
    """Register a temporary file or directory for periodic cleanup.

    p: filesystem path
    """
    try:
        if not p:
            return
        with _TEMP_REG_LOCK:
            _TEMP_PATH_REGISTRY.append((p, time.time()))
    except Exception:
        logger.debug("Failed to register temp path %s", p)


def _cleanup_once():
    now = time.time()
    to_remove = []
    with _TEMP_REG_LOCK:
        for p, ts in list(_TEMP_PATH_REGISTRY):
            try:
                if now - ts >= _CLEANUP_AGE:
                    if os.path.exists(p):
                        try:
                            if os.path.isdir(p):
                                shutil.rmtree(p)
                            else:
                                os.remove(p)
                        except Exception:
                            logger.debug("Failed to remove temp path %s", p)
                    to_remove.append((p, ts))
            except Exception:
                logger.debug("Error during cleanup check for %s", p)
        for item in to_remove:
            try:
                _TEMP_PATH_REGISTRY.remove(item)
            except Exception:
                pass


def _cleanup_worker():
    while True:
        try:
            _cleanup_once()
        except Exception:
            logger.exception("Temp cleanup worker error")
        time.sleep(_CLEANUP_INTERVAL)


def _cleanup_all():
    # Attempt to remove all registered temp paths (called at exit)
    with _TEMP_REG_LOCK:
        for p, _ in list(_TEMP_PATH_REGISTRY):
            try:
                if os.path.exists(p):
                    if os.path.isdir(p):
                        shutil.rmtree(p)
                    else:
                        os.remove(p)
            except Exception:
                logger.debug("Failed to cleanup temp path at exit: %s", p)
        _TEMP_PATH_REGISTRY.clear()


# Start cleanup background thread (daemon)
try:
    _cleanup_thread = threading.Thread(target=_cleanup_worker, daemon=True)
    _cleanup_thread.start()
except Exception:
    logger.debug("Failed to start temp cleanup thread")

# Ensure final cleanup on process exit
atexit.register(_cleanup_all)


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


def prepare_model_tables(file):
    """Return (nodes_df, edges_df) by parsing a CSV that contains a nodes block
    followed by an edges block (like data/wagon_frame.csv).

    If file is None, attempt to load the packaged default data/wagon_frame.csv.
    """
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
        # try packaged default
        pkg_default = os.path.normpath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'wagon_frame.csv'))
        if os.path.exists(pkg_default):
            path = pkg_default

    if not path:
        return pd.DataFrame(), pd.DataFrame()

    try:
        with open(path, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()

        edge_header_idx = None
        for i, line in enumerate(lines):
            low = line.strip().lower()
            if low.startswith('edge_id') or 'start_node' in low or 'end_node' in low:
                edge_header_idx = i
                break

        if edge_header_idx is None:
            # whole file considered nodes
            nodes_csv = ''.join(lines)
            try:
                nodes_df = pd.read_csv(io.StringIO(nodes_csv))
            except Exception:
                nodes_df = pd.DataFrame()
            edges_df = pd.DataFrame(columns=[
                                    'edge_id', 'start_node', 'end_node', 'E', 'Iy', 'Iz', 'J', 'A', 'w', 'dist_dir'])
            return nodes_df, edges_df

        nodes_lines = lines[:edge_header_idx]
        edges_lines = lines[edge_header_idx:]

        try:
            nodes_df = pd.read_csv(io.StringIO(''.join(nodes_lines)))
        except Exception:
            nodes_df = pd.DataFrame()
        try:
            edges_df = pd.read_csv(io.StringIO(''.join(edges_lines)))
        except Exception:
            edges_df = pd.DataFrame()

        return nodes_df, edges_df
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


def save_model_csv(nodes_df, edges_df):
    """Save edited nodes and edges DataFrames into a combined CSV and return path."""
    try:
        nd = nodes_df if hasattr(
            nodes_df, 'to_csv') else pd.DataFrame(nodes_df)
        ed = edges_df if hasattr(
            edges_df, 'to_csv') else pd.DataFrame(edges_df)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.modified.csv')
        with open(tmp.name, 'w', encoding='utf-8') as fh:
            nd.to_csv(fh, index=False)
            fh.write('\n')
            ed.to_csv(fh, index=False)
        _register_temp_path(tmp.name)
        return tmp.name
    except Exception:
        logger.exception("Failed to save modified model CSV")
        return None


def load_documentation():
    """Load README and docs/*.md into a single Markdown string for the UI."""
    parts = []
    base = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..', '..'))
    candidates = [
        os.path.join(base, 'README.md'),
        os.path.join(base, 'docs', 'index.md'),
        os.path.join(base, 'docs', 'usage.md'),
        os.path.join(base, 'docs', 'api.md'),
    ]
    for p in candidates:
        try:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                parts.append(f"## {os.path.basename(p)}\n\n" + content)
        except Exception:
            continue
    if not parts:
        return "Документация не найдена в репозитории."
        return "\n\n---\n\n".join(parts)


def load_documentation_ru():
    """Возвращает подробную русскоязычную документацию для отображения в UI.

    Текст даёт развернутые инструкции по установке, формату CSV, описанию вкладок
    интерфейса, пример использования и советы по развертыванию на Hugging Face Spaces.
    """
    return """
# wagon-fem — подробная документация (русский)

Wagon FEM — облегчённый пакет для построения простых 3D‑рам и расчёта эпюр изгибающих моментов.
Программа использует Pynite/PyniteFEA как расчётное ядро и предоставляет удобный
Gradio-интерфейс для загрузки модели, редактирования таблиц конструкции и получения
экспортируемых результатов.

## Установка

1. Создайте виртуальное окружение и активируйте его:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Установите пакет и зависимости:

```bash
pip install -e .
pip install -r requirements.txt
```

> Примечание: некоторые окружения требуют `python3` вместо `python`.

## Быстрый запуск (локально)

```bash
PYTHONPATH=src python -m wagon_fem.ui
# или, при наличии entrypoint:
# wagon-fem-ui serve --port 7860 --share
```

Откройте адрес, который выведет Gradio (обычно http://127.0.0.1:7860).

## Формат CSV (Nodes + Edges)

Поддерживается единый CSV вида "Nodes block" затем пустая строка, затем "Edges block".
Пример — две таблицы в одном файле:

Nodes (пример):

```
node_id,x,y,z
1,0,0,0
2,1000,0,0
3,1000,500,0
```

Edges (пример):

```
edge_id,start_node,end_node,E,Iy,Iz,J,A,w,dist_dir
1,1,2,210000,1e6,1e6,100,100,0.0,x
2,2,3,210000,1e6,1e6,100,100,0.0,x
```

Рекомендуемые колонки для узлов:
- `node_id` или `id`, `x`, `y`, `z`
- опции: `support_dx`, `support_dy`, `support_dz`, `support_rx`, `support_ry`, `support_rz`
- опции: `fx`, `fy`, `fz`, `mx`, `my`, `mz`

Рекомендуемые колонки для рёбер:
- `edge_id`/`id`, `start_node`, `end_node`
- опции: `E`, `Iy`, `Iz`, `J`, `A`, `w`, `w1`, `w2`, `dist_dir`

## Описание вкладок интерфейса

- Главная (Main): загрузите CSV (или оставьте пустым для демо) и нажмите «Выполнить расчет».
    Отображается статус расчёта и автор.
- Настройки (Settings): параметры визуализации — масштаб деформации, способ раскраски
    элементов (по Mz, My или без цвета), разрешение выборки вдоль элемента и выбор
    интерактивного вьювера (Plotly).
- Свойства узлов (Node properties): таблица, где можно редактировать опоры и нагрузки
    по узлам — эти значения применяются при запуске расчёта (если включён флаг
    "Применять опоры и силы из CSV").
- Данные конструкции (Construction data): интерактивные таблицы Nodes и Edges. Изменения
    в таблицах используются немедленно при нажатии "Выполнить расчет" — файл CSV
    не нужно сохранять вручную. Кнопка "Сохранить модифицированный CSV" экспортирует
    объединённый файл Nodes+Edges в раздел Exports.
- 3D Viewer: интерактивное 3D‑представление каркаса (Plotly, при наличии). Можно
    выделять элементы/узлы — клики обрабатываются и подсвечивают выбранный объект.
- Plots: примерная 2D‑эпюра для выбранного элемента и галерея с PNG‑графиками (их
    можно скачать в ZIP).
- Results: табличные экспортируемые результаты — эпюры моментов и смещения узлов.
- Exports: ссылки/файлы для скачивания (moments.csv, displacements.csv, modified_model.csv, plots.zip).

## Экспорт и временные файлы

При расчёте создаются временные файлы (PNG графики, результирующие CSV, ZIP архив).
В приложении реализована автоматическая очистка временных файлов старше нескольких
минут — порог можно настроить через переменные окружения:

- `WAGON_FEM_TEMP_MAX_AGE` — максимальный возраст временных файлов в секундах (по умолчанию 300).
- `WAGON_FEM_TEMP_CLEAN_INTERVAL` — интервал проверки в секундах (по умолчанию 60).

## Программный API

Вы можете использовать пакет программно:

```python
from wagon_fem.model import load_model_from_csv
from wagon_fem.solver import run_analysis, get_moments_table

model = load_model_from_csv('data/wagon_frame.csv')
model = run_analysis(model)
df = get_moments_table(model)
```

## Развёртывание на Hugging Face Spaces

1. Включите `app.py` и `requirements.txt` в корень репозитория.
2. Создайте новый Space и подключите репозиторий — HF самостоятельно установит зависимости.
3. Убедитесь, что `app.py` запускает `demo.launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 7860)))`.

## Типичные проблемы и отладка

- Если Gradio не запускается: проверьте, что установлены `gradio` и остальные зависимости.
- Если 3D‑вьювер не интерактивен — убедитесь, что `plotly` установлен.
- Если экспортные файлы отсутствуют — проверьте логи приложения, сообщения об ошибках
    и доступность временной папки (права файловой системы).

## Единицы измерения

- Длины: мм
- Силы: N
- Модуль упругости E: N/mm² (MPa)

## Автор и лицензия

Автор: Yuri Bulavin

Лицензия: см. файл LICENSE в корне репозитория.

"""


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
    model_nodes=None,
    model_edges=None,
):
    """Load model (or demo), apply node supports/loads (from CSV or edited table), run analysis,
    and return plots/tables and exportable CSV files.

    Returns:
      text_result, matplotlib figure, moments DF, displacements DF, 3D figure,
      moments_csv_path, displacements_csv_path, modified_model_csv_path, node_props_out
    """
    logger.info("Starting analyze_structure (show_deformed=%s, scale=%s, apply_node_props=%s)",
                show_deformed, scale, apply_node_props)

    # If editable construction tables were provided, write them to a temporary
    # combined CSV and use that as the model input. This allows the Run button
    # to operate directly on the edited tables without saving to disk first.
    tmp_model_csv = None
    has_model_tables = False
    try:
        nd_df = None
        ed_df = None
        if model_nodes is not None:
            nd_df = model_nodes if hasattr(
                model_nodes, 'columns') else pd.DataFrame(model_nodes)
            if getattr(nd_df, 'shape', (0, 0))[0] > 0:
                has_model_tables = True
        if model_edges is not None:
            ed_df = model_edges if hasattr(
                model_edges, 'columns') else pd.DataFrame(model_edges)
            if getattr(ed_df, 'shape', (0, 0))[0] > 0:
                has_model_tables = True
        if has_model_tables:
            # ensure DataFrames are at least empty frames if missing
            nd_df = nd_df if nd_df is not None else pd.DataFrame()
            ed_df = ed_df if ed_df is not None else pd.DataFrame()
            tmp_model_csv = save_model_csv(nd_df, ed_df)
            if tmp_model_csv:
                # override uploaded file with the generated combined CSV
                file = tmp_model_csv
    except Exception:
        tmp_model_csv = None

    # Resolve uploaded file path (or use the generated temporary CSV above)
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
            logger.exception("Failed to load model from CSV: %s", e)
            # return the same shape as the successful path; last value is server-side model state (None)
            # Output tuple length must match the successful case (+1 for plotly_html)
            return f"Ошибка загрузки файла: {e}", None, [], None, None, None, None, None, None, None, None, prepare_node_table(file), None

    # Helper to interpret truthy values from editable table
    def _truthy(v):
        if v is None:
            return False
        if isinstance(v, (bool, int, float)):
            return bool(v)
        s = str(v).strip().lower()
        return s in ("1", "true", "t", "yes", "y", "x", "on")

    # Apply node_props table values (if provided)
    # If the editable construction tables were provided and applied by the
    # loader (has_model_tables + apply_node_props), skip re-applying node_props
    node_props_out = None
    skip_node_props_application = bool(has_model_tables and apply_node_props)
    if node_props is not None and not skip_node_props_application:
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

    # Run analysis (may be long-running). Keep logging and fail-safe handling.
    try:
        model = run_analysis(model)
    except Exception as e:
        logger.exception("run_analysis failed: %s", e)
        # Match the full output tuple (gallery placeholder = []) — include extra HTML slot
        return f"Ошибка выполнения расчета: {e}", None, [], None, None, None, None, None, None, None, None, node_props_out, None

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

    # Defensive: compute max safely
    try:
        max_mz = float(df_moments["Max_Mz"].max()) if (
            df_moments is not None and "Max_Mz" in df_moments.columns) else 0.0
    except Exception:
        max_mz = 0.0
    text_result = f"Расчет завершен.\nВсего элементов: {len(model.members)}\nМаксимальный момент: {max_mz:.2f} Н*мм"

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

    # Normalize returned 3D figure into two outputs:
    # - `fig3d_plot`: a Matplotlib Figure (or None)
    # - `fig3d_html`: an HTML fragment containing Plotly markup (or None)
    fig3d_plot = None
    fig3d_html = None
    try:
        # If get_3d_figure returned a Plotly Figure, convert to HTML for robust
        # client-side rendering (works across Gradio/Spaces versions).
        import plotly.graph_objects as _go  # type: ignore
        import plotly.io as _pio  # type: ignore
        if isinstance(fig3d, _go.Figure):
            try:
                fig3d_html = _pio.to_html(
                    fig3d, full_html=False, include_plotlyjs='cdn')
            except Exception:
                logger.exception(
                    "Failed to convert Plotly figure to HTML; dropping interactive")
                fig3d_plot = None
        else:
            # Assume a Matplotlib Figure was returned
            fig3d_plot = fig3d
    except Exception:
        # Plotly not available — treat fig3d as Matplotlib Figure
        try:
            fig3d_plot = fig3d
        except Exception:
            fig3d_plot = None

    # Generate per-member moment (Mz) and approximate shear plots and bundle them
    plots_zip_path = None
    plot_files = []
    try:
        tmpdir = tempfile.mkdtemp(prefix='wagon_plots_')
        _register_temp_path(tmpdir)
        sr_plots = max(2, int(sample_resolution))
        for mem in model.members.values():
            try:
                L = mem.L()
            except Exception:
                L = getattr(mem, 'length', 0.0)
            if sr_plots > 1 and L > 0:
                positions = [i * (L / (sr_plots - 1)) for i in range(sr_plots)]
            else:
                positions = [0.0]

            m_vals = []
            for pos in positions:
                try:
                    v = mem.moment('Mz', pos)
                except Exception:
                    try:
                        frac = (pos / L) if L else 0.0
                        v = mem.moment('Mz', frac)
                    except Exception:
                        v = 0.0
                try:
                    m_vals.append(float(v))
                except Exception:
                    m_vals.append(0.0)

            # approximate shear as -dM/dx (finite difference)
            shear = []
            n = len(positions)
            for i in range(n):
                try:
                    if n == 1:
                        slope = 0.0
                    elif i == 0:
                        dx = positions[1] - positions[0] or 1.0
                        slope = (m_vals[1] - m_vals[0]) / dx
                    elif i == n - 1:
                        dx = positions[-1] - positions[-2] or 1.0
                        slope = (m_vals[-1] - m_vals[-2]) / dx
                    else:
                        dx = positions[i + 1] - positions[i - 1] or 1.0
                        slope = (m_vals[i + 1] - m_vals[i - 1]) / dx
                except Exception:
                    slope = 0.0
                shear.append(-slope)

            # Save Mz plot
            try:
                figm, axm = plt.subplots()
                axm.plot(positions, m_vals, marker='o')
                axm.set_title(f"Mz for member {mem.name}")
                axm.set_xlabel("Length (mm)")
                axm.set_ylabel("Moment Mz (N*mm)")
                axm.grid(True)
                fname_m = os.path.join(tmpdir, f"{mem.name}_Mz.png")
                figm.savefig(fname_m, bbox_inches='tight')
                plt.close(figm)
                plot_files.append(fname_m)
            except Exception:
                pass

            # Save shear plot
            try:
                figs, axs = plt.subplots()
                axs.plot(positions, shear, marker='o')
                axs.set_title(f"Shear (approx) for member {mem.name}")
                axs.set_xlabel("Length (mm)")
                axs.set_ylabel("Shear (N)")
                axs.grid(True)
                fname_s = os.path.join(tmpdir, f"{mem.name}_Shear.png")
                figs.savefig(fname_s, bbox_inches='tight')
                plt.close(figs)
                plot_files.append(fname_s)
            except Exception:
                pass

        if plot_files:
            tmpzip = tempfile.NamedTemporaryFile(
                delete=False, suffix='.plots.zip')
            try:
                with zipfile.ZipFile(tmpzip.name, 'w') as zf:
                    for p in plot_files:
                        zf.write(p, arcname=os.path.basename(p))
                plots_zip_path = tmpzip.name
                _register_temp_path(tmpzip.name)
            except Exception:
                plots_zip_path = None
    except Exception:
        plots_zip_path = None

    # Create separate export CSVs for moments and displacements
    moments_path = None
    disp_path = None
    modified_csv_path = None
    try:
        tmpm = tempfile.NamedTemporaryFile(delete=False, suffix='.moments.csv')
        df_moments.to_csv(tmpm.name, index=False)
        _register_temp_path(tmpm.name)
        moments_path = tmpm.name
    except Exception:
        logger.exception("Failed to write moments CSV")
        moments_path = None

    try:
        tmpd = tempfile.NamedTemporaryFile(
            delete=False, suffix='.displacements.csv')
        df_disp.to_csv(tmpd.name, index=False)
        _register_temp_path(tmpd.name)
        disp_path = tmpd.name
    except Exception:
        logger.exception("Failed to write displacements CSV")
        disp_path = None

    # Persist edited node table back to CSV (nodes block + original edges block when possible)
    try:
        nodes_df = node_props_out if node_props_out is not None else prepare_node_table(
            file)
        original_edges = []
        if path:
            try:
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
            except Exception:
                original_edges = []

        tmpc = tempfile.NamedTemporaryFile(
            delete=False, suffix='.modified.csv')
        with open(tmpc.name, 'w', encoding='utf-8') as fh:
            try:
                nodes_df.to_csv(fh, index=False)
            except Exception:
                # nodes_df may be an empty structure — write headers only
                try:
                    pd.DataFrame(nodes_df).to_csv(fh, index=False)
                except Exception:
                    pass
            fh.write('\n')
            if original_edges:
                try:
                    fh.writelines(original_edges)
                except Exception:
                    pass
        modified_csv_path = tmpc.name
        _register_temp_path(tmpc.name)
    except Exception:
        logger.exception("Failed to write modified CSV")
        modified_csv_path = None

    # Return plot file paths (registered for cleanup) so Gradio can move/cache them
    # Avoid converting to long data-URI strings which some Gradio versions treat as
    # file paths and then call Path.exists() (causing OSError for very long names).
    plot_gallery_data = []
    try:
        if plot_files:
            for p in plot_files:
                try:
                    _register_temp_path(p)
                    plot_gallery_data.append(p)
                except Exception:
                    logger.debug("Failed to add plot %s to gallery list", p)
                    plot_gallery_data.append(None)
    except Exception:
        plot_gallery_data = []

    # Return the computed results and keep the server-side model in the last output
    # Outputs order (note extra slot for Plotly HTML):
    # text_result, example_plot(fig), gallery_images(list of paths), df_moments, df_disp,
    # fig3d_plot (Matplotlib) or None, fig3d_html (Plotly HTML) or None,
    # moments_csv, displacements_csv, modified_model_csv, plots_zip, node_props_out, model
    return text_result, fig, plot_gallery_data, df_moments, df_disp, fig3d_plot, fig3d_html, moments_path, disp_path, modified_csv_path, plots_zip_path, node_props_out, model


def on_3d_plot_click(evt, model):
    """Handle Plotly click/select events forwarded by Gradio.

    evt: event payload dict (expects 'points' list)
    model: server-side FEModel3D instance stored in gr.State

    Returns: (updated_figure, selection_text)
    """
    try:
        if not evt:
            return None, "No selection"
        points = evt.get('points') if isinstance(evt, dict) else None
    except Exception:
        points = None

    if not points:
        return None, "No selection"

    p = points[0]
    cd = p.get('customdata') if isinstance(p, dict) else None
    sel_type = None
    sel_id = None
    if isinstance(cd, (list, tuple)):
        cd0 = cd[0]
    else:
        cd0 = cd

    if isinstance(cd0, str):
        if cd0.startswith('MEM:'):
            sel_type = 'member'
            sel_id = cd0.split(':', 1)[1]
        elif cd0.startswith('NODE:'):
            sel_type = 'node'
            sel_id = cd0.split(':', 1)[1]

    # Fallback: try text fields
    if sel_id is None:
        txt = p.get('text') or p.get('hovertext') or ''
        if isinstance(txt, str):
            if txt.startswith('Member') or 'Member' in txt:
                sel_type = 'member'
                # try to parse name from text
                parts = txt.split()
                if len(parts) > 1:
                    sel_id = parts[0]

    if sel_id is None:
        return None, "Selection not recognized"

    try:
        if sel_type == 'member':
            new_fig = get_3d_figure(
                model, prefer_plotly=True, highlight_member=sel_id)
            sel_text = f"Selected member: {sel_id}"
        else:
            new_fig = get_3d_figure(
                model, prefer_plotly=True, highlight_node=sel_id)
            sel_text = f"Selected node: {sel_id}"
        return new_fig, sel_text
    except Exception as e:
        logger.exception("Error handling plot click: %s", e)
        return None, f"Error: {e}"


with gr.Blocks(title="Wagon FEM Analysis") as demo:
    gr.Markdown("# 🚂 Расчет конструкции вагона (Pynite + Gradio)")

    # Convert the single-row layout into a tabbed app with "Main" as the default tab.
    # "Main" contains the primary Run button and status fields; other tabs hold
    # settings, editable tables and exports.
    with gr.Tabs():
        with gr.Tab("Main"):
            with gr.Row():
                with gr.Column():
                    file_input = gr.File(
                        label="Загрузить CSV (или оставить пустым для демо)")
                    btn_run = gr.Button("Выполнить расчет", variant="primary")
                    gr.Markdown("**Author:** Yuri Bulavin")

                with gr.Column():
                    # Primary status textbox — exports are grouped into the Exports tab below.
                    output_text = gr.Textbox(label="Статус расчета")
                    selection_info = gr.Textbox(
                        label="Selection", interactive=False)

        with gr.Tab("Settings"):
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

        with gr.Tab("3D Viewer"):
            plot_3d = gr.Plot(label="3D Viewer")
            # HTML placeholder for Plotly interactive markup (used as a robust
            # fallback on platforms where native Plotly objects are not rendered
            # correctly by Gradio). When Plotly is available we return an HTML
            # fragment (plotly.io.to_html) into this component; otherwise the
            # Matplotlib Figure is returned to `plot_3d`.
            plotly_html = gr.HTML(
                value="", label="Interactive 3D (Plotly HTML)")

        with gr.Tab("Plots"):
            plot_output = gr.Plot(label="Эпюра моментов (пример)")
            # Gallery of generated PNG plots (moments + shear)
            plot_gallery = gr.Gallery(label="Сгенерированные графики")

        with gr.Tab("Results"):
            with gr.Row():
                with gr.Column():
                    table_moments = gr.DataFrame(label="Таблица моментов")
                with gr.Column():
                    table_disp = gr.DataFrame(
                        label="Таблица перемещений узлов")

        with gr.Tab("Construction data"):
            # Editable tables for nodes and edges from the model CSV (wagon_frame.csv)
            nodes_df_def, edges_df_def = prepare_model_tables(None)
            model_nodes_table = gr.DataFrame(
                value=nodes_df_def, label="Nodes (editable)", interactive=True)
            model_edges_table = gr.DataFrame(
                value=edges_df_def, label="Edges (editable)", interactive=True)
            save_model_btn = gr.Button("Save modified model CSV")

        with gr.Tab("Exports"):
            export_moments_file = gr.File(label="Export moments (CSV)")
            export_disp_file = gr.File(label="Export displacements (CSV)")
            export_modified_csv = gr.File(label="Modified model CSV")
            export_plots_zip = gr.File(label="Export moment/shear plots (zip)")
        with gr.Tab("Документация"):
            docs_md = load_documentation_ru()
            gr.Markdown(docs_md)

        with gr.Tab("Помощь"):
            gr.Markdown(
                """
                ## Помощь

                - Вкладка «Главная»: загрузите CSV (или оставьте пустым для демо) и нажмите «Выполнить расчет».
                - Вкладка «Настройки»: параметры визуализации (масштаб деформации, раскраска, разрешение выборки).
                - Вкладка «Свойства узлов»: отредактируйте опоры и нагрузки узлов, которые будут применены к модели.
                - Вкладка «Данные конструкции»: редактируйте таблицы Nodes и Edges прямо в браузере; эти правки можно применить немедленно при нажатии «Выполнить расчет» (без предварительного сохранения CSV). Кнопка «Сохранить модифицированный CSV» экспортирует объединённый файл Nodes+Edges.

                Если возникли вопросы, откройте файл `README.md` в репозитории или используйте вкладку «Документация» для полного описания.
                """
            )

    # Populate node table when a CSV is uploaded
    file_input.change(fn=prepare_node_table, inputs=[
                      file_input], outputs=[node_props_table])
    # Also populate editable construction tables (nodes + edges)
    try:
        file_input.change(fn=prepare_model_tables, inputs=[file_input], outputs=[
                          model_nodes_table, model_edges_table])
    except Exception:
        logger.debug("Model tables change binding not available")

    # Server-side model state (stores FEModel3D instance between calls)
    model_state = gr.State()

    # Run analysis. Use Gradio queuing for long-running computation and show progress.
    btn_run.click(
        fn=analyze_structure,
        inputs=[file_input, show_deformed, scale_slider, apply_node_props_ck, color_by_dd,
                max_elem_len, node_props_table, show_colorbar_ck, colormap_dd, sample_res, use_plotly_ck, model_nodes_table, model_edges_table],
        outputs=[output_text, plot_output, plot_gallery, table_moments, table_disp, plot_3d, plotly_html,
                 export_moments_file, export_disp_file, export_modified_csv, export_plots_zip, node_props_table, model_state],
        api_name="run_analysis",
        api_description="Run FEM analysis (may be long-running)",
        show_progress="full",
        queue=True,
        concurrency_limit=1,
    )

    # Save edited model CSV from Construction tab -> Exports
    try:
        save_model_btn.click(fn=save_model_csv, inputs=[
                             model_nodes_table, model_edges_table], outputs=[export_modified_csv], queue=False)
    except Exception:
        logger.debug("Save model binding not available")

    # Bind Plotly click/select events to the server-side handler. The event handler
    # will receive the event payload and the server-side model_state to re-render
    # the figure with a highlighted selection.
    try:
        plot_3d.select(fn=on_3d_plot_click, inputs=[model_state], outputs=[
                       plot_3d, selection_info], queue=False)
    except Exception:
        # Older Gradio versions may not support plot events in the same way; ignore silently
        logger.debug("Plot event binding not available in this Gradio version")


def main():
    # Respect environment variables for host/port/share to make this app more
    # friendly for CI/containers and cloud deployments.
    host = os.environ.get("WAGON_FEM_HOST", os.environ.get(
        "GRADIO_SERVER_NAME", "127.0.0.1"))
    port = int(os.environ.get("WAGON_FEM_PORT", os.environ.get("PORT", 7860)))
    share = os.environ.get("WAGON_FEM_SHARE", os.environ.get(
        "GRADIO_SHARE", "false")).lower() in ("1", "true", "yes", "y")

    # Enable Gradio queue for background processing of long tasks
    try:
        demo.queue()
    except Exception:
        # Older Gradio versions may not support demo.queue(); ignore if unavailable
        logger.debug(
            "demo.queue() not available or failed; continuing without global queue")

    try:
        demo.launch(server_name=host, server_port=port, share=share)
    except Exception:
        logger.exception("Failed to launch Gradio demo on %s:%s", host, port)
        raise


if __name__ == "__main__":
    main()
