# Usage

This page contains quick examples to run the package from the command line, the
Gradio UI, or programmatically from Python.

## Quickstart (CLI)

Install the package (see README) and run the CLI with a CSV file:

```bash
python -m wagon_fem data/wagon_frame.csv
```

The CLI accepts `--supports` to apply supports from the command line. Example:

```bash
python -m wagon_fem data/wagon_frame.csv --supports 1:True,True,True,False,False,False
```

If the package is installed, a console entrypoint is available:

```bash
# Installed entrypoint (preferred):
wagon-fem-ui serve --port 7860 --share
# Or run the Typer CLI module directly:
python -m wagon_fem.ui_cli serve --port 7860 --share
# The Typer wrapper supports flags for --host, --port, --share, --no-queue and
# --log-level. For backward compatibility the UI module also exposes a
# `main()` entrypoint (e.g. `python -m wagon_fem.ui`) but the Typer CLI is
# recommended when you need to configure host/port/share.
```

## Programmatic example

```python
from wagon_fem.model import load_model_from_csv
from wagon_fem.solver import run_analysis, get_moments_table

model = load_model_from_csv('data/wagon_frame.csv')
model = run_analysis(model)
df = get_moments_table(model)
print(df)
```

## CSV input format

The loader accepts a CSV that contains a node table followed by an edge table
in the same file (the loader detects the start of the edge table by looking for
headers like `edge_id`, `start_node` or `end_node`).

Example (excerpt from `data/wagon_frame.csv`):

```
node_id,x,y,z,support_dx,support_dy,support_dz,support_rx,support_ry,support_rz,fx,fy,fz,mx,my,mz
1,0,0,0,1,1,1,1,1,1,0,0,0,0,0
2,2000,0,0,0,0,0,0,0,0,0,0,0,0,0
...
edge_id,start_node,end_node,E,Iy,Iz,J,A,w,dist_dir
1,1,2,210000,5000000,2000000,100000,5000,-10,FY
2,2,3,210000,5000000,2000000,100000,5000,-10,FY
```

Notes:
- Node table columns: `node_id`/`id`, `x`, `y`, `z` and optional `support_*` or `fx,fy,fz`.
- Edge table columns: `edge_id`/`id`, `start_node`, `end_node`, and optional
  section/material properties (`E`, `Iy`, `Iz`, `J`, `A`) and distributed loads
  (`w`, `w1`, `w2`, `dist_dir`).

## Edge columns (detailed)

Field-by-field explanation and loader behavior:

- `edge_id` / `id`: unique member identifier. Used to name created members; if
  missing the loader falls back to `M{start}_{end}`.

- `start_node`, `end_node`: node identifiers the member connects — must match
  node IDs from the nodes table.

- Section/material properties:
  - `E`: Young's modulus (N/mm²). Default: `210000`.
  - `Iy`, `Iz`: second moments of area (mm⁴).
  - `J`: torsional constant (mm⁴).
  - `A`: cross-sectional area (mm²). Default: `1.0`.

  The loader will try to add a material (`mat_{int(E)}`) and a section
  (`S_{int(A)}_{int(Iy)}_{int(Iz)}_{int(J)}`) to the FE model and reuse them
  where possible.

- Distributed loads:
  - `w`: uniform distributed load (N/mm). If `w1`/`w2` are not provided, `w`
    is applied to both ends.
  - `w1`, `w2`: linearly-varying start/end intensities (N/mm).
  - `dist_dir` / `load_dir` / `dir`: direction of the distributed load (uppercased),
    default `FY`. Common values: `FX`, `FY`, `FZ`.

  When members are split into sub-members the loader interpolates the load
  intensities across pieces and applies loads to each sub-member.

- Aliases & options: `area` → `A`, `w_start`/`w_end` → `w1`/`w2`, and `n_segments`
  to force subdivision. Alternatively `max_member_length` passed to the loader
  controls automatic segmentation.

- Units & conventions: lengths in mm, forces in N, E in N/mm², distributed loads in N/mm,
  areas in mm², moments in N·mm.

Example:
```
1,1,2,210000,5000000,2000000,100000,5000,-10,FY
```
→ `M1`, nodes `1`→`2`, `E=210000` N/mm², `Iy=5e6` mm⁴, `Iz=2e6` mm⁴, `J=1e5` mm⁴,
`A=5000` mm², uniform load `w=-10` N/mm in `FY`.
