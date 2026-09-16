# DeepSeek rate whale for Waybar

A DeepSeek mark in the Waybar bar that is **green when API rates are off-peak**
and **red during peak hours**, with a hover tooltip carrying the next change and
the current per-million-token prices.

Peak hours (from the DeepSeek docs): **Mon-Fri 01:00-04:00 and 06:00-10:00 UTC**.
Everything else is off-peak at half the rate.

The tooltip is shown entirely in the **user's local time** — no UTC. It converts
once via `date`, and says what happens rather than when a UTC boundary falls:

```
DeepSeek API - off-peak (half price)

Rates rise to full price at 03:00 America/Sao_Paulo - in 24h 46m

Rates per 1M tokens (off-peak)
  ...

Peak hours 22:00-01:00, 03:00-07:00 (UTC-03:00); weekends off-peak all day
```

` tomorrow` is appended when the change crosses local midnight. The zone name
comes from `/etc/localtime`, or `%Z` when that reports a real abbreviation.

## Install on another machine

```sh
git clone <this repo> ~/Documents/Projects/HyprDeepSeek   # or wherever
cd ~/Documents/Projects/HyprDeepSeek/deepseek
./install.sh
```

Requirements: Omarchy/Arch with Waybar, `bash`, `jq`, `python3` and `fontconfig`
— all present on a default Omarchy install. No `sudo`, nothing system-wide: the
font goes to `~/.local/share/fonts` and the config to `~/.config/waybar`.

`fontforge` + `python-fonttools` are needed **only** to regenerate the font
(`make font`); the built `DeepSeekWhale.ttf` is committed, so a plain install
never needs them.

`install.sh` is **idempotent** — re-run it after any `git pull`. It symlinks the
resources into place (so this repo stays the source of truth, nothing is copied),
registers the font, patches `~/.config/waybar/config.jsonc` and `style.css` in
place, and restarts Waybar.

```sh
./install.sh            # install / update from this checkout
./install.sh status     # what is currently live, and where it points
./install.sh --force    # take over from a different checkout
./install.sh uninstall  # remove module, symlinks and font
```

Because the resources are symlinked, **a second checkout cannot silently take
over**: if an install already points at another path, `install.sh` prints both
paths and exits non-zero without changing anything. Use `--force` when you
genuinely mean to switch.

## Layout

```
deepseek/
├── install.sh              install / uninstall
├── Makefile                make install | uninstall | font | check
├── resources/              everything needed at runtime
│   ├── deepseek-price      rate schedule + tooltip; emits {tooltip, class}
│   ├── DeepSeekWhale.ttf   the mark as one glyph, U+E900
│   └── whale.path          source SVG path data
└── lib/
    ├── build-font.py       whale.path -> DeepSeekWhale.ttf (fontforge)
    └── patch-waybar.py     idempotent config.jsonc / style.css patcher
```

`resources/` is the payload; `lib/` is only needed to rebuild it.

## How it works

The state machine is two CSS rules:

```css
#custom-deepseek       { color: #8fd97a; }   /* off-peak */
#custom-deepseek.peak  { color: #e2685f; }   /* peak */
```

`deepseek-price` reports the state and the hover text:

```json
{"tooltip": "…", "class": "peak"}
```

Waybar renders the glyph from the module's `format` (`\ue900`), tints it from
`class`, and shows `tooltip` on hover. No images, no per-state files.

All time arithmetic is done in **UTC minutes since Monday 00:00**, derived from
the epoch — so local time, timezone and day boundaries cannot skew it.

## Why a font

Waybar's `custom` modules are text-only, and only the text modules support a
normal JSON tooltip. Putting the mark in a font is what lets one module show it,
tint it from CSS, and still carry a tooltip. A PNG would have forced the
`image` module's `$path\n$tooltip` contract.

Rebuild the font after editing the mark:

```sh
make font        # needs: sudo pacman -S fontforge python-fonttools
```

## Adjusting

| Want | Where |
|---|---|
| different colours | `~/.config/waybar/style.css`, `#custom-deepseek` |
| glyph size / spacing | same rule, `font-size` / `margin` |
| refresh rate | `interval` in the module block (seconds) |
| rates or peak hours | `resources/deepseek-price` (`in_peak()`, the price table) |
| tooltip wording | the `TOOLTIP=` printf in `resources/deepseek-price` |
