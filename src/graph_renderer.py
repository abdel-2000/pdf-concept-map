"""
graph_renderer.py
Mind-map style renderer: central node on the left, branches expanding right.
Each branch has a unique colour. Labels always fully visible.
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Palette — one colour per branch
BRANCH_COLORS = [
    "#E8A598",  # soft red
    "#F5D98B",  # soft yellow
    "#A8D5A2",  # soft green
    "#A8C8E8",  # soft blue
    "#D5A8D5",  # soft purple
    "#F5C88B",  # soft orange
    "#A8D5D5",  # soft teal
    "#E8C5A8",  # soft peach
    "#B8E8A8",  # soft lime
]
CENTRAL_COLOR  = "#2C2C2C"  # dark grey for central node
CENTRAL_TEXT   = "#FFFFFF"
BRANCH_TEXT    = "#1A1A1A"
LINE_COLOR     = "#888888"
BG_COLOR       = "#FAFAFA"


def render_graph(concept_map: dict, figsize=(16, 10)) -> bytes:
    nodes = concept_map.get("nodes", [])
    edges = concept_map.get("edges", [])
    title = concept_map.get("title", "Concept Map")

    if not nodes:
        return _empty_image(title)

    # Find central node (first "main" type, or first node)
    central_id = None
    for n in nodes:
        if n.get("type") == "main":
            central_id = str(n["id"])
            break
    if central_id is None:
        central_id = str(nodes[0]["id"])

    # Build children map from edges
    children = {}
    for edge in edges:
        src = str(edge.get("from", ""))
        dst = str(edge.get("to", ""))
        lbl = edge.get("label", "")
        if src not in children:
            children[src] = []
        children[src].append({"id": dst, "label": lbl})

    # Get all nodes as dict
    node_dict = {str(n["id"]): n for n in nodes}
    central_label = node_dict[central_id].get("label", "")

    # Children of central node
    direct_children = children.get(central_id, [])
    # Add any node not connected as orphan
    connected = {c["id"] for c in direct_children}
    for nid, n in node_dict.items():
        if nid != central_id and nid not in connected:
            direct_children.append({"id": nid, "label": ""})

    n_branches = len(direct_children)

    fig, ax = plt.subplots(figsize=figsize, facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold",
                 color="#1B3A5C", pad=14)

    # Central node position (left-center)
    cx, cy = 1.8, 5.0

    # Branch positions spread vertically on the right
    if n_branches == 0:
        _draw_node(ax, cx, cy, central_label, CENTRAL_COLOR, CENTRAL_TEXT,
                   fontsize=12, bold=True)
    else:
        # Vertical spacing
        total_height = min(n_branches * 1.4, 8.0)
        y_start = cy + total_height / 2
        y_step  = total_height / max(n_branches - 1, 1) if n_branches > 1 else 0

        for i, child in enumerate(direct_children):
            color = BRANCH_COLORS[i % len(BRANCH_COLORS)]
            bx = 5.5
            by = y_start - i * y_step if n_branches > 1 else cy

            # Curved line from central to branch
            _draw_curve(ax, cx + 0.55, cy, bx - 0.55, by, color)

            # Relation label on the curve
            rel_label = child.get("label", "")
            if rel_label:
                mx = (cx + bx) / 2
                my = (cy + by) / 2 + 0.15
                ax.text(mx, my, rel_label, fontsize=7.5, color="#555555",
                        ha="center", va="center",
                        bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                  ec=color, alpha=0.85),
                        zorder=6)

            # Branch node
            child_node = node_dict.get(child["id"], {})
            child_label = child_node.get("label", child["id"])

            # Sub-children of this branch
            sub_children = children.get(child["id"], [])

            if sub_children:
                # Draw branch node slightly left, sub-nodes further right
                bx2 = bx
                _draw_node(ax, bx2, by, child_label, color, BRANCH_TEXT,
                           fontsize=10, bold=True)

                sub_total = len(sub_children) * 1.0
                sub_start = by + sub_total / 2
                for j, sub in enumerate(sub_children):
                    sub_y = sub_start - j * 1.0
                    sub_x = 8.2
                    sub_color = _lighten(color)
                    _draw_curve(ax, bx2 + 0.5, by, sub_x - 0.4, sub_y, sub_color)

                    sub_node  = node_dict.get(sub["id"], {})
                    sub_label = sub_node.get("label", sub["id"])
                    sub_rel   = sub.get("label", "")
                    if sub_rel:
                        ax.text((bx2 + sub_x) / 2, (by + sub_y) / 2 + 0.12,
                                sub_rel, fontsize=7, color="#666666",
                                ha="center", va="center",
                                bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                          ec=sub_color, alpha=0.8),
                                zorder=6)
                    _draw_node(ax, sub_x, sub_y, sub_label, sub_color,
                               BRANCH_TEXT, fontsize=9)
            else:
                _draw_node(ax, bx, by, child_label, color, BRANCH_TEXT,
                           fontsize=10, bold=True)

        # Draw central node on top
        _draw_node(ax, cx, cy, central_label, CENTRAL_COLOR, CENTRAL_TEXT,
                   fontsize=12, bold=True, width=1.0)

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _draw_node(ax, x, y, label, bg_color, text_color,
               fontsize=10, bold=False, width=None):
    """Draw a rounded rectangle node with text."""
    lines = _wrap(label, 18)
    text  = "\n".join(lines)
    weight = "bold" if bold else "normal"
    ax.text(x, y, text,
            fontsize=fontsize, fontweight=weight,
            color=text_color, ha="center", va="center",
            multialignment="center",
            bbox=dict(
                boxstyle="round,pad=0.45",
                facecolor=bg_color,
                edgecolor=_darken(bg_color),
                linewidth=1.5,
                alpha=0.95,
            ),
            zorder=10)


def _draw_curve(ax, x0, y0, x1, y1, color):
    """Draw a smooth bezier-like curve using a Path."""
    from matplotlib.path import Path
    import matplotlib.patches as patches

    # Control point for curve
    cx = (x0 + x1) / 2
    cy0 = y0
    cy1 = y1

    verts = [(x0, y0), (cx, cy0), (cx, cy1), (x1, y1)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    path  = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor="none",
                              edgecolor=color, linewidth=1.8, zorder=3)
    ax.add_patch(patch)


def _wrap(text: str, max_len: int) -> list:
    words = text.split()
    lines, line = [], []
    for w in words:
        if line and len(" ".join(line + [w])) > max_len:
            lines.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))
    return lines or [text]


def _darken(hex_color: str, factor: float = 0.6) -> str:
    """Return a darker version of a hex colour."""
    if not hex_color.startswith("#") or len(hex_color) != 7:
        return "#888888"
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = int(r * factor); g = int(g * factor); b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(hex_color: str, factor: float = 0.85) -> str:
    """Return a lighter version of a hex colour."""
    if not hex_color.startswith("#") or len(hex_color) != 7:
        return "#cccccc"
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def _empty_image(title: str) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG_COLOR)
    ax.text(0.5, 0.5, f"No nodes found for:\n{title}",
            ha="center", va="center", fontsize=14, color="#1B3A5C")
    ax.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
