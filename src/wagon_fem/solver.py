"""Solver utilities: import FEModel3D class robustly and provide helpers.

Provides:
- dynamic FEModel3D import
- run_analysis(model)
- get_moments_table(model)
- get_displacements_table(model)
- get_3d_figure(model, ...)
"""
from typing import Optional

import pandas as pd


def _import_FEModel3D_class():
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
        "FEModel3D class not found in 'Pynite' or 'pynite' package. Please install pynite.")


FEModel3D = _import_FEModel3D_class()


def run_analysis(model: FEModel3D):
    """Run model analysis (wrap Pynite call)."""
    model.analyze(check_statics=True)
    return model


def get_moments_table(model: FEModel3D) -> pd.DataFrame:
    data = []
    for member in model.members.values():
        try:
            member_length = member.L()
        except Exception:
            member_length = 1.0
        try:
            mz0 = member.moment('Mz', 0)
            mz1 = member.moment('Mz', member_length)
        except Exception:
            mz0 = mz1 = 0.0
        try:
            my0 = member.moment('My', 0)
            my1 = member.moment('My', member_length)
        except Exception:
            my0 = my1 = 0.0
        data.append({
            "Элемент": member.name,
            "Mz_start": mz0,
            "Mz_end": mz1,
            "My_start": my0,
            "My_end": my1,
            "Max_Mz": max(abs(mz0), abs(mz1)),
        })
    return pd.DataFrame(data)


def get_displacements_table(model: FEModel3D) -> pd.DataFrame:
    data = []

    def _pick_disp(mapping, combo='Combo 1'):
        if not mapping:
            return 0.0
        if combo in mapping:
            return mapping[combo]
        return next(iter(mapping.values()))

    for node in model.nodes.values():
        data.append({
            "Узел": node.name,
            "Dx": _pick_disp(getattr(node, 'DX', {})),
            "Dy": _pick_disp(getattr(node, 'DY', {})),
            "Dz": _pick_disp(getattr(node, 'DZ', {})),
        })
    return pd.DataFrame(data)


