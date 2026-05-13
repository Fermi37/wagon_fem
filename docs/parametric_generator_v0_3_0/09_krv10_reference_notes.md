# KRV 10 Reference Notes

## Source Context

The local source folder `/Volumes/Data/dev200/rstu/krv_2026/info/krv_10` contains Chapter 10 material on tank-car construction and calculation. The notes below are used only to guide the first parametric beam-system description.

## Modeling-Relevant Statements

The tank car body should be treated as a coupled tank-and-frame system. The tank is a stiff load-carrying component, and its supports strongly affect how vertical load reaches the frame and trucks.

For a typical four-axle general-purpose tank car, the source material lists representative dimensions:

- payload near `66 t`;
- tare near `26...28 t`;
- length over coupling axes near `12.02 m`;
- truck base near `7.8 m`;
- internal tank diameter near `3.0...3.2 m`;
- tank length near `10.8...11.2 m`.

The tank is attached to the frame in the middle region and supported near the ends. End supports may permit longitudinal movement caused by thermal deformation. The middle attachment can restrain relative longitudinal displacement between tank and frame.

The frame carries longitudinal compression and tension mainly through the center sill. Bolster beams receive significant vertical forces from tank supports and can experience high stresses in local lifting or support cases.

## Consequences for v0.3.0

The generator should expose:

- tank diameter, length, and center height;
- tank ring spacing and angular division count;
- bolster positions;
- center-sill and cross-beam layout;
- middle attachment position and longitudinal-lock flag;
- end saddle positions and slip metadata;
- vertical payload placement on the tank lattice;
- longitudinal end-load placement on the center sill;
- postprocessing by member tag and station.

## Default Parameter Anchors

The default YAML example uses:

- `length_over_coupler_axes = 12020 mm`;
- `truck_base = 7800 mm`;
- `tank.length = 10818 mm`;
- `tank.diameter = 3000 mm`;
- `payload.total_force = -647000 N` as an approximate first-stage value for `66 t`;
- `tank_self_weight.total_force = -78000 N` as a placeholder for tank and local equipment weight.

These defaults are engineering anchors for generator development. A calculation report should replace them with model-specific passport, drawing, or measurement data.

