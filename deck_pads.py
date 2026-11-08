"""Passive Steam Deck HID reader. No controller feature reports or remapping.

Offsets follow Linux drivers/hid/hid-steam.c, steam_do_deck_input_event.
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import GdkX11
import ctypes
import os
from pathlib import Path
import struct
import time
from gi.repository import GLib, Gtk, Gdk
from evdev import InputDevice, list_devices, ecodes


def decode(data):
    if len(data) < 60 or data[:3] != b'\x01\x00\x09':
        return None
    xy = struct.unpack_from('<hhhh', data, 16)
    return [(bool(data[10] & touch), bool(data[10] & press or data[8] & trigger),
             xy[i*2], xy[i*2+1])
            for i, (touch, press, trigger) in enumerate(((8, 2, 2), (16, 4, 1)))]


class DeckPads:
    def __init__(self, window):
        self.w = window
        self.fd = None
        self.mouse_devices = []
        self.selected = [None, None]
        self.down = [False, False]
        self.grabbed = False
        self.stats = dict(reports=0, touches=[False, False], grabbed=False, error="")
        self.x = ctypes.CDLL('libX11.so.6')
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.display = self.x.XOpenDisplay(None)
        self.fixes = ctypes.CDLL('libXfixes.so.3')
        self.fixes.XFixesHideCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.fixes.XFixesShowCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.cursor_window = None
        self.last_touch = 0
        self.hidden_press = False
        self.x.XGrabPointer.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int,
            ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_ulong,
            ctypes.c_ulong, ctypes.c_ulong]
        self.x.XUngrabPointer.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x.XFlush.argtypes = [ctypes.c_void_p]
        self.x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        self.x.XDefaultRootWindow.restype = ctypes.c_ulong
        for p in Path('/sys/class/hidraw').glob('*'):
            info = (p / 'device/uevent').read_text()
            if '000028DE:00001205' in info and '/input2' in info:
                self.fd = os.open('/dev/' + p.name, os.O_RDONLY | os.O_NONBLOCK)
                break
        if self.fd is None:
            raise RuntimeError('Steam Deck trackpad HID not found')
        css = Gtk.CssProvider()
        css.load_from_data(b'button.pad-left {border:3px solid #48d9ff; background:#164758;} '
                          b'button.pad-right {border:3px solid #ffbf58; background:#59401b;}')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, 900)
        window.connect('show', lambda *_: self.grab_mouse())
        window.connect('hide', lambda *_: (self.release(), self.ungrab_mouse()))
        GLib.timeout_add(8, self.poll)

    def grab_mouse(self):
        if self.mouse_devices:
            return
        for path in list_devices():
            dev = InputDevice(path)
            caps = dev.capabilities()
            if dev.name == 'Valve Software Steam Controller' and ecodes.EV_REL in caps:
                try:
                    dev.grab()
                    self.mouse_devices.append(dev)
                except OSError as ex:
                    self.stats['mouse_grab_error'] = str(ex)
                    dev.close()
            else:
                dev.close()
        self.stats['mouse_devices_grabbed'] = len(self.mouse_devices)

    def ungrab_mouse(self):
        for dev in self.mouse_devices:
            try:
                dev.ungrab()
                dev.close()
            except OSError:
                pass
        self.mouse_devices = []
        self.stats['mouse_devices_grabbed'] = 0

    def release(self):
        if self.grabbed:
            if self.cursor_window:
                self.fixes.XFixesShowCursor(self.display, self.cursor_window)
                self.cursor_window = None
            self.x.XUngrabPointer(self.display, 0)
            self.x.XFlush(self.display)
            self.grabbed = False
        self.stats["grabbed"] = False
        for i in range(2):
            self.highlight(i, None)
        self.down = [False, False]

    def highlight(self, side, button):
        cls = ('pad-left', 'pad-right')[side]
        old = self.selected[side]
        if old is not None and old != button:
            old.get_style_context().remove_class(cls)
        self.selected[side] = button
        if button is not None:
            button.get_style_context().add_class(cls)

    def target(self, side, x, y):
        grids = self.w._grids
        grid = grids[side] if self.w.split else grids[0]
        gx, gy = grid.translate_coordinates(self.w, 0, 0)
        a = grid.get_allocation()
        left = gx if self.w.split else gx + side * a.width / 2
        width = a.width if self.w.split else a.width / 2
        center = getattr(self.w, 'center_grid', None)
        if center is not None:
            cx, _ = center.translate_coordinates(self.w, 0, 0)
            ca = center.get_allocation()
            if side == 0:
                width = cx + ca.width - left
            else:
                right = left + width
                left = cx
                width = right - left
        px = left + (x + 32768) / 65535 * width
        py = (32767 - max(-32768, min(32767, y))) / 65535 * self.w.get_allocated_height()
        candidates = []
        for b in grid.get_children() + (center.get_children() if center is not None else []) + (self.w.bottom_grid.get_children() if self.w.bottom_grid is not None else []):
            if not isinstance(b, Gtk.Button):
                continue
            bx, by = b.translate_coordinates(self.w, 0, 0)
            ba = b.get_allocation()
            cx, cy = bx + ba.width / 2, by + ba.height / 2
            if not self.w.split and (cx < gx + a.width / 2) != (side == 0):
                continue
            dx = max(bx-px, 0, px-bx-ba.width)
            dy = max(by-py, 0, py-by-ba.height)
            candidates.append((dx*dx+dy*dy, abs(cx-px)+abs(cy-py), b))
        return min(candidates, key=lambda c: c[:2])[2] if candidates else None

    def poll(self):
        try:
            for dev in self.mouse_devices:
                try:
                    for _ in dev.read():
                        pass
                except BlockingIOError:
                    pass
            while True:
                try:
                    data = os.read(self.fd, 64)
                except BlockingIOError:
                    break
                if not data:
                    raise OSError('HID disconnected')
                pads = decode(data)
                if pads is None:
                    continue
                self.stats['reports'] += 1
                self.stats['touches'] = [p[0] for p in pads]
                if not self.w.get_visible():
                    pressed = pads[1][1]
                    if pressed and not self.hidden_press and hasattr(self.w, 'double_click'):
                        self.w.double_click.hardware_click()
                    self.hidden_press = pressed
                    continue
                active = any(p[0] for p in pads)
                if active:
                    self.last_touch = time.monotonic()
                if active and not self.grabbed and self.display:
                    native = self.w.get_window()
                    if native:
                        xid = native.get_xid()
                        self.grabbed = self.x.XGrabPointer(self.display, xid, 0, 0,
                                                          1, 1, xid, 0, 0) == 0
                        if self.grabbed and self.cursor_window is None:
                            self.cursor_window = self.x.XDefaultRootWindow(self.display)
                            self.fixes.XFixesHideCursor(self.display, self.cursor_window)
                        self.stats['grabbed'] = self.grabbed
                        self.x.XFlush(self.display)
                elif not active and self.grabbed and time.monotonic() - self.last_touch > 0.40:
                    self.release()
                for i, (touch, pressed, x, y) in enumerate(pads):
                    button = self.target(i, x, y) if touch else None
                    self.highlight(i, button)
                    if pressed and not self.down[i] and button is not None:
                        button.clicked()
                    self.down[i] = pressed
                    if not self.w.get_visible():
                        break
        except Exception as ex:
            self.stats['error'] = str(ex)
            print('deck-pads:', ex, flush=True)
            self.release()
            self.ungrab_mouse()
            return False
        return True
