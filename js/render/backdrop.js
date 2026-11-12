'use strict';
// 战场背景：分层视差的像素风远景
//   天空（日 / 月、云、星）→ 远山（或海）→ 旧世界废墟 → 地平线雾 → 本时代的建筑 → 近处碎石草丛 → 地面
// 全部用代码画（没有新图片），按 BG_PX 个逻辑像素一个点画在小画布上，再不插值放大，和兵的像素风一致。
// 每个时代的图层只生成一次并缓存，之后每帧只贴 6 张图。

/** 背景的像素块大小（逻辑像素） */
const BG_PX = 3;
/** 视差：镜头移动 1 像素时各层移动多少 */
const BG_PAR = { far: 0.2, mid: 0.45, near: 0.8 };
/** 地面画布向下多画的高度（开始页演示局把战场抬高时用，见 js/ui/attract.js 的 DEMO_LIFT） */
const BG_DEPTH = 220;
/** 镜头最多能移动的距离（缩放后的屏幕像素），决定各层画布要多宽 */
const BG_PAN = WORLD - W;

/**
 * 每个时代的布景（下标 = 时代编号，和 AGES 对应）
 * props: 中景里的时代建筑；vines: 废墟上长藤蔓；grass: 地面长草；sea: 远景是海；blimps: 天上有飞艇；lamps: 近景路灯
 */
const BG_THEME = [
  { props: ['huts'], vines: 1, grass: 1 },          // 部落纪
  { props: ['ziggurat', 'obelisk'] },               // 青铜纪
  { props: ['chimney'] },                           // 蒸汽纪
  { props: ['pylon', 'factory', 'pylon'], lamps: 1 }, // 电气纪：电塔连成一线，中间夹砖厂房；近景有路灯
  { props: ['mech', 'pylon'] },                     // 机甲纪
  { props: ['tree'], vines: 1, grass: 1 },          // 驯兽纪
  { props: ['pod', 'tree'], vines: 1, grass: 1 },   // 生化纪
  { props: ['windmill', 'fort'] },                  // 火药纪
  { props: ['ship', 'fort'], sea: 1 },              // 帆船纪（船画在远景海上，中景是港口城墙）
  { props: ['cooling'] },                           // 核能纪
  { props: ['monolith'] },                          // 智械纪
  { props: ['mushroom', 'tree'], vines: 1, grass: 1 }, // 共生纪
  { props: ['bones', 'tree'], grass: 1 },           // 巨兽纪
  { props: ['hive'] },                              // 蜂群纪
  { props: ['ship', 'chimney'], sea: 1 },           // 铁甲舰纪
  { props: ['hangar'], blimps: 1 },                 // 航空纪
  { props: ['flag', 'huts'] },                      // 远征纪
];

// ---------- 小工具 ----------
function bgHex(c) { const n = parseInt(c.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; }
/** 两个 #rrggbb 颜色按 t 混合 */
function bgMix(a, b, t) {
  const A = bgHex(a), B = bgHex(b);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('');
}
/** 固定种子的随机数：同一时代每次生成的背景都一样 */
function bgRng(seed) { let s = (seed * 7919 + 13) % 233280; return () => (s = (s * 9301 + 49297) % 233280) / 233280; }
function bgCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }
/** 实心像素圆 */
function pDisc(x, cx, cy, r) { for (let dy = -r; dy <= r; dy++) { const dx = Math.floor(Math.sqrt(r * r - dy * dy)); x.fillRect(cx - dx, cy + dy, dx * 2 + 1, 1); } }
/** 上半个像素圆（圆顶、土丘） */
function pDome(x, cx, cy, r) { for (let dy = -r; dy <= 0; dy++) { const dx = Math.floor(Math.sqrt(r * r - dy * dy)); x.fillRect(cx - dx, cy + dy, dx * 2 + 1, 1); } }
/** 1 像素宽的直线 */
function pLine(x, x0, y0, x1, y1) {
  const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0), 1);
  for (let i = 0; i <= n; i++) x.fillRect(Math.round(x0 + (x1 - x0) * i / n), Math.round(y0 + (y1 - y0) * i / n), 1, 1);
}
/** 烟：几团半透明的圆，往右上飘 */
function pSmoke(x, cx, cy, col, r) {
  x.fillStyle = col;
  for (let i = 0; i < 5; i++) { x.globalAlpha = 0.32 - i * 0.05; pDisc(x, cx + i * 3 + Math.floor(r() * 2), cy - i * 5, 2 + i); }
  x.globalAlpha = 1;
}

