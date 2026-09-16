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

FORCE=0
CMD=install
for arg in "$@"; do
  case "$arg" in
    uninstall|status|install) CMD="$arg" ;;
    --force|-f)               FORCE=1 ;;
    *) echo "Usage: $(basename "$0") [install|uninstall|status] [--force]" >&2; exit 2 ;;
  esac
done

[[ "$CMD" == "uninstall" ]] && { uninstall; exit 0; }

# where is this install currently pointing, if anywhere?
current_target() {  # $1 = symlink path
  [[ -L "$1" ]] || return 1
  readlink -f "$1" 2>/dev/null || return 1
}

status() {
  echo "DeepSeek rate whale"
  for pair in "$WB_SCRIPTS/deepseek-price|script" "$WB_FONTS/$FONT_NAME|font"; do
    link="${pair%%|*}"; what="${pair##*|}"
    if [[ -L "$link" ]]; then
      printf '  %-7s -> %s\n' "$what" "$(readlink -f "$link")"
    elif [[ -e "$link" ]]; then
      printf '  %-7s present but NOT a symlink (%s)\n' "$what" "$link"
    else
      printf '  %-7s not installed\n' "$what"
    fi
  done
  [[ -e "$WB_SCRIPTS/deepseek-price" ]] && printf '  state   %s, next %s UTC\n' \
    "$("$WB_SCRIPTS/deepseek-price" state 2>/dev/null || echo '?')" \
    "$("$WB_SCRIPTS/deepseek-price" next 2>/dev/null || echo '?')"
}

[[ "$CMD" == "status" ]] && { status; exit 0; }

echo "Installing the DeepSeek rate whale"

# 0. refuse to hijack an install that points at a different checkout ----------
# Keeps the repo relocatable (any path works) without letting a second clone
# silently take over from a working one.
conflict=""
for pair in "$WB_SCRIPTS/deepseek-price|$RES/deepseek-price" \
            "$WB_FONTS/$FONT_NAME|$FONT_SRC"; do
  link="${pair%%|*}"; want="${pair##*|}"
  [[ "$want" == "$(readlink -f "$link" 2>/dev/null)" ]] && continue
  if [[ -e "$link" || -L "$link" ]]; then
    conflict+="    $(basename "$link")"$'\n'
    conflict+="      installed: $(readlink -f "$link" 2>/dev/null || echo "$link (not a symlink)")"$'\n'
    conflict+="      this repo: $want"$'\n'
  fi
done
if [[ -n "$conflict" && "$FORCE" -eq 0 ]]; then
  cat >&2 <<EOF
ERROR: an install already exists and points elsewhere:

$conflict
Refusing to take over silently. Either:
  - run the installer from the checkout you want live (that path is listed above), or
  - re-run with --force to replace it with this repository.

Nothing was changed.
EOF
  exit 1
fi

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
