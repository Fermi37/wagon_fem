# Parameter Contract

## Purpose

The parameter contract defines a stable input structure for generating single-deck and double-deck passenger-car beam models. The current implementation can initially load the shared fields used by `v0.1.0`, then extend the schema with passenger-specific groups.

`YAML` means `YAML Ain't Markup Language`, a human-readable structured data format used here for parameter files.

## Top-Level Fields

```yaml
wagon_type: passenger_single_deck
geometry: {}
layout: {}
levels: {}
openings: {}
zones: {}
sections: {}
loads: {}
supports: {}
generation: {}
```

`wagon_type` selects the topology generator. Required values:

- `passenger_single_deck`;
- `passenger_double_deck`;
- later values for freight wagons remain supported by the existing generator.

## Geometry Parameters

`L_body` means body length in millimeters.

`B_body` means outside body width in millimeters.

`H_body` means body height from the reference floor or lower reference plane to the roof top in millimeters.

Recommended fields:

```yaml
geometry:
  length: 24537
  width: 3105
  floor_y: 0
  side_height: 3000
  roof_height: 650
  bolster_positions: [3768.5, 20768.5]
  end_positions: [0, 24537]
  coupler_axis_y: 1060
  body_reference: body_over_end_beams
```

For double-deck cars:

```yaml
geometry:
  length: 26232
  width: 3154
  external_width: 3185
  floor_y: 0
  lowered_floor_y: -450
  side_height: 4700
  roof_height: 550
  bolster_positions: [3616, 22616]
  end_positions: [0, 26232]
  coupler_axis_y: 1060
  gauge_profile: Tpr
```

The body reference should be recorded in metadata because published dimensions may use body length, length over coupler axes, or length over coupling faces.

## Level Parameters

`levels` defines vertical beam layers:

```yaml
levels:
  main_floor_y: 0
  lower_floor_y: -450
  interdeck_floor_y: 2100
  upper_window_sill_y: 2750
  upper_window_head_y: 3650
  roof_side_y: 4700
  roof_ridge_y: 5250
```

Single-deck models may omit `lower_floor_y` and `interdeck_floor_y`.

## Layout Parameters

```yaml
layout:
  cross_beam_pitch: 1000
  side_post_pitch: 850
  roof_bow_pitch: 850
  side_height_divisions: 5
  floor_longitudinal_count_each_side: 2
  include_diagonals: true
  include_rigid_offsets: true
  include_interdeck: true
```

The generator should merge pitch-generated coordinates with mandatory coordinates from bolsters, openings, stairwell boundaries, service zones, and user-defined stations.

## Opening Parameters

```yaml
openings:
  side_windows:
    - x_start: 6200
      x_end: 7350
      y_bottom: 1100
      y_top: 2050
      z_side: both
      repeat:
        count: 8
        pitch: 1700
  side_doors:
    - x_start: 800
      x_end: 1850
      y_bottom: 0
      y_top: 2100
      z_side: both
  end_doors:
    - x: 0
      z_start: -450
      z_end: 450
      y_bottom: 0
      y_top: 2000
```

`z_side` accepts `left`, `right`, or `both`.

## Zone Parameters

Zones describe regions that affect topology, support placement, loads, or member tags:

```yaml
zones:
  vestibules:
    - x_start: 0
      x_end: 2200
  service_rooms:
    - x_start: 2200
      x_end: 4500
  passenger_compartments:
    - x_start: 4500
      x_end: 20500
  sanitary_modules:
    - x_start: 20500
      x_end: 22800
  stairwells:
    - x_start: 2500
      x_end: 3900
    - x_start: 22300
      x_end: 23700
  lowered_floor:
    - x_start: 4300
      x_end: 21900
```

For a single-deck passenger car, `stairwells` and `lowered_floor` can be omitted.

## Section Assignment

```yaml
sections:
  default_E: 210000
  catalog: first_stage_passenger_v0.2.0
  center_sill: center_sill_placeholder
  side_sill: side_sill_placeholder
  bolster_beam: bolster_beam_placeholder
  end_beam: end_beam_placeholder
  cross_beam: cross_beam_placeholder
  floor_longitudinal: floor_longitudinal_placeholder
  side_post: side_post_placeholder
  opening_post: opening_post_placeholder
  side_belt: side_belt_placeholder
  end_post: end_post_placeholder
  main_impact_post: main_impact_post_placeholder
  roof_bow: roof_bow_placeholder
  roof_longitudinal: roof_longitudinal_placeholder
  interdeck_cross_beam: interdeck_cross_beam_placeholder
  interdeck_longitudinal: interdeck_longitudinal_placeholder
  diagonal_tie: diagonal_tie_equiv
  rigid_offset: rigid_offset_stub
```

The section catalog names remain semantic placeholders until measured or normative section properties are introduced.

## Load Parameters

```yaml
loads:
  vertical_distributed_load:
    enabled: true
    target_tags: [center_sill, side_sill, cross_beam, floor_longitudinal]
    w: -18
    dist_dir: FY
  equipment_zone_loads:
    - name: climate_unit
      x_start: 1000
      x_end: 3500
      y: 4700
      target_tags: [roof_longitudinal, roof_bow]
      w: -5
      dist_dir: FY
  longitudinal_end_load:
    enabled: false
    x_end: 0
    force: 1000000
    direction: FX
```

`FY` means force along the global vertical direction. `FX` means force along the global longitudinal direction.

## Support Parameters

```yaml
supports:
  scheme: four_point_bolster_reference
  support_points:
    - x: 3768.5
      y: 0
      z: -900
      dy: true
    - x: 3768.5
      y: 0
      z: 900
      dy: true
    - x: 20768.5
      y: 0
      z: -900
      dy: true
    - x: 20768.5
      y: 0
      z: 900
      dy: true
  reference_restraints:
    primary:
      x: 3768.5
      y: 0
      z: 0
      dx: true
      dy: true
      dz: true
    secondary:
      x: 20768.5
      y: 0
      z: 0
      dz: true
```

Named support schemes should remain reproducible through exported metadata.
