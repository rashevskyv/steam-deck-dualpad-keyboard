#!/usr/bin/env python3
"""Generate exact version-checked Millennium hook rules from our addon."""
from pathlib import Path
import re
base=Path(__file__).resolve().parent
addon=(base/'addon.js').read_text()
rules=[
 ('RenderStandardKeyboard(me){','RenderStandardKeyboard(me){'+addon),
 ('Vt(Ie).map((yt,Kt)=>this.RenderKeyboardRow','window.__deckNativeKeyboard.transform(Vt(Ie),this).map((yt,Kt)=>this.RenderKeyboardRow'),
 ('const Kt=Me.s_keyToggleData[et];if(Kt)','if(et==="VKDeckMode"){window.__deckNativeKeyboard.toggle(this);this.forceUpdate();return}const Kt=Me.s_keyToggleData[et];if(Kt)'),
 ('for(const tr of nr.document.elementsFromPoint(me,et))','const __deckHit=window.__deckNativeKeyboard&&window.__deckNativeKeyboard.hit(this,me,et);if(__deckHit)return __deckHit;for(const tr of nr.document.elementsFromPoint(me,et))')]
source=(Path.home()/'.local/share/Steam/steamui/sp.js').read_text()
lines=['local millennium = require("millennium")','local patches = {']
for old,new in rules:
 if source.count(old)!=1: raise SystemExit('Unsupported Steam bundle: '+old)
 if ']=]' in new: raise SystemExit('Invalid Lua delimiter')
 pattern=re.escape(old).replace('\\ ', ' ')
 lines+=['  {','    file = [[sp[.]js]],','    find = [=['+pattern+']=],','    transforms = {{ match = [=['+pattern+']=], replace = [=['+new+']=] }}','  },']
lines+=['}','return { on_load = function() millennium.ready() end, patches = patches }','']
(base/'millennium-plugin/backend/main.lua').write_text('\n'.join(lines))
print('All four Steam hooks match exactly once.')
