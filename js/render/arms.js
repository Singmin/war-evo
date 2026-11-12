'use strict';
// 画面：防御塔、弹道、大招（落弹、落点标记、冲击波、焦痕）、大招释放横幅
// 都是像素风：用 3 像素一格的方块拼，和兵、基地的像素画一致。world.js 的 drawBase / drawWorld / drawFx 调用这里。

/** 塔的像素格大小（逻辑像素） */
const ARM_PX = 3;
/** 塔开火后后坐 + 枪口火光持续的秒数 */
const TOWER_RECOIL_T = 0.14, TOWER_FLASH_T = 0.07;
/** 塔的材质：按时代所属路线（无 / 机械 / 生化 / 火器）配色；dark 描边、base 底色、mid 主体、light 高光、metal 炮管 / 金属件 */
const TOWER_PAL = {
  wood: { dark: '#170d05', base: '#7a4e28', mid: '#ad7a44', light: '#e8bd84', metal: '#c4beb2' },
  mech: { dark: '#161b22', base: '#414c5a', mid: '#64738a', light: '#b0bfd0', metal: '#d8ac4c' },
  bio:  { dark: '#101a0b', base: '#355226', mid: '#58803c', light: '#a2d070', metal: '#d6ec86' },
  gun:  { dark: '#171210', base: '#3a332e', mid: '#5c5148', light: '#94867a', metal: '#c08a3c' },
};
const towerPal = era => TOWER_PAL[ERA_ROUTE[era] || 'wood'];

/** apx 画到哪块画布上：平时是战场 ctx，底栏按钮的塔缩略图画到离屏画布（towerIcon） */
let armG = null;
/** 在当前坐标系里按像素格画方块 */
function apx(x, y, w, h, col) { armG.fillStyle = col; armG.fillRect(x * ARM_PX, y * ARM_PX, w * ARM_PX, h * ARM_PX); }

/**
 * 画一座塔（基地本地坐标，x 朝战场为正；已按阵营翻转）。y = 塔位木板顶面。
 * 三种塔外形不同：轻塔 = 小型速射台，中塔 = 弩炮 / 双管炮，重塔 = 粗管臼炮。
 * 炮管跟着瞄准角转，开火时后坐 + 枪口火光；升级等级画成木板上的金色铆钉。
 */
