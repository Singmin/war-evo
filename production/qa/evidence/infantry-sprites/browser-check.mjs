// Run after python -m http.server 8765.
// Usage: node browser-check.mjs [--mobile] [--anim-v2] [path-to-Chromium-headless-shell]
import { spawn } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const evidence = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const mobile = args.includes('--mobile');
const animV2 = args.includes('--anim-v2');
const out = animV2 ? join(evidence, 'anim-v2', 'browser') : evidence;
mkdirSync(out, { recursive: true });
const chrome = args.find(arg => !arg.startsWith('--')) || join(process.env.LOCALAPPDATA, 'ms-playwright',
  'chromium_headless_shell-1248', 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
const url = process.env.INFANTRY_QA_URL || 'http://127.0.0.1:8765/';
const port = mobile ? 9374 : 9373;
const eras = mobile ? [4, 13] : animV2 ? [0, 2, 3, 6, 10, 13] : [0, 2, 4, 6, 10, 13];
const errors = [];
const viewport = mobile ? { width: 844, height: 390, deviceScaleFactor: 2, mobile: true } :
  { width: 1366, height: 768, deviceScaleFactor: 1, mobile: false };
const report = { viewport, battle: {}, archive: {} };
const profile = mkdtempSync(join(tmpdir(), 'infantry-sprites-browser-'));
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
      if (m === SPRITE_META[me().era][0]) blits.push([frame, row]);
      return originalBlit(sheet, m, frame, row);
    };
    window.blits = [];
    window.rank = side => G.units.filter(u => u.side === side && u.type === 0 && !u.dead)
      .sort((a, b) => side ? a.x-b.x : b.x-a.x);
    window.human = () => rank(0)[0];
    window.foe = () => rank(1)[0];
    window.infantryButton = () => menuDefs.find(d => d.id === 'u0').el;
    window.visibleIconIsFrameOne = async era => {
      const icon = infantryButton().querySelector('img.un');
      if (!icon) return false;
      await icon.decode();
      const m = spriteMeta(era, 0), s = spriteSheet(era, 0);
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
      if (icon.naturalWidth !== w || icon.naturalHeight !== h) return false;
      const actual = p.getImageData(0, 0, w, h).data;
      // Alpha must match throughout. The PNG/canvas round trip can round
      // the RGB values of the translucent shadow during premultiplication.
      return actual.every((value, i) => {
        const alphaIndex = i - (i % 4) + 3;
        return (i === alphaIndex || expected[alphaIndex] === 255) ? value === expected[i] : true;
      });
    }; 1`);
  report.atlasVersion = await evalPage('SPRITE_VER');
  for (const era of eras) {
    const prefix = (mobile ? 'mobile-era-' : 'era-') + String(era).padStart(2, '0');
    await evalPage(`newGame(S.diff); me().era = G.sides[1].era = ${era}; me().gold = 999;
      G.camX = 0; G.zoom = 1; setMenu('units'); 1`);
    await until(() => evalPage(`!!spriteSheet(${era}, 0) && !!infantryButton().querySelector('img.un')`),
      prefix + ' icon');
    await until(() => evalPage(`visibleIconIsFrameOne(${era})`), prefix + ' frame 01 thumbnail');
    await click('infantryButton()');
    if (mobile) {
      await until(() => evalPage("selectedId === 'u0' && infantryButton().classList.contains('sel')"),
        prefix + ' touch selection');
      assert.equal(await evalPage('me().queue.length'), 0);
      await shot(prefix + '-selected');
      await click('infantryButton()');
    }
    assert.equal(await evalPage(`me().queue.some(q => q.type === 0 && q.age === ${era})`), true);
    const spawned = await evalPage(`(() => {
      for (let i = 0; i < 3; i++) {
        const error = actTrain(me(), 0);
        if (error) throw Error(error);
      }
      for (let n = 0; rank(0).length < 4 && n < 1200; n++) tick(1);
      const u = human();
      if (!u) return null;
      return { name: UNIT_NAMES[u.age][0], w: u.w, h: u.h, air: u.air, altitude: unitAlt(u),
        trained: rank(0).length, drawn: captureBlits().filter(([frame, row]) => frame < 8 && row === 0).length };
    })()`);
    assert.ok(spawned && !spawned.air && spawned.altitude === 0);
    assert.deepEqual([spawned.trained, spawned.drawn], [4, 4]);
    assert.deepEqual([spawned.w, spawned.h], [22, 44]);
    await shot(prefix + '-spawn');

    // Use real spawn objects. Arrange a repeatable two-sided encounter within the camera.
    const counts = await evalPage(`(() => {
      rank(0).forEach((unit, i) => { unit.x = 825-i*49; });
      for (const side of [0, 1]) {
        const start = side ? 1095 : 825;
        for (let i = rank(side).length; i < 8; i++) {
          if (!trySpawn(G.sides[side], { type: 0, age: ${era} })) throw Error('spawn blocked');
          const unit = G.units.at(-1);
          unit.x = start + (side ? 49 : -49) * i;
          unit.cd = 99;
        }
      }
      G.camX = 320;
      return [rank(0).length, rank(1).length];
    })()`);
    assert.deepEqual(counts, [8, 8]);
    const walked = await evalPage(`(() => {
      const x = human().x, frames = new Set();
      for (let i = 0; i < 38; i++) {
        tick(1);
        if (human().walking) frames.add(unitFrame(human()));
      }
      return { distance: human().x-x, frames: [...frames].sort(), moving: G.units.filter(u => u.walking).length };
    })()`);
    assert.ok(walked.distance > 0 && walked.moving >= 12);
    assert.deepEqual(walked.frames, [0, 1, 2, 3]);
    await shot(prefix + '-walk');

    const attack = await evalPage(`(() => {
      const u = human(), v = foe();
      const gap = 48, rankSpacing = 27;
      rank(0).forEach((unit, i) => { unit.x = 936-i*rankSpacing; unit.cd = 99; });
      rank(1).forEach((unit, i) => { unit.x = 936+gap+i*rankSpacing; unit.cd = 99; });
      u.cd = .34;
      const frames = new Set();
      for (let i = 0; i < 30; i++) {
        tick(1);
        frames.add(unitFrame(u));
        if (u.swing > .125) break;
      }
      const draws = captureBlits();
      return { frames: [...frames], hpLoss: v.maxHp-v.hp, blits: draws, rankSpacing,
        allyCount: rank(0).length, enemyCount: rank(1).length };
    })()`);
    assert.deepEqual(attack.frames, [4, 5, 6]);
    assert.ok(attack.hpLoss > 0 && attack.blits.some(([f, r]) => f === 6 && r === 0));
    assert.equal(attack.blits.length, 16);
    assert.deepEqual([attack.allyCount, attack.enemyCount], [8, 8]);
    await shot(prefix + '-attack');
    const recover = await evalPage(`tick(9); ({ pose: unitFrame(human()), draws: captureBlits() })`);
    assert.equal(recover.pose, 7);
    assert.ok(recover.draws.some(([, r]) => r === 0) && recover.draws.some(([, r]) => r === 1));
    if (!animV2) await shot(prefix + '-crowd');

    const hit = await evalPage(`(() => {
      const u = human();
      foe().cd = 0; u.cd = 99; u.swing = 0; tick(1);
      const draws = captureBlits();
      return { hpLoss: u.maxHp-u.hp, flash: u.hit, blits: draws };
    })()`);
    assert.ok(hit.hpLoss > 0 && hit.flash > 0 && hit.blits.some(([, row]) => row === 2));
    await shot(prefix + '-hit');

    // Observe the real health bar call and compare it to the rendered ally sprite at the same zoom.
    const healthBar = await evalPage(`(() => {
      tick(12);
      const u = human(), m = spriteMeta(u.age, u.type), img = spriteSheet(u.age, u.type);
      const c = document.createElement('canvas'); c.width = m.cw; c.height = m.ch;
      const p = c.getContext('2d');
      p.drawImage(img, unitFrame(u)*m.cw, m.y, m.cw, m.ch, 0, 0, m.cw, m.ch);
      const data = p.getImageData(0, 0, m.cw, m.ch).data;
      const top = Math.floor(data.findIndex((v, i) => i%4 === 3 && v > 0) / (4*m.cw));
      const spriteTop = GROUND_Y - (m.ch-1-top)*(m.s || SPRITE_SCALE)*G.zoom;
      const original = ctx.fillRect;
      let bounds;
      ctx.fillRect = function(x, y, w, h) {
        if (this.fillStyle === '#7dff6b' && Math.abs(x - (sx(u.x) - Math.max(26, u.w*G.zoom)/2)) < .01) {
          bounds = { x, y, w, h };
        }
        return original.call(this, x, y, w, h);
      };
      try { render(); } finally { ctx.fillRect = original; }
      return { bounds, spriteTop, zoom: G.zoom };
    })()`);
    assert.ok(healthBar.bounds?.w > 0 && healthBar.bounds.y + healthBar.bounds.h < healthBar.spriteTop);

    const death = await evalPage(`(() => {
      const u = human();
      damageUnit(u, 1e6);
      const seen = new Set();
      for (let i = 0; i < 19; i++) {
        if (i % 3 === 0) for (const [frame, side] of captureBlits()) {
          if (frame >= 8 && side === 0) seen.add(frame);
        }
        tick(1);
      }
      return { fx: G.fx.find(f => f.kind === 'die' && f.type === 0), frames: [...seen],
        blits: captureBlits() };
    })()`);
    assert.equal(death.fx?.alt, 0);
    assert.deepEqual(death.frames, [8, 9, 10]);
    assert.ok(death.blits.some(([f, r]) => f === 10 && r === 0));
    await shot(prefix + '-death');
    const landed = await evalPage('tick(4); captureBlits()');
    assert.ok(landed.some(([f, r]) => f === 11 && r === 0));
    await shot(prefix + '-landed');
    report.battle[era] = { spawned, iconFrame: 1, walked, attack, recover, hit, healthBar, death, landed,
      input: mobile ? 'landscape touch selection and queue' : 'desktop mouse queue' };
  }
  report.bootErrors = await evalPage('bootErrors');
  report.browser = await evalPage('navigator.userAgent');
  if (!mobile) {
    await send('Page.navigate', { url: url + 'tools/asset-browser/' });
    await until(() => evalPage("!!document.querySelector('#unit-0-0')"), 'asset browser');
    for (let era = 0; era < 17; era++) {
      await evalPage(`document.querySelector('#unit-${era}-0').click(); 1`);
      const info = await until(() => evalPage(`(() => {
        const frames = [...document.querySelectorAll('#unit-detail .filmstrip canvas')];
        const unique = new Set(frames.map(c => c.toDataURL())).size;
        return frames.length === 12 && unique === 12 ?
          { title: document.querySelector('#detail-title').textContent, frames: frames.length, unique } : null;
      })()`), 'asset browser era ' + era);
      if (animV2) {
        const count = await evalPage(`(async () => {
          const button = [...document.querySelectorAll('#unit-detail button')]
            .find(b => b.textContent === '连续 12 帧');
          if (!button) return 0;
          button.click();
          const canvas = document.querySelector('#unit-detail .detail-preview canvas');
          const frames = new Set();
          for (let i = 0; i < 66; i++) {
            await new Promise(resolve => setTimeout(resolve, 27));
            frames.add(canvas.toDataURL());
          }
          return frames.size;
        })()`);
        assert.equal(count, 12, 'continuous playback era ' + era);
        info.played = count;
      }
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
