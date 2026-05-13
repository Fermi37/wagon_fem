# Parametric Wagon Generator Documentation

Version: `0.1.0-parametric-generator`

Date: 2026-05-13

Status: implementation-ready draft

Scope: first-stage parametric generation of spatial beam models for wagon bodies in the existing `wagon_fem` CSV format.

Primary objective: generate beam-only models for calculating member forces, bending moments, support reactions, and displacement trends with Pynite through `wagon_fem`.

Out of scope for this version:

- detailed shell or plate meshing;
- calibrated stress assessment by local welded joints;
- fatigue checks;
- buckling checks;
- automatic extraction of real section properties from drawings.

Acceptance target for version `0.1.0-parametric-generator`: the generator creates connected, loadable, and solvable open-wagon and covered-wagon frame topologies with documented approximate section classes.
