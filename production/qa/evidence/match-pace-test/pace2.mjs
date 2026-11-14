// 针对性实验：构造「玩家领先 2 级」局面，测 90 秒间隔能否追回，以及压制是否饿死 AI 科技点。
// 只测只报告，不改 data.js。用 step(1/60) 推进游戏秒。
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2] || join(process.cwd(), 'production/qa/evidence/match-pace-test/out');
const SCRATCH = process.argv[3] || join(process.cwd(), 'production/qa/evidence/match-pace-test/scratch');
mkdirSync(OUT, { recursive: true });

const PORT = 9352;
const URL = 'http://localhost:8765/';
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const http = spawn('python', ['-m', 'http.server', '8765'], { cwd: process.cwd(), stdio: 'ignore' });
await sleep(800);

const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${join(SCRATCH, 'profile2')}`, '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch { /* 未就绪 */ }
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
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: URL });
for (let i = 0; i < 100; i++) { await sleep(100); if (await ev(`document.readyState === 'complete' && typeof startGame === 'function' && typeof step === 'function'`).catch(() => false)) break; }

const HARNESS = `(() => {
  save.settings.sfx = 0; save.settings.music = 0;
  S.screen = 'sim'; persist = () => {};
  const realRandom = Math.random;
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const realGrant = grantAiTechPoint, realEvolve = actEvolve;
  let EV = null;
  function beginEvents() { EV = { grants: [], evolves: [], aiCumExp: 0 }; }
  grantAiTechPoint = function (sd) {
    const before = sd.pts; const interval = sd.age < G.sides[0].age ? AI_BEHIND_POINT_INTERVAL : AI_TECH_POINT_INTERVAL;
    const beforeExp = sd.exp, need = ptNeed(sd);
    realGrant(sd);
    if (EV && sd.pts > before) EV.grants.push({ t: Math.round(G.t * 10) / 10, pts: sd.pts, expAtSettle: Math.round(beforeExp * 10) / 10, need, interval, pAge: G.sides[0].age, aAge: sd.age });
  };
  actEvolve = function (sd, e) {
    const r = realEvolve(sd, e);
    if (EV && r === null) EV.evolves.push({ t: Math.round(G.t * 10) / 10, side: sd.s, fromAge: sd.age, toAge: sd.age + 1, toEra: e });
    return r;
  };

  function forceAge(sd, targetAge) {
    while (sd.age < targetAge) {
      const ch = eraChildren(sd.era)[0];
      sd.gold = 100000; sd.pts = 100;
      if (actEvolve(sd, ch) !== null) throw new Error('forceEvolve failed at age ' + sd.age);
      for (let k = 0; k < 600 && sd.evolveT > 0; k++) step(1 / 60);
    }
  }

  function playerThink(strategy) {
    const me = G.sides[0];
    if (G.over || me.evolveT > 0) return;
    const foes = G.units.some(u => u.side === 1 && !u.dead);
    if (me.specialCd <= 0 && !me.special && foes) { if (!actSpecial(me)) return; }
    if (me.mine < 1 && G.t > 25 && me.gold > MINE_COST[0] + 110) { actMine(me); return; }
    if (me.drill < 1 && G.t > 45 && me.gold > DRILL_COST[0] + 130) { actDrill(me); return; }
    if (!me.towers.some(Boolean) && G.t > 40 && me.gold > towerStats(0, me.era).price + 90) { actBuild(me, 0); return; }
    if (strategy !== 'C') {
      const cost = evolveGold(me);
      if (me.pts >= ERA_PTS && me.gold >= cost) { const ch = eraChildren(me.era); if (ch.length) { actEvolve(me, ch[0]); return; } }
      if (me.pts >= ERA_PTS) { const excess = me.gold - cost; if (me.queue.length < 2 && excess > 0) { for (const t of [0, 1, 2]) { const p = unitStats(t, me.era, me).price; if (p <= excess) { actTrain(me, t); break; } } } return; }
    }
    const maxQ = strategy === 'B' ? 5 : 3;
    if (me.queue.length >= maxQ) return;
    const order = strategy === 'B' ? [0, 1, 0, 1, 2, 0, 1] : [0, 1, 2, 0, 1, 3, 4, 0, 1, 5];
    const t = order[me._pc % order.length]; me._pc = (me._pc || 0) + 1;
    const p = unitStats(t, me.era, me).price;
    if (p <= me.gold) actTrain(me, t);
  }

  function runConstruct(diff, seed, mode) {
    Math.random = rng(seed * 7919 + diff.length * 131 + mode.length * 7);
    beginEvents();
    newGame(diff); G.aiAdjustment = 0;
    const P = G.sides[0], A = G.sides[1]; P._pc = 0;
    forceAge(P, 2);                          // 玩家领先 2 级（age 2 vs AI age 0）
    P.gold = 600; P.pts = 0; P.exp = 0;      // 模拟刚跃迁完：没有富余点数和金币
    if (mode === 'q3') {                      // q3：再加满塔和大军，彻底压制 AI 击杀
      for (let i = 0; i < P.slots; i++) if (!P.towers[i]) { P.towers[i] = { type: 1, age: P.era, cd: 0, aim: 0, lvl: 0, spent: 0 }; }
      P.gold = 5000;
    }
    const r = { diff, seed, mode, setupT: Math.round(G.t * 10) / 10, playerStartAge: P.age, aiStartAge: A.age, aiStartEraStay: A.eraStartedAt };
    let lastDiff = 0; const diffLog = [];
    const aiExpSamples = [];
    const T = mode === 'q3' ? 1200 : 1800; let gs = 0;
    for (; gs < T && !G.over; gs++) {
      for (let i = 0; i < 60; i++) {
        step(1 / 60);
        if (i % 30 === 0) playerThink('A');
        const d = P.age - A.age;
        if (d !== lastDiff) { diffLog.push({ t: Math.round(G.t * 10) / 10, to: d }); lastDiff = d; }
      }
      if (gs % 30 === 0) aiExpSamples.push({ t: G.t, aiExp: Math.round(A.exp), aiCumExp: Math.round(EV.aiCumExp), aiPts: A.pts });
    }
    r.endT = Math.round(G.t * 10) / 10;
    r.stop = G.over ? (G.winner === 0 ? '玩家拆掉AI基地' : 'AI拆掉玩家基地') : '时间到';
    r.winner = G.winner;
    r.aiGrants = EV.grants;
    r.aiEvolves = EV.evolves.filter(e => e.side === 1);
    r.playerEvolves = EV.evolves.filter(e => e.side === 0);
    r.diffLog = diffLog;
    r.aiExpSamples = aiExpSamples;
    r.evidence = {
      player: { age: P.age, era: AGES[P.era], mine: P.mine, drill: P.drill, towers: P.towers.filter(Boolean).length, baseHp: Math.round(P.baseHp) },
      ai: { age: A.age, era: AGES[A.era], mine: A.mine, drill: A.drill, towers: A.towers.filter(Boolean).length, baseHp: Math.round(A.baseHp) },
      kills: G.kills, losses: G.losses,
    };
    return r;
  }

  const out = { matches: [] };
  for (const diff of ['normal', 'hard']) {
    for (const mode of ['q2', 'q3']) {
      for (let seed = 1; seed <= 3; seed++) {
        save.stats.normal.streak = 0; save.stats.normal.aiAdjustment = 0;
        out.matches.push(runConstruct(diff, seed, mode));
      }
    }
  }
  Math.random = realRandom; grantAiTechPoint = realGrant; actEvolve = realEvolve;
  return JSON.stringify(out);
})()`;

const resultJson = await ev(HARNESS);
writeFileSync(join(OUT, 'results2.json'), resultJson);
const data = JSON.parse(resultJson);
const fmt = s => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;
for (const m of data.matches) {
  console.log(`\n=== ${m.diff} ${m.mode} 种子${m.seed} | 结束:${m.stop} @${fmt(m.endT)} | 玩家age ${m.evidence.player.age} vs AI age ${m.evidence.ai.age} ===`);
  console.log('  AI 拿点:', m.aiGrants.map(g => `pts${g.pts}@${fmt(g.t)}(间隔${g.interval},exp${g.expAtSettle})`).join(' ') || '(无)');
  console.log('  AI 跃迁:', m.aiEvolves.map(e => `→age${e.toAge}@${fmt(e.t)}`).join(' ') || '(无)');
  console.log('  玩家跃迁:', m.playerEvolves.map(e => `→age${e.toAge}@${fmt(e.t)}`).join(' ') || '(无)');
  console.log('  时代差变化:', m.diffLog.map(d => `${d.to}@${fmt(d.t)}`).join(' → '));
  console.log('  AI 经验采样(每30s):', m.aiExpSamples.map(s => `${s.aiCumExp}`).join(','));
}
ws.close(); proc.kill(); http.kill();
process.exit(0);
