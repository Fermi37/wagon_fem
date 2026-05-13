# CSV Contract

## Combined CSV Structure

`wagon_fem` accepts one combined CSV file with a node table followed by an edge table. The edge table begins at the row whose header contains `edge_id`, `start_node`, or `end_node`.

## Node Table

Required columns:

| Column | Meaning | Unit |
|---|---:|---:|
| `node_id` | unique node identifier | dimensionless |
| `x` | longitudinal coordinate | mm |
| `y` | vertical coordinate | mm |
| `z` | transverse coordinate | mm |

Optional support columns:

| Column | Meaning |
|---|---|
| `support_dx` | restrained displacement along `x` |
| `support_dy` | restrained displacement along `y` |
| `support_dz` | restrained displacement along `z` |
| `support_rx` | restrained rotation about `x` |
| `support_ry` | restrained rotation about `y` |
| `support_rz` | restrained rotation about `z` |

Optional nodal load columns:

| Column | Meaning | Unit |
|---|---:|---:|
| `fx` | nodal force along `x` | N |
| `fy` | nodal force along `y` | N |
| `fz` | nodal force along `z` | N |
| `mx` | nodal moment about `x` | N mm |
| `my` | nodal moment about `y` | N mm |
| `mz` | nodal moment about `z` | N mm |

## Edge Table

Required columns:

| Column | Meaning | Unit |
|---|---:|---:|
| `edge_id` | unique member identifier | dimensionless |
| `start_node` | first node identifier | dimensionless |
| `end_node` | second node identifier | dimensionless |

Recommended section and material columns:

| Column | Meaning | Unit |
|---|---:|---:|
| `E` | Young's modulus | N/mm^2 |
| `A` | cross-sectional area | mm^2 |
| `Iy` | second moment of area about local `y` axis | mm^4 |
| `Iz` | second moment of area about local `z` axis | mm^4 |
| `J` | torsional constant | mm^4 |

Optional distributed load columns:

| Column | Meaning | Unit |
|---|---:|---:|
| `w` | uniform member load intensity | N/mm |
| `w1` | start load intensity | N/mm |
| `w2` | end load intensity | N/mm |
| `dist_dir` | load direction, for example `FX`, `FY`, `FZ` | dimensionless |

Optional generation columns:

| Column | Meaning |
|---|---|
| `section_tag` | generator section class |
| `member_tag` | structural role |
| `n_segments` | requested subdivision count |

`section_tag` and `member_tag` are useful for auditing and postprocessing. The current loader ignores unknown columns during model construction where applicable.

## Export Rules

Node coordinates should be rounded to a fixed tolerance, initially `1e-6 mm`.

Coincident nodes should be merged by coordinate key.

Members with identical unordered node pairs and identical role should be rejected during generation.

Each `edge_id` should map to one physical member in the generated topology. Subdivision may be requested through `n_segments`.

## Minimal Example

```csv
node_id,x,y,z,support_dx,support_dy,support_dz,support_rx,support_ry,support_rz,fx,fy,fz,mx,my,mz
1,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0
2,1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0
edge_id,start_node,end_node,E,Iy,Iz,J,A,w,dist_dir,section_tag,member_tag
1,1,2,210000,80000000,120000000,5000000,9000,-20,FY,center_sill,center_sill
```
