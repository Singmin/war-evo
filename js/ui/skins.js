'use strict';
// 时代皮肤：每个时代的顶栏（画布 HUD 面板）和底栏（css/skins.css）用什么材质
// 图在 assets/ui/textures/，按材质存（不按时代）：<材质>.webp 平铺纹理，btn_<材质>.webp / btn_<材质>_s.webp 底栏按钮
// 图由 tools/gen_textures.py + tools/gen_materials.py 生成（高度图 + 打光，所以有真实的凹凸感）
// 新增时代皮肤：1) 在 tools/gen_materials.py 里加一种材质并运行  2) 在 SKINS 里加一行  3) 在 SKIN_OF_ERA 里把时代对上
//   css/skins.css 是通用的，不用改（只有想加特别装饰时才改）
const mat = (tex, edge, shade = 'rgba(12,10,8,.42)', extra = {}) => ({ tex, shade, edge, edgeW: 2, deco: null, ...extra });
const SKINS = {
  wood: { tex: null, fill: 'rgba(42,30,20,.88)', edge: '#6b5338', edgeW: 2, deco: null },   // 默认（还没加载好时用）
  stone: mat('stone', '#2a2622', 'rgba(22,19,16,.42)'),                                      // 部落纪：石板
  bronze: mat('bronze', '#3a2810', 'rgba(26,16,6,.45)'),                                     // 青铜纪：铸青铜 + 铜绿
  rivet: mat('rivet', '#1b1f23', 'rgba(12,16,20,.42)', { deco: 'rivets', decoCol: '#b9c1c8' }), // 蒸汽纪：铆钉铁板
  copper: mat('copper', '#3a1a0c', 'rgba(30,12,6,.45)'),                                     // 电气纪：锤纹紫铜
  armor: mat('armor', '#16181b', 'rgba(8,10,12,.4)'),                                        // 机甲纪：枪灰装甲板
  hide: mat('hide', '#2a170a', 'rgba(34,18,8,.45)', { deco: 'stitch', decoCol: '#e6cfa4' }), // 驯兽纪：兽皮 + 缝线
  bio: mat('bio', '#1c2a12', 'rgba(10,18,6,.45)'),                                           // 生化纪：湿润细胞组织
  oak: mat('oak', '#24160a', 'rgba(20,12,4,.42)'),                                           // 火药纪：橡木板
  canvas: mat('canvas', '#3a2a14', 'rgba(24,18,8,.5)'),                                      // 帆船纪：帆布
  hazard: mat('hazard', '#1e1e1c', 'rgba(14,14,12,.48)'),                                    // 核能纪：混凝土 + 警示条
  circuit: mat('circuit', '#0a1e12', 'rgba(4,14,8,.4)'),                                     // 智械纪：电路板
  bark: mat('bark', '#20140a', 'rgba(16,10,4,.42)'),                                         // 共生纪：树皮 + 苔藓
  scales: mat('scales', '#1a200e', 'rgba(10,14,4,.42)'),                                     // 巨兽纪：鳞片
  honey: mat('honey', '#3a2406', 'rgba(26,14,2,.45)'),                                       // 蜂群纪：蜂巢
  hull: mat('hull', '#1a2026', 'rgba(10,14,18,.42)'),                                        // 铁甲舰纪：舰体灰钢
  alu: mat('alu', '#2a3036', 'rgba(14,18,22,.5)'),                                           // 航空纪：拉丝铝
  alloy: mat('alloy', '#0e1418', 'rgba(4,8,12,.35)'),                                        // 远征纪：钛合金 + 青光
};
// 时代编号 → 材质（时代编号见 js/core/data.js 的 AGES）
const SKIN_OF_ERA = ['stone', 'bronze', 'rivet', 'copper', 'armor', 'hide', 'bio', 'oak', 'canvas',
  'hazard', 'circuit', 'bark', 'scales', 'honey', 'hull', 'alu', 'alloy'];
const skinOf = era => SKINS[SKIN_OF_ERA[era]] ? SKIN_OF_ERA[era] : 'wood';

// ---------- 纹理加载：只加载当前时代和下一步能进化到的时代（17 个时代全加载太重）----------
const TEX = {}, TEX_IMG = {}, texLoading = new Set();
const texUrl = f => new URL(`assets/ui/textures/${f}.webp`, location.href).href;
function loadSkin(key) {
  const k = SKINS[key] && SKINS[key].tex;
  if (!k || texLoading.has(k)) return;
  texLoading.add(k);
  const img = new Image();
  img.onload = () => { TEX[k] = ctx.createPattern(img, 'repeat'); TEX_IMG[k] = img; };
  img.src = texUrl(k);
  for (const f of [`btn_${k}`, `btn_${k}_s`]) new Image().src = texUrl(f);   // 底栏按钮图（css/skins.css 用）
}
function preloadAround(era) {
  loadSkin(skinOf(era));
  ERA_PARENTS.forEach((ps, e) => { if (ps.includes(era)) loadSkin(skinOf(e)); });
  preloadSpritesAround(era);   // 兵种图同样按需加载（js/render/sprites.js）
}
preloadAround(0);