function drawTower(t, y, side, g = ctx) {
  armG = g;
  const team = SIDE_COL[side].body, pal = towerPal(t.age), tier = ERA_TIER[t.age], acc = AGE_COL[t.age];
  const since = TOWER_BASE[t.type].rate - t.cd;            // 距上次开火的秒数
  const rec = since >= 0 && since < TOWER_RECOIL_T ? 1 - since / TOWER_RECOIL_T : 0;
  g.save(); g.translate(0, y);
  // 等级铆钉：木板正面
  for (let k = 0; k < 2; k++) {
    g.fillStyle = '#1b120a'; g.fillRect(-21 + k * 9, 1, 7, 6);
    g.fillStyle = k < (t.lvl || 0) ? '#ffd34d' : '#5a4430'; g.fillRect(-20 + k * 9, 2, 5, 4);
  }
  let pivotY, len, aim = t.aim || 0;
  if (t.type === 0) {        // 轻塔：三脚架 + 小方箱 + 前挡板
    apx(-4, -2, 1, 2, pal.dark); apx(3, -2, 1, 2, pal.dark); apx(-1, -2, 2, 2, pal.dark);
    apx(-4, -7, 8, 5, pal.dark); apx(-3, -7, 6, 4, pal.mid); apx(-3, -7, 6, 1, pal.light); apx(-3, -4, 6, 1, team);
    apx(3, -8, 2, 6, pal.dark); apx(3, -8, 1, 5, pal.base);
    pivotY = -5.5; len = 8;
  } else if (t.type === 1) { // 中塔：宽台座 + 机匣 + 铆钉
    apx(-6, -3, 12, 3, pal.dark); apx(-5, -3, 10, 2, pal.base);
    apx(-5, -9, 10, 6, pal.dark); apx(-4, -9, 8, 5, pal.mid); apx(-4, -9, 8, 1, pal.light); apx(-4, -6, 8, 1, team);
    apx(-3, -5, 1, 1, pal.metal); apx(2, -5, 1, 1, pal.metal);
    pivotY = -7.5; len = 10;
  } else {                   // 重塔：带轮炮座 + 半圆炮塔
    apx(-7, -4, 14, 4, pal.dark); apx(-6, -4, 12, 2, pal.base);
    apx(-6, -2, 3, 2, '#111'); apx(3, -2, 3, 2, '#111'); apx(-5, -2, 1, 1, pal.metal); apx(4, -2, 1, 1, pal.metal);
    apx(-6, -9, 12, 5, pal.dark); apx(-5, -9, 10, 4, pal.mid); apx(-4, -10, 8, 1, pal.dark); apx(-3, -10, 6, 1, pal.mid);
    apx(-5, -9, 10, 1, pal.light); apx(-5, -6, 10, 1, team);
    pivotY = -7; len = 10;
    aim = Math.min(aim, 0.2) - 0.55;                         // 臼炮：炮口总是往上翘
  }
  // 高时代：机身上一盏时代色的灯
  if (tier >= 3) {
    g.globalAlpha = 0.65 + 0.35 * Math.sin(performance.now() / 260 + t.type);
    apx(-2, pivotY - 1 + (t.type === 2 ? 3 : 2), 2, 1, acc); g.globalAlpha = 1;
  }
  // 炮管
  g.translate(0, pivotY * ARM_PX); g.rotate(aim); g.translate(-rec * 2 * ARM_PX, 0);
  if (t.type === 0) {
    apx(0, -1, len, 2, pal.dark); apx(0, -1, len, 1, pal.metal);
    if (tier === 0) apx(len - 1, -1.5, 2, 3, pal.light);     // 石器：弹兜里一颗石子
  } else if (t.type === 1) {
    if (tier <= 1) {          // 弩炮：横梁 + 弓臂
      apx(-2, -1, len + 2, 2, pal.dark); apx(-2, -1, len + 2, 1, pal.light);
      apx(len - 3, -5, 1, 10, pal.dark); apx(len - 4, -4, 1, 8, pal.base);
      apx(len - 1, -1, 2, 2, pal.metal);
    } else {                  // 双管
      apx(-1, -2.5, len, 2, pal.dark); apx(-1, -2.5, len, 1, pal.metal);
      apx(-1, 0.5, len, 2, pal.dark); apx(-1, 0.5, len, 1, pal.metal);
      apx(-2, -3, 4, 6, pal.dark);
    }
  } else {
    apx(-2, -2, len, 4, pal.dark); apx(-1, -2, len - 2, 3, tier === 0 ? pal.light : pal.metal);
    apx(len - 3, -3, 3, 6, pal.dark); apx(len - 2, -2, 1, 4, pal.base);
  }
  // 枪口火光
  if (since >= 0 && since < TOWER_FLASH_T) {
    const s = t.type === 2 ? 4 : 2.5;
    apx(len + 0.5, -s / 2, s, s, '#fff2b8'); g.globalAlpha = 0.7; apx(len + s, -s / 3, s * 0.7, s * 0.66, '#ffb03a'); g.globalAlpha = 1;
  }
  g.restore();
}

// ---------- 塔位支架 ----------
// 支架和平台按时代路线换材质：原始 = 捆扎原木，机械 = 钢桁架 + 爬梯，生化 = 扭藤 + 骨肋，火药 = 砖石塔身 + 城垛。
// 材质按"这一层塔的建造时代"选，不按基地当前时代：跃迁后旧塔和它那一层都不变，塔身一层层叠出历史感。
// 和塔一样按 ARM_PX 一格的像素画，配色用 towerPal。坐标是基地本地坐标（x 朝战场为正，已按阵营翻转），单位是格。
const SLOT_GROW_T = 0.6;        // 扩建：新的一节从下面升上来的秒数
const SLOT_DUST_T = 0.55;       // 升到位以后扬尘、迸火星的秒数
const SLOT_RISE = 18;           // 新的一节从多低的地方升上来（像素）
const SCAFFOLD_BASE = -100;     // 支架从基地这个高度往上搭（像素）
const ROPE = '#c9a96e';

