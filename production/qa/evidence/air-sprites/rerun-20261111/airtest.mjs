// 无头 Chromium 实跑空军：node airtest.mjs <输出目录>
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2];
const SCRATCH = process.argv[3];
const URL = 'http://localhost:8765/';
const PORT = 9347;
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${join(SCRATCH, 'profile')}`, '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch { /* 还没起来 */ }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let seq = 0; const pending = new Map(); const errors = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id) { pending.get(m.id)?.(m); pending.delete(m.id); return; }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push('console.error: ' + m.params.args.map(a => a.value ?? a.description).join(' '));
  if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') errors.push('log: ' + m.params.entry.text + ' ' + (m.params.entry.url || ''));
});
const send = (method, params = {}) => new Promise((res, rej) => {
  const id = ++seq; pending.set(id, m => m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result));
  ws.send(JSON.stringify({ id, method, params }));
});
const ev = async expr => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};
const shot = async name => {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(OUT, name), Buffer.from(r.data, 'base64'));
};
const load = async (w, h, mobile) => {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: mobile ? 2 : 1, mobile });
  await send('Emulation.setTouchEmulationEnabled', { enabled: mobile, maxTouchPoints: 5 });
  await send('Page.navigate', { url: URL });
  for (let i = 0; i < 100; i++) { await sleep(100); if (await ev(`document.readyState === 'complete' && typeof startGame === 'function'`).catch(() => false)) break; }
  await ev(`startGame(); 1`);
};
await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable');
const result = {};

// ---------- 1. 17 时代 × 两套外观：真实出生、图集绘制、图标、攻击帧、坠落 ----------
await load(1280, 720, false);
const HELPERS = `
window.__spawn = (side, type, era, x, patch) => {
  const sd = G.sides[side];
  for (const u of G.units) if (u.side === side) u.__x = u.x, u.x = side ? 900 : 1000;   // 让开出生点
  const ok = trySpawn(sd, { type, age: era });
  for (const u of G.units) if (u.__x !== undefined) u.x = u.__x, delete u.__x;
  if (!ok) throw new Error('spawn refused ' + type + '/' + era);
  const u = G.units[G.units.length - 1]; u.x = x; Object.assign(u, patch || {}); return u;
};
window.__realStep = step; 1`;
await ev(HELPERS);
result.matrix = await ev(`(async () => {
  const out = { cases: 0, spriteDrawn: 0, icons: 0, attackFrames: 0, flashRows: 0, crashes: 0, fails: [] };
  for (const pack of ['original', 'chibi-tribe']) {
    if (pack === 'chibi-tribe') await ensureSpriteDlc();
    save.settings.spritePack = pack;
    for (let era = 0; era < 17; era++) {
      for (let i = 0; i < 100 && !spriteSheet(era, 5); i++) await new Promise(r => setTimeout(r, 50));
      G.units.length = 0; G.fx.length = 0; out.cases++;
      const tag = pack + '/' + era;
      const a = __spawn(0, 5, era, 700), b = __spawn(1, 5, era, 1100);
      if (!a.air || a.type !== 5) out.fails.push(tag + ' not air');
      const m = spriteMeta(era, 5);
      if (!m || m.cw !== 88 || !m.airTop) out.fails.push(tag + ' meta');
      ctx.save(); const drawn = drawUnitSprite(a) && drawUnitSprite(b); ctx.restore();
      drawn ? out.spriteDrawn++ : out.fails.push(tag + ' fallback drawing');
      const icon = unitIcon(5, era);
      icon && icon.startsWith('data:image/png') ? out.icons++ : out.fails.push(tag + ' icon');
      // 攻击帧：出手与收势
      a.swing = 0.2; const f1 = unitFrame(a); a.swing = 0.05; const f2 = unitFrame(a); a.swing = 0;
      const fly = unitFrame(a);
      (f1 === 6 && f2 === 7 && fly >= 0 && fly < 4) ? out.attackFrames++ : out.fails.push(tag + ' frames ' + [f1, f2, fly]);
      // 受击闪白行与每帧不为空
      const sheet = spriteSheet(era, 5), c = document.createElement('canvas'); c.width = m.cw * 12; c.height = m.ch * 3;
      const g = c.getContext('2d'); g.drawImage(sheet, 0, m.y, c.width, c.height, 0, 0, c.width, c.height);
      let okCells = 0;
      for (let r = 0; r < 3; r++) for (let f = 0; f < 12; f++) {
        const d = g.getImageData(f * m.cw, r * m.ch, m.cw, m.ch).data; let n = 0, nonWhite = 0;
        for (let p = 0; p < d.length; p += 4) if (d[p + 3] > 200) { n++; if (d[p] < 250 || d[p + 1] < 250 || d[p + 2] < 250) nonWhite++; }
        if (n > 20 && (r < 2 || nonWhite === 0)) okCells++;
      }
      okCells === 36 ? out.flashRows++ : out.fails.push(tag + ' cells ' + okCells);
      // 坠落：真实伤害结算产生的特效
      damageUnit(b, 1e9);
      const fx = G.fx.find(f => f.kind === 'die' && f.type === 5);
      if (fx && fx.alt === AIR_ALT) { fx.t = 0.3; const ok = drawDeathSprite(fx); fx.t = 0.9; (ok && drawDeathSprite(fx)) ? out.crashes++ : out.fails.push(tag + ' crash draw'); }
      else out.fails.push(tag + ' no crash fx');
    }
  }
  save.settings.spritePack = 'original';
  return out;
})()`);

// ---------- 1b. 规则回归：谁能打到空军、空军打基地 ----------
result.rules = await ev(`(() => {
  const realAi = aiThink; aiThink = () => {};
  const run = (setup, secs) => { newGame(S.diff); G.sides[1].gold = 0; const r = setup(); for (let i = 0; i < secs * 60; i++) step(1 / 60); return r; };
  const out = {};
  { const o = run(() => ({ air: __spawn(0, 5, 0, 900), foes: [0, 2, 3, 4].map((t, i) => __spawn(1, t, 0, 960 + i * 45)) }), 12);
    out.groundCannotHitAir = o.air.hp === o.air.maxHp && !o.air.dead; out.airHitsGround = o.foes.some(f => f.hp < f.maxHp || f.dead); }
  { const o = run(() => ({ air: __spawn(0, 5, 0, 900, { atk: 0 }), arc: __spawn(1, 1, 0, 1000) }), 6);
    out.archerHitsAir = o.air.hp < o.air.maxHp || o.air.dead; }
  { const o = run(() => ({ a: __spawn(0, 5, 0, 800), b: __spawn(1, 5, 0, 1000) }), 4);
    out.airIgnoresAir = o.a.hp === o.a.maxHp && o.b.hp === o.b.maxHp && o.a.x > o.b.x; }
  { const o = run(() => ({ air: __spawn(0, 5, 0, BASE_R - 400) }), 8); const lost = BASE_HP[0] - G.sides[1].baseHp, per = o.air.atk * AIR_BASE_DMG;
    out.baseDamage = { lost, perHit: per, wholeHits: lost > 0 && Math.abs(lost / per - Math.round(lost / per)) < 1e-6 }; }
  aiThink = realAi; newGame(S.diff);
  return out;
})()`);

// ---------- 2. 17 时代一字排开（缩到最远，暂停模拟） ----------
await ev(`G.units.length = 0; G.fx.length = 0; G.projs.length = 0; step = () => {}; G.zoom = 0; clampCam(); G.camX = 0; clampCam();
  const span = (BASE_R - BASE_L - 160) / 16;
  for (let era = 0; era < 17; era++) { const u = __spawn(era % 2, 5, era, BASE_L + 80 + era * span); u.hp = u.maxHp * (0.4 + era % 3 * 0.25); }
  1`);
await sleep(600); await shot('lineup-17-eras.png');
result.lineupZoom = await ev(`G.zoom`);

// ---------- 3. 实战：弓手对空、空军打地面、坠落 ----------
await ev(`step = __realStep; G.units.length = 0; G.fx.length = 0; G.zoom = 1; G.camX = 320; clampCam();
  G.sides[1].gold = 0; G.sides[0].gold = 0;
  __spawn(0, 5, 9, 800); __spawn(0, 5, 9, 880); __spawn(0, 0, 9, 930); __spawn(0, 3, 9, 860);
  __spawn(1, 1, 9, 1090); __spawn(1, 1, 9, 1130); __spawn(1, 0, 9, 1010); __spawn(1, 5, 9, 1180);
  1`);
for (let i = 0; i < 80; i++) { await sleep(100); if (await ev(`G.units.some(u => u.air && u.side === 0 && u.hp < u.maxHp) && G.projs.length > 1`)) break; }
await shot('battle-era9.png');
result.battle = await ev(`({ airHurt: G.units.filter(u => u.air && u.side === 0 && u.hp < u.maxHp).length, projs: G.projs.length, units: G.units.length })`);
// 击落一架，拍下坠中的一帧
await ev(`{ const t = G.units.find(u => u.air && u.side === 0 && !u.dead); t.hp = 1; damageUnit(t, 5); } 1`);
await sleep(330); await shot('crash-midfall.png');
result.crash = await ev(`(() => { const f = G.fx.find(f => f.kind === 'die' && f.type === 5); return f ? { t: +f.t.toFixed(2), alt: f.alt } : null; })()`);

// ---------- 4. 桌面真实操作：点兵种栏 → 排队 → 出兵 ----------
await ev(`newGame(S.diff); setMenu('units'); me().gold = 3000; me().era = 4; G.sides[1].gold = 0; 1`);
await sleep(300);
const rect = await ev(`(() => { const r = menuDefs.find(d => d.id === 'u5').el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`);
await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: rect.x, y: rect.y });
await sleep(200); await shot('desktop-hover-info.png');
result.desktopInfo = await ev(`infoEl.innerText`);
await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: rect.x, y: rect.y, button: 'left', clickCount: 1 });
await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: rect.x, y: rect.y, button: 'left', clickCount: 1 });
result.desktopQueue = await ev(`JSON.stringify(me().queue)`);
let spawned = false;
for (let i = 0; i < 80 && !spawned; i++) { await sleep(100); spawned = await ev(`G.units.some(u => u.air && u.side === 0 && u.age === 4)`); }
result.desktopSpawned = spawned;
await sleep(700); await shot('desktop-trained-era4.png');

// ---------- 5. 手机横屏 812×375：点两下出兵 ----------
await load(812, 375, true);
await ev(HELPERS);
await ev(`setMenu('units'); me().gold = 3000; me().era = 12; G.sides[1].gold = 0; 1`);
await sleep(300);
const tap = async () => {
  const r = await ev(`(() => { const r = menuDefs.find(d => d.id === 'u5').el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`);
  await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: r.x, y: r.y }] });
  await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await sleep(250);
};
await tap();
result.phone = await ev(`(() => { const b = [...bar.children].map(e => e.getBoundingClientRect()); const i = infoEl.getBoundingClientRect();
  return { selectedId, queueAfterFirstTap: me().queue.length, buttons: b.length, oneRow: b.every(r => Math.abs(r.top - b[0].top) < 1),
    inView: b.every(r => r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight), info: infoEl.innerText,
    infoInView: i.left >= 0 && i.right <= innerWidth && i.top >= 0, name: menuDefs.find(d => d.id === 'u5').bEl.textContent,
    nameFits: menuDefs.every(d => d.bEl.scrollWidth <= d.bEl.clientWidth + 1) }; })()`);
await shot('phone-selected-era12.png');
await tap();
result.phone.queueAfterSecondTap = await ev(`me().queue.length`);
spawned = false;
for (let i = 0; i < 80 && !spawned; i++) { await sleep(100); spawned = await ev(`G.units.some(u => u.air && u.side === 0 && u.age === 12)`); }
result.phone.spawned = spawned;
await sleep(700); await shot('phone-trained-era12.png');

result.errors = [...new Set(errors)];
writeFileSync(join(OUT, 'checks.json'), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
ws.close(); proc.kill();
