// 快速模拟：我方（同一套 AI，收入加成）压到敌方门口时，敌方买了什么兵、撑了多久
// node siege.mjs <输出 json> <临时目录> [收入倍数]
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2], SCRATCH = process.argv[3], BOOST = +(process.argv[4] || 1.8);
const PORT = 9348;
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${join(SCRATCH, 'profile-siege')}`, 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch { /* 还没起来 */ }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let seq = 0; const pending = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id) { pending.get(m.id)?.(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => {
  const id = ++seq; pending.set(id, m => m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result));
  ws.send(JSON.stringify({ id, method, params }));
});
const ev = async expr => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};
await send('Page.enable');
await send('Page.navigate', { url: 'http://localhost:8765/?sim=' + Date.now() });
for (let i = 0; i < 100; i++) { await sleep(100); if (await ev(`document.readyState === 'complete' && typeof startGame === 'function'`).catch(() => false)) break; }

const result = await ev(`(() => {
  save.settings.sfx = 0; save.settings.music = 0;
  S.screen = 'sim';                       // 主循环不再推进，只由这里推进
  const realRandom = Math.random, realPersist = persist; persist = () => {};
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const realTrain = actTrain;
  const out = {};
  for (const diff of ['easy', 'normal', 'hard']) {
    const agg = { games: 0, aiWins: 0, playerWins: 0, timeouts: 0, avgLen: 0, siegeBuys: [0, 0, 0, 0, 0, 0], calmBuys: [0, 0, 0, 0, 0, 0], siegeSeconds: 0, towersBuilt: 0, lens: [] };
    for (let seed = 1; seed <= 10; seed++) {
      Math.random = rng(seed * 7919 + diff.length);
      newGame(diff);
      G.sides[0].mod.income *= ${BOOST};
      actTrain = (sd, type) => {
        const err = realTrain(sd, type);
        if (!err && sd.s === 1) {
          const besieged = G.units.some(u => u.side === 0 && !u.dead && Math.abs(u.x - BASE_R) < AI_SP_GATE);
          (besieged ? agg.siegeBuys : agg.calmBuys)[type]++;
        }
        return err;
      };
      let tick = 0;
      while (!G.over && G.t < 1500) {
        step(1 / 60);
        if (++tick % 30 === 0) {
          aiThink(0);
          if (G.units.some(u => u.side === 0 && !u.dead && Math.abs(u.x - BASE_R) < AI_SP_GATE)) agg.siegeSeconds += 0.5;
        }
      }
      agg.games++; agg.lens.push(Math.round(G.t));
      if (!G.over) agg.timeouts++; else if (G.winner === 1) agg.aiWins++; else agg.playerWins++;
      agg.towersBuilt += G.sides[1].towers.filter(Boolean).length;
    }
    agg.avgLen = Math.round(agg.lens.reduce((a, b) => a + b, 0) / agg.lens.length);
    const tot = agg.siegeBuys.reduce((a, b) => a + b, 0) || 1;
    agg.siegeShare = agg.siegeBuys.map(n => +(n / tot).toFixed(3));
    out[diff] = agg;
  }
  actTrain = realTrain; Math.random = realRandom; persist = realPersist;
  return out;
})()`);
writeFileSync(OUT, JSON.stringify({ order: '步兵,射手,骑兵,重装,炮兵,空军', playerIncomeBoost: BOOST, result }, null, 2));
for (const [d, a] of Object.entries(result)) console.log(d, 'AI胜', a.aiWins, '玩家胜', a.playerWins, '超时', a.timeouts, '均长', a.avgLen, '被堵秒', a.siegeSeconds, '堵门购买', JSON.stringify(a.siegeBuys), '占比', JSON.stringify(a.siegeShare), '平时', JSON.stringify(a.calmBuys));
ws.close(); proc.kill();