/** 一节支架：y = 0 是这一节底部，往上 h 格（负方向） */
function drawSection(mat, pal, h, i) {
  const diag = (x0, x1, col) => {             // 从 (x0, 0) 到 (x1, -h) 的阶梯斜撑
    const n = Math.max(1, h);
    for (let s = 0; s < n; s++) apx(Math.round(x0 + (x1 - x0) * s / n), -s - 1, 1, 1, col);
  };
  if (mat === 'gun') {          // 砖石塔身：错缝砖 + 射击孔
    apx(-6, -h, 12, h, pal.base);
    for (let y = 0; y < h; y += 2) {
      apx(-6, -y - 1, 12, 1, pal.mid);
      apx(-6, -y - 2, 12, 1, pal.dark);
      for (let x = -6 + ((y / 2 + i) % 2) * 2; x < 6; x += 4) apx(x, -y - 1, 1, 1, pal.dark);
    }
    apx(-6, -h, 1, h, pal.light); apx(5, -h, 1, h, pal.dark);
    apx(-1, -Math.round(h / 2) - 3, 2, 5, pal.dark); apx(-1, -Math.round(h / 2) - 3, 2, 4, '#0c0806');
    return;
  }
  if (mat === 'bio') {          // 两股扭在一起的藤干 + 一根根骨肋
    for (let y = 0; y < h; y++) {
      const o = Math.round(Math.sin((y + i * 5) / 2.2) * 1.4);
      apx(-6 + o, -y - 1, 3, 1, pal.dark); apx(-5 + o, -y - 1, 1, 1, pal.mid);
      apx(3 - o, -y - 1, 3, 1, pal.dark); apx(4 - o, -y - 1, 1, 1, pal.mid);
    }
    for (let y = 3; y < h - 1; y += 4) {
      apx(-4, -y - 1, 8, 1, pal.light); apx(-4, -y, 8, 1, pal.dark);
      apx(-5, -y, 1, 1, pal.light); apx(4, -y, 1, 1, pal.light);
    }
    armG.globalAlpha = 0.5 + 0.5 * Math.sin(performance.now() / 300 + i * 2);
    apx(-1 + (i % 2) * 2, -Math.round(h / 2), 1, 1, pal.metal); armG.globalAlpha = 1;
    return;
  }
  if (mat === 'mech') {         // 钢桁架：两根工字梁 + 交叉拉杆 + 铆钉；背面一架爬梯
    apx(-10, -h, 1, h, pal.dark); apx(-8, -h, 1, h, pal.dark);
    for (let y = 1; y < h; y += 2) apx(-9, -y - 1, 1, 1, pal.light);
    diag(-4, 3, pal.mid); diag(3, -4, pal.mid);
    apx(-4, -Math.round(h / 2), 8, 1, pal.dark);
    for (const x0 of [-6, 4]) {
      apx(x0, -h, 2, h, pal.dark); apx(x0, -h, 1, h, pal.mid);
      for (let y = 1; y < h; y += 3) apx(x0 + 1, -y - 1, 1, 1, pal.metal);
    }
    return;
  }
  // 原始：两根原木 + 交叉斜撑 + 麻绳绑扎
  diag(-4, 3, pal.base); diag(3, -4, pal.base);
  for (const x0 of [-7, 4]) {
    apx(x0, -h, 3, h, pal.mid); apx(x0, -h, 1, h, pal.dark); apx(x0 + 2, -h, 1, h, pal.base);
    for (let y = 2 + (x0 > 0 ? 2 : 0); y < h; y += 5) apx(x0 + 1, -y - 1, 1, 1, pal.dark);   // 树疖
    for (const y of [h - 2, Math.round(h / 2)]) { apx(x0, -y - 1, 3, 1, ROPE); apx(x0, -y, 3, 1, pal.dark); }
  }
}

/** 塔位平台：y = 0 是台面（塔就踩在这里），往下 3 格 */
function drawPlatform(mat, pal) {
  if (mat === 'gun') {          // 石台 + 两头城垛 + 托石
    apx(-9, 0, 18, 3, pal.dark); apx(-9, 0, 18, 1, pal.light); apx(-8, 1, 16, 1, pal.base);
    for (const x of [-10, 7]) { apx(x, -3, 3, 3, pal.dark); apx(x, -3, 3, 1, pal.light); apx(x + 1, -2, 1, 1, pal.base); }
    apx(-8, 3, 2, 1, pal.dark); apx(6, 3, 2, 1, pal.dark);
  } else if (mat === 'bio') {   // 甲壳台：圆边、亮斑，边上垂几片叶子
    apx(-8, 0, 16, 1, pal.light); apx(-9, 1, 18, 1, pal.mid); apx(-8, 2, 16, 1, pal.dark);
    for (const x of [-6, -1, 5]) apx(x, 1, 1, 1, pal.metal);
    apx(-9, 2, 1, 2, pal.light); apx(8, 2, 1, 3, pal.mid); apx(-3, 3, 1, 1, pal.light); apx(3, 3, 1, 2, pal.mid);
  } else if (mat === 'mech') {  // 钢格板 + 两头护栏 + 三角托架
    apx(-9, 0, 18, 2, pal.dark); apx(-9, 0, 18, 1, pal.light);
    for (let x = -8; x < 8; x += 2) apx(x, 1, 1, 1, pal.base);
    for (const x of [-9, 8]) apx(x, -3, 1, 3, pal.metal);
    apx(-9, -3, 3, 1, pal.metal); apx(6, -3, 3, 1, pal.metal);
    apx(-7, 2, 3, 1, pal.dark); apx(-6, 3, 1, 1, pal.dark); apx(4, 2, 3, 1, pal.dark); apx(5, 3, 1, 1, pal.dark);
  } else {                      // 木板拼的台面，接缝 + 钉头
    apx(-9, 0, 18, 3, pal.dark); apx(-9, 0, 18, 1, pal.light); apx(-8, 1, 16, 1, pal.mid);
    for (let x = -5; x < 8; x += 4) { apx(x, 1, 1, 1, pal.dark); apx(x - 2, 0, 1, 1, '#f0d8a8'); }
  }
}

