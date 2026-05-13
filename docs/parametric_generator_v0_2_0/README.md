# Parametric Wagon Generator v0.2.0

This folder contains the design documents for extending the parametric wagon generator to passenger-car body frames.

`МКЭ` means the finite element method. In this project, the first passenger-car model is a spatial beam model intended for force-flow analysis, member-force extraction, and bending-moment extraction. Section properties are retained as technical placeholders because the current stage prioritizes topology, connectivity, support placement, and load paths.

## Document Set

- [01_scope_and_modeling_assumptions.md](01_scope_and_modeling_assumptions.md) - purpose, model level, and accepted engineering assumptions.
- [02_passenger_body_beam_scheme.md](02_passenger_body_beam_scheme.md) - passenger-car body-frame representation as a connected beam system.
- [03_parameter_contract.md](03_parameter_contract.md) - parameter groups for single-deck and double-deck passenger cars.
- [04_generation_rules.md](04_generation_rules.md) - deterministic topology rules for beams, nodes, openings, floors, roof, and supports.
- [05_double_deck_reference_notes.md](05_double_deck_reference_notes.md) - source-grounded notes for double-deck passenger cars.
- [06_validation_and_implementation_tasks.md](06_validation_and_implementation_tasks.md) - validation checks and implementation sequence.
- [07_body_scheme_illustration.md](07_body_scheme_illustration.md) - visual topology reference for passenger-car beam schemes.
- [08_single_deck_krv11_alignment.md](08_single_deck_krv11_alignment.md) - alignment of the single-deck passenger-car beam model with KRV chapter 11.
- [params.passenger_single_deck.example.yaml](params.passenger_single_deck.example.yaml) - starter parameters for a single-deck passenger car.
- [params.passenger_double_deck.example.yaml](params.passenger_double_deck.example.yaml) - starter parameters for a double-deck passenger car.

## Relation to v0.1.0

Version `v0.1.0` defines the baseline generator for open and covered freight wagons. Version `v0.2.0` reuses its stable principles:

- deterministic coordinate lines;
- stable node and member identifiers;
- combined `CSV` export for `wagon_fem`;
- semantic member tags for postprocessing;
- graph validation before solver execution;
- named support schemes.

The new version adds passenger-specific coordinates, side-window and door openings, underframe transition zones, roof-bow geometry, optional interdeck beams, stairwell zones, and service-equipment load zones.

## Target Implementation Shape

The target package extension is:

```text
src/wagon_fem/
  parametric/
    passenger_common.py
    passenger_single_deck.py
    passenger_double_deck.py
```

The initial public functions should be:

```python
build_passenger_single_deck(params)
build_passenger_double_deck(params)
```

Both functions should return the existing `GeneratedFrame` object and export through the existing combined `CSV` contract.

## Example Commands

```text
python -m wagon_fem.parametric docs/parametric_generator_v0_2_0/params.passenger_single_deck.example.yaml --output tmp/passenger_single_deck.csv --validate
python -m wagon_fem.parametric docs/parametric_generator_v0_2_0/params.passenger_double_deck.example.yaml --output tmp/passenger_double_deck.csv --validate
```
