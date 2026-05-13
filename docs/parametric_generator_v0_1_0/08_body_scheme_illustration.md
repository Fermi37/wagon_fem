# Body Scheme Illustration

This document gives a visual reference for the proposed first-stage beam scheme. The drawings are conceptual and define topology, member groups, and coordinate logic for implementation.

![Parametric beam scheme of a wagon body](assets/body_scheme_v0_1_0.svg)

![3D view of the parametric wagon body beam scheme](assets/body_scheme_3d_v0_1_0.svg)

The first figure shows line types and two-dimensional projections. The second figure gives an isometric three-dimensional view of the same beam topology with a low trapezoidal roof profile.

The figures keep structural labels outside the plotted geometry. The line-type legend defines the visual classes, while the tables below map those classes to `member_tag` and `section_tag` values for implementation.

## Coordinate Convention

```text
          y
          ^
          |
          |
          o------> x
         /
        z
```

- `x`: longitudinal wagon axis.
- `y`: vertical axis.
- `z`: transverse wagon axis.
- `L`: body length.
- `B`: body width.
- `H`: side-wall height.

## Plan View: Frame Topology

```mermaid
flowchart LR
    subgraph frame["Plan view at floor level: x-z plane"]
        direction LR

        A1["End beam<br/>x = 0"] --- C1["Center sill<br/>z = 0"]
        C1 --- B1["Bolster beam<br/>x = x_bolster_1"]
        B1 --- X1["Intermediate cross beams<br/>x = x_cross"]
        X1 --- B2["Bolster beam<br/>x = x_bolster_2"]
        B2 --- C2["Center sill<br/>z = 0"]
        C2 --- A2["End beam<br/>x = L"]

        L1["Left side longitudinal<br/>z = -B/2"] --- LB1["Left bolster joint"]
        LB1 --- LX1["Left cross-beam joints"]
        LX1 --- LB2["Left bolster joint"]
        LB2 --- L2["Left side longitudinal<br/>z = -B/2"]

        R1["Right side longitudinal<br/>z = +B/2"] --- RB1["Right bolster joint"]
        RB1 --- RX1["Right cross-beam joints"]
        RX1 --- RB2["Right bolster joint"]
        RB2 --- R2["Right side longitudinal<br/>z = +B/2"]

        A1 --- L1
        A1 --- R1
        B1 --- LB1
        B1 --- RB1
        X1 --- LX1
        X1 --- RX1
        B2 --- LB2
        B2 --- RB2
        A2 --- L2
        A2 --- R2

        C1 -. "console diagonal ties" .- LB1
        C1 -. "console diagonal ties" .- RB1
        C2 -. "console diagonal ties" .- LB2
        C2 -. "console diagonal ties" .- RB2
    end
```

### Frame Explanation

The frame grid is generated from `end_positions`, `bolster_positions`, and `x_cross`.

The center sill is the main longitudinal load path. The side longitudinal beams support the lower side-wall belt and participate in transverse load transfer. Bolster beams and end beams create the primary transverse frame lines. Intermediate cross beams define floor support and side-wall connection points. Console diagonal ties transfer part of longitudinal force from the center sill to the side frame.

Recommended member tags:

| Drawing item | `member_tag` | `section_tag` |
|---|---|---|
| Center sill | `center_sill` | `center_sill_heavy` |
| Bolster beam | `bolster_beam` | `bolster_beam_heavy` |
| End beam | `end_beam` | `end_beam_medium` |
| Side longitudinal | `side_longitudinal` | `side_longitudinal_medium` |
| Intermediate cross beam | `cross_beam` | `cross_beam_medium` |
| Console diagonal tie | `diagonal_tie` | `diagonal_tie_equiv` |

## Side View: Open-Wagon Wall Topology

