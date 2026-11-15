"""Assembly drawing of the selected variant, written as SVG. Owned by pcba-design.

The drawing uses the neutral rows and the captured board outline. It marks each `dnp` reference
with a cross and the text DNP. It marks each `hand_installed` reference with the text HAND.
The output has no clock value and no random value, so equal inputs give equal bytes.
It does not claim a physical result.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

SCALE = 4.0  # SVG units per millimeter.
MARGIN = 5.0


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def assembly_svg(rows: list, outline: list, variant: str, board_name: str) -> bytes:
    """Return the SVG bytes of the assembly drawing. `rows` are neutral rows. `outline` is the captured polygon."""
    xs = [point["x"] for point in outline]
    ys = [point["y"] for point in outline]
    min_x, max_y = min(xs), max(ys)
    width = (max(xs) - min_x) * SCALE + 2 * MARGIN
    height = (max(ys) - min(ys)) * SCALE + 2 * MARGIN + 12

    def px(x: float) -> float:
        return MARGIN + (x - min_x) * SCALE

    def py(y: float) -> float:
        return MARGIN + (max_y - y) * SCALE

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt(width)}mm" height="{_fmt(height)}mm" '
           f'viewBox="0 0 {_fmt(width)} {_fmt(height)}">',
           f'<title>{escape(board_name)} assembly, variant {escape(variant)}</title>']
    path = " ".join(f"{'M' if i == 0 else 'L'}{_fmt(px(p['x']))} {_fmt(py(p['y']))}" for i, p in enumerate(outline))
    out.append(f'<path d="{path} Z" fill="none" stroke="black" stroke-width="0.2"/>')
    for row in sorted(rows, key=lambda r: r["reference"]):
        state = row["variant_state"]
        if state == "exclude_from_assembly":
            continue
        x, y = px(row["x_mm"]), py(row["y_mm"])
        ref = escape(row["reference"])
        if state == "dnp":
            out.append(f'<g class="dnp" data-reference="{ref}">')
            out.append(f'<line x1="{_fmt(x - 2)}" y1="{_fmt(y - 2)}" x2="{_fmt(x + 2)}" y2="{_fmt(y + 2)}" '
                       f'stroke="red" stroke-width="0.3"/>')
            out.append(f'<line x1="{_fmt(x - 2)}" y1="{_fmt(y + 2)}" x2="{_fmt(x + 2)}" y2="{_fmt(y - 2)}" '
                       f'stroke="red" stroke-width="0.3"/>')
            out.append(f'<text x="{_fmt(x + 2.5)}" y="{_fmt(y - 2.5)}" font-size="2.5" fill="red">{ref} DNP</text>')
            out.append("</g>")
            continue
        label = f"{ref} HAND" if row["installation_method"] == "hand_installed" else ref
        out.append(f'<g class="populate" data-reference="{ref}">')
        out.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="0.6" fill="none" stroke="black" stroke-width="0.15"/>')
        out.append(f'<text x="{_fmt(x + 1)}" y="{_fmt(y - 1)}" font-size="2.2" fill="black">{escape(label)}</text>')
        out.append("</g>")
    footer = f"Variant {variant}. Generated from neutral data. Physical measurements are not measured."
    out.append(f'<text x="{_fmt(MARGIN)}" y="{_fmt(height - 3)}" font-size="2.2" fill="black">'
               f'{escape(footer)}</text>')
    out.append("</svg>")
    return ("\n".join(out) + "\n").encode("utf-8")
