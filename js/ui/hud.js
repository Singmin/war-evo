'use strict';
// 局内 HUD（画在画布上）+ 右上角按钮
// 布局（1280×720 逻辑像素）：
//   左上 = 我方资源面板（金币 / 收入、经验 / 科技点、时代格）
//   左上面板下面 = 我方阵营、时代和基地血条；右上按钮下面 = 敌方的（对称）
//   顶部中间 = 小地图 + 训练条；它们下面是操作提示（css/hud.css 的 #info）
//   我方血条下面 = 看广告按钮（css/hud.css 的 #adBtns）
const HUD_LAYOUT = {
  res: { x: 8, y: 8, w: 372, h: 128 },          // 资源面板
  side: { y: 146, w: 372, barH: 26 },           // 阵营 + 基地血条（左右各一）
  mini: { x: 400, y: 12, w: 600, h: 30 },       // 小地图（input.js 用它判断点击）
  train: { x: 396, y: 50, w: 608, h: 42 },      // 训练条
};
// 整个顶栏按这个比例缩小（手机上不挡战场）。左边的面板以左上角为基准缩，右边以右上角，中间以顶部中点
// 上面的坐标都是缩放前的；看广告按钮、提示文字的位置在 css/hud.css 里，改比例时一起改
const HUD_SCALE = 0.9;
const MID_SCALE = 0.8;     // 顶部中间的小地图 + 训练条再小一点，少挡战场
function hudAt(ax, fn, k = HUD_SCALE) { ctx.save(); ctx.translate(ax, 0); ctx.scale(k, k); ctx.translate(-ax, 0); fn(); ctx.restore(); }
// 小地图在屏幕上的实际位置（缩放后），input.js 判断点击用
function miniRect() {
  const m = HUD_LAYOUT.mini, k = MID_SCALE, c = W / 2;
  return { x: c + (m.x - c) * k, y: m.y * k, w: m.w * k, h: m.h * k };
}

const HUD_INK = '#1a120b';
// 四向硬描边：在天空和材质底板上都能看清。
function outlined(str, x, y, fill, offset = 2) {
  ctx.fillStyle = HUD_INK;
  ctx.fillText(str, x - offset, y);
  ctx.fillText(str, x + offset, y);
  ctx.fillText(str, x, y - offset);
  ctx.fillText(str, x, y + offset);
  ctx.fillStyle = fill;
  ctx.fillText(str, x, y);
}

function pixelMeter(x, y, w, h, fraction, color, fromRight = false) {
  ctx.fillStyle = HUD_INK;
  ctx.fillRect(x, y, w, h);
  ctx.fillStyle = '#392b20';
  ctx.fillRect(x + 2, y + 2, w - 4, h - 4);
  if (!(fraction > 0)) return;
  const fill = Math.max(2, Math.round((w - 4) * Math.min(fraction, 1) / 2) * 2);
  const left = fromRight ? x + w - 2 - fill : x + 2;
  ctx.fillStyle = color;
  ctx.fillRect(left, y + 2, fill, h - 4);
  ctx.fillStyle = '#fff6';
  ctx.fillRect(left, y + 2, fill, 4);
}

