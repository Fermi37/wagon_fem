---
sdk: gradio
app_file: app.py
title: wagon-fem
---

# wagon-fem

Wagon FEM — a small Python package for building simple 3D frame models of a wagon
and computing bending moments with a Pynite-based FE backend. Includes a lightweight
Gradio UI for interactive exploration and CSV-based model importers for quick tests.

## Quick start

Prerequisites: Python 3.9+, git, and a virtual environment.

Create and activate a virtualenv, then install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# (optional) install development extras:
pip install -e '.[dev]'
```

Notes:
- The FE model implementation is provided by external packages (e.g. `pynite` / `pynitefea`).
   Install one of those into the same virtualenv before running analyses:

```bash
pip install pynitefea
```

## Running

CLI (simple):

```bash
python -m wagon_fem data/wagon_frame.csv
```

Interactive web UI (Gradio):

```bash
# after installation this command is registered by the project. The CLI supports
# flags for host/port/share and can be run as a Typer subcommand `serve`.
# Examples:
# run the installed console script (preferred)
wagon-fem-ui serve --port 7860 --share
# or run the Typer CLI module directly
python -m wagon_fem.ui_cli serve --port 7860 --share
# for backward compatibility the UI module still exposes a `main()` that can be
# run directly (`python -m wagon_fem.ui`), but the Typer wrapper provides a
# friendlier CLI surface with flags such as `--port`, `--host`, `--share`, and
# `--no-queue`.
```

## Programmatic API (example)

```python
from wagon_fem.model import load_model_from_csv
from wagon_fem.solver import run_analysis, get_moments_table

model = load_model_from_csv('data/wagon_frame.csv')
model = run_analysis(model)
df = get_moments_table(model)
print(df)
```

Key modules:
- `wagon_fem.loader` — helpers for small CSV formats (edge/node tables)
- `wagon_fem.model` — model construction helpers (create demo frames, load CSVs)
- `wagon_fem.solver` — analysis wrappers and result extraction (moments, displacements)
- `wagon_fem.ui` — Gradio front-end and helpers for interactive use

## CSV format

Two common CSV layouts are supported:

- A node table followed by an edge table in the same file (the loader will detect
   the start of the edge table by a header like `edge_id`, `start_node` or `end_node`).

- Separate node/edge tables with columns (case-insensitive) as follows.

Recommended node columns:
- `node_id` or `id`, `x`, `y`, `z` — coordinates
- Optional supports: `support_dx`, `support_dy`, `support_dz`, `support_rx`, `support_ry`, `support_rz` (truthy values: 1/true/yes/x)
- Optional single `supports` column with comma-separated flags (e.g. `dx,dy`)
- Optional nodal loads: `fx`, `fy`, `fz`, `mx`, `my`, `mz`

Recommended edge columns:
- `edge_id` (or `id`), `start_node`, `end_node`
- Optional section/material properties: `E`, `Iy`, `Iz`, `J`, `A`
- Optional distributed load columns: `w`, `w1`, `w2`, `dist_dir` / `dir` (e.g. `FY`)

See `data/wagon_frame.csv` for a sample input combining a node table and an edge table.

## Development & tests

### Edge columns explained

- `edge_id` (or `id`) — Unique identifier for the member. The loader uses this
   to name the created member (for example `M{edge_id}`). If `edge_id` is missing
   the loader falls back to a generated name like `M{start}_{end}`.

- `start_node`, `end_node` — Node IDs that the member connects. These must match
   node identifiers from the node table (or previously added nodes).

- Section / material properties:
   - `E` — Young's modulus (stiffness). Units used in the code: N/mm² (MPa).
      Default used by the loader: `210000`.
   - `Iy`, `Iz` — second moments of area about local axes (units: mm⁴).
   - `J` — torsional constant (mm⁴).
   - `A` — cross-sectional area (mm²). Default if missing: `1.0`.

   The loader will create/reuse a material key (`mat_{int(E)}`) and a section key
   (`S_{int(A)}_{int(Iy)}_{int(Iz)}_{int(J)}`) and attempt to register them with
   the FE backend before adding the member.

- Distributed loads and directions:
   - `w` — uniform distributed load (force per length). Units: N/mm. If `w` is
      present and `w1`/`w2` are not, it is applied as constant along the member.
   - `w1`, `w2` — start/end intensities (N/mm) for a linearly-varying distributed
      load across the member.
   - `dist_dir`, `dist_load_dir`, `load_dir`, `dir`, `direction` — load direction
      string; the loader uppercases the value and defaults to `FY` when absent.
      Typical values: `FX`, `FY`, `FZ` (local axes).

   When members are subdivided (see `n_segments` or `max_member_length`) the
   loader interpolates `w1`→`w2` across sub-members and applies piecewise loads.

- Additional recognized/alternative columns: `n_segments` (force subdivision),
   `area` (alias for `A`), `w_start`/`w_end` or `w_a`/`w_b` (aliases for `w1`/`w2`),
   etc.

- Units & defaults — conventions used in the loader:
   - Lengths: mm
   - Forces: N
   - Young's modulus `E`: N/mm² (MPa)
   - Distributed loads `w`, `w1`, `w2`: N/mm
   - Areas: mm²; moments: N·mm
   - Defaults: `E=210000`, `A=1.0`, `Iy/Iz/J` default to `0.0` where not provided.

The loader is robust to missing or malformed values: it uses sensible defaults
where possible and continues loading even if some FE API calls fail due to
backend differences.

Example row (from `data/wagon_frame.csv`):
```
1,1,2,210000,5000000,2000000,100000,5000,-10,FY
```
This describes member `M1` connecting node `1`→`2` with `E=210000` N/mm²,
`Iy=5e6` mm⁴, `Iz=2e6` mm⁴, `J=1e5` mm⁴, `A=5000` mm², and a uniform vertical
distributed load `w = -10` N/mm applied in the `FY` direction.

Run tests (requires a Pynite-compatible backend installed in the environment):

```bash
pytest -q
```

If you encounter import errors for FE classes, install `pynite`/`pynitefea` in the
active virtualenv.

## Known issues / notes

- The package dynamically imports `FEModel3D` from `Pynite` or `pynite`; make sure
   one of the implementations is installed.
- A small mismatch exists between the CLI in `__main__.py` and the exported API:
   some entrypoints reference a `WagonModel` symbol that is not provided as a
   public class — the CLI may need a minor fix. See `docs/KNOWN_ISSUES.md` (TODO).

## Documentation

Human-friendly docs live in the `docs/` directory. You can preview them with MkDocs
or any static site generator that reads Markdown.

## License

See the `LICENSE` file.
