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

Recommended first-stage support scheme:

- one primary bolster node with translations restrained in `x`, `y`, and `z`;
- a second bolster node with vertical and transverse translations restrained;
- additional vertical supports at paired side or bolster points for load distribution studies.

The exact support scheme should be exported through node support columns.

## Solver Checks

The implementation should run:

- CSV export;
- `load_model_from_csv(...)`;
- Pynite model construction;
- static analysis;
- moment table extraction;
- displacement table extraction.

## Numerical Smoke Tests

Minimum tests:

1. Open wagon with default parameters generates non-empty nodes and edges.
2. Covered wagon with default parameters generates roof members and door boundary members.
3. Every generated edge references an existing node.
4. Graph connectivity test passes.
5. Combined CSV can be loaded by `wagon_fem.model.load_model_from_csv`.
6. A simple supported default model solves and produces member force output.
7. Increasing center-sill stiffness changes force distribution in the expected direction.

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
- output moments and forces can be traced back to structural groups.