// ---------- 我方资源面板 ----------
function drawResources(me, op) {
  const { x, y, w, h } = HUD_LAYOUT.res;
  skinPanel(x, y, w, h);
  // 第 1 行：金币 + 每秒收入
  ctx.fillStyle = HUD_INK;
  ctx.fillRect(x + 16, y + 16, 16, 24); ctx.fillRect(x + 12, y + 20, 24, 16);
  ctx.fillStyle = UI.col.gold;
  ctx.fillRect(x + 16, y + 20, 16, 16); ctx.fillRect(x + 18, y + 18, 12, 20);
  ctx.fillStyle = '#ffeb9c'; ctx.fillRect(x + 18, y + 20, 12, 4);
  ctx.fillStyle = '#9e5e1c'; ctx.fillRect(x + 22, y + 24, 4, 8);
  ctx.textAlign = 'left'; ctx.font = UI.font(36, true); ctx.fillStyle = UI.col.gold;
  const gold = String(Math.floor(me.gold));
  outlined(gold, x + 44, y + 41, UI.col.gold);
  const gw = ctx.measureText(gold).width;
  ctx.font = UI.font(UI.fs.s, true); ctx.fillStyle = UI.col.good;
  outlined(`+${incomeOf(me).toFixed(1)}/秒${me.mine ? `  采矿 Lv${me.mine}` : ''}${me.drill ? `  练兵 Lv${me.drill}` : ''}`, x + 54 + gw, y + 39, UI.col.good, 1);
  // 第 2 行：经验条 + 科技点
  const thr = ptNeed(me), bx = x + 12, by = y + 54, bw = 222, bh = 24;
  pixelMeter(bx, by, bw, bh, me.exp / thr, UI.col.tech);
  ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = 'center';
  outlined(`经验 ${Math.floor(me.exp)} / ${thr}`, bx + bw / 2, by + 19, '#fff');
  ctx.textAlign = 'left'; ctx.font = UI.font(UI.fs.m, true); ctx.fillStyle = UI.col.tech;
  outlined(`科技点 ${me.pts}`, bx + bw + 12, by + 21, UI.col.tech, 1);
  // 第 3 行：5 个时代格。上半 = 我方，下半 = 敌方；没到的时代显示问号
  for (let i = 0; i < 5; i++) {
    const cx = x + 12 + i * 70, cy = y + 88, cw = 64, ch = 30;
    ctx.fillStyle = HUD_INK; ctx.fillRect(cx, cy, cw, ch);
    ctx.fillStyle = UI.col.track; ctx.fillRect(cx + 2, cy + 2, cw - 4, ch - 4);
    if (i <= me.age) { ctx.fillStyle = SIDE_COL[0].body; ctx.fillRect(cx + 2, cy + 2, cw - 4, 12); }
    if (i <= op.age) { ctx.fillStyle = SIDE_COL[1].body; ctx.fillRect(cx + 2, cy + 14, cw - 4, 14); }
    ctx.fillStyle = i === me.age ? UI.col.gold : '#fff4d74d';
    ctx.fillRect(cx + 2, cy + 2, cw - 4, 2);
    if (i === me.age) {
      ctx.fillRect(cx + 2, cy + ch - 4, cw - 4, 2);
      ctx.fillRect(cx + 2, cy + 4, 2, ch - 8);
      ctx.fillRect(cx + cw - 4, cy + 4, 2, ch - 8);
    }
    const pe = me.path.find(e => ERA_TIER[e] === i);
    ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = 'center';
    outlined(pe !== undefined ? AGES[pe].slice(0, 2) : '？', cx + cw / 2, cy + 22, '#fff');
  }
  ctx.textAlign = 'left';
}

// ---------- 双方阵营、时代、基地血条（左右对称）----------
function drawSides() {
  const L = HUD_LAYOUT.side;
  for (const sd of G.sides) hudAt(sd.s === 1 ? W : 0, () => {
    const right = sd.s === 1, x = right ? W - 8 - L.w : 8, frac = Math.max(0, sd.baseHp / BASE_HP[sd.age]);
    // 阵营 · 时代（路线）
    const lbl = `${SIDE_COL[sd.s].name} · ${AGES[sd.era]}${sd.route ? '（' + ROUTES[sd.route].name + '）' : ''}`;
    ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = right ? 'right' : 'left';
    outlined(lbl, right ? W - 10 : 10, L.y + 18, right ? UI.col.foe : UI.col.me);
    // 血条：我方从左往右，敌方从右往左
    const by = L.y + 26;
    pixelMeter(x, by, L.w, L.barH, frac, sd.flash > 0 ? '#fff' : (right ? UI.col.foeHp : UI.col.meHp), right);
    ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = 'center';
    outlined(`基地 ${Math.ceil(sd.baseHp)} / ${BASE_HP[sd.age]}`, x + L.w / 2, by + 20, '#fff');
  });
  ctx.textAlign = 'left';
}

