# Validation Plan

## Geometry Checks

The generator should validate:

- unique node identifiers;
- unique edge identifiers;
- positive member length;
- coordinates inside declared frame and tank bounds;
- coincident-node merge behavior;
- absence of duplicate members for the same node pair and member tag;
- symmetric tank ring coordinates for symmetric parameter files;
- valid angular division count of at least `6`.

## Tank-Specific Checks

The generator should verify:

- every tank station has the same angular node count;
- each ring is closed;
- each angular generator forms a connected longitudinal chain;
- tank end rings exist at `tank.x_start` and `tank.x_end`;
- saddle positions coincide with generated tank stations;
- every saddle or lug connects a tank node to a frame node;
- strap anchor angles map to existing or interpolated angular nodes.

## Graph Checks

The full member graph should be connected for the default tank wagon. Optional equipment members may form separate groups only if explicitly marked as non-structural metadata.

Mandatory member tags for the default tank wagon:

- `center_sill`;
- `bolster_beam`;
- `end_beam`;
- `cross_beam`;
- `tank_longitudinal`;
- `tank_ring`;
- `tank_end_ring`;
- `saddle_support`;
- `middle_tank_lug`.

## Load Checks

For every enabled load group:

- total generated nodal load should match the requested total force within tolerance;
- distributed loads should have a valid global direction;
- payload loads should be attached to tank members or tank nodes;
- end loads should be attached to draft-gear or center-sill nodes;
- load placement method should be recorded in metadata.

## Support Checks

The support scheme should remove rigid-body modes. Each scheme should be tested for:

- successful static solve;
- finite reactions;
- finite displacements;
- force-balance error within documented tolerance;
- absence of accidental fully restrained nodes in ordinary study cases.

## Solver Checks

The validation suite should run:

```text
params.tank_wagon.example.yaml
        |
        v
load_params(...)
        |
        v
build_tank_wagon(...)
        |
        v
validate_generated_frame(...)
        |
        v
export_model_csv(...)
        |
        v
load_model_from_csv(...)
        |
        v
static solve
        |
        v
member forces, moments, reactions
```

## Numerical Smoke Tests

Minimum smoke tests:

1. Default tank wagon generates non-empty node and edge tables.
2. Every generated edge references existing nodes.
3. Tank rings are closed for all stations.
4. Tank longitudinal generators are connected from `tank.x_start` to `tank.x_end`.
5. Saddle and lug members connect tank and frame nodes.
6. Total vertical load equals requested tare plus payload force within tolerance.
7. Default support scheme solves with finite reactions.
8. Increasing tank-ring density changes node and member counts deterministically.
9. Repeated generation from identical parameters produces identical normalized CSV.
10. Result tables can be grouped by `member_tag` for force-flow summaries.

## Visual Checks

The generated model should be inspected in a 3D viewer. The first visual review should confirm:

- tank cylinder lattice has the expected radius and length;
- underframe lies below the tank centerline;
- bolsters align with support positions;
- saddle members connect the bottom tank region to frame members;
- left and right strap ties are symmetric for symmetric parameters;
- no isolated structural member appears in the default model.

## Acceptance Criteria

Version `0.3.0` documentation is implementation-ready when:

- the parameter contract covers geometry, tank, frame, attachments, loads, supports, and generation controls;
- the default YAML example can be converted into an unambiguous topology;
- all mandatory member tags are defined;
- validation rules cover geometry, graph, tank lattice, loads, supports, and solver execution;
- the implementation task list supports a vertical slice from YAML input to member-force output.

