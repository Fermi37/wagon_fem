# Implementation Tasks

## Phase 1 - Schema Extension

1. Add `TankParams`, `FrameParams`, `AttachmentParams`, and tank-specific load parameter dataclasses.
2. Extend `wagon_params_from_dict(...)` to parse `wagon_type: tank_wagon`.
3. Preserve all existing `v0.1.0` fields for open and covered wagons.
4. Add validation for tank radius, length, angular divisions, support station positions, and saddle spans.

## Phase 2 - Tank Topology Builder

1. Implement `build_tank_wagon(params)`.
2. Generate deterministic frame stations and tank stations.
3. Generate underframe nodes and members.
4. Generate tank ring nodes and ring members.
5. Generate tank longitudinal members.
6. Generate tank end-ring and optional end-dish spoke members.
7. Generate saddle, middle-lug, pad, and strap members.

## Phase 3 - Load and Support Assignment

1. Implement vertical tare and payload load assignment.
2. Implement end longitudinal load assignment.
3. Implement lateral inertial load assignment as an optional first-stage case.
4. Implement `two_bolster_with_reference_lock`.
5. Implement `four_point_bolster_reference`.
6. Export load-case metadata and support-scheme metadata.

## Phase 4 - Export and Validation

1. Reuse the combined CSV export route.
2. Preserve `section_tag`, `member_tag`, and `n_segments` columns.
3. Add tank-specific graph checks.
4. Add load-balance checks.
5. Add solver smoke checks.
6. Add normalized fixture export for the default tank wagon.

## Phase 5 - Postprocessing

1. Add grouping of member forces by `member_tag`.
2. Add station-based summaries for center sill, bolsters, tank rings, and saddle supports.
3. Add maximum axial force and bending moment tables by structural group.
4. Add reaction summary by support station.
5. Add optional CSV export for force-flow comparison across parameter variants.

## Phase 6 - Documentation and Examples

1. Keep `params.tank_wagon.example.yaml` synchronized with the parsed schema.
2. Add a minimal tank-car generation command to the main documentation.
3. Add a visual topology snapshot after implementation.
4. Record known modeling limits in release notes.

## Definition of Done

The implementation is complete when:

- the default tank example generates a valid CSV;
- validation passes for the default tank example;
- the existing solver loads the generated CSV;
- static analysis produces finite reactions and member forces;
- member-force summaries can be grouped by tank and frame tags;
- repeated generation is deterministic.