// ---------- 中景里的时代建筑：(画布, 中心 x, 地平线 y, 主色, 强调色, 随机数, 是否夜晚) ----------
const BG_PROPS = {
  huts(x, cx, gy, c, a, r) {          // 帐篷 + 炊烟
    for (let k = 0; k < 2; k++) {
      const hx = cx + k * 16, h = 10 + Math.floor(r() * 5);
      x.fillStyle = c; for (let i = 0; i < h; i++) x.fillRect(hx - Math.floor(i * 0.7), gy - h + i, Math.floor(i * 1.4) + 1, 1);
      x.fillStyle = a; x.fillRect(hx - 1, gy - 4, 3, 4);
    }
    pSmoke(x, cx + 8, gy - 16, '#d8d0c0', r);
  },
  ziggurat(x, cx, gy, c, a) {         // 阶梯神庙
    x.fillStyle = c; for (let i = 0; i < 5; i++) x.fillRect(cx - 18 + i * 4, gy - 5 - i * 5, 36 - i * 8, 5);
    x.fillStyle = a; x.fillRect(cx - 1, gy - 28, 3, 3);
  },
  obelisk(x, cx, gy, c, a) {          // 方尖碑
    x.fillStyle = c; x.fillRect(cx - 2, gy - 30, 5, 30); x.fillRect(cx - 1, gy - 32, 3, 2); x.fillRect(cx, gy - 33, 1, 1);
    x.fillStyle = a; x.fillRect(cx, gy - 24, 1, 8);
  },
  chimney(x, cx, gy, c, a, r) {       // 烟囱 + 黑烟
    for (let k = 0; k < 2; k++) {
      const hx = cx + k * 9, h = 30 + Math.floor(r() * 14);
      x.fillStyle = c; x.fillRect(hx - 2, gy - h, 5, h); x.fillRect(hx - 3, gy - h, 7, 2);
      x.fillStyle = a; x.fillRect(hx - 2, gy - h + 5, 5, 1);
      pSmoke(x, hx, gy - h - 4, '#5a5550', r);
    }
    x.fillStyle = c; x.fillRect(cx - 8, gy - 12, 26, 12);
  },
  pylon(x, cx, gy, c, a) {            // 电塔 + 电线
    x.fillStyle = c; const h = 42;
    pLine(x, cx - 6, gy, cx - 1, gy - h); pLine(x, cx + 6, gy, cx + 1, gy - h);
    for (let i = 1; i < 5; i++) { const y = gy - i * 8, w = Math.round(6 - i); pLine(x, cx - w, y, cx + w, y - 8); pLine(x, cx + w, y, cx - w, y - 8); }
    x.fillRect(cx - 8, gy - h + 6, 17, 1); x.fillRect(cx - 6, gy - h + 12, 13, 1);
    x.fillStyle = a; x.fillRect(cx, gy - h - 1, 1, 1);
  },
  factory(x, cx, gy, c, a, r, night) {  // 砖厂房：锯齿屋顶 + 一排亮窗 + 矮烟囱
    const w = 30, h = 16;
    x.fillStyle = c; x.fillRect(cx - w / 2, gy - h, w, h);
    for (let k = 0; k < 3; k++) for (let i = 0; i < 6; i++) x.fillRect(cx - w / 2 + k * 10 + i, gy - h - i, 1, i);   // 锯齿
    x.fillRect(cx + 9, gy - h - 14, 3, 14);
    x.fillStyle = night ? '#ffcf6a' : bgMix(c, '#000000', 0.3);
    for (let i = 0; i < 5; i++) if (!night || r() < 0.8) x.fillRect(cx - w / 2 + 3 + i * 6, gy - h + 5, 3, 3);
    if (night) { x.globalAlpha = 0.18; for (let i = 0; i < 5; i++) x.fillRect(cx - w / 2 + 2 + i * 6, gy - h + 4, 5, 5); x.globalAlpha = 1; }
    pSmoke(x, cx + 10, gy - h - 18, '#5a5866', r);
  },
  mech(x, cx, gy, c, a) {             // 半埋的巨型机甲头
    x.fillStyle = c; pDome(x, cx, gy, 14); x.fillRect(cx + 8, gy - 22, 2, 10); x.fillRect(cx - 18, gy - 4, 6, 4);
    x.fillStyle = a; x.fillRect(cx - 6, gy - 8, 4, 2); x.fillRect(cx + 3, gy - 8, 4, 2); x.fillRect(cx + 8, gy - 23, 2, 1);
  },
  tree(x, cx, gy, c, a, r) {          // 大树
    const h = 18 + Math.floor(r() * 10);
    x.fillStyle = c; x.fillRect(cx - 1, gy - h, 3, h);
    pDisc(x, cx, gy - h - 4, 7); pDisc(x, cx - 6, gy - h + 1, 5); pDisc(x, cx + 6, gy - h + 1, 6);
  },
  pod(x, cx, gy, c, a) {              // 生化培养罐
    for (let k = 0; k < 2; k++) {
      const px = cx + k * 11, h = 20 + k * 6;
      x.fillStyle = c; x.fillRect(px - 4, gy - h, 9, h); pDisc(x, px, gy - h, 4);
      x.fillStyle = a; x.fillRect(px - 2, gy - h + 6, 1, h - 9); x.fillRect(px - 3, gy - h + 4, 7, 1);
    }
  },
  windmill(x, cx, gy, c, a) {         // 风车
    x.fillStyle = c; for (let i = 0; i < 24; i++) x.fillRect(cx - 4 + Math.floor(i / 8), gy - i, 9 - Math.floor(i / 4), 1);
    pLine(x, cx, gy - 24, cx - 12, gy - 36); pLine(x, cx, gy - 24, cx + 12, gy - 12); pLine(x, cx, gy - 24, cx + 12, gy - 36); pLine(x, cx, gy - 24, cx - 12, gy - 12);
    x.fillStyle = a; x.fillRect(cx - 1, gy - 6, 2, 4);
  },
  fort(x, cx, gy, c) {                // 城墙垛口
    x.fillStyle = c; x.fillRect(cx - 18, gy - 12, 36, 12);
    for (let i = 0; i < 6; i++) x.fillRect(cx - 18 + i * 6, gy - 15, 4, 3);
    x.fillRect(cx - 4, gy - 20, 8, 8);
  },
  ship(x, cx, gy, c, a) {             // 远处海上的船（gy 是海平面；由 bgFar 画）
    x.fillStyle = c; x.fillRect(cx - 14, gy - 4, 28, 3); x.fillRect(cx - 11, gy - 1, 22, 1);
    x.fillRect(cx - 4, gy - 26, 1, 22); x.fillRect(cx + 5, gy - 20, 1, 16);
    x.fillStyle = a; for (let i = 0; i < 14; i++) x.fillRect(cx - 3, gy - 24 + i, Math.floor(i * 0.6) + 1, 1);
    for (let i = 0; i < 10; i++) x.fillRect(cx + 6, gy - 18 + i, Math.floor(i * 0.6) + 1, 1);
  },
  cooling(x, cx, gy, c, a, r) {       // 核电站冷却塔 + 蒸汽
    const h = 30;
    x.fillStyle = c; for (let i = 0; i < h; i++) { const w = Math.round(9 - 3 * Math.sin(Math.PI * i / h)); x.fillRect(cx - w, gy - i, w * 2 + 1, 1); }
    x.fillStyle = a; x.fillRect(cx - 7, gy - 10, 15, 1);
    pSmoke(x, cx - 2, gy - h - 4, '#e8e8e8', r);
  },
  monolith(x, cx, gy, c, a) {         // 发光的机器方碑
    x.fillStyle = c; x.fillRect(cx - 4, gy - 44, 9, 44); x.fillRect(cx - 7, gy - 3, 15, 3);
    x.fillStyle = a; x.fillRect(cx, gy - 40, 1, 36); for (let i = 0; i < 5; i++) x.fillRect(cx - 2, gy - 38 + i * 8, 5, 1);
  },
  mushroom(x, cx, gy, c, a) {         // 巨型发光蘑菇
    x.fillStyle = c; x.fillRect(cx - 1, gy - 18, 4, 18); pDome(x, cx + 1, gy - 18, 11);
    x.fillStyle = a; x.fillRect(cx - 5, gy - 24, 2, 2); x.fillRect(cx + 4, gy - 26, 2, 2); x.fillRect(cx + 8, gy - 21, 2, 1);
  },
  bones(x, cx, gy, c) {               // 巨兽骨架（肋骨）
    x.fillStyle = c; x.fillRect(cx - 20, gy - 20, 40, 2); pDisc(x, cx + 24, gy - 16, 5);
    for (let i = 0; i < 6; i++) { const bx = cx - 16 + i * 6; for (let j = 0; j < 18; j++) x.fillRect(bx + Math.round(Math.sin(j / 18 * Math.PI) * 3), gy - 20 + j, 1, 1); }
  },
  hive(x, cx, gy, c, a) {             // 虫巢土丘
    x.fillStyle = c; pDome(x, cx, gy, 13); x.fillRect(cx - 3, gy - 22, 7, 10);
    x.fillStyle = a; for (let i = 0; i < 4; i++) x.fillRect(cx - 7 + i * 4, gy - 6 - (i % 2) * 4, 2, 2);
  },
  hangar(x, cx, gy, c, a) {           // 机库拱顶
    x.fillStyle = c; pDome(x, cx, gy, 18);
    x.fillStyle = a; pDome(x, cx, gy, 11);
    x.fillStyle = c; for (let i = -9; i <= 9; i += 3) x.fillRect(cx + i, gy - 10, 1, 10);
  },
  flag(x, cx, gy, c, a) {             // 远征旗
    x.fillStyle = c; x.fillRect(cx, gy - 26, 1, 26);
    x.fillStyle = a; x.fillRect(cx + 1, gy - 26, 9, 3); x.fillRect(cx + 1, gy - 23, 7, 3);
  },
};