// ---------- 小地图 + 训练条 ----------
function drawMinimap() {
  const { x: mx, y: my, w: mw, h: mh } = HUD_LAYOUT.mini, k = mw / WORLD;
  skinPanel(mx - 4, my - 4, mw + 8, mh + 8);
  const left = Math.round(BASE_L * k / 2) * 2, right = Math.round(BASE_R * k / 2) * 2;
  ctx.fillStyle = SIDE_COL[0].body; ctx.fillRect(mx, my + 2, left, mh - 4);
  ctx.fillStyle = SIDE_COL[1].body; ctx.fillRect(mx + right, my + 2, mw - right, mh - 4);
  ctx.fillStyle = '#fff5';
  ctx.fillRect(mx, my + 2, left, 4); ctx.fillRect(mx + right, my + 2, mw - right, 4);
  for (const u of G.units) {
    ctx.fillStyle = u.side ? UI.col.foe : UI.col.me;
    ctx.fillRect(mx + Math.round(u.x * k / 2) * 2 - 2, my + 2 + u.type * 4, 4, 4);
  }
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(mx + G.camX * k, my, (W / G.zoom) * k, mh);
}
function drawTraining(me) {
  const { x, y, w, h } = HUD_LAYOUT.train, base = y + h / 2 + 8;
  skinPanel(x, y, w, h);
  ctx.font = UI.font(UI.fs.m); ctx.textAlign = 'left';
  if (me.evolveT > 0) { outlined(`跃迁中…… ${me.evolveT.toFixed(1)} 秒（训练暂停）`, x + 14, base, UI.col.gold, 1); }
  else if (me.queue.length) {
    const q = me.queue[0], st = unitStats(q.type, q.age, me);   // q.age = 时代编号
    outlined(st.name, x + 14, base, UI.col.text, 1);
    const px = x + 190, pw = 220;
    pixelMeter(px, y + 12, pw, 16, me.trainT / st.train, UI.col.train);
    if (me.trainT >= st.train) { ctx.font = UI.font(UI.fs.xs, true); outlined(G.units.filter(u => u.side === 0 && !u.dead).length >= MAX_UNITS ? `场上已满 ${MAX_UNITS} 人` : '等待出门', px + 10, y + 28, UI.col.bad); }
  } else { outlined('训练队列空闲', x + 14, base, UI.col.dim, 1); }
  // 队列格子
  for (let i = 0; i < QUEUE_MAX; i++) {
    const qx = x + w - 14 - (QUEUE_MAX - i) * 34, qy = y + 6;
    ctx.fillStyle = HUD_INK; ctx.fillRect(qx, qy, 28, 28);
    ctx.fillStyle = me.queue[i] ? '#52361d' : '#2b231a'; ctx.fillRect(qx + 2, qy + 2, 24, 24);
    ctx.fillStyle = '#fff4d74d'; ctx.fillRect(qx + 2, qy + 2, 24, 2);
    if (me.queue[i]) { ctx.fillStyle = UI.col.me; ctx.font = UI.font(UI.fs.xs, true); ctx.textAlign = 'center'; ctx.fillText(TYPE_SHORT[me.queue[i].type], qx + 14, qy + 21); ctx.textAlign = 'left'; }
  }
}

// ---------- 屏幕中间的大字提示、回声台词 ----------
/** 大字提示左缘最小 x（逻辑像素），避开左侧看广告按钮 */
const TOAST_LEFT = 300;
function drawMessages() {
  ctx.textAlign = 'center';
  if (G.toast) {
    ctx.globalAlpha = Math.min(1, G.toast.t);
    ctx.font = UI.font(34, true);
    // 左边是看广告按钮（右缘约 x=280），长提示往右让开，不压在按钮上
    const tw = ctx.measureText(G.toast.str).width;
    outlined(G.toast.str, Math.max(W / 2, TOAST_LEFT + tw / 2), 230, G.toast.side < 0 ? '#ff7a5c' : G.toast.side ? '#c9a7ff' : UI.col.me);
    ctx.globalAlpha = 1;
  }
  if (G.echo) {
    ctx.globalAlpha = Math.min(1, G.echo.t);
    ctx.fillStyle = HUD_INK; pixelPanelShape(ctx, W / 2 - 400, 300, 800, 76);
    ctx.fillStyle = '#112134'; ctx.fillRect(W / 2 - 392, 304, 784, 68);
    ctx.fillStyle = '#5ff7ff'; ctx.fillRect(W / 2 - 392, 304, 784, 2);
    ctx.font = UI.font(26);
    outlined(`回声：“${G.echo.str}”`, W / 2, 347, '#bff8ff', 1);
    ctx.globalAlpha = 1;
  }
  ctx.textAlign = 'left';
}

