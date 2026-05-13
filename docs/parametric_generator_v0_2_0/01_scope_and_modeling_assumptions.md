# Scope and Modeling Assumptions

## Purpose

Version `0.2.0` defines a parameterized beam representation of a passenger-car body. The model describes the load-bearing frame as connected spatial beams and prepares input data for subsequent `wagon_fem` calculations of:

- axial forces;
- shear forces;
- bending moments;
- support reactions;
- global displacement trends;
- force redistribution between underframe, side walls, end walls, roof, and interdeck members.

## Modeling Level

The first passenger-car model is a beam-only finite-element approximation. The body is represented by the following structural groups:

- center sill;
- side sills and side longitudinal underframe members;
- end beams;
- bolster beams;
- intermediate cross beams;
- floor longitudinal members;
- lower, intermediate, window, and upper side-wall belts;
- side-wall posts, including window and door boundary posts;
- end-wall corner posts and main impact posts;
- end-wall horizontal belts and door-frame members;
- roof side rails, ridge line, roof bows, and roof longitudinal stiffeners;
- optional diagonal ties for equivalent panel shear transfer;
- optional rigid offsets for connecting beams whose real centroidal axes are eccentric;
- optional interdeck longitudinal and transverse beams for double-deck cars.

The model follows the engineering idea stated in the local passenger-car material `krv_11/full.md`: the finite-element grid should be aligned with the principal reinforcing members of the body, including underframe beams, side-wall posts, roof bows, belts, and end-wall reinforcements.

## Coordinate System

`x` is the longitudinal coordinate in millimeters. Positive `x` runs from the brake end or selected origin end toward the opposite end.

`y` is the vertical coordinate in millimeters. Positive `y` points upward.

`z` is the transverse coordinate in millimeters. Positive `z` points toward the right side wall when looking in the positive `x` direction.

## Section Properties

Section properties are placeholders in this version. `E` means Young's modulus, the elastic modulus of the material. `A` means cross-sectional area. `Iy` and `Iz` mean second moments of area about local axes. `J` means torsional constant.

The generator must assign valid positive placeholder values for solver stability. The engineering interpretation of moments and forces at this stage should use structural tags and topology; stress assessment is deferred to calibrated section models.

## Primary Assumptions

The passenger-car body is treated as a welded all-metal body whose global load path is carried by the underframe, side walls, end walls, roof, and, for double-deck cars, the interdeck structure.

Corrugated or sheet panels are represented by equivalent horizontal belts and optional diagonal ties. These ties are computational devices for force-flow approximation.

Window and door openings control which panel-equivalent members are generated. Boundary posts, lintels, thresholds, and adjacent belts remain mandatory at opening edges.

Bolster zones define the principal support and load-transfer regions. End zones define the regions for longitudinal forces from coupler and buffer equipment.

For double-deck cars, the interdeck structure is modeled as a second floor grid coupled to side walls and selected transverse frames. The lowered first-floor central zone is represented through separate `y` levels and transition zones.

## Expected Accuracy

The model should provide a reproducible first-stage estimate of internal forces and moments in beams. It is suitable for comparing topology variants, load-path assumptions, support schemes, and parameter changes. Stress assessment requires calibrated section properties and a refined plate-beam or shell-beam model.
