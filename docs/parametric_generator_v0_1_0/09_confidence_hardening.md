# Confidence Hardening

## Purpose

This document defines the additional verification layers required to raise confidence in `0.1.0-parametric-generator` from an implementation-ready plan to a solver-backed engineering prototype.

`CI` means continuous integration, an automated test environment that runs checks on every relevant code change.

`SHA-256` means a deterministic cryptographic hash used to detect accidental changes in normalized generated files.

`Golden fixture` means an approved reference artifact used for regression comparison.

## Target Confidence

The target confidence range is `0.88` to `0.92` after the checks below are implemented and passing on default examples.

The confidence estimate remains conditional on the modeling level stated in [01_scope_and_assumptions.md](01_scope_and_assumptions.md): the model provides qualitative force paths and first numerical estimates for a beam-only representation.

## Verification Layers

### 1. Vertical Slice

Implement a minimal default open-wagon route:

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

Required assertions:

- generated node and member tables are non-empty;
- mandatory structural tags are present;
- exported CSV loads through `wagon_fem.model.load_model_from_csv`;
- static analysis completes;
- member force, reaction, and displacement outputs contain finite values.

### 2. Local-Axis Mini-Models

Create four deliberately small models that isolate finite-element local-axis behavior:

| Case | Geometry | Purpose |
|---|---|---|
| `axis_x` | beam along `x` | verify longitudinal member bending response |
| `axis_y` | beam along `y` | verify vertical post orientation |
| `axis_z` | beam along `z` | verify transverse beam orientation |
| `axis_roof_inclined` | inclined roof-bow segment | verify sloped roof member behavior |

Use asymmetric stiffness values such as `Iy = 1.0e6` and `Iz = 1.0e8`. The test should make a swapped-axis error visible through a large displacement-ratio change.

Acceptance requirements:

- each case solves with finite displacements;
- the strong-axis response is stiffer than the weak-axis response;
- the expected local-axis interpretation is documented in the test or fixture metadata.

### 3. Support-Scheme Matrix

Support schemes should be named and validated independently:

| Scheme | Intended use | Required outcome |
|---|---|---|
| `two_bolster_reference` | default engineering estimate | solve with finite reactions and displacements |
| `four_point_vertical` | load-distribution study | solve with balanced vertical reactions |
| `solver_stability_clamped_reference` | regression and smoke testing | solve robustly with documented reference restraints |

Each scheme should report:

- restrained node identifiers;
- restrained degrees of freedom;
- total applied vertical load;
- total vertical reaction;
- maximum displacement magnitude;
- maximum member force magnitude.

### 4. Topology Invariants

The generator should enforce invariant checks that are independent of solver behavior:

- graph connectivity;
- left-right symmetry around `z = 0`;
- positive member lengths;
- unique coordinate keys after rounding;
- duplicate-member rejection by unordered node pair and member tag;
- mandatory structural tag coverage;
- deterministic `node_id` and `edge_id` generation;
- correct covered-wagon door-opening omissions;
- roof ridge and roof-bow continuity for covered wagons.

These checks should run before solver tests so topology defects produce direct diagnostics.

### 5. Golden Fixtures

Create normalized reference exports for the default open wagon and default covered wagon.

Normalization rules:

- sort nodes by `node_id`;
- sort members by `edge_id`;
- round floating-point coordinates and section values to the documented tolerance;
- use a stable column order;
- write line endings consistently.

Fixture checks:

- node count;
- member count;
- required structural tags;
- key coordinates at ends, bolsters, side beams, wall top, and roof ridge where applicable;
- `SHA-256` hash of the normalized CSV.

Fixture updates should require an explicit note describing the intended topology or export-contract change.

## Recommended Implementation Order

1. Implement the vertical slice for the default open wagon.
2. Add local-axis mini-models before interpreting section-property trends.
3. Add the support-scheme matrix before expanding load placement rules.
4. Add topology invariants before implementing covered-wagon openings.
5. Add golden fixtures before changing generator defaults.

## Confidence Exit Criteria

The confidence range may be raised to `0.88` to `0.92` when:

- the vertical slice passes in `CI`;
- all four local-axis mini-models pass;
- at least two support schemes solve with finite values and balanced reactions;
- topology invariants pass for default open and covered wagons;
- golden fixtures pass for both default wagon types;
- the solver smoke tests run through `load_model_from_csv(...)` using generated CSV files.
