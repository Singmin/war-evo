'use strict';
// 兵种像素画：图在 assets/sprites/era<N>.webp，格子信息在 js/render/sprite_meta.js（都由 tools/gen_sprites.py 生成）
// 有像素画的时代用像素画，没有的时代还是 world.js 里的矢量画法
// 每个兵种 12 帧：走路或飞行 0-3、攻击 4-7、死亡 8-11；三行：我方、敌方、纯白（受击闪白）
const SPRITE_IMG = {};
let spriteDlc = null, spriteDlcLoading = null;
// 图与格子信息一起就绪后才允许切换，加载失败时继续使用原版。
function ensureSpriteDlc() {
  if (spriteDlc) return Promise.resolve(spriteDlc);
  if (spriteDlcLoading) return spriteDlcLoading;
  spriteDlcLoading = (async () => {
    const response = await fetch('assets/dlc/chibi-tribe/manifest.json');
    if (!response.ok) throw new Error('DLC manifest unavailable');
    const data = await response.json(), era = data.eras && data.eras[0];
    if (data.id !== 'chibi-tribe' || !/^[a-f0-9]{10}$/.test(data.version) || !era || era.file !== 'era0.webp' ||
        !Array.isArray(era.units) || era.units.length !== 5 || era.units.some(m =>
          !m || !['cw', 'ch', 'ax', 'y', 's'].every(k => Number.isFinite(m[k])) ||
          m.cw <= 0 || m.ch <= 0 || m.ax < 0 || m.ax >= m.cw || m.y < 0 || m.s <= 0)) throw new Error('Invalid DLC manifest');
    const img = await new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error('DLC image unavailable'));
      image.src = `assets/dlc/chibi-tribe/${era.file}?v=${data.version}`;
    });
    if (era.units.some(m => 12 * m.cw > img.naturalWidth || m.y + 3 * m.ch > img.naturalHeight)) throw new Error('Invalid DLC atlas');
    SPRITE_IMG['chibi-tribe/0'] = img;
    spriteDlc = data;
    return data;
  })().catch(error => { spriteDlcLoading = null; throw error; });
  return spriteDlcLoading;
}
function spriteDescriptor(era, type) {
  if (save.settings.spritePack === 'chibi-tribe' && spriteDlc && spriteDlc.eras[era] &&
      (type === undefined || spriteDlc.eras[era].units[type])) {
    const entry = spriteDlc.eras[era];
    return { key: 'chibi-tribe/' + era, meta: entry.units };
  }
  return { key: 'original/' + era, meta: SPRITE_META[era], url: `assets/sprites/era${era}.webp?v=${SPRITE_VER}` };
}
function spriteAppearanceKey(era, type) { return spriteDescriptor(era, type).key; }
function spriteMeta(era, type) { const meta = spriteDescriptor(era, type).meta; return meta && meta[type]; }
function spriteSheet(era, type) {
  const source = spriteDescriptor(era, type);
  if (!source.meta) return null;
  let s = SPRITE_IMG[source.key];
  // 图片地址带图集版本 SPRITE_VER：和 sprite_meta.js 的格子信息永远配套，浏览器缓存不会拿旧格子切新图
  if (!s) { s = SPRITE_IMG[source.key] = new Image(); s.src = source.url; }
  return s.complete && s.naturalWidth ? s : null;
}
/** 提前加载某时代和它下一步能进化到的时代的兵种图（17 张全加载解码后约 70 MB，低端安卓机会卡死） */
function preloadSpritesAround(era) {
  spriteSheet(era);
  ERA_PARENTS.forEach((ps, e) => { if (ps.includes(era)) spriteSheet(e); });
}
preloadSpritesAround(0);
if (save.settings.spritePack === 'chibi-tribe') ensureSpriteDlc().then(() => {
  if (G) refreshMenu();
}).catch(() => { save.settings.spritePack = 'original'; persist(); });

// 这一帧该画哪一格
function unitFrame(u) {
  const F = SPRITE_FRAMES;
  if (u.swing > 0) return F.atk + (u.swing > 0.125 ? 2 : 3);              // 出手、收势（攻击生效后 0.25 秒）
  if (!u.walking && (!u.air || u.aiming) && u.cd < 0.35) return F.atk + (u.cd > 0.17 ? 0 : 1); // 蓄力、瞄准
  if (u.air) return F.walk + (Math.floor((G.t + u.id * 0.13) * 8) % 4); // 盘旋时也继续振翅或运转
  if (u.walking) return F.walk + Math.floor(u.anim * 8) % 4;
  return F.walk + 1;
}

// 在已经平移到单位脚下、缩放和左右翻转好的坐标系里画一格
function blitSprite(sheet, m, frame, row) {
  const S = m.s || SPRITE_SCALE;   // 高清兵种自带更小的倍数（像素翻倍）
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(sheet, frame * m.cw, m.y + row * m.ch, m.cw, m.ch, -m.ax * S, -(m.ch - 1) * S, m.cw * S, m.ch * S);
}

/** 卡通弹性：以脚底为支点的挤压拉伸 + 小跳，让兵“活”起来（只是画面，不影响碰撞和数值）
 *  走路：每步落地压扁、抬脚拉长，身体上下颠；站着：缓慢呼吸；攻击：蓄力压低、出手拉长前冲、收势回弹；受击：被打扁一下 */
