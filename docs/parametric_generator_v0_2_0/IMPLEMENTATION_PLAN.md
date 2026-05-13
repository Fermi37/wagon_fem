# Parametric Generator v0.2.0 Implementation Plan

## Brief Conclusion

The implementation should be delivered as three sequential pull requests:

1. Schema, passenger section catalog, dispatch, and an executable single-deck vertical slice.
2. Double-deck topology and passenger-specific topology invariants.
3. Solver validation, normalized fixtures, and acceptance closure.

The current base branch is `generator`. Before branch creation, preserve the current unrelated working-tree changes:

- modified `docs/index.md`;
- untracked `docs/parametric_generator_v0_3_0/`.

## Proposed Technical Solution

The goal is to convert `docs/parametric_generator_v0_2_0` from a design package into an executable parametric generator while preserving the existing `v0.1.0` freight-wagon behavior.

Mandatory implementation path:

- extend `src/wagon_fem/parametric/schemas.py` with passenger-specific parameter groups;
- add passenger placeholder sections to `src/wagon_fem/parametric/sections.py`;
- add shared passenger topology helpers in `src/wagon_fem/parametric/passenger_common.py`;
- add `src/wagon_fem/parametric/passenger_single_deck.py`;
- add `src/wagon_fem/parametric/passenger_double_deck.py`;
- route `passenger_single_deck` and `passenger_double_deck` in `src/wagon_fem/parametric/__main__.py`;
- export passenger builders from `src/wagon_fem/parametric/__init__.py`;
- keep `GeneratedFrame`, `FrameBuilder`, and the combined `CSV` export contract as the integration foundation.

`CSV` means comma-separated values, the table-based model export format used by the solver. `YAML` means YAML Ain't Markup Language, the human-readable parameter format. `CLI` means command-line interface.

## PR Decomposition

Branch policy:

```text
PR1: base=generator, branch=codex/parametric-v0-2-0/pr1
  a: branch=codex/parametric-v0-2-0/pr1-a
  b: branch=codex/parametric-v0-2-0/pr1-b
  c: branch=codex/parametric-v0-2-0/pr1-c
PR2: base=codex/parametric-v0-2-0/pr1, branch=codex/parametric-v0-2-0/pr2
  a: branch=codex/parametric-v0-2-0/pr2-a
  b: branch=codex/parametric-v0-2-0/pr2-b
  c: branch=codex/parametric-v0-2-0/pr2-c
PR3: base=codex/parametric-v0-2-0/pr2, branch=codex/parametric-v0-2-0/pr3
  a: branch=codex/parametric-v0-2-0/pr3-a
  b: branch=codex/parametric-v0-2-0/pr3-b
  c: branch=codex/parametric-v0-2-0/pr3-c
```

Branch creation commands:

```text
git checkout generator
git pull --ff-only
git checkout -b codex/parametric-v0-2-0/pr1
git checkout codex/parametric-v0-2-0/pr1
git checkout -b codex/parametric-v0-2-0/pr1-a
git checkout codex/parametric-v0-2-0/pr1
git checkout -b codex/parametric-v0-2-0/pr1-b
git checkout codex/parametric-v0-2-0/pr1
git checkout -b codex/parametric-v0-2-0/pr1-c

git checkout codex/parametric-v0-2-0/pr1
git checkout -b codex/parametric-v0-2-0/pr2
git checkout codex/parametric-v0-2-0/pr2
git checkout -b codex/parametric-v0-2-0/pr2-a
git checkout codex/parametric-v0-2-0/pr2
git checkout -b codex/parametric-v0-2-0/pr2-b
git checkout codex/parametric-v0-2-0/pr2
git checkout -b codex/parametric-v0-2-0/pr2-c

git checkout codex/parametric-v0-2-0/pr2
git checkout -b codex/parametric-v0-2-0/pr3
git checkout codex/parametric-v0-2-0/pr3
git checkout -b codex/parametric-v0-2-0/pr3-a
git checkout codex/parametric-v0-2-0/pr3
git checkout -b codex/parametric-v0-2-0/pr3-b
git checkout codex/parametric-v0-2-0/pr3
git checkout -b codex/parametric-v0-2-0/pr3-c
```

