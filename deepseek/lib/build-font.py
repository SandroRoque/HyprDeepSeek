#!/usr/bin/env python3
"""Build DeepSeekWhale.ttf with fontforge: the DeepSeek mark as one PUA glyph.

Waybar's `custom` modules are text-only, so a font glyph is the only way to show
our own mark *and* get a normal JSON tooltip. This compiles the mark into a
single codepoint (U+E900) so the module can render it with a `format` string and
colour it with plain CSS.

Run with:  make font   (or python3 lib/build-font.py)
"""

import pathlib
import re
import sys

import fontforge

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "resources" / "whale.path"
OUT = HERE.parent / "resources" / "DeepSeekWhale.ttf"

EM = 1000
CODEPOINT = 0xE900
FAMILY = "DeepSeek Whale"
STYLE = "Regular"
MARK_FRACTION = 0.88        # mark height as a fraction of the em


def parse_ops(path_data: str):
    """SVG path -> list of contours; each is a list of ('M'|'L', x, y) / ('C', 6 pts)."""
    toks = re.findall(r"[MLCZ]|-?\d*\.?\d+", path_data)
    contours, cur, cmd, i = [], [], None, 0
    while i < len(toks):
        t = toks[i]
        if t in "MLCZ":
            cmd = t
            i += 1
            if cmd == "Z" and cur:
                contours.append(cur); cur = []
            continue
        if cmd == "M":
            cur.append(("M", float(toks[i]), float(toks[i + 1]))); i += 2
            cmd = "L"
        elif cmd == "L":
            cur.append(("L", float(toks[i]), float(toks[i + 1]))); i += 2
        elif cmd == "C":
            cur.append(("C", *[float(v) for v in toks[i:i + 6]])); i += 6
    if cur:
        contours.append(cur)
    return contours


def build():
    contours = parse_ops(SRC.read_text().strip())

    xs = [v for c in contours for s in c for v in s[1::2]]
    ys = [v for c in contours for s in c for v in s[2::2]]
    xmin_s, ymax_s = min(xs), max(ys)
    height = ymax_s - min(ys)
    scale = (EM * MARK_FRACTION) / height
    sw = int(round((max(xs) - xmin_s) * scale))

    font = fontforge.font()
    font.em = EM
    font.ascent = int(EM * 0.92)
    font.descent = EM - font.ascent
    font.fontname = "DeepSeekWhale"
    font.familyname = FAMILY
    font.fullname = FAMILY

    glyph = font.createChar(CODEPOINT, "whale")
    pen = glyph.glyphPen()

    for contour in contours:
        first = True
        for seg in contour:
            if seg[0] == "M":
                x, y = seg[1], seg[2]
                pt = ((x - xmin_s) * scale, (ymax_s - y) * scale)
                pen.moveTo(pt)
                first = False
            elif seg[0] == "L":
                x, y = seg[1], seg[2]
                pen.lineTo(((x - xmin_s) * scale, (ymax_s - y) * scale))
            else:
                _, x1, y1, x2, y2, x, y = seg
                pen.curveTo(
                    ((x1 - xmin_s) * scale, (ymax_s - y1) * scale),
                    ((x2 - xmin_s) * scale, (ymax_s - y2) * scale),
                    ((x - xmin_s) * scale, (ymax_s - y) * scale),
                )
        pen.closePath()

    glyph.width = sw + int(EM * 0.04)
    glyph.correctDirection()

    font.generate(str(OUT))
    print(f"wrote {OUT.name}: {OUT.stat().st_size} bytes, U+{CODEPOINT:04X}, "
          f"advance={int(glyph.width)}, {len(contours)} contours")
    return 0


if __name__ == "__main__":
    sys.exit(build())
