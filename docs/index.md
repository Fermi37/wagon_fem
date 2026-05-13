# Documentation

This directory contains user-oriented documentation for the wagon-fem package.
The Gradio app itself exposes one curated `Guide` tab for the operational
workflow, while this directory keeps the broader repository documentation.

Available pages:

- `usage.md` — Quick start, CLI and UI examples, CSV format
- `api.md` — Short API reference and examples
- `parametric_generator_v0_1_0/` — Versioned implementation documents for the parametric wagon beam generator
- `parametric_generator_v0_1_0/params.open_wagon.example.yaml` — Default open-wagon generator parameters
- `parametric_generator_v0_1_0/params.covered_wagon.example.yaml` — Default covered-wagon generator parameters
- `parametric_generator_v0_3_0/` - Tank-car beam-system generator documents and unified wagon-type roadmap
- `parametric_generator_v0_3_0/params.tank_wagon.example.yaml` - Default tank-wagon generator parameters

To preview locally you can use MkDocs or any static site generator that reads Markdown:

```text
mkdocs serve
```
