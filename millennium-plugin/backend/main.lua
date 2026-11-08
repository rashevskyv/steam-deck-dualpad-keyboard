local millennium = require("millennium")
local patches = {
  {
    file = [[sp[.]js]],
    find = [=[RenderStandardKeyboard\(me\)\{]=],
    transforms = {{ match = [=[RenderStandardKeyboard\(me\)\{]=], replace = [=[RenderStandardKeyboard(me){/* Steam Deck keyboard layout addon. Injected by patch.py; no Steam source is redistributed. */
(function () {
  'use strict';
  if (window.__deckNativeKeyboard) return;
  console.log("[deck-native] addon loaded");
  const native = window.__deckNativeKeyboard = {
    split: (() => { try { return localStorage.getItem('deck_native_split') !== '0'; } catch (_) { return true; } })(),
    toggle: function (component) {
      this.split = !this.split;
      try { localStorage.setItem('deck_native_split', this.split ? '1' : '0'); } catch (_) {}
      const doc = component.m_keyboardDiv?.ownerDocument || document;
      doc.documentElement.dataset.deckNativeSplit = this.split ? '1' : '0';
    },
    transform: function (rows, component) {
      if (!component.props.windowInstance.IsStandaloneKeyboardWindow()) return rows;
      const doc = component.m_keyboardDiv?.ownerDocument || component.props.windowInstance.BrowserWindow?.document || document;
      this.installStyle(doc);
      doc.documentElement.dataset.deckNativeSplit = this.split ? '1' : '0';
      if (!Array.isArray(rows) || rows.length < 4) return rows;
      const out = rows.map(r => Array.isArray(r) ? r.slice() : r);
      const last = out[out.length - 1];
      if (!Array.isArray(last)) return rows;
      const find = (v, key) => Array.isArray(v) ? v.map(x => find(x, key)).find(Boolean)
        : v && typeof v === 'object' && v.key === key ? v : null;
      const language = find(last, 'SwitchKeys_Layout');
      const space = find(last, ' ');
      if (!language || !space) return rows;
      const mode = { key: 'VKDeckMode', label: '◫', type: 4, strLocDescription: 'Split / standard' };
      if (this.split) {
        const used = new Set(['SwitchKeys_Layout', ' ', 'ArrowLeft', 'ArrowUp', 'ArrowDown', 'ArrowRight']);
        out[out.length - 1] = last.filter(item => !Array.from(used).some(key => find(item, key)));
        out[0].push(language, mode);
        out[out.length - 1].push(
          {key:'ArrowLeft', label:'←', type:4}, {key:'ArrowUp', label:'↑', type:4},
          {key:'ArrowDown', label:'↓', type:4}, {key:'ArrowRight', label:'→', type:4}, space
        );
      } else {
        out[0].push(mode);
      }
      return out;
    },
    hit: function (component, x, y) {
      if (!this.split || !component.props.windowInstance.IsStandaloneKeyboardWindow()) return null;
      const root = component.m_keyboardDiv;
      if (!root) return null;
      const rect = root.getBoundingClientRect();
      const close = root.querySelector('[data-key="VKClose"], [data-key="VKDone"]');
      const cr = close && close.getBoundingClientRect();
      if (cr && x >= cr.left && x <= cr.right && y >= cr.top && y <= cr.bottom) return null;
      if (x >= rect.left && x <= rect.right && y >= rect.bottom - 34 && y <= rect.bottom)
        return root.querySelector('[data-key=" "]');
      return null;
    }
  };
  const css = [
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"]{height:200px!important;max-height:200px!important;min-height:0!important;position:relative!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [role="row"]{position:static!important;min-height:32px!important;max-height:40px!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [role="row"]>[data-key]{min-height:32px!important;max-height:40px!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [role="row"]>[data-key]>div{min-height:30px!important;max-height:38px!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key="VKDeckMode"], [data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key="SwitchKeys_Layout"]{position:absolute!important;z-index:4;top:0!important;width:10%!important;min-width:0!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key="VKDeckMode"]{left:40%!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key="SwitchKeys_Layout"]{left:50%!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key=" "]{position:absolute!important;z-index:4;bottom:0!important;left:20%!important;width:60%!important;min-width:0!important}',
    '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key="VKClose"], [data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key="VKDone"]{position:absolute!important;z-index:5;bottom:0!important;right:0!important;width:6.25%!important;min-width:0!important}',
    ...['ArrowLeft','ArrowUp','ArrowDown','ArrowRight'].map((key,i) => '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [data-key="'+key+'"]{position:absolute!important;z-index:4;bottom:34px!important;left:'+(40+i*5)+'%!important;width:5%!important;min-width:0!important}'),
    '[data-deck-native-split="0"] [role="grid"][class*="Layout_"] [data-key="VKDeckMode"]{position:absolute!important;z-index:4;top:0!important;left:45%!important;width:10%!important}'
  ];
  for (let n = 4; n <= 20; n++) {
    const row = '[data-deck-native-split="1"] [role="grid"][class*="Layout_"] [role="row"]:not(.Row_0):not(.Row_4):has(> [data-key-col="'+(n-1)+'"]):not(:has(> [data-key-col="'+n+'"]))';
    css.push(row+' > [data-key-col="'+Math.floor(n/2)+'"]{margin-left:20%!important}');
  }
  css.push('[data-deck-native-split="1"] [role="grid"][class*="Layout_"] .Row_0>[data-key-col="7"]{margin-left:20%!important}');
  native.installStyle = function(doc) {
    if (doc.getElementById('deck-native-style')) return;
    const style = doc.createElement('style');
    style.id = 'deck-native-style';
    style.textContent = css.join(' ');
    (doc.head || doc.documentElement).appendChild(style);
  };
}());
]=] }}
  },
  {
    file = [[sp[.]js]],
    find = [=[Vt\(Ie\)\.map\(\(yt,Kt\)=>this\.RenderKeyboardRow]=],
    transforms = {{ match = [=[Vt\(Ie\)\.map\(\(yt,Kt\)=>this\.RenderKeyboardRow]=], replace = [=[window.__deckNativeKeyboard.transform(Vt(Ie),this).map((yt,Kt)=>this.RenderKeyboardRow]=] }}
  },
  {
    file = [[sp[.]js]],
    find = [=[const Kt=Me\.s_keyToggleData\[et\];if\(Kt\)]=],
    transforms = {{ match = [=[const Kt=Me\.s_keyToggleData\[et\];if\(Kt\)]=], replace = [=[if(et==="VKDeckMode"){window.__deckNativeKeyboard.toggle(this);this.forceUpdate();return}const Kt=Me.s_keyToggleData[et];if(Kt)]=] }}
  },
  {
    file = [[sp[.]js]],
    find = [=[for\(const tr of nr\.document\.elementsFromPoint\(me,et\)\)]=],
    transforms = {{ match = [=[for\(const tr of nr\.document\.elementsFromPoint\(me,et\)\)]=], replace = [=[const __deckHit=window.__deckNativeKeyboard&&window.__deckNativeKeyboard.hit(this,me,et);if(__deckHit)return __deckHit;for(const tr of nr.document.elementsFromPoint(me,et))]=] }}
  },
}
return { on_load = function() millennium.ready() end, patches = patches }
