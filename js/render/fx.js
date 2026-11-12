'use strict';
// 受击 / 爆炸特效（pixelfx，MIT）：图在 assets/fx/fx.webp，帧信息在 js/render/fx_meta.js（都由 tools/gen_fx.py 生成）
// sim.js 在命中时调用 spawnHitFx，往 G.fx 里放一个 kind:'pfx' 的特效；world.js 的 drawFx 遇到它就调用 drawHitFx
//   blunt 近战钝击 · spark 远程命中 · crit 重击 · flash 基地受击 · dirt 溅射爆炸 · big 大招爆炸
//   各时代弹道的命中特效（bullet zap acid spore plasma implode grenade boom barrel nuke）和炮口火光（m_*）也走这里，
//   用哪个由 data.js 的 PROJ_STYLE 决定；飞行体（kind:'fly'）不走这里，由 arms.js 的 drawProjs 画
const FX_IMG = new Image();
FX_IMG.src = 'assets/fx/fx.webp?v=20261108u';   // 图集和 fx_meta.js 必须同一版，改了图记得改版本号
const FX_CAP = 24;                                                     // 同时最多几个，战线挤的时候不至于糊成一片
// 满了以后，优先级高的挤掉最低的；炮口火光最低，不会挤掉命中特效
const FX_PRIO = { m_pistol: -1, m_smg: -1, m_shotgun: -1, m_cannon: -1,
  flash: 0, spark: 0, blunt: 0, bullet: 0, zap: 0, acid: 1, crit: 1, plasma: 1, implode: 1,
  dirt: 2, spore: 2, grenade: 2, boom: 2, barrel: 2, thunder: 2, big: 3, nuke: 3, strike: 3,
  burn: -1, puddle: -1, slam: 1, emp: 3, pillar: 3, meteor: 3, burst: 3 };
// 爆炸、酸液、孢子、落雷以地面为锚点；受击特效以命中点为中心；炮口火光以炮口为锚点（meta 的 px/py）
const FX_GROUND = { dirt: true, big: true, acid: true, spore: true, grenade: true, boom: true, barrel: true, nuke: true, strike: true, thunder: true,
  meteor: true, pillar: true, emp: true, slam: true, burn: true, puddle: true, burst: true };
const FX_ADD = { flash: true, zap: true, plasma: true, strike: true, thunder: true, pillar: true, emp: true };
// 留在地上的：画在兵之前（压在兵脚下），由 arms.js 的 drawScorch 画，drawFx 跳过
const FX_UNDER = { burn: true, puddle: true };

// kind：上面 6 种之一；x 世界坐标，y 离地高度（负数往上，和 G.fx 其他特效一样）
// opts.flip：朝左（敌方打出的）；opts.scale：额外缩放
function spawnHitFx(kind, x, y, opts = {}) {
  const m = FX_META[kind];
  if (!m) return;
  let n = 0, low = null;
  for (const f of G.fx) {
    if (f.kind !== 'pfx') continue;
    n++;
    // 同一处刚放过同一种：不叠
    if (f.name === kind && f.t < 0.06 && Math.abs(f.x - x) < 8 && Math.abs(f.y - y) < 8) return;
    if (!low || FX_PRIO[f.name] < FX_PRIO[low.name] || (FX_PRIO[f.name] === FX_PRIO[low.name] && f.t > low.t)) low = f;
  }
  if (n >= FX_CAP) {
    if (FX_PRIO[low.name] > FX_PRIO[kind]) return;
    G.fx.splice(G.fx.indexOf(low), 1);
  }
  G.fx.push({ kind: 'pfx', name: kind, x, y, t: 0, dur: m.n / m.fps, flip: !!opts.flip, s: opts.scale || 1 });
}

function drawHitFx(f) {
  const m = FX_META[f.name];
  if (!FX_IMG.complete || !FX_IMG.naturalWidth || f.t >= f.dur) return;
  const i = Math.min(m.n - 1, Math.floor(f.t * m.fps));
  const S = FX_SCALE * G.zoom * f.s;
  const py = FX_GROUND[f.name] || m.kind ? m.py : m.h / 2;
  ctx.save();
  ctx.imageSmoothingEnabled = false;
  ctx.translate(Math.round(sx(f.x)), Math.round(sy(f.y)));
  ctx.scale(f.flip ? -S : S, S);
  const k = f.t / f.dur;
  ctx.globalAlpha = k < 0.8 ? 1 : (1 - k) / 0.2;                     // 最后 20% 淡出，不会突然消失
  if (FX_ADD[f.name]) ctx.globalCompositeOperation = 'lighter';       // 发光类特效叠加混合，在基地上也看得清
  ctx.drawImage(FX_IMG, m.x + (i % m.cols) * m.w, m.y + Math.floor(i / m.cols) * m.h, m.w, m.h, -m.px, -py, m.w, m.h);
  ctx.restore();
}
