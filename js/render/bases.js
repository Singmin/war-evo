'use strict';
// 基地（城堡）像素画：图在 assets/bases/bases.webp，格子信息在 js/render/base_meta.js（都由 tools/gen_bases.py 生成）
// 有像素画的时代用像素画，没有的时代还是 world.js 里的矢量画法
// 列 = 损坏程度（完好 / 受损 <60% / 残破 <30%），行 = 我方、敌方、纯白（受击闪白）
const BASE_IMG = new Image();
BASE_IMG.src = 'assets/bases/bases.webp';

function baseDamage(sd) {
  const pct = sd.baseHp / BASE_HP[sd.age];
  return pct < 0.3 ? 2 : pct < 0.6 ? 1 : 0;
}

// 每个时代会动的小东西（在像素画上面画）：坐标是基地本地坐标（x 向战场为正，y 向上为负）
const BASE_ANIM = {
  0(t) {   // 门前篝火
    ctx.fillStyle = '#3a2414'; ctx.fillRect(18, -4, 22, 4);
    const f = Math.sin(t / 90) * 2;
    ctx.fillStyle = '#ff9a2e'; ctx.beginPath(); ctx.moveTo(20, -4); ctx.quadraticCurveTo(29, -26 - f, 38, -4); ctx.fill();
    ctx.fillStyle = '#ffe08a'; ctx.beginPath(); ctx.moveTo(25, -4); ctx.quadraticCurveTo(29, -16 + f, 33, -4); ctx.fill();
  },
  2(t) {   // 两根烟囱冒烟
    smoke(-65, -138, t, 'rgba(80,80,80,.5)', 1);
    smoke(-46, -122, t + 700, 'rgba(80,80,80,.45)', 0.8);
  },
  3(t) {   // 铁塔顶红灯闪烁 + 探照灯来回扫
    if (Math.floor(t / 600) % 2) glow(-66, -162, 4, '#ff4a3a', 1);
    const a = -0.5 + Math.sin(t / 1500) * 0.4;
    ctx.fillStyle = 'rgba(255,240,170,.16)'; ctx.beginPath(); ctx.moveTo(24, -138);
    ctx.lineTo(24 + Math.cos(a - 0.08) * 260, -138 + Math.sin(a - 0.08) * 260);
    ctx.lineTo(24 + Math.cos(a + 0.08) * 260, -138 + Math.sin(a + 0.08) * 260); ctx.fill();
  },
  4(t) {   // 能量塔顶的球、机库里机甲的眼睛一呼一吸
    const k = 0.5 + 0.5 * Math.sin(t / 300);
    glow(-70, -112, 8 + k * 4, '#5ff7ff', 0.35 + k * 0.3);
    glow(58, -34, 4 + k * 2, '#5ff7ff', 0.3 + k * 0.4);
  },
  6(t) {   // 培养罐里冒气泡
    ctx.fillStyle = 'rgba(220,255,200,.75)';
    for (let i = 0; i < 6; i++) {
      const k = (t / 2200 + i / 6) % 1;
      ctx.beginPath(); ctx.arc(-12 + (i * 37 % 24) + Math.sin(t / 300 + i) * 2, -18 - k * 84, 1.5 + (i % 3) * 0.7, 0, 7); ctx.fill();
    }
  },
  9(t) {   // 冷却塔冒白汽 + 反应堆绿光
    smoke(-61, -122, t, 'rgba(235,240,235,.55)', 1.3);
    glow(0, -61, 22, '#b6ff3b', 0.12 + 0.08 * Math.sin(t / 400));
  },
  10(t) {  // 主眼来回扫视
    glow(Math.sin(t / 700) * 4, -75, 6, '#c0e4ff', 0.9);
    glow(0, -75, 18, '#4fa8ff', 0.15 + 0.1 * Math.sin(t / 500));
  },
  11(t) {  // 菌褶飘出发光孢子
    ctx.fillStyle = '#9ff7d8';
    for (let i = 0; i < 8; i++) {
      const k = (t / 4000 + i / 8) % 1;
      ctx.globalAlpha = 1 - k;
      ctx.fillRect(-40 + i * 11 + Math.sin(t / 600 + i) * 8, -90 - k * 90, 3, 3);
    }
    ctx.globalAlpha = 1;
  },
  12(t) {  // 头骨眼窝里的火
    const k = 0.6 + 0.4 * Math.sin(t / 250);
    glow(-14, -89, 6 * k + 3, '#ff8a3a', 0.6); glow(14, -89, 6 * k + 3, '#ff8a3a', 0.6);
  },
  13(t) {  // 蜂群绕着蜂巢飞
    ctx.fillStyle = '#2a1a10';
    for (let i = 0; i < 12; i++) {
      const a = t / (500 + i * 37) + i * 2.1, r = 36 + (i % 4) * 9;
      ctx.fillRect(Math.cos(a) * r - 1, -95 + Math.sin(a * 1.3) * r * 0.5 - 1, 3, 2);
    }
  },
  14(t) {  // 烟囱冒黑烟
    smoke(-48, -143, t, 'rgba(50,50,55,.5)', 1.1);
  },
  15(t) {  // 塔台顶的航标灯
    if (Math.floor(t / 450) % 2) glow(22, -136, 4, '#ff4a3a', 1);
  },
};

