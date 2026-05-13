# Parametric Wagon Generator v0.3.0

This folder contains the version `0.3.0` documentation for a parametric generator of wagon beam schemes with a tank-car first case.

`YAML` means a human-readable structured data format used for generator input files.

`CSV` means comma-separated values, the exchange table format already consumed by `wagon_fem`.

`FEM` means finite element method. In this version, the finite-element model is a beam network used to obtain member forces, bending moments, support reactions, and qualitative load-path redistribution under parameter variation.

`node` means a geometric joint of the generated beam system.

`member` means a beam finite element between two nodes.

`section_tag` means a semantic section label used by the generator. At this stage, section properties are computational placeholders that keep the solver stable and allow load-path comparisons.

## Document Set

- [01_scope_and_assumptions.md](01_scope_and_assumptions.md) - modeling objective, assumptions, and result boundaries.
- [02_tank_car_beam_scheme.md](02_tank_car_beam_scheme.md) - tank-car load-bearing scheme as connected beams.
- [03_parameter_contract.md](03_parameter_contract.md) - stable input structure for parametric generation.
- [04_generation_rules.md](04_generation_rules.md) - deterministic topology rules and member tags.
- [05_load_and_support_model.md](05_load_and_support_model.md) - first-stage load cases and support idealizations.
- [06_validation_plan.md](06_validation_plan.md) - geometry, graph, load, support, and solver checks.
- [07_implementation_tasks.md](07_implementation_tasks.md) - executable implementation roadmap.
- [08_unified_wagon_type_roadmap.md](08_unified_wagon_type_roadmap.md) - path toward freight and passenger generator families.
- [09_krv10_reference_notes.md](09_krv10_reference_notes.md) - local notes extracted from `krv_10` for tank-car modeling.
- [10_calculation_scheme.md](10_calculation_scheme.md) - finite-element calculation scheme with loads, supports, and result groups.
- [11_illustrated_scheme.md](11_illustrated_scheme.md) - report-ready illustrated calculation scheme with Russian labels.
- [params.tank_wagon.example.yaml](params.tank_wagon.example.yaml) - starter parameter file.
- [assets/tank_car_beam_scheme_v0_3_0.svg](assets/tank_car_beam_scheme_v0_3_0.svg) - conceptual topology illustration.
- [assets/tank_car_calculation_scheme_v0_3_0.svg](assets/tank_car_calculation_scheme_v0_3_0.svg) - calculation scheme illustration.
- [assets/tank_car_illustrated_calculation_scheme_v0_3_0.svg](assets/tank_car_illustrated_calculation_scheme_v0_3_0.svg) - report-ready illustrated scheme.

## Intended Use

The generator should create a deterministic beam model from a parameter file:

```bash
python -m wagon_fem.parametric docs/parametric_generator_v0_3_0/params.tank_wagon.example.yaml --output tmp/tank_wagon.csv --validate
```

The exported CSV should be compatible with the existing solver route:

```bash
python -m wagon_fem tmp/tank_wagon.csv
```

## Version Position

Version `0.1.0` defines the initial beam generator for open and covered freight wagons.

Version `0.2.0` defines passenger-car parameter extensions.

Version `0.3.0` defines the tank-car beam-system model and the shared generator contract needed to support freight and passenger wagon families in a single parametric package.