```mermaid
flowchart LR
    subgraph sidewall["Side wall: x-y plane at z = +/-B/2"]
        direction LR

        P0["Corner post<br/>x = 0"] --- P1["Post<br/>x_posts[1]"]
        P1 --- P2["Post<br/>x_posts[2]"]
        P2 --- P3["Post<br/>x_posts[3]"]
        P3 --- P4["Corner post<br/>x = L"]

        L0["Lower belt<br/>y = floor_y"] --- L1["Lower belt node"]
        L1 --- L2["Lower belt node"]
        L2 --- L3["Lower belt node"]
        L3 --- L4["Lower belt node"]

        M0["Intermediate belt<br/>y = H/2"] --- M1["Intermediate belt node"]
        M1 --- M2["Intermediate belt node"]
        M2 --- M3["Intermediate belt node"]
        M3 --- M4["Intermediate belt node"]

        U0["Upper belt<br/>y = H"] --- U1["Upper belt node"]
        U1 --- U2["Upper belt node"]
        U2 --- U3["Upper belt node"]
        U3 --- U4["Upper belt node"]

        L0 --- M0
        M0 --- U0
        L1 --- M1
        M1 --- U1
        L2 --- M2
        M2 --- U2
        L3 --- M3
        M3 --- U3
        L4 --- M4
        M4 --- U4

        L0 -. "panel diagonal" .- M1
        M0 -. "panel diagonal" .- U1
        L1 -. "panel diagonal" .- M2
        M1 -. "panel diagonal" .- U2
        L2 -. "panel diagonal" .- M3
        M2 -. "panel diagonal" .- U3
        L3 -. "panel diagonal" .- M4
        M3 -. "panel diagonal" .- U4
    end
```

### Side-Wall Explanation

The side wall is generated at both transverse positions, `z = -B/2` and `z = +B/2`.

The lower belt coincides with the side longitudinal beam in the floor frame. Vertical posts are placed at `x_posts`. The wall height is divided by `side_height_divisions`; the drawing shows one intermediate belt for compactness. Equivalent panel diagonals represent in-plane shear transfer from sheathing and provide a practical first-stage substitute for plate action.

Recommended member tags:

| Drawing item | `member_tag` | `section_tag` |
|---|---|---|
| Lower belt | `side_longitudinal` | `side_longitudinal_medium` |
| Upper belt | `upper_belt` | `upper_belt_light` |
| Intermediate belt | `horizontal_belt` | `horizontal_belt_light` |
| Side post | `side_post` | `side_post_light` |
| Panel diagonal | `diagonal_tie` | `diagonal_tie_equiv` |

## Cross Section: Open and Covered Wagon Extension

```mermaid
flowchart TB
    subgraph cross["Cross section: y-z plane at a typical x station"]
        direction TB

        R["Optional roof ridge<br/>covered wagon"] --- RL["Roof bow segment"]
        R --- RR["Roof bow segment"]

        UL["Upper side belt<br/>z = -B/2"] --- R
        R --- UR["Upper side belt<br/>z = +B/2"]

        UL --- ML["Side post division nodes"]
        UR --- MR["Side post division nodes"]

        ML --- LL["Lower side belt<br/>floor level"]
        MR --- LR["Lower side belt<br/>floor level"]

        LL --- CB["Cross beam"]
        CB --- LR

        CB --- CS["Center sill<br/>z = 0"]
    end
```

### Cross-Section Explanation

The open-wagon model uses the lower and upper side-wall belts, vertical posts, and transverse frame beams. The covered-wagon model adds roof side lines, roof bows, and a ridge or top longitudinal line. Roof bows may be represented by two to four straight segments.

Recommended additional member tags for the covered wagon:

| Drawing item | `member_tag` | `section_tag` |
|---|---|---|
| Roof bow | `roof_bow` | `roof_bow_light` |
| Roof longitudinal | `roof_longitudinal` | `roof_longitudinal_light` |
| Door post | `side_post` | `side_post_light` |
| Door lintel | `upper_belt` | `upper_belt_light` |

## Implementation Notes

The generator should create the same topology through coordinate grids instead of hard-coded node identifiers. Each diagram node corresponds to one or more generated `node_id` values, depending on the selected pitch and height division count.

The first-stage export should keep `member_tag` and `section_tag` columns for review and postprocessing. These columns allow moment and force tables to be grouped by structural role after analysis.
