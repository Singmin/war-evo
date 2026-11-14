// 节奏测试：AI 跃迁闸门 vs 玩家，3 难度 × 3 打法 × 3 种子
// node pace.mjs <输出目录>
// 只测只报告，不改 data.js。用 step(1/60) 直接推进游戏秒，speed 只影响现实时间（3 倍速现实 = 游戏秒 / 3）。
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2] || join(process.cwd(), 'production/qa/evidence/match-pace-test/out');
const SCRATCH = process.argv[3] || join(process.cwd(), 'production/qa/evidence/match-pace-test/scratch');
mkdirSync(OUT, { recursive: true });
mkdirSync(SCRATCH, { recursive: true });

const PORT = 9351;
const URL = 'http://localhost:8765/';
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// 自起一个静态服务器（避免依赖外部进程）
const http = spawn('python', ['-m', 'http.server', '8765'], { cwd: process.cwd(), stdio: 'ignore' });
await sleep(800);

const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${join(SCRATCH, 'profile')}`, '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch { /* 未就绪 */ }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let seq = 0; const pending = new Map(); const errors = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id) { pending.get(m.id)?.(m); pending.delete(m.id); return; }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
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
await send('Runtime.enable');
await send('Page.enable');
await send('Page.navigate', { url: URL });
for (let i = 0; i < 100; i++) { await sleep(100); if (await ev(`document.readyState === 'complete' && typeof startGame === 'function' && typeof step === 'function'`).catch(() => false)) break; }

const HARNESS = `(async () => {
  save.settings.sfx = 0; save.settings.music = 0;
  S.screen = 'sim'; persist = () => {};
  const realRandom = Math.random;
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

  const realAddExp = addExp, realGrant = grantAiTechPoint, realEvolve = actEvolve;
  let EV = null;
  function beginEvents() { EV = { grants: [], evolves: [], playerDone: [], aiEvolveDone: [], idle: [], aiCumExp: 0, exp4T: null, got4T: null }; }

  addExp = function (sd, v) {
    if (EV && sd.s === 1) {
      EV.aiCumExp += v;
      if (sd.got < ERA_PTS && EV.exp4T == null && EV.aiCumExp >= ERA_PTS * PT_EXP[sd.age]) EV.exp4T = Math.round(G.t * 10) / 10;
    }
    return realAddExp(sd, v);
  };
  grantAiTechPoint = function (sd) {
    const before = sd.pts;
    const interval = sd.age < G.sides[0].age ? AI_BEHIND_POINT_INTERVAL : AI_TECH_POINT_INTERVAL;
    const beforeExp = sd.exp, need = ptNeed(sd);
    realGrant(sd);
    if (EV && sd.pts > before) {
      const t = Math.round(G.t * 10) / 10;
      EV.grants.push({ t, pts: sd.pts, expAtSettle: Math.round(beforeExp * 10) / 10, need, interval, pAge: G.sides[0].age, aAge: sd.age });
      if (sd.got === ERA_PTS) { EV.got4T = t; EV.idle.push({ age: sd.age, exp4T: EV.exp4T, got4T: t, idle: EV.exp4T == null ? null : Math.round((t - EV.exp4T) * 10) / 10, interval }); }
    }
  };
  actEvolve = function (sd, e) {
    const r = realEvolve(sd, e);
    if (EV && r === null) EV.evolves.push({ t: Math.round(G.t * 10) / 10, side: sd.s, fromAge: sd.age, toAge: sd.age + 1, toEra: e, name: AGES[e] });
    return r;
  };

  function aiBlocker(ai) {
    const child = eraChildren(ai.era)[0];
    const blockText = eraBlock(ai, child);
    const interval = ai.age < G.sides[0].age ? AI_BEHIND_POINT_INTERVAL : AI_TECH_POINT_INTERVAL;
    const need = ptNeed(ai);
    let reason;
    if (aiEvolveTimeLeft(ai) > 0) reason = '停留不足300秒';
    else if (ai.pts < ERA_PTS) reason = (ai.exp >= need && G.t - ai.lastAiPointAt < interval) ? '经验够了但等结算间隔' : '科技点不足';
    else if (ai.gold < evolveGold(ai)) reason = '金币不足';
    else reason = '应跃迁未跃迁(疑似bug)';
    return { blockText, reason, pts: ai.pts, exp: Math.round(ai.exp * 10) / 10, ptNeed: need, gold: Math.round(ai.gold * 10) / 10, evolveGold: evolveGold(ai), eraStay: Math.round((G.t - ai.eraStartedAt) * 10) / 10, sinceLastPoint: Math.round((G.t - ai.lastAiPointAt) * 10) / 10, interval };
  }

  function playerThink(strategy) {
    const me = G.sides[0];
    if (G.over || me.evolveT > 0) return;
    const foes = G.units.some(u => u.side === 1 && !u.dead);

    // 1. 大招：冷却好且场上有敌兵就放（清兵 → 击杀 → 经验/金币）
    if (me.specialCd <= 0 && !me.special && foes) { if (!actSpecial(me)) return; }

    // 2. 采矿场：早期补 1 级（经济撑住，也更快攒到跃迁金币）
    if (me.mine < 1 && G.t > 25 && me.gold > MINE_COST[0] + 110) { actMine(me); return; }
    // 3. 练兵场：1 级（兵更硬）
    if (me.drill < 1 && G.t > 45 && me.gold > DRILL_COST[0] + 130) { actDrill(me); return; }
    // 4. 防御塔：一座都没有时补一座轻塔，减少被压死
    if (!me.towers.some(Boolean) && G.t > 40 && me.gold > towerStats(0, me.era).price + 90) { actBuild(me, 0); return; }

    // 5. 跃迁（A/B 速升）
    if (strategy !== 'C') {
      const cost = evolveGold(me);
      if (me.pts >= ERA_PTS && me.gold >= cost) { const ch = eraChildren(me.era); if (ch.length) { actEvolve(me, ch[0]); return; } }
      if (me.pts >= ERA_PTS) { // 攒钱：只把超出跃迁费的部分补兵
        const excess = me.gold - cost;
        if (me.queue.length < 2 && excess > 0) { for (const t of [0, 1, 2]) { const p = unitStats(t, me.era, me).price; if (p <= excess) { actTrain(me, t); break; } } }
        return;
      }
    }

    // 6. 出兵
    const maxQ = strategy === 'B' ? 5 : 3;
    if (me.queue.length >= maxQ) return;
    const order = strategy === 'B' ? [0, 1, 0, 1, 2, 0, 1] : [0, 1, 2, 0, 1, 3, 4, 0, 1, 5];
    const t = order[me._pc % order.length]; me._pc = (me._pc || 0) + 1;
    const p = unitStats(t, me.era, me).price;
    if (p <= me.gold) actTrain(me, t);
  }

  function runMatch(diff, strategy, seed, adj0) {
    Math.random = rng(seed * 7919 + diff.length * 131 + strategy.charCodeAt(0) * 7 + (adj0 ? 1009 : 0));
    beginEvents();
    newGame(diff);
    if (adj0 || diff === 'normal') G.aiAdjustment = 0;
    const P = G.sides[0], A = G.sides[1]; P._pc = 0;
    const r = { diff, strategy, seed, aiAdjustment: G.aiAdjustment, stop: '', endT: 0, winner: -1 };
    let lastDiff = 0, d1 = 0, d2 = 0; const diffLog = [];
    const T = 2700; let gs = 0;
    for (; gs < T && !G.over; gs++) {
      for (let i = 0; i < 60; i++) {
        const ev0 = P.evolveT, ev1 = A.evolveT;
        step(1 / 60);
        if (ev0 > 0 && P.evolveT === 0) EV.playerDone.push({ t: Math.round(G.t * 10) / 10, playerAge: P.age, aiAge: A.age, ai: aiBlocker(A) });
        if (ev1 > 0 && A.evolveT === 0) { EV.aiEvolveDone.push({ t: Math.round(G.t * 10) / 10, aiAge: A.age }); EV.aiCumExp = 0; EV.exp4T = null; EV.got4T = null; }
        if (i % 30 === 0) playerThink(strategy);
        const d = P.age - A.age;
        if (d === 1) d1 += 1 / 60; else if (d === 2) d2 += 1 / 60;
        if (d !== lastDiff) { diffLog.push({ t: Math.round(G.t * 10) / 10, to: d }); lastDiff = d; }
      }
    }
    r.endT = Math.round(G.t * 10) / 10;
    r.stop = G.over ? (G.winner === 0 ? '玩家拆掉AI基地' : 'AI拆掉玩家基地') : (P.age >= 2 && A.age >= 2 ? '双方均到第3时代' : '满45游戏分钟');
    r.winner = G.winner;
    r.playerEras = EV.evolves.filter(e => e.side === 0);
    r.aiEras = EV.evolves.filter(e => e.side === 1);
    r.aiGrants = EV.grants;
    r.playerDone = EV.playerDone;
    r.aiEvolveDone = EV.aiEvolveDone;
    r.idle = EV.idle;
    r.diffLog = diffLog;
    r.diffDur = { d1: Math.round(d1), d2: Math.round(d2) };
    r.maxDiff = diffLog.reduce((m, x) => Math.max(m, Math.abs(x.to)), 0);
    r.evidence = {
      player: { age: P.age, era: AGES[P.era], mine: P.mine, drill: P.drill, towers: P.towers.filter(Boolean).length, baseHp: Math.round(P.baseHp) },
      ai: { age: A.age, era: AGES[A.era], mine: A.mine, drill: A.drill, towers: A.towers.filter(Boolean).length, baseHp: Math.round(A.baseHp) },
      kills: G.kills, losses: G.losses,
    };
    return r;
  }

  const saveAdj = save.stats.normal.aiAdjustment;
  const out = { saveNormalAiAdjustment: saveAdj, matches: [] };
  for (const diff of ['easy', 'normal', 'hard']) {
    for (const strategy of ['A', 'B', 'C']) {
      for (let seed = 1; seed <= 3; seed++) {
        save.stats.normal.streak = 0; save.stats.normal.aiAdjustment = 0; // 归零，避免连胜连败漂移
        out.matches.push(runMatch(diff, strategy, seed, diff === 'normal'));
      }
    }
  }
  // 普通难度 adj=0 对照列（内部仍按 normal 跑，只改标签；全新 profile 存档 aiAdjustment 本来就是 0）
  for (const strategy of ['A', 'B', 'C']) {
    for (let seed = 1; seed <= 3; seed++) {
      save.stats.normal.streak = 0; save.stats.normal.aiAdjustment = 0;
      const m = runMatch('normal', strategy, seed, true); m.diff = 'normal-adj0';
      out.matches.push(m);
    }
  }

  // ---- 3 倍速现实换算验证：跑真实帧循环 3 秒现实，看 G.t 是否 ≈ 9 ----
  const speedCheck = await new Promise(res => {
    save.stats.normal.streak = 0; save.stats.normal.aiAdjustment = 0;
    newGame('normal'); S.speed = 3; S.screen = 'play';
    const t0 = G.t; const w0 = performance.now();
    const tick = () => { if (performance.now() - w0 >= 3000) { S.screen = 'sim'; res({ realMs: Math.round(performance.now() - w0), gameDt: Math.round((G.t - t0) * 10) / 10, ratio: +((G.t - t0) / ((performance.now() - w0) / 1000)).toFixed(2), speed: S.speed }); } else requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  });

  Math.random = realRandom;
  addExp = realAddExp; grantAiTechPoint = realGrant; actEvolve = realEvolve;
  return JSON.stringify({ ...out, speedCheck, errors: [] });
})()`;

const resultJson = await ev(HARNESS);
writeFileSync(join(OUT, 'results.json'), resultJson);
const data = JSON.parse(resultJson);

// ---- 汇总打印 ----
const fmt = s => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;
const eraLine = list => list.length ? list.map(e => `${e.toAge}@${fmt(e.t)}`).join(' ') : '—';
console.log('save 普通难度 aiAdjustment =', data.saveNormalAiAdjustment);
console.log('3倍速换算验证:', JSON.stringify(data.speedCheck));
console.log('\n总表（难度 × 打法 × 种子）：');
console.log(['难度', '打法', '种', '玩家各时代完成', 'AI各时代完成', '最大差', '差1秒', '差2秒', '结束', 'AI主因'].join(' | '));
for (const m of data.matches) {
  const mainReason = m.playerDone.length ? m.playerDone[m.playerDone.length - 1].ai.reason : '—';
  console.log([m.diff, m.strategy, m.seed, eraLine(m.playerDone.map(d => ({ toAge: d.playerAge, t: d.t }))), eraLine(m.aiEvolveDone.map(d => ({ toAge: d.aiAge, t: d.t }))), m.maxDiff, m.diffDur.d1, m.diffDur.d2, m.stop, mainReason].join(' | '));
}

ws.close(); proc.kill(); http.kill();
process.exit(0);
