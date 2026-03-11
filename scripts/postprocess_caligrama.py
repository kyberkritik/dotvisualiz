#!/usr/bin/env python3
"""postprocess_caligrama.py — Visual post-processor for the caligrama_extremo SVG.

Transforms a raw Graphviz SVG into an expressive visual piece with:
- Glow halos on core nodes
- Typographic hierarchy (font families, weights, sizes)
- Chromatic family differentiation
- Ghost orbit lines and calligraphic traces
- Subtle paper-grain texture layer
- Enhanced line weights and styles
"""

import argparse
import copy
import os
import re
import sys
import tempfile
from lxml import etree

NS = {"svg": "http://www.w3.org/2000/svg", "xlink": "http://www.w3.org/1999/xlink"}
SVG_NS = "http://www.w3.org/2000/svg"

# ── Chromatic families ──────────────────────────────────────────────
FAMILIES = {
    "nucleo":     {"fill": "#f2ede1", "stroke": "#1a1a18", "text": "#1a1a18",
                   "glow": "#d6cdb8", "halo_r": 60},
    "sistemica":  {"fill": "#dce7ef", "stroke": "#304a5f", "text": "#1e3448",
                   "glow": "#a8bed4", "halo_r": 40},
    "signo":      {"fill": "#f3dddd", "stroke": "#8c3d3d", "text": "#5c1e1e",
                   "glow": "#d4a0a0", "halo_r": 38},
    "fuga":       {"fill": "#e9e2f8", "stroke": "#6546a5", "text": "#3b2668",
                   "glow": "#bfb0e0", "halo_r": 38},
    "uso":        {"fill": "#efe4d5", "stroke": "#8b6a2f", "text": "#4a3818",
                   "glow": "#d4c4a4", "halo_r": 36},
    "estetica":   {"fill": "#ddeee8", "stroke": "#2e6b5d", "text": "#1a3f34",
                   "glow": "#a8d4c4", "halo_r": 36},
    "politica":   {"fill": "#efe7d8", "stroke": "#7a6740", "text": "#3e341f",
                   "glow": "#d0c4a8", "halo_r": 34},
    "resonancia": {"fill": "#e3efe0", "stroke": "#4b7a4d", "text": "#263e27",
                   "glow": "#a8d4aa", "halo_r": 34},
    "maquinaria": {"fill": "#fff2d8", "stroke": "#9a6a00", "text": "#5a3e00",
                   "glow": "#e8d4a0", "halo_r": 42},
}

# Map node ID prefixes to families
NODE_FAMILY_MAP = {
    "N": "nucleo", "L": "sistemica", "R": "signo", "D": "fuga",
    "A": "uso", "T": "estetica", "P": "politica", "S": "resonancia",
    "J": "maquinaria", "X": None,  # orbit points — no family
}

# Author nodes get special typographic treatment
AUTHOR_NODES = {"L0", "L1", "L2", "L3", "L4", "L5", "L6",
                "R0", "D0", "D1", "A0", "A1", "T0", "T1", "T2",
                "P0", "P1", "S0"}

CORE_NODES = {"N0", "N1", "N2", "N3", "N4"}
INNER_NODES = {"N5", "N6", "N7", "N8"}
MACHINE_NODES = {"J0", "J1", "J2", "J3", "J4"}


def get_node_id(g_element):
    """Extract the Graphviz node ID from a <g> element's <title>."""
    title_el = g_element.find("svg:title", NS)
    if title_el is not None and title_el.text:
        raw = title_el.text.strip()
        # Edges have titles like "N0->N1"
        if "->" in raw:
            return None
        return raw
    return None


def get_edge_id(g_element):
    """Extract edge endpoints from a <g> element's <title>."""
    title_el = g_element.find("svg:title", NS)
    if title_el is not None and title_el.text and "->" in title_el.text:
        return title_el.text.strip()
    return None


def node_family(nid):
    if not nid:
        return None
    for prefix, fam in NODE_FAMILY_MAP.items():
        if nid.startswith(prefix):
            return fam
    return None


def get_node_center(g_el):
    """Get the center coordinates of a node <g> element."""
    for el in g_el.iter():
        tag = etree.QName(el.tag).localname if isinstance(el.tag, str) else ""
        if tag == "ellipse":
            return float(el.get("cx", 0)), float(el.get("cy", 0))
        if tag == "polygon":
            points = el.get("points", "")
            coords = re.findall(r"([-\d.]+),([-\d.]+)", points)
            if coords:
                xs = [float(c[0]) for c in coords]
                ys = [float(c[1]) for c in coords]
                return sum(xs)/len(xs), sum(ys)/len(ys)
    return None, None


