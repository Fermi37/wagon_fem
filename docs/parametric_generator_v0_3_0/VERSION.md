# Version

`0.3.0-parametric-generator-tank-car-beam-model`

## Scope

Version `0.3.0` defines a parametric beam-system description for a tank car body and frame. It extends the `v0.1.0` beam-only generator concept with tank-specific topology, tank-to-frame supports, and a unified type interface intended to cover freight and passenger rolling stock.

## Status

Documentation baseline for implementation.

## Primary Additions

- tank car as a connected system of frame beams, tank-shell equivalent beams, ring beams, saddle supports, straps, and local attachment beams;
- parameter groups for tank geometry, frame geometry, support stations, load cases, and generation density;
- first-stage finite-element model focused on internal forces, bending moments, shear forces, axial forces, reactions, and load-path comparison;
- common generator vocabulary for later support of freight and passenger car families.

