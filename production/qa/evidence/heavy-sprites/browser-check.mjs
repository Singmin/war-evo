// Run after python -m http.server 8765.
// Usage: node browser-check.mjs [--mobile] [path-to-Chromium-headless-shell]
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const out = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const mobile = args.includes('--mobile');
const chrome = args.find(arg => arg !== '--mobile') || join(process.env.LOCALAPPDATA, 'ms-playwright',
  'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const url = 'http://127.0.0.1:8765/';
const port = 9372;
const eras = mobile ? [4, 15] : [0, 2, 4, 6, 12, 15];
const errors = [];
const viewport = mobile ? { width: 844, height: 390, deviceScaleFactor: 2, mobile: true } :
  { width: 1366, height: 768, deviceScaleFactor: 1, mobile: false };
const report = { viewport, battle: {}, archive: {} };
const profile = mkdtempSync(join(tmpdir(), 'heavy-sprites-browser-'));
const processChrome = spawn(chrome, [`--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, '--autoplay-policy=no-user-gesture-required', 'about:blank'],
  { stdio: ['ignore', 'ignore', 'pipe'], windowsHide: true });
let launchError = '';
let chromeLog = '';
processChrome.on('error', error => { launchError = error.message; });
processChrome.stderr.on('data', data => { chromeLog += data.toString(); });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function until(check, description) {
  for (let i = 0; i < 120; i++) {
    const value = await check();
    if (value) return value;
    await sleep(100);
  }
  throw new Error(`Timed out: ${description}`);
}

let ws;
try {
  const page = await until(async () => {
    if (launchError || processChrome.exitCode !== null) {
      throw new Error(launchError || chromeLog || `Chromium exited with code ${processChrome.exitCode}`);
    }
    try {
      const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      return targets.find(t => t.type === 'page');
    } catch {
      return null;
    }
  }, 'Chromium debugging endpoint');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(resolve => ws.addEventListener('open', resolve));
  let seq = 0;
  const pending = new Map();
  ws.addEventListener('message', e => {
    const m = JSON.parse(e.data);
    if (m.id) {
      pending.get(m.id)?.(m);
      pending.delete(m.id);
    } else if (m.method === 'Runtime.exceptionThrown') {
      errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    } else if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
      errors.push(m.params.args.map(x => x.value || x.description).join(' '));
    } else if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
      errors.push(m.params.entry.text + ' ' + (m.params.entry.url || ''));
    }
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++seq;
    pending.set(id, m => m.error ? reject(new Error(m.error.message)) : resolve(m.result));
    ws.send(JSON.stringify({ id, method, params }));
  });
  const evalPage = async expression => {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  const shot = async name => {
    await evalPage('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    const image = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(join(out, name + '.png'), Buffer.from(image.data, 'base64'));
  };
  const click = async expression => {
    const { x, y } = await evalPage(`(() => {
      const r = (${expression}).getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    })()`);
    if (mobile) {
      await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
      await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      return;
    }
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  };
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Log.enable');
  await send('Network.enable');
  await send('Network.setCacheDisabled', { cacheDisabled: true });
  await send('Emulation.setDeviceMetricsOverride', viewport);
  if (mobile) await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
  await send('Page.navigate', { url });
  await until(() => evalPage("document.readyState === 'complete' && typeof startGame === 'function'"), 'game scripts');
  await evalPage(`startGame(); save.settings.spritePack = 'original';
    window.advanceOne = step; step = () => {}; aiThink = () => {};
    window.tick = n => { for (let i = 0; i < n; i++) advanceOne(STEP); };
    window.captureBlits = () => { window.blits = []; render(); return blits; };
    window.originalBlit = blitSprite;
    blitSprite = (sheet, m, frame, row) => {
      if (m.articulated) blits.push([frame, row]);
      return originalBlit(sheet, m, frame, row);
    };
    window.blits = [];
    window.human = () => G.units.find(u => u.side === 0 && u.type === 3);
    window.foe = () => G.units.find(u => u.side === 1 && u.type === 3);
    window.heavyButton = () => menuDefs.find(d => d.id === 'u3').el;
    window.visibleIconIsFrameOne = async era => {
      const icon = heavyButton().querySelector('img.un');
      if (!icon) return false;
      await icon.decode();
      const m = spriteMeta(era, 3), s = spriteSheet(era, 3);
      const c = document.createElement('canvas'); c.width = m.cw; c.height = m.ch;
      const p = c.getContext('2d');
      p.drawImage(s, m.cw, m.y, m.cw, m.ch, 0, 0, m.cw, m.ch);
      const data = p.getImageData(0, 0, m.cw, m.ch).data;
      const xs = [], ys = [];
      for (let i = 0; i < data.length / 4; i++) if (data[i*4+3] === 255) {
        xs.push(i % m.cw); ys.push(Math.floor(i / m.cw));
      }
      const x = Math.min(...xs), y = Math.min(...ys);
      const w = Math.max(...xs)-x+1, h = Math.max(...ys)-y+1;
      const expected = p.getImageData(x, y, w, h).data;
      p.clearRect(0, 0, m.cw, m.ch); p.drawImage(icon, 0, 0);
      return icon.naturalWidth === w && icon.naturalHeight === h &&
        p.getImageData(0, 0, w, h).data.every((v, i) => v === expected[i]);
    }; 1`);
  report.atlasVersion = await evalPage('SPRITE_VER');
  for (const era of eras) {
    const prefix = (mobile ? 'mobile-era-' : 'era-') + String(era).padStart(2, '0');
    await evalPage(`newGame(S.diff); me().era = G.sides[1].era = ${era}; me().gold = 999;
      G.camX = 0; G.zoom = 1; setMenu('units'); 1`);
    await until(() => evalPage(`!!spriteSheet(${era}, 3) && !!heavyButton().querySelector('img.un')`), prefix + ' icon');
    assert.equal(await evalPage(`visibleIconIsFrameOne(${era})`), true);
    await click('heavyButton()');
    let touch = null;
    if (mobile) {
      await until(() => evalPage("selectedId === 'u3' && heavyButton().classList.contains('sel')"),
        prefix + ' touch selection');
      touch = await evalPage(`(() => {
        const bounds = [...bar.querySelectorAll('button')].map(b => b.getBoundingClientRect());
        return { selectedId, queueAfterFirstTap: me().queue.length,
          allButtonsVisible: bounds.every(r => r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight) };
      })()`);
      assert.deepEqual(touch, { selectedId: 'u3', queueAfterFirstTap: 0, allButtonsVisible: true });
      await shot(prefix + '-selected');
      await click('heavyButton()');
      await until(() => evalPage('me().queue.length > 0'), prefix + ' touch queue');
    }
    assert.equal(await evalPage(`me().queue.some(q => q.type === 3 && q.age === ${era})`), true);
    const spawned = await evalPage(`(() => {
      for (let n = 0; !human() && n < 480; n++) tick(1);
      const u = human();
      if (!u) return null;
      return { name: UNIT_NAMES[u.age][3], w: u.w, h: u.h, air: u.air, altitude: unitAlt(u), x: u.x,
        drawn: captureBlits().length > 0 };
    })()`);
    assert.ok(spawned?.drawn && !spawned.air && spawned.altitude === 0);
    assert.deepEqual([spawned.w, spawned.h], [46, era === 4 ? 64 : 44]);
    await shot(prefix + '-spawn');
    const walked = await evalPage(`(() => {
      const x = human().x, frames = new Set();
      for (let i = 0; i < 38; i++) { tick(1); if (human().walking) frames.add(unitFrame(human())); }
      return { distance: human().x-x, frames: [...frames].sort() };
    })()`);
    assert.ok(walked.distance > 0);
    assert.deepEqual(walked.frames, [0, 1, 2, 3]);
    await shot(prefix + '-walk');
    const attack = await evalPage(`(() => {
      const u = human();
      if (!trySpawn(G.sides[1], { type: 3, age: u.age })) throw Error('Could not spawn enemy heavy');
      const v = foe(); u.x += 220; v.x = u.x+82; v.cd = 99; u.cd = .34;
      const frames = new Set();
      for (let i = 0; i < 30; i++) {
        tick(1); frames.add(unitFrame(u));
        if (u.swing > .125) break;
      }
      return { frames: [...frames], hpLoss: v.maxHp-v.hp, blits: captureBlits() };
    })()`);
    assert.deepEqual(attack.frames, [4, 5, 6]);
    assert.ok(attack.hpLoss > 0 && attack.blits.some(([f,r]) => f === 6 && r === 0));
    await shot(prefix + '-attack');
    assert.equal(await evalPage('tick(9); unitFrame(human())'), 7);
    const hit = await evalPage(`(() => {
      foe().cd = 0; human().cd = 99; human().swing = 0; tick(1);
      return { hpLoss: human().maxHp-human().hp, flash: human().hit, blits: captureBlits() };
    })()`);
    assert.ok(hit.hpLoss > 0 && hit.flash > 0 && hit.blits[0]?.[1] === 2);
    await shot(prefix + '-hit');
    const death = await evalPage(`damageUnit(human(), 1e6); tick(9);
      ({ death: G.fx.find(f => f.kind === 'die' && f.type === 3), blits: captureBlits() })`);
    assert.equal(death.death?.alt, 0);
    assert.ok(death.blits.some(([f,r]) => f === 9 && r === 0));
    await shot(prefix + '-death');
    const wreck = await evalPage('tick(15); captureBlits()');
    assert.ok(wreck.some(([f,r]) => f === 11 && r === 0));
    await shot(prefix + '-wreck');
    report.battle[era] = { spawned, iconFrame: 1, walked, attack, recovery: 7, hit, death, wreck };
    if (touch) report.battle[era].touch = touch;
  }
  report.bootErrors = await evalPage('bootErrors');
  report.browser = await evalPage('navigator.userAgent');
  if (!mobile) {
    await send('Page.navigate', { url: url + 'tools/asset-browser/' });
    await until(() => evalPage("!!document.querySelector('#unit-0-3')"), 'asset browser');
    for (let era = 0; era < 17; era++) {
      await evalPage(`document.querySelector('#unit-${era}-3').click(); 1`);
      const info = await until(() => evalPage(`(() => {
        const frames = [...document.querySelectorAll('#unit-detail .filmstrip canvas')];
        const unique = new Set(frames.map(c => c.toDataURL())).size;
        return frames.length === 12 && unique === 12 ?
          { title: document.querySelector('#detail-title').textContent, frames: frames.length, unique } : null;
      })()`), 'asset browser era ' + era);
      report.archive[era] = info;
      if (eras.includes(era)) await shot('archive-era-' + String(era).padStart(2, '0'));
      await evalPage("document.querySelector('#unit-detail').close(); 1");
      await sleep(40);
    }
  }
  report.consoleErrors = [...new Set(errors)];
  assert.deepEqual(report.bootErrors, []);
  assert.deepEqual(report.consoleErrors, []);
  console.log(mobile ? `Checked ${eras.length} eras with landscape touch emulation.` :
    `Checked ${eras.length} eras in battle and 17 in the asset browser.`);
} finally {
  report.consoleErrors = [...new Set(errors)];
  writeFileSync(join(out, mobile ? 'mobile-browser-checks.json' : 'browser-checks.json'),
    JSON.stringify(report, null, 2) + '\n');
  ws?.close();
  processChrome.kill();
}
