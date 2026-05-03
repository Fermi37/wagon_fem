import pandas as pd
from io import StringIO
from typing import Optional


def _import_FEModel3D_class():
    """Dynamically import the FEModel3D class from either Pynite or pynite packages.

    Some distributions expose a top-level package named `Pynite` (capitalized) while
    others may use `pynite`. The actual class lives in the submodule `FEModel3D`, so
    prefer importing that class directly.
    """
    # Import locally to avoid hard runtime dependency until needed.
    for pkg in ("Pynite", "pynite"):
        try:
            mod = __import__(f"{pkg}.FEModel3D", fromlist=["FEModel3D"])
            FEClass = getattr(mod, "FEModel3D", None)
            if FEClass is not None:
                return FEClass
        except Exception:
            try:
                pkgmod = __import__(pkg, fromlist=["FEModel3D"])
                FEClass = getattr(pkgmod, "FEModel3D", None)
                if FEClass is not None:
                    return FEClass
            except Exception:
                continue
    raise ImportError(
        "FEModel3D class not found in 'Pynite' or 'pynite' package. Please install pynite/pynitefa.")


FEModel3D = _import_FEModel3D_class()


def load_model_from_csv(csv_path: str, apply_node_props: bool = True, max_member_length: float = 0.0) -> FEModel3D:
    """Загружает модель из CSV файла.

    Parameters
    ----------
    csv_path:
        Path to CSV that may contain a node table followed by an edge table.
    apply_node_props:
        If True, look for support and nodal-load columns in the node table and
        apply them to the model (columns: FX,FY,FZ,MX,MY,MZ and support_dx, support_dy, ...).
    """

    # The CSV may contain two tables in one file: a node table followed by an edge table
    # (see `data/wagon_frame.csv`). We'll split the file by detecting the edge header and
    # parse each table separately.
    model = FEModel3D()

    with open(csv_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    edge_header_idx: Optional[int] = None
    for i, line in enumerate(lines):
        low = line.strip().lower()
        # detect likely start of edge table
        if low.startswith("edge_id") or "start_node" in low or "end_node" in low:
            edge_header_idx = i
            break

    node_lines = lines[:edge_header_idx] if edge_header_idx is not None else lines
    edge_lines = lines[edge_header_idx:] if edge_header_idx is not None else []

    # Parse nodes
    nodes_csv = "".join(node_lines).strip()
    if nodes_csv:
        nodes_df = pd.read_csv(StringIO(nodes_csv))

        # Create a lowercase-to-original column mapping for tolerant lookups
        nodes_cols = {c.lower(): c for c in nodes_df.columns}

        def _truthy(v):
            if pd.isna(v):
                return False
            if isinstance(v, (int, float)):
                return v != 0
            s = str(v).strip().lower()
            return s in ("1", "true", "t", "yes", "y", "x", "on")

        for _, row in nodes_df.iterrows():
            # support various column names, prefer integer node ids when possible
            node_id = None
            if "node_id" in nodes_df.columns:
                node_id = row.get("node_id")
            elif "id" in nodes_df.columns:
                node_id = row.get("id")

            if pd.isna(node_id):
                continue
            try:
                nid = int(node_id)
            except Exception:
                nid = node_id

            # coordinates (handle common names)
            x = 0.0
            y = 0.0
            z = 0.0
            if "x" in nodes_cols:
                v = row.get(nodes_cols["x"])
                if not pd.isna(v):
                    x = float(v)
            if "y" in nodes_cols:
                v = row.get(nodes_cols["y"])
                if not pd.isna(v):
                    y = float(v)
            if "z" in nodes_cols:
                v = row.get(nodes_cols["z"])
                if not pd.isna(v):
                    z = float(v)

            model.add_node(nid, x, y, z)

            # Optionally read supports and nodal loads from extra CSV columns
            if apply_node_props:
                # Supports
                support_dx = _truthy(row.get(nodes_cols.get("support_dx", "")))
                support_dy = _truthy(row.get(nodes_cols.get("support_dy", "")))
                support_dz = _truthy(row.get(nodes_cols.get("support_dz", "")))
                support_rx = _truthy(row.get(nodes_cols.get("support_rx", "")))
                support_ry = _truthy(row.get(nodes_cols.get("support_ry", "")))
                support_rz = _truthy(row.get(nodes_cols.get("support_rz", "")))

                # Some CSVs may use a single 'supports' column with comma-separated flags
                if not any((support_dx, support_dy, support_dz, support_rx, support_ry, support_rz)) and "supports" in nodes_cols:
                    val = row.get(
                        nodes_cols["supports"]) if "supports" in nodes_cols else None
                    if not pd.isna(val):
                        parts = [p.strip().lower()
                                 for p in str(val).split(",")]
                        support_dx = support_dx or (
                            "dx" in parts or "x" in parts)
                        support_dy = support_dy or (
                            "dy" in parts or "y" in parts)
                        support_dz = support_dz or (
                            "dz" in parts or "z" in parts)
                        support_rx = support_rx or ("rx" in parts)
                        support_ry = support_ry or ("ry" in parts)
                        support_rz = support_rz or ("rz" in parts)

                if any((support_dx, support_dy, support_dz, support_rx, support_ry, support_rz)):
                    try:
                        model.def_support(
                            nid, support_dx, support_dy, support_dz, support_rx, support_ry, support_rz)
                    except Exception:
                        # ignore if node not present or API differs
                        pass

                # Nodal loads (FX,FY,FZ,MX,MY,MZ)
                for dir_key in ("fx", "fy", "fz", "mx", "my", "mz"):
                    if dir_key in nodes_cols:
                        try:
                            val = row.get(nodes_cols[dir_key])
                            if not pd.isna(val) and float(val) != 0:
                                model.add_node_load(
                                    nid, dir_key.upper(), float(val))
                        except Exception:
                            # ignore malformed loads
                            pass

    # Parse edges
    edges_csv = "".join(edge_lines).strip()
    if edges_csv:
        edges_df = pd.read_csv(StringIO(edges_csv))

        # Simple caches to avoid creating duplicate materials/sections
        material_cache = {}
        section_cache = {}

        import math

        for _, row in edges_df.iterrows():
            # Map common column names used in exported CSVs
            eid = row.get(
                "edge_id") if "edge_id" in edges_df.columns else row.get("id")
            start = row.get("start_node") or row.get(
                "node_i") or row.get("i_node") or row.get("from")
            end = row.get("end_node") or row.get(
                "node_j") or row.get("j_node") or row.get("to")
            if pd.isna(start) or pd.isna(end):
                # skip malformed rows
                continue
            try:
                start = int(start)
            except Exception:
                pass
            try:
                end = int(end)
            except Exception:
                pass

            # section properties (provide defaults if missing)
            E = float(row.get("E") or row.get("E_modulus") or 210000)
            Iy = float(row.get("Iy") or 0.0)
            Iz = float(row.get("Iz") or 0.0)
            J = float(row.get("J") or 0.0)
            A = float(row.get("A") or row.get("area") or 1.0)

            # Create or reuse a material for this E
            mat_key = f"mat_{int(E)}"
            if mat_key not in material_cache:
                # estimate shear modulus and use typical steel properties
                nu = 0.3
                G = E / (2 * (1 + nu))
                rho = 7850
                try:
                    model.add_material(mat_key, E, G, nu, rho)
                except Exception:
                    # some FE versions may require different args; ignore if already present
                    pass
                material_cache[mat_key] = mat_key

            # Create or reuse a section for these geometric properties
            sec_key = f"S_{int(A)}_{int(Iy)}_{int(Iz)}_{int(J)}"
            if sec_key not in section_cache:
                try:
                    model.add_section(sec_key, A, Iy, Iz, J)
                except Exception:
                    pass
                section_cache[sec_key] = sec_key

            mname = f"M{int(eid)}" if (
                eid is not None and not pd.isna(eid)) else f"M{start}_{end}"

            # Determine segmentation for this member. CSV may optionally include
            # a 'n_segments' column to force a particular subdivision. Otherwise,
            # use max_member_length to decide how many segments are needed.
            nseg = None
            if "n_segments" in edges_df.columns:
                try:
                    v = row.get("n_segments")
                    if not pd.isna(v) and int(v) > 0:
                        nseg = int(v)
                except Exception:
                    nseg = None

            # Resolve node objects to compute physical length
            try:
                node_i = model.nodes[start]
                node_j = model.nodes[end]
                length = node_i.distance(node_j)
            except Exception:
                # If nodes aren't accessible, fall back to single segment
                length = 0.0

            if nseg is None:
                if max_member_length and length > 0 and length > max_member_length:
                    nseg = math.ceil(length / max_member_length)
                else:
                    nseg = 1

            if nseg <= 1:
                model.add_member(mname, start, end,
                                 material_cache[mat_key], section_cache[sec_key])
                member_names = [mname]

            else:
                # Create intermediate nodes along the straight line and add sub-members
                node_names = [start]
                xi, yi, zi = node_i.X, node_i.Y, node_i.Z
                xj, yj, zj = node_j.X, node_j.Y, node_j.Z
                for k in range(1, nseg):
                    new_name = f"{mname}_n{k}"
                    # linear interpolation
                    t = k / nseg
                    xk = xi + t * (xj - xi)
                    yk = yi + t * (yj - yi)
                    zk = zi + t * (zj - zi)
                    # Avoid clobbering existing node names
                    if new_name in model.nodes:
                        node_names.append(new_name)
                    else:
                        model.add_node(new_name, xk, yk, zk)
                        node_names.append(new_name)

                node_names.append(end)

                # Create sub-members
                for s in range(len(node_names) - 1):
                    sub_start = node_names[s]
                    sub_end = node_names[s + 1]
                    sub_name = f"{mname}_s{s+1}"
                    model.add_member(sub_name, sub_start, sub_end,
                                     material_cache[mat_key], section_cache[sec_key])
                member_names = [
                    f"{mname}_s{idx+1}" for idx in range(len(node_names)-1)]

            # Optional: parse distributed loads defined on the edge row. Supported
            # columns (case-insensitive): 'w', 'w1', 'w2', 'w_start', 'w_end',
            # and direction columns like 'dist_dir','dist_load_dir','load_dir','dir'.
            # If present, the loader will add member distributed loads to each
            # created member (or sub-member) splitting a linearly-varying load
            # across sub-members.
            try:
                # determine load direction
                dir_col_candidates = [
                    'dist_dir', 'dist_load_dir', 'load_dir', 'dir', 'direction']
                load_dir = None
                for c in dir_col_candidates:
                    if c in edges_df.columns:
                        v = row.get(c)
                        if not pd.isna(v):
                            load_dir = str(v).strip().upper()
                            break
                if load_dir is None or load_dir == '':
                    load_dir = 'FY'

                # determine w_start and w_end
                def _get_val(keys):
                    for k in keys:
                        if k in edges_df.columns:
                            v = row.get(k)
                            if not pd.isna(v):
                                try:
                                    return float(v)
                                except Exception:
                                    return None
                    return None

                w = _get_val(['w', 'load', 'w_uniform'])
                w1 = _get_val(['w1', 'w_start', 'w_a'])
                w2 = _get_val(['w2', 'w_end', 'w_b'])
                if w is not None and w1 is None and w2 is None:
                    w1 = w2 = w
                if w1 is None and w2 is not None:
                    w1 = w2
                if w2 is None and w1 is not None:
                    w2 = w1

                if (w1 is not None) or (w2 is not None):
                    # ensure numeric
                    w1 = 0.0 if w1 is None else float(w1)
                    w2 = 0.0 if w2 is None else float(w2)

                    # get total number of member pieces
                    pieces = len(
                        member_names) if 'member_names' in locals() else 1
                    for idx, sub_mname in enumerate(member_names):
                        # linear interpolation of w across the whole member
                        local_w1 = w1 + (idx / pieces) * (w2 - w1)
                        local_w2 = w1 + ((idx + 1) / pieces) * (w2 - w1)
                        try:
                            model.add_member_dist_load(
                                sub_mname, load_dir, local_w1, local_w2)
                        except Exception:
                            # ignore if API differs or member not found
                            pass
            except Exception:
                # do not fail loading model for missing/invalid load columns
                pass

    return model


def create_simple_wagon_model() -> FEModel3D:
    """Создает простую модель вагона для теста."""
    model = FEModel3D()

    # Узлы (рама)
    nodes = [
        (1, 0, 0, 0), (2, 4000, 0, 0), (3, 8000, 0, 0),
        (4, 0, 1500, 0), (5, 4000, 1500, 0), (6, 8000, 1500, 0)
    ]
    for n in nodes:
        model.add_node(*n)

    # Ребра (балки)
    # E=210000 МПа, Iy, Iz, J, A
    members = [
        ("M1", 1, 2, 210000, 5e6, 2e6, 1e5, 5000),
        ("M2", 2, 3, 210000, 5e6, 2e6, 1e5, 5000),
        ("M3", 4, 5, 210000, 5e6, 2e6, 1e5, 5000),
        ("M4", 5, 6, 210000, 5e6, 2e6, 1e5, 5000),
        ("M5", 1, 4, 210000, 3e6, 1.5e6, 8e4, 4000),
        ("M6", 2, 5, 210000, 3e6, 1.5e6, 8e4, 4000),
        ("M7", 3, 6, 210000, 3e6, 1.5e6, 8e4, 4000),
    ]

    # Add a default material and create sections for members
    default_E = 210000
    nu = 0.3
    G = default_E / (2 * (1 + nu))
    rho = 7850
    mat_name = f"mat_{int(default_E)}"
    try:
        model.add_material(mat_name, default_E, G, nu, rho)
    except Exception:
        pass

    section_cache = {}
    for m in members:
        mname, i_node, j_node, E, Iy, Iz, J, A = m
        sec_key = f"S_{int(A)}_{int(Iy)}_{int(Iz)}_{int(J)}"
        if sec_key not in section_cache:
            try:
                model.add_section(sec_key, A, Iy, Iz, J)
            except Exception:
                pass
            section_cache[sec_key] = sec_key

        model.add_member(mname, i_node, j_node, mat_name,
                         section_cache[sec_key])

    # Граничные условия (опоры)
    # Use the FEModel3D API's `def_support` method and pass node names as they were added (integers here)
    model.def_support(1, True, True, True, True, True, True)
    model.def_support(3, True, True, True, True, True, True)

    # Нагрузка (собственный вес + полезная)
    model.add_member_dist_load("M1", "Fy", -10, -10)
    model.add_member_dist_load("M2", "Fy", -10, -10)

    return model


def create_simply_supported_beam(L: float = 4000.0, w: float = -10.0, E: float = 210000.0,
                                 A: float = 5000.0, Iy: float = 5e6, Iz: float = 2e6,
                                 J: float = 1e5, support_type: str = "clamped", n_segments: int = 1) -> FEModel3D:
    """Create a simple single-span beam for verification tests.

    The function will automatically discretize into multiple colinear members when
    a non-clamped support configuration (e.g., simply-supported) is requested and
    a single segment would be unstable.

    Parameters
    ----------
    L : float
        Span length (mm)
    w : float
        Uniform distributed load (force per length, N/mm). Use negative for downward.
    support_type : str
        'clamped' for fixed ends, otherwise 'simple' (pinned/roller) for simply-supported.
    n_segments : int
        Number of beam elements to divide the span into. If support_type is not
        'clamped' and n_segments < 2, the function will use at least 2 segments to
        avoid numerical singularity for single-member simple supports.

    Returns
    -------
    FEModel3D
        The constructed FE model (unsolved).
    """
    model = FEModel3D()

    # Ensure enough segments for non-clamped supports
    if support_type != "clamped" and n_segments < 2:
        n_segments = 2

    # Create nodes evenly spaced along the X axis
    for i in range(n_segments + 1):
        node_id = i + 1
        x = i * (L / n_segments)
        model.add_node(node_id, x, 0.0, 0.0)

    # Material
    nu = 0.3
    G = E / (2 * (1 + nu))
    rho = 7850
    mat_name = f"mat_{int(E)}"
    try:
        model.add_material(mat_name, E, G, nu, rho)
    except Exception:
        pass

    # Section
    sec_name = "S_sim"
    try:
        model.add_section(sec_name, A, Iy, Iz, J)
    except Exception:
        pass

    # Members
    for i in range(n_segments):
        start = i + 1
        end = i + 2
        mname = f"M{i+1}"
        model.add_member(mname, start, end, mat_name, sec_name)
        # Apply uniform load on each member
        try:
            model.add_member_dist_load(mname, "FY", w, w)
        except Exception:
            # if API signature differs, ignore and continue
            pass

    # Supports: choose support configuration
    first_node = 1
    last_node = n_segments + 1

    if support_type == "clamped":
        # Fully fix both ends (clamped-clamped)
        model.def_support(first_node, True, True, True, True, True, True)
        model.def_support(last_node, True, True, True, True, True, True)
    else:
        # Pinned left, roller right (simple support)
        model.def_support(first_node, True, True, False, False, False, False)
        model.def_support(last_node, False, True, False, False, False, False)

    return model
