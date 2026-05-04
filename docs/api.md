# API reference

This page summarizes the main programmatic building blocks available in the
`wagon_fem` package. Prefer the high-level helpers in `model` and `solver` for
most workflows.

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
  - `get_3d_figure(model, ...)` — returns a Plotly or Matplotlib figure for visualization.

- `wagon_fem.ui`
  - Gradio-based UI. The `analyze_structure` function wires together model loading,
    application of node supports/loads, running analysis and returning plots/tables.
  
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
- There are a few small API mismatches in the codebase (for example some
  top-level entrypoints reference a `WagonModel` symbol that is not exported).
  The easiest approach is to use the functions shown above (`load_model_from_csv`,
  `run_analysis`, etc.) until those entrypoints are harmonized.
