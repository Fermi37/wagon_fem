# API reference

This page summarizes the main programmatic building blocks available in the
`wagon_fem` package. Prefer the high-level helpers in `model`, `solver`, and
`services` for most workflows.

Modules and highlights

- `wagon_fem.loader`
  - `load_edges_from_csv(filepath: str)` — a small CSV reader for edge-only
    files (simple utility used in examples).

- `wagon_fem.model`
  - `load_model_from_csv(csv_path: str, apply_node_props: bool = True, max_member_length: float = 0.0)`
    — loads nodes and edges from a CSV into a Pynite `FEModel3D` instance.
  - `create_simple_wagon_model()` — a small demo model used by the UI/tests.
  - `create_simply_supported_beam(L=4000, w=-10.0, ..., n_segments=1)` — helper
    for creating verification beams.

- `wagon_fem.solver`
  - `run_analysis(model: FEModel3D)` — wrapper that calls the FE backend `analyze()`.
  - `get_moments_table(model)`, `get_displacements_table(model)` — return pandas
    DataFrames with extracted results.
  - `get_3d_figure(model, ...)` — legacy figure helper for local visualization paths.

- `wagon_fem.services`
  - `prepare_ui_tables(source)` — splits combined CSV content into geometry tables and task-data tables.
  - `analyze_model(...)` — merges task data back into the model, runs the solver, writes CSV exports, computes viewer metric metadata, and generates a `.gltf` viewer artifact.
  - `load_guide_markdown()` — returns the curated in-app guide content.

- `wagon_fem.ui`
  - Gradio-based UI with `Main`, `Construction Data`, `Task Data`, `3D Viewer`, `Results`, and `Guide` surfaces. The `3D Viewer` tab also contains the metric selector, legend, and viewer settings below the model.
  
- `wagon_fem.ui_cli`
  - Typer-based CLI wrapper for launching the Gradio UI. Use
    `python -m wagon_fem.ui_cli serve` or the installed `wagon-fem-ui` console
    script to start the UI with optional flags: `--host`, `--port`, `--share`,
    `--no-queue`, and `--log-level`.

Example: building, analyzing, and extracting results

```python
from wagon_fem.model import load_model_from_csv
from wagon_fem.solver import run_analysis, get_moments_table

model = load_model_from_csv('data/wagon_frame.csv')
model = run_analysis(model)
df = get_moments_table(model)
print(df)
```

Notes & caveats

- The package dynamically imports the FE class from either `Pynite` or `pynite`.
  Install a compatible FE implementation (for example `pynitefea`) in the same
  environment before running the examples or tests.
- The primary Hugging Face viewer path is the generated `.gltf` artifact used by
  Gradio `Model3D`, rather than Plotly-based interactivity.
