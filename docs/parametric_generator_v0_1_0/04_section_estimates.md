# Approximate Section Estimates

## Purpose

This document defines the first-stage section catalog for moment and force calculations in beam members. Values are intentionally approximate and grouped by structural role. They establish a physically reasonable stiffness hierarchy before detailed section calibration.

## Unit System

- Length: mm.
- Force: N.
- Stress and modulus: N/mm^2.
- Area: mm^2.
- Second moments of area: mm^4.
- Torsional constant: mm^4.

## Material

All first-stage steel members use:

| Property | Value |
|---|---:|
| `E` | `210000` |

## Recommended First-Stage Section Classes

| `section_tag` | Structural group | `A` | `Iy` | `Iz` | `J` |
|---|---|---:|---:|---:|---:|
| `center_sill_heavy` | center sill | 18000 | 2.20e8 | 4.50e8 | 1.50e7 |
| `bolster_beam_heavy` | bolster beam | 16000 | 1.80e8 | 3.20e8 | 1.20e7 |
| `end_beam_medium` | end beam | 12000 | 9.00e7 | 1.80e8 | 8.00e6 |
| `side_longitudinal_medium` | side longitudinal beam | 11000 | 8.00e7 | 1.60e8 | 7.00e6 |
| `cross_beam_medium` | intermediate cross beam | 9000 | 6.00e7 | 1.20e8 | 5.00e6 |
| `floor_longitudinal_light` | floor longitudinal beam | 6500 | 3.00e7 | 7.00e7 | 2.50e6 |
| `side_post_light` | side-wall post | 5000 | 2.50e7 | 5.00e7 | 1.50e6 |
| `end_post_light` | end-wall post | 5000 | 2.50e7 | 5.00e7 | 1.50e6 |
| `upper_belt_light` | upper side-wall or end-wall belt | 6000 | 3.50e7 | 7.00e7 | 2.00e6 |
| `horizontal_belt_light` | intermediate wall belt | 4500 | 2.00e7 | 4.00e7 | 1.20e6 |
| `roof_bow_light` | roof bow | 4500 | 2.00e7 | 4.50e7 | 1.00e6 |
| `roof_longitudinal_light` | roof longitudinal member | 4000 | 1.80e7 | 3.50e7 | 9.00e5 |
| `diagonal_tie_equiv` | equivalent panel diagonal | 1800 | 5.00e5 | 5.00e5 | 1.00e4 |
| `rigid_offset_stub` | rigid offset approximation | 50000 | 1.00e10 | 1.00e10 | 1.00e9 |

## Interpretation

The catalog ranks the center sill and bolster beams as the stiffest frame elements. Side longitudinal beams and cross beams receive medium stiffness. Wall posts, belts, and roof members receive lower stiffness. Equivalent diagonal ties primarily transfer axial force and provide in-plane shear representation.

## Calibration Path

1. Replace approximate values with measured section properties where drawings provide flange, web, thickness, and profile dimensions.
2. Group real sections by structural role.
3. Run a sensitivity study for `Iy`, `Iz`, and `J` in each group.
4. Compare global reactions and force paths with a reference hand calculation or a refined finite-element model.
5. Freeze a calibrated catalog as `sections_v0.2.yaml`.

## Local-Axis Check

Beam local axes in the FE backend affect which value is interpreted as the strong-axis or weak-axis bending stiffness. The implementation should include a small verification model for each major orientation:

- longitudinal member along `x`;
- transverse member along `z`;
- vertical member along `y`;
- roof bow segment with inclined geometry.

The verification should confirm that bending response follows the intended strong and weak axes.
