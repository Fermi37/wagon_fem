# Validation and Implementation Tasks

## Geometry Validation

The generator should validate:

- unique node identifiers;
- unique member identifiers;
- positive member lengths;
- coordinate bounds for `x`, `y`, and `z`;
- merged coincident nodes within tolerance;
- absence of duplicate unordered node pairs for the same member tag;
- generated opening boundaries inside body limits;
- generated lowered-floor and stairwell zones inside body limits;
- roof coordinates inside the declared gauge envelope when a gauge check is implemented.

## Graph Validation

The generated member graph should be connected.

Each side-wall opening should retain boundary posts and boundary belts.

Each stairwell opening should retain interdeck boundary beams.

Each bolster line should connect the center sill, side sills, floor longitudinals, and side-wall bases.

Each roof bow should connect both roof side rails and the ridge or top longitudinal line.

For double-deck cars, the interdeck graph should connect to side-wall posts and selected transverse frames.

## Solver Validation

Minimum solver checks:

1. Generate passenger single-deck `CSV`.
2. Generate passenger double-deck `CSV`.
3. Load both files through `wagon_fem.model.load_model_from_csv`.
4. Solve both models using a stable named support scheme.
5. Extract member forces and bending moments.
6. Check finite support reactions and finite nodal displacements.
7. Check vertical reaction balance against applied vertical loads within a documented tolerance.

## Topology Invariants

The default examples should satisfy:

- mandatory structural tags are present;
- left and right side walls are symmetric when the parameter file uses symmetric openings;
- window omissions affect only equivalent panel members;
- stairwell omissions affect only interdeck panel members;
- repeated generation produces identical normalized tables;
- increasing roof-bow pitch reduces the number of roof-bow members;
- increasing side-post pitch reduces the number of regular side posts while keeping opening posts.

## Implementation Sequence

### Milestone 1: Schema Extension

1. Add passenger-specific schema objects for `levels`, `zones`, side windows, end doors, roof openings, stairwells, and equipment loads.
2. Keep backward compatibility for `open_wagon` and `covered_wagon` parameter files.
3. Add schema tests for both passenger example files.

### Milestone 2: Common Passenger Builder

1. Add coordinate-line expansion for repeated windows and zones.
2. Add helpers for opening midpoint omission.
3. Add member tags listed in [02_passenger_body_beam_scheme.md](02_passenger_body_beam_scheme.md).
4. Add topology metadata for generated coordinate lines and zones.

### Milestone 3: Single-Deck Generator

1. Generate underframe, side walls, end walls, and roof.
2. Implement side-window and door opening rules.
3. Implement passenger support schemes.
4. Add `CSV` export smoke tests.

### Milestone 4: Double-Deck Generator

1. Generate lowered-floor central zone.
2. Generate interdeck grid.
3. Generate stairwell frames and omission rules.
4. Generate strengthened transition frames.
5. Add double-deck topology and solver smoke tests.

### Milestone 5: Verification Fixtures

1. Add normalized passenger single-deck fixture.
2. Add normalized passenger double-deck fixture.
3. Record node count, member count, mandatory tags, and normalized file hash.
4. Add a fixture update procedure for intentional topology changes.

## Acceptance Criteria

Version `0.2.0-passenger-body-frame` is ready for implementation when:

- parameter files cover single-deck and double-deck passenger bodies;
- generation rules define all mandatory structural groups;
- opening, stairwell, roof, and interdeck rules are explicit;
- validation checks cover geometry, graph connectivity, supports, and solver execution;
- source assumptions for double-deck cars are documented with URLs;
- the output remains compatible with the existing combined `CSV` contract.

