# Implementation Tasks

## Milestone 1: Data Contracts

1. Add `src/wagon_fem/parametric/__init__.py`.
2. Add parameter schemas in `schemas.py`.
3. Add section catalog in `sections.py`.
4. Add a YAML or JSON loader for parameter files.
5. Add tests for default parameter construction.

## Milestone 2: FrameBuilder

1. Implement stable node creation by coordinate key.
2. Implement stable member creation by node pair and member tag.
3. Store `node_tags` and `edge_tags`.
4. Add symmetric helper methods for left and right side members.
5. Add tests for duplicate-node and duplicate-member handling.

## Milestone 3: Grid Generation

1. Generate mandatory `x` lines from ends, bolsters, cross beams, posts, and openings.
2. Generate `y` lines from floor level, height divisions, wall top, and roof points.
3. Generate `z` lines from centerline, side beams, and optional floor longitudinal lines.
4. Add tests for deterministic coordinate ordering.

## Milestone 4: Open Wagon Generator

1. Generate frame members.
2. Generate side-wall posts, belts, and diagonals.
3. Generate end-wall posts, belts, and ties.
4. Assign section tags by structural role.
5. Add default supports near bolster positions.
6. Add tests for graph connectivity and CSV export.

## Milestone 5: Covered Wagon Generator

1. Reuse frame generation.
2. Add side doors and omit panel members inside openings.
3. Add door posts, lintels, and threshold members.
4. Add roof side lines, bows, ridge line, and roof longitudinal members.
5. Add tests for roof generation and door opening behavior.

## Milestone 6: Export and Validation

1. Implement combined CSV export matching `wagon_fem` expectations.
2. Implement validation checks from `06_validation_plan.md`.
3. Add a CLI command for generating CSV from a parameter file.
4. Add solver smoke tests through `load_model_from_csv(...)`.

## Milestone 7: Documentation and Examples

1. Add generated example CSV files for default open and covered wagons.
2. Add a short usage page under `docs/`.
3. Add references from `docs/index.md`.
4. Document how to replace approximate sections with real section properties.

## Suggested Branch

```bash
git checkout -b codex/parametric-generator-v0.1.0
```

## Suggested Test Commands

```bash
uv run pytest -q
uv run python -m wagon_fem.parametric examples/open_wagon.yaml
```