/** 空塔位：半透明的塔座框 + 一闪一闪的"+"，提示这里能建塔 */
function drawEmptySlot(phase) {
  const a = 0.7 + 0.3 * Math.sin(performance.now() / 260 + phase);
  armG.globalAlpha = a * 0.7;
  for (const [x, y, w, h] of [[-6, -10, 3, 1], [-6, -10, 1, 3], [3, -10, 3, 1], [5, -10, 1, 3], [-6, -1, 3, 1], [-6, -3, 1, 3], [3, -1, 3, 1], [5, -3, 1, 3]])
    apx(x, y, w, h, '#ffffff');
  armG.globalAlpha = a;
  apx(-2, -8, 4, 6, 'rgba(0,0,0,.55)'); apx(-3, -7, 6, 4, 'rgba(0,0,0,.55)');
  apx(-1, -8, 2, 6, '#ffe08a'); apx(-3, -6, 6, 2, '#ffe08a');
  apx(-1, -8, 2, 1, '#fff8e0'); apx(-3, -6, 2, 1, '#fff8e0');
  armG.globalAlpha = 1;
}

/** 扩建落地：平台两头扬尘，中间迸几颗锤击火星（k 0→1） */
function drawSlotDust(k) {
  for (const d of [-1, 1]) for (let j = 0; j < 3; j++) {
    armG.globalAlpha = (1 - k) * 0.75;
    const s = 2 + Math.round(k * 2);
    apx(d * (10 + k * 7 + j * 2) - s / 2, 1 - j - k * 3 - s / 2, s, s, j === 1 ? '#d8cbb0' : '#b8aa90');
  }
  armG.globalAlpha = 1 - k;
  for (let j = 0; j < 4; j++) apx(Math.round((j - 1.5) * 4 + Math.sin(j * 7) * 2 * k), Math.round(-2 - k * (6 + j * 3)), 1, 1, j % 2 ? '#ffd34d' : '#fff2b8');
  armG.globalAlpha = 1;
}

/**
 * 画全部塔位（基地本地坐标，已翻转）：支架、平台、塔或空位提示，最高处插阵营旗。
 * 扩建时（sd.growAt 记着扩建那一刻的 G.t）最新的一节从下面一节后面升上来，到位时扬尘、迸火星，我方再响一声。
 */
