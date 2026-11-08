#!/usr/bin/env bash
set -eu
ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
[ -f "$ROOT/config/config.json" ] || cp "$ROOT/config/config.example.json" "$ROOT/config/config.json"
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript deck-keyboard-trial >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$ROOT/space.js" deck-keyboard-trial >/dev/null
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.start >/dev/null
if qdbus6 org.handheld.Keyboard /org/handheld/Keyboard org.handheld.Keyboard.Show >/dev/null 2>&1; then
    exit 0
fi
setsid -f env GDK_BACKEND=x11 HANDHELD_KBD_SHOW=1 python3 "$ROOT/handheld-kbd.py" >>"$ROOT/trial.log" 2>&1 </dev/null

