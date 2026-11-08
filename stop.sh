#!/usr/bin/env bash
set -eu
ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
if [ -f /tmp/handheld-kbd.pid ]; then
    pid=$(cat /tmp/handheld-kbd.pid)
    python3 - "$pid" "$ROOT/handheld-kbd.py" <<'PYCODE'
import os, signal, sys
from pathlib import Path
pid, expected = sys.argv[1:]
try:
    args = Path('/proc/'+pid+'/cmdline').read_bytes().split(b'\0')
    cwd = Path('/proc/'+pid+'/cwd').resolve()
    if any((cwd / os.fsdecode(arg)).resolve() == Path(expected) for arg in args[1:] if arg):
        os.kill(int(pid), signal.SIGTERM)
except (OSError, ValueError):
    pass
PYCODE
    sleep 0.4

fi
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript deck-keyboard-trial >/dev/null 2>&1 || true
