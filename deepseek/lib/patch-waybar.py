#!/usr/bin/env python3
"""Patch ~/.config/waybar/{config.jsonc,style.css} for the DeepSeek module.

Idempotent: re-running updates the values rather than appending duplicates.
The JSONC is edited textually so the user's comments and formatting survive.
"""

import pathlib
import re
import sys

MODULE = "custom/deepseek"
EXEC = "~/.config/waybar/scripts/deepseek-price json"
NOTIFY = "~/.config/waybar/scripts/deepseek-price notify"
GLYPH = "\\ue900"          # U+E900 in the DeepSeek Whale font
ANCHOR = '"bluetooth",'    # module is inserted right after this

BLOCK = f'''  "{MODULE}": {{
    "exec": "{EXEC}",
    "return-type": "json",
    "interval": 60,
    "tooltip": true,
    "format": "{GLYPH}",
    "on-click": "{NOTIFY}"
  }},'''

CSS = """
/* DeepSeek mark: one font glyph; the colour IS the state machine. */
#custom-deepseek {
  font-family: 'DeepSeek Whale';
  font-size: 15px;
  margin: 0 10px 0 6px;
  color: #8fd97a;              /* off-peak */
}

#custom-deepseek.peak {
  color: #e2685f;              /* peak */
}
"""


def patch_config(path: pathlib.Path) -> list[str]:
    text = path.read_text()
    notes = []

    if f'"{MODULE}"' not in text:
        if ANCHOR not in text:
            return [f"ERROR: could not find {ANCHOR} in {path}"]
        text = text.replace(ANCHOR, ANCHOR + f'\n    "{MODULE}",', 1)
        notes.append("registered module in modules-right")
    else:
        notes.append("module already registered")

    existing = re.search(rf'  "{re.escape(MODULE)}": \{{.*?\n  \}},', text, re.S)
    if existing:
        text = text[:existing.start()] + BLOCK + text[existing.end():]
        notes.append("refreshed module block")
    else:
        # insert after the bluetooth block, which we know exists
        m = re.search(r'  "bluetooth": \{.*?\n  \},\n', text, re.S)
        if not m:
            return notes + [f"ERROR: no bluetooth block to anchor to in {path}"]
        text = text[:m.end()] + BLOCK + "\n" + text[m.end():]
        notes.append("inserted module block")

    path.write_text(text)
    return notes


def patch_style(path: pathlib.Path) -> list[str]:
    text = path.read_text()
    notes = []

    # Drop every block for this selector first, so stale rules from earlier
    # designs (.lvl-N, .active, ...) cannot survive a re-install. Then re-add
    # the current two rules.
    base = re.sub(r'#custom-deepseek[^\{]*\{[^}]*\}\n?', '', text)
    base = re.sub(r'\n{3,}', '\n\n', base)
    if base != text:
        text = base
        notes.append("removed stale #custom-deepseek rules")
    text = text.rstrip() + "\n" + CSS
    notes.append("applied CSS rules")

    path.write_text(text)
    return notes


def main() -> int:
    home = pathlib.Path.home()
    cfg = home / ".config/waybar/config.jsonc"
    css = home / ".config/waybar/style.css"
    for f in (cfg, css):
        if not f.exists():
            print(f"ERROR: {f} not found", file=sys.stderr)
            return 1
    for note in patch_config(cfg):
        print(f"  config: {note}")
    for note in patch_style(css):
        print(f"  style:  {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