function unitBounce(u) {
  if (u.air) return { sx: u.hit > 0 ? 1.06 : 1, sy: u.hit > 0 ? 0.94 : 1, lift: Math.sin(G.t * 2.6 + u.anim) * 3, lean: 0 };
  let sx = 1, sy = 1, lift = 0, lean = 0;
  if (u.hit > 0) { sx = 1.1; sy = 0.9; }
  else if (u.swing > 0) {                                   // 出手 0.25 秒：先拉长前冲，再回弹
    const k = clamp(1 - u.swing / 0.25, 0, 1);
    sy = 1 + 0.1 * Math.sin(k * Math.PI); sx = 1 - 0.06 * Math.sin(k * Math.PI);
    lean = 0.1 * Math.sin(k * Math.PI);
  } else if (!u.walking && u.cd < 0.35) {                   // 蓄力：压低、后仰一点
    // 被队友挡住排队时 cd 会一直减成很大的负数，必须夹在 0~1，否则兵会被拉成好几倍大、上下翻转
    const k = clamp(1 - u.cd / 0.35, 0, 1);
    sy = 1 - 0.07 * k; sx = 1 + 0.05 * k; lean = -0.06 * k;
  } else if (u.walking) {
    const ph = u.anim * 8 * Math.PI / 2;                    // 和 unitFrame 的步频一致：每秒 8 帧，一步两帧
    const s = Math.sin(ph * 2);
    sy = 1 + 0.045 * s; sx = 1 - 0.03 * s;
    lift = Math.max(0, -s) * 1.5;                           // 抬脚时离地一点
    lean = 0.03 * Math.sin(ph);
  } else {
    const s = Math.sin(G.t * 3.2 + u.anim);                 // 站着呼吸，每个兵相位不同
    sy = 1 + 0.025 * s; sx = 1 - 0.015 * s;
  }
  return { sx, sy, lift, lean };
}

// world.js 的 drawUnit 先调用它：画成了返回 true
function drawUnitSprite(u) {
  const sheet = spriteSheet(u.age, u.type), m = spriteMeta(u.age, u.type);
  if (!sheet || !m) return false;
  const b = unitBounce(u);
  ctx.save();
  ctx.translate(0, -b.lift); ctx.rotate(b.lean); ctx.scale(b.sx, b.sy);
  blitSprite(sheet, m, unitFrame(u), u.hit > 0 ? 2 : u.side);
  ctx.restore();
  return true;
}

// 死亡动画（sim.js 在单位死时放一个 kind:'die' 的特效）：画了返回 true
function drawDeathSprite(f) {
  const sheet = spriteSheet(f.era, f.type), m = spriteMeta(f.era, f.type);
  if (!sheet || !m) return false;
  const z = G.zoom, dir = f.side ? -1 : 1;
  let x = f.x, y = GROUND_Y, frame = Math.floor(f.t / 0.12);
  if (f.alt) {
    const k = Math.min(1, f.t / 0.6); // 空军加速下坠，第四帧在地面显示残片
    x += dir * 24 * k;
    y -= f.alt * (1 - k * k) * z;
    frame = Math.floor(k * 3);
  }
  ctx.save(); ctx.translate(sx(x), y); ctx.scale(z * dir, z);
  ctx.globalAlpha = f.t < 0.6 ? 1 : Math.max(0, 1 - (f.t - 0.6) / 0.4);
  blitSprite(sheet, m, SPRITE_FRAMES.die + Math.min(3, frame), f.side);
  ctx.restore();
  return true;
}

/** 底栏兵种按钮用的缩略图：该时代兵种的像素画（站姿、我方配色），按 时代 / 兵种 缓存；图还没载入时返回 null */
const unitIconCache = {};
function unitIcon(type, era) {
  const key = spriteAppearanceKey(era, type) + '/' + type;
  if (unitIconCache[key]) return unitIconCache[key];
  const sheet = spriteSheet(era, type), m = spriteMeta(era, type);
  if (!sheet || !m) return null;
  const c = document.createElement('canvas'); c.width = m.cw; c.height = m.ch;
  const g = c.getContext('2d');
  g.drawImage(sheet, (SPRITE_FRAMES.walk + 1) * m.cw, m.y, m.cw, m.ch, 0, 0, m.cw, m.ch);
  // 裁掉格子四周的透明边，让小图标里的兵尽量大；只看不透明像素，脚下半透明影子不算（Q 版兵种有影子）
  const a = g.getImageData(0, 0, m.cw, m.ch).data;
  let x0 = m.cw, y0 = m.ch, x1 = -1, y1 = -1;
  for (let y = 0; y < m.ch; y++) for (let x = 0; x < m.cw; x++) if (a[(y * m.cw + x) * 4 + 3] > 200) {
    if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
  }
  if (x1 < 0) return (unitIconCache[key] = c.toDataURL());
  const t = document.createElement('canvas'); t.width = x1 - x0 + 1; t.height = y1 - y0 + 1;
  t.getContext('2d').drawImage(c, x0, y0, t.width, t.height, 0, 0, t.width, t.height);
  return (unitIconCache[key] = t.toDataURL());
}
