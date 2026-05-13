# Single-Deck Passenger-Car Alignment with KRV Chapter 11

This note records the check of the single-deck beam model against `/Volumes/Data/dev200/rstu/krv_2026/info/krv_11/full.md`.

## Reference Basis

The single-deck scheme is aligned with the descriptions of passenger-car bodies models 61-820, 61-4179, and 61-4170. The chapter describes the body as a thin-walled shell stiffened by posts, roof bows, transverse beams, and longitudinal members. For the beam generator, these elements become the primary coordinate lines and member groups.

## Alignment Table

| Source description in chapter 11 | Generator representation |
|---|---|
| Body consists of underframe with floor, side walls, end walls, vestibule posts, and roof. | Separate member groups: `center_sill`, `side_sill`, `cross_beam`, `side_post`, `end_post`, `roof_bow`, `roof_longitudinal`. |
| Underframe has a variable-section center sill, bolster beams, end beams, intermediate cross beams, and side frame members. | Center sill is divided into end, transition, and middle spans; bolster stations are mandatory `x` lines; end beams and cross beams are generated at mandatory stations. |
| Side wall has lower, middle window, and upper belts; window-zone sections form inter-window piers and opening boundary members. | Side-wall grid uses lower belt, window-sill belt, window-head belt, and upper belt; window boundaries create `opening_post` members. |
| Intermediate side-wall posts are attached to the sheathing and placed at inter-window regions and selected window-center regions. | Regular `side_post` members are generated at pitch stations; opening boundaries and inter-window zones become mandatory coordinates. |
| End wall has corner posts, main posts around the transition opening, horizontal reinforcements, and connection to the end beam and roof. | End-frame generation requires corner posts, `main_impact_post`, door boundary members, lower end belt, upper end belt, and roof-transition members. |
| Roof is a thin-walled supported cylindrical shell with longitudinal side bindings, transverse roof bows, and roof longitudinal reinforcements. | The single-deck cross section uses a segmented cylindrical roof bow, roof side rails, top longitudinal line, and optional roof longitudinal stiffeners. |
| Global finite-element grid should coincide with the main reinforcing members of the body. | Generator coordinate lines are built from bolsters, cross beams, posts, window boundaries, door boundaries, roof bows, and user-defined stations. |
| Vertical load is introduced through nodes along the side-wall belt system in simplified schemes. | The first load-placement rule should support nodal or distributed vertical loads on side belts, floor beams, and center sill members. |

## Correction Note

The side projection of the single-deck beam model shows longitudinal side-wall members only. The rounded or segmented roof-bow contour belongs to the transverse `y-z` section and should be generated at roof-bow stations along `x`.

Vertical members adjacent to windows are split into boundary segments above and below the opening. Full-height posts are retained at inter-window piers and in end/service zones.

## Required Single-Deck Defaults

The default single-deck passenger-car example should include:

- body length near `24537 mm` or `25500 mm`, depending on selected prototype;
- bogie base `17000 mm`;
- external body width near `3104-3105 mm`;
- one main side-window row;
- two end vestibule or service zones;
- variable center sill metadata;
- mandatory bolster beam stations;
- side wall with lower, window, and upper belts;
- segmented cylindrical roof bow with roof side rails and top longitudinal line.

## Consequences for Implementation

The single-deck generator should keep a dedicated passenger-car topology. Freight-car roof and side-wall defaults should remain separate from the passenger-car defaults.

The side-wall opening rules should preserve boundary posts and belt members around windows. Equivalent panel ties may be omitted inside window openings and retained in solid panels.

The underframe generator should allow a center-sill zone map so later section calibration can assign different placeholder or measured section properties to end, transition, and middle regions.
