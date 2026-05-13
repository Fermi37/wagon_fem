# Scope and Assumptions

## Purpose

The first implementation stage builds a parametric spatial beam model of wagon bodies and exports it to the existing `wagon_fem` CSV format. The resulting model is intended for calculating:

- axial forces in members;
- shear forces in members;
- bending moments in members;
- support reactions;
- displacement trends of the body frame.

## Modeling Level

The first-stage model is a beam-only finite-element approximation. The main load-bearing members are represented by three-dimensional beam elements:

- center sill;
- side longitudinal beams;
- end beams;
- bolster beams;
- intermediate cross beams;
- floor longitudinal beams;
- side-wall posts;
- side-wall belts;
- end-wall posts;
- roof bows for covered wagons;
- conditional diagonal ties for panel shear transfer.

The shell action of corrugated sheets is represented through equivalent diagonal or axial ties. This approximation is suitable for early force-flow analysis and member-force ranking.

## Coordinate System

- `x`: longitudinal wagon axis, mm.
- `y`: vertical axis, mm.
- `z`: transverse wagon axis, mm.

Positive `x` runs from one end beam to the opposite end beam. Positive `y` points upward from the floor plane. Positive `z` points to one side wall.

## Primary Parameters

- `L`: body length, mm.
- `B`: body width, mm.
- `H`: side-wall height, mm.
- `x_bolsters`: longitudinal coordinates of bolster beams, mm.
- `x_posts`: longitudinal coordinates of side-wall posts, mm.
- `x_cross`: longitudinal coordinates of cross beams, mm.
- `n_side_height`: number of side-wall divisions by height.

## Initial Engineering Assumptions

Steel is modeled with `E = 210000 N/mm^2`.

Member properties are assigned by structural group. This gives a physically meaningful stiffness hierarchy while keeping geometry generation independent from final section selection.

Loads are introduced through the existing `wagon_fem` node and member load fields:

- `fx`, `fy`, `fz` for nodal forces;
- `mx`, `my`, `mz` for nodal moments;
- `w`, `w1`, `w2`, `dist_dir` for distributed member loads.

Supports are introduced through `support_dx`, `support_dy`, `support_dz`, `support_rx`, `support_ry`, and `support_rz`.

## Expected Accuracy Level

The model should provide reliable qualitative force paths and useful first numerical estimates of member forces and bending moments. Quantitative stress conclusions require calibrated section properties and later verification against a refined plate-beam or plate model.
