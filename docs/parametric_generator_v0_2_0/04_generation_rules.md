# Generation Rules

## Shared Deterministic Rules

The generator must construct ordered coordinate lines along `x`, `y`, and `z` from:

- body ends;
- bolster positions;
- cross-beam pitch;
- side-post pitch;
- roof-bow pitch;
- window and door boundaries;
- end-door boundaries;
- stairwell boundaries;
- lowered-floor transition boundaries;
- service-equipment boundaries;
- user-defined additional stations.

Coordinate values are merged by tolerance. The recommended tolerance is `1e-6 mm`.

Each structural line is generated as beam members between adjacent coordinate points. Member identifiers must be stable for identical parameter files.

## Underframe Rules

Generate the center sill along `x` at `z = 0`.

Generate side sills along `x` at `z = +/-B_body/2`, where `B_body` means body width.

Generate end beams at both end stations.

Generate bolster beams at all `bolster_positions`.

Generate intermediate cross beams at `cross_beam_pitch` stations and at mandatory opening or equipment boundaries when those boundaries need direct load transfer.

Generate floor longitudinal beams between the center sill and side sills according to `floor_longitudinal_count_each_side`.

Generate optional diagonal underframe ties in the end-transition zones and around bolster transitions.

## Side-Wall Rules

For each side wall:

- generate lower, window-level, and upper belts;
- generate posts at pitch stations and mandatory opening boundaries;
- tag posts adjacent to windows and doors as `opening_post`;
- omit equivalent panel ties whose midpoint lies inside a window or door opening;
- retain boundary members around each opening;
- generate strengthened post tags in vestibule, stairwell, sanitary, and service-equipment zones where requested.

For a repeated window group, expand the group before coordinate-line generation so every opening boundary becomes a mandatory station.

## End-Wall Rules

At each body end:

- generate corner posts;
- generate main impact posts around the end-door or transition opening;
- generate lower, intermediate, and upper belts;
- generate door lintel, threshold, and vertical boundary members;
- connect end-wall members to the end beam and roof frame.

The end-wall contour should follow the roof-side and roof-ridge levels provided by the `levels` group.

## Roof Rules

Generate roof side rails along `x` at the top of the side walls.

Generate the ridge line or roof top line along `x`.

Generate roof bows at `roof_bow_pitch` stations and mandatory opening boundaries.

Generate optional roof longitudinal stiffeners between side rails and ridge.

Frame roof equipment openings by transverse and longitudinal members and omit panel-equivalent members inside each opening.

## Single-Deck Rules

The single-deck generator creates one main floor grid, one side-window belt system, one end-wall system, and one roof system.

The default side-wall vertical levels should include:

- floor level;
- lower belt;
- window sill;
- window head;
- upper belt;
- roof-side line.

Additional height divisions can be inserted for diagonal-tie placement and load distribution.

## Double-Deck Rules

The double-deck generator creates:

- lower floor grid in the lowered central zone;
- main end-zone floor grid where applicable;
- interdeck grid at `interdeck_floor_y`;
- upper side-window belt system;
- roof system;
- stairwell boundary frames;
- strengthened transverse frames at lowered-floor transitions.

The lowered-floor zone changes the vertical coordinate of floor members only inside its longitudinal interval. Transition stations must be generated at both boundaries.

Interdeck beams should connect to side-wall posts and selected transverse frames. Stairwell openings should omit interdeck members whose midpoint lies inside the stairwell region while retaining stairwell boundary beams.

## Load Placement Rules

Vertical loads may be applied as distributed loads on floor and interdeck members or as nodal loads at grid nodes.

Roof equipment loads may be distributed to roof longitudinal members and roof bows inside the equipment zone.

Water, sanitary, and service-equipment loads may be assigned to underframe members by zone.

Longitudinal coupler loads should be applied near the end-center sill nodes or through end-zone load-transfer members.

Lateral loads may be converted to nodal forces at side-wall posts and belts using tributary panel areas.

## Support Rules

Support schemes should be named:

- `two_bolster_reference`;
- `four_point_bolster_reference`;
- `solver_stability_clamped_reference`;
- `body_on_secondary_suspension_reference`.

The default engineering scheme for passenger bodies is `four_point_bolster_reference`, with vertical restraints at paired support points near both bolster lines and reference restraints to remove rigid-body motion.

