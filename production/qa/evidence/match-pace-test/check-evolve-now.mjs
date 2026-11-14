// 边界：AI 经验攒满立刻结成科技点；4 点 + 半价金币齐了，不等 600/300 秒就跃迁。
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const PORT = 9460;
const HTTP = 8771;
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const profile = mkdtempSync(join(tmpdir(), 'evolve-now-'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const http = spawn('python', ['-m', 'http.server', String(HTTP)], { cwd: process.cwd(), stdio: 'ignore' });
await sleep(600);
const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch { /* 未就绪 */ }
}
if (!target) { http.kill(); proc.kill(); throw new Error('chrome 没起来'); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let seq = 0;
const pending = new Map();
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id) { pending.get(m.id)?.(m); pending.delete(m.id); }
});
const send = (method, params = {}) => new Promise((res, rej) => {
  const id = ++seq;
  pending.set(id, m => m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result));
  ws.send(JSON.stringify({ id, method, params }));
});
const ev = async expr => {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};
await send('Page.enable');
await send('Page.navigate', { url: `http://127.0.0.1:${HTTP}/` });
for (let i = 0; i < 100; i++) {
  await sleep(100);
  if (await ev(`typeof newGame === 'function' && typeof step === 'function'`).catch(() => false)) break;
}

const report = await ev(`(() => {
  save.settings.sfx = 0; save.settings.music = 0;
  const out = [];
  const snap = () => {
    const ai = G.sides[1];
    return { t: Math.round(G.t * 10) / 10, pts: ai.pts, exp: Math.round(ai.exp * 10) / 10, gold: Math.round(ai.gold * 10) / 10, evolveT: Math.round(ai.evolveT * 100) / 100, age: ai.age };
  };
  newGame('easy');
  const me = G.sides[0], ai = G.sides[1];
  addExp(me, 599);
  out.push(['玩家 599 经验不发点', me.pts === 0 && me.exp === 599]);
  addExp(me, 1);
  out.push(['玩家满 600 立刻 1 点', me.pts === 1 && me.exp === 0]);
  addExp(me, 1800);
  out.push(['玩家一次结完剩余 3 点', me.pts === 4 && me.exp === 0]);

  ai.exp = 599; ai.gold = 1000; G.t = 10;
  step(1 / 60);
  out.push(['AI 599 经验、开局 10 秒不发点', ai.pts === 0 && ai.evolveT === 0]);

  newGame('easy');
  G.sides[1].exp = 2400; G.sides[1].gold = 100; G.t = 10;
  const goldBefore = G.sides[1].gold;
  step(1 / 60);
  const broke = snap();
  out.push(['经验够、金币不够：结满 4 点但不跃迁', broke.pts === 4 && broke.evolveT === 0 && broke.t < 30]);
  out.push(['只差金币时这一拍没有把金币花掉', G.sides[1].gold > goldBefore && G.sides[1].gold < 270]);

  G.sides[1].gold = 270;
  step(1 / 60);
  const paid = snap();
  out.push(['补到 270 金的下一拍立刻扣费开跃', paid.evolveT > 0 && paid.pts === 0 && paid.age === 0 && paid.gold < 270]);
  return out;
})()`);

http.kill();
proc.kill();
ws.close();
const failed = report.filter(row => !row[1]);
for (const [name, ok] of report) console.log((ok ? 'PASS' : 'FAIL') + '  ' + name);
if (failed.length) process.exit(1);
