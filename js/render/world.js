'use strict';
// 画面：战场（背景、基地、单位、弹道、特效）
// ---------- 背景：见 js/render/backdrop.js（drawBackground） ----------

// ---------- 基地 ----------
function drawBase(sd) {
  const c = SIDE_COL[sd.s], acc = AGE_COL[sd.era];
  const cx = sx(sd.s === 0 ? 80 : WORLD - 80), z = G.zoom;
  if (cx < -200 || cx > W + 200) return;
  ctx.save(); ctx.translate(cx, GROUND_Y); ctx.scale(z * (sd.s ? -1 : 1), z);
  const hit = sd.flash > 0;
  drawBaseFooting(sd);
  ctx.fillStyle = hit ? '#ff5a4a' : c.dark; ctx.strokeStyle = '#1b130c'; ctx.lineWidth = 3;
  if (!drawBaseSprite(sd)) switch (ERA_BASE_ART[sd.era]) {   // 像素画（js/render/bases.js），没有的时代用矢量画法
    case 0: // 兽皮帐篷 + 篝火
      ctx.beginPath(); ctx.moveTo(-80, 0); ctx.lineTo(-10, -140); ctx.lineTo(60, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.fillStyle = c.body; ctx.beginPath(); ctx.moveTo(-40, 0); ctx.lineTo(-10, -80); ctx.lineTo(20, 0); ctx.fill();
      ctx.fillStyle = '#ff9a2e'; ctx.beginPath(); ctx.arc(70, -8, 9 + Math.sin(performance.now() / 90) * 2, 0, 7); ctx.fill();
      break;
    case 1: // 石墙城堡
      ctx.fillRect(-80, -130, 150, 130); ctx.strokeRect(-80, -130, 150, 130);
      ctx.fillStyle = c.body; for (let i = 0; i < 5; i++) ctx.fillRect(-80 + i * 32, -148, 20, 18);
      ctx.fillStyle = '#2a1a10'; ctx.fillRect(40, -60, 30, 60);
      break;
    case 2: // 工坊 + 烟囱
      ctx.fillRect(-80, -110, 150, 110); ctx.strokeRect(-80, -110, 150, 110);
      ctx.fillRect(-60, -170, 26, 60); ctx.strokeRect(-60, -170, 26, 60);
      ctx.fillStyle = 'rgba(80,80,80,.5)'; const t = performance.now() / 600;
      for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(-47 + Math.sin(t + i) * 8, -185 - i * 18 - (t * 10 % 18), 10 + i * 3, 0, 7); ctx.fill(); }
      ctx.fillStyle = c.body; ctx.fillRect(-60, -80, 100, 16);
      ctx.fillStyle = '#2a1a10'; ctx.fillRect(40, -60, 30, 60);
      break;
    case 3: // 混凝土塔 + 天线
      ctx.fillRect(-75, -150, 140, 150); ctx.strokeRect(-75, -150, 140, 150);
      ctx.strokeStyle = acc; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-5, -150); ctx.lineTo(-5, -200); ctx.stroke();
      ctx.fillStyle = acc; ctx.beginPath(); ctx.arc(-5, -204, 6, 0, 7); ctx.fill();
      ctx.fillStyle = c.body; for (let i = 0; i < 3; i++) ctx.fillRect(-60, -130 + i * 36, 110, 12);
      ctx.fillStyle = '#10141c'; ctx.fillRect(38, -60, 28, 60);
      break;
    case 4: // 能量穹顶
      ctx.beginPath(); ctx.arc(-5, 0, 85, Math.PI, 0); ctx.fill(); ctx.stroke();
      ctx.strokeStyle = acc; ctx.lineWidth = 3; ctx.globalAlpha = 0.5 + 0.3 * Math.sin(performance.now() / 300);
      ctx.beginPath(); ctx.arc(-5, 0, 95, Math.PI, 0); ctx.stroke(); ctx.globalAlpha = 1;
      ctx.fillStyle = c.body; ctx.fillRect(-60, -40, 110, 10);
      ctx.fillStyle = '#05060c'; ctx.fillRect(40, -50, 26, 50);
      break;
    case 5: { // 驯兽纪：木栅栏 + 门上的兽骨
      for (let i = 0; i < 8; i++) {
        const x = -80 + i * 19, h = 110 + (i % 2) * 14;
        ctx.fillStyle = hit ? '#ff5a4a' : c.dark; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, -h); ctx.lineTo(x + 8, -h - 14); ctx.lineTo(x + 16, -h); ctx.lineTo(x + 16, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
      }
      ctx.fillStyle = c.body; ctx.fillRect(-80, -70, 152, 10);
      ctx.fillStyle = '#efe6d2'; ctx.beginPath(); ctx.ellipse(-4, -150, 20, 15, 0, 0, 7); ctx.fill();
      ctx.strokeStyle = '#efe6d2'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-20, -158); ctx.quadraticCurveTo(-46, -176, -40, -200); ctx.moveTo(12, -158); ctx.quadraticCurveTo(38, -176, 32, -200); ctx.stroke();
      ctx.fillStyle = '#1b130c'; ctx.fillRect(-12, -154, 6, 6); ctx.fillRect(0, -154, 6, 6);
      ctx.fillStyle = '#2a1a10'; ctx.fillRect(40, -56, 28, 56);
      ctx.fillStyle = acc; ctx.beginPath(); ctx.arc(-60, -126, 6, 0, 7); ctx.arc(50, -132, 6, 0, 7); ctx.fill();
      break;
    }
    case 6: { // 生化纪：有机穹顶 + 发光的孢子囊
      ctx.beginPath(); ctx.ellipse(-8, 0, 88, 130, 0, Math.PI, 0); ctx.fill(); ctx.stroke();
      const t6 = performance.now() / 400;
      for (let i = 0; i < 5; i++) {
        const a = Math.PI + 0.45 + i * 0.55, r = 6 + 3 * Math.sin(t6 + i);
        ctx.fillStyle = acc; ctx.globalAlpha = 0.55 + 0.35 * Math.sin(t6 + i);
        ctx.beginPath(); ctx.arc(-8 + Math.cos(a) * 66, Math.sin(a) * 100, r + 6, 0, 7); ctx.fill();
      }
      ctx.globalAlpha = 1;
      ctx.strokeStyle = c.body; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(-8, 0, 60, 95, 0, Math.PI, 0); ctx.stroke();
      ctx.fillStyle = '#16200e'; ctx.beginPath(); ctx.ellipse(52, 0, 16, 40, 0, Math.PI, 0); ctx.fill();
      break;
    }
    case 7: // 火药纪：棱堡 + 炮口 + 旗子
      ctx.beginPath(); ctx.moveTo(-85, 0); ctx.lineTo(-75, -100); ctx.lineTo(65, -100); ctx.lineTo(75, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.fillStyle = c.body; ctx.fillRect(-75, -112, 140, 12);
      ctx.fillStyle = '#2b2b2b'; ctx.fillRect(30, -86, 52, 12); ctx.fillRect(30, -50, 52, 12);
      ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(82, -80, 5, 0, 7); ctx.arc(82, -44, 5, 0, 7); ctx.fill();
      ctx.strokeStyle = '#3a2a1c'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-50, -112); ctx.lineTo(-50, -180); ctx.stroke();
      ctx.fillStyle = acc; ctx.beginPath(); ctx.moveTo(-50, -180); ctx.lineTo(-14, -170 + Math.sin(performance.now() / 200) * 3); ctx.lineTo(-50, -158); ctx.fill();
      ctx.fillStyle = '#2a1a10'; ctx.fillRect(-10, -50, 28, 50);
      break;
    case 8: // 帆船纪：船身要塞 + 桅杆和帆
      ctx.beginPath(); ctx.moveTo(-92, -70); ctx.lineTo(82, -70); ctx.lineTo(62, 0); ctx.lineTo(-76, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.fillStyle = c.body; ctx.fillRect(-88, -78, 166, 10);
      ctx.fillStyle = '#111'; for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(-50 + i * 32, -40, 6, 0, 7); ctx.fill(); }
      ctx.strokeStyle = '#3a2a1c'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(-10, -78); ctx.lineTo(-10, -210); ctx.stroke();
      ctx.fillStyle = '#f2ead8'; ctx.strokeStyle = '#1b130c'; ctx.lineWidth = 2;
      const bw = Math.sin(performance.now() / 500) * 4;
      ctx.beginPath(); ctx.moveTo(-8, -200); ctx.quadraticCurveTo(44 + bw, -160, -8, -96); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.fillStyle = acc; ctx.beginPath(); ctx.moveTo(-10, -210); ctx.lineTo(18, -203); ctx.lineTo(-10, -196); ctx.fill();
      break;
  }
  // 塔位：按路线换材质的像素支架、平台、塔 / 空位提示、阵营旗，扩建动画（js/render/arms.js drawSlots）
  drawSlots(sd);
  ctx.restore();
}
/** 基地脚下：大块接地阴影 + 一圈石头地基（像素块），让基地像是建在地上 */
function drawBaseFooting(sd) {
  ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.beginPath(); ctx.ellipse(-5, 2, 120, 12, 0, 0, 7); ctx.fill();
  const g = GROUND_COL[sd.era], P = 6;
  const stones = [bgMix(g, '#000000', 0.35), bgMix(g, '#000000', 0.2), bgMix(g, '#ffffff', 0.08)];
  for (let i = 0; i < 34; i++) {        // 两排错开的石块，边缘一级级往下
    const x = -110 + i * P, edge = Math.min(i, 33 - i);
    const h = edge < 2 ? P : edge < 5 ? P * 2 : P * 3;
    ctx.fillStyle = stones[(i * 7 + sd.s) % 3]; ctx.fillRect(x, -h, P, h);
    ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(x, -h, P, 1);
  }
}
// drawTower、drawSlots（塔位支架）：见 js/render/arms.js