def get_3d_figure(model: FEModel3D,
                  deformed: bool = True,
                  scale: float = 1.0,
                  combo: str = 'Combo 1',
                  color_by: str = 'Mz',
                  sample_resolution: int = 11,
                  colormap: str = 'viridis',
                  show_colorbar: bool = True,
                  prefer_plotly: bool = True,
                  highlight_member: Optional[str] = None,
                  highlight_node: Optional[str] = None):
    """Create a 3D viewer for the model.

    Returns a Plotly Figure when plotly is available and preferred, otherwise
    returns a matplotlib 3D Figure.
    """

    # Helper to pick a displacement value from node DX/DY/DZ dicts
    def _pick_disp(mapping):
        if not mapping:
            return 0.0
        if combo in mapping:
            return mapping[combo]
        return next(iter(mapping.values()))

    # collect nodes and coordinates
    nodes = list(model.nodes.values())
    node_coords = [(n.X, n.Y, n.Z) for n in nodes]

    # deformed coordinates
    def_coords = []
    for n in nodes:
        dx = _pick_disp(getattr(n, 'DX', {}))
        dy = _pick_disp(getattr(n, 'DY', {}))
        dz = _pick_disp(getattr(n, 'DZ', {}))
        def_coords.append(
            (n.X + scale * dx, n.Y + scale * dy, n.Z + scale * dz))

    # optional matplotlib helpers
    try:
        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
    except Exception:
        cm = None
        mcolors = None

    def _sample_member_metric(mem, label, samples):
        vals = []
        try:
            L = mem.L()
        except Exception:
            L = getattr(mem, 'length', 0.0)
        if samples < 1:
            samples = 1
        for i in range(samples):
            if samples == 1:
                pos = 0.5 * L
            else:
                pos = i * (L / (samples - 1))
            try:
                if label in ('Mz', 'My'):
                    v = mem.moment(label, pos)
                else:
                    v = 0.0
            except Exception:
                try:
                    frac = (pos / L) if L else 0.0
                    if label in ('Mz', 'My'):
                        v = mem.moment(label, frac)
                    else:
                        v = 0.0
                except Exception:
                    v = 0.0
            try:
                vals.append(float(v))
            except Exception:
                vals.append(0.0)
        if not vals:
            return 0.0
        return max(abs(x) for x in vals)

    # compute metrics per member
    metrics = []
    for mem in model.members.values():
        try:
            if color_by in ('Mz', 'My'):
                v = _sample_member_metric(
                    mem, color_by, int(sample_resolution))
            else:
                v = 0.0
        except Exception:
            v = 0.0
        metrics.append(v)

    # Try Plotly interactive view first
    if prefer_plotly:
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            vmin = min(metrics) if metrics else 0.0
            vmax = max(metrics) if metrics else 1.0
            if vmin == vmax:
                vmin = 0.0

            for mi, mem in enumerate(model.members.values()):
                xi, yi, zi = mem.i_node.X, mem.i_node.Y, mem.i_node.Z
                xj, yj, zj = mem.j_node.X, mem.j_node.Y, mem.j_node.Z
                if deformed:
                    xi += scale * _pick_disp(getattr(mem.i_node, 'DX', {}))
                    yi += scale * _pick_disp(getattr(mem.i_node, 'DY', {}))
                    zi += scale * _pick_disp(getattr(mem.i_node, 'DZ', {}))
                    xj += scale * _pick_disp(getattr(mem.j_node, 'DX', {}))
                    yj += scale * _pick_disp(getattr(mem.j_node, 'DY', {}))
                    zj += scale * _pick_disp(getattr(mem.j_node, 'DZ', {}))

                try:
                    m_mean = 0.5 * (mem.moment('Mz', 0) +
                                    mem.moment('Mz', mem.L()))
                except Exception:
                    m_mean = 0.0

                color_hex = 'royalblue'
                if metrics:
                    v = metrics[mi]
                    try:
                        if cm is not None and mcolors is not None:
                            cmap = cm.get_cmap(colormap or 'viridis')
                            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
                            rgba = cmap(norm(v))
                            color_hex = mcolors.to_hex(rgba)
                    except Exception:
                        color_hex = 'royalblue'

                is_highlight = (highlight_member is not None and str(
                    mem.name) == str(highlight_member))
                line_width = 10 if is_highlight else 6
                line_color = 'red' if is_highlight else color_hex

                # attach customdata so clicks can identify the member
                customdata = [f"MEM:{mem.name}", f"MEM:{mem.name}"]
                hover_text = f"{mem.name}\\n{color_by}: {metrics[mi]:.3g}\\navg Mz: {m_mean:.3g}"

                fig.add_trace(go.Scatter3d(
                    x=[xi, xj], y=[yi, yj], z=[zi, zj],
                    mode='lines', line=dict(color=line_color, width=line_width),
                    hoverinfo='text', text=hover_text, customdata=customdata
                ))

            # nodes
            if deformed:
                xs, ys, zs = zip(*def_coords) if def_coords else ([], [], [])
            else:
                xs, ys, zs = zip(*node_coords) if node_coords else ([], [], [])

            # node markers with customdata for identification
            node_custom = [f"NODE:{n.name}" for n in nodes]
            node_texts = [str(n.name) for n in nodes]
            marker_size = 6
            if highlight_node is not None:
                marker_colors = ['crimson' if str(n.name) == str(
                    highlight_node) else 'lightgray' for n in nodes]
                marker_sizes = [12 if str(n.name) == str(
                    highlight_node) else 6 for n in nodes]
            else:
                marker_colors = ['red' for _ in nodes]
                marker_sizes = [6 for _ in nodes]

            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs, mode='markers+text',
                marker=dict(size=marker_sizes, color=marker_colors),
                text=node_texts, textposition='top center', name='nodes',
                customdata=node_custom, hovertemplate='Node: %{customdata}<extra></extra>'
            ))

            if show_colorbar and metrics:
                mids_x = []
                mids_y = []
                mids_z = []
                for mem in model.members.values():
                    xi, yi, zi = mem.i_node.X, mem.i_node.Y, mem.i_node.Z
                    xj, yj, zj = mem.j_node.X, mem.j_node.Y, mem.j_node.Z
                    if deformed:
                        xi += scale * _pick_disp(getattr(mem.i_node, 'DX', {}))
                        yi += scale * _pick_disp(getattr(mem.i_node, 'DY', {}))
                        zi += scale * _pick_disp(getattr(mem.i_node, 'DZ', {}))
                        xj += scale * _pick_disp(getattr(mem.j_node, 'DX', {}))
                        yj += scale * _pick_disp(getattr(mem.j_node, 'DY', {}))
                        zj += scale * _pick_disp(getattr(mem.j_node, 'DZ', {}))
                    mids_x.append(0.5 * (xi + xj))
                    mids_y.append(0.5 * (yi + yj))
                    mids_z.append(0.5 * (zi + zj))

                plotly_cmap = {
                    'viridis': 'Viridis', 'plasma': 'Plasma', 'inferno': 'Inferno',
                    'magma': 'Magma', 'cividis': 'Cividis'
                }.get((colormap or 'viridis').lower(), 'Viridis')

                fig.add_trace(go.Scatter3d(
                    x=mids_x, y=mids_y, z=mids_z, mode='markers',
                    marker=dict(size=2, color=metrics, colorscale=plotly_cmap,
                                cmin=vmin, cmax=vmax, colorbar=dict(title=color_by)),
                    hoverinfo='none', showlegend=False,
                    customdata=[
                        f"MEM:{mem.name}" for mem in model.members.values()]
                ))

            fig.update_layout(scene=dict(aspectmode='data'),
                              margin=dict(l=0, r=0, b=0, t=0))
            return fig

        except Exception:
            # fall back to matplotlib below
            pass

    # matplotlib fallback
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    except Exception:
        raise

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    vmin = min(metrics) if metrics else 0.0
    vmax = max(metrics) if metrics else 1.0
    if vmin == vmax:
        vmin = 0.0

    for mi, mem in enumerate(model.members.values()):
        xi, yi, zi = mem.i_node.X, mem.i_node.Y, mem.i_node.Z
        xj, yj, zj = mem.j_node.X, mem.j_node.Y, mem.j_node.Z
        if deformed:
            xi += scale * _pick_disp(getattr(mem.i_node, 'DX', {}))
            yi += scale * _pick_disp(getattr(mem.i_node, 'DY', {}))
            zi += scale * _pick_disp(getattr(mem.i_node, 'DZ', {}))
            xj += scale * _pick_disp(getattr(mem.j_node, 'DX', {}))
            yj += scale * _pick_disp(getattr(mem.j_node, 'DY', {}))
            zj += scale * _pick_disp(getattr(mem.j_node, 'DZ', {}))

        color_hex = 'blue'
        if metrics:
            v = metrics[mi]
            try:
                if cm is not None and mcolors is not None:
                    cmap = cm.get_cmap(colormap or 'viridis')
                    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
                    rgba = cmap(norm(v))
                    color_hex = mcolors.to_hex(rgba)
            except Exception:
                color_hex = 'blue'

        ax.plot([xi, xj], [yi, yj], [zi, zj], color=color_hex, linewidth=2)

    xs, ys, zs = (zip(*def_coords) if deformed else zip(*
                  node_coords)) if nodes else ([], [], [])
    ax.scatter(xs, ys, zs, color='red', s=12)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    if show_colorbar and metrics and cm is not None and mcolors is not None:
        try:
            cmap = cm.get_cmap(colormap or 'viridis')
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
            sm = cm.ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])
            fig.colorbar(sm, ax=ax, shrink=0.5, aspect=10, label=color_by)
        except Exception:
            pass

    return fig
