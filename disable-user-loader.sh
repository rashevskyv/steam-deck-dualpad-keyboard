#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
RUNTIME="$ROOT/millennium-runtime"
STEAM_DIR="$HOME/.local/share/Steam"
for pair in 'ubuntu12_32/libXtst.so.6:libmillennium_bootstrap_x86.so' 'ubuntu12_64/libXtst.so.6:libmillennium_bootstrap_hhx64.so' 'ubuntu12_64/libmillennium_hhx64.so:libmillennium_hhx64.so'; do
 path="$STEAM_DIR/${pair%%:*}"
 expected="$RUNTIME/${pair#*:}"
 if [ -L "$path" ] && [ "$(readlink "$path")" = "$expected" ]; then rm "$path"; fi
done
CONF="$HOME/.config/environment.d/90-steam-native-keyboard.conf"
if [ -f "$CONF" ] && [ "$(cat "$CONF")" = "MILLENNIUM_RUNTIME_PATH=$RUNTIME/libmillennium_x86.so" ]; then rm "$CONF"; fi
systemctl --user unset-environment MILLENNIUM_RUNTIME_PATH
echo 'Millennium preload disabled. Restart Steam to return to the original interface.'