### PR1

PR goal: schema, passenger section catalog, and executable single-deck vertical slice.

Base branch: `generator`.

Branch name: `codex/parametric-v0-2-0/pr1`.

Why this PR can merge independently: existing freight examples remain compatible, and `passenger_single_deck` becomes usable through both public API and CLI.

#### PR1-a

What to change:

- add typed schema objects for `levels`, repeated side windows, end doors, zones, equipment loads, explicit support points, and reference restraints;
- preserve the existing `open_wagon` and `covered_wagon` parameter contract.

Files / modules:

- `src/wagon_fem/parametric/schemas.py`;
- `tests/test_parametric_schemas.py`.

Why:

- passenger-only fields from the `v0.2.0` YAML examples currently do not become part of the typed parameter model.

Expected result:

- both passenger YAML files load with typed passenger-specific fields;
- existing freight YAML tests keep passing.

How to verify correctness:

- schema tests for `params.passenger_single_deck.example.yaml`;
- schema tests for `params.passenger_double_deck.example.yaml`;
- existing freight schema tests.

Mandatory or desirable: mandatory.

#### PR1-b

What to change:

- add passenger placeholder section tags and aliases:
  `center_sill_placeholder`, `side_sill_placeholder`, `bolster_beam_placeholder`,
  `end_beam_placeholder`, `cross_beam_placeholder`, `floor_longitudinal_placeholder`,
  `side_post_placeholder`, `opening_post_placeholder`, `side_belt_placeholder`,
  `end_post_placeholder`, `main_impact_post_placeholder`, `roof_bow_placeholder`,
  `roof_longitudinal_placeholder`, `interdeck_cross_beam_placeholder`,
  `interdeck_longitudinal_placeholder`.

Files / modules:

- `src/wagon_fem/parametric/sections.py`;
- `tests/test_parametric_schemas.py`.

Why:

- passenger YAML examples currently reference section tags that are absent from the first-stage catalog.

Expected result:

- every section tag referenced by the passenger examples resolves through `get_section`.

How to verify correctness:

- catalog coverage test that scans both passenger YAML files and calls `get_section` for every referenced section tag.

Mandatory or desirable: mandatory.

#### PR1-c

What to change:

- add `passenger_common.py` helpers for coordinate-line expansion, repeated-window expansion, zone boundaries, load assignment, support assignment, and required-tag sets;
- implement `build_passenger_single_deck(params)`;
- route `wagon_type == "passenger_single_deck"` in CLI dispatch;
- export `build_passenger_single_deck` from the package.

Files / modules:

- `src/wagon_fem/parametric/passenger_common.py`;
- `src/wagon_fem/parametric/passenger_single_deck.py`;
- `src/wagon_fem/parametric/__main__.py`;
- `src/wagon_fem/parametric/__init__.py`;
- `tests/test_parametric_cli.py`;
- new `tests/test_parametric_passenger_single_deck.py`.

Why:

- this provides the first executable passenger model and validates the shared contract before the double-deck extension.

Expected result:

- single-deck YAML builds a `GeneratedFrame`;
- validation passes;
- exported combined `CSV` is deterministic across repeated runs.

How to verify correctness:

- graph connectivity test;
- required structural tags test;
- CLI smoke test;
- stable normalized hash test.

Mandatory or desirable: mandatory.

### PR2

PR goal: double-deck generator and passenger topology invariants.

Base branch: `codex/parametric-v0-2-0/pr1`.

Branch name: `codex/parametric-v0-2-0/pr2`.

Why this PR can merge independently: it extends the passenger API introduced by PR1 while preserving the working single-deck path.

#### PR2-a

What to change:

- implement `build_passenger_double_deck(params)`;
- generate lowered floor, main floor, interdeck grid, side walls, roof, and end walls;
- route `wagon_type == "passenger_double_deck"` in CLI dispatch;
- export `build_passenger_double_deck` from the package.

