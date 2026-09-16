# HyprDeepSeek

Waybar and Hyprland customisations.

## `deepseek/` — DeepSeek rate whale for Waybar

A DeepSeek mark in the bar that is **green when API rates are off-peak** and
**red during peak hours**, with a hover tooltip showing the next rate change and
the current per-million-token prices.

Self-contained and installable on any Omarchy/Arch machine with Waybar:

```sh
git clone <this repo> ~/Documents/Projects/HyprDeepSeek
cd ~/Documents/Projects/HyprDeepSeek/deepseek
./install.sh
```

See [`deepseek/README.md`](deepseek/README.md) for the layout, the two CSS rules
that form the state machine, and how to adjust colours, refresh rate or prices.
`./install.sh uninstall` reverses everything.

Peak hours (DeepSeek docs): Mon-Fri 01:00-04:00 and 06:00-10:00 UTC; all other
times are off-peak at half the rate.

## `font-preview.py` — glyph browser

Renders the glyphs of any installed font into labelled PNG sheets (codepoint
printed under each glyph), so a glyph can be picked by eye and pasted into a
config as `\uXXXX`:

```sh
python3 font-preview.py --list                                    # families + counts
python3 font-preview.py --font "JetBrainsMono Nerd Font" --range e000-e0ff
python3 font-preview.py --font "Font Awesome 7 Free" --range f000-f8ff --cols 10 --rows 8
```

Sheets go to `--out` (default `~/Downloads/font-glyphs/`); page names embed the
codepoint range so repeated runs never overwrite each other.

Online equivalents: [Nerd Fonts cheat sheet](https://www.nerdfonts.com/cheat-sheet),
[Font Awesome 7 Free](https://fontawesome.com/search?o=r&m=free).

### Glyph notes worth keeping

- Font Awesome 7 Free has **no whale**: `U+F48B` is a truck, and its charset
  jumps `1F409` -> `1F40E`. It covers `1F41F` fish, `1F6A2` ship.
- Noto Color Emoji has `U+1F40B` WHALE and `U+1F433` SPOUTING WHALE, but they are
  colour glyphs, so CSS `color` will not tint them.
- Nerd Fonts' whale glyph is the Docker logo, not a generic whale.

## History

The mark started as a hand-drawn SVG, moved through per-state PNGs swapped by
files, and ended as a **glyph in a font with colour coming from CSS** — which is
what lets one Waybar text module show the mark *and* carry a normal JSON tooltip.
Discarded approaches were deleted; `deepseek/lib/build-font.py` is the only
generator.
