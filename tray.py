#!/usr/bin/env python3
"""Tray launcher for Steam's native keyboard; contains no Steam client code."""
import fcntl, os, signal, subprocess, sys, time
from pathlib import Path
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, GLib, Gio

runtime=Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))
lock=open(runtime/'steam-native-keyboard-tray.lock','w')
try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError: sys.exit(0)

keyboard_state={'visible':False, 'down':False, 'first':0.0}

def show(*_):
    subprocess.Popen(['steam','-ifrunning','steam://open/keyboard'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def quit_app(*_):
    Gtk.main_quit()

# Read the right pad in parallel with Steam, without grabbing its input device.
fd = None
for device in Path('/sys/class/hidraw').glob('*'):
    try:
        info = (device/'device/uevent').read_text()
        if '000028DE:00001205' in info and '/input2' in info:
            fd = os.open('/dev/'+device.name, os.O_RDONLY|os.O_NONBLOCK)
            break
    except OSError:
        pass

def process_pad(source, condition):
    if condition & (GLib.IO_HUP | GLib.IO_ERR):
        print('Right trackpad disconnected', flush=True)
        return False
    try:
        while True:
            try: packet=os.read(fd,64)
            except BlockingIOError: break
            if len(packet)<11 or packet[:3]!=b'\x01\x00\x09': continue
            down=bool(packet[10]&4)
            if down and not keyboard_state['down'] and not keyboard_state['visible']:
                now=time.monotonic()
                elapsed=now-keyboard_state['first']
                if 0.07 <= elapsed <= 0.50:
                    keyboard_state['first']=0.0
                    show()
                    print('Right-trackpad double click: opening keyboard', flush=True)
                elif elapsed > 0.07:
                    keyboard_state['first']=now
            keyboard_state['down']=down
    except OSError as ex:
        print('Right trackpad listener:',ex,flush=True)
        return False
    return True

if fd is None:
    print('Right trackpad unavailable; tray launcher remains usable',flush=True)
else:
    GLib.io_add_watch(fd, GLib.IO_IN|GLib.IO_HUP|GLib.IO_ERR, process_pad)
    print('Right-trackpad double-click listener active',flush=True)

# KWin tells us whether Steam's keyboard is open, so typing does not summon it again.
xml='''<node><interface name="org.deck.NativeKeyboard">
<method name="SetVisible"><arg type="b" direction="in"/></method>
</interface></node>'''

def acquired(connection, name, *_):
    info=Gio.DBusNodeInfo.new_for_xml(xml)
    def on_call(conn,sender,path,iface,method,params,reply):
        if method == 'SetVisible':
            keyboard_state['visible']=bool(params.unpack()[0])
            keyboard_state['first']=0.0
        reply.return_value(None)
    connection.register_object('/org/deck/NativeKeyboard',info.interfaces[0],on_call)

owner=Gio.bus_own_name(Gio.BusType.SESSION,'org.deck.NativeKeyboard',
                       Gio.BusNameOwnerFlags.NONE,acquired,None,None)

tray=Gtk.StatusIcon.new_from_icon_name('input-keyboard')
tray.set_title('Клавіатура Steam')
tray.set_tooltip_text('Відкрити клавіатуру Steam')
tray.set_visible(True)
tray.connect('activate',show)
def menu(icon,button,stamp):
    popup=Gtk.Menu()
    for label,fn in [('Відкрити клавіатуру Steam',show),('Зупинити значок',quit_app)]:
        item=Gtk.MenuItem(label=label)
        item.connect('activate',fn)
        popup.append(item)
    popup.show_all()
    popup.popup(None,None,Gtk.StatusIcon.position_menu,icon,button,stamp)
    tray._menu=popup
tray.connect('popup-menu',menu)
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda *_:(Gtk.main_quit(),False)[1],None)
Gtk.main()
