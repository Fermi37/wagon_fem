# Architecture

## Target Package Layout

```text
src/wagon_fem/
  parametric/
    __init__.py
    schemas.py
    sections.py
    grid.py
    builder.py
    open_wagon.py
    covered_wagon.py
    export.py
    validation.py
```

## Responsibilities

`schemas.py` defines typed parameter objects for geometry, layout, openings, sections, loads, and supports.

`sections.py` stores the first-stage section catalog. Each section class contains `E`, `A`, `Iy`, `Iz`, and `J`.

`grid.py` generates ordered coordinate lines along `x`, `y`, and `z`. It also merges mandatory coordinates such as end beams, bolster beams, door boundaries, and post coordinates.

`builder.py` contains `FrameBuilder`, a small construction API for nodes and members. `FrameBuilder` means a helper object that adds unique nodes, prevents duplicate members, and records semantic tags.

`open_wagon.py` implements `build_open_wagon(params)`.

`covered_wagon.py` implements `build_covered_wagon(params)`.

`export.py` converts internal tables to the combined `wagon_fem` CSV schema.

`validation.py` performs structural and data checks before solver execution.

## Data Flow

```text
params.yaml / params.json
        |
        v
schemas.py
        |
        v
grid.py + sections.py
        |
        v
open_wagon.py / covered_wagon.py
        |
        v
nodes_df, edges_df, metadata
        |
        v
validation.py
        |
        v
export.py
        |
        v
wagon_fem CSV
        |
        v
load_model_from_csv(...)
        |
        v
Pynite analysis
```

## Public API

```python
from wagon_fem.parametric import load_params, build_open_wagon, export_model_csv

params = load_params("params.open_wagon.yaml")
model = build_open_wagon(params)
csv_path = export_model_csv(model.nodes_df, model.edges_df, "open_wagon.csv")
```

## Internal Model Object

The generator should return a compact result object:

```python
@dataclass
class GeneratedFrame:
    nodes_df: pd.DataFrame
    edges_df: pd.DataFrame
    node_tags: dict[int, set[str]]
    edge_tags: dict[int, set[str]]
    metadata: dict[str, object]
```

Tags support later filtering by structural group, for example `center_sill`, `side_beam`, `bolster_beam`, `side_post`, `roof_bow`, and `diagonal_tie`.

## Design Constraints

The generator must keep node identifiers stable for identical input parameters.

The generator must keep member identifiers stable for identical input parameters.

The generator must preserve the existing `wagon_fem` loader contract.

The generator should use deterministic sorting of coordinates and members.

The generator should separate geometry, section assignment, load assignment, and export.
