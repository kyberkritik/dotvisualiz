# Caligrama Extremo — Render & Post-Processing Guide

## Overview

This project transforms the `caligrama_extremo.dot` sociocybernetic concept map into an expressive visual piece — a hybrid between a constructivist poster, a visual poem, and a cybernetic diagram.

![Caligrama Extremo](https://github.com/user-attachments/assets/19b2e8eb-8ab3-487b-aae5-271474d8788f)

## Output Files

| File | Description |
|------|-------------|
| `dist/caligrama_extremo.svg` | Full expressive SVG with halos, ghost orbits, and enhanced typography |
| `dist/caligrama_extremo_poster.svg` | Cleaner poster version (no animated layers, no grain texture) |
| `dist/caligrama_extremo.png` | High-resolution PNG export (4000px wide) |
| `dist/caligrama_extremo.html` | Interactive HTML viewer with zoom, legend, hover effects, and breathing animations |

## Requirements

- **Graphviz** (`dot` command) — for DOT → SVG rendering
- **Python 3** with:
  - `lxml` — XML/SVG manipulation
  - `cairosvg` — SVG → PNG conversion

### Install dependencies

```bash
# Graphviz
sudo apt-get install graphviz    # Debian/Ubuntu
brew install graphviz             # macOS

# Python packages
pip install lxml cairosvg
```

## How to Regenerate

Run the full pipeline:

```bash
bash scripts/render_caligrama.sh
```

This will:
1. Render `caligrama_extremo.dot` → raw SVG via Graphviz (`neato` layout)
2. Post-process the SVG with visual enhancements (halos, typography, chromatic families)
3. Generate a clean poster variant
4. Export a high-res PNG
5. Generate an interactive HTML viewer

## Architecture

### Pipeline

```
caligrama_extremo.dot
        │
        ▼  (Graphviz neato)
   raw SVG
        │
        ▼  (postprocess_caligrama.py)
   ┌────┴────┐
   │         │
   ▼         ▼
 .svg      _poster.svg
 (expressive) (clean)
   │
   ├──▶ .png  (cairosvg)
   │
   └──▶ .html (embedded SVG + CSS animations + JS interactions)
```

### Post-Processing Layers

The Python post-processor (`scripts/postprocess_caligrama.py`) adds these visual layers:

1. **Chromatic families** — Each conceptual family gets a distinct color palette:
   - *Núcleo*: warm blacks, sepia, bone
   - *Sistémica*: grayish blues
   - *Signo/Simulacro*: muted reds, wine, oxide
   - *Fuga deleuziana*: violets, plum
   - *Uso/Cuerpo*: ochres, opaque golds, earth
   - *Estética-Técnica*: grayish greens, soft petrol
   - *Política/Articulación*: browns, sand, tobacco
   - *Resonancia/Salida*: soft greens
   - *Maquinaria propia*: amber, gold

2. **Typographic hierarchy**:
   - Core nodes → Georgia serif, bold, large, letter-spaced
   - Inner concepts → Georgia italic
   - Author nodes → Helvetica small-caps, bold
   - Machine nodes → Courier monospace, bold
   - Derived concepts → Georgia regular

3. **Glow halos** — Subtle radial glow behind core, author, and machine nodes

4. **Ghost orbits** — Faint concentric dashed circles emanating from the center

5. **Paper grain** — Ultra-subtle fractal noise texture overlay

6. **Edge classification** — Visual distinction between:
   - Nuclear connections (thick, dark)
   - Lines of force (medium, colored by family)
   - Lines of flight (dashed, violet)
   - Sign chains (medium, red)
   - Machine connections (medium, brown)
   - Calligraphic orbits (thin, dotted, faint)

### HTML Viewer Features

- **Zoom controls** (buttons + keyboard: `+`, `-`, `0`)
- **Poster/Poema Visual toggle** — switch between clean and expressive modes
- **Collapsible legend** (button + `L` key)
- **Hover effects** — nodes brighten and gain shadow on hover
- **Breathing animations** — halos and ghost orbits pulse subtly
- **Responsive** — works on desktop and mobile with zoom

## Structural vs. Stylistic Changes

### Structure (DOT file)
The original `caligrama_extremo.dot` was **not modified**. All conceptual content, node positions, relationships, and topology are preserved exactly as authored.

### Style (post-processing only)
All visual enhancements are applied *after* Graphviz rendering, in the SVG post-processing step:
- Colors and fills adjusted per chromatic family
- Font families, sizes, weights, and styles modified
- Stroke widths adjusted for visual hierarchy
- SVG filter effects added (glow, grain)
- Additional SVG elements added (halo circles, ghost orbit rings)
- Edge styles differentiated by relationship type

This separation ensures the conceptual structure remains untouched while enabling expressive visual treatment.
