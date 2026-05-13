# Validation Plan

## Geometry Checks

The generator should validate:

- all node identifiers are unique;
- all edge identifiers are unique;
- each edge references existing nodes;
- each member has positive geometric length;
- coincident nodes are merged or reported;
- duplicate members are rejected;
- generated coordinates stay within `[0, L]`, `[floor_y, floor_y + side_height + roof_height]`, and `[-B/2, B/2]` unless explicitly allowed.

## Graph Checks

The member graph should be connected for the generated body model.

Each non-support node should have enough incident members for the intended topology.

Wall-panel nodes introduced for height divisions should be connected to vertical and horizontal members.

Diagonal ties should connect opposite corners of a panel.

## Support Checks

The model should include enough restraints to remove rigid-body motion for the selected analysis case.

The implementation should expose a named support scheme so each generated model can be reproduced and audited.

Recommended first-stage support schemes:

### `two_bolster_reference`

- one primary bolster node with translations restrained in `x`, `y`, and `z`;
- a second bolster node with vertical and transverse translations restrained;
- additional vertical supports at paired side or bolster points for load distribution studies.

### `four_point_vertical`

- paired vertical restraints at both bolster cross beams;
- one longitudinal restraint at the primary bolster;
- one transverse restraint at each bolster line.

### `solver_stability_clamped_reference`

- fully restrained primary reference node;
- vertical and transverse restraints at secondary support nodes;
- intended for regression and solver smoke tests where stable execution is the primary objective.

Each support scheme should be tested for:

- successful static solve;
- finite support reactions;
- finite nodal displacements;
- reaction balance against applied vertical load within a documented tolerance;
- absence of unintended fully restrained nodes except in `solver_stability_clamped_reference`.

The exact support scheme should be exported through node support columns.

## Solver Checks

The implementation should run:

- CSV export;
- `load_model_from_csv(...)`;
- Pynite model construction;
- static analysis;
- moment table extraction;
- displacement table extraction.

## Vertical-Slice Checks

The first implementation increment should prove the complete route for the default open wagon:

```text
params.open_wagon.example.yaml
        |
        v
load_params(...)
        |
        v
build_open_wagon(...)
        |
        v
export_model_csv(...)
        |
        v
load_model_from_csv(...)
        |
        v
Pynite static analysis
        |
        v
member forces, reactions, displacements
```

This check should run in continuous integration once the parametric package is available. The test should assert that the model contains members with the tags `center_sill`, `side_longitudinal`, `bolster_beam`, `cross_beam`, `side_post`, `upper_belt`, and `diagonal_tie`.

## Local-Axis Verification

The implementation should include four minimal beam models that verify how the finite-element backend interprets `Iy`, `Iz`, and `J`:

1. Longitudinal beam along `x`.
2. Vertical beam along `y`.
3. Transverse beam along `z`.
4. Inclined roof-bow segment.

Each verification case should use a deliberately asymmetric section, for example `Iy = 1.0e6` and `Iz = 1.0e8`, so axis swaps are numerically visible. The expected displacement trend should be documented for each orientation before the test is accepted.

## Topology Invariants

Every generated default model should satisfy these graph and symmetry invariants:

- the member graph is connected;
- left and right side-wall node coordinates are symmetric with respect to `z = 0`;
- every mandatory structural tag appears at least once;
- every member has positive length after coordinate rounding;
- no duplicate unordered node pair exists for the same member tag;
- door-opening rules remove panel belts and diagonal ties whose segment midpoints lie inside an opening;
- repeated generation from identical parameters produces identical `node_id`, `edge_id`, coordinate tables, and member tables after normalization.

## Golden Fixtures

The implementation should create normalized fixture exports for:

- default open wagon;
- default covered wagon.

The fixture comparison should include:

- node count;
- member count;
- mandatory structural tags;
- key coordinates at ends, bolsters, side beams, wall top, and roof ridge where applicable;
- SHA-256 hash of a normalized CSV export.

`SHA-256` means a deterministic cryptographic hash used here to detect accidental export changes.

## Numerical Smoke Tests

Minimum tests:

1. Open wagon with default parameters generates non-empty nodes and edges.
2. Covered wagon with default parameters generates roof members and door boundary members.
3. Every generated edge references an existing node.
4. Graph connectivity test passes.
5. Combined CSV can be loaded by `wagon_fem.model.load_model_from_csv`.
6. A simple supported default model solves and produces member force output.
7. Increasing center-sill stiffness changes force distribution in the expected direction.
8. All named support schemes solve or report a documented validation failure.
9. Local-axis verification cases show the expected strong-axis and weak-axis displacement trends.
10. Golden fixture hashes remain stable unless an intentional topology change is recorded.

## Visual Checks

The generated geometry should be inspected in the existing 3D viewer. The first visual review should confirm:

- symmetric left and right side geometry;
- correct bolster locations;
- correct side-wall height divisions;
- correct roof bow placement for covered wagons;
- correct door opening omission for covered wagons;
- absence of isolated members.

## Acceptance Criteria

Version `0.1.0-parametric-generator` is accepted when:

- both wagon generators produce valid CSV files;
- validation passes for default examples;
- solver execution succeeds for a supported default model;
- generated members carry section tags;
- output moments and forces can be traced back to structural groups;
- the vertical-slice check passes for the default open wagon;
- local-axis verification passes for the four canonical orientations;
- at least two support schemes solve with finite reactions and displacements;
- golden fixture comparisons pass for default open and covered wagons.
