// 验证 ai.js「攒钱跃迁不再躺平」改动：被压还手 / 没被打时建矿 / 没被打且钱少仍攒钱不出兵
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2] || join(process.cwd(), 'production/qa/evidence/match-pace-test/out');
const SCRATCH = process.argv[3] || join(process.cwd(), 'production/qa/evidence/match-pace-test/scratch');
mkdirSync(OUT, { recursive: true });
const PORT = 9400;
const exe = join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const http = spawn('python', ['-m', 'http.server', '8765'], { cwd: process.cwd(), stdio: 'ignore' });
await sleep(800);
const proc = spawn(exe, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${join(SCRATCH, 'profile3')}`, '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) { await sleep(200); try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === 'page'); } catch { /* 未就绪 */ } }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let seq = 0; const pending = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id) { pending.get(m.id)?.(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; pending.set(id, m => m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const ev = async expr => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text); return r.result.value; };
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: 'http://localhost:8765/' });
for (let i = 0; i < 100; i++) { await sleep(100); if (await ev(`document.readyState === 'complete' && typeof step === 'function'`).catch(() => false)) break; }

const HARNESS = `(() => {
  save.settings.sfx = 0; save.settings.music = 0;
  S.screen = 'sim'; persist = () => {};
  const realRandom = Math.random; Math.random = () => 0.5;   // 去掉随机抖动，行为确定

  function spawnUnit(side, type, age, x) {
    const sd = G.sides[side], st = unitStats(type, age, sd);
    G.units.push({ id: G.nextId++, side, type, age, st: ERA_ART[age][type], x, w: st.w, h: st.h, hp: st.hp, maxHp: st.hp, atk: st.atk, range: st.range, minRange: st.minRange, rate: st.rate, speed: st.speed, price: st.price, ranged: st.ranged, air: st.air, splash: st.splash, cd: 0.3, anim: 0, walking: false, hit: 0, swing: 0, dead: false });
  }
  const setup = (diff, age, gold, era) => {
    newGame(diff); G.aiAdjustment = 0;
    const A = G.sides[1];
    A.age = age; A.era = era; A.path = era ? [0, era] : [0];
    A.pts = 4; A.exp = 0; A.gold = gold; A.eraStartedAt = -400;   // 停留早已满 300 秒
    A.lastAiPointAt = -400;
    return A;
  };
  const run = (secs) => { for (let i = 0; i < secs * 60; i++) step(1 / 60); };

  const out = {};

  // 场景 A：被压到家门口（threat>0），应出兵/补塔还手，而不是躺平
  {
    const A = setup('normal', 0, 200, 0);
    spawnUnit(0, 0, 0, 1500); spawnUnit(0, 1, 0, 1560);   // 两个玩家兵打进 AI 半场
    const before = { q: A.queue.length, towers: A.towers.filter(Boolean).length, gold: A.gold, aiUnits: G.units.filter(u => u.side === 1).length };
    run(15);
    out.A_被压还手 = { before, after: { q: A.queue.length, towers: A.towers.filter(Boolean).length, gold: Math.round(A.gold), aiUnits: G.units.filter(u => u.side === 1).length }, pts: A.pts, evolved: A.age };
  }

  // 场景 B：没被打（threat=0）+ 青铜纪差钱攒跃迁，应建采矿场投资
  {
    const A = setup('normal', 1, 400, 1);   // age1 青铜，evolveGold=645，差 245
    G.t = 400;                               // 模拟已打了很久（跳过 G.t>40 的建矿时间门槛）
    const before = { mine: A.mine, gold: A.gold };
    run(15);
    out.B_无威胁建矿 = { before, after: { mine: A.mine, gold: Math.round(A.gold) }, pts: A.pts, evolved: A.age };
  }

  // 场景 C：没被打 + 金币太少建不起矿，仍应 return 攒钱（不出兵、不建塔）
  {
    const A = setup('normal', 0, 120, 0);
    const before = { q: A.queue.length, towers: A.towers.filter(Boolean).length, mine: A.mine, gold: A.gold };
    run(20);
    out.C_无威胁钱少仍攒钱 = { before, after: { q: A.queue.length, towers: A.towers.filter(Boolean).length, mine: A.mine, gold: Math.round(A.gold) }, pts: A.pts };
  }

  Math.random = realRandom;
  return JSON.stringify(out);
})()`;

const resultJson = await ev(HARNESS);
writeFileSync(join(OUT, 'results3.json'), resultJson);
console.log(resultJson);
ws.close(); proc.kill(); http.kill();
process.exit(0);