function drawSlots(sd) {
  const n = sd.slots;
  if (n <= 0) return;
  armG = ctx;
  // 每一层的支架和平台跟着这一层塔的建造时代走（跃迁后旧塔连同它脚下那层都保持原样）；空层用当前时代
  const eraOf = i => (sd.towers[i] ? sd.towers[i].age : sd.era);
  const matOf = i => ERA_ROUTE[eraOf(i)] || 'wood';
  const age = sd.growAt == null ? 99 : G.t - sd.growAt;
  const k = Math.min(1, age / SLOT_GROW_T);
  // 新一节还差多少像素到位（只升 SLOT_RISE，不然新平台会从下面那座塔身上穿过去），同时淡入
  const rise = n > 1 ? Math.round((1 - k) ** 3 * SLOT_RISE / ARM_PX) * ARM_PX : 0;
  if (age >= SLOT_GROW_T && sd.growSfx !== sd.growAt) { sd.growSfx = sd.growAt; if (sd.s === 0) sfx('build'); }
  const lift = i => (i === n - 1 ? rise : 0);
  // 支架：从下往上一节一节画；正在升起的那一节剪掉下面一节平台以下的部分，看起来是从里面顶出来的
  for (let i = 0; i < n; i++) {
    const bottom = i === 0 ? SCAFFOLD_BASE : slotY(i - 1) + 3 * ARM_PX;
    const h = Math.round((bottom - slotY(i)) / ARM_PX) - 3;   // 到这一层平台的底面
    if (h <= 0) continue;
    ctx.save();
    if (lift(i)) { ctx.beginPath(); ctx.rect(-60, bottom - 200, 120, 200); ctx.clip(); }   // 只露出下面一层平台以上的部分
    ctx.translate(0, bottom + lift(i));
    drawSection(matOf(i), towerPal(eraOf(i)), h, i);
    ctx.restore();
  }
  for (let i = 0; i < n; i++) {
    const y = slotY(i) + lift(i), fade = i === n - 1 && n > 1 ? Math.min(1, k * 1.5) : 1;
    ctx.save(); ctx.globalAlpha = fade; ctx.translate(0, y); drawPlatform(matOf(i), towerPal(eraOf(i))); ctx.restore();
    const t = sd.towers[i];
    if (t) drawTower(t, y, sd.s);
    // 建塔提示只给玩家看，敌方空塔位不显示
    else if (fade >= 1 && sd.s === 0) { armG = ctx; ctx.save(); ctx.translate(0, y); drawEmptySlot(i); ctx.restore(); }
    armG = ctx;
    if (i === n - 1 && age >= SLOT_GROW_T && age < SLOT_GROW_T + SLOT_DUST_T) {
      ctx.save(); ctx.translate(0, y); drawSlotDust((age - SLOT_GROW_T) / SLOT_DUST_T); ctx.restore();
    }
  }
  drawSlotFlag(sd, slotY(n - 1) + lift(n - 1));
}

/** 阵营旗：插在最高塔位的后侧，阵营色，像素式飘动 */
function drawSlotFlag(sd, top) {
  const c = SIDE_COL[sd.s], dark = '#2a1a0e', px = -30, py = top - 8, t = performance.now() / 160;
  ctx.fillStyle = dark; ctx.fillRect(px - 2, py - 62, 4, 62);
  ctx.fillStyle = c.light; ctx.fillRect(px - 3, py - 66, 6, 5);
  for (let i = 0; i < 7; i++) {
    const dy = Math.round(Math.sin(t - i * 0.7) * 2) * 2;
    ctx.fillStyle = i % 3 === 2 ? c.dark : c.body; ctx.fillRect(px + 2 + i * 5, py - 60 + dy, 5, 22);
    ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(px + 2 + i * 5, py - 40 + dy, 5, 2);
  }
}

/** 底栏按钮用的塔缩略图（像素画，和战场上的塔一模一样），按 类型 / 时代 / 等级 缓存成图片地址 */
const towerIconCache = {};
function towerIcon(type, era, lvl = 0) {
  const key = type + '/' + era + '/' + lvl;
  if (!towerIconCache[key]) {
    const c = document.createElement('canvas'); c.width = 60; c.height = 48;
    const g = c.getContext('2d'); g.translate(24, 38);
    drawTower({ type, age: era, cd: 9, aim: -0.25, lvl }, 0, 0, g);
    towerIconCache[key] = c.toDataURL();
  }
  return towerIconCache[key];
}

// ---------- 弹道 ----------
/** 弹道在第 t 秒时的位置（同 sim.js projPos，但可指定时刻，用来画拖尾） */
function projAt(p, t) { return projPos({ x0: p.x0, y0: p.y0, target: p.target, dur: p.dur, arc: p.arc, t: Math.max(0, t) }); }

/** 画一帧飞行体（FX_META 里 kind:'fly'）：锚点在弹头，朝 ang 方向；朝左飞时上下翻一下，羽毛 / 尾焰不会倒过来 */
function drawFly(key, x, y, ang, s, t) {
  const m = FX_META[key];
  const i = Math.floor(t * m.fps) % m.n, S = FX_SCALE * G.zoom * s;
  ctx.save();
  ctx.translate(Math.round(x), Math.round(y));
  if (m.spin) { ctx.rotate(t * 14 * (Math.cos(ang) < 0 ? -1 : 1)); ctx.scale(S, S); }
  else { ctx.rotate(ang); ctx.scale(S, Math.cos(ang) < 0 ? -S : S); }
  const ax = m.spin ? m.w / 2 : m.px, ay = m.spin ? m.h / 2 : m.py;
  ctx.drawImage(FX_IMG, m.x + (i % m.cols) * m.w, m.y + Math.floor(i / m.cols) * m.h, m.w, m.h, -ax, -ay, m.w, m.h);
  ctx.restore();
}

