#!/usr/bin/env bash
set -eu
ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
setsid -f python3 "$ROOT/tray.py" >>"$ROOT/tray.log" 2>&1 </dev/null
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if qdbus6 org.deck.NativeKeyboard /org/deck/NativeKeyboard >/dev/null 2>&1; then break; fi
  sleep 0.1
done
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript deck-native-keyboard >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$ROOT/window.js" deck-native-keyboard >/dev/null
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.start >/dev/null
