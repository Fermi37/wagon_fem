# Generation Rules

## Shared Rules

See [08_body_scheme_illustration.md](08_body_scheme_illustration.md) for a conceptual body-frame illustration that maps the rules below to member groups and section tags.

The generator should create deterministic coordinate lines:

- end positions: `0`, `L`;
- bolster positions: all values from `x_bolsters`;
- cross-beam positions: generated from `cross_beam_pitch`;
- post positions: generated from `side_post_pitch`;
- opening boundaries: door or hatch start and end coordinates;
- user-defined extra coordinates.

Coordinates are merged by tolerance. The recommended tolerance is `1e-6 mm`.

Each structural line is created as a sequence of beam members between adjacent coordinate points.

## Open Wagon Topology

### Frame

Create:

- center sill along `x` at `y = floor_y`, `z = 0`;
- two side longitudinal beams along `x` at `z = -B/2` and `z = B/2`;
- end beams at `x = 0` and `x = L`;
- bolster beams at each `x_bolster`;
- intermediate cross beams at `x_cross`;
- optional floor longitudinal beams between the center sill and side beams;
- diagonal braces in console regions from the center sill to side beams.

### Side Walls

For each side wall at `z = +/-B/2`, create:

- lower belt tied to the side longitudinal beam;
- upper belt at `y = floor_y + side_height`;
- vertical posts at `x_posts`;
- intermediate horizontal belts using `side_height_divisions`;
- equivalent diagonal ties for panel shear where `include_diagonals = true`.

### End Walls

At `x = 0` and `x = L`, create:

- corner posts;
- intermediate posts;
- upper end belt;
- intermediate horizontal belts;
- ties to the frame end beam.

### Side-Height Division

For open wagons, `side_height_divisions` is a primary load-distribution parameter. Recommended initial values:

- `3` for coarse exploratory calculations;
- `4` for routine first-stage force calculations;
- `6` for closer representation of lateral bulk load distribution.

## Covered Wagon Topology

The covered-wagon generator extends the open-wagon frame with door openings and a roof.

### Frame

Create:

- center sill;
- side longitudinal beams;
- bolster beams;
- end beams;
- door-area cross beams;
- intermediate cross beams;
- floor longitudinal beams.

### Side Walls

Create:

- lower and upper belts;
- corner posts;
- bolster-area posts;
- door posts;
- intermediate posts;
- top lintel above each side door;
- lower threshold line near the door opening;
- side panel members outside the opening.

Elements whose segment midpoint lies inside a door opening should be omitted for panel belts and diagonal ties. Door boundary posts and lintels should remain.

### End Walls

Create:

- corner posts;
- intermediate posts;
- upper end belt;
- intermediate belts;
- connections to the end beam and roof frame.

### Roof

Create:

- roof side longitudinal lines;
- roof bows at `x_roof_bows`;
- ridge or top longitudinal line;
- roof longitudinal stiffeners;
- segmented bow geometry using two to four straight beam segments.

For the first implementation, a three-point bow is sufficient:

```text
left roof side line -> ridge line -> right roof side line
```

## Load Placement Rules

Vertical loads may be applied as distributed loads on floor beams or as nodal loads at floor grid nodes.

Longitudinal loads may be applied near the center sill end zones and bolster zones.

Lateral bulk pressure may be converted to nodal forces at side-wall posts and belts using tributary panel areas.

Support reactions may be modeled at bolster nodes or at idealized body support points near the center plate positions.
