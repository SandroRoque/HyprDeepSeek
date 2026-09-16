#!/usr/bin/env python3
"""Render every glyph in a font to labeled PNG sheets, so the catalog can be
browsed visually.

Usage:
    font-preview.py --list
    font-preview.py --font "Font Awesome 7 Free" [--out DIR] [--cols N] [--rows N]
    font-preview.py --font "JetBrainsMono Nerd Font" --range f000-f0ff
    font-preview.py --all

Each sheet is a grid of glyph tiles. Every tile is labeled with its codepoint,
so a chosen glyph can be pasted straight into a Waybar config.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

DEFAULT_OUT = pathlib.Path.home() / "Downloads" / "font-glyphs"


def fc_charset(font_file: str) -> list[int]:
    """Every codepoint the font maps, via fontconfig (covers WOFF2 too)."""
    out = subprocess.run(
        ["fc-query", "-f", "%{charset}\n", font_file],
        capture_output=True, text=True, check=True,
    ).stdout
    cps: list[int] = []
    for tok in out.split():
        if "-" in tok:
            a, b = tok.split("-", 1)
            cps.extend(range(int(a, 16), int(b, 16) + 1))
        else:
            cps.append(int(tok, 16))
    return sorted(set(cps))


def fc_fonts() -> list[tuple[str, str]]:
    """Installed (family, file) pairs."""
    out = subprocess.run(
        ["fc-list", "-f", "%{family[0]}|%{file}\n"], capture_output=True, text=True, check=True
    ).stdout
    seen = {}
    for line in out.splitlines():
        if "|" not in line:
            continue
        fam, path = line.rsplit("|", 1)
        seen.setdefault(fam, path)
    return sorted(seen.items())


def glyph_ok(font: str, ch: str, tmp: pathlib.Path) -> bool:
    """Render one glyph; report whether it produced real ink."""
    r = subprocess.run(
        ["magick", "-size", "72x72", "xc:black", "-font", font, "-pointsize", "44",
         "-fill", "white", "-gravity", "center", "-annotate", "+0+0", ch, str(tmp)],
        capture_output=True,
    )
    if r.returncode != 0 or not tmp.exists():
        return False
    stat = subprocess.run(
        ["magick", str(tmp), "-format", "%[fx:mean]", "info:"],
        capture_output=True, text=True,
    ).stdout.strip()
    try:
        return float(stat) > 0.0015
    except ValueError:
        return False


def render_font(name: str, font_file: str, cps: list[int], out: pathlib.Path,
                cols: int, rows: int, per_page: int) -> int:
    """Render sheets for one font. Returns number of pages written."""
    cps = [c for c in cps if not (0xD800 <= c <= 0xDFFF)]
    pages = 0
    tmpdir = pathlib.Path(tempfile.mkdtemp())
    idx = 0
    kept: list[tuple[int, pathlib.Path]] = []

    # range prefix keeps multiple invocations from overwriting each other
    rng = f"u{min(cps):04x}-{max(cps):04x}" if cps else "empty"

    while idx < len(cps):
        # collect up to per_page glyphs that actually draw something
        while len(kept) < per_page and idx < len(cps):
            cp = cps[idx]; idx += 1
            ch = chr(cp)
            tile = tmpdir / f"g{cp:06X}.png"
            if glyph_ok(font_file, ch, tile):
                kept.append((cp, tile))
        if not kept:
            break

        cell_w = cell_h = 78
        label_h = 22
        sheets = []
        for i in range(0, len(kept), cols * rows):
            chunk = kept[i:i + cols * rows]
            tiles = []
            for cp, tile in chunk:
                lab = tmpdir / f"l{cp:06X}.png"
                subprocess.run(
                    ["magick", str(tile), "-background", "#101010", "-fill", "#7fc4ff",
                     "-pointsize", "16", "-gravity", "center", f"label:U+{cp:04X}",
                     "+swap", "-append", str(lab)],
                    check=True, capture_output=True,
                )
                tiles.append(lab)
            # pad the final row so the grid stays rectangular
            while len(tiles) % cols:
                pad = tmpdir / f"pad{len(tiles)}.png"
                subprocess.run(
                    ["magick", "-size", f"{cell_w}x{cell_h + label_h}", "xc:#101010", str(pad)],
                    check=True, capture_output=True,
                )
                tiles.append(pad)
            # build rows by hand (montage is unreliable here)
            row_imgs = []
            for r in range(0, len(tiles), cols):
                rp = tmpdir / f"row{pages}_{r}.png"
                subprocess.run(
                    ["magick", *[str(t) for t in tiles[r:r + cols]], "+append", str(rp)],
                    check=True, capture_output=True,
                )
                row_imgs.append(rp)
            page = out / f"{re.sub(r'[^A-Za-z0-9]+', '-', name).strip('-')}-{rng}-p{pages + 1:02d}.png"
            subprocess.run(
                ["magick", *[str(r) for r in row_imgs], "-append", str(page)],
                check=True, capture_output=True,
            )
            sheets.append(page)
        for p in sheets:
            print(f"  wrote {p} ({p.stat().st_size // 1024} KB)")
        pages += len(sheets)
        kept = []
    return pages


def parse_range(spec: str) -> list[int]:
    cps: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            cps.extend(range(int(a, 16), int(b, 16) + 1))
        elif part:
            cps.append(int(part, 16))
    return sorted(set(cps))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", help="font family name (substring match) or a font file path")
    ap.add_argument("--range", dest="rng", help="codepoint range, e.g. f000-f0ff or 1f400-1f4ff")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output directory")
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--list", action="store_true", help="list installed families and exit")
    args = ap.parse_args()

    fonts = fc_fonts()
    if args.list or not args.font:
        print(f"{len(fonts)} families installed:\n")
        for fam, path in fonts:
            try:
                n = len(fc_charset(path))
            except Exception:
                n = 0
            print(f"  {fam:<38} {n:>6} codepoints  {path}")
        return 0

    matches = [(f, p) for f, p in fonts if args.font.lower() in f.lower()]
    if not matches and pathlib.Path(args.font).is_file():
        matches = [(pathlib.Path(args.font).stem, args.font)]
    if not matches:
        print(f"no installed family matches {args.font!r}", file=sys.stderr)
        return 1

    out = pathlib.Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    per_page = args.cols * args.rows
    total = 0
    for fam, path in matches:
        cps = fc_charset(path)
        if args.rng:
            want = parse_range(args.rng)
            cps = [c for c in want if c in set(cps)] or want
        print(f"{fam}  ({len(cps)} codepoints)  ->  {out}")
        total += render_font(fam, path, cps, out, args.cols, args.rows, per_page)
    print(f"\n{total} sheet(s) in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
