#!/usr/bin/env bash
#
# Install the DeepSeek rate whale into Waybar on this machine.
#
# Idempotent and re-runnable: symlinks the resources and patches the config in
# place, so edits here take effect immediately (nothing is copied).
#
#   ./install.sh            install / update
#   ./install.sh uninstall  remove the module, symlinks and font

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RES="$HERE/resources"
LIB="$HERE/lib"
FONT_SRC="$RES/DeepSeekWhale.ttf"
FONT_NAME="DeepSeekWhale.ttf"

WB="$HOME/.config/waybar"
WB_SCRIPTS="$WB/scripts"
WB_FONTS="$HOME/.local/share/fonts"
WAYBAR_LOG="${XDG_RUNTIME_DIR:-/tmp}/deepseek-waybar.log"

say() { printf '  %s\n' "$*"; }

# ------------------------------------------------------------------ uninstall
uninstall() {
  echo "Removing the DeepSeek whale module"
  rm -f "$WB_SCRIPTS/deepseek-price" "$WB_FONTS/$FONT_NAME"
  python3 - "$WB" <<'PY'
import pathlib, re, sys
wb = pathlib.Path(sys.argv[1])
cfg = wb / "config.jsonc"
if cfg.exists():
    t = cfg.read_text()
    t = t.replace('    "custom/deepseek",\n', '')
    t = re.sub(r'  "custom/deepseek": \{.*?\n  \},\n', '', t, flags=re.S)
    cfg.write_text(t)
css = wb / "style.css"
if css.exists():
    t = css.read_text()
    t = re.sub(r'\n/\* DeepSeek mark:.*?\*/\n', '\n', t, flags=re.S)
    t = re.sub(r'#custom-deepseek[^\{]*\{[^}]*\}\n?', '', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    css.write_text(t.rstrip() + "\n")
PY
  fc-cache -f "$WB_FONTS" >/dev/null 2>&1 || true
  pkill -x waybar 2>/dev/null || true
  sleep 1
  setsid waybar >"$WAYBAR_LOG" 2>&1 &
  say "removed; Waybar restarted"
}

if [[ "${1:-install}" == "uninstall" ]]; then
  uninstall
  exit 0
fi

echo "Installing the DeepSeek rate whale"

# 1. preflight --------------------------------------------------------------
[[ -f "$FONT_SRC" ]] || { echo "ERROR: missing $FONT_SRC (run 'make font')"; exit 1; }
[[ -f "$RES/deepseek-price" ]] || { echo "ERROR: missing $RES/deepseek-price"; exit 1; }
[[ -d "$WB" ]] || { echo "ERROR: $WB not found - is this an Omarchy/Waybar machine?"; exit 1; }
command -v waybar >/dev/null || { echo "ERROR: waybar not installed"; exit 1; }

# 2. resources: symlinked, so this repo stays the source of truth -------------
mkdir -p "$WB_SCRIPTS" "$WB_FONTS"
ln -sfn "$RES/deepseek-price" "$WB_SCRIPTS/deepseek-price"
ln -sfn "$FONT_SRC" "$WB_FONTS/$FONT_NAME"
chmod +x "$RES/deepseek-price"
say "linked deepseek-price and $FONT_NAME"

# 3. font cache so Pango/Waybar can resolve 'DeepSeek Whale' ----------------
fc-cache -f "$WB_FONTS" >/dev/null 2>&1 || true
if fc-list | grep -qi "DeepSeek Whale"; then
  say "font registered"
else
  echo "ERROR: font did not register with fontconfig"; exit 1
fi

# 4. waybar config + style ---------------------------------------------------
python3 "$LIB/patch-waybar.py"

# 5. make sure our glyph actually resolves (silent fallback would show a box) -
CH="$(python3 -c 'print(chr(0xE900))')"
for fam in "DeepSeek Whale"; do
  bbox=$(pango-view --no-display --font="$fam 40" --text="$CH" -q -o /tmp/ds-preflight.png 2>/dev/null &&
         magick /tmp/ds-preflight.png -trim -format '%wx%h' info: 2>/dev/null || echo "")
done
rm -f /tmp/ds-preflight.png
if [[ -n "$bbox" && "${bbox%%x*}" -gt 40 ]]; then
  say "glyph resolves in Pango ($bbox)"
else
  echo "  WARNING: glyph may not resolve (bbox='${bbox:-none}') - check ~/.local/share/fonts"
fi

# 6. restart ----------------------------------------------------------------
pkill -x waybar 2>/dev/null || true
sleep 1
setsid waybar >"$WAYBAR_LOG" 2>&1 &
sleep 2
if pgrep -x waybar >/dev/null; then
  say "Waybar restarted"
else
  echo "ERROR: Waybar did not start; see $WAYBAR_LOG"; exit 1
fi

echo
echo "Done. Hover the whale for rates; click it for a notification."
echo "  state: $("$RES/deepseek-price" state)   next: $("$RES/deepseek-price" next) UTC"