// ---------- 各层生成 ----------
function bgSky(era, th) {
  const w = Math.ceil(W / BG_PX), h = Math.ceil(GROUND_Y / BG_PX), [c, x] = bgCanvas(w, h);
  const [top, bot] = SKY[era], night = isNight(era), r = bgRng(era + 1);
  const N = 16;   // 分成色带，像素画的天空
  for (let i = 0; i < N; i++) { x.fillStyle = bgMix(top, bot, i / (N - 1)); x.fillRect(0, Math.floor(h * i / N), w, Math.ceil(h / N) + 1); }
  if (night) for (let i = 0; i < 110; i++) {
    x.globalAlpha = 0.35 + r() * 0.65; x.fillStyle = r() < 0.25 ? '#ffffff' : '#cfd8ff';
    x.fillRect(Math.floor(r() * w), Math.floor(r() * h * 0.75), 1, 1);
  }
  x.globalAlpha = 1;
  // 太阳 / 月亮（带几圈光晕）
  // 放在右侧血条下方（逻辑 y≈230–260），不躲在顶栏 HUD 后面
  const cx = Math.floor(w * (0.7 + r() * 0.12)), cy = Math.floor(h * (night ? 0.39 : 0.43)), R = night ? 8 : 11;
  const glow = night ? '#dfe6ff' : '#fff3c0';
  [[R + 14, 0.07], [R + 8, 0.1], [R + 3, 0.16]].forEach(([rr, al]) => { x.globalAlpha = al; x.fillStyle = glow; pDisc(x, cx, cy, rr); });
  x.globalAlpha = 1; x.fillStyle = night ? '#eef1fa' : bgMix(glow, '#ffffff', 0.5); pDisc(x, cx, cy, R);
  if (night) { x.fillStyle = '#c9cfe0'; x.fillRect(cx - 3, cy - 2, 2, 2); x.fillRect(cx + 2, cy + 2, 3, 2); x.fillRect(cx - 1, cy + 4, 1, 1); }
  // 云
  const cloud = night ? bgMix(top, bot, 0.55) : bgMix(bot, '#ffffff', 0.6), shade = night ? bgMix(top, bot, 0.35) : bgMix(top, bot, 0.65);
  for (let i = 0; i < 6; i++) {
    const kx = Math.floor(r() * w), ky = Math.floor(h * (0.12 + r() * 0.4)), n = 3 + Math.floor(r() * 3);
    const rs = []; for (let j = 0; j < n; j++) rs.push(3 + Math.floor(r() * 3));
    if (night) {                    // 夜里：暗云 + 上沿一圈月光，不画底下那条平板（会像一块砖）
      x.globalAlpha = 0.5; x.fillStyle = bgMix(cloud, glow, 0.45); for (let j = 0; j < n; j++) pDisc(x, kx + j * 6, ky - 1, rs[j]);
      x.globalAlpha = 0.85; x.fillStyle = cloud; for (let j = 0; j < n; j++) pDisc(x, kx + j * 6, ky, rs[j]);
      x.globalAlpha = 1;
      continue;
    }
    x.fillStyle = shade; for (let j = 0; j < n; j++) pDisc(x, kx + j * 6, ky + 2, rs[j] + 1);
    x.fillStyle = cloud; for (let j = 0; j < n; j++) pDisc(x, kx + j * 6, ky, rs[j]);
    x.fillStyle = shade; x.fillRect(kx - 4, ky + 4, n * 6 + 6, 2);
  }
  // 飞艇
  if (th.blimps) for (let i = 0; i < 2; i++) {
    const bx = Math.floor(w * (0.15 + i * 0.4)), by = Math.floor(h * (0.25 + i * 0.12));
    x.fillStyle = bgMix(top, '#000000', 0.35); for (let dy = -4; dy <= 4; dy++) { const dx = Math.floor(14 * Math.sqrt(1 - (dy / 5) ** 2)); x.fillRect(bx - dx, by + dy, dx * 2, 1); }
    x.fillRect(bx - 3, by + 5, 6, 2); x.fillRect(bx - 16, by - 3, 3, 6);
  }
  return c;
}
function bgFar(era, th) {
  const w = Math.ceil((W + BG_PAN * BG_PAR.far) / BG_PX) + 2, h = Math.ceil(GROUND_Y / BG_PX), [c, x] = bgCanvas(w, h);
  const [top, bot] = SKY[era], night = isNight(era), r = bgRng(era + 101);
  const ph = [r() * 9, r() * 9, r() * 9, r() * 9];
  const back = bgMix(bgMix(bot, top, 0.35), '#000000', night ? 0.35 : 0.12);
  const front = bgMix(bgMix(bot, GROUND_COL[era], 0.35), '#000000', night ? 0.45 : 0.18);
  for (let i = 0; i < w; i++) {   // 两道山脊：裂谷两侧的远山
    const y1 = h * 0.66 - 22 * Math.abs(Math.sin(i * 0.011 + ph[0])) - 9 * Math.sin(i * 0.05 + ph[1]) - 3 * Math.sin(i * 0.23);
    x.fillStyle = back; x.fillRect(i, Math.round(y1), 1, h);
    if (!th.sea) {
      const y2 = h * 0.8 - 12 * Math.abs(Math.sin(i * 0.017 + ph[2])) - 5 * Math.sin(i * 0.07 + ph[3]) - 2 * Math.sin(i * 0.31);
      x.fillStyle = front; x.fillRect(i, Math.round(y2), 1, h);
    }
  }
  if (th.sea) {                   // 海：一条水面 + 浪花
    const sy = Math.round(h * 0.8), sea = bgMix(bgMix(top, bot, 0.3), '#000000', 0.15);
    x.fillStyle = sea; x.fillRect(0, sy, w, h - sy);
    x.fillStyle = bgMix(sea, '#ffffff', 0.35);
    for (let i = 0; i < 70; i++) x.fillRect(Math.floor(r() * w), sy + 2 + Math.floor(r() * (h - sy - 3)), 3 + Math.floor(r() * 5), 1);
    // 海上的船：画在远景的海平面上，前面的废墟会挡住一部分
    const ship = bgMix(sea, '#000000', 0.45), sail = bgMix(bot, '#ffffff', 0.3);
    for (let px = 30 + Math.floor(r() * 40); px < w - 20; px += 60 + Math.floor(r() * 50)) BG_PROPS.ship(x, px, sy + 3, ship, sail);
  }
  return c;
}
function bgMid(era, th) {
  const w = Math.ceil((W + BG_PAN * BG_PAR.mid) / BG_PX) + 2, h = Math.ceil(GROUND_Y / BG_PX), [c, x] = bgCanvas(w, h);
  const [top, bot] = SKY[era], night = isNight(era), r = bgRng(era + 202);
  const body = bgMix(bgMix(bot, GROUND_COL[era], 0.55), '#000000', night ? 0.5 : 0.22);
  const hole = night ? bgMix(body, '#000000', 0.3) : bgMix(body, bot, 0.35);
  const vine = '#4f7a35';
  // 旧世界的废墟楼
  for (let bx = Math.floor(r() * 10); bx < w; bx += 14 + Math.floor(r() * 26)) {
    const bw = 7 + Math.floor(r() * 14), bh = 14 + Math.floor(r() * 40);
    x.fillStyle = body;
    let top0 = h - bh;
    for (let i = 0; i < bw; i++) {                // 楼顶塌成参差不齐的样子
      if (r() < 0.35) top0 += Math.floor(r() * 5) - 2;
      x.fillRect(bx + i, Math.max(h - bh - 3, top0), 1, h);
    }
    if (r() < 0.5) { const rx = bx + Math.floor(r() * bw); pLine(x, rx, h - bh, rx + Math.floor(r() * 5) - 2, h - bh - 4 - Math.floor(r() * 5)); }   // 露出的钢筋
    for (let wy = h - bh + 4; wy < h - 3; wy += 4) for (let wx = bx + 2; wx < bx + bw - 2; wx += 3) {
      const v = r();
      if (v < 0.5) { x.fillStyle = hole; x.fillRect(wx, wy, 1, 2); }   // 废墟的窗都是黑的：亮灯的是本时代建筑
    }
    if (th.vines) { x.fillStyle = vine; for (let k = 0; k < bw; k++) if (r() < 0.6) x.fillRect(bx + k, h - 1 - Math.floor(r() * bh * 0.6), 1, 1 + Math.floor(r() * 3)); }
  }
  return c;
}
/** 本时代的建筑：和中景同一视差，但画在地平线雾前面，比废墟清楚 */
function bgProps(era, th) {
  const w = Math.ceil((W + BG_PAN * BG_PAR.mid) / BG_PX) + 2, h = Math.ceil(GROUND_Y / BG_PX), [c, x] = bgCanvas(w, h);
  const [, bot] = SKY[era], night = isNight(era), r = bgRng(era + 505);
  const body = bgMix(bgMix(bot, GROUND_COL[era], 0.55), '#000000', night ? 0.5 : 0.22);
  const lit = bgMix(AGE_COL[era], '#ffe2a0', 0.4);
  const pc = bgMix(body, '#000000', 0.25), acc = night ? lit : bgMix(AGE_COL[era], body, 0.35);
  const props = th.props.filter(p => p !== 'ship');   // 船在远景的海上画（bgFar）
  const poles = [];
  if (props.length) for (let px = 20 + Math.floor(r() * 30); px < w - 10; px += 70 + Math.floor(r() * 50)) {
    const k = props[Math.floor(r() * props.length)];
    BG_PROPS[k](x, px, h, pc, acc, r, night);
    if (k === 'pylon') poles.push(px);
  }
  // 电线：相邻两座电塔之间连两根，中间往下垂
  x.fillStyle = pc;
  for (let i = 1; i < poles.length; i++) {
    const a = poles[i - 1] + 8, b = poles[i] - 8, sag = Math.round((b - a) * 0.07);
    for (const y0 of [h - 42 + 6, h - 42 + 12]) for (let px = a; px <= b; px++) {
      const t = (px - a) / (b - a); x.fillRect(px, y0 + Math.round(4 * sag * t * (1 - t)), 1, 1);
    }
  }
  return c;
}
function bgNear(era, th) {
  const w = Math.ceil((W + BG_PAN * BG_PAR.near) / BG_PX) + 2, h = Math.ceil(GROUND_Y / BG_PX), [c, x] = bgCanvas(w, h);
  const r = bgRng(era + 303), col = bgMix(GROUND_COL[era], '#000000', 0.3), hi = bgMix(GROUND_COL[era], '#ffffff', 0.12);
  for (let i = Math.floor(r() * 20); i < w; i += 18 + Math.floor(r() * 40)) {   // 碎石堆
    const rr = 2 + Math.floor(r() * 5);
    x.fillStyle = col; pDome(x, i, h, rr);
    x.fillStyle = hi; x.fillRect(i - Math.floor(rr / 2), h - rr, Math.max(1, rr - 1), 1);
    if (r() < 0.3) { x.fillStyle = col; x.fillRect(i + rr, h - rr - 3, 1, rr + 3); }      // 断掉的柱子
  }
  if (th.lamps) {                  // 路灯：铁杆 + 弯头，夜里灯下一圈暖光
    const night = isNight(era);
    for (let i = 40 + Math.floor(r() * 30); i < w; i += 110 + Math.floor(r() * 60)) {
      x.fillStyle = col; x.fillRect(i, h - 22, 1, 22); x.fillRect(i - 1, h - 2, 3, 2); x.fillRect(i, h - 22, 4, 1); x.fillRect(i + 3, h - 22, 1, 2);
      x.fillStyle = night ? '#ffd27a' : hi; x.fillRect(i + 2, h - 20, 3, 1);
      if (night) { x.fillStyle = '#ffd27a'; x.globalAlpha = 0.3; x.fillRect(i + 1, h - 21, 5, 3); x.globalAlpha = 0.22; x.fillRect(i - 2, h - 1, 11, 1); x.globalAlpha = 1; }   // 灯泡光晕 + 灯下一小片暖光
    }
  }
  if (th.grass) {
    x.fillStyle = bgMix('#5c8a3a', GROUND_COL[era], 0.3);
    for (let i = 0; i < w; i += 2 + Math.floor(r() * 5)) { const gh = 1 + Math.floor(r() * 3); x.fillRect(i, h - gh, 1, gh); }
  }
  return c;
}
function bgGround(era, th) {
  const w = Math.ceil(WORLD / BG_PX), h = Math.ceil((H - GROUND_Y + BG_DEPTH) / BG_PX), [c, x] = bgCanvas(w, h);
  const g = GROUND_COL[era], r = bgRng(era + 404);
  const bands = [[0, bgMix(g, '#ffffff', 0.1)], [3, g], [12, bgMix(g, '#000000', 0.12)], [26, bgMix(g, '#000000', 0.22)], [44, bgMix(g, '#000000', 0.32)]];
  for (let i = 0; i < bands.length; i++) {        // 土层：越深越暗，分界线带一点起伏
    const [y0, col] = bands[i];
    x.fillStyle = col;
    for (let k = 0; k < w; k++) x.fillRect(k, y0 + (i ? Math.round(Math.sin(k * 0.09 + i) * 1.5) : 0), 1, h);
  }
  x.fillStyle = bgMix(g, '#000000', 0.35); x.fillRect(0, 0, w, 1);   // 地平线
  if (th.grass) { x.fillStyle = bgMix('#6a9a40', g, 0.25); x.fillRect(0, 1, w, 1); for (let k = 0; k < w; k += 1 + Math.floor(r() * 3)) x.fillRect(k, 2, 1, 1); }
  for (let i = 0; i < w * 0.6; i++) {              // 石子
    const px = Math.floor(r() * w), py = 3 + Math.floor(r() * (h - 3));
    x.fillStyle = r() < 0.5 ? bgMix(g, '#ffffff', 0.18) : bgMix(g, '#000000', 0.3);
    x.fillRect(px, py, 1 + Math.floor(r() * 2), 1);
  }
  x.fillStyle = bgMix(g, '#000000', 0.4);           // 裂缝
  for (let i = 0; i < w / 50; i++) { let px = Math.floor(r() * w), py = 4 + Math.floor(r() * 8); for (let k = 0; k < 8; k++) { x.fillRect(px, py, 1, 1); px += 1; py += Math.floor(r() * 3) - 1; } }
  return c;
}

