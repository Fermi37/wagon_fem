# Wagon FEM Project

Проект для расчета моментов в балках конструкции вагона.

## Установка и запуск

1. Установите зависимости (требуется `uv`):
   ```bash
   uv sync
    
## CSV format (nodes + edges)

The loader accepts a single CSV file that may contain two tables concatenated: a node table followed by an edge table. The loader will split the file by detecting an edge header (e.g. a line containing "edge_id" or "start_node").

Node table recommended columns (case-insensitive):
- `node_id` or `id` (integer)
- `x`, `y`, `z` — coordinates
- Optional support flags: `support_dx`, `support_dy`, `support_dz`, `support_rx`, `support_ry`, `support_rz` (truthy values: 1/true/yes/x)
- Optional single `supports` column with comma-separated flags, e.g. `DX,DY` or `dx,dy`
- Optional nodal loads: `FX`, `FY`, `FZ`, `MX`, `MY`, `MZ` (numeric)

Edge table recommended columns (case-insensitive):
- `edge_id` (or `id`)
- `start_node`, `end_node` (node ids)
- Optional section/material properties: `E`, `Iy`, `Iz`, `J`, `A`

When loading a CSV via the UI you can toggle whether node supports & nodal loads from the CSV are applied.

## Pynite import note

Some Python distributions expose the package as `Pynite` (capital P) while others install `pynite`. This project imports the FE class dynamically from either `Pynite.FEModel3D` or `pynite.FEModel3D`, so simply having `pynite` installed in the virtualenv is sufficient. If you hit import errors, ensure the package is installed in the project's `.venv`.