# ── SVG Defs: filters, gradients, patterns ──────────────────────────

def build_defs(poster_mode=False):
    """Create <defs> block with filters, gradients, patterns."""
    defs = etree.Element(f"{{{SVG_NS}}}defs")

    # Glow filter for halos
    if not poster_mode:
        for fam_name, fam in FAMILIES.items():
            f = etree.SubElement(defs, f"{{{SVG_NS}}}filter",
                                 id=f"glow-{fam_name}",
                                 x="-50%", y="-50%", width="200%", height="200%")
            flood = etree.SubElement(f, f"{{{SVG_NS}}}feFlood",
                                     result="flood")
            flood.set("flood-color", fam.get("glow", "#ccc"))
            flood.set("flood-opacity", "0.35")
            etree.SubElement(f, f"{{{SVG_NS}}}feComposite",
                             **{"in": "flood", "in2": "SourceGraphic", "operator": "in", "result": "masked"})
            etree.SubElement(f, f"{{{SVG_NS}}}feGaussianBlur",
                             **{"in": "masked", "stdDeviation": "8", "result": "blur"})
            merge = etree.SubElement(f, f"{{{SVG_NS}}}feMerge")
            etree.SubElement(merge, f"{{{SVG_NS}}}feMergeNode", **{"in": "blur"})
            etree.SubElement(merge, f"{{{SVG_NS}}}feMergeNode", **{"in": "SourceGraphic"})

    # Paper grain texture
    if not poster_mode:
        turb_filter = etree.SubElement(defs, f"{{{SVG_NS}}}filter",
                                        id="paper-grain",
                                        x="0%", y="0%", width="100%", height="100%")
        etree.SubElement(turb_filter, f"{{{SVG_NS}}}feTurbulence",
                         type="fractalNoise", baseFrequency="0.65",
                         numOctaves="4", stitchTiles="stitch", result="noise")
        etree.SubElement(turb_filter, f"{{{SVG_NS}}}feColorMatrix",
                         type="saturate", values="0", **{"in": "noise", "result": "gray"})
        etree.SubElement(turb_filter, f"{{{SVG_NS}}}feBlend",
                         **{"in": "SourceGraphic", "in2": "gray", "mode": "multiply"})

    return defs


# ── Styling transforms ──────────────────────────────────────────────

def style_node(g_el, nid, poster_mode=False):
    """Apply chromatic and typographic styling to a node group."""
    fam = node_family(nid)
    if not fam:
        return
    fam_data = FAMILIES.get(fam, {})

    # Apply glow filter to core / author / machine nodes
    if not poster_mode and nid in (CORE_NODES | AUTHOR_NODES | MACHINE_NODES):
        g_el.set("filter", f"url(#glow-{fam})")

    # Style shapes (ellipse, polygon)
    for el in g_el.iter():
        tag = etree.QName(el.tag).localname if isinstance(el.tag, str) else ""

        if tag in ("ellipse", "polygon"):
            el.set("fill", fam_data.get("fill", "#fff"))
            el.set("stroke", fam_data.get("stroke", "#333"))

            # Pen width hierarchy
            if nid == "N0":
                el.set("stroke-width", "3.5")
            elif nid in CORE_NODES:
                el.set("stroke-width", "2.8")
            elif nid in AUTHOR_NODES:
                el.set("stroke-width", "2.2")
            elif nid in MACHINE_NODES:
                el.set("stroke-width", "2.8")

        if tag == "text":
            el.set("fill", fam_data.get("text", "#222"))

            # Typographic hierarchy
            if nid == "N0":
                el.set("font-family", "'Georgia', 'Palatino Linotype', 'Times New Roman', serif")
                el.set("font-size", "17")
                el.set("font-weight", "bold")
                el.set("letter-spacing", "1.5")
            elif nid in CORE_NODES:
                el.set("font-family", "'Georgia', 'Palatino Linotype', serif")
                el.set("font-size", "14")
                el.set("font-weight", "bold")
            elif nid in INNER_NODES:
                el.set("font-family", "'Georgia', serif")
                el.set("font-size", "12")
                el.set("font-style", "italic")
            elif nid in AUTHOR_NODES:
                el.set("font-family", "'Helvetica Neue', 'Arial', sans-serif")
                el.set("font-size", "13")
                el.set("font-weight", "bold")
                el.set("font-variant", "small-caps")
                el.set("letter-spacing", "0.8")
            elif nid in MACHINE_NODES:
                el.set("font-family", "'Courier New', 'Consolas', monospace")
                el.set("font-size", "12")
                el.set("font-weight", "bold")
            else:
                # Derived concepts
                el.set("font-family", "'Georgia', serif")
                el.set("font-size", "11")