/** 折线闪电：从 (x0,y0) 到 (x1,y1)，jag 抖动幅度，每帧重新随机 */
function boltPath(x0, y0, x1, y1, seg, jag) {
  const pts = [[x0, y0]], dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
  for (let i = 1; i < seg; i++) { const k = i / seg, o = (Math.random() * 2 - 1) * jag; pts.push([x0 + dx * k + nx * o, y0 + dy * k + ny * o]); }
  pts.push([x1, y1]);
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (const [px, py] of pts) ctx.lineTo(px, py);
}

/** 瞬发类：电弧 / 连锁闪电 / 光束 / 藤鞭，从发射点直接打到目标 */
function drawBeam(p) {
  const z = G.zoom, k = Math.min(1, p.t / p.dur), e = projAt(p, p.dur);
  const x0 = sx(p.x0), y0 = sy(p.y0), x1 = sx(e.x), y1 = sy(e.y), kind = p.st.beam;
  ctx.save(); ctx.lineJoin = 'miter'; ctx.lineCap = 'square';
  if (kind === 'arc' || kind === 'chain') {
    const strands = kind === 'chain' ? 2 : 1;
    for (let s = 0; s < strands; s++) {
      boltPath(x0, y0, x1, y1, 7, 9 * z); ctx.strokeStyle = 'rgba(90,150,255,.55)'; ctx.lineWidth = 5 * z; ctx.stroke();
      boltPath(x0, y0, x1, y1, 7, 7 * z); ctx.strokeStyle = '#e8f4ff'; ctx.lineWidth = 2 * z; ctx.stroke();
    }
  } else if (kind === 'ray') {
    ctx.globalAlpha = 1 - k * 0.6;
    ctx.strokeStyle = 'rgba(40,220,255,.5)'; ctx.lineWidth = 8 * z; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    ctx.strokeStyle = '#eaffff'; ctx.lineWidth = 2.5 * z; ctx.stroke();
  } else {                    // vine：藤鞭从塔里抽出去，越抽越长，带刺
    const L = Math.min(1, k * 1.6), n = 14;
    ctx.strokeStyle = '#2a4416'; ctx.lineWidth = 5 * z; ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const u = i / n * L, w = Math.sin(u * 9 + p.t * 30) * 6 * z * (1 - u);
      const px = x0 + (x1 - x0) * u, py = y0 + (y1 - y0) * u + w;
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.stroke(); ctx.strokeStyle = '#6f9a3a'; ctx.lineWidth = 2.5 * z; ctx.stroke();
    ctx.fillStyle = '#d8e8a0';
    for (let i = 2; i <= n; i += 3) { const u = i / n * L; ctx.fillRect(x0 + (x1 - x0) * u - z, y0 + (y1 - y0) * u - 4 * z, 2 * z, 2 * z); }
  }
  ctx.restore();
}

/** 蜂群：一小团虫子绕着弹道点乱飞 */
function drawSwarm(p, x, y) {
  const z = G.zoom, n = p.st.n || 5, b = Math.max(2, Math.round(2 * z));
  for (let i = 0; i < n; i++) {
    const a = i * 2.4 + p.t * (9 + i), r = (4 + (i % 3) * 4) * z;
    const bx = Math.round(x + Math.cos(a) * r - (p.side ? -1 : 1) * i * 2 * z), by = Math.round(y + Math.sin(a * 1.3) * r * 0.7);
    ctx.fillStyle = '#1a1408'; ctx.fillRect(bx - b, by - b / 2, b * 2, b);
    ctx.fillStyle = p.st.swarm; ctx.fillRect(bx - b / 2, by - b / 2, b, b);
    if ((Math.floor(p.t * 40) + i) & 1) { ctx.fillStyle = 'rgba(255,255,255,.8)'; ctx.fillRect(bx - b / 2, by - b, b, b / 2); }
  }
}

