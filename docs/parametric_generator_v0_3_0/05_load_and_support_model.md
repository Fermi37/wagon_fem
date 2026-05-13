# Load and Support Model

## Purpose

The load and support model defines first-stage cases for member-force and moment extraction in the tank-car beam system.

## Recommended Load Cases

### `tare_vertical`

Represents the structural weight of the tank and frame. The first implementation may apply a total vertical force to tank bottom generators and selected frame members.

### `gross_vertical`

Represents tank self-weight, payload weight, and selected equipment weight. This is the main case for evaluating center-sill, bolster, saddle, ring, and longitudinal tank-beam force distribution.

### `longitudinal_compression`

Represents compressive train action applied at the draft gear or center-sill end nodes. The case is useful for studying how much load remains in the center sill and how much is transmitted into tank attachments.

### `longitudinal_tension`

Represents tensile train action applied at the draft gear or center-sill end nodes. This case should share the same geometric model as `longitudinal_compression` and reverse force direction.

### `lateral_inertia`

Represents transverse inertial loading. The first implementation may distribute it to tank ring nodes by tributary mass.

### `support_lift_or_jacking`

Represents local lifting at selected bolster or frame-side nodes. This case helps reveal high bending moments in bolsters and local frame members.

## Payload Distribution

For a filled cylindrical tank, the generator should support three levels of payload distribution:

- uniform vertical load on lower tank longitudinal members;
- nodal loads on tank ring nodes below the fill level;
- sector-weighted nodal loads computed from angular tributary areas.

The first implementation should start with uniform load on lower tank longitudinal members because it is transparent, deterministic, and easy to validate against total force balance.

## Support Schemes

### `two_bolster_with_reference_lock`

Use paired vertical support points at both bolster stations. Add the minimum reference restraints needed to remove rigid-body motion.

### `four_point_bolster_reference`

Use four vertical support points, one longitudinal reference restraint, and transverse reference restraints at the bolster lines.

### `tank_saddle_study`

Place vertical supports through the saddle support paths and retain frame supports at bolster nodes. This scheme is useful for studying tank-to-frame load transfer and local reaction paths.

### `solver_stability_clamped_reference`

Use a fully restrained reference node and secondary vertical support points. This scheme is reserved for regression tests and solver smoke checks.

## Reaction Checks

Each solved load case should report:

- total applied `FX`, `FY`, and `FZ`;
- total support reaction in `FX`, `FY`, and `FZ`;
- relative force-balance error;
- maximum member axial force by tag;
- maximum bending moment by tag;
- maximum support reaction by station.

## Metadata Requirements

The exported model metadata should record:

- load-case name;
- payload fill level;
- total applied payload force;
- tank self-weight force;
- support scheme;
- release or slip assumptions represented only as metadata;
- station sources used by the generator.

