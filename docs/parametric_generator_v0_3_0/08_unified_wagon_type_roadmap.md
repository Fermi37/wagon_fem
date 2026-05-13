# Unified Wagon-Type Roadmap

## Goal

The generator should evolve into a shared parametric package for freight and passenger rolling stock while keeping each wagon family in a specialized topology module.

## Type Registry

The public interface should route by `wagon_type`:

```text
open_wagon              -> build_open_wagon(...)
covered_wagon           -> build_covered_wagon(...)
tank_wagon              -> build_tank_wagon(...)
passenger_single_deck   -> build_passenger_single_deck(...)
passenger_double_deck   -> build_passenger_double_deck(...)
```

The registry should return one `GeneratedFrame` object for every wagon type.

## Shared Schema Layers

Shared groups:

- `metadata`;
- `geometry`;
- `layout`;
- `sections`;
- `loads`;
- `supports`;
- `generation`.

Family-specific groups:

- `tank` and `attachments` for tank wagons;
- `openings` and `roof` for covered freight wagons;
- `levels`, `zones`, and passenger openings for passenger cars.

## Shared Tags

Common tags should remain stable across wagon families:

- `center_sill`;
- `bolster_beam`;
- `end_beam`;
- `cross_beam`;
- `side_beam`;
- `floor_longitudinal`;
- `diagonal_tie`;
- `support_stub`.

Tank-specific tags should use the `tank_` prefix where the member belongs to the tank lattice:

- `tank_longitudinal`;
- `tank_ring`;
- `tank_end_ring`;
- `tank_end_dish_spoke`;
- `tank_top_stringer`;
- `tank_bottom_stringer`.

Passenger-specific tags should use semantic body-frame names already introduced by `v0.2.0`.

## Shared Validation

All wagon types should pass:

- node and edge integrity checks;
- graph connectivity checks;
- support stability checks;
- load-balance checks;
- deterministic export checks;
- solver smoke checks.

Each wagon type should also define its own mandatory tags and topology invariants.

## Section-Catalog Policy

The section catalog should support semantic aliases for every wagon family. First-stage values may remain approximate while member forces and moments are the main deliverable.

Later calibrated catalogs can be introduced by changing `sections.catalog` and preserving member tags.

## Implementation Sequence

Recommended sequence:

1. Stabilize the existing open and covered freight wagon path.
2. Add `tank_wagon` as the first cylindrical-body freight topology.
3. Add passenger single-deck and double-deck builders using the `v0.2.0` contract.
4. Unify postprocessing across all wagon types.
5. Introduce calibrated section libraries and reference fixtures.