def classify_edge(edge_id):
    """Classify an edge for visual treatment."""
    if not edge_id:
        return "default"
    src, dst = edge_id.split("->")
    src, dst = src.strip(), dst.strip()

    # Orbit traces
    if src.startswith("X") or dst.startswith("X"):
        return "orbit"

    # Nuclear connections
    if src.startswith("N") and dst.startswith("N"):
        return "nuclear"

    # Lines of force: author → core concept
    if src in AUTHOR_NODES and dst.startswith("N"):
        return "force"
    if src.startswith("L") and dst == "A0":
        return "force"

    # Machine connections
    if src.startswith("J") or dst.startswith("J"):
        return "machine"

    # Deleuzian flight lines
    if src.startswith("D") or dst.startswith("D"):
        return "flight"

    # Baudrillard chain
    if src.startswith("R") or dst.startswith("R"):
        return "sign"

    return "default"


EDGE_STYLES = {
    "nuclear":  {"stroke-width": "3.2", "stroke": "#1a1a18", "opacity": "0.95"},
    "force":    {"stroke-width": "2.6", "stroke": None, "opacity": "0.9"},
    "flight":   {"stroke-width": "2.0", "stroke": "#6546a5", "opacity": "0.85",
                 "stroke-dasharray": "8,4"},
    "sign":     {"stroke-width": "2.2", "stroke": "#8c3d3d", "opacity": "0.88"},
    "machine":  {"stroke-width": "2.4", "stroke": "#7a5d3a", "opacity": "0.88"},
    "orbit":    {"stroke-width": "1.2", "stroke": "#c8bfa8", "opacity": "0.5",
                 "stroke-dasharray": "3,6"},
    "default":  {"stroke-width": "1.6", "stroke": None, "opacity": "0.82"},
}


def style_edge(g_el, edge_id, poster_mode=False):
    """Apply visual style to an edge group."""
    cls = classify_edge(edge_id)
    style_data = EDGE_STYLES.get(cls, EDGE_STYLES["default"])

    for el in g_el.iter():
        tag = etree.QName(el.tag).localname if isinstance(el.tag, str) else ""

        if tag == "path":
            if style_data.get("stroke"):
                el.set("stroke", style_data["stroke"])
            el.set("stroke-width", style_data.get("stroke-width", "1.5"))
            el.set("opacity", style_data.get("opacity", "0.85"))
            if style_data.get("stroke-dasharray"):
                el.set("stroke-dasharray", style_data["stroke-dasharray"])

        if tag == "polygon":
            # Arrowheads
            if style_data.get("stroke"):
                el.set("stroke", style_data["stroke"])
                el.set("fill", style_data["stroke"])

        if tag == "text":
            el.set("font-family", "'Georgia', serif")
            el.set("font-size", "9.5")
            el.set("font-style", "italic")
            el.set("fill", "#3a3a3a")


# ── Halo / ghost orbit layer ────────────────────────────────────────

def add_halo_circles(svg_root, node_groups):
    """Add subtle radial glow circles behind key nodes."""
    layer = etree.SubElement(svg_root, f"{{{SVG_NS}}}g",
                             id="halo-layer", opacity="0.30")

    for nid, g_el in node_groups.items():
        if nid not in (CORE_NODES | MACHINE_NODES):
            continue
        cx, cy = get_node_center(g_el)
        if cx is None:
            continue
        fam = node_family(nid)
        fam_data = FAMILIES.get(fam, {})
        r = fam_data.get("halo_r", 40)

        circle = etree.SubElement(layer, f"{{{SVG_NS}}}circle",
                                  cx=str(cx), cy=str(cy), r=str(r),
                                  fill=fam_data.get("glow", "#ccc"),
                                  opacity="0.4")
        circle.set("stroke", "none")


