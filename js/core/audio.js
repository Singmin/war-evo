'use strict';
// 声音
// =====================================================================
// 声音（Web Audio 合成）
// =====================================================================
let AC = null, lastHitSfx = 0, lastBoomSfx = 0;
function audioInit() {
  try {
    if (!AC) AC = new (window.AudioContext || window.webkitAudioContext)();
    if (AC.state === 'suspended') Promise.resolve(AC.resume()).catch(() => {});
  } catch (e) { /* 宿主限制音频时仍可开局 */ }
}
function tone(freq, dur, type = 'square', vol = 0.08, slide = 1, chan = 'sfx') {
  const v = save.settings[chan];
  if (!AC || v <= 0) return;
  const t = AC.currentTime, o = AC.createOscillator(), g = AC.createGain();
  o.type = type; o.frequency.setValueAtTime(freq, t);
  if (slide !== 1) o.frequency.exponentialRampToValueAtTime(Math.max(20, freq * slide), t + dur);
  g.gain.setValueAtTime(vol * v, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g).connect(AC.destination); o.start(t); o.stop(t + dur + 0.02);
}
function noise(dur, vol = 0.2) {
  if (!AC || save.settings.sfx <= 0) return;
  const len = Math.floor(AC.sampleRate * dur), buf = AC.createBuffer(1, len, AC.sampleRate), d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
  const s = AC.createBufferSource(), g = AC.createGain(), f = AC.createBiquadFilter();
  f.type = 'lowpass'; f.frequency.value = 900;
  s.buffer = buf; g.gain.value = vol * save.settings.sfx;
  s.connect(f).connect(g).connect(AC.destination); s.start();
}
function sfx(kind) {
  if (G && G.demo) return;   // 开始页背后的演示局不出声
  const now = performance.now();
  switch (kind) {
    case 'hit': if (now - lastHitSfx < 70) return; lastHitSfx = now; tone(rand(160, 220), 0.06, 'square', 0.03, 0.6); break;
    case 'die': tone(300, 0.15, 'sawtooth', 0.04, 0.4); break;
    case 'buy': tone(660, 0.07, 'square', 0.05); setTimeout(() => tone(880, 0.08, 'square', 0.05), 60); break;
    case 'build': [0, 110, 220].forEach((d, i) => setTimeout(() => { tone(180 - i * 20, 0.05, 'square', 0.05, 0.5); noise(0.05, 0.1); }, d)); break;   // 扩塔位落地：三下锤子
    case 'err': tone(140, 0.18, 'square', 0.06, 0.8); break;
    case 'boom': if (now - lastBoomSfx < 90) return; lastBoomSfx = now; noise(0.35, 0.25); break;
    case 'evolve': [523, 659, 784, 1046].forEach((f, i) => setTimeout(() => tone(f, 0.25, 'triangle', 0.09), i * 110)); break;
    case 'win': [523, 659, 784, 1046, 1318].forEach((f, i) => setTimeout(() => tone(f, 0.3, 'triangle', 0.1), i * 140)); break;
    case 'lose': [440, 392, 330, 262].forEach((f, i) => setTimeout(() => tone(f, 0.35, 'triangle', 0.1), i * 180)); break;
  }
}
// 简单的背景音乐：五声音阶琶音，随玩家时代变调
const MUSIC_SCALE = [0, 2, 4, 7, 9, 12, 9, 7, 4, 2];
let musicStep = 0;
setInterval(() => {
  if (!AC || S.screen !== 'play' || !G || G.over) return;
  const root = [196, 220, 174.6, 233, 261.6][G.sides[0].age];
  const n = MUSIC_SCALE[musicStep % MUSIC_SCALE.length];
  tone(root * Math.pow(2, n / 12), 0.4, 'triangle', 0.05, 1, 'music');
  if (musicStep % 4 === 0) tone(root / 2, 0.9, 'sine', 0.06, 1, 'music');
  musicStep++;
}, 320);
