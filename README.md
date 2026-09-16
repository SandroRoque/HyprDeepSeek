# HyprDeepSeek

A small collection of Hyprland and Waybar customizations, led by a live
DeepSeek API pricing indicator for Waybar.

## DeepSeek rate whale

The whale gives you the current DeepSeek pricing window at a glance:

- **Green** — off-peak pricing (50% discount)
- **Red** — peak pricing
- **Hover** — current rates, the next price change, and a local-time countdown
- **Click** — show the same information in a desktop notification

DeepSeek's peak windows are Monday–Friday, **01:00–04:00 UTC** and
**06:00–10:00 UTC**. The tooltip converts those windows and the next change to
your local time automatically.

### Install

On an Omarchy or Arch system with Waybar:

```sh
git clone https://github.com/SandroRoque/HyprDeepSeek.git
cd HyprDeepSeek/deepseek
./install.sh
```

The installer links the script and bundled whale font into your user
directories, updates your existing Waybar config and stylesheet, refreshes the
font cache, verifies that Pango can render the glyph, and restarts Waybar. It
does not need `sudo` or install anything system-wide.

Requirements: `bash`, `jq`, `python3`, `fontconfig`, and Waybar. `pango-view`
and ImageMagick enable the installer's extra glyph-rendering check. A default
Omarchy installation already includes them.

### Manage the installation

Run these commands from `HyprDeepSeek/deepseek`:

```sh
./install.sh status       # show the active script, font, and pricing state
./install.sh              # install, update, or repair the integration
./install.sh --force      # switch an install from a different checkout
./install.sh uninstall    # remove the module, styles, script, and font
```

The install is idempotent, so it is safe to rerun after `git pull`. Resources
are symlinked to the checkout, making local changes immediately available. To
avoid silently hijacking a working setup, another clone must use `--force`.

### Customize it

| Change | Location |
|---|---|
| Peak and off-peak colors | `~/.config/waybar/style.css` |
| Glyph size and spacing | `#custom-deepseek` in the same stylesheet |
| Refresh interval | `custom/deepseek` in `~/.config/waybar/config.jsonc` |
| Pricing schedule or rates | `deepseek/resources/deepseek-price` |
| Tooltip wording | `deepseek/resources/deepseek-price` |

Re-running the installer restores the module block and its default CSS rules,
so keep durable project changes in this repository.

### Troubleshooting

Check what is installed and where each symlink points:

```sh
./install.sh status
```

If the installer stops, its error identifies the failing stage. Useful manual
checks are:

```sh
fc-list | grep -F "DeepSeek Whale"   # bundled font is registered
fc-match "DeepSeek Whale"            # Fontconfig selects the expected family
tail -n 50 "${XDG_RUNTIME_DIR:-/tmp}/deepseek-waybar.log"
```

If you moved or recloned the repository, run `./install.sh --force` so the
installed symlinks point to the new checkout.

For implementation details—including the font-based rendering approach and
repository layout—see [the DeepSeek module guide](deepseek/README.md).

## Font preview utility

`font-preview.py` renders an installed font into labeled PNG contact sheets.
Use it to find a glyph visually and copy its Unicode code point into a config:

```sh
python3 font-preview.py --list
python3 font-preview.py --font "JetBrainsMono Nerd Font" --range e000-e0ff
python3 font-preview.py --font "Font Awesome 7 Free" --range f000-f8ff --cols 10 --rows 8
```

Output goes to `~/Downloads/font-glyphs/` by default. Page filenames include
their code-point range, so repeated runs do not overwrite earlier sheets.

## Development

Run the lightweight checks before committing:

```sh
make -C deepseek check
```

The built `DeepSeekWhale.ttf` is committed, so users do not need font tooling.
Only regenerating it requires `fontforge` and `python-fonttools`:

```sh
make -C deepseek font
```

The whale began as an SVG, briefly used per-state PNG files, and now lives at
`U+E900` in a tiny custom font. That lets a standard Waybar text module tint the
mark with CSS while retaining a native JSON tooltip.
