// 快速模拟：我方（同一套 AI，收入加成）压到敌方门口时，敌方买了什么兵、撑了多久
// node siege.mjs <输出 json> <临时目录> [收入倍数]
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2], SCRATCH = process.argv[3], MODE = process.argv[4] || 'new';
const PORT = 9349;
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${join(SCRATCH, 'profile-siege2')}`, 'about:blank'], { stdio: 'ignore' });
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


if (MODE === 'old') await ev(`fetch('/production/backups/air-vs-air-siege-20261111/js/core/ai.js').then(r => r.text()).then(src => { (0, eval)(src.replace("'use strict';", '')); return 1; })`);
const TUNE = process.argv[5] || '{}';
const result = await ev(`(() => {
  for (const d of ['normal', 'hard']) Object.assign(AI_RECRUIT[d], ${TUNE});
  save.settings.sfx = 0; save.settings.music = 0; S.screen = 'sim';
  const realRandom = Math.random, realPersist = persist; persist = () => {};
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const realTrain = actTrain;
  const put = (side, type, era, x) => { const sd = G.sides[side]; const keep = G.units.filter(u => u.side === side); for (const u of keep) u.__x = u.x, u.x = 960;
    const ok = trySpawn(sd, { type, age: era }); for (const u of keep) u.x = u.__x; if (ok) G.units[G.units.length - 1].x = x; return ok; };
  const STACKS = { ground: [3, 3, 0, 0, 1, 1, 1, 4], mixed: [3, 0, 0, 1, 1, 5, 5, 4], air: [3, 0, 5, 5, 5, 1, 1] };
  const out = {};
  for (const diff of ['normal', 'hard']) for (const tier of [0, 2]) for (const stack of Object.keys(STACKS)) {
    const agg = { games: 0, buys: [0, 0, 0, 0, 0, 0], held: 0, aiWon: 0, baseLeft: 0, killed: 0, fallAt: [] };
    for (let seed = 1; seed <= 16; seed++) {
      Math.random = rng(seed * 104729 + tier * 31 + stack.length);
      newGame(diff);
      const era = [0, 1, 2][tier];
      for (const sd of G.sides) { sd.age = tier; sd.era = era; sd.path = [0, 1, 2].slice(0, tier + 1); sd.baseHp = BASE_HP[tier]; sd.gold = START_GOLD * pow2(tier);
        const rt = ERA_ROUTE[era]; if (rt) sd.route = rt; }
      STACKS[stack].forEach((t, i) => put(0, t, era, BASE_R - 90 - i * 34));
      actTrain = (sd, type) => { const err = realTrain(sd, type); if (!err && sd.s === 1) agg.buys[type]++; return err; };
      let tick = 0; const k0 = G.losses;
      while (!G.over && G.t < 120) {
        step(1 / 60);
        if (++tick % 720 === 0) put(0, STACKS[stack][(tick / 720) % STACKS[stack].length], era, BASE_R - 420);   // 我方每 12 秒补一个兵
      }
      agg.games++; agg.killed += G.losses; agg.towers = (agg.towers || 0) + G.sides[1].towers.filter(Boolean).length;
      if (!G.over) { agg.held++; agg.baseLeft += G.sides[1].baseHp / BASE_HP[tier]; } else if (G.winner === 0) agg.fallAt.push(Math.round(G.t)); else agg.aiWon++;
    }
    const tot = agg.buys.reduce((a, b) => a + b, 0) || 1;
    out[diff + '/tier' + tier + '/' + stack] = { buys: agg.buys, share: agg.buys.map(n => Math.round(n / tot * 100)), held: agg.held, aiWon: agg.aiWon, fell: agg.fallAt.length, playerUnitsKilled: agg.killed, towers: agg.towers, avgBaseLeftWhenHeld: agg.held ? +(agg.baseLeft / agg.held).toFixed(2) : null,
      avgFallAt: agg.fallAt.length ? Math.round(agg.fallAt.reduce((a, b) => a + b, 0) / agg.fallAt.length) : null };
  }
  actTrain = realTrain; Math.random = realRandom; persist = realPersist;
  return out;
})()`);
writeFileSync(OUT, JSON.stringify({ mode: MODE, order: '步兵,射手,骑兵,重装,炮兵,空军', note: '我方一支部队钉在敌方门口并每 12 秒补一个兵，每组 16 局，120 秒内敌方买了什么、基地是否守住', result }, null, 2));
for (const [k, a] of Object.entries(result)) console.log(k.padEnd(22), '购买%', JSON.stringify(a.share), '守住', a.held, '反推获胜', a.aiWon, '失守', a.fell, '剩余血', a.avgBaseLeftWhenHeld, '失守秒', a.avgFallAt, '击杀我方', a.playerUnitsKilled, '塔', a.towers);
ws.close(); proc.kill();
