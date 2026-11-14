// 练兵场 + 右上角大招按钮：无头 Chromium 截图与 AI 模拟。node verify.mjs <输出目录> <临时目录>
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2], SCRATCH = process.argv[3];
const URL = 'http://localhost:8766/', PORT = 9351;
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${join(SCRATCH, 'profile-tg')}`, 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) { await sleep(200); try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch { } }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let seq = 0; const pending = new Map(); const errors = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id) { pending.get(m.id)?.(m); pending.delete(m.id); return; }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push('console.error: ' + m.params.args.map(a => a.value ?? a.description).join(' '));
});
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, m => m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const ev = async expr => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text); return r.result.value; };
const shot = async name => { const r = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(join(OUT, name), Buffer.from(r.data, 'base64')); };
const load = async (w, h, mobile) => {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: mobile ? 2 : 1, mobile });
  await send('Emulation.setTouchEmulationEnabled', { enabled: mobile, maxTouchPoints: 5 });
  await send('Page.navigate', { url: URL });
  for (let i = 0; i < 100; i++) { await sleep(100); if (await ev(`document.readyState === 'complete' && typeof startGame === 'function'`).catch(() => false)) break; }
  await ev(`startGame(); 1`); await sleep(400);
};
await send('Runtime.enable'); await send('Page.enable');
const result = { checks: [] };
const check = (name, ok, detail) => result.checks.push({ name, ok: !!ok, detail });

// 1. 桌面：大招就绪（闪烁）+ 底栏六个按钮
await load(1280, 720, false);
const geo = await ev(`G.sides[0].specialCd = 0; refreshMenu();
  const b = document.getElementById('btnSpecial').getBoundingClientRect(), g = document.getElementById('game').getBoundingClientRect();
  ({ btn: [b.left - g.left, b.top - g.top, b.right - g.left, b.bottom - g.top], gw: g.width, cls: document.getElementById('btnSpecial').className,
     bar: [...document.querySelectorAll('#bar .mb')].filter(e => e.style.display !== 'none').map(e => e.querySelector('b').textContent),
     barOverflow: document.getElementById('bar').scrollWidth > document.getElementById('bar').clientWidth + 1 })`);
check('大招按钮在右上半区', geo.btn[0] > geo.gw * 0.7 && geo.btn[2] <= geo.gw + 1 && geo.btn[1] < 300, geo);
check('就绪时 ready 类（闪烁）', geo.cls.includes('ready'), geo.cls);
check('底栏无大招、采矿场和练兵场单独一格', !geo.bar.some(t => /陨石|大招/.test(t)) && geo.bar.includes('采矿场') && geo.bar.includes('练兵场'), geo.bar);
check('底栏不溢出', !geo.barOverflow);
await sleep(700); await shot('desktop-special-ready.png');
// 冷却
await ev(`G.sides[0].specialCd = 25; refreshMenu(); 1`); await sleep(200); await shot('desktop-special-cooldown.png');
const cd = await ev(`({ cls: document.getElementById('btnSpecial').className, txt: document.getElementById('btnSpecial').textContent })`);
check('冷却显示秒数且不闪烁', !cd.cls.includes('ready') && cd.cls.includes('cool') && /25 秒/.test(cd.txt), cd);
// 鼠标悬停练兵场看说明
await ev(`G.sides[0].gold = 600; G.sides[0].specialCd = 0; refreshMenu(); 1`);
const dr = await ev(`(() => { const r = [...document.querySelectorAll('#bar .mb')].find(e => e.textContent.includes('练兵场')).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()`);
await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: dr[0], y: dr[1] }); await sleep(300);
const info = await ev(`document.getElementById('info').textContent`);
check('练兵场说明含生命攻击预览', /练兵场 Lv1/.test(info) && /→/.test(info), info);
await shot('desktop-drill-info.png');
// 真实点击大招按钮
const sp = await ev(`(() => { const r = document.getElementById('btnSpecial').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()`);
await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: sp[0], y: sp[1], button: 'left', clickCount: 1 });
await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: sp[0], y: sp[1], button: 'left', clickCount: 1 });
await sleep(300);
check('点击大招按钮释放', await ev(`!!G.sides[0].special && G.sides[0].specialCd > 0`));
await sleep(500); await shot('desktop-special-casting.png');
// 快捷键 R / G
await ev(`G.sides[0].gold = 2000; G.sides[0].drill = 0; G.sides[0].mine = 0; 1`);
for (const key of ['r', 'g']) { await send('Input.dispatchKeyEvent', { type: 'keyDown', key, text: key }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key }); }
check('R 建练兵场、G 建采矿场', await ev(`G.sides[0].drill === 1 && G.sides[0].mine === 1`), await ev(`[G.sides[0].drill, G.sides[0].mine]`));
// 机械线：强化大招按钮出现后底栏 7 个仍不溢出
const mech = await ev(`G.sides[0].route = 'mech'; setMenu('root'); refreshMenu();
  ({ n: [...document.querySelectorAll('#bar .mb')].filter(e => e.style.display !== 'none').length,
     over: document.getElementById('bar').scrollWidth > document.getElementById('bar').clientWidth + 1 })`);
check('机械线 7 个按钮不溢出', mech.n === 7 && !mech.over, mech);
await sleep(200); await shot('desktop-mech-bar.png');

// 2. 手机横屏 812×375
await load(812, 375, true);
await ev(`G.sides[0].specialCd = 0; refreshMenu(); 1`); await sleep(600);
await shot('phone-812x375.png');
const ph = await ev(`(() => { const b = document.getElementById('btnSpecial').getBoundingClientRect(); return { r: [b.left, b.top, b.right, b.bottom], vw: innerWidth, vh: innerHeight }; })()`);
check('手机上大招按钮在屏幕内', ph.r[2] <= ph.vw + 1 && ph.r[0] > ph.vw * 0.6 && ph.r[3] < ph.vh * 0.6, ph);
// 触屏点一下即释放
const tp = [(ph.r[0] + ph.r[2]) / 2, (ph.r[1] + ph.r[3]) / 2];
await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: tp[0], y: tp[1] }] });
await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
await sleep(300);
check('触屏点一下释放大招', await ev(`!!G.sides[0].special`));

// 3. AI 模拟（不渲染，600 秒模拟时间）：both = 双方 AI；idle = 玩家不操作（只看敌方 AI 是否建造）
for (const mode of ['both', 'idle']) for (const diff of ['easy', 'normal', 'hard']) {
  const r = await ev(`(() => {
    newGame('${diff}'); const firsts = [null, null], mines = [null, null]; let t0 = 0;
    for (let i = 0; i < 600 * 30 && !G.over; i++) {
      step(1 / 30); t0 += 1 / 30;
      if ('${mode}' === 'both' && t0 >= 0.5) { t0 = 0; aiThink(0); }
      for (const s of [0, 1]) { if (firsts[s] === null && G.sides[s].drill > 0) firsts[s] = +G.t.toFixed(1); if (mines[s] === null && G.sides[s].mine > 0) mines[s] = +G.t.toFixed(1); }
    }
    return { t: +G.t.toFixed(1), over: G.over, winner: G.winner, drill: G.sides.map(s => s.drill), mine: G.sides.map(s => s.mine), firstMine: mines, firstDrill: firsts, age: G.sides.map(s => s.age) };
  })()`);
  result['ai_' + mode + '_' + diff] = r;
  if (diff === 'easy') check(mode + ' 简单 AI 不建练兵场', r.drill[1] === 0, r);
  else check(mode + ' ' + diff + ' AI 练兵场不超过规则上限', r.drill[1] <= (diff === 'hard' ? r.mine[1] : 1), r);
}
result.errors = errors;
check('页面无异常', errors.length === 0, errors);
writeFileSync(join(OUT, 'checks.json'), JSON.stringify(result, null, 2));
console.log(result.checks.map(c => (c.ok ? 'PASS ' : 'FAIL ') + c.name + (c.ok ? '' : '  ' + JSON.stringify(c.detail))).join('\n'));
for (const k of Object.keys(result).filter(k => k.startsWith('ai_'))) console.log(k, JSON.stringify(result[k]));
ws.close(); proc.kill();