// ---------- 单位 ----------
function drawUnit(u) {
  const px = sx(u.x), z = G.zoom;
  if (px < -80 || px > W + 80) return;
  const c = SIDE_COL[u.side], acc = AGE_COL[u.age];
  ctx.save(); ctx.translate(px, GROUND_Y); ctx.scale(z * (u.side ? -1 : 1), z);
  const step = u.walking ? Math.sin(u.anim * 12) : 0;
  const body = u.hit > 0 ? '#ffffff' : c.body;
  drawFooting(u.w * 0.55, c.body);
  ctx.translate(0, -unitAlt(u));
  ctx.lineCap = 'round';
  if (drawUnitSprite(u)) { /* 像素画（js/render/sprites.js） */ }
  else if (u.air) drawAirUnit(u, c, acc, body);
  else if (u.type === 3) drawHeavy(u, c, acc, body, step);
  else if (u.type === 2) drawCavalry(u, c, acc, body, step);
  else if (u.type === 4) drawArtillery(u, c, acc, body);
  else {
    // 腿
    ctx.strokeStyle = c.dark; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(-3, -18); ctx.lineTo(-3 + step * 6, 0); ctx.moveTo(3, -18); ctx.lineTo(3 - step * 6, 0); ctx.stroke();
    // 身体和头
    ctx.fillStyle = body; ctx.fillRect(-7, -36, 14, 19);
    ctx.fillStyle = acc; ctx.fillRect(-7, -24, 14, 4);
    ctx.fillStyle = '#f0cfa8'; ctx.beginPath(); ctx.arc(0, -42, 6, 0, 7); ctx.fill();
    if (u.st >= 2) { ctx.fillStyle = u.st === 4 ? c.light : '#3b3b3b'; ctx.fillRect(-7, -49, 14, 5); }
    // 武器
    const sw = u.swing > 0 ? Math.sin((0.25 - u.swing) / 0.25 * Math.PI) : 0;
    ctx.strokeStyle = acc; ctx.lineWidth = u.type === 0 ? 4 : 3;
    ctx.beginPath();
    if (u.type === 0) { ctx.moveTo(5, -28); ctx.lineTo(16 + sw * 6, -42 + sw * 22); }
    else if (u.st === 0) { ctx.moveTo(4, -30); ctx.lineTo(10, -40 + sw * 10); }
    else { ctx.moveTo(-2, -29); ctx.lineTo(20, -31); }
    ctx.stroke();
    if (u.type === 1 && u.st === 4) { ctx.fillStyle = c.light; ctx.beginPath(); ctx.arc(20, -31, 3, 0, 7); ctx.fill(); }
  }
  ctx.restore();
  if (u.hp < u.maxHp) {   // 血条：带黑边，最短 26 像素，手机上也看得见
    const headroom = u.h * 1.12 + 14;
    const airTop = u.air ? (spriteMeta(u.age, u.type) || {}).airTop || headroom : headroom;
    const bw = Math.max(26, u.w * z), by = GROUND_Y - (unitAlt(u) + (u.air ? unitBounce(u).lift : 0) + airTop) * z;
    ctx.fillStyle = '#000'; ctx.fillRect(px - bw / 2 - 1, by - 1, bw + 2, 7);
    ctx.fillStyle = '#3a0d0d'; ctx.fillRect(px - bw / 2, by, bw, 5);
    ctx.fillStyle = u.side ? '#b98cff' : '#7dff6b'; ctx.fillRect(px - bw / 2, by, bw * Math.max(0, u.hp / u.maxHp), 5);
  }
}
/** 图集加载期间的空军兜底外观：生物振翅、飞艇和机械飞翼。 */
function drawAirUnit(u, c, acc, body) {
  const b = unitBounce(u), flap = Math.sin(G.t * 9 + u.anim) * 7;
  ctx.save(); ctx.translate(0, -b.lift); ctx.scale(b.sx, b.sy);
  ctx.strokeStyle = '#1b130c'; ctx.lineWidth = 2;
  ctx.fillStyle = body;
  if ([2, 8, 16].includes(u.age)) {
    ctx.beginPath(); ctx.ellipse(0, -21, 24, 11, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = acc; ctx.fillRect(-17, -24, 32, 5);
    ctx.strokeRect(-7, -8, 16, 7); ctx.fillStyle = c.dark; ctx.fillRect(-7, -8, 16, 7);
    ctx.beginPath(); ctx.moveTo(-8, -13); ctx.lineTo(-5, -8); ctx.moveTo(8, -13); ctx.lineTo(6, -8); ctx.stroke();
  } else {
    const organic = [0, 1, 5, 6, 7, 11, 12, 13].includes(u.age);
    const wingY = organic ? -27 + flap : -28;
    ctx.beginPath(); ctx.moveTo(-6, -18); ctx.lineTo(-24, wingY); ctx.lineTo(-15, -12); ctx.lineTo(-5, -9);
    ctx.lineTo(16, -12); ctx.lineTo(25, wingY); ctx.lineTo(6, -20); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = acc; ctx.beginPath(); ctx.ellipse(0, -14, 12, 6, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = organic ? '#f0cfa8' : c.light; ctx.fillRect(7, -21, 8, 7);
    ctx.fillStyle = '#fff1b8'; ctx.fillRect(13, -20, 2, 2);
    ctx.fillStyle = c.dark; ctx.fillRect(-16, -13, 8, 4);
  }
  if (u.swing > 0) { ctx.fillStyle = '#ffd16b'; ctx.fillRect(20, -14, 6, 4); }
  ctx.restore();
}
/** 兵脚下：接地阴影 + 阵营色的圈（两派一眼分清）。在已平移到脚下的坐标系里画，rx = 半宽 */
function drawFooting(rx, col) {
  ctx.fillStyle = 'rgba(0,0,0,.32)'; ctx.beginPath(); ctx.ellipse(0, 1, rx, 5, 0, 0, 7); ctx.fill();
  ctx.globalAlpha = 0.85; ctx.strokeStyle = col; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.ellipse(0, 1, rx + 3, 6.5, 0, 0, 7); ctx.stroke();
  ctx.globalAlpha = 1;
}
function drawRider(c, acc, body, x, y, sw) {
  ctx.fillStyle = body; ctx.fillRect(x - 5, y - 16, 10, 14);
  ctx.fillStyle = '#f0cfa8'; ctx.beginPath(); ctx.arc(x, y - 21, 5, 0, 7); ctx.fill();
  ctx.strokeStyle = acc; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x + 3, y - 10); ctx.lineTo(x + 20, y - 18 + sw * 10); ctx.stroke();
}
function drawCavalry(u, c, acc, body, step) {
  const sw = u.swing > 0 ? Math.sin((0.25 - u.swing) / 0.25 * Math.PI) : 0;
  ctx.strokeStyle = '#1b130c'; ctx.lineWidth = 2;
  if (u.st <= 1) { // 狼 / 马
    ctx.fillStyle = u.st === 0 ? '#6d6a66' : '#7a4a26';
    for (const lx of [-12, -5, 6, 13]) ctx.fillRect(lx - 2, -16 + (lx > 0 ? step : -step) * 3, 4, 16);
    ctx.beginPath(); ctx.ellipse(0, -22, 18, 9, 0, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.ellipse(18, -30, 7, 5, -0.5, 0, 7); ctx.fill();
    drawRider(c, acc, body, -2, -28, sw);
  } else if (u.st <= 3) { // 摩托 / 电动突击车
    ctx.fillStyle = '#222';
    for (const wx of [-12, 13]) { ctx.beginPath(); ctx.arc(wx, -8, 8, 0, 7); ctx.fill(); }
    ctx.fillStyle = u.st === 3 ? acc : '#555'; ctx.fillRect(-14, -20, 28, 8);
    drawRider(c, acc, body, -2, -20, sw);
  } else { // 悬浮飞骑
    ctx.fillStyle = acc; ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.ellipse(0, -4, 16, 3, 0, 0, 7); ctx.fill(); ctx.globalAlpha = 1;
    ctx.fillStyle = '#d7e3f0'; ctx.beginPath(); ctx.ellipse(0, -16 + step * 2, 18, 6, 0, 0, 7); ctx.fill(); ctx.stroke();
    drawRider(c, acc, body, -2, -22 + step * 2, sw);
  }
}
function drawArtillery(u, c, acc, body) {
  const recoil = u.swing > 0 ? -u.swing * 16 : 0;
  ctx.strokeStyle = '#1b130c'; ctx.lineWidth = 2;
  ctx.fillStyle = '#3a2a1c';
  ctx.beginPath(); ctx.arc(-6, -9, 9, 0, 7); ctx.fill(); ctx.stroke();
  ctx.fillStyle = body; ctx.fillRect(-16, -18, 22, 8);
  ctx.save(); ctx.translate(-2 + recoil, -18); ctx.rotate(-0.6);
  ctx.fillStyle = u.st === 0 ? '#7a5a3a' : acc; ctx.fillRect(0, -4, u.st === 0 ? 22 : 26, u.st >= 3 ? 7 : 8);
  if (u.st === 0) { ctx.fillStyle = '#888'; ctx.beginPath(); ctx.arc(22, 0, 6, 0, 7); ctx.fill(); }
  ctx.restore();
  // 操作手
  ctx.fillStyle = body; ctx.fillRect(-28, -30, 10, 16);
  ctx.fillStyle = '#f0cfa8'; ctx.beginPath(); ctx.arc(-23, -35, 5, 0, 7); ctx.fill();
  ctx.strokeStyle = c.dark; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-25, -14); ctx.lineTo(-25, 0); ctx.moveTo(-21, -14); ctx.lineTo(-21, 0); ctx.stroke();
}
function drawHeavy(u, c, acc, body, step) {
  ctx.strokeStyle = '#1b130c'; ctx.lineWidth = 2;
  if (u.st === 0) { // 猛犸
    ctx.fillStyle = '#6b4a30';
    for (const lx of [-16, -6, 6, 16]) ctx.fillRect(lx - 3, -14 + (lx % 2 ? step : -step) * 2, 7, 14);
    ctx.beginPath(); ctx.ellipse(0, -24, 25, 15, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.arc(22, -26, 10, 0, 7); ctx.fill();
    ctx.strokeStyle = '#f5ecd6'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(30, -14, 8, Math.PI, Math.PI * 1.8, true); ctx.stroke();
    ctx.fillStyle = body; ctx.fillRect(-14, -40, 22, 8);
    ctx.fillStyle = '#f0cfa8'; ctx.beginPath(); ctx.arc(-2, -48, 5, 0, 7); ctx.fill();
  } else if (u.st === 4) { // 机甲
    ctx.strokeStyle = c.dark; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.moveTo(-8, -30); ctx.lineTo(-10 + step * 8, 0); ctx.moveTo(8, -30); ctx.lineTo(10 - step * 8, 0); ctx.stroke();
    ctx.fillStyle = body; ctx.fillRect(-18, -60, 36, 32); ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.strokeRect(-18, -60, 36, 32);
    ctx.fillStyle = acc; ctx.fillRect(4, -54, 10, 6); ctx.fillRect(14, -44, 22, 7);
  } else { // 战车 / 蒸汽坦克 / 电磁战车
    ctx.fillStyle = body; ctx.fillRect(-23, -30, 46, 20); ctx.strokeRect(-23, -30, 46, 20);
    ctx.fillStyle = '#2a2a2a';
    const wheels = u.st === 1 ? [[-10, 11]] : [[-15, 7], [0, 7], [15, 7]];
    for (const [wx, r] of wheels) { ctx.beginPath(); ctx.arc(wx, -r, r, 0, 7); ctx.fill(); }
    ctx.fillStyle = acc;
    if (u.st === 1) { ctx.fillRect(10, -40, 3, 14); ctx.fillStyle = '#f0cfa8'; ctx.beginPath(); ctx.arc(0, -38, 5, 0, 7); ctx.fill(); ctx.strokeStyle = acc; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(6, -34); ctx.lineTo(30, -40); ctx.stroke(); }
    else {
      ctx.fillRect(-10, -40, 22, 10); ctx.fillRect(10, -37, 22, 5);
      if (u.st === 2) { ctx.fillStyle = 'rgba(90,90,90,.6)'; ctx.beginPath(); ctx.arc(-16, -42 - (u.anim * 20 % 10), 5, 0, 7); ctx.fill(); }
      if (u.st === 3 && Math.random() < 0.3) { ctx.strokeStyle = '#bfe8ff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-6, -42); ctx.lineTo(-2, -50); ctx.lineTo(2, -44); ctx.lineTo(6, -52); ctx.stroke(); }
    }
  }
}

// ---------- 弹道、特效 ----------
// drawProjs / drawShells：见 js/render/arms.js
function drawFx() {
  for (const f of G.fx) {
    if (f.kind === 'pfx') { if (!FX_UNDER[f.name]) drawHitFx(f); continue; }   // 像素受击 / 爆炸特效（fx.js）；燃烧圈 / 毒池在 drawScorch 里画
    const k = f.t / f.dur, x = sx(f.x), y = sy(f.y), z = G.zoom;
    ctx.globalAlpha = 1 - k;
    if (f.kind === 'die') {   // 单位死亡：有像素画就播死亡动画，没有就冒一团烟
      ctx.globalAlpha = 1; if (drawDeathSprite(f)) continue;
      const kk = Math.min(1, f.t / 0.4); ctx.globalAlpha = 1 - kk;
      ctx.fillStyle = f.col; ctx.beginPath(); ctx.arc(x, y, (8 + kk * 18) * z, 0, 7); ctx.fill();
    }
    else if (f.kind === 'puff') { ctx.fillStyle = f.col; ctx.beginPath(); ctx.arc(x, y, (8 + k * 18) * z, 0, 7); ctx.fill(); }
    else if (f.kind === 'boom') { ctx.fillStyle = '#ffcf6b'; ctx.beginPath(); ctx.arc(x, y, f.r * (0.3 + k * 0.7) * z, 0, 7); ctx.fill(); ctx.fillStyle = '#ff6a2e'; ctx.beginPath(); ctx.arc(x, y, f.r * 0.4 * (1 - k) * z, 0, 7); ctx.fill(); }
    else if (f.kind === 'bolt') { ctx.strokeStyle = '#d8f2ff'; ctx.lineWidth = 4 * z; ctx.beginPath(); let bx = x, by = sy(-600); ctx.moveTo(bx, by); while (by < y) { by += 50 * z; bx += rand(-18, 18) * z; ctx.lineTo(bx, Math.min(by, y)); } ctx.stroke(); ctx.fillStyle = f.col; ctx.beginPath(); ctx.arc(x, y, f.r * k * z, 0, 7); ctx.fill(); }
    ctx.globalAlpha = 1;
  }
  ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = 'center';   // 击杀飘字
  for (const t of G.texts) {
    ctx.globalAlpha = 1 - t.t / 1.1;
    const x = sx(t.x), y = sy(t.y) - t.t * 30;
    ctx.lineWidth = 3; ctx.strokeStyle = '#000'; ctx.strokeText(t.str, x, y);
    ctx.fillStyle = '#ffd34d'; ctx.fillText(t.str, x, y);
  }
  ctx.globalAlpha = 1;
}
