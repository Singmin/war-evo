'use strict';
// 画面：画布缩放和镜头
// =====================================================================
// 画面与输入
// =====================================================================
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const gameEl = document.getElementById('game');
let scale = 1, dpr = 1, adInsetTop = 0, adInsetBottom = 0;
function setGameAdInsets(top, bottom) {
  if (top === adInsetTop && bottom === adInsetBottom) return;
  adInsetTop = top; adInsetBottom = bottom;
  layout();
}
function layout() {
  const vw = window.innerWidth, vh = window.innerHeight;
  document.getElementById('rotate').style.display = vh > vw ? 'flex' : 'none';
  const topInset = vh > vw ? 0 : adInsetTop;
  const usableHeight = Math.max(1, vh - (vh > vw ? 0 : adInsetTop + adInsetBottom));
  scale = Math.min(vw / W, usableHeight / H);
  const left = (vw - W * scale) / 2, top = topInset + (usableHeight - H * scale) / 2;
  gameEl.style.transform = `translate(${left}px,${top}px) scale(${scale})`;
  dpr = Math.min(2, window.devicePixelRatio || 1);
  const width = Math.round(W * scale * dpr), height = Math.round(H * scale * dpr);
  if (cv.width !== width) cv.width = width;
  if (cv.height !== height) cv.height = height;
}
window.addEventListener('resize', layout);
window.addEventListener('orientationchange', () => setTimeout(layout, 200));
layout();

// ---------- 镜头 ----------
function clampCam() {
  if (!G) return;
  G.zoom = clamp(G.zoom, MIN_ZOOM, 1);
  G.camX = clamp(G.camX, 0, WORLD - W / G.zoom);
}
function zoomAt(z, px) {
  const wx = G.camX + px / G.zoom;
  G.zoom = clamp(z, MIN_ZOOM, 1);
  G.camX = wx - px / G.zoom;
  clampCam();
}
const sx = wx => (wx - G.camX) * G.zoom;
const sy = wy => GROUND_Y + wy * G.zoom;
