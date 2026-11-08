#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
RUNTIME="$ROOT/millennium-runtime"
STEAM_DIR="$HOME/.local/share/Steam"
PLUGIN_DIR="$HOME/.local/share/millennium/plugins"
CONFIG_DIR="$HOME/.config/millennium"
ENV_DIR="$HOME/.config/environment.d"
[ -f "$RUNTIME/libmillennium_x86.so" ] || { echo 'Millennium runtime missing' >&2; exit 1; }
chmod u+x "$RUNTIME/libmillennium_pvs64" "$RUNTIME/libmillennium_luavm_x86"
[ -f "$ROOT/ua.deck.native-split-keyboard.star" ] || { echo 'Plugin package missing' >&2; exit 1; }
if [ -e "$CONFIG_DIR/config.json" ]; then
 python3 - "$CONFIG_DIR/config.json" <<'PYCODE'
import json,sys
p=sys.argv[1]
c=json.load(open(p))
assert c.get('plugins',{}).get('enabledPlugins') == ['ua.deck.native-split-keyboard'], 'Existing Millennium configuration differs'
PYCODE
fi
[ ! -e "$ENV_DIR/90-steam-native-keyboard.conf" ] || { echo 'Environment file already exists; leaving untouched' >&2; exit 1; }
for target in "$STEAM_DIR/ubuntu12_32/libXtst.so.6" "$STEAM_DIR/ubuntu12_64/libXtst.so.6" "$STEAM_DIR/ubuntu12_64/libmillennium_hhx64.so"; do
 [ ! -e "$target" ] && [ ! -L "$target" ] || { echo "Existing Steam library: $target" >&2; exit 1; }
done
mkdir -p "$PLUGIN_DIR" "$CONFIG_DIR" "$ENV_DIR"
install -m 644 "$ROOT/ua.deck.native-split-keyboard.star" "$PLUGIN_DIR/ua.deck.native-split-keyboard.star"
if [ ! -e "$CONFIG_DIR/config.json" ]; then printf '%s\n' '{"plugins":{"enabledPlugins":["ua.deck.native-split-keyboard"]}}' > "$CONFIG_DIR/config.json"; fi
printf 'MILLENNIUM_RUNTIME_PATH=%s/libmillennium_x86.so\n' "$RUNTIME" > "$ENV_DIR/90-steam-native-keyboard.conf"
ln -s "$RUNTIME/libmillennium_bootstrap_x86.so" "$STEAM_DIR/ubuntu12_32/libXtst.so.6"
ln -s "$RUNTIME/libmillennium_bootstrap_hhx64.so" "$STEAM_DIR/ubuntu12_64/libXtst.so.6"
ln -s "$RUNTIME/libmillennium_hhx64.so" "$STEAM_DIR/ubuntu12_64/libmillennium_hhx64.so"
systemctl --user set-environment "MILLENNIUM_RUNTIME_PATH=$RUNTIME/libmillennium_x86.so"
echo 'User-scoped Millennium and native keyboard plugin installed.'