def add_ghost_orbits(svg_root, node_groups):
    """Add faint concentric orbit rings around the center."""
    layer = etree.SubElement(svg_root, f"{{{SVG_NS}}}g",
                             id="ghost-orbits", opacity="0.15")

    # Get center node position
    cx, cy = 0, 0
    if "N0" in node_groups:
        cx, cy = get_node_center(node_groups["N0"])
        if cx is None:
            cx, cy = 0, 0

    for i, r in enumerate([120, 240, 380, 540]):
        circle = etree.SubElement(layer, f"{{{SVG_NS}}}circle",
                                  cx=str(cx), cy=str(cy), r=str(r),
                                  fill="none",
                                  stroke="#b8a88a",
                                  opacity=str(0.4 - i * 0.08))
        circle.set("stroke-width", "0.8")
        circle.set("stroke-dasharray", f"{4 + i*2},{6 + i*3}")


def add_paper_grain_overlay(svg_root, width, height, poster_mode=False):
    """Add a very subtle paper grain texture overlay."""
    if poster_mode:
        return
    rect = etree.SubElement(svg_root, f"{{{SVG_NS}}}rect",
                            x="0", y="0", width=str(width), height=str(height),
                            fill="none", filter="url(#paper-grain)",
                            opacity="0.04")
    rect.set("pointer-events", "none")


# ── Main processing ─────────────────────────────────────────────────

def process_svg(input_path, output_path, poster_mode=False):
    """Load raw SVG, apply all visual enhancements, save."""
    parser = etree.XMLParser(remove_blank_text=True, huge_tree=True)
    tree = etree.parse(input_path, parser)
    root = tree.getroot()

    etree.cleanup_namespaces(root)

    # Get SVG dimensions
    vb = root.get("viewBox", "0 0 1000 1000")
    vb_parts = vb.split()
    svg_w = float(vb_parts[2]) if len(vb_parts) >= 3 else 1000
    svg_h = float(vb_parts[3]) if len(vb_parts) >= 4 else 1000

    # Build and insert defs
    defs = build_defs(poster_mode)
    # Check if defs already exists
    existing_defs = root.find(f"{{{SVG_NS}}}defs")
    if existing_defs is not None:
        for child in defs:
            existing_defs.append(child)
    else:
        root.insert(0, defs)

    # Collect node and edge groups
    node_groups = {}
    edge_groups = {}

    for g in root.iter(f"{{{SVG_NS}}}g"):
        cls = g.get("class", "")
        if cls == "node":
            nid = get_node_id(g)
            if nid:
                node_groups[nid] = g
        elif cls == "edge":
            eid = get_edge_id(g)
            if eid:
                edge_groups[eid] = g

    # Insert halo and orbit layers BEFORE nodes (under them visually)
    # Find the main graph group
    graph_g = root.find(f".//{{{SVG_NS}}}g[@class='graph']")
    target = graph_g if graph_g is not None else root

    if not poster_mode:
        add_ghost_orbits(target, node_groups)
        add_halo_circles(target, node_groups)

    # Style all nodes
    for nid, g_el in node_groups.items():
        style_node(g_el, nid, poster_mode)

    # Style all edges
    for eid, g_el in edge_groups.items():
        style_edge(g_el, eid, poster_mode)

    # Add paper grain overlay
    add_paper_grain_overlay(target, svg_w, svg_h, poster_mode)

    # Set background
    bg_rect = None
    for el in root.iter(f"{{{SVG_NS}}}polygon"):
        if el.get("fill") == "white" or el.get("fill") == "#faf7f0":
            bg_rect = el
            break
    if bg_rect is not None:
        bg_rect.set("fill", "#faf7f0")

    # Write output
    tree.write(output_path, xml_declaration=True, encoding="utf-8", pretty_print=True)
    print(f"  ✓ Written: {output_path}")
    return root, tree