// 一团发光（中心实、外圈淡）
function glow(x, y, r, col, a) {
  ctx.fillStyle = col;
  ctx.globalAlpha = a * 0.35; ctx.beginPath(); ctx.arc(x, y, r * 2, 0, 7); ctx.fill();
  ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
  ctx.globalAlpha = 1;
}

// 一串往上飘、越飘越大越淡的烟
function smoke(x, y, t, col, s) {
  ctx.fillStyle = col;
  for (let i = 0; i < 4; i++) {
    const k = ((t / 1400 + i / 4) % 1);
    ctx.globalAlpha = 1 - k;
    ctx.beginPath(); ctx.arc(x + Math.sin(t / 500 + i) * 6 * k, y - k * 60 * s, (6 + k * 12) * s, 0, 7); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

// world.js 的 drawBase 先调用它（已平移到基地中心脚下、缩放和左右翻转好）：画成了返回 true
function drawBaseSprite(sd) {
  const m = BASE_META[sd.era];
  if (!m || !BASE_IMG.complete || !BASE_IMG.naturalWidth) return false;
  const S = BASE_SCALE, { cw, ch, ax } = BASE_CELL, dmg = baseDamage(sd), t = performance.now();
  const blit = row => ctx.drawImage(BASE_IMG, dmg * cw, m.y + row * ch, cw, ch, -ax * S, -(ch - 1) * S, cw * S, ch * S);
  ctx.imageSmoothingEnabled = false;
  blit(sd.s);
  if (sd.flash > 0) { ctx.globalAlpha = 0.55; blit(2); ctx.globalAlpha = 1; }   // 受击：叠一层白
  if (BASE_ANIM[sd.era]) BASE_ANIM[sd.era](t);
  // 受损冒黑烟，残破再加几簇火
  if (dmg >= 1) smoke(-20, -100, t + sd.s * 300, 'rgba(40,36,34,.55)', 1.1);
  if (dmg >= 2) {
    smoke(40, -60, t + 900, 'rgba(40,36,34,.5)', 0.9);
    for (const [x, y] of [[-40, -50], [22, -66], [56, -20]]) {
      const f = Math.sin(t / 80 + x) * 2;
      ctx.fillStyle = '#ff7a2e'; ctx.beginPath(); ctx.moveTo(x - 6, y); ctx.quadraticCurveTo(x, y - 18 - f, x + 6, y); ctx.fill();
      ctx.fillStyle = '#ffd86a'; ctx.beginPath(); ctx.moveTo(x - 3, y); ctx.quadraticCurveTo(x, y - 9 + f, x + 3, y); ctx.fill();
    }
  }
  return true;
}
