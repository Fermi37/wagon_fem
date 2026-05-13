# Scope and Assumptions

## Objective

The objective is to define a parametric description of a tank car as a connected system of beams suitable for first-stage finite-element calculations of member forces and moments.

The model should support rapid variation of body and tank parameters: length, base, tank diameter, tank length, support positions, frame width, saddle geometry, longitudinal member count, ring spacing, and load placement.

## Result Boundary

The primary outputs are:

- axial force in each generated member;
- shear forces in local member directions;
- bending moments about local member axes;
- torsional moment where the finite-element backend provides it;
- support reactions at bolster and tank-support nodes;
- force-flow summaries by member tag.

The model uses simplified section properties during the first stage. These values are required for stiffness assembly and solver conditioning. They are treated as analysis placeholders until calibrated section data are introduced.

## Modeling Level

The tank car is represented by four coupled subsystems:

- underframe beams: center sill, side beams where present, end beams, bolsters, cross beams, console-region members;
- tank equivalent beam lattice: longitudinal beams on selected angular generators, ring beams at station lines, end-dish equivalent rings;
- tank-to-frame interfaces: middle lugs, saddle supports, wooden-pad or elastic-pad idealizations, straps, and transverse tie members;
- equipment attachment members: manhole zone, drain zone, ladder brackets, and local fitting beams when requested by the parameter file.

The tank shell is represented through an equivalent beam lattice. The lattice captures global force transmission between the tank and frame. Local shell stresses, weld stresses, buckling, ovalization, and liquid-structure interaction require later specialized models.

## Coordinate System

The coordinate system follows the existing `wagon_fem` convention:

- `x` is the longitudinal coordinate in millimeters;
- `y` is the vertical coordinate in millimeters;
- `z` is the transverse coordinate in millimeters.

The reference origin is placed at the left end of the structural frame. The centerline of the wagon is `z = 0`.

## Baseline Tank-Car Assumptions

The first baseline represents a four-axle general-purpose tank car:

- length over coupling axes near `12020 mm`;
- truck base near `7800 mm`;
- internal tank diameter near `3000 mm`;
- tank length near `10800...11200 mm`;
- two bolster lines;
- central and end tank supports;
- longitudinal forces primarily routed through the center sill;
- vertical tank load routed through tank supports, bolsters, and the center-sill region.

The values above are default engineering anchors. Each production case should record the source of dimensions in metadata.

## Extension Policy

The tank-car topology should share the same generated-frame object, CSV export, validation route, and solver route as earlier generator versions. New tank-specific fields should be added as optional schema groups so existing open-wagon, covered-wagon, and passenger-car workflows remain loadable.

