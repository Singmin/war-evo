// Start python -m http.server 8765 before running this script with Node 22+.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const output = dirname(fileURLToPath(import.meta.url));
const shots = join(output, 'browser');
mkdirSync(shots, { recursive: true });
const chrome = process.argv[2] || join(process.env.LOCALAPPDATA, 'ms-playwright',
  'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const url = 'http://localhost:8765/';
const port = 9397;
const viewport = { width: 1366, height: 768, deviceScaleFactor: 1, mobile: false };
const types = [1, 2, 4];
const eras = [0, 2, 4, 6, 10, 12, 13, 15];
const errors = [];
const report = { viewport, battle: {}, archive: {} };
const profile = mkdtempSync(join(tmpdir(), 'd-roster-browser-'));
const proc = spawn(chrome, [`--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  '--autoplay-policy=no-user-gesture-required', 'about:blank'], { windowsHide: true });
let launchError;
proc.on('error', error => { launchError = error; });
proc.stderr.resume();
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function until(check, label) {
  for (let tries = 0; tries < 160; tries++) {
    if (launchError || proc.exitCode !== null) throw launchError || Error(`Chromium exited ${proc.exitCode}`);
    const result = await check();
    if (result) return result;
    await sleep(80);
  }
  throw Error(`Timed out: ${label}`);
}

let ws;
try {
  const page = await until(async () => {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      return targets.find(target => target.type === 'page');
    } catch {
      return null;
    }
  }, 'Chromium debugging endpoint');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true });
    ws.addEventListener('error', reject, { once: true });
  });
  let seq = 0;
  const pending = new Map();
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    const p = message.params;
    if (message.id) {
      pending.get(message.id)?.(message);
      pending.delete(message.id);
    } else if (message.method === 'Runtime.exceptionThrown') {
      errors.push(p.exceptionDetails.exception?.description || p.exceptionDetails.text);
    } else if (message.method === 'Runtime.consoleAPICalled' && p.type === 'error') {
      errors.push(p.args.map(value => value.value || value.description).join(' '));
    } else if (message.method === 'Log.entryAdded' && p.entry.level === 'error') {
      errors.push(p.entry.text + ' ' + (p.entry.url || ''));
    }
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++seq;
    pending.set(id, message => message.error ? reject(Error(message.error.message)) : resolve(message.result));
    ws.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result.value;
  };
  const shot = async name => {
    await evaluate('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    const image = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(join(shots, name + '.png'), Buffer.from(image.data, 'base64'));
  };
  const click = async expression => {
    const { x, y } = await evaluate(`(() => {
      const r = (${expression}).getBoundingClientRect();
      return { x: r.x+r.width/2, y: r.y+r.height/2 };
    })()`);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  };
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Log.enable');
  await send('Emulation.setDeviceMetricsOverride', viewport);
  await send('Page.navigate', { url });
  await until(() => evaluate("document.readyState === 'complete' && typeof startGame === 'function'"), 'game');
  await evaluate(`for (const id of ['intro', ...GUIDE_STEPS.map(s => s.id)]) save.guide[id] = 1;
    save.settings.spritePack = 'original'; startGame();
    window.advance = step; step = () => {}; aiThink = () => {};
    window.tick = n => { for (let i=0; i<n; i++) advance(STEP); };
    window.types = ${JSON.stringify(types)};
    window.buttonFor = type => menuDefs.find(d => d.id === 'u' + type).el;
    window.allies = () => types.map(type => G.units.find(u => u.side === 0 && u.type === type && !u.dead));
    window.recorded = []; window.originalBlit = blitSprite;
    blitSprite = (sheet, m, frame, row) => {
      const type = SPRITE_META[me().era].indexOf(m);
      if (types.includes(type)) recorded.push({type, frame, row});
      originalBlit(sheet,m,frame,row);
    };
    window.capture = () => { recorded = []; render(); return recorded; };
    window.place = (units, offset=0) => units.forEach((u,i) => { u.x=420+i*210+offset; });
    1`);
  report.version = await evaluate('SPRITE_VER');
  report.browser = await evaluate('navigator.userAgent');
  for (const era of eras) {
    const name = `era-${String(era).padStart(2,'0')}`;
    await evaluate(`newGame(S.diff); me().era = G.sides[1].era = ${era};
      me().gold = 9999; G.camX = 0; G.zoom = 1; setMenu('units'); 1`);
    await until(() => evaluate(`!!spriteSheet(${era}) && types.every(t => !!buttonFor(t).querySelector('img.un'))`), name+' atlas');
    for (const type of types) await click(`buttonFor(${type})`);
    assert.deepEqual(await evaluate('me().queue.map(q => q.type)'), types);
    const spawn = await evaluate(`(() => {
      const seen = new Set();
      for (let i=0; i<1400 && seen.size<3; i++) {
        tick(1);
        for (const u of allies().filter(Boolean)) {
          if (!seen.has(u.type)) { seen.add(u.type); u.x = 420+types.indexOf(u.type)*210; }
        }
      }
      place(allies());
      return { units: allies().map(u => [u.type,u.age,u.w,u.h,unitAlt(u)]), draws:capture() };
    })()`);
    assert.deepEqual(spawn.units.map(([t,e,w,h,alt]) => [t,e,alt]), types.map(t => [t,era,0]));
    assert.equal(spawn.draws.filter(d => d.row === 0).length, 3);
    await shot(name+'-spawn');
    const walk = await evaluate(`(() => {
      const units = allies(), start = units.map(u => u.x);
      const frames = units.map(() => new Set());
      for (let n=0; n<44; n++) {
        tick(1);
        units.forEach((u,i) => { if (u.walking) frames[i].add(unitFrame(u)); });
      }
      return units.map((u,i) => ({ distance:u.x-start[i], frames:[...frames[i]].sort() }));
    })()`);
    for (const entry of walk) {
      assert.ok(entry.distance > 0);
      assert.deepEqual(entry.frames, [0,1,2,3]);
    }
    await shot(name+'-walk');
    const attack = await evaluate(`(() => {
      const units = allies();
      place(units);
      window.targets = units.map((u,i) => {
        if (!trySpawn(G.sides[1], { type:u.type, age:u.age })) throw Error('enemy spawn blocked');
        const target=G.units.at(-1);
        target.x=u.x+58; target.cd=99; u.cd=.34;
        return target;
      });
      const frames=units.map(() => new Set());
      for (let i=0; i<26; i++) {
        units.forEach((u,j) => {
          moveLine([u], [targets[j]], 1, STEP);
          frames[j].add(unitFrame(u));
        });
        if (units.every(u => u.swing > 0)) break;
      }
      return { frames:frames.map(set => [...set]), draws:capture(), projs:G.projs.length,
               mountedHit:targets[1].hp<targets[1].maxHp };
    })()`);
    assert.deepEqual(attack.frames, types.map(() => [4,5,6]));
    assert.ok(attack.mountedHit && attack.projs >= 2);
    for (const type of types) assert.ok(attack.draws.some(d => d.type===type && d.frame===6 && d.row===0));
    await shot(name+'-attack');
    const hit = await evaluate(`allies().forEach(u => damageUnit(u, 1)); capture()`);
    for (const type of types) assert.ok(hit.some(d => d.type===type && d.row===2));
    await shot(name+'-flash');
    const death = await evaluate(`(() => {
      allies().forEach(u => damageUnit(u, 1e6));
      const seen=types.map(() => new Set());
      for (let n=0; n<27; n++) {
        for (const d of capture()) if (d.row===0 && d.frame>=8) seen[types.indexOf(d.type)].add(d.frame);
        tick(1);
      }
      return { frames:seen.map(set=>[...set]), draws:capture() };
    })()`);
    assert.deepEqual(death.frames, types.map(() => [8,9,10,11]));
    for (const type of types) assert.ok(death.draws.some(d => d.type===type && d.frame===11 && d.row===0));
    await shot(name+'-death');
    report.battle[era] = { spawn, walk, attack, hit, death };
    console.log(`Battle era ${era} passed`);
  }
  report.bootErrors = await evaluate('bootErrors');
  assert.deepEqual(report.bootErrors, []);
  await send('Page.navigate', { url:url+'tools/asset-browser/' });
  await until(() => evaluate("!!document.querySelector('#unit-0-1')"), 'asset browser');
  for (let era=0; era<17; era++) {
    for (const type of types) {
      const key = `${era}-${type}`;
      await evaluate(`document.querySelector('#unit-${key}').click(); 1`);
      const frames = await until(() => evaluate(`(() => {
        const strip = [...document.querySelectorAll('#unit-detail .filmstrip canvas')];
        return strip.length===12 && new Set(strip.map(c=>c.toDataURL())).size===12 ? strip.length : 0;
      })()`), key+' filmstrip');
      const played = await evaluate(`(async () => {
        const button = [...document.querySelectorAll('#unit-detail button')].find(b => b.textContent==='连续 12 帧');
        if (!button) return 0;
        button.click();
        const canvas = document.querySelector('#unit-detail .detail-preview canvas');
        canvas.scrollIntoView({ block: 'center' });
        const frames = new Set();
        const end = performance.now()+1900;
        while (frames.size<12 && performance.now()<end) {
          await new Promise(resolve => requestAnimationFrame(resolve));
          const ctx = canvas.getContext('2d');
          if (!ctx.getImageData(0,0,canvas.width,canvas.height).data.some((v,i) => i%4===3 && v)) continue;
          frames.add(canvas.toDataURL());
        }
        return frames.size;
      })()`);
      assert.equal(played, 12, key+' continuous playback');
      report.archive[key] = { frames, played };
      if (era === 10) await shot('archive-'+key);
      await evaluate(`new Promise(resolve => {
        const dialog = document.querySelector('#unit-detail');
        dialog.addEventListener('close', resolve, { once:true });
        dialog.close();
      })`);
    }
    console.log(`Archive era ${era} passed`);
  }
  assert.deepEqual(errors, []);
  console.log('8 battle eras, 40 battle screenshots, and all 51 archive previews passed.');
} finally {
  report.consoleErrors = [...new Set(errors)];
  writeFileSync(join(output,'browser-checks.json'), JSON.stringify(report,null,2)+'\n');
  ws?.close();
  proc.kill();
}
