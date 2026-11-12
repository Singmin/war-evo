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

function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
// 面板外观跟着时代皮肤走（js/ui/skins.js）
function panel(x, y, w, h) { skinPanel(x, y, w, h); }
// 描边文字：画在战场上方时保证看得清
function outlined(str, x, y, fill, lw = 4) { ctx.lineWidth = lw; ctx.strokeStyle = '#000'; ctx.strokeText(str, x, y); ctx.fillStyle = fill; ctx.fillText(str, x, y); }

// ---------- 我方资源面板 ----------
function drawResources(me, op) {
  const { x, y, w, h } = HUD_LAYOUT.res;
  panel(x, y, w, h);
  // 第 1 行：金币 + 每秒收入
  ctx.fillStyle = UI.col.gold; ctx.beginPath(); ctx.arc(x + 24, y + 28, 12, 0, 7); ctx.fill();
  ctx.fillStyle = '#b8860b'; ctx.beginPath(); ctx.arc(x + 24, y + 28, 6, 0, 7); ctx.fill();
  ctx.textAlign = 'left'; ctx.font = UI.font(36, true); ctx.fillStyle = UI.col.gold;
  const gold = String(Math.floor(me.gold));
  ctx.fillText(gold, x + 44, y + 41);
  const gw = ctx.measureText(gold).width;
  ctx.font = UI.font(UI.fs.s, true); ctx.fillStyle = UI.col.good;
  ctx.fillText(`+${incomeOf(me).toFixed(1)}/秒${me.mine ? `  采矿 Lv${me.mine}` : ''}`, x + 54 + gw, y + 39);
  // 第 2 行：经验条 + 科技点
  const thr = ptNeed(me), bx = x + 12, by = y + 54, bw = 222, bh = 24;
  ctx.fillStyle = UI.col.track; roundRect(bx, by, bw, bh, 6); ctx.fill();
  const ef = bw * Math.min(1, me.exp / thr);
  if (ef >= 8) { ctx.fillStyle = UI.col.tech; roundRect(bx, by, ef, bh, 6); ctx.fill(); }
  ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = 'center';
  outlined(`经验 ${Math.floor(me.exp)} / ${thr}`, bx + bw / 2, by + 19, '#fff', 3);
  ctx.textAlign = 'left'; ctx.font = UI.font(UI.fs.m, true); ctx.fillStyle = UI.col.tech;
  ctx.fillText(`科技点 ${me.pts}`, bx + bw + 12, by + 21);
  // 第 3 行：5 个时代格。上半 = 我方，下半 = 敌方；没到的时代显示问号
  for (let i = 0; i < 5; i++) {
    const cx = x + 12 + i * 70, cy = y + 88, cw = 64, ch = 30;
    ctx.fillStyle = UI.col.track; ctx.fillRect(cx, cy, cw, ch);
    if (i <= me.age) { ctx.fillStyle = SIDE_COL[0].body; ctx.fillRect(cx, cy, cw, ch / 2); }
    if (i <= op.age) { ctx.fillStyle = SIDE_COL[1].body; ctx.fillRect(cx, cy + ch / 2, cw, ch / 2); }
    ctx.strokeStyle = i === me.age ? UI.col.gold : UI.col.edge; ctx.lineWidth = i === me.age ? 3 : 1.5; ctx.strokeRect(cx, cy, cw, ch);
    const pe = me.path.find(e => ERA_TIER[e] === i);
    ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = 'center';
    outlined(pe !== undefined ? AGES[pe].slice(0, 2) : '？', cx + cw / 2, cy + 22, '#fff', 3);
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
    ctx.fillStyle = 'rgba(0,0,0,.55)'; roundRect(x, by, L.w, L.barH, 6); ctx.fill();
    const fw = L.w * frac;
    if (fw > 1) {
      ctx.fillStyle = sd.flash > 0 ? '#fff' : (right ? UI.col.foeHp : UI.col.meHp);
      roundRect(right ? x + L.w - fw : x, by, fw, L.barH, 6); ctx.fill();
    }
    ctx.strokeStyle = 'rgba(0,0,0,.6)'; ctx.lineWidth = 2; roundRect(x, by, L.w, L.barH, 6); ctx.stroke();
    ctx.font = UI.font(UI.fs.s, true); ctx.textAlign = 'center';
    outlined(`基地 ${Math.ceil(sd.baseHp)} / ${BASE_HP[sd.age]}`, x + L.w / 2, by + 20, '#fff', 3);
  });
  ctx.textAlign = 'left';
}

