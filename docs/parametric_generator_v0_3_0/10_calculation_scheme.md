# Calculation Scheme

## Purpose

This document defines the first-stage calculation scheme for the tank-car beam model. The scheme is intended for finite-element extraction of internal forces, bending moments, shear forces, torsional moments, and support reactions in the generated beam network.

## Structural System

The calculation model contains three coupled load-bearing subsystems:

- underframe subsystem: center sill, bolsters, end beams, cross beams, side beams, and local draft-gear members;
- tank equivalent subsystem: longitudinal tank beams, ring beams, end rings, and optional end-dish spokes;
- connection subsystem: saddle support members, middle lugs, support-pad stubs, and strap ties.

The tank is represented as an equivalent spatial beam lattice. The underframe is represented as a spatial beam frame. Tank-to-frame load transfer is represented by explicit connection members, so member-force postprocessing can separate tank, frame, and interface effects.

## Coordinate System

The calculation scheme uses the global coordinate system of `wagon_fem`:

- `x`: longitudinal wagon axis, mm;
- `y`: vertical axis, mm;
- `z`: transverse wagon axis, mm.

Positive vertical coordinates are directed upward from the underframe reference plane.

## Calculation Nodes

Mandatory node groups:

- `N_frame_end_left`, `N_frame_end_right`: center-sill end nodes for longitudinal train-force application;
- `N_bolster_left_*`, `N_bolster_right_*`: bolster support nodes;
- `N_tank_ring_i_j`: tank ring nodes at station `i` and angular index `j`;
- `N_saddle_i_j`: interface nodes that connect tank lower-sector nodes to frame nodes;
- `N_lug_mid`: middle tank-lug node near the lower tank generator;
- `N_drain`, `N_manhole`: optional local feature nodes when requested.

Node names above are semantic names. The implementation should export numeric `node_id` values while preserving semantic tags in metadata or auxiliary audit tables.

## Boundary Conditions

### Main Support Scheme

The default calculation scheme is `two_bolster_with_reference_lock`.

It contains:

- four vertical support points at the bolster region;
- transverse restraints at selected bolster-side nodes;
- one longitudinal reference restraint at the primary bolster station;
- additional rotational stabilization only when required by solver conditioning.

Recommended support layout:

| Point | `x` | `y` | `z` | `dx` | `dy` | `dz` |
|---|---:|---:|---:|---:|---:|---:|
| `S1` | `x_b1` | `0` | `-z_s` | true | true | true |
| `S2` | `x_b1` | `0` | `+z_s` | false | true | false |
| `S3` | `x_b2` | `0` | `-z_s` | false | true | true |
| `S4` | `x_b2` | `0` | `+z_s` | false | true | false |

Here `x_b1` and `x_b2` are bolster positions, and `z_s` is the transverse support offset.

### Tank Support Idealization

End saddle supports transfer vertical and transverse forces from the lower tank sector to the frame. Their longitudinal slip assumption is recorded in metadata through `allow_longitudinal_slip`.

The middle lug transfers vertical, transverse, and selected longitudinal interaction forces between the tank and center sill. In the baseline scheme, the middle lug is the primary longitudinal tank-to-frame lock.

## Load Cases

### LC1: Tare Vertical

Purpose: force distribution under structural self-weight.

Load placement:

- tank self-weight on lower tank longitudinal beams or lower-sector ring nodes;
- frame self-weight on center sill, cross beams, and bolsters when frame mass data are available.

### LC2: Gross Vertical

Purpose: main strength calculation for vertical bending and support reactions.

Load placement:

- tank self-weight;
- payload weight distributed to tank lattice according to selected fill model;
- optional equipment loads at manhole, drain, walkway, valve, and ladder nodes.

### LC3: Longitudinal Compression

Purpose: estimate axial force path through the center sill and tank attachments.

Load placement:

- compressive force at the draft-gear or center-sill end node;
- opposite balancing force or reference reaction through the support scheme.

### LC4: Longitudinal Tension

Purpose: estimate tensile force path through the center sill and tank attachments.

Load placement:

- tensile force at the draft-gear or center-sill end node;
- opposite balancing force or reference reaction through the support scheme.

### LC5: Lateral Inertia

Purpose: estimate transverse load transfer through tank rings, straps, saddle supports, and bolsters.

Load placement:

- transverse inertial force on tank ring nodes by tributary mass;
- optional additional lateral load at equipment nodes.

### LC6: Jacking or Local Lift

Purpose: identify high local bending in bolsters, end beams, and adjacent center-sill regions.

Load placement:

- imposed vertical reaction or displacement-equivalent load at selected lifting points;
- gravity loads retained from LC1 or LC2 where required by the study.

## Equivalent Payload Distribution

The first implementation should provide two payload placement modes:

- `tank_bottom_generators`: distribute vertical payload to the bottom tank longitudinal beams;
- `tank_lattice`: distribute vertical payload to tank ring nodes using a fill-level rule.

For both modes, the sum of generated loads must match the requested payload force within tolerance.

## Result Extraction

The postprocessor should report:

- maximum axial force by `member_tag`;
- maximum shear force by `member_tag`;
- maximum bending moment by `member_tag`;
- maximum torsional moment by `member_tag`;
- support reactions by station and support point;
- force-flow share between `center_sill`, `tank_longitudinal`, `tank_ring`, and `saddle_support`.

Recommended result groups:

| Group | Tags |
|---|---|
| Underframe | `center_sill`, `bolster_beam`, `end_beam`, `cross_beam`, `side_beam` |
| Tank lattice | `tank_longitudinal`, `tank_ring`, `tank_end_ring`, `tank_end_dish_spoke` |
| Interface | `saddle_support`, `middle_tank_lug`, `support_pad_stub`, `strap_tie` |
| Local equipment | `drain_support`, `manhole_ring`, `walkway_support`, `ladder_bracket` |

## Calculation-Scheme Invariants

The generated model should satisfy these invariants before analysis:

- all enabled loads are assigned to existing nodes or members;
- total applied load is reported for each global direction;
- support restraints remove rigid-body modes;
- every interface member connects one tank node and one frame node unless explicitly marked as local equipment;
- all mandatory result groups contain at least one member in the default tank example;
- repeated generation with the same parameter file produces identical result-group membership.

## Scheme Illustration

The calculation scheme is illustrated in [assets/tank_car_calculation_scheme_v0_3_0.svg](assets/tank_car_calculation_scheme_v0_3_0.svg).