function drawProjs() {
  const z = G.zoom, ready = FX_IMG.complete && FX_IMG.naturalWidth;
  ctx.lineCap = 'round';
  for (const p of G.projs) {
    const q = projPos(p), b = projAt(p, p.t - 0.05);
    const x = sx(q.x), y = sy(q.y), bx = sx(b.x), by = sy(b.y);
    const st = p.st || {};
    if (st.beam) { drawBeam(p); continue; }
    if (st.swarm) { drawSwarm(p, x, y); continue; }
    if (ready && FX_META[st.f]) {
      if (st.f === 'ball' || st.f === 'bomb') {   // 铁球 / 航弹：后面拖一串灰烟
        for (let i = 1; i <= 3; i++) {
          const s = projAt(p, p.t - i * 0.05), r = Math.round((2 + i) * z * (st.s || 1));
          ctx.fillStyle = `rgba(110,104,98,${0.5 - i * 0.13})`; ctx.fillRect(Math.round(sx(s.x)) - r, Math.round(sy(s.y)) - r, r * 2, r * 2);
        }
      }
      const still = Math.abs(x - bx) + Math.abs(y - by) < 0.01;   // 刚发射的第一帧还没有方向
      drawFly(st.f, x, y, still ? (p.side ? Math.PI : 0) : Math.atan2(y - by, x - bx), st.s || 1, p.t);
      continue;
    }
    // 下面是图还没加载出来时的兜底画法
    if (p.tower) {
      const pal = towerPal(p.age);
      if (p.tower === 3) {    // 重塔：铁球 + 烟尾
        for (let i = 1; i <= 3; i++) { const s = projAt(p, p.t - i * 0.05); ctx.fillStyle = `rgba(90,85,80,${0.45 - i * 0.12})`; ctx.beginPath(); ctx.arc(sx(s.x), sy(s.y), (3 + i) * z, 0, 7); ctx.fill(); }
        ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(x, y, 6 * z, 0, 7); ctx.fill();
        ctx.fillStyle = pal.metal; ctx.fillRect(x - 3 * z, y - 3 * z, 2.5 * z, 2.5 * z);
      } else {                // 轻塔：亮色曳光；中塔：粗一点的弩箭 / 弹头
        const mid = p.tower === 2;
        ctx.strokeStyle = mid ? pal.dark : 'rgba(255,230,160,.55)'; ctx.lineWidth = (mid ? 4 : 3) * z;
        ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(x, y); ctx.stroke();
        ctx.strokeStyle = mid ? pal.metal : '#fff6d0'; ctx.lineWidth = (mid ? 2 : 1.5) * z;
        ctx.beginPath(); ctx.moveTo((x + bx) / 2, (y + by) / 2); ctx.lineTo(x, y); ctx.stroke();
      }
      continue;
    }
    // 兵的弹道：时代色弹头 + 一小段拖尾
    let col = AGE_COL[p.age];
    if (p.age === 4 || p.age === 10) col = SIDE_COL[p.side].light;
    ctx.globalAlpha = 0.45; ctx.strokeStyle = col; ctx.lineWidth = (p.splash ? 5 : 2.5) * z;
    ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(x, y); ctx.stroke(); ctx.globalAlpha = 1;
    ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(x, y, Math.max(2.5, (p.splash ? 6 : 3) * z) + 1, 0, 7); ctx.fill();
    ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x, y, Math.max(2, (p.splash ? 6 : 3) * z), 0, 7); ctx.fill();
  }
  ctx.lineCap = 'butt';
  drawShells();
}

// ---------- 大招 ----------
/** 落点标记：地上一圈阵营色的准星，炮弹越近圈越亮、越收紧 */
function drawReticle(s, k) {
  const z = G.zoom, x = sx(s.x), y = sy(0), r = SPECIAL_RADIUS * z * (1.5 - 0.5 * k);
  const col = SIDE_COL[s.side].light;
  ctx.globalAlpha = 0.12 + 0.18 * k; ctx.fillStyle = col;
  ctx.beginPath(); ctx.ellipse(x, y, r, r * 0.22, 0, 0, 7); ctx.fill();
  ctx.globalAlpha = 0.35 + 0.55 * k; ctx.strokeStyle = col; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.ellipse(x, y, r, r * 0.22, 0, 0, 7); ctx.stroke();
  ctx.fillRect(x - r - 4, y - 1, 8, 2); ctx.fillRect(x + r - 4, y - 1, 8, 2); ctx.fillRect(x - 1, y - r * 0.22 - 4, 2, 6);
  ctx.globalAlpha = 1;
}
// 大招弹体：全部用 pixelfx 飞行体（FX_META kind:'fly'），[名字, 缩放, 几发并排]
const SHELL_FLY = {
  meteor: ['fireball', 2.4, 1], arrow: ['arrow', 1.6, 5], shell: ['bomb', 3, 1], nuke: ['rocket_y', 1.7, 1],
  beam: ['laser_b', 2.2, 1], drone: ['rocket', 1.1, 3], spore: ['plasma_s', 2.4, 1],
};