/** 地平线雾：一条 1 像素宽的竖条（拉伸到整屏），把中景废墟往后推，兵站在前面更清楚 */
const BG_HAZE_H = 210;
function bgHaze(era) {
  const night = isNight(era);
  const b = bgHex(night ? bgMix(SKY[era][0], SKY[era][1], 0.35) : SKY[era][1]), k = night ? 0.6 : 1;
  const [c, x] = bgCanvas(1, BG_HAZE_H), g = x.createLinearGradient(0, 0, 0, BG_HAZE_H);
  g.addColorStop(0, `rgba(${b},0)`); g.addColorStop(0.65, `rgba(${b},${0.28 * k})`); g.addColorStop(1, `rgba(${b},${0.5 * k})`);
  x.fillStyle = g; x.fillRect(0, 0, 1, BG_HAZE_H);
  return c;
}

const BG_CACHE = {};
/** 某个时代的全部图层（第一次用到时生成） */
function bgLayers(era) {
  let L = BG_CACHE[era];
  if (!L) {
    const th = BG_THEME[era] || BG_THEME[0];
    L = BG_CACHE[era] = { sky: bgSky(era, th), far: bgFar(era, th), mid: bgMid(era, th), props: bgProps(era, th), near: bgNear(era, th), ground: bgGround(era, th), haze: bgHaze(era) };
  }
  return L;
}