// ---------- 小地图 + 训练条 ----------
function drawMinimap() {
  const { x: mx, y: my, w: mw, h: mh } = HUD_LAYOUT.mini, k = mw / WORLD;
  panel(mx - 4, my - 4, mw + 8, mh + 8);
  ctx.fillStyle = SIDE_COL[0].body; ctx.fillRect(mx, my, BASE_L * k, mh);
  ctx.fillStyle = SIDE_COL[1].body; ctx.fillRect(mx + BASE_R * k, my, (WORLD - BASE_R) * k, mh);
  const row = (mh - 4) / UNIT_BASE.length;
  for (const u of G.units) { ctx.fillStyle = u.side ? UI.col.foe : UI.col.me; ctx.fillRect(mx + u.x * k - 2, my + 2 + u.type * row, 4, Math.min(5, row)); }
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(mx + G.camX * k, my, (W / G.zoom) * k, mh);
}
function drawTraining(me) {
  const { x, y, w, h } = HUD_LAYOUT.train, base = y + h / 2 + 8;
  panel(x, y, w, h);
  ctx.font = UI.font(UI.fs.m); ctx.textAlign = 'left';
  if (me.evolveT > 0) { ctx.fillStyle = UI.col.gold; ctx.fillText(`跃迁中…… ${me.evolveT.toFixed(1)} 秒（训练暂停）`, x + 14, base); }
  else if (me.queue.length) {
    const q = me.queue[0], st = unitStats(q.type, q.age, me);   // q.age = 时代编号
    ctx.fillStyle = UI.col.text; ctx.fillText(st.name, x + 14, base);
    const px = x + 190, pw = 220;
    ctx.fillStyle = UI.col.track; roundRect(px, y + 13, pw, 16, 5); ctx.fill();
    const tf = pw * Math.min(1, me.trainT / st.train);
    if (tf >= 6) { ctx.fillStyle = UI.col.train; roundRect(px, y + 13, tf, 16, 5); ctx.fill(); }
    if (me.trainT >= st.train) { ctx.font = UI.font(UI.fs.xs, true); outlined(G.units.filter(u => u.side === 0).length >= MAX_UNITS ? '场上已满 20 人' : '等待出门', px + 10, y + 28, UI.col.bad, 3); }
  } else { ctx.fillStyle = UI.col.dim; ctx.fillText('训练队列空闲', x + 14, base); }
  // 队列格子
  for (let i = 0; i < QUEUE_MAX; i++) {
    const qx = x + w - 14 - (QUEUE_MAX - i) * 34, qy = y + 7;
    ctx.strokeStyle = '#a58a66'; ctx.lineWidth = 2; ctx.strokeRect(qx, qy, 28, 28);
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
    outlined(G.toast.str, Math.max(W / 2, TOAST_LEFT + tw / 2), 230,G.toast.side < 0 ? '#ff7a5c' : G.toast.side ? '#c9a7ff' : UI.col.me, 7);
    ctx.globalAlpha = 1;
  }
  if (G.echo) {
    ctx.globalAlpha = Math.min(1, G.echo.t);
    ctx.fillStyle = 'rgba(8,10,24,.85)'; roundRect(W / 2 - 400, 300, 800, 76, 14); ctx.fill();
    ctx.strokeStyle = '#5ff7ff'; ctx.lineWidth = 2; ctx.stroke();
    ctx.font = UI.font(26); ctx.fillStyle = '#bff8ff';
    ctx.fillText(`回声：“${G.echo.str}”`, W / 2, 347);
    ctx.globalAlpha = 1;
  }
  ctx.textAlign = 'left';
}

function drawHUD() {
  const me = G.sides[0], op = G.sides[1];
  hudAt(0, () => drawResources(me, op));
  drawSides();
  hudAt(W / 2, () => { drawMinimap(); drawTraining(me); }, MID_SCALE);
  if (S.screen === 'play') { drawCastBanner(); drawMessages(); }   // 暂停 / 结算等覆盖页上不画大字提示，免得透过来压住标题
}

$('btnPause').onclick = () => pause();
$('btnSpeed').onclick = () => cycleSpeed();
