"""Optional AT-SPI double click activation, restricted to focused editable fields."""
import time
import types
import threading
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi, GLib


class FieldDoubleClick:
    def __init__(self, config, summon):
        self.config = config
        self.summon = summon
        self.focused = None
        self.last_click = None
        self.status = 'starting'
        self.stats = dict(clicks=0, focus_events=0, summons=0)
        self.listeners = []
        self.scanning = False
        try:
            Atspi.set_timeout(150, 300)
            for kind, callback in [('object:state-changed:focused', self.focus),
                                   ('mouse:button:1p', self.click)]:
                listener = Atspi.EventListener.new(callback, None)
                if not listener.register(kind):
                    raise RuntimeError('AT-SPI event registration failed: ' + kind)
                self.listeners.append(listener)
            self.status = 'listening'
            print('Double-click field listener ready (AT-SPI)', flush=True)
        except Exception as ex:
            self.status = str(ex)
            print('Double-click listener unavailable:', ex, flush=True)

    def hardware_click(self):
        from gi.repository import Gdk
        _, x, y = Gdk.Display.get_default().get_default_seat().get_pointer().get_position()
        self.click(types.SimpleNamespace(detail1=x, detail2=y))

    def focus(self, event, *_):
        self.stats["focus_events"] += 1
        self.focused = event.source if event.detail1 else None

    def click(self, event, *_):
        if not self.config.get('double_click_summon', True):
            return
        self.stats['clicks'] += 1
        now = time.monotonic()
        point = (event.detail1, event.detail2)
        previous = self.last_click
        if previous and now - previous[0] < 0.06:
            return
        self.last_click = (now, point)
        if previous is None or now - previous[0] > 0.40:
            return
        if sum((a-b)**2 for a, b in zip(point, previous[1])) > 100:
            return
        try:
            field = self.focused
            if field is None:
                if not self.scanning:
                    self.scanning = True
                    threading.Thread(target=self.find_focused, args=(point,), daemon=True).start()
                return
            states = field.get_state_set()
            if not (states.contains(Atspi.StateType.EDITABLE)
                    and states.contains(Atspi.StateType.FOCUSED)):
                return
            rect = field.get_component_iface().get_extents(Atspi.CoordType.SCREEN)
            if not (rect.x <= point[0] < rect.x + rect.width
                    and rect.y <= point[1] < rect.y + rect.height):
                return
            self.last_click = None
            self.stats["summons"] += 1
            GLib.idle_add(lambda: (self.summon(), False)[1])
        except Exception as ex:
            self.status = str(ex)

    def find_focused(self, point):
        # A field may already have focus when the keyboard daemon starts.
        deadline = time.monotonic() + 2.0
        stack = [(Atspi.get_desktop(0), 0)]
        visited = 0
        found = None
        try:
            while stack and time.monotonic() < deadline and visited < 400:
                node, depth = stack.pop()
                visited += 1
                try:
                    states = node.get_state_set()
                    if states.contains(Atspi.StateType.FOCUSED) and states.contains(Atspi.StateType.EDITABLE):
                        rect = node.get_component_iface().get_extents(Atspi.CoordType.SCREEN)
                        if rect.x <= point[0] < rect.x + rect.width and rect.y <= point[1] < rect.y + rect.height:
                            found = node
                            break
                    if depth < 14:
                        count = min(node.get_child_count(), 100)
                        for i in range(count-1, -1, -1):
                            child = node.get_child_at_index(i)
                            if child is not None:
                                stack.append((child, depth+1))
                except Exception:
                    continue
            if found is not None:
                self.focused = found
                if self.config.get("double_click_summon", True):
                    self.stats['summons'] += 1
                    GLib.idle_add(lambda: (self.summon(), False)[1])
        finally:
            self.scanning = False
