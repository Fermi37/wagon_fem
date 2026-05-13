# Passenger Body Beam Scheme

## Engineering Representation

The passenger-car body is modeled as a closed spatial beam frame assembled from the underframe, side walls, end walls, roof, and optional interdeck structure. The generator creates nodes at all mandatory longitudinal, vertical, and transverse coordinate lines, then connects adjacent nodes with beam members assigned to structural groups.

The body-frame model should preserve the following force paths:

- vertical loads from passengers, interior equipment, water systems, climate equipment, and roof equipment transfer into floor beams, side walls, center sill, and bolster beams;
- longitudinal forces transfer through the coupler zone, center sill, end beams, side sills, and diagonal underframe ties;
- lateral loads transfer through side-wall posts, side belts, roof bows, and floor cross beams;
- torsional loading is resisted by the spatial contour formed by underframe beams, side walls, end walls, and roof members.

## Underframe

The underframe contains:

- a center sill on the longitudinal centerline;
- side sills at the side-wall planes;
- end beams at both body ends;
- bolster beams at bogie support locations;
- intermediate cross beams between bolster zones and in the central span;
- floor longitudinal beams between the center sill and side sills;
- optional diagonal underframe ties in end-transition zones.

The center sill may have zone tags along its length: `end_heavy`, `transition`, and `middle`. These tags allow later section calibration while keeping the first version topology driven.

## Side Walls

Each side wall contains:

- lower belt tied to the side sill;
- under-window belt;
- window belt or opening boundary line;
- above-window belt;
- upper side-wall belt;
- vertical posts at regular pitch and at opening boundaries;
- strengthened posts in door, vestibule, service-room, and stairwell zones;
- optional diagonal ties in solid panels.

Window openings are represented by omitted panel-equivalent belts and diagonals inside the window region. Boundary posts and belts around the window are retained.

## End Walls

Each end wall contains:

- corner posts;
- main impact posts around the end door or transition opening;
- lower and upper end belts;
- intermediate horizontal belts;
- door lintel and threshold members;
- roof-transition members;
- ties into the end beam and roof frame.

End-wall post tags should distinguish `corner_post`, `main_impact_post`, and `door_boundary_post` because these members carry different safety functions in later detailed models.

## Roof

The roof contains:

- roof side rails connected to the upper side-wall belts;
- roof bows at frame stations;
- ridge line or top longitudinal line;
- optional roof longitudinal stiffeners;
- opening frames for climate equipment, hatches, and service apertures.

Roof bows may be approximated by a three-point broken line in the first implementation:

```text
left roof side rail -> roof ridge -> right roof side rail
```

For a rounded or multi-radius roof contour, the parameter contract permits additional roof profile points.

## Single-Deck Passenger Car

The single-deck variant uses one main floor grid, one side-window belt system, and one roof system. The default grid is suitable for a locomotive-hauled passenger car with a body length near 24.5 m, a bogie-base distance near 17.0 m, and side walls divided by vestibules, service rooms, compartments, and sanitary zones.

## Double-Deck Passenger Car

The double-deck variant adds:

- a lowered first-floor zone between bogies;
- a second-floor grid;
- interdeck transverse beams;
- interdeck longitudinal beams;
- stairwell opening frames;
- strengthened frames at the boundaries of lowered-floor zones;
- roof members governed by the larger vertical envelope.

The double-deck topology should support central two-level passenger compartments and end zones with service spaces, vestibules, stairs, and equipment rooms.

## Member Tags

Recommended member tags:

| Tag | Meaning |
|---|---|
| `center_sill` | longitudinal center sill |
| `side_sill` | side longitudinal underframe member |
| `end_beam` | end transverse beam |
| `bolster_beam` | bolster transverse beam |
| `cross_beam` | intermediate floor cross beam |
| `floor_longitudinal` | secondary floor longitudinal beam |
| `side_post` | regular side-wall vertical post |
| `opening_post` | window or door boundary post |
| `side_belt_lower` | lower side-wall belt |
| `side_belt_window` | window-zone side-wall belt |
| `side_belt_upper` | upper side-wall belt |
| `end_post` | end-wall post |
| `main_impact_post` | strengthened end-wall post |
| `roof_bow` | transverse roof bow |
| `roof_longitudinal` | roof longitudinal member |
| `interdeck_cross_beam` | double-deck transverse interdeck member |
| `interdeck_longitudinal` | double-deck longitudinal interdeck member |
| `diagonal_tie` | equivalent shear-transfer tie |
| `rigid_offset` | rigid connection between eccentric axes |

