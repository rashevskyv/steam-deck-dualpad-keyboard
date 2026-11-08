// Session-only keyboard placement and application geometry restoration.
var saved = [];
var lastTarget = workspace.activeWindow;
var currentKeyboard = null;
function custom(w) { return String(w.resourceClass).indexOf('handheld-kbd') >= 0; }
function stock(w) { return /Steam Input On-screen Keyboard|Екранна клавіатура введення Steam/.test(String(w.caption)); }
function keyboard(w) { return custom(w) || stock(w); }
function heightFor(w, area) {
    return Math.min(area.height * 0.75, Math.max(80, custom(w) ? Math.round(area.height * 0.30) : w.frameGeometry.height));
}
function restore() {
    saved.forEach(function(s) {
        try { s.w.setMaximize(false, false); s.w.frameGeometry = s.rect;
              s.w.setMaximize(s.vertical, s.horizontal); } catch (e) {}
    });
    saved = [];
}
function shrink(target, w) {
    if (!target || keyboard(target) || !target.normalWindow || target.fullScreen) return;
    var area = workspace.clientArea(KWin.WorkArea, w);
    var height = heightFor(w, area);
    if (!saved.some(function(s) { return s.w === target; })) {
        var r = target.frameGeometry;
        saved.push({w:target, rect:{x:r.x,y:r.y,width:r.width,height:r.height},
            vertical:target.maximizeMode === 2 || target.maximizeMode === 3,
            horizontal:target.maximizeMode === 1 || target.maximizeMode === 3});
    }
    target.setMaximize(false, false);
    target.frameGeometry = {x:area.x,y:area.y,width:area.width,height:area.height-height};
}
function opened(w) {
    if (!keyboard(w)) return;
    if (custom(w)) workspace.windowList().forEach(function(other) {
        if (stock(other)) other.closeWindow();
    });
    currentKeyboard = w;
    if (stock(w)) callDBus('org.handheld.Keyboard','/org/handheld/Keyboard',
        'org.handheld.Keyboard','StockVisible',true);
    var area = workspace.clientArea(KWin.WorkArea, w);
    var height = heightFor(w, area);
    w.keepAbove = true;
    var g = w.frameGeometry;
    w.frameGeometry = {x:custom(w) ? area.x : g.x,y:area.y+area.height-height,
        width:custom(w) ? area.width : g.width,height:height};
    shrink(lastTarget, w);
}
workspace.windowActivated.connect(function(w) {
    if (w && !keyboard(w) && w.normalWindow) {
        lastTarget = w;
        if (currentKeyboard) shrink(w,currentKeyboard);
    }
});
function watch(w) {
    if (w.captionChanged) w.captionChanged.connect(function() { if (keyboard(w)) opened(w); });
    if (w.windowShown) w.windowShown.connect(function() { if (keyboard(w)) opened(w); });
    if (w.windowHidden) w.windowHidden.connect(function() {
        if (stock(w)) callDBus('org.handheld.Keyboard','/org/handheld/Keyboard',
            'org.handheld.Keyboard','StockVisible',false);
        if (w === currentKeyboard) { currentKeyboard = null; restore(); }
    });
    if (w.frameGeometryChanged) w.frameGeometryChanged.connect(function() {
        if (w === currentKeyboard && stock(w)) shrink(lastTarget,w);
    });
    opened(w);
}
workspace.windowAdded.connect(watch);
workspace.windowRemoved.connect(function(w) {
    if (stock(w)) callDBus('org.handheld.Keyboard','/org/handheld/Keyboard',
            'org.handheld.Keyboard','StockVisible',false);
        if (w === currentKeyboard) { currentKeyboard = null; restore(); }
    if (w === lastTarget) lastTarget = null;
});
workspace.windowList().forEach(function(w) { if (!w.minimized) watch(w); });
