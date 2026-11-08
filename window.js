// Session-only KWin companion for Steam's standalone keyboard.
var keyboard = null;
var currentTarget = workspace.activeWindow;
var saved = [];
var adjusting = false;
function isKeyboard(w) {
  return String(w.resourceClass).toLowerCase().indexOf('steam') >= 0 &&
    /Steam Input On-screen Keyboard|Екранна клавіатура введення Steam/i.test(String(w.caption));
}
function restore() {
  saved.forEach(function (s) {
    try {
      s.w.setMaximize(false, false);
      s.w.frameGeometry = s.rect;
      if (s.maximize) s.w.setMaximize(true, true);
    } catch (_) {}
  });
  saved = [];
}
function fitApplication(w) {
  if (!keyboard || !w || isKeyboard(w) || !w.normalWindow || w.fullScreen) return;
  var a = workspace.clientArea(KWin.WorkArea, keyboard);
  var kg = keyboard.frameGeometry;
  var bottom = Math.max(a.y, Math.min(a.y+a.height, kg.y));
  if (!saved.some(function (item) { return item.w === w; })) {
    var g = w.frameGeometry;
    saved.push({w:w,rect:{x:g.x,y:g.y,width:g.width,height:g.height},maximize:w.maximizeMode === 3});
  }
  w.setMaximize(false, false);
  w.frameGeometry = {x:a.x,y:a.y,width:a.width,height:Math.max(100,bottom-a.y)};
}
function show(w) {
  if (!isKeyboard(w) || adjusting) return;
  keyboard = w;
  callDBus('org.deck.NativeKeyboard','/org/deck/NativeKeyboard','org.deck.NativeKeyboard','SetVisible',true);
  var a = workspace.clientArea(KWin.WorkArea, w);
  var h = Math.min(a.height, w.frameGeometry.height);
  adjusting = true;
  w.keepAbove = true;
  w.frameGeometry = {x:a.x,y:a.y+a.height-h,width:a.width,height:w.frameGeometry.height};
  adjusting = false;
  fitApplication(currentTarget);
}
function watch(w) {
  if (w.captionChanged) w.captionChanged.connect(function () { if (isKeyboard(w)) show(w); });
  if (w.windowShown) w.windowShown.connect(function () { if (isKeyboard(w)) show(w); });
  if (w.windowHidden) w.windowHidden.connect(function () { if (w === keyboard) { keyboard=null;callDBus('org.deck.NativeKeyboard','/org/deck/NativeKeyboard','org.deck.NativeKeyboard','SetVisible',false);restore(); } });
  if (w.frameGeometryChanged) w.frameGeometryChanged.connect(function () {
    if (!adjusting && w === keyboard) fitApplication(currentTarget);
  });
  if (isKeyboard(w)) show(w);
}
workspace.windowAdded.connect(watch);
workspace.windowRemoved.connect(function(w) { if (w === keyboard) { keyboard=null;callDBus('org.deck.NativeKeyboard','/org/deck/NativeKeyboard','org.deck.NativeKeyboard','SetVisible',false);restore(); } });
workspace.windowActivated.connect(function(w) {
  if (w && w.normalWindow && !isKeyboard(w)) { currentTarget=w; if (keyboard) fitApplication(w); }
});
workspace.windowList().forEach(watch);
