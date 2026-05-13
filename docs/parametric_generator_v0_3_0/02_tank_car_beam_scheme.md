# Tank-Car Beam Scheme

## Structural Idealization

A tank car is modeled as a spatial frame with a cylindrical tank coupled to an underframe. The cylinder is represented by a set of longitudinal beam lines and ring beam lines. The underframe is represented by the center sill, bolsters, end beams, cross beams, and optional side beams.

The most important engineering feature is the load transfer between the stiff tank and the underframe. The generator should therefore expose tank supports and attachment elements explicitly, with stable member tags and coordinates.

## Member Groups

### Underframe

The underframe contains:

- `center_sill`: main longitudinal beam along `z = 0`;
- `bolster_beam`: transverse beams at truck-center or center-plate lines;
- `end_beam`: transverse beams at the frame ends;
- `cross_beam`: intermediate transverse beams;
- `console_side_beam`: side members in console zones when specified;
- `draft_gear_stub`: short longitudinal members near coupler-force application points;
- `diagonal_tie`: equivalent bracing in selected frame panels.

### Tank Equivalent Lattice

The tank lattice contains:

- `tank_longitudinal`: longitudinal beams on angular generators of the cylindrical shell;
- `tank_ring`: polygonal ring beams around the tank at generated stations;
- `tank_end_ring`: equivalent ring near each tank end;
- `tank_end_dish_spoke`: optional radial members approximating end-dish load transfer;
- `tank_top_stringer`: optional upper longitudinal line near manhole or walkway zones;
- `tank_bottom_stringer`: optional lower longitudinal line near drain and support zones.

### Tank-to-Frame Interface

The interface contains:

- `middle_tank_lug`: central positive attachment that restrains longitudinal tank slip where selected;
- `saddle_support`: vertical and transverse load-transfer members at tank support stations;
- `end_saddle_support`: end support members with optional longitudinal slip release in metadata;
- `strap_tie`: tension-only or equivalent beam ties from the tank to frame-side nodes;
- `support_pad_stub`: short vertical members between tank surface nodes and frame support nodes.

### Attachments and Equipment

The attachment subsystem contains optional local members:

- `manhole_ring`;
- `drain_support`;
- `ladder_bracket`;
- `walkway_support`;
- `valve_mount`.

These members should be generated only when the parameter file requests the corresponding feature.

## Tank Lattice Geometry

For a tank radius `R_tank`, a tank center height `y_tank_center`, and a transverse centerline `z = 0`, each angular generator has coordinates:

```text
y = y_tank_center + R_tank * sin(theta)
z = R_tank * cos(theta)
```

The ring polygon is formed by connecting adjacent angular generator points at the same longitudinal station. The longitudinal shell beams connect equal angular points at adjacent stations.

Recommended first-stage angular sets:

- coarse: `theta = [0, 60, 120, 180, 240, 300] deg`;
- routine: `theta = [0, 45, 90, 135, 180, 225, 270, 315] deg`;
- detailed beam lattice: `12` or `16` angular divisions.

## Longitudinal Stations

The generator should merge station coordinates from:

- frame ends;
- tank ends;
- bolster positions;
- tank support stations;
- middle lug station;
- manhole and drain stations;
- regular `tank_ring_pitch`;
- user-defined extra stations.

Station merging should follow the same tolerance policy as `v0.1.0`.

## Load-Path Interpretation

Vertical load from tank self-weight and payload is assigned to tank lattice members or tank nodes. The load passes through the ring-longitudinal lattice into saddle supports and then into bolsters, center sill, and frame members.

Longitudinal compression and tension from train action should be applied to the draft gear or center-sill end nodes. The model should allow the tank to participate through middle lugs and straps when these attachments are enabled.

Lateral load should be applied to tank shell nodes by angular sector or to frame nodes through equivalent nodal loads. This allows comparison of lateral stability and support reaction patterns.