let skinKey = 'wood', skinEra = -1, skinFlashT = 0;
function applySkin(key, animate) {
  skinKey = key;
  gameEl.dataset.skin = key;   // css/skins.css 按 #game[data-skin=...] 加材质特有的装饰
  // 通用样式用的图：底栏纹理、按钮图（css/skins.css 里的 var(--skin-tex) 等）
  const t = SKINS[key].tex;
  gameEl.classList.toggle('skinned', !!t);
  if (t) {
    gameEl.style.setProperty('--skin-tex', `url("${texUrl(t)}")`);
    gameEl.style.setProperty('--btn-img', `url("${texUrl('btn_' + t)}")`);
    gameEl.style.setProperty('--btn-img-s', `url("${texUrl('btn_' + t + '_s')}")`);
  }
  if (animate) {
    skinFlashT = performance.now();
    gameEl.classList.remove('skin-swap'); void gameEl.offsetWidth; gameEl.classList.add('skin-swap');
  }
}
// 每帧调用：我方时代变了就换皮肤（升级时带一下闪光）
function updateSkin() {
  const era = G ? G.sides[0].era : 0;
  if (era === skinEra) return;
  const animate = skinEra !== -1 && !!G && G.t > 0.5;
  skinEra = era;
  preloadAround(era);
  const key = skinOf(era);
  applySkin(key, animate && key !== skinKey);
}

// ---------- 画布上的皮肤面板（hud.js 的 panel() 调用）----------
// 面板（投影、纹理、倒角、装饰）每帧不变，但投影模糊和纹理填充很贵（每块 ~0.7ms）：
// 按「材质 + 尺寸 + 画布缩放」画到离屏画布上缓存，之后每帧只贴一张图。只有换皮肤的闪光是实时画的。
const PANEL_PAD = 14;   // 给投影留的边
const panelCache = new Map();
function rr(c, x, y, w, h, r) { c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r); c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath(); }
function paintPanel(c, w, h) {   // 在 c 上、以 (0,0) 为左上角画一块面板
  const s = SKINS[skinKey], r = 12, img = s.tex && TEX_IMG[s.tex];
  if (img) {
    // 投影：让面板"浮"在战场上
    c.save(); c.shadowColor = 'rgba(0,0,0,.45)'; c.shadowBlur = 8; c.shadowOffsetY = 3;
    c.fillStyle = '#000'; rr(c, 0, 0, w, h, r); c.fill(); c.restore();
    c.save(); rr(c, 0, 0, w, h, r); c.clip();
    c.fillStyle = c.createPattern(img, 'repeat'); c.fillRect(0, 0, w, h);
    c.fillStyle = s.shade; c.fillRect(0, 0, w, h);          // 压暗，保证字看得清
    // 倒角：上沿亮、下沿暗
    const g = c.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, 'rgba(255,255,255,.16)'); g.addColorStop(.12, 'rgba(255,255,255,0)');
    g.addColorStop(.85, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.35)');
    c.fillStyle = g; c.fillRect(0, 0, w, h);
    c.restore();
    c.strokeStyle = 'rgba(255,255,255,.18)'; c.lineWidth = 1; rr(c, 1.5, 1.5, w - 3, h - 3, r - 1); c.stroke();
  } else {
    c.fillStyle = s.fill || SKINS.wood.fill; rr(c, 0, 0, w, h, r); c.fill();
  }
  c.strokeStyle = s.edge; c.lineWidth = s.edgeW; rr(c, 0, 0, w, h, r); c.stroke();
  // 材质装饰
  if (s.deco === 'stitch') {
    // 皮革缝线：每一针一亮一暗，像线压进皮里
    c.save(); c.setLineDash([6, 4]); c.lineWidth = 1.6;
    c.strokeStyle = 'rgba(0,0,0,.5)'; rr(c, 6, 6.8, w - 12, h - 12, 8); c.stroke();
    c.strokeStyle = s.decoCol; c.globalAlpha = 0.8; rr(c, 6, 6, w - 12, h - 12, 8); c.stroke(); c.restore();
  } else if (s.deco === 'rivets') {
    for (const [px, py] of [[9, 9], [w - 9, 9], [9, h - 9], [w - 9, h - 9]]) {
      c.fillStyle = 'rgba(0,0,0,.5)'; c.beginPath(); c.arc(px + 1, py + 1.5, 4.2, 0, 7); c.fill();
      const rg = c.createRadialGradient(px - 1.3, py - 1.3, .5, px, py, 4);
      rg.addColorStop(0, '#f1f4f6'); rg.addColorStop(.45, s.decoCol); rg.addColorStop(1, '#3a4046');
      c.fillStyle = rg; c.beginPath(); c.arc(px, py, 4, 0, 7); c.fill();
    }
  }
}
function skinPanel(x, y, w, h) {
  const k = Math.hypot(ctx.getTransform().a, ctx.getTransform().b);   // 当前画布缩放（含 dpr、HUD 缩放）
  const s = SKINS[skinKey], loaded = !!(s.tex && TEX_IMG[s.tex]);
  const key = `${skinKey}|${loaded}|${w}|${h}|${k.toFixed(3)}`;
  let cv2 = panelCache.get(key);
  if (!cv2) {
    if (panelCache.size > 24) panelCache.clear();
    cv2 = document.createElement('canvas');
    cv2.width = Math.ceil((w + PANEL_PAD * 2) * k); cv2.height = Math.ceil((h + PANEL_PAD * 2) * k);
    const c = cv2.getContext('2d');
    c.scale(k, k); c.translate(PANEL_PAD, PANEL_PAD);
    paintPanel(c, w, h);
    panelCache.set(key, cv2);
  }
  const sm = ctx.imageSmoothingEnabled; ctx.imageSmoothingEnabled = true;
  ctx.drawImage(cv2, x - PANEL_PAD, y - PANEL_PAD, cv2.width / k, cv2.height / k);
  ctx.imageSmoothingEnabled = sm;
  // 换皮肤时的闪光
  const ft = (performance.now() - skinFlashT) / 700;
  if (ft < 1) { ctx.save(); ctx.globalAlpha = 0.55 * (1 - ft); ctx.fillStyle = '#fff6d8'; roundRect(x, y, w, h, 12); ctx.fill(); ctx.restore(); }
}
