'use strict';
// 输入：拖动、缩放、小地图、键盘
// =====================================================================
// 输入：拖动、缩放、小地图、键盘
// =====================================================================
const ptrs = new Map();
let dragMoved = false, pinchD = 0, miniDrag = false;
function toLogical(e) { const r = gameEl.getBoundingClientRect(); return { x: (e.clientX - r.left) / scale, y: (e.clientY - r.top) / scale }; }
function inMinimap(p) { const m = miniRect(); return p.x >= m.x - 4 && p.x <= m.x + m.w + 4 && p.y >= m.y - 4 && p.y <= m.y + m.h + 4; }
function miniJump(p) { const m = miniRect(); G.camX = (p.x - m.x) / m.w * WORLD - (W / G.zoom) / 2; clampCam(); }
cv.addEventListener('pointerdown', e => {
  if (S.screen !== 'play') return;
  cv.setPointerCapture(e.pointerId);
  const p = toLogical(e); ptrs.set(e.pointerId, p); dragMoved = false;
  if (ptrs.size === 1 && inMinimap(p)) { miniDrag = true; miniJump(p); }
  if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinchD = Math.hypot(a.x - b.x, a.y - b.y); }
});
cv.addEventListener('pointermove', e => {
  if (!ptrs.has(e.pointerId) || !G) return;
  const p = toLogical(e), old = ptrs.get(e.pointerId);
  ptrs.set(e.pointerId, p);
  if (miniDrag) { miniJump(p); return; }
  if (ptrs.size === 1) {
    const dx = p.x - old.x;
    if (Math.abs(dx) > 0.5) dragMoved = true;
    G.camX -= dx / G.zoom; clampCam();
  } else if (ptrs.size === 2) {
    const [a, b] = [...ptrs.values()];
    const d = Math.hypot(a.x - b.x, a.y - b.y);
    if (pinchD > 0) zoomAt(G.zoom * d / pinchD, (a.x + b.x) / 2);
    pinchD = d; dragMoved = true;
  }
});
function ptrEnd(e) {
  if (!ptrs.has(e.pointerId)) return;
  ptrs.delete(e.pointerId);
  if (ptrs.size === 0) { if (!dragMoved && !miniDrag) { selectedId = null; hoverDef = null; } miniDrag = false; }
  pinchD = 0;
}
cv.addEventListener('pointerup', ptrEnd);
cv.addEventListener('pointercancel', ptrEnd);
cv.addEventListener('wheel', e => {
  if (S.screen !== 'play' || !G) return;
  e.preventDefault();
  zoomAt(G.zoom * (e.deltaY > 0 ? 0.9 : 1.1), toLogical(e).x);
}, { passive: false });

const keys = new Set();
let towerKeyT = 0;
window.addEventListener('keydown', e => {
  const k = e.key.toLowerCase();
  if (S.screen === 'tree') {
    const activatesButton = k === ' ' && e.target instanceof HTMLButtonElement;
    if (k === 'escape' || k === 'e' || (k === ' ' && !activatesButton)) {
      e.preventDefault();
      closeTree();
    }
    return;
  }
  if (k === ' ' || k === 'escape') { e.preventDefault(); if (S.screen === 'play') pause(); else if (S.screen === 'pause') resume(); return; }
  if (S.screen !== 'play' || !G) return;
  keys.add(k);
  let err = undefined;
  if (k.length === 1 && +k >= 1 && +k <= UNIT_ORDER.length) {
    const pos = +k - 1;
    if (towerKeyT > 0) { err = pos < 3 ? actBuild(me(), pos) : '防御塔只有 1 / 2 / 3'; towerKeyT = 0; } else err = actTrain(me(), UNIT_ORDER[pos]);
  } else if (k === 't') { towerKeyT = 1.5; }
  else if (k === 'b') err = actExpand(me());
  else if (k === 'g') err = actMine(me());
  else if (k === 'r') err = actDrill(me());
  else if (k === 'e') err = openTree();
  else if (k === 'q') err = actSpecial(me());
  else if (k === 'f') cycleSpeed();
  else if (k === '+' || k === '=') zoomAt(G.zoom * 1.15, W / 2);
  else if (k === '-') zoomAt(G.zoom / 1.15, W / 2);
  if (err === null) sfx('buy'); else if (err) showErr(err);
});
window.addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
window.addEventListener('blur', () => keys.clear());