Files / modules:

- `src/wagon_fem/parametric/passenger_double_deck.py`;
- `src/wagon_fem/parametric/passenger_common.py`;
- `src/wagon_fem/parametric/__main__.py`;
- `src/wagon_fem/parametric/__init__.py`;
- new `tests/test_parametric_passenger_double_deck.py`.

Why:

- the double-deck YAML requires topology that differs from single-deck topology through lowered-floor and interdeck structures.

Expected result:

- double-deck YAML builds a connected and valid `GeneratedFrame`.

How to verify correctness:

- required tags include `interdeck_cross_beam`, `interdeck_longitudinal`, `roof_bow`, `opening_post`, and `main_impact_post`;
- graph connectivity test passes.

Mandatory or desirable: mandatory.

#### PR2-b

What to change:

- implement stairwell boundary frames;
- omit interdeck members whose midpoint lies inside stairwell regions;
- generate strengthened transition frames at lowered-floor boundaries.

Files / modules:

- `src/wagon_fem/parametric/passenger_common.py`;
- `src/wagon_fem/parametric/passenger_double_deck.py`;
- new `tests/test_parametric_passenger_topology.py`.

Why:

- stairwell and lowered-floor transition rules are the highest-risk topology-specific part of the double-deck generator.

Expected result:

- stairwell openings affect interdeck panel members while preserving boundary beams;
- lowered-floor transition stations are present in metadata and topology.

How to verify correctness:

- tests for stairwell boundary nodes;
- tests for interdeck omission count;
- tests for transition-frame tags and graph connectivity.

Mandatory or desirable: mandatory.

#### PR2-c

What to change:

- add invariant tests for pitch sensitivity, left/right symmetry, mandatory coordinate stations, and opening boundaries.

Files / modules:

- `tests/test_parametric_passenger_topology.py`;
- possible helper fixtures in `tests/fixtures/parametric/`.

Why:

- deterministic topology needs regression protection beyond smoke tests.

Expected result:

- larger `roof_bow_pitch` reduces the number of `roof_bow` members;
- larger `side_post_pitch` reduces regular side-post count while preserving opening posts;
- window and door boundaries remain in coordinate metadata.

How to verify correctness:

- targeted pytest module for topology invariants.

Mandatory or desirable: mandatory.

### PR3

PR goal: solver validation, fixtures, and acceptance closure.

Base branch: `codex/parametric-v0-2-0/pr2`.

Branch name: `codex/parametric-v0-2-0/pr3`.

Why this PR can merge independently: it adds acceptance-level evidence and fixture discipline after both passenger generators exist.

#### PR3-a

What to change:

- add solver smoke tests for passenger single-deck and passenger double-deck combined `CSV` exports.

Files / modules:

- new `tests/test_parametric_passenger_solver.py`;
- integration with `src/wagon_fem/model.py`;
- integration with `src/wagon_fem/solver.py`.

Why:

- graph validation alone does not prove that generated models are accepted by the finite-element solver.

Expected result:

- both passenger examples load through `load_model_from_csv`;
- `run_analysis` completes;
- displacement and moment tables contain finite values.

How to verify correctness:

- finite displacement checks;
- finite moment checks;
- optional reaction-balance check once support reactions are exposed in a stable table.

Mandatory or desirable: mandatory.

#### PR3-b

What to change:

- add normalized passenger fixtures;
- record node count, member count, required tags, and normalized `CSV` hashes;
- document fixture update procedure for intentional topology changes.

Files / modules:

- `tests/fixtures/parametric/`;
- `tests/test_parametric_fixtures.py`;
- optional helper script if the current fixture workflow needs a repeatable update command.

Why:

- fixture hashes provide a stable regression guard for deterministic generation.

Expected result:

- fixture tests fail on unintended topology changes;
- intentional updates have a documented path.

How to verify correctness:

