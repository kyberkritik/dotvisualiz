#!/usr/bin/env bash
# render_caligrama.sh — Renders the caligrama_extremo DOT file into SVG, PNG, and HTML outputs.
# Usage: bash scripts/render_caligrama.sh
# Requirements: graphviz, python3, lxml, cairosvg

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOT_FILE="$REPO_ROOT/caligrama_extremo.dot"
DIST_DIR="$REPO_ROOT/dist"
SCRIPTS_DIR="$REPO_ROOT/scripts"

mkdir -p "$DIST_DIR"

echo "=== Step 1: Rendering DOT → raw SVG with Graphviz ==="
dot -Tsvg -Kneato "$DOT_FILE" -o "$DIST_DIR/caligrama_extremo_raw.svg"
echo "  → $DIST_DIR/caligrama_extremo_raw.svg"

echo "=== Step 2: Post-processing SVG (visual enhancement) ==="
python3 "$SCRIPTS_DIR/postprocess_caligrama.py" \
  --input "$DIST_DIR/caligrama_extremo_raw.svg" \
  --output "$DIST_DIR/caligrama_extremo.svg" \
  --poster "$DIST_DIR/caligrama_extremo_poster.svg"
echo "  → $DIST_DIR/caligrama_extremo.svg"
echo "  → $DIST_DIR/caligrama_extremo_poster.svg"

echo "=== Step 3: Generating PNG from post-processed SVG ==="
python3 - "$DIST_DIR" <<'PYEOF'
import cairosvg, sys, os
dist_dir = sys.argv[1]
svg_path = os.path.join(dist_dir, "caligrama_extremo.svg")
png_path = os.path.join(dist_dir, "caligrama_extremo.png")
cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=4000)
print(f"  → {png_path}")
PYEOF

echo "=== Step 4: Generating HTML viewer ==="
python3 "$SCRIPTS_DIR/postprocess_caligrama.py" \
  --input "$DIST_DIR/caligrama_extremo_raw.svg" \
  --html "$DIST_DIR/caligrama_extremo.html"
echo "  → $DIST_DIR/caligrama_extremo.html"

echo ""
echo "✓ All outputs generated in $DIST_DIR/"
ls -lh "$DIST_DIR/"
