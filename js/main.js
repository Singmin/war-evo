'use strict';
// 主循环：渲染一帧 = 战场 + HUD
function render() {
  ctx.setTransform(scale * dpr, 0, 0, scale * dpr, 0, 0);
  if (!G) { demoRender(); return; }   // 开始页：背后是 AI 对 AI 的演示局（js/ui/attract.js）
  let shx = 0, shy = 0;
  if (G.shake > 0) { shx = rand(-4, 4); shy = rand(-3, 3); }
  ctx.translate(shx, shy);
  drawWorld();
  if (G.specialView) { ctx.fillStyle = 'rgba(0,0,0,.12)'; ctx.fillRect(0, 0, W, H); }
  ctx.setTransform(scale * dpr, 0, 0, scale * dpr, 0, 0);
  drawHUD();
}

/** 画战场（背景、基地、兵、弹道、特效），不含 HUD；正式对局和开始页演示局共用 */
function drawWorld() {
  drawBackground(G.sides[0].era);
  for (const sd of G.sides) drawBase(sd);
  drawScorch();
  for (const u of G.units) drawUnit(u);
  drawProjs();
  drawFx();
}

// =====================================================================
// 主循环
// =====================================================================
let lastT = performance.now(), acc = 0, menuTick = 0;
function frame(now) {
  // 任何一帧出错都不能让主循环断掉（否则画面永久冻结），错误显示在屏幕上（js/boot.js）
  requestAnimationFrame(frame);
  try { frameBody(now); } catch (e) {
    lastT = now;
    if (typeof bootReport === 'function') bootReport(e && e.message || e, e && e.stack ? String(e.stack).split(String.fromCharCode(10))[1] : '');
  }
}
function frameBody(now) {
  guideTick(now);   // 新手指引的光圈和气泡（js/ui/guide.js）；离开对局画面时它自己收起
  // 正在播激励视频：不模拟也不重画（画布保留最后一帧），减少内存/GPU 压力，避免低端机被系统杀掉
  if (S.screen === 'ad') { lastT = now; return; }
  updateSkin();   // 我方升级时代 → 顶栏、底栏换材质
  const rdt = Math.min(0.1, (now - lastT) / 1000); lastT = now;
  if (G && S.screen === 'play') {
    updateAdBtns();
    // 实时计时的东西（不受游戏速度影响）
    if (G.toast) { G.toast.t -= rdt; if (G.toast.t <= 0) G.toast = null; }
    if (G.echo) { G.echo.t -= rdt; if (G.echo.t <= 0) G.echo = null; }
    if (G.castFx) { G.castFx.t -= rdt; if (G.castFx.t <= 0) G.castFx = null; }
    G.shake = Math.max(0, G.shake - rdt);
    errT = Math.max(0, errT - rdt); towerKeyT = Math.max(0, towerKeyT - rdt);
    const pan = (keys.has('d') ? 1 : 0) - (keys.has('a') ? 1 : 0);
    if (pan) { G.camX += pan * 900 * rdt / G.zoom; clampCam(); }
    if (G.specialView) {
      G.specialView.t -= rdt;
      if (G.specialView.t <= 0) { G.zoom = G.specialView.zoom; G.camX = G.specialView.camX; G.specialView = null; clampCam(); }
    }
    if (G.freeze > 0) G.freeze -= rdt;
    else {
      acc += rdt * S.speed;
      let n = 0;
      while (acc >= STEP && n < 12) { step(STEP); acc -= STEP; n++; }
      if (n >= 12) acc = 0;
    }
    if (G.over) { G.overT -= rdt; if (G.overT <= 0) showResult(); }
    menuTick -= rdt;
    if (menuTick <= 0) { menuTick = 0.1; refreshMenu(); }
  } else if (!G) demoTick(rdt);
  render();
}
show('menu');
requestAnimationFrame(frame);