- fixture tests for single-deck and double-deck passenger outputs.

Mandatory or desirable: mandatory.

#### PR3-c

What to change:

- update `v0.2.0` documentation with implemented API names, test commands, validation status, and acceptance notes;
- add validation-report examples if they are useful for review.

Files / modules:

- `docs/parametric_generator_v0_2_0/README.md`;
- `docs/parametric_generator_v0_2_0/06_validation_and_implementation_tasks.md`;
- optional generated validation reports under `docs/parametric_generator_v0_2_0/`.

Why:

- the public implementation contract should match the delivered generator behavior.

Expected result:

- documentation states how to generate and validate both passenger examples.

How to verify correctness:

- documented CLI examples run successfully;
- doc links resolve.

Mandatory or desirable: desirable for internal use, mandatory before tagging or release.

## API / Data Model / Invariant Changes

Public API additions:

- `build_passenger_single_deck(params)`;
- `build_passenger_double_deck(params)`.

Data model additions:

- `levels`;
- `zones`;
- expanded `openings`;
- expanded `loads`;
- explicit support points and reference restraints.

Compatibility requirements:

- existing `open_wagon` and `covered_wagon` YAML files keep their current behavior;
- existing `v0.1.0` fixture hashes should remain stable unless a documented defect is fixed;
- unknown `wagon_type` should raise a clear `ValueError`;
- `passenger_single_deck` and `passenger_double_deck` should route to passenger builders.

Topology invariants:

- stable node and member identifiers for identical inputs;
- connected graph;
- positive member lengths;
- no duplicate unordered node pair with the same `member_tag`;
- retained boundary members around windows, doors, and stairwells;
- mandatory coordinate stations include bolsters, pitch stations, opening boundaries, zone boundaries, and support points.

## Tests and Validation

Use the local `uv` cache for macOS sandbox stability:

```text
UV_CACHE_DIR=.uv-cache uv run pytest -q
```

PR1 target:

```text
UV_CACHE_DIR=.uv-cache uv run pytest -q tests/test_parametric_schemas.py tests/test_parametric_cli.py tests/test_parametric_passenger_single_deck.py
```

PR2 target:

```text
UV_CACHE_DIR=.uv-cache uv run pytest -q tests/test_parametric_passenger_double_deck.py tests/test_parametric_passenger_topology.py
```

PR3 target:

```text
UV_CACHE_DIR=.uv-cache uv run pytest -q tests/test_parametric_passenger_solver.py tests/test_parametric_fixtures.py
```

Acceptance commands:

```text
UV_CACHE_DIR=.uv-cache uv run pytest -q tests/test_parametric_schemas.py tests/test_parametric_cli.py tests/test_parametric_passenger_topology.py tests/test_parametric_passenger_solver.py tests/test_parametric_fixtures.py
UV_CACHE_DIR=.uv-cache uv run python -m wagon_fem.parametric docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml --output tmp/passenger_single.csv --validate
UV_CACHE_DIR=.uv-cache uv run python -m wagon_fem.parametric docs/parametric_generator_v0_2_0/params.passenger_double_deck.example.yaml --output tmp/passenger_double.csv --validate
```

## Risks, Blockers, Dependencies

Current branch-work blocker:

- the working tree has unrelated user changes in `docs/index.md` and `docs/parametric_generator_v0_3_0/`;
- these changes should be preserved before creating implementation branches.

Main technical risks:

- double-deck support stability;
- over-dense beam grids causing slow solver smoke tests;
- placeholder sections causing ill-conditioned finite-element systems;
- ambiguous mapping between passenger `side_sill` and existing freight `side_longitudinal`;
- support-reaction balance checks may require additional stable solver output APIs.

Mitigation:

- keep PR1 focused on schema, catalog, dispatch, and single-deck export/validation;
- implement double-deck topology before solver smoke tests;
- use `solver_stability_clamped_reference` as a diagnostic support scheme if `four_point_bolster_reference` is underconstrained;
- add fixture hashes only after topology invariants are stable.
