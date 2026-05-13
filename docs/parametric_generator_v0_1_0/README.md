# Parametric Wagon Generator v0.1.0

This folder contains the implementation documents for a parametric generator of wagon beam schemes.

`CSV` means comma-separated values, a tabular exchange format with delimiter-separated columns. In this project, `CSV` is used as the input contract for `wagon_fem`.

`DataFrame` means an in-memory table, typically represented by `pandas.DataFrame`.

`nodes_df` means the node table. It stores `node_id`, `x`, `y`, and `z`.

`edges_df` means the member table. It stores `edge_id`, `start_node`, `end_node`, `E`, `A`, `Iy`, `Iz`, `J`, and load fields.

## Document Set

- [01_scope_and_assumptions.md](01_scope_and_assumptions.md) - goal, assumptions, and modeling level.
- [02_architecture.md](02_architecture.md) - proposed Python package structure and data flow.
- [03_csv_contract.md](03_csv_contract.md) - exact input and output schema for `wagon_fem`.
- [04_section_estimates.md](04_section_estimates.md) - approximate first-stage beam properties.
- [05_generation_rules.md](05_generation_rules.md) - topology rules for open and covered wagons.
- [06_validation_plan.md](06_validation_plan.md) - checks for geometry, graph connectivity, supports, and solvability.
- [07_implementation_tasks.md](07_implementation_tasks.md) - executable task list for implementation.
- [08_body_scheme_illustration.md](08_body_scheme_illustration.md) - conceptual body-frame illustration with topology explanations.
- [09_confidence_hardening.md](09_confidence_hardening.md) - verification layers for raising implementation confidence before full delivery.
- [params.open_wagon.example.yaml](params.open_wagon.example.yaml) - starter parameter file.
- [params.covered_wagon.example.yaml](params.covered_wagon.example.yaml) - starter covered-wagon parameter file.

## Implemented Entry Points

Generate and validate the default open-wagon CSV:

```bash
python -m wagon_fem.parametric params.open_wagon.example.yaml --output ../../tmp/open_wagon.csv --validate
```

Run the existing solver on the generated CSV:

```bash
python -m wagon_fem ../../tmp/open_wagon.csv
```

## Version Policy

The current documentation version is `0.1.0-parametric-generator`.

Version `0.1.x` covers beam-only generator work. Version `0.2.x` should cover calibrated section libraries and stronger verification against reference examples. Version `0.3.x` should cover plate-beam extensions.