// ---------- 右侧操作按钮让开宿主右上角的胶囊 ----------
// 坐标都是 1280×720 逻辑像素；按钮本身的位置在 css/hud.css 的 #topR
const TOP_BTNS = {
  right: 10, top: 10, w: 176, h: 76,   // 两个按钮合起来占的范围（和 css 一致）
  gap: 10,                             // 让开后和胶囊之间留的空
  minLeft: 940,                        // 最多左移到这里（再往左就压到训练条）
  // 宿主里读不到胶囊位置时按这个估（屏幕像素，贴右上角）：微信系胶囊约 87×32，外加边距
  fallback: { w: 96, h: 44 },
};
let topBtnsKey = '';
/** 宿主胶囊按钮的屏幕位置；不在 TapTap 里返回 null */
function capsuleRect() {
  const sdk = window.tap;
  if (!sdk) return null;
  try {
    const r = typeof sdk.getMenuButtonBoundingClientRect === 'function' && sdk.getMenuButtonBoundingClientRect();
    if (r && r.width > 0 && r.height > 0) return r;
  } catch (e) { /* 读不到就用估计值 */ }
  const f = TOP_BTNS.fallback, vw = window.innerWidth;
  return { left: vw - f.w, right: vw, top: 0, bottom: f.h, width: f.w, height: f.h };
}
/**
 * 胶囊压到倍速 / 暂停键时，把两个键整体左移到胶囊左边。画面缩放变了才重算；
 * force = true 强制重算（胶囊位置可能晚一点才读得到）
 */
function syncTopButtons(force) {
  const key = gameEl.style.transform;
  if (!force && key === topBtnsKey) return;
  topBtnsKey = key;
  const B = TOP_BTNS, c = capsuleRect(), g = gameEl.getBoundingClientRect(), k = g.width / W;
  let shift = 0, sideTop = 186;
  if (c && k > 0) {
    const left = (c.left - g.left) / k, top = (c.top - g.top) / k, bottom = (c.bottom - g.top) / k;
    // 右侧按钮低于常规胶囊。宿主回报更靠下的位置时，整组再往下让。
    const hit = left < W - B.right && top < B.top + B.h && bottom > B.top;
    if (hit) shift = Math.min(W - B.right - B.w - B.minLeft, Math.max(0, W - B.right - left + B.gap));
    if (left < W - 8 && top < sideTop + 138 && bottom > sideTop) sideTop = bottom + B.gap;
  }
  gameEl.style.setProperty('--capsule-shift', Math.round(shift) + 'px');
  gameEl.style.setProperty('--side-actions-top', Math.ceil(sideTop) + 'px');
}
[500, 2000].forEach(ms => setTimeout(() => syncTopButtons(true), ms));

function drawHUD() {
  syncTopButtons();
  if (S.screen === 'tree') return;
  const me = G.sides[0], op = G.sides[1];
  hudAt(0, () => drawResources(me, op));
  drawSides();
  hudAt(W / 2, () => { drawMinimap(); drawTraining(me); }, MID_SCALE);
  if (S.screen === 'play') { drawCastBanner(); drawMessages(); }   // 暂停 / 结算等覆盖页上不画大字提示，免得透过来压住标题
}

$('btnPause').onclick = () => pause();
$('btnSpeed').onclick = () => cycleSpeed();
$('btnGameGuide').onclick = () => { if (S.screen === 'play' && G && !G.over) openGuide(true); };