function drawShells() {
  if (!FX_IMG.complete || !FX_IMG.naturalWidth) { for (const s of G.shells) drawReticle(s, Math.min(1, s.t / s.fall)); return; }
  const z = G.zoom, now = performance.now() / 1000;
  for (const s of G.shells) {
    const k = Math.min(1, s.t / s.fall), dir = s.side ? -1 : 1;
    drawReticle(s, k);
    const style = SHELL_STYLE[s.age];
    if (style === 'bolt') {          // 雷暴：落点上空聚起一团 pixelfx 雷云（越来越浓），落地时由 sim.js 放落雷 + 电震波
      ctx.globalAlpha = Math.min(1, 0.25 + k * 1.2);
      drawFly('cloud', sx(s.x), sy(-230), 0, 0.8 + 0.4 * k, now + s.x);
      ctx.globalAlpha = 1;
      continue;
    }
    // 光束从正上方直落，其余斜着砸下来
    const sk = style === 'beam' ? 0 : 140;
    const x = sx(s.x - dir * sk * (1 - k)), y = sy(-620 * (1 - k));
    const ang = Math.atan2(620, dir * sk);
    // 弹体大小不随镜头缩放变小（放大招时镜头会拉远），最小 1.3 倍
    const b = Math.max(1.3, z * 1.3) / z;
    const [key, sc, n] = SHELL_FLY[style];
    for (let i = 0; i < n; i++) {
      const off = (i - (n - 1) / 2) * 15 * z * b;
      drawFly(key, x + off, y - Math.abs(off) * 0.8, ang, sc * b / 1.3, now + i * 0.13 + s.x);
    }
  }
}

/** 大招落点留在地上的燃烧圈 / 毒池（pixelfx，在兵之前画，压在兵脚下） */
function drawScorch() {
  for (const f of G.fx) if (f.kind === 'pfx' && FX_UNDER[f.name]) drawHitFx(f);
}

// ---------- 大招释放横幅（HUD 层） ----------
/** 横幅总时长 / 闪屏时长（秒，真实时间） */
const CAST_T = 1.8, CAST_FLASH_T = 0.3;
function drawCastBanner() {
  const c = G.castFx; if (!c) return;
  const e = CAST_T - c.t;                     // 已经过的秒数
  if (e < CAST_FLASH_T) { ctx.globalAlpha = 0.35 * (1 - e / CAST_FLASH_T); ctx.fillStyle = AGE_COL[c.era]; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
  const inK = Math.min(1, e / 0.18), outK = Math.min(1, c.t / 0.35);
  const mine = c.side === 0, y = 250, h = 74;   // 在两边基地血条下面、地面上方的天空里
  ctx.globalAlpha = outK;
  // 横向的条带：中间实、两头渐隐
  const band = ctx.createLinearGradient(0, 0, W, 0);
  const tint = mine ? '20,14,6' : '26,8,20';
  band.addColorStop(0, `rgba(${tint},0)`); band.addColorStop(0.25, `rgba(${tint},.86)`); band.addColorStop(0.75, `rgba(${tint},.86)`); band.addColorStop(1, `rgba(${tint},0)`);
  const sy0 = y - h / 2 * inK;
  ctx.fillStyle = band; ctx.fillRect(0, sy0, W, h * inK);
  const edge = mine ? '#d8a64a' : '#c35aa0';
  const eg = ctx.createLinearGradient(0, 0, W, 0);
  eg.addColorStop(0, 'rgba(0,0,0,0)'); eg.addColorStop(0.3, edge); eg.addColorStop(0.7, edge); eg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = eg; ctx.fillRect(0, sy0, W, 3); ctx.fillRect(0, sy0 + h * inK - 3, W, 3);
  if (inK >= 1) {
    const slide = (1 - Math.min(1, (e - 0.18) / 0.22)) * (mine ? -60 : 60);
    ctx.textAlign = 'center';
    ctx.font = UI.font(UI.fs.s, true);
    outlined(mine ? `${SIDE_COL[0].name} · 大招` : `⚠ ${SIDE_COL[1].name}释放大招`, W / 2 + slide * 0.5, y - 14, mine ? '#f6d98e' : '#ffb0d8', 3);
    ctx.font = UI.font(40, true);
    const g = ctx.createLinearGradient(0, y - 6, 0, y + 30);
    g.addColorStop(0, mine ? '#fff4c8' : '#ffe0f0'); g.addColorStop(0.55, mine ? '#f0b850' : '#ff7ab8'); g.addColorStop(1, mine ? '#9a5a1c' : '#8a2a60');
    outlined(SPECIAL_NAMES[c.era] + '！', W / 2 + slide, y + 26, g, 6);
    ctx.textAlign = 'left';
  }
  ctx.globalAlpha = 1;
}