def generate_html(svg_path, html_output_path):
    """Generate an interactive HTML viewer wrapping the SVG."""
    # Read SVG content
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Remove XML declaration if present
    svg_content = re.sub(r'<\?xml[^?]*\?>\s*', '', svg_content)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Caligrama Extremo — Cartografía Sociocibernética</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; }}

  body {{
    margin: 0;
    padding: 0;
    background: #f5f1e8;
    font-family: 'Inter', 'Helvetica Neue', sans-serif;
    color: #1a1a18;
    overflow-x: hidden;
  }}

  .header {{
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    border-bottom: 1px solid #d6cdb8;
    background: linear-gradient(180deg, #faf7f0 0%, #f5f1e8 100%);
  }}

  .header h1 {{
    font-family: 'Cormorant Garamond', 'Georgia', serif;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 0 0 0.3rem;
    color: #1a1a18;
  }}

  .header p {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
    font-style: italic;
    color: #5a5040;
    margin: 0;
    letter-spacing: 0.5px;
  }}

  .toolbar {{
    display: flex;
    justify-content: center;
    gap: 1rem;
    padding: 0.8rem;
    background: #eee9dd;
    border-bottom: 1px solid #d6cdb8;
    flex-wrap: wrap;
  }}

  .toolbar button {{
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    padding: 0.4rem 1rem;
    border: 1px solid #b8a88a;
    background: #faf7f0;
    color: #3a3020;
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.3px;
  }}

  .toolbar button:hover {{
    background: #1a1a18;
    color: #faf7f0;
    border-color: #1a1a18;
  }}

  .toolbar button.active {{
    background: #1a1a18;
    color: #faf7f0;
    border-color: #1a1a18;
  }}

  .svg-container {{
    position: relative;
    width: 100%;
    overflow: auto;
    background: #faf7f0;
    min-height: 80vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }}

  .svg-container svg {{
    max-width: 100%;
    height: auto;
    transition: transform 0.3s ease;
  }}

  /* Hover effects on nodes */
  .svg-container svg g.node:hover {{
    filter: brightness(1.08) drop-shadow(0 0 8px rgba(0,0,0,0.15));
    cursor: pointer;
  }}

  .svg-container svg g.node ellipse,
  .svg-container svg g.node polygon {{
    transition: all 0.3s ease;
  }}

  .svg-container svg g.node:hover ellipse,
  .svg-container svg g.node:hover polygon {{
    stroke-width: 3.5;
  }}

  /* Subtle breathing animation on halo layer */
  @keyframes breathe {{
    0%, 100% {{ opacity: 0.25; }}
    50% {{ opacity: 0.40; }}
  }}

  .svg-container svg #halo-layer {{
    animation: breathe 6s ease-in-out infinite;
  }}

  /* Ghost orbit pulse */
  @keyframes orbit-pulse {{
    0%, 100% {{ opacity: 0.12; }}
    50% {{ opacity: 0.22; }}
  }}

  .svg-container svg #ghost-orbits {{
    animation: orbit-pulse 8s ease-in-out infinite;
  }}

  /* Edge hover */
  .svg-container svg g.edge:hover path {{
    stroke-width: 4 !important;
    opacity: 1 !important;
  }}

  /* Legend */
  .legend-toggle {{
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    z-index: 100;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    padding: 0.5rem 1rem;
    border: 1px solid #b8a88a;
    background: #faf7f0;
    color: #3a3020;
    border-radius: 3px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}

  .legend {{
    position: fixed;
    bottom: 4rem;
    right: 1.5rem;
    z-index: 99;
    background: #faf7f0;
    border: 1px solid #b8a88a;
    border-radius: 4px;
    padding: 1rem 1.2rem;
    max-width: 300px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    font-size: 0.82rem;
    line-height: 1.6;
    display: none;
  }}

  .legend.visible {{
    display: block;
  }}

  .legend h3 {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 1rem;
    margin: 0 0 0.6rem;
    border-bottom: 1px solid #d6cdb8;
    padding-bottom: 0.4rem;
    font-weight: 600;
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.3rem;
  }}

  .legend-swatch {{
    width: 14px;
    height: 14px;
    border-radius: 2px;
    border: 1px solid rgba(0,0,0,0.15);
    flex-shrink: 0;
  }}

  .legend-line {{
    width: 24px;
    height: 3px;
    flex-shrink: 0;
    border-radius: 1px;
  }}

  .footer {{
    text-align: center;
    padding: 1.2rem;
    font-size: 0.75rem;
    color: #8a7e6a;
    border-top: 1px solid #d6cdb8;
    background: #f0ece3;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.3px;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>Caligrama Extremo</h1>
  <p>Cartografía sociocibernética · Poema visual maquínico</p>
</div>

<div class="toolbar">
  <button onclick="resetZoom()">↺ Reset</button>
  <button onclick="zoomIn()">+ Zoom In</button>
  <button onclick="zoomOut()">− Zoom Out</button>
  <button id="btn-poster" onclick="toggleMode('poster')">Poster</button>
  <button id="btn-poema" onclick="toggleMode('poema')" class="active">Poema Visual</button>
</div>

<div class="svg-container" id="svgContainer">
{svg_content}
</div>

<button class="legend-toggle" onclick="toggleLegend()">◈ Leyenda</button>

<div class="legend" id="legend">
  <h3>Familias conceptuales</h3>
  <div class="legend-item"><div class="legend-swatch" style="background:#f2ede1;border-color:#1a1a18;"></div> Núcleo (observación, sistema, comunicación)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#dce7ef;border-color:#304a5f;"></div> Sistémica (Luhmann, Bateson, von Foerster…)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#f3dddd;border-color:#8c3d3d;"></div> Signo / Simulacro (Baudrillard)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#e9e2f8;border-color:#6546a5;"></div> Fuga / Máquina (Deleuze, Guattari)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#efe4d5;border-color:#8b6a2f;"></div> Uso / Cuerpo (Agamben, de Certeau)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#ddeee8;border-color:#2e6b5d;"></div> Estética / Técnica (Benjamin, Simondon, Haraway)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#efe7d8;border-color:#7a6740;"></div> Política / Articulación (Laclau, Stuart Hall)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#e3efe0;border-color:#4b7a4d;"></div> Resonancia / Salida (Rosa)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#fff2d8;border-color:#9a6a00;"></div> Maquinaria propia (proyecto)</div>

  <h3 style="margin-top:0.8rem;">Tipos de línea</h3>
  <div class="legend-item"><div class="legend-line" style="background:#1a1a18;"></div> Conexión nuclear</div>
  <div class="legend-item"><div class="legend-line" style="background:#304a5f;"></div> Línea de fuerza</div>
  <div class="legend-item"><div class="legend-line" style="background:#6546a5;background:repeating-linear-gradient(90deg,#6546a5 0,#6546a5 6px,transparent 6px,transparent 10px);"></div> Línea de fuga</div>
  <div class="legend-item"><div class="legend-line" style="background:#c8bfa8;background:repeating-linear-gradient(90deg,#c8bfa8 0,#c8bfa8 3px,transparent 3px,transparent 8px);"></div> Órbita caligramática</div>
</div>

<div class="footer">
  Caligrama Extremo · Máquina deleuziana de pensamiento sociocibernético · Generado con Graphviz + postprocesado visual
</div>

<script>
let currentScale = 1;
const container = document.getElementById('svgContainer');
const svgEl = container.querySelector('svg');

function resetZoom() {{
  currentScale = 1;
  if (svgEl) svgEl.style.transform = 'scale(1)';
}}

function zoomIn() {{
  currentScale = Math.min(currentScale * 1.25, 5);
  if (svgEl) svgEl.style.transform = `scale(${{currentScale}})`;
}}

function zoomOut() {{
  currentScale = Math.max(currentScale / 1.25, 0.3);
  if (svgEl) svgEl.style.transform = `scale(${{currentScale}})`;
}}

function toggleLegend() {{
  document.getElementById('legend').classList.toggle('visible');
}}

function toggleMode(mode) {{
  const halo = svgEl ? svgEl.querySelector('#halo-layer') : null;
  const orbits = svgEl ? svgEl.querySelector('#ghost-orbits') : null;
  const btnPoster = document.getElementById('btn-poster');
  const btnPoema = document.getElementById('btn-poema');

  if (mode === 'poster') {{
    if (halo) halo.style.display = 'none';
    if (orbits) orbits.style.display = 'none';
    btnPoster.classList.add('active');
    btnPoema.classList.remove('active');
  }} else {{
    if (halo) halo.style.display = '';
    if (orbits) orbits.style.display = '';
    btnPoema.classList.add('active');
    btnPoster.classList.remove('active');
  }}
}}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {{
  if (e.key === '+' || e.key === '=') zoomIn();
  if (e.key === '-') zoomOut();
  if (e.key === '0') resetZoom();
  if (e.key === 'l' || e.key === 'L') toggleLegend();
}});
</script>

</body>
</html>"""

    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ Written: {html_output_path}")


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Post-process caligrama_extremo SVG")
    parser.add_argument("--input", required=True, help="Input raw SVG from Graphviz")
    parser.add_argument("--output", help="Output enhanced SVG")
    parser.add_argument("--poster", help="Output poster (cleaner) SVG")
    parser.add_argument("--html", help="Output interactive HTML viewer")
    args = parser.parse_args()

    if args.output:
        print("  Processing: expressive SVG…")
        process_svg(args.input, args.output, poster_mode=False)

    if args.poster:
        print("  Processing: poster SVG…")
        process_svg(args.input, args.poster, poster_mode=True)

    if args.html:
        tmp_svg = os.path.join(tempfile.gettempdir(), "caligrama_html_tmp.svg")
        process_svg(args.input, tmp_svg, poster_mode=False)
        generate_html(tmp_svg, args.html)
        os.unlink(tmp_svg)


if __name__ == "__main__":
    main()