/** 画战场背景（era = 我方当前时代编号）。镜头位置取 G；G 为 null 时画镜头在最左边的样子 */
function drawBackground(era) {
  const L = bgLayers(era), z = G ? G.zoom : 1, cam = G ? G.camX : 0, smooth = ctx.imageSmoothingEnabled;
  ctx.imageSmoothingEnabled = false;
  // 开始页演示局把战场整体抬高了 DEMO_LIFT；天空不跟着抬，太阳 / 月亮仍在标题下方
  const demo = G && G.demo ? DEMO_LIFT : 0;
  ctx.drawImage(L.sky, 0, demo, L.sky.width * BG_PX, L.sky.height * BG_PX);
  for (const k of ['far', 'mid', 'props', 'near']) {
    const c = L[k];
    ctx.drawImage(c, -Math.round(cam * z * BG_PAR[k === 'props' ? 'mid' : k]), 0, c.width * BG_PX, c.height * BG_PX);
    if (k === 'mid') { ctx.imageSmoothingEnabled = true; ctx.drawImage(L.haze, 0, GROUND_Y - BG_HAZE_H, W, BG_HAZE_H); ctx.imageSmoothingEnabled = false; }
  }
  // 地面跟着战场走（视差 1），横向随缩放拉伸；开始页演示局把战场抬高了，要多画一截
  const gh = Math.ceil((H - GROUND_Y + demo) / BG_PX);
  ctx.drawImage(L.ground, 0, 0, L.ground.width, gh, -cam * z, GROUND_Y, WORLD * z, gh * BG_PX);
  ctx.imageSmoothingEnabled = smooth;
}
