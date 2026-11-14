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
/** 暂停整个 AudioContext（播广告时让出音频焦点）；audioInit() 恢复 */
function audioPause() {
  try { if (AC && AC.state === 'running') Promise.resolve(AC.suspend()).catch(() => {}); } catch (e) {}
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
// =====================================================================
// 背景音乐：明亮的大调五声拨弦（像拇指琴 / 古筝）+ 柔和贝斯 + 很轻的手鼓
// 一条 8 小节主题，按玩家时代层级换调、加速、加声部；开始页放慢版，决战再提速。
// 全部实时合成，不带音频文件。要调味道只改下面几张表。
// =====================================================================
/** 主旋律：每格一个八分音符，8 小节 × 8 格。数字 = 相对主音的半音数（只用五声 0 2 4 7 9），null = 延续 */
const MUSIC_LEAD = [
  7, null, 9, 7, 4, null, 7, null,
  9, null, 12, 9, 7, null, 4, null,
  2, null, 4, 7, 9, null, 7, 4,
  2, null, null, null, 7, null, 9, null,
  12, null, 9, 12, 14, null, 12, null,
  9, null, 7, 9, 12, null, 9, 7,
  4, null, 7, null, 9, 7, 4, 2,
  0, null, null, null, null, null, 7, null,
];
/** 每小节的和弦：[根音相对主音的半音数, 三度音程（3 = 小三，4 = 大三）]。I vi IV V | I vi IV I */
const MUSIC_CHORDS = [[0, 4], [-3, 3], [-7, 4], [-5, 4], [0, 4], [-3, 3], [-7, 4], [0, 4]];
/**
 * 各场合的编曲。bpm 速度；tr 移调（半音）；arp 每小节分解和弦个数（0 = 不要）；
 * bass 贝斯型（whole 全音符 / half 二分 / bounce 四分根音五度交替 / walk 八分走动）；
 * drums 一小节 16 格（k 手鼓、w 木鱼、h 沙锤、. 空）；echo 主旋律回声；shimmer 主旋律加一层微微失谐的泛音
 */
const MUSIC_VARIANTS = {
  menu: { bpm: 76, tr: 0, arp: 4, bass: 'whole', drums: '................' },
  tiers: [
    { bpm: 88, tr: 0, arp: 0, bass: 'half', drums: 'k.....k...k.....' },                             // 部落
    { bpm: 94, tr: 2, arp: 4, bass: 'half', drums: 'k..h..k.k..h....' },                             // 青铜
    { bpm: 100, tr: 4, arp: 8, bass: 'half', drums: 'k.h.w.h.k.h.w.h.' },                            // 蒸汽
    { bpm: 106, tr: 5, arp: 8, bass: 'bounce', drums: 'k.h.w.h.k.hhw.h.', echo: true },              // 电气
    { bpm: 112, tr: 7, arp: 16, bass: 'walk', drums: 'k.hhw.h.k.hhw.hh', echo: true, shimmer: true }, // 机甲
  ],
  final: { bpm: 124, tr: 7, arp: 16, bass: 'walk', drums: 'k.hhwkh.k.hhw.hk', echo: true, shimmer: true },
};
/** 各声部主音频率（Hz，移调前）和音量（再乘设置里的音乐音量） */
const MUSIC_BASE = { lead: 392, arp: 196, bass: 196 };
const MUSIC_VOL = { lead: 0.085, arp: 0.028, bass: 0.07, drum: 0.09, wood: 0.028, shaker: 0.012 };
/** 总线低通截止频率（Hz）：越低越柔和 */
const MUSIC_SOFTEN = 3400;
/** 游戏每快 1 倍速，音乐快这么多（×3 时 +12%） */
const MUSIC_SPEED_PUSH = 0.06;
/** 提前排多少秒的音符；比定时器间隔大，卡一下也不会断拍 */
const MUSIC_AHEAD = 0.2;
const MUSIC_WALK = [0, 0, 7, 0, 12, 0, 7, 0];

let musicBus = null, musicNoise = null, musicStep = 0, musicNext = 0, musicVar = null;
/** 一个振荡器音。attack 起音秒数；ring 衰减到无声的秒数；slide = 结束时频率倍数 */
function musicNote(type, freq, t, ring, vol, attack = 0.004, slide = 1) {
  const o = AC.createOscillator(), g = AC.createGain();
  o.type = type; o.frequency.setValueAtTime(freq, t);
  if (slide !== 1) o.frequency.exponentialRampToValueAtTime(freq * slide, t + ring);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(vol, t + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, t + ring);
  o.connect(g).connect(musicBus); o.start(t); o.stop(t + ring + 0.02);
}
/** 拨弦：三角波基音 + 高八度泛音，泛音消得快，听起来像拇指琴 */
function musicPluck(freq, t, dur, vol, shimmer) {
  const ring = Math.min(1.4, dur + 0.35);
  musicNote('triangle', freq, t, ring, vol);
  musicNote('sine', freq * 2, t, ring * 0.45, vol * 0.3);
  if (shimmer) musicNote('sine', freq * 2.006, t, ring * 0.8, vol * 0.18);
}
/** 沙锤：一小段高通噪声 */
function musicShaker(t) {
  const s = AC.createBufferSource(), f = AC.createBiquadFilter(), g = AC.createGain();
  s.buffer = musicNoise; f.type = 'highpass'; f.frequency.value = 5000;
  g.gain.setValueAtTime(MUSIC_VOL.shaker, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
  s.connect(f).connect(g).connect(musicBus); s.start(t, Math.random() * 0.5, 0.07);
}
/** 现在该放哪套编曲；null = 不放（暂停、设置、结算等页面） */
function musicWanted() {
  if (S.screen === 'menu') return MUSIC_VARIANTS.menu;
  if ((S.screen !== 'play' && S.screen !== 'tree') || !G || G.over || G.demo) return null;
  if (G.finalOn) return MUSIC_VARIANTS.final;
  return MUSIC_VARIANTS.tiers[Math.min(G.sides[0].age, MUSIC_VARIANTS.tiers.length - 1)];
}
/** 排第 s 个十六分音符（0–127）在时刻 t 的所有声部；d = 一格的秒数 */
function musicPlayStep(v, s, t, d) {
  const bar = s >> 4, st = s & 15, [root, third] = MUSIC_CHORDS[bar], k = Math.pow(2, v.tr / 12);
  const semi = n => Math.pow(2, n / 12);
  if (st % 2 === 0) {
    const i = bar * 8 + st / 2, n = MUSIC_LEAD[i];
    if (n !== null) {
      let len = 1;
      while (i + len < MUSIC_LEAD.length && MUSIC_LEAD[i + len] === null) len++;
      const f = MUSIC_BASE.lead * k * semi(n), dur = len * 2 * d;
      musicPluck(f, t, dur, MUSIC_VOL.lead, v.shimmer);
      if (v.echo) musicPluck(f, t + 3 * d, d, MUSIC_VOL.lead * 0.25, false);
    }
    const bf = MUSIC_BASE.bass * k * semi(root), bv = MUSIC_VOL.bass;
    if (v.bass === 'whole' && st === 0) musicNote('triangle', bf, t, 16 * d, bv, 0.03);
    else if (v.bass === 'half' && st % 8 === 0) musicNote('triangle', bf, t, 8 * d, bv, 0.03);
    else if (v.bass === 'bounce' && st % 4 === 0) musicNote('triangle', bf * semi(st % 8 ? 7 : 0), t, 4 * d, bv, 0.02);
    else if (v.bass === 'walk') musicNote('triangle', bf * semi(MUSIC_WALK[st / 2]), t, 2.4 * d, bv * 0.85, 0.015);
  }
  if (v.arp && st % (16 / v.arp) === 0) {
    const tones = [0, 7, 12, 12 + third, 12, 7], gap = 16 / v.arp;
    musicPluck(MUSIC_BASE.arp * k * semi(root + tones[(st / gap) % tones.length]), t, gap * d, MUSIC_VOL.arp, false);
  }
  const hit = v.drums[st];
  if (hit === 'k') musicNote('sine', 120, t, 0.16, MUSIC_VOL.drum, 0.003, 0.5);
  else if (hit === 'w') musicNote('sine', 900, t, 0.06, MUSIC_VOL.wood, 0.002);
  else if (hit === 'h') musicShaker(t);
}
/** 定时器回调：把接下来 MUSIC_AHEAD 秒内的音符排进 AudioContext 时间线 */
function musicTick() {
  if (!AC || AC.state !== 'running') return;
  const vol = save.settings.music, want = musicWanted();
  if (!want || vol <= 0) { musicNext = 0; return; }
  if (!musicBus) {
    const soft = AC.createBiquadFilter();
    soft.type = 'lowpass'; soft.frequency.value = MUSIC_SOFTEN;
    musicBus = AC.createGain(); musicBus.connect(soft).connect(AC.destination);
    musicNoise = AC.createBuffer(1, AC.sampleRate, AC.sampleRate);
    const data = musicNoise.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  }
  musicBus.gain.value = vol;
  const menu = want === MUSIC_VARIANTS.menu;
  if (!musicVar || menu !== (musicVar === MUSIC_VARIANTS.menu)) { musicVar = want; musicStep = 0; }   // 进出开始页：从头放
  const now = AC.currentTime;
  if (musicNext < now) musicNext = now + 0.05;
  while (musicNext < now + MUSIC_AHEAD) {
    const s = musicStep % (MUSIC_CHORDS.length * 16);
    if (s % 16 === 0) musicVar = want;   // 换时代 / 进决战：等到小节线再换编曲
    const d = 60 / (musicVar.bpm * (menu ? 1 : 1 + MUSIC_SPEED_PUSH * (S.speed - 1))) / 4;
    musicPlayStep(musicVar, s, musicNext, d);
    musicNext += d; musicStep++;
  }
}
setInterval(musicTick, 40);
